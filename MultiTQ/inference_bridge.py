import os
import json
import re
import time
import string
import asyncio
import pickle
from collections import defaultdict
from typing import List

from datetime import datetime
from dateutil import parser
from tqdm.asyncio import tqdm_asyncio
from termcolor import colored
from pydantic import BaseModel, Field
from langchain_deepseek import ChatDeepSeek
from langchain.messages import SystemMessage, HumanMessage

from config import Config
from Retriever import Retrieval_BGE


# os.chdir(sys.path[0])  # 设置工作目录为脚本所在目录
STRUCTURED_LLM = None

class HistoricalResponse(BaseModel):
    """
    Response model for historical fact retrieval.
    """
    reasoning: str = Field(
        ...,
        description=(
            "Step-by-step reasoning based on the provided facts. "
            "Analyze semantic relevance (e.g., distinguishing 'Business (South Korea)' from 'South Korea'), "
            "handle time logic (before/after/first/last), and explain how the final answer was derived."
        )
    )
    final_answer: List[str] = Field(
        ...,
        description=(
            "The final concise answer. "
            "- If the question asks for a specific Year (e.g., 'Which year'), return a list containing the string 'YYYY'. "
            "- If the question asks for a specific Month (e.g., 'Which month'), return a list containing the string 'YYYY-MM'. "
            "- If the question asks for a specific Date (e.g., 'When', 'What day'), return a list containing the string 'YYYY-MM-DD'. "
            "- If the question asks for Entities (e.g., 'Who', 'Which country'), return a LIST of strings, where each string is formatted as 'EntityName Timestamp'. Include all correct, non-duplicate entities."
        )
    )

def load_prompt(key):
    path = Config.PROMPT_PATHS[key]
    if path and os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return '\n'.join([l.strip() for l in f.readlines()])
    return "" # Return empty or default prompt

async def llm_invoke(question, sys_mes, fact_text, label="Relevant facts"):
    human_message = f"{label}:\n{fact_text}\n\nQuestion: {question}"
    messages = [SystemMessage(sys_mes), HumanMessage(human_message)]
    results = await STRUCTURED_LLM.ainvoke(messages)
    return results.final_answer

async def get_facts_from_faiss(question, retriever, sys_mes, n=15):
    fact_result = await retriever.get_faiss_similarity(question, n)
    facts = fact_result.get('fact', [])
    fact_text = '\n'.join(facts) if facts else 'No facts provided.'
    answer = await llm_invoke(question, sys_mes, fact_text, "Historical facts")
    return answer, fact_text

def parse_date_str(date_str):
    try:
        return parser.parse(date_str, fuzzy=True, default=datetime(1, 1, 1))
    except (ValueError, TypeError):
        return None

async def extract_and_compare_dates(date_strings):
    parsed_dates = []
    for date_str in date_strings:
        dt = parse_date_str(date_str)
        if dt:
            parsed_dates.append(dt)
    
    if not parsed_dates:
        return None, None, None
    
    # Preserving logic: First valid date is most relevant (based on similarity rank)
    most_relevant = parsed_dates[0].strftime('%Y-%m-%d')
    
    # Sort for chrono bounds
    parsed_dates.sort()
    earliest = parsed_dates[0].strftime('%Y-%m-%d')
    latest = parsed_dates[-1].strftime('%Y-%m-%d')
    
    return most_relevant, earliest, latest

def filter_facts_by_date(facts, ref_date, question):
    if not ref_date:
        return facts
        
    filtered_facts = []
    is_before = "before" in question or "Before" in question
    is_after = "after" in question or "After" in question
    
    if not (is_before or is_after):
        return facts

    for fact in facts:
        dt = parse_date_str(fact)
        if dt:
            fact_date = dt.strftime('%Y-%m-%d')
            if is_before and fact_date < ref_date:
                filtered_facts.append(fact)
            elif is_after and fact_date > ref_date:
                filtered_facts.append(fact)
                
    return filtered_facts

