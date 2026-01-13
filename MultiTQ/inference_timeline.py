import os, sys
import json
import re
import time
import ast
import math
import string
import asyncio
import aiohttp
import argparse
import pickle
import numpy as np
import multiprocessing as mp
from config import Config
from datetime import datetime
from collections import defaultdict
from tqdm.asyncio import tqdm_asyncio
from typing import List, Union, Annotated
from pydantic import BaseModel, Field
from termcolor import colored
from dateutil import parser
from Retriever import TemporalKnowledgeGraph, Retrieval_BGE
from langchain_deepseek import ChatDeepSeek
from langchain.messages import SystemMessage, HumanMessage


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

async def llm_invoke(question, sys_mes, fact_text):
    system_message = sys_mes
    human_message = f"Relevant facts:\n{fact_text}\n\nQuestion: {question}"
    messages = [SystemMessage(system_message), HumanMessage(human_message)]
    results = await STRUCTURED_LLM.ainvoke(messages)
    answer = results.final_answer
    return answer

async def get_facts_from_faiss(question, retriever, sys_mes, n=15):
    fact_result = await retriever.get_faiss_similarity(question, n)
    
    fact_list = fact_result.get('fact')
    fact_text = '\n'.join(fact_list) if fact_list else 'No facts provided.'
    
    system_message = sys_mes
    human_message = f"Historical facts:\n{fact_text}\n\nQuestion: {question}"
    messages = [SystemMessage(system_message), HumanMessage(human_message)]
    results = await STRUCTURED_LLM.ainvoke(messages)
    answer = results.final_answer
    return answer, fact_text

async def get_answer_from_other_subqs(question, relevant_fact, sys_mes):
    if isinstance(relevant_fact, str):
        fact_text = relevant_fact
    else:
        fact_text = '\n'.join(relevant_fact) if relevant_fact else 'No facts provided.'
    system_message = sys_mes
    human_message = f"Relevant facts:\n{fact_text}\n\nQuestion: {question}"
    messages = [SystemMessage(system_message), HumanMessage(human_message)]
    results = await STRUCTURED_LLM.ainvoke(messages)
    answer = results.final_answer
    return answer, fact_text

async def get_facts_from_graph(question, entity_names, retriever, sys_mes):
    fact_result = await retriever.compute_similarity(question, entity_names, n=15)
    fact_list = [fact['fact'] for fact in fact_result]
    fact_text = '\n'.join(fact_list) if fact_list else 'No facts provided.'

    system_message = sys_mes
    human_message = f"Historical facts:\n{fact_text}\n\nQuestion: {question}"
    messages = [SystemMessage(system_message), HumanMessage(human_message)]
    results = await STRUCTURED_LLM.ainvoke(messages)
    answer = results.final_answer
    return answer, fact_text

async def extract_and_compare_dates(date_strings):
    parsed_dates = []
    for date_str in date_strings:
        try:
            # 使用 fuzzy=True 可以从包含其他文本的字符串中提取日期
            dt = parser.parse(date_str, fuzzy=True, default=datetime(1, 1, 1))
            parsed_dates.append((dt, date_str))
        except (ValueError, TypeError):
            # 如果解析失败，跳过该字符串
            continue
    
    if not parsed_dates:
        return None
    
    # 格式化为 YYYY-MM-DD
    first_fomatted = parsed_dates[0][0].strftime('%Y-%m-%d')
    
    return first_fomatted

