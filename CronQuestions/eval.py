import os, sys
import json
import time
import string
from config import args
from utils import get_result_paths
from termcolor import colored


def normalize_text(s):
    """基础文本归一化"""
    if not isinstance(s, str):
        return str(s)
    s = s.strip()
    # 移除句尾标点
    if s and s[-1] in string.punctuation:
        s = s[:-1]
    return " ".join(s.lower().split())

def normalize_prediction(prediction):
    return normalize_text(prediction)

def normalize_gold_events(gold_events):
    normalized_events = []
    for event in gold_events:
        parts = event.strip().split('|')
        if len(parts) > 4:
            subject = parts[0]
            predicate = parts[1]
            obj = parts[2]
            start_time = parts[3]
            end_time = parts[4] if len(parts) > 4 else start_time
            event_str = f"{subject} {predicate} {obj} from {start_time} to {end_time}"
            normalized_events.append(normalize_text(event_str))
    return normalized_events

def mean_reciprocal_rank(rs):
    """
    Calculate Mean Reciprocal Rank (MRR).

    Args:
    rs (list of lists): List of results for each query. Each result is a list of binary values
                        (1 if the item is relevant, 0 otherwise).

    Returns:
    float: Mean Reciprocal Rank (MRR) score.
    """

    def reciprocal_rank(r):
        """
        Calculate the reciprocal rank of a single result list.
        """
        rank = r["rank"]
        labels = r["labels"]
        # if all rank = 0, then rr = 0
        if sum(rank) == 0:
            return 0
        rr = 0
        for i, val in enumerate(rank):
            if val:
                rr += int(i / labels)

        if sum(rank) < labels:
            # punishment for not all labels are in the top k
            # we will assume then rest are all rank 31
            rr += int(31 / labels) * (labels - sum(rank))
        rr = 1 / (rr + 1)
        # print(rr, r["rank"], r["labels"])
        return rr

    return sum(reciprocal_rank(r) for r in rs) / len(rs)


def hit_n(rs, n=1):
    """
    Calculate Hit@N.
    Args:
    rs (list of lists): List of results for each query. Each result is a list of binary values
                        (1 if the item is relevant, 0 otherwise).
    n (int): The maximum rank to consider a hit.

    """

    def hit_at_n(r):
        """Calculate the hit@n of a single result list.

        If n = 1, then it is equivalent to precision@1.

        simple, medium, complex must all hit at n
        """
        rank = r["rank"]
        labels = r["labels"]
        rank = rank[: labels * n]
        if sum(rank) == labels:
            return 1
        return 0

    return sum(hit_at_n(r) for r in rs) / len(rs)

def save_failed_samples(ranks_list, results, error_file, n):
    """
    保存 Hit@N 为 0 的样本以便分析。
    """
    failed_samples = []
    
    # ranks_list 和 trees 的顺序是一一对应的 (在 evaluate 函数中是同步 append 的)
    for i, item in enumerate(ranks_list):
        rank_info = item["rank"]
        rank_binary = rank_info["rank"]
        labels = rank_info["labels"]
        
        # 使用与 hit_n 相同的逻辑判断是否失败
        cutoff = labels * n
        top_k = rank_binary[:cutoff]
        
        # 失败条件：前 k 个里面命中的数量小于预期 labels
        if sum(top_k) < labels:
            # 获取原始树信息
            result = results[i]
            
            failed_samples.append({
                "idx": i,
                "question": result['question'],
                "level": result['qlevel'],
                "labels_needed": labels,
                "hits_found": sum(top_k),
                "gold_events": result['gold_events'],
                "events": result['inference']['events'],
                "rank_binary": rank_binary, # 展示命中情况，例如 [0, 1, 0, 0]
                "cutoff_at": cutoff
            })

    with open(error_file, "w", encoding='utf-8') as f:
        json.dump(failed_samples, f, indent=2, ensure_ascii=False)

def log_metrics(ranks_list):
    levels = ["all", "simple", "medium", "complex"]
    level_to_labels = {"simple": 1, "medium": 2, "complex": 3}

    metric_results = {}
    print("-" * 60)
    for level in levels:
        if level == "all":
            # 提取所有的 rank 信息字典
            current_rs = [item["rank"] for item in ranks_list]
        else:
            target_labels = level_to_labels.get(level)
            current_rs = [
                item["rank"] 
                for item in ranks_list 
                if item["rank"]["labels"] == target_labels
            ]
        
        count = len(current_rs)
        if count == 0:
            print(f"Level: {level.capitalize():<10} | Count: 0")
            continue

        print(f"Level: {level.capitalize():<10} | Count: {count}")
        
        mrr_score = mean_reciprocal_rank(current_rs)
        hit_score = hit_n(current_rs, n=args.hit_k)

        metric_results[level] = {
            "mrr": mrr_score,
            f"hit@{args.hit_k}": hit_score
        }
        
        print(f"mrr score: {mrr_score * 100:.2f}%\nhit@{args.hit_k} score: {hit_score * 100:.2f}%")
    print("-" * 60)

    return metric_results

def evaluate(result_file, error_file, eval_log_path, total_tokens=None):
    print(colored("Evaluating Results...", "green"))
    
    with open(result_file, 'r', encoding='utf-8') as f:
        results = json.load(f)

    ranks_data = []
    valid_results = [] # 存储对应的结果用于失败分析
    for result in results:
        events = result['inference']['events']
        gold_events = result['gold_events']

        if not gold_events:
            continue

        norm_gold = set(normalize_gold_events(gold_events))
        
        # 构建 0/1 Rank 列表
        rank_binary = []
        for event in events:
            norm_fact = normalize_prediction(event)
            is_match = 0
            for g in norm_gold:
                if g in norm_fact or norm_fact in g:
                    is_match = 1
                    break
            rank_binary.append(is_match)

        real_labels_count = len(gold_events)

        ranks_data.append({
            "question": result['question'],
            "rank": {
                "rank": rank_binary,
                "labels": real_labels_count
            }
        })
        valid_results.append(result)

    save_failed_samples(ranks_data, valid_results, error_file, n=args.hit_k)

    metric_results = log_metrics(ranks_data)
    eval_result = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "config": {k: getattr(args, k) for k in [
            "top_k", "rerank_top_k", "hit_k", "llm", "dataset", "sample"
        ]},
        "metrics": {key: value for key, value in metric_results.items()},
        "total_tokens": dict(total_tokens) if total_tokens else None
    }

    # 读取已有日志
    if os.path.exists(eval_log_path):
        with open(eval_log_path, 'r') as log_f:
            eval_logs = json.load(log_f)
    else:
        eval_logs = []

    eval_logs.append(eval_result)

    with open(eval_log_path, 'w') as log_f:
        json.dump(eval_logs, log_f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    output_path, error_path, eval_log = get_result_paths(
        args.dataset,
        args.sample,
        args.suffix,
        top_k=args.top_k,
        rerank_top_k=args.rerank_top_k,
    )
    evaluate(output_path, error_path, eval_log)