async def solve_single_tree(tree, idx, retriever, semaphore, sys_mes, reranker_lock):
    async with semaphore:
        try:
            ori_node = tree[-1]
            dt = parse_date_str(ori_node["question_text"])
            q_date = dt.strftime('%Y-%m-%d') if dt else None

            for node in tree:
                question = node["question_text"].strip()
                type_ = node.get("type", "")
                idx = node["idx"]

                if type_ == "Anchor":
                    async with reranker_lock:
                        fact_result, fact_scores = await retriever.rerank_facts(question, top_k=Config.RERANK_NUM)
                    
                    node["facts"] = fact_result
                    node["most_relevant_date"], node["earliest_date"], node["latest_date"] = \
                        await extract_and_compare_dates(fact_result)
                        
                elif type_ == "Bridge":
                    anchor_node = None
                    for i in range(idx - 1, -1, -1):
                        if tree[i].get("type") == "Anchor":
                            anchor_node = tree[i]
                            break

                    has_placeholder = bool(re.search(r"#t\b", question))
                    facts = []

                    if has_placeholder and anchor_node:
                        replacement_date = anchor_node.get("most_relevant_date")
                        if replacement_date:
                            question = re.sub(r"#t\b", replacement_date, question)
                            facts_result = await retriever.get_faiss_similarity(question, n=Config.FACTS_NUM)
                            raw_facts = facts_result.get('fact', []) if isinstance(facts_result, dict) else []
                            facts = filter_facts_by_date(raw_facts, replacement_date, question)[:25]
                        else:
                            print(f"Warning: No replacement found for #t in question: {question}")
                            facts_result = await retriever.get_faiss_similarity(question, n=Config.FACTS_NUM)
                            facts = facts_result.get('fact', []) if isinstance(facts_result, dict) else []

                    elif anchor_node:
                        facts = anchor_node.get('facts', [])
                    else:
                        facts_result = await retriever.get_faiss_similarity(question, n=Config.FACTS_NUM)
                        raw_facts = facts_result.get('fact', [])
                        facts = filter_facts_by_date(raw_facts, q_date, question)[:35]

                    fact_text = '\n'.join(facts) if facts else 'No facts provided.'
                    node['facts'] = facts
                    node['answer'] = await llm_invoke(question, sys_mes, fact_text)
                else:
                    answer = tree[idx - 1]['answer']
                    if not answer:
                        node['answer'], node['facts'] = await get_facts_from_faiss(question, retriever, sys_mes, n=Config.FACTS_NUM)
                    else:
                        node['answer'] = answer

                node['question'] = question
                    
        except Exception as e:
            raise e
        return tree

