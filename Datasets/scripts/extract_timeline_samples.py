import json
import random
import re
import argparse

random.seed(42)


def has_noise(question: str) -> bool:
    """
    检测问题中是否包含噪声（relation, description, category, code, semantic 等键值对）

    Args:
        question: 问题字符串

    Returns:
        True 如果包含噪声，False 否则
    """
    noise_pattern = r"\{\s*['\"]?(?:relation|description|category|code|semantic)['\"]?\s*:"
    return bool(re.search(noise_pattern, question))


def extract_samples(enable_denoise: bool = False):
    data_path = [
        '../cron/questions/test.json',
        '../icews_actor/questions/test.json'
    ]
    output_path = [
        '../cron/questions/test_1500.json',
        '../icews_actor/questions/test_1500.json'
    ]

    for i, dp in enumerate(data_path):
        with open(dp, 'r', encoding='utf-8') as f:
            datas = json.load(f)
        
        # 按类型分组
        simple_datas = [d for d in datas if d['question_level'] == 'simple']
        medium_datas = [d for d in datas if d['question_level'] == 'medium']
        complex_datas = [d for d in datas if d['question_level'] == 'complex']

        # 去噪
        if enable_denoise:
            simple_datas = [d for d in simple_datas if not has_noise(d.get('question'))]
            medium_datas = [d for d in medium_datas if not has_noise(d.get('question'))]
            complex_datas = [d for d in complex_datas if not has_noise(d.get('question'))]

        # 各选500个
        sample_num = 500
        sample_test = []
        sample_test.extend(random.sample(simple_datas, min(sample_num, len(simple_datas))))
        sample_test.extend(random.sample(medium_datas, min(sample_num, len(medium_datas))))
        sample_test.extend(random.sample(complex_datas, min(sample_num, len(complex_datas))))

        with open(output_path[i], 'w', encoding='utf-8') as of:
            json.dump(sample_test, of, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Extract timeline samples with optional denoising')
    parser.add_argument('--enable_denoise', action='store_true',
                        help='Enable denoising to skip questions with noise (relation, description, etc.)')
    args = parser.parse_args()

    extract_samples(enable_denoise=args.enable_denoise)
