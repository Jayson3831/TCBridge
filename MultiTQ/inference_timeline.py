import os
import re
import json
import time
import string
import asyncio
from config import Config
from datetime import datetime
from collections import defaultdict
from typing import Optional, List
from tqdm.asyncio import tqdm_asyncio
from pydantic import BaseModel, Field
from termcolor import colored
from dateutil import parser
from Retriever import Retrieval_BGE
from langchain_deepseek import ChatDeepSeek
from langchain.messages import SystemMessage, HumanMessage


STRUCTURED_LLM = None

# ==================== 响应模型 ====================

class HistoricalResponse(BaseModel):
    """Response model for historical fact retrieval."""

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


# ==================== 工具函数 ====================

def load_prompt(key: str) -> str:
    """加载 prompt 模版"""
    path = Config.PROMPT_PATHS.get(key)
    if path and os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return '\n'.join([l.strip() for l in f.readlines()])
    return ""


async def llm_invoke(question: str, sys_mes: str, fact_text: str) -> List[str]:
    """调用 LLM 生成答案"""
    messages = [
        SystemMessage(sys_mes),
        HumanMessage(f"Relevant facts:\n{fact_text}\n\nQuestion: {question}")
    ]
    results = await STRUCTURED_LLM.ainvoke(messages)
    return results.final_answer


async def get_facts_from_faiss(question: str, retriever, sys_mes: str, n: int = 15):
    """从 FAISS 检索事实并调用 LLM"""
    fact_result = await retriever.get_faiss_similarity(question, n)
    fact_list = fact_result.get('fact', [])
    fact_text = '\n'.join(fact_list) if fact_list else 'No facts provided.'

    messages = [
        SystemMessage(sys_mes),
        HumanMessage(f"Historical facts:\n{fact_text}\n\nQuestion: {question}")
    ]
    results = await STRUCTURED_LLM.ainvoke(messages)
    return results.final_answer, fact_text


# ==================== 辅助函数 ====================

def parse_date_string(date_str: str) -> Optional[str]:
    """解析日期字符串为 YYYY-MM-DD 格式"""
    try:
        dt = parser.parse(date_str, fuzzy=True, default=datetime(1, 1, 1))
        return dt.strftime('%Y-%m-%d')
    except (ValueError, TypeError):
        return None


async def extract_most_relevant_date(date_strings) -> Optional[str]:
    """
    从事实列表中提取最相关日期（第一个可解析的日期）
    Returns:
        YYYY-MM-DD 格式的日期或 None
    """
    for date_str in date_strings:
        fact_date = parse_date_string(date_str)
        if fact_date:
            return fact_date
    return None


def _get_comparison_type(question: str) -> Optional[str]:
    """从问题中提取时间比较类型"""
    question_lower = question.lower()
    if "before" in question_lower:
        return 'before'
    elif "after" in question_lower:
        return 'after'
    return None


def filter_facts_by_time(facts: List[str], ref_date: str, comparison_type: str, max_count: int = 35) -> List[str]:
    """
    根据时间过滤事实（单次遍历优化）
    Args:
        facts: 事实列表
        ref_date: 参考日期（YYYY-MM-DD）
        comparison_type: 'before' | 'after'
        max_count: 最多返回多少条
    Returns:
        过滤后的事实列表
    """
    if not ref_date or comparison_type not in ('before', 'after'):
        return facts[:max_count]

    filtered = []
    for fact in facts:
        fact_date = parse_date_string(fact)
        if not fact_date:
            continue
        if comparison_type == 'before' and fact_date < ref_date:
            filtered.append(fact)
        elif comparison_type == 'after' and fact_date > ref_date:
            filtered.append(fact)
    return filtered[:max_count]


# ==================== 推理引擎 ====================

