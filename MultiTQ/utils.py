import os
import json
import numpy as np
from openai import AsyncOpenAI
from dateutil import parser
from datetime import datetime
from config import args
from typing import Optional, List, Dict

client = AsyncOpenAI(api_key=args.api_key, base_url=args.base_url, max_retries=2, timeout=120.0)

async def llm_invoke(messages: List[Dict], total_tokens: Dict[str, int]):
    response = await client.chat.completions.create(
        model=args.llm,
        messages=messages,
        temperature=args.temperature,
        max_tokens=args.max_length,
        timeout=120,
        response_format={
            'type': 'json_object'
        }
    )
    try:
        # 获取结构化输出
        response_json = json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"LLM Invoke Error: {e}")
        print(f"Problematic content: {messages[-1]['content'][:200]}...")
        response_json = {}

    # 统计token用量
    total_tokens['completion'] += response.usage.completion_tokens
    total_tokens['prompt'] += response.usage.prompt_tokens
    total_tokens['total'] += response.usage.total_tokens

    return response_json

async def tcbridge_module(ref_tokens, curq, allq, retriever, reranker_lock):
    # 逐一处理所有占位符
    for ref_token in ref_tokens:
        ref_idx = int(ref_token[1:])
        if ref_idx < 0 or ref_idx > len(allq):
            continue

        ref_subq = next((subq for subq in allq if subq['subq_idx'] == ref_idx), allq[ref_idx - 1])
        refq = ref_subq['best_subq']
        ref_facts = ref_subq['facts']

        # 找到替换占位符的最佳时间
        async with reranker_lock:
            result = await retriever.rerank_facts(refq, ref_facts, rerank_top_k=args.rerank_top_k)
        reranked_facts = result['facts']
        reranked_scores = result['scores']
        ref_subq['top1_fact'] = [reranked_facts[0]]
        ref_subq['top1_score'] = [reranked_scores[0]]

        # 替换占位符
        relevant_date = parse_date_string(ref_facts[0]) if ref_facts else None
        if relevant_date:
            curq = curq.replace(ref_token, relevant_date)

    return curq

async def bridge_module(ref_tokens, curq, allq, retriever, reranker_lock):
    for ref_token in ref_tokens:
        ref_idx = int(ref_token[1:])
        if ref_idx < 0 or ref_idx > len(allq):
            continue

        ref_subq = next((subq for subq in allq if subq['subq_idx'] == ref_idx), allq[ref_idx - 1])
        refq = ref_subq['best_subq']
        ref_facts = ref_subq['facts']
        ref_scores = ref_subq['similarities']

        # 计算置信度和全局熵，决定是否采用精排。
        if ref_scores and len(ref_scores) > 1:
            f_conf, f_entropy = calculate_metrics(ref_scores, args.temp)

            if f_conf > args.conf_threshold and f_entropy < args.entropy_threshold:
                top_facts = ref_facts
                top_scores = ref_scores
            else:
                async with reranker_lock:
                    reranked = await retriever.rerank_facts(refq, ref_facts, rerank_top_k=args.rerank_top_k)
                top_facts = reranked['facts']
                top_scores = reranked['scores']

        # 语义重构（替换占位符）
        relevant_date = parse_date_string(top_facts[0]) if ref_facts else None
        if relevant_date:
            curq = curq.replace(ref_token, relevant_date)

    return curq

def calculate_metrics(scores, temp=1.0):
    if not scores or len(scores) < 2:
        return 1.0, 0.0
    
    scores = np.array(scores)
    # 1. Softmax & Entropy
    exp_scores = np.exp((scores - np.max(scores)) / temp)
    probs = exp_scores / np.sum(exp_scores)
    entropy = -np.sum(probs * np.log(probs + 1e-9))
    h_norm = entropy / np.log(len(scores))

    # 2. Confidence
    delta_s = scores[0] - scores[1]
    conf = 1 / (1 + np.exp(-delta_s)) # Sigmoid

    return conf, h_norm

async def tc_rerank(question, events, time_constraint):
    """
    time_constraint: 'before', 'after', or None
    """
    main_date = parse_date_string(question)
    if not main_date:
        return events   # 无法解析日期时返回原列表

    tc_events = []
    for event in events:
        event_date = parse_date_string(event)
        if not event_date:
            continue

        if time_constraint == 'before' and event_date < main_date:
            tc_events.append(event)
        elif time_constraint == 'after' and event_date > main_date:
            tc_events.append(event)

    return tc_events

def parse_date_string(date_str: str) -> Optional[str]:
    """解析日期字符串为 YYYY-MM-DD 格式"""
    try:
        dt = parser.parse(date_str, fuzzy=True, default=datetime(1, 1, 1))
        return dt.strftime('%Y-%m-%d')
    except (ValueError, TypeError):
        return None

def get_result_paths(dataset, sample, suffix, **kwargs):
    """生成结果文件路径"""
    param_parts = []
    for key, value in kwargs.items():
        if value is not None and value != getattr(args, '_default_' + key, None):
            param_parts.append(f"{key}={value}")

    param_suffix = "_".join(param_parts)
    if param_suffix:
        param_suffix = "_" + param_suffix

    if suffix:
        param_suffix += "_" + suffix

    output_path = f"outputs/{dataset}_{args.dataset_type}_{sample}{param_suffix}.json"
    error_path = f"errors/{dataset}_{args.dataset_type}_{sample}{param_suffix}.json"
    result_path = f"results/{dataset}_{args.dataset_type}_{sample}{param_suffix}.json"

    return output_path, error_path, result_path