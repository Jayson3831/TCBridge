import os
import json
from openai import OpenAI
from dateutil import parser
from datetime import datetime
from config import args
from typing import Optional, List, Dict

client = OpenAI(api_key=args.api_key, base_url=args.base_url, max_retries=2)

async def llm_invoke(messages: List[Dict], total_tokens: Dict[str, int]):
    response = client.chat.completions.create(
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

        # 统计token用量
        total_tokens['completion'] += response.usage.completion_tokens
        total_tokens['prompt'] += response.usage.prompt_tokens
        total_tokens['total'] += response.usage.total_tokens
    except json.JSONDecodeError as e:
        raise e

    return response_json

async def tcbridge_module(ref_tokens, curq, allq, retriever, reranker_lock):
    # 逐一处理所有占位符
    for ref_token in ref_tokens:
        ref_idx = int(ref_token[1:])
        for subq in allq:
            idx = subq['subq_idx']
            if ref_idx == idx:
                refq = subq['best_subq']
                ref_facts = subq['facts']
                break
        if not refq:
            refq = allq[ref_idx - 1]['best_subq']
            ref_facts = allq[ref_idx - 1]['facts']

        # 找到替换占位符的最佳时间
        async with reranker_lock:
            ref_facts = await retriever.rerank_facts(refq, ref_facts, rerank_top_k=args.rerank_top_k)
        relevant_date = parse_date_string(ref_facts[0]) if ref_facts else None

        if relevant_date:
            curq = curq.replace(ref_token, relevant_date)

    return curq

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

