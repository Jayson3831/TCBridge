import os
import time
import json
import re
import string
from config import args
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

def evaluate(result_file, error_file, total_tokens=None):
    print(colored("Evaluating Results...", "green"))
    
    with open(result_file, 'r') as f:
        results = json.load(f)
        
    error_results = []
    hit_list = []
    hit_by_answer_type = defaultdict(lambda: {"hit": 0, "total": 0})
    hit_by_qlabel = defaultdict(lambda: {"hit": 0, "total": 0})
    hit_by_equal = defaultdict(lambda: {"hit": 0, "total": 0})
    hit_by_before_after = defaultdict(lambda: {"hit": 0, "total": 0})
    hit_by_equal_multi = defaultdict(lambda: {"hit": 0, "total": 0})
    print(len(results))

    for result in results:
        predictions = result["inference"]["answers"]
        topk_preds = predictions[:args.hit_k]

        gold = result["gold_answers"]
        qlabel = result["qlabel"]
        qtype = result["qtype"]
        answer_type = result["answer_type"]
        time_level = result["time_level"]
        hit = eval_hit(topk_preds, gold)

        if hit == 0:
            error_results.append(result)

        hit_list.append(hit)
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
        stats['acc'] = f"{acc:.2f}%"
        print(f"  {atype}: {acc:.2f}% ({hit}/{total})")

    # 输出按 qlabel 分类的命中率
    print("Hit by QLabel:")
    for qlabel, stats in hit_by_qlabel.items():
        hit, total = stats["hit"], stats["total"]
        acc = hit * 100 / total if total > 0 else 0.0
        stats['acc'] = f"{acc:.2f}%"
        print(f"  {qlabel}: {acc:.2f}% ({hit}/{total})")

    print("Hit by Equal:")
    for qlabel, stats in hit_by_equal.items():
        hit, total = stats["hit"], stats["total"]
        acc = hit * 100 / total if total > 0 else 0.0
        stats['acc'] = f"{acc:.2f}%"
        print(f"  {qlabel}: {acc:.2f}% ({hit}/{total})")

    print("Hit by Before_after:")
    for qlabel, stats in hit_by_before_after.items():
        hit, total = stats["hit"], stats["total"]
        acc = hit * 100 / total if total > 0 else 0.0
        stats['acc'] = f"{acc:.2f}%"
        print(f"  {qlabel}: {acc:.2f}% ({hit}/{total})")

    print("Hit by Equal_Multi:")
    for qlabel, stats in hit_by_equal_multi.items():
        hit, total = stats["hit"], stats["total"]
        acc = hit * 100 / total if total > 0 else 0.0
        stats['acc'] = f"{acc:.2f}%"
        print(f"  {qlabel}: {acc:.2f}% ({hit}/{total})")

    with open(error_file, 'w') as ef:
        json.dump(error_results, ef, ensure_ascii=False, indent=4)

    # 构建结果字典
    eval_result = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "overall_hit": f"{sum(hit_list) * 100 / len(hit_list):.2f}%",
        "hit_by_answer_type": dict(hit_by_answer_type),
        "hit_by_qlabel": dict(hit_by_qlabel),
        "hit_by_equal": dict(hit_by_equal),
        "hit_by_before_after": dict(hit_by_before_after),
        "hit_by_equal_multi": dict(hit_by_equal_multi),
        "total_tokens": dict(total_tokens) if total_tokens else None
    }

    # 追加到评估日志文件
    eval_log_path = f"results/{args.dataset}_test_{args.sample}_eval_log.json"

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
    result_path = f"results/{args.dataset}_test_{args.sample}_results.json"
    error_file = f"results/{args.dataset}_test_{args.sample}_errors.json"
    evaluate(result_path, error_file)