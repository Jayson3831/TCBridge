import os, sys
import json
import re
import string
from config import Config
from collections import defaultdict
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
        if len(parts) >= 4:
            subject = parts[0]
            predicate = parts[1]
            obj = parts[2]
            start_time = parts[3]
            end_time = parts[4] if len(parts) > 4 else start_time
            
            if start_time == end_time:
                event_str = f"{subject} {predicate} {obj} on {start_time}"
            else:
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

def save_failed_samples(ranks_list, trees, n=1, output_file=Config.ANALYSIS_FILE):
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
            tree = trees[i]
            node = tree[-1] # 根节点
            
            failed_samples.append({
                "idx": i,
                "question": node.get("question_text", ""), # 注意有些文件字段是 question_text
                "level": node.get("question_level", "unknown"),
                "labels_needed": labels,
                "hits_found": sum(top_k),
                "gold_events": node.get("events"),
                "facts": node.get("facts"), # 虽然 facts 是全量，这里只展示前k个相关的
                "rank_binary": rank_binary, # 展示命中情况，例如 [0, 1, 0, 0]
                "cutoff_at": cutoff
            })

    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w", encoding='utf-8') as f:
        json.dump(failed_samples, f, indent=2, ensure_ascii=False)
    
    print(colored(f"Saved {len(failed_samples)} failed samples (Hit@{n}=0) to {output_file}", "yellow"))


def log_metrics(ranks_list):
    metrics = ["mrr", "hit_1", "hit_3", "hit_5", "hit_10"]
    levels = ["all", "simple", "medium", "complex"]
    level_to_labels = {"simple": 1, "medium": 2, "complex": 3}

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
        
        results_str = []
        for metric in metrics:
            if metric == "mrr":
                score = mean_reciprocal_rank(current_rs)
            else:
                n = int(metric.split("_")[1])
                score = hit_n(current_rs, n=n)
            results_str.append(f"{metric.upper()}: {score:.4f}")
        
        print("  " + " | ".join(results_str))
    print("-" * 60)

def evaluate(result_file):
    print(colored("Evaluating Results...", "green"))
    
    with open(result_file, 'r', encoding='utf-8') as f:
        trees = json.load(f)

    ranks_data = []
    valid_trees = [] # 存储对应的 tree 数据用于失败分析
    level_map = {"simple": 1, "medium": 2, "complex": 3}
    for tree in trees:
        node = tree[-1]
        gold_events = node.get('events', [])
        retrieved_facts = node.get('facts', [])

        if not gold_events:
            continue

        norm_gold = set(normalize_gold_events(gold_events))
        
        # 构建 0/1 Rank 列表
        rank_binary = []
        for fact in retrieved_facts:
            norm_fact = normalize_prediction(fact)
            is_match = 0
            for g in norm_gold:
                if g in norm_fact or norm_fact in g:
                    is_match = 1
                    break
            rank_binary.append(is_match)

        real_labels_count = len(gold_events)

        ranks_data.append({
            "question": node.get('question'),
            "rank": {
                "rank": rank_binary,
                "labels": real_labels_count
            }
        })
        valid_trees.append(tree)

    log_metrics(ranks_data)

    save_failed_samples(ranks_data, valid_trees, n=1, output_file=Config.ANALYSIS_FILE)


if __name__ == "__main__":
    evaluate(Config.RESULT_FILE)