async def run_inference(tree_file):
    print(colored("Running Inference Engine...", "green"))
    triple_list = []
    if os.path.exists(Config.KG_PATH):
        with open(Config.KG_PATH, 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.strip().replace("_", " ").split('\t')
                if len(parts) >= 4:
                    triple_list.append(parts)
    # 初始化检索器
    retriever = Retrieval_BGE('time', Config.BGE, Config.RERANKER, triple_list, gpu_id=Config.GPU_ID)
    await retriever.load()
    
    # 加载树
    with open(tree_file, "r") as f:
        trees = json.load(f)
    
    sys_mes = load_prompt('ag')

    # 并发执行
    semaphore = asyncio.Semaphore(Config.CONCURRENCY)

    # 创建一个全局锁用于Reranker
    reranker_lock = asyncio.Lock()
    tasks = []
    for i, tree in enumerate(trees):
        task = asyncio.create_task(solve_single_tree(tree, i, retriever, semaphore, sys_mes, reranker_lock))
        tasks.append(task)
    
    results = []
    # 使用 tqdm 显示进度
    for task in tqdm_asyncio(asyncio.as_completed(tasks), total=len(tasks), desc="Inferencing"):
        res = await task
        results.append(res)
        
    # 保存
    os.makedirs(os.path.dirname(Config.RESULT_FILE), exist_ok=True)
    with open(Config.RESULT_FILE, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"Inference done. Results saved to {Config.RESULT_FILE}")
    return Config.RESULT_FILE

def normalize_text(s):
    s = str(s).lower()
    exclude = set(string.punctuation)
    s = "".join(char for char in s if char not in exclude)
    s = re.sub(r"\b(a|an|the)\b", " ", s)
    return " ".join(s.split())

def normalize_prediction(prediction):
    if isinstance(prediction, list):
        return prediction
    elif isinstance(prediction, (int, float)):
        return [str(prediction)]
    elif isinstance(prediction, str):
        try:
            return json.loads(prediction) if prediction.strip().startswith("[") else [prediction]
        except:
            return [prediction]
    return []

def topk(prediction, k=-1):
    if isinstance(prediction, list):
        return prediction[:k]
    elif isinstance(prediction, str):
        return [prediction]
    elif isinstance(prediction, int) or isinstance(prediction, float):
        return [str(prediction)]  # 转成字符串列表
    else:
        raise ValueError(f"Unsupported prediction type: {type(prediction)}")

def eval_hit(prediction, answers):
    if not isinstance(answers, list): answers = [answers]
    pred_norm = normalize_text(prediction)
    for ans in answers:
        if normalize_text(ans) in pred_norm:
            return 1
    return 0

def evaluate(result_file):
    print(colored("Evaluating Results...", "green"))
    
    with open(result_file, 'r') as f:
        trees = json.load(f)
        
    q2a = []
    q2a_trees = []
    hit_list = []
    
    stats_map = {
        "answer_type": defaultdict(lambda: {"hit": 0, "total": 0}),
        "qlabel": defaultdict(lambda: {"hit": 0, "total": 0}),
        "equal": defaultdict(lambda: {"hit": 0, "total": 0}),
        "before_after": defaultdict(lambda: {"hit": 0, "total": 0}),
        "equal_multi": defaultdict(lambda: {"hit": 0, "total": 0})
    }

    print(len(trees))
    
    for i, tree in enumerate(trees):
        node = tree[-1]
        
        question, prediction = node["question"], node["answer"]
        normalized_pred = normalize_prediction(prediction)
        topk_pred = topk(normalized_pred, 1)
        
        gold = node["gold_answer"]
        qlabel = node["qlabel"]
        qtype = node["qtype"]
        answer_type = node["answer_type"]
        time_level = node["time_level"]
        
        hit = eval_hit(topk_pred, gold)
        hit_list.append(hit)
        
        if hit == 0:
            q2a_trees.append(tree)
            q2a.append({
                "question": question, 
                "prediction": prediction, 
                "gold_answer": gold, 
                "qlabel": qlabel, 
                "qtype": qtype, 
                "answer_type": answer_type, 
                "time_level": time_level
            })

        # Update stats
        stats_map["answer_type"][answer_type]["hit"] += hit
        stats_map["answer_type"][answer_type]["total"] += 1
        
        stats_map["qlabel"][qlabel]["hit"] += hit
        stats_map["qlabel"][qlabel]["total"] += 1
        
        if qtype in ["equal", "before_after", "equal_multi"]:
             stats_map[qtype][time_level]["hit"] += hit
             stats_map[qtype][time_level]["total"] += 1

    print(f"Overall Hit: {sum(hit_list) * 100 / len(hit_list):.2f}% ({sum(hit_list)}/{len(hit_list)})")

    def print_stats(name, data):
        print(f"Hit by {name}:")
        for key, val in data.items():
            hit, total = val["hit"], val["total"]
            acc = hit * 100 / total if total > 0 else 0.0
            print(f"  {key}: {acc:.2f}% ({hit}/{total})")

    print_stats("Answer Type", stats_map["answer_type"])
    print_stats("QLabel", stats_map["qlabel"])
    print_stats("Equal", stats_map["equal"])
    print_stats("Before_after", stats_map["before_after"])
    print_stats("Equal_Multi", stats_map["equal_multi"])

    json.dump(q2a, open(Config.Q2A_FILE, "w"), indent=2)
    output_path = Config.Q2A_FULL_FILE
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(q2a_trees, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    # mp.set_start_method("spawn", force=True) # CUDA 要求 spawn
    start_time = time.time()
    # 初始化 LLM
    LLM = ChatDeepSeek(model=Config.LLM, api_key=Config.API_KEY, temperature=0.0, max_tokens=8192, timeout=120, max_retries=2)
    STRUCTURED_LLM = LLM.with_structured_output(HistoricalResponse)
    
    # 1. 构建树
    # 注意：如果已经有 formatted tree，可以注释掉这行
    tree_file = Config.SUBQ_FORMATTED_FILE
    
    if tree_file:
        # 2. 运行推理 (Async)
        try:
            result_file = asyncio.run(run_inference(tree_file))
            # result_file = Config.RESULT_FILE
            
            # 3. 评估
            if result_file:
                evaluate(result_file)
                
        except KeyboardInterrupt:
            print("Interrupted by user.")
        except Exception as e:
            print(f"Pipeline failed: {e}")
            import traceback
            traceback.print_exc()

    print(f"Total time: {time.time() - start_time:.2f}s")