async def solve_single_tree(tree, retriever, semaphore, sys_mes, reranker_lock):
    """处理单个问题树的推理"""
    async with semaphore:
        try:
            # 解析问题中的日期（用于没有占位符的 Target）
            ori_node = tree[-1]
            q_date = parse_date_string(ori_node["question_text"])

            # 预查找 Anchor 节点索引，避免在 Target 中重复查找
            anchor_indices = {i for i, node in enumerate(tree) if node.get("type") == "Anchor"}

            for node in tree:
                question = node["question_text"].strip()
                node_type = node.get("type", "")
                node_idx = node["idx"]

                if node_type == "Anchor":
                    # Anchor 子问题的处理逻辑
                    async with reranker_lock:
                        fact_result, _ = await retriever.rerank_facts(question, top_k=Config.RERANK_NUM)

                    node["facts"] = fact_result
                    node["most_relevant_date"] = await extract_most_relevant_date(fact_result)

                elif node_type == "Target":
                    # Target 子问题的处理逻辑
                    # 查前置 Anchor 节点
                    anchor_node = None
                    for i in range(node_idx - 1, -1, -1):
                        if i in anchor_indices:
                            anchor_node = tree[i]
                            break

                    # 判断是否有占位符
                    has_placeholder = bool(re.search(r"#t\b", question))

                    if has_placeholder and anchor_node:
                        replacement_date = anchor_node.get("most_relevant_date")
                        if not replacement_date:
                            print(f"Warning: No replacement date found for {question[:50]}...")
                            facts_result = await retriever.get_faiss_similarity(question, n=Config.FACTS_NUM)
                            facts = facts_result.get('fact', []) if isinstance(facts_result, dict) else []
                        else:
                            # 替换占位符并检索
                            modified_question = re.sub(r"#t\b", replacement_date, question)
                            facts_result = await retriever.get_faiss_similarity(modified_question, n=Config.FACTS_NUM)
                            facts = facts_result.get('fact', []) if isinstance(facts_result, dict) else []

                        # 时间过滤
                        comparison_type = _get_comparison_type(modified_question)
                        facts = filter_facts_by_time(facts, replacement_date, comparison_type, max_count=25)

                    elif anchor_node:
                        # 没有占位符，使用 Anchor 的事实
                        facts = anchor_node.get('facts', [])
                    else:
                        # 没有 Anchor 节点，直接检索
                        facts_result = await retriever.get_faiss_similarity(question, n=Config.FACTS_NUM)
                        facts = facts_result.get('fact', []) if isinstance(facts_result, dict) else []

                        if q_date:
                            comparison_type = _get_comparison_type(question)
                            facts = filter_facts_by_time(facts, q_date, comparison_type, max_count=35)

                    fact_text = '\n'.join(facts) if facts else 'No facts provided.'
                    node['facts'] = facts
                    node['answer'] = await llm_invoke(question, sys_mes, fact_text)
                else:
                    # 其他类型节点，使用前一个节点的答案
                    answer = tree[node_idx - 1]['answer'] if node_idx > 0 else None
                    if not answer:
                        node['answer'], node['facts'] = await get_facts_from_faiss(question, retriever, sys_mes, n=Config.FACTS_NUM)
                    else:
                        node['answer'] = answer

                node['question'] = question

        except Exception as e:
            raise e
        return tree


async def run_inference(tree_file: str) -> str:
    """运行推理引擎"""
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
    reranker_lock = asyncio.Lock()
    tasks = []
    for tree in trees:
        task = asyncio.create_task(solve_single_tree(tree, retriever, semaphore, sys_mes, reranker_lock))
        tasks.append(task)

    results = []
    for task in tqdm_asyncio(asyncio.as_completed(tasks), total=len(tasks), desc="Inferencing"):
        res = await task
        results.append(res)

    # 保存结果
    os.makedirs(os.path.dirname(Config.RESULT_FILE), exist_ok=True)
    with open(Config.RESULT_FILE, "w") as f:
        json.dump(results, f, indent=2)

    print(f"Inference done. Results saved to {Config.RESULT_FILE}")
    return Config.RESULT_FILE


# ==================== 评估函数 ====================

def normalize_text(s: str) -> str:
    """文本标准化"""
    s = str(s).lower()
    exclude = set(string.punctuation)
    s = "".join(char for char in s if char not in exclude)
    s = re.sub(r"\b(a|an|the)\b", " ", s)
    return " ".join(s.split())


def normalize_prediction(prediction):
    """预测结果标准化"""
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


def topk(prediction, k: int = -1):
    """取前 k 个预测结果"""
    if isinstance(prediction, list):
        return prediction[:k]
    elif isinstance(prediction, str):
        return [prediction]
    elif isinstance(prediction, (int, float)):
        return [str(prediction)]
    else:
        raise ValueError(f"Unsupported prediction type: {type(prediction)}")


def eval_hit(prediction, answers) -> int:
    """评估命中"""
    if not isinstance(answers, list):
        answers = [answers]
    pred_norm = normalize_text(prediction)
    for ans in answers:
        if normalize_text(ans) in pred_norm:
            return 1
    return 0


def evaluate(result_file: str):
    """评估结果"""
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

    for tree in trees:
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

    # 输出统计结果
    print(f"Total trees: {len(trees)}")
    print(f"Overall Hit: {sum(hit_list) * 100 / len(hit_list):.2f}% ({sum(hit_list)}/{len(hit_list)})")

    print("Hit by Answer Type:")
    for atype, stats in hit_by_answer_type.items():
        hit, total = stats["hit"], stats["total"]
        acc = hit * 100 / total if total > 0 else 0.0
        print(f"  {atype}: {acc:.2f}% ({hit}/{total})")

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

    # 保存错误分析
    json.dump(q2a, open(Config.Q2A_FILE, "w"), indent=2)
    output_path = Config.Q2A_FULL_FILE
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(q2a_trees, f, indent=2, ensure_ascii=False)


# ==================== 主入口 ====================

if __name__ == "__main__":
    start_time = time.time()

    # 初始化 LLM
    LLM = ChatDeepSeek(
        model=Config.LLM,
        api_key=Config.API_KEY,
        temperature=0.0,
        max_tokens=8192,
        timeout=120,
        max_retries=2
    )
    STRUCTURED_LLM = LLM.with_structured_output(HistoricalResponse)

    tree_file = Config.SUBQ_FORMATTED_FILE

    if tree_file and os.path.exists(tree_file):
        try:
            # 运行推理
            result_file = asyncio.run(run_inference(tree_file))

            # 评估结果
            if result_file:
                evaluate(result_file)

        except KeyboardInterrupt:
            print("Interrupted by user.")
        except Exception as e:
            print(f"Pipeline failed: {e}")
            import traceback
            traceback.print_exc()

    print(f"\nTotal time: {time.time() - start_time:.2f}s")
