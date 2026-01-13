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
from Retriever import Retrieval_BGE
from langchain_deepseek import ChatDeepSeek
from langchain.messages import SystemMessage, HumanMessage


# os.chdir(sys.path[0])  # 设置工作目录为脚本所在目录
STRUCTURED_LLM = None

class HistoricalResponse(BaseModel):
    """
    Response model for historical fact retrieval.
    """
    reason: str = Field(
        ...,
        description=(
            "Step-by-step reasoning. "
            "1. List the key time intervals extracted from facts for each entity/event in the question. "
            "2. Perform the required temporal calculation (e.g., Intersection: max(start), min(end)). "
            "3. State the result clearly. If no overlap or no matching facts, state 'No Answer'."
        )
    )
    relevant_events: List[str] = Field(
        ...,
        description=(
            "A dictionary-like list of the specific facts used to derive the answer. "
            "Filter out irrelevant noise. Only include the facts that directly contributed to the calculation."
        )
    )
    final_answer: List[str] = Field(
        ...,
        description=(
            "The final precise answer. "
            "- For Time Periods (Intersection/Duration): Return a list of TWO strings ['YYYY-MM-DD', 'YYYY-MM-DD'] representing Start and End. "
            "- For Specific Dates: Return ['YYYY-MM-DD']. "
            "- For Entities: Return a list of entity names. "
            "- If no valid answer exists (e.g., no time overlap), return ['No Answer']."
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
    human_message = f"Events:\n{fact_text}\n\nQuestion: {question}"
    messages = [SystemMessage(system_message), HumanMessage(human_message)]
    results = await STRUCTURED_LLM.ainvoke(messages)
    reason, relevant_events, final_answer = results.reason, results.relevant_events, results.final_answer
    return reason, relevant_events, final_answer

async def extract_dates(text):
    parsed_dates = []
    date_pattern = re.compile(r'\b\d{4}(?:[-\/]\d{1,2})?(?:[-\/]\d{1,2})?\b')
    matches = date_pattern.findall(text)
    for match in matches:
        try:
            dt = parser.parse(match, fuzzy=False, default=datetime(1, 1, 1))
            parsed_dates.append(dt)
        except Exception as e:
            print(f"Error parsing date '{match}': {e}")
            continue

    parsed_dates.sort()
    formatted_dates = []
    seen = set()
    for dt in parsed_dates:
        d_str = dt.strftime('%Y-%m-%d')
        if d_str not in seen:
            formatted_dates.append(d_str)
            seen.add(d_str)
            
    return formatted_dates

async def solve_single_tree(tree, idx, retriever, semaphore, sys_mes, reranker_lock):
    async with semaphore:
        try:
            sub_facts = []
            for node in tree:
                question = node["question_text"].strip()

                ref_tokens = re.findall(r"#\d+", question)
                for ref_token in ref_tokens:
                    date = None
                    ref_idx = int(ref_token[1:])
                    pre_fact = tree[ref_idx]["facts"][0]
                    if pre_fact is None:
                        continue

                    formatted_dates = await extract_dates(pre_fact)
                    if len(formatted_dates) == 1:
                        date = formatted_dates[0]
                    elif len(formatted_dates) > 1:
                        first_date, last_date = formatted_dates[0], formatted_dates[-1]
                    else:
                        continue
                    question = question.replace(ref_token, date if date else f"{first_date}~{last_date}")

                node["question"] = question

                # 检索子问题相关事件
                if "ori" in node:
                    async with reranker_lock:
                        fact_result, fact_scores = await retriever.rerank_facts(question, top_k=Config.RERANK_NUM)
                    node["facts"] = fact_result
                    sub_facts.extend(fact_result)
                else:
                    fact_text = '\n'.join(sub_facts) if sub_facts else 'No facts provided.'

                    # 用大模型来找事件
                    node['reason'], node['facts'], node['answer'] = await llm_invoke(question, sys_mes, fact_text)
                    
                    # 用 BGE 来找
                    # async with reranker_lock:
                    #     node['facts'], _ = await retriever.ori_rerank_facts(question, sub_facts)

                    # 直接取所有子问题的第一个相关事件
                    # ori_facts = []
                    # for sub_node in tree[:-1]:
                    #     ori_facts.append(sub_node['facts'][0])
                    # node['facts'] = ori_facts

        except Exception as e:
            raise e
        return tree

async def run_inference(tree_file):
    print(colored("Running Inference Engine...", "green"))
    with open(Config.KG_PATH, 'r', encoding='utf-8') as f:
        kg_list = json.load(f)
    # 初始化检索器
    retriever = Retrieval_BGE('time', Config.BGE, Config.RERANKER, kg_list, gpu_id=Config.GPU_ID)
    await retriever.load()
    
    # 加载树
    with open(tree_file, "r") as f:
        trees = json.load(f)
    
    sys_mes = load_prompt('inference')

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
                
        except KeyboardInterrupt:
            print("Interrupted by user.")
        except Exception as e:
            print(f"Pipeline failed: {e}")
            import traceback
            traceback.print_exc()

    print(f"Total time: {time.time() - start_time:.2f}s")