async def solve_single_tree(tree, idx, retriever, semaphore, sys_mes, reranker_lock):
    async with semaphore:
        try:
            ori_node = tree[-1]
            try:
                dt = parser.parse(ori_node["question_text"], fuzzy=True, default=datetime(1, 1, 1))
                q_date = dt.strftime('%Y-%m-%d')
            except (ValueError, TypeError):
                q_date = None
            for node in tree:
                question = node["question_text"].strip()
                entities = node["entities"]
                type = node.get("type", "")
                idx = node["idx"]

                # 处理 anchor 和 bridge 子问题
                if type == "Anchor":
                    # Anchor 子问题的处理逻辑
                    async with reranker_lock:
                        fact_result, fact_scores = await retriever.rerank_facts(question, top_k=Config.RERANK_NUM)
                    
                    node["facts"] = fact_result
                    most_relevant_date, earliest_date, latest_date = await extract_and_compare_dates(fact_result)
                    node["most_relevant_date"], node["earliest_date"], node["latest_date"] = most_relevant_date, earliest_date, latest_date
                elif type == "Bridge":
                    # Bridge 子问题的处理逻辑
                    # 查 Anchor 子问题
                    anchor_node = None
                    for i in range(idx - 1, -1, -1):
                        if tree[i].get("type") == "Anchor":
                            anchor_node = tree[i]
                            break

                    # 找占位符
                    ref_tokens = re.findall(r"#t\b", question)
                    facts = [] # 初始化 facts
                    if ref_tokens and anchor_node:
                        # 假设 bridge 依赖于前一个 anchor 子问题
                        # 在当前的 tree 结构中，通常 anchor 是 bridge 的前置节点
                        replacement_date = anchor_node.get("most_relevant_date")

                        # 替换所有 #t
                        if replacement_date:
                            question = re.sub(r"#t\b", replacement_date, question)
                            facts_results = await retriever.get_faiss_similarity(question, n=Config.FACTS_NUM)
                            if isinstance(facts_results, dict):
                                facts = facts_results.get('fact', [])
                        else:
                            # 无法替换，可能需要记录错误或使用原问题检索
                            print(f"Warning: No replacement found for #t in question: {question}")
                            facts = await retriever.get_faiss_similarity(question, n=Config.FACTS_NUM)
                            if isinstance(facts, dict):
                                facts = facts.get('fact', [])
                        
                        filtered_facts = []
                        if "before" in question or "Before" in question:
                            # 过滤出在 replacement_date 之前的事实
                            for fact in facts:
                                try:
                                    dt = parser.parse(fact, fuzzy=True, default=datetime(1, 1, 1))
                                    fact_date = dt.strftime('%Y-%m-%d')
                                    if fact_date < replacement_date:
                                        filtered_facts.append(fact)
                                except (ValueError, TypeError):
                                    continue
                        elif "after" in question or "After" in question:
                            # 过滤出在 replacement_date 之后的事实
                            for fact in facts:
                                try:
                                    dt = parser.parse(fact, fuzzy=True, default=datetime(1, 1, 1))
                                    fact_date = dt.strftime('%Y-%m-%d')
                                    if fact_date > replacement_date:
                                        filtered_facts.append(fact)
                                except (ValueError, TypeError):
                                    continue
                        facts = filtered_facts[:25]
                    elif anchor_node:
                        # 如果没有占位符但存在前一个节点，从其事件中获取答案
                        facts = anchor_node.get('facts', [])
                    else:
                        facts_result = await retriever.get_faiss_similarity(question, n=Config.FACTS_NUM)
                        facts = facts_result.get('fact', [])
                        filtered_facts = []
                        if "before" in question or "Before" in question:
                            for fact in facts:
                                try:
                                    dt = parser.parse(fact, fuzzy=True, default=datetime(1, 1, 1))
                                    fact_date = dt.strftime('%Y-%m-%d')
                                    if q_date and fact_date < q_date:
                                        filtered_facts.append(fact)
                                except (ValueError, TypeError):
                                    continue
                        elif "after" in question or "After" in question:
                            for fact in facts:
                                try:
                                    dt = parser.parse(fact, fuzzy=True, default=datetime(1, 1, 1))
                                    fact_date = dt.strftime('%Y-%m-%d')
                                    if q_date and fact_date > q_date:
                                        filtered_facts.append(fact)
                                except (ValueError, TypeError):
                                    continue
                        facts = filtered_facts[:35]

                    fact_text = '\n'.join(facts) if facts else 'No facts provided.'
                    node['facts'] = facts
                    node['answer'] = await llm_invoke(question, sys_mes, fact_text)
                else:
                    answer = tree[idx - 1]['answer']
                    if not answer:
                        node['answer'], node['facts'] = await get_facts_from_faiss(question, retriever, sys_mes, n=Config.FACTS_NUM)
                    else:
                        node['answer'] = answer

                node['question'] = question  # 更新问题文本
                    
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
    hit_by_answer_type = defaultdict(lambda: {"hit": 0, "total": 0})
    hit_by_qlabel = defaultdict(lambda: {"hit": 0, "total": 0})
    hit_by_equal = defaultdict(lambda: {"hit": 0, "total": 0})
    hit_by_before_after = defaultdict(lambda: {"hit": 0, "total": 0})
    hit_by_equal_multi = defaultdict(lambda: {"hit": 0, "total": 0})
    print(len(trees))
    
    for i, tree in enumerate(trees):
        # 根节点是最后一个
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
        if(hit==0):
            q2a_trees.append(
                tree
            )
            q2a.append({"question": question, "prediction": prediction, "gold_answer": gold, "qlabel": qlabel, "qtype": qtype, "answer_type": answer_type, "time_level": time_level})
        hit_by_answer_type[answer_type]["hit"] += hit
        hit_by_answer_type[answer_type]["total"] += 1
        hit_by_qlabel[qlabel]["hit"] += hit
        hit_by_qlabel[qlabel]["total"] += 1
        if qtype == "equal":
            hit_by_equal[time_level]["hit"] += hit
            hit_by_equal[time_level]["total"] += 1
        elif qtype == "before_after":
            hit_by_before_after[time_level]["hit"] += hit
            hit_by_before_after[time_level]["total"] += 1
        elif qtype == "equal_multi":
            hit_by_equal_multi[time_level]["hit"] += hit
            hit_by_equal_multi[time_level]["total"] += 1
    print(f"Overall Hit: {sum(hit_list) * 100 / len(hit_list):.2f}% ({sum(hit_list)}/{len(hit_list)})")
    print("Hit by Answer Type:")
    for atype, stats in hit_by_answer_type.items():
        hit, total = stats["hit"], stats["total"]
        acc = hit * 100 / total if total > 0 else 0.0
        print(f"  {atype}: {acc:.2f}% ({hit}/{total})")

    # 输出按 qlabel 分类的命中率
    print("Hit by QLabel:")
    for qlabel, stats in hit_by_qlabel.items():
        hit, total = stats["hit"], stats["total"]
        acc = hit * 100 / total if total > 0 else 0.0
        print(f"  {qlabel}: {acc:.2f}% ({hit}/{total})")

    print("Hit by Equal:")
    for qlabel, stats in hit_by_equal.items():
        hit, total = stats["hit"], stats["total"]
        acc = hit * 100 / total if total > 0 else 0.0
        print(f"  {qlabel}: {acc:.2f}% ({hit}/{total})")

    print("Hit by Before_after:")
    for qlabel, stats in hit_by_before_after.items():
        hit, total = stats["hit"], stats["total"]
        acc = hit * 100 / total if total > 0 else 0.0
        print(f"  {qlabel}: {acc:.2f}% ({hit}/{total})")

    print("Hit by Equal_Multi:")
    for qlabel, stats in hit_by_equal_multi.items():
        hit, total = stats["hit"], stats["total"]
        acc = hit * 100 / total if total > 0 else 0.0
        print(f"  {qlabel}: {acc:.2f}% ({hit}/{total})")

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