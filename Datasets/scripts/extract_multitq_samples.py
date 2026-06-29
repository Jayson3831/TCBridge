import json
import random

# 设置随机种子
random.seed(42)

def extract_samples():
    """从test.json中提取满足多种条件的样本"""

    # 加载原始数据
    input_path = '../multitq/questions/test.json'
    with open(input_path, 'r', encoding='utf-8') as f:
        all_data = json.load(f)

    print(f"Total questions in original file: {len(all_data)}")

    sample_num = 500
    collected_samples = {}  # 存储已采样的样本，key为question
    category_samples = {}   # 存储每个类别的样本列表

    # 步骤1: 先采样 answer_type=entity 和 answer_type=time
    print("\n" + "="*50)
    print("Step 1: Sampling answer_type conditions")
    print("="*50)

    for answer_type in ["entity", "time"]:
        print(f"\n[{answer_type}] Filtering...")
        filtered = [item for item in all_data if item.get('answer_type') == answer_type]
        print(f"  Found {len(filtered)} samples")

        # 从过滤结果中排除已采样的
        available = [item for item in filtered if item.get('question') not in collected_samples]
        print(f"  Available after deduplication: {len(available)}")

        # 采样500个
        target_count = min(sample_num, len(available))
        sampled = random.sample(available, target_count)

        for item in sampled:
            collected_samples[item['question']] = item
            category_name = f"answer_type_{answer_type}"
            if category_name not in category_samples:
                category_samples[category_name] = []
            category_samples[category_name].append(item)

        print(f"  Sampled {len(sampled)} samples")

    # 步骤2: 计算已采样中满足 qlabel 条件的个数，不足则继续采样
    print("\n" + "="*50)
    print("Step 2: Checking and supplementing qlabel conditions")
    print("="*50)

    for qlabel in ["Single", "Multiple"]:
        category_name = f"qlabel_{qlabel}"
        print(f"\n[{qlabel}] Checking...")

        # 统计已采样中满足条件的个数
        existing = [item for item in collected_samples.values() if item.get('qlabel') == qlabel]
        existing_count = len(existing)
        print(f"  Existing samples: {existing_count}/{sample_num}")

        # 初始化类别样本
        if category_name not in category_samples:
            category_samples[category_name] = []

        # 添加已存在的样本到类别
        for item in existing:
            category_samples[category_name].append(item)

        if existing_count < sample_num:
            need_count = sample_num - existing_count
            print(f"  Need {need_count} more samples")

            # 从剩余数据中采样
            filtered = [item for item in all_data if item.get('qlabel') == qlabel]
            available = [item for item in filtered if item.get('question') not in collected_samples]
            print(f"  Available candidates: {len(available)}")

            actual_count = min(need_count, len(available))
            if actual_count > 0:
                sampled = random.sample(available, actual_count)
                for item in sampled:
                    collected_samples[item['question']] = item
                    category_samples[category_name].append(item)
                print(f"  Supplement sampled {len(sampled)} samples")

    # 合并所有样本
    all_collected = list(collected_samples.values())

    # 输出统计
    print("\n" + "="*50)
    print(f"Total unique samples: {len(all_collected)}")
    print("="*50)

    # 保存结果
    output_path = f'../multitq/questions/test_{len(all_collected)}.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(all_collected, f, ensure_ascii=False, indent=4)

    print(f"\nSaved to: {output_path}")

    # 打印每个条件的实际样本数
    print("\n" + "="*50)
    print("Actual sample count per category:")
    for category_name in ["answer_type_entity", "answer_type_time", "qlabel_Single", "qlabel_Multiple"]:
        count = len(category_samples.get(category_name, []))
        print(f"  {category_name}: {count}/{sample_num}")
    print("="*50)


if __name__ == "__main__":
    extract_samples()
