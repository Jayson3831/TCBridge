import os, sys
import json
import re
import string
from config import Config
from collections import defaultdict
from termcolor import colored


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
    print(colored("Step 3: Evaluating Results...", "green"))
    
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
        topk_pred = topk(normalized_pred, 10)
        
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
    evaluate(Config.RESULT_FILE)