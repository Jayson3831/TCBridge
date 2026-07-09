import os
import time
import json
import re
import string
from config import args
from utils import *
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

def evaluate(result_file, error_file, eval_log_path, total_tokens=None):
    print(colored("Evaluating Results...", "green"))

    with open(result_file, 'r') as f:
        results = json.load(f)

    error_results_at1 = []
    hit_at1_list = []
    hit_at10_list = []
    hit_by_answer_type_at1 = defaultdict(lambda: {"hit": 0, "total": 0})
    hit_by_answer_type_at10 = defaultdict(lambda: {"hit": 0, "total": 0})
    hit_by_qlabel_at1 = defaultdict(lambda: {"hit": 0, "total": 0})
    hit_by_qlabel_at10 = defaultdict(lambda: {"hit": 0, "total": 0})
    hit_by_equal_at1 = defaultdict(lambda: {"hit": 0, "total": 0})
    hit_by_equal_at10 = defaultdict(lambda: {"hit": 0, "total": 0})
    hit_by_before_after_at1 = defaultdict(lambda: {"hit": 0, "total": 0})
    hit_by_before_after_at10 = defaultdict(lambda: {"hit": 0, "total": 0})
    hit_by_equal_multi_at1 = defaultdict(lambda: {"hit": 0, "total": 0})
    hit_by_equal_multi_at10 = defaultdict(lambda: {"hit": 0, "total": 0})
    print(len(results))

    for result in results:
        predictions = result["inference"]["answers"]
        gold = result["gold_answers"]
        qlabel = result["qlabel"]
        qtype = result["qtype"]
        answer_type = result["answer_type"]
        time_level = result["time_level"]

        # Hit@1 和 Hit@10 同时计算
        hit1 = eval_hit(predictions[:1], gold)
        hit10 = eval_hit(predictions[:10], gold)

        if hit1 == 0:
            error_results_at1.append(result)

        hit_at1_list.append(hit1)
        hit_at10_list.append(hit10)

        hit_by_answer_type_at1[answer_type]["hit"] += hit1
        hit_by_answer_type_at1[answer_type]["total"] += 1
        hit_by_answer_type_at10[answer_type]["hit"] += hit10
        hit_by_answer_type_at10[answer_type]["total"] += 1

        hit_by_qlabel_at1[qlabel]["hit"] += hit1
        hit_by_qlabel_at1[qlabel]["total"] += 1
        hit_by_qlabel_at10[qlabel]["hit"] += hit10
        hit_by_qlabel_at10[qlabel]["total"] += 1

        if qtype == "equal":
            hit_by_equal_at1[time_level]["hit"] += hit1
            hit_by_equal_at1[time_level]["total"] += 1
            hit_by_equal_at10[time_level]["hit"] += hit10
            hit_by_equal_at10[time_level]["total"] += 1
        elif qtype == "before_after":
            hit_by_before_after_at1[time_level]["hit"] += hit1
            hit_by_before_after_at1[time_level]["total"] += 1
            hit_by_before_after_at10[time_level]["hit"] += hit10
            hit_by_before_after_at10[time_level]["total"] += 1
        elif qtype == "equal_multi":
            hit_by_equal_multi_at1[time_level]["hit"] += hit1
            hit_by_equal_multi_at1[time_level]["total"] += 1
            hit_by_equal_multi_at10[time_level]["hit"] += hit10
            hit_by_equal_multi_at10[time_level]["total"] += 1

    def print_section(title, at1_dict, at10_dict):
        print(title)
        for key in at1_dict:
            h1, t1 = at1_dict[key]["hit"], at1_dict[key]["total"]
            h10, t10 = at10_dict[key]["hit"], at10_dict[key]["total"]
            acc1 = h1 * 100 / t1 if t1 > 0 else 0.0
            acc10 = h10 * 100 / t10 if t10 > 0 else 0.0
            at1_dict[key]['acc'] = f"{acc1:.2f}%"
            at10_dict[key]['acc'] = f"{acc10:.2f}%"
            print(f"  {key}: Hit@1={acc1:.2f}% ({h1}/{t1})  Hit@10={acc10:.2f}% ({h10}/{t10})")

    overall_hit1 = sum(hit_at1_list) * 100 / len(hit_at1_list)
    overall_hit10 = sum(hit_at10_list) * 100 / len(hit_at10_list)
    print(f"Overall: Hit@1={overall_hit1:.2f}% ({sum(hit_at1_list)}/{len(hit_at1_list)})  Hit@10={overall_hit10:.2f}% ({sum(hit_at10_list)}/{len(hit_at10_list)})")

    print_section("By Answer Type:", hit_by_answer_type_at1, hit_by_answer_type_at10)
    print_section("By QLabel:", hit_by_qlabel_at1, hit_by_qlabel_at10)
    print_section("By Equal:", hit_by_equal_at1, hit_by_equal_at10)
    print_section("By Before_after:", hit_by_before_after_at1, hit_by_before_after_at10)
    print_section("By Equal_Multi:", hit_by_equal_multi_at1, hit_by_equal_multi_at10)

    with open(error_file, 'w') as ef:
        json.dump(error_results_at1, ef, ensure_ascii=False, indent=4)

    # 构建结果字典
    eval_result = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "config": {k: getattr(args, k) for k in [
            "top_k", "conf_threshold", "entropy_threshold", "llm", "dataset", "sample"
        ]},
        "overall_hit_at1": f"{overall_hit1:.2f}%",
        "overall_hit_at10": f"{overall_hit10:.2f}%",
        "hit_by_answer_type_at1": dict(hit_by_answer_type_at1),
        "hit_by_answer_type_at10": dict(hit_by_answer_type_at10),
        "hit_by_qlabel_at1": dict(hit_by_qlabel_at1),
        "hit_by_qlabel_at10": dict(hit_by_qlabel_at10),
        "hit_by_equal_at1": dict(hit_by_equal_at1),
        "hit_by_equal_at10": dict(hit_by_equal_at10),
        "hit_by_before_after_at1": dict(hit_by_before_after_at1),
        "hit_by_before_after_at10": dict(hit_by_before_after_at10),
        "hit_by_equal_multi_at1": dict(hit_by_equal_multi_at1),
        "hit_by_equal_multi_at10": dict(hit_by_equal_multi_at10),
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