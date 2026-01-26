import json
import os
import re
import time
import random
import atexit
import multiprocessing
from multiprocessing import Pool
import torch
import torch.nn.functional as F
import torch.nn as nn
from typing import Annotated, Any, Dict, List
from dateutil import parser
from tqdm import tqdm
from termcolor import colored
from openai import OpenAI
from sentence_transformers import SentenceTransformer
import os, sys
from config import Config
from pydantic import BaseModel, Field
from langchain_deepseek import ChatDeepSeek


os.chdir(sys.path[0])
random.seed(42)


class ConcatBCEClassifier(nn.Module):
    """将 q_emb 与 s_emb 拼接后，通过MLP输出单logit。"""
    def __init__(self, embedding_dim: int, dropout: float = Config.DROPOUT):
        super().__init__()
        in_dim = embedding_dim * 2
        self.net = nn.Sequential(
            nn.Linear(in_dim, 128),
            nn.LayerNorm(128),
            nn.ReLU(),
            # nn.Dropout(dropout),
            # nn.Linear(512, 1),  # 单logit
        )
        self.classifier = nn.Linear(128 + 1, 1) # +1 是为了拼接余弦相似度

    def forward(self, q_emb: torch.Tensor, s_emb: torch.Tensor, batch_cosine: torch.Tensor) -> torch.Tensor:
        if q_emb.dim() == 1:
            q_emb = q_emb.unsqueeze(0)
        if s_emb.dim() == 1:
            s_emb = s_emb.unsqueeze(0)
        x = torch.cat([q_emb, s_emb], dim=-1)
        fea = self.net(x).squeeze(-1)

        # add cosine
        batch_cosine = batch_cosine.unsqueeze(1)
        combined = torch.cat([fea, batch_cosine], dim=1)
        # 最终决策
        logit = self.classifier(combined).squeeze()

        return logit


class BestSubquestionSelector:
    def __init__(self, model, device, encoder, normalize=True, encode_bs=64):
        """
        model: 你已有的下游模型 (callable: model(q, s, cosine) -> logits)
        device: torch.device，例如 torch.device("cuda") 或 torch.device("cpu")
        encoder_path: 本地 sentence-transformers 模型路径
        normalize: 是否对句向量做 L2 归一化；为 True 时 cos 更稳定
        encode_bs: 计算嵌入时的 batch size
        """
        self.model = model
        self.device = device
        self.encoder = encoder
        self.normalize = normalize
        self.encode_bs = encode_bs

    @torch.no_grad()
    def _encode(self, texts):
        # 返回 [len(texts), dim] 的 tensor，放到 self.device 上
        emb = self.encoder.encode(
            texts,
            batch_size=self.encode_bs,
            convert_to_tensor=True,
            normalize_embeddings=self.normalize,
            show_progress_bar=False
        )
        return emb.to(self.device)

    @torch.no_grad()
    def select_batch(self, questions, subquestions_list):
        """
        questions: List[str]，长度为 N
        subquestions_list: List[List[str]]，形如 [[s1,s2,s3], [s1,s2,s3], ...]，长度为 N，每个内部长度=3
        返回:
          best_subqs: List[str]，每个问题对应的最佳 subquestion 文本
          best_idx:  LongTensor [N]，每个问题最佳 subquestion 的索引(0..2)
          logits_grouped: FloatTensor [N,3]，每个问题的三个 logits
        """
        assert len(questions) == len(subquestions_list), "questions 与 subquestions_list 的长度必须一致"
        N = len(questions)
        if N == 0:
            return [], torch.empty(0, dtype=torch.long), torch.empty(0, 3)

        # 1) 计算文本 embedding
        q_emb = self._encode(questions)                 # [N, d]
        flat_subqs = [sq for trio in subquestions_list for sq in trio]  # 按问题顺序展平
        s_emb = self._encode(flat_subqs)                # [N*3, d]

        # 2) 将 q_emb 按每个问题重复 3 次，与 s_emb 对齐
        q_emb_rep = q_emb.repeat_interleave(3, dim=0)   # [N*3, d]

        # 3) 计算 cos(q_i, s_i)（一一配对）
        cosine = F.cosine_similarity(q_emb_rep, s_emb, dim=1)  # [N*3]

        # 4) 喂入你的模型，拿到逐对 logits
        logits = self.model(q_emb_rep, s_emb, cosine)          # 期望 [N*3] 或 [N*3,1]
        if logits.dim() == 2 and logits.size(1) == 1:
            logits = logits.squeeze(1)
        else:
            logits = logits.view(-1)                           # 保底展平成 [N*3]

        # 5) 还原为 [N,3]，并取每行 argmax
        logits_grouped = logits.view(N, 3)                     # [N, 3]
        best_idx = torch.argmax(logits_grouped, dim=1)         # [N]

        # 6) 取回最佳 subquestion 文本
        best_subqs = [subquestions_list[i][best_idx[i].item()] for i in range(N)]
        return best_subqs, best_idx

    @torch.no_grad()
    def select_single(self, question: str, variations: List[str]):
        """处理单个问题及其3个变体"""
        # 包装成列表调用 select_batch
        best_subqs, best_idxs = self.select_batch([question], [variations])
        # 解包返回
        return best_subqs[0], best_idxs[0].item()


class SubQuestionStep(BaseModel):
    """Represents a single logical step in the decomposition of a complex question."""
    
    subq_type: Annotated[
        str,
        Field(description="The logical role of this sub-question. Must be 'Anchor' (to retrieve prerequisite info: either a reference event's timestamp OR a set of candidate events for ranking) or 'Target' (to derive the final answer using temporal comparison, ranking logic, or direct explicit time constraints).")
    ]
    entities: Annotated[
        List[str],
        Field(
            description="A list of entities involved in this sub-question. Entities should be specific and relevant to the sub-question."
        )
    ]
    variations: Annotated[
        List[str],
        Field(
            min_length=3,
            max_length=3,
            description="A list of 3 distinct natural language variations of the sub-question. These variations should use different synonyms or sentence structures to maximize retrieval recall."
        )
    ]

class QuestionDecomposition(BaseModel):
    """The full decomposition result containing all necessary steps to answer the complex question."""

    steps: Annotated[
        List[SubQuestionStep],
        Field(
            description="A list of all sub-question steps that together form the complete decomposition of the original complex question."
        )
    ]

class OpenaiReq():
    def __init__(self, api_key, base_url):
        self.api_key = api_key
        self.base_url = base_url
        self.cache = {}
        self.cache_path = "temp/cache.jsonl"
        # 加载缓存
        if os.path.exists(self.cache_path):
            try:
                with open(self.cache_path, "r", encoding='utf-8') as f:
                    for line in f:
                        try:
                            datum = json.loads(line.strip())
                            self.cache[tuple(datum["input"])] = datum["response"]
                        except:
                            continue
            except Exception as e:
                print(f"Warning: Cache load failed: {e}")

    def req2openai(self, prompt, model="deepseek-chat", temperature=0, max_tokens=8192, stop=None, logprobs=True, use_cache=False):
        assert isinstance(prompt, str)
        # 构造缓存键
        input_key = (prompt, model, max_tokens, stop, logprobs)
        
        if use_cache and temperature == 0 and input_key in self.cache:
            return self.cache[input_key]
            
        llm = ChatDeepSeek(
            model=model,
            api_key=self.api_key,
            temperature=temperature,
            max_tokens=max_tokens,  # DeepSeek V3 上下文很大，可以适当给大
            timeout=120,
            max_retries=2,
        )
        struc_llm = llm.with_structured_output(QuestionDecomposition)
        messages = [{"role": "user", "content": prompt}]
        try:
            response = struc_llm.invoke(messages)
            steps = response.steps
            response_content = []
            for step in steps:
                response_content.append({
                    "subq_type": step.subq_type,
                    "entities": step.entities,
                    "variations": step.variations
                })
        except Exception as e:
            raise e

        if response and temperature == 0:
            if input_key not in self.cache:
                self.cache[input_key] = [response_content]
                # 追加写入缓存
                with open(self.cache_path, "a", encoding='utf-8') as f:
                    f.write(json.dumps({"input": input_key, "response": [response_content]}, ensure_ascii=False) + "\n")
             
        return response_content

def cleanup():
    """终止所有残留子进程"""
    for process in multiprocessing.active_children():
        process.terminate()

def clean_json_response(response_text):
    """清洗大模型返回的 JSON 字符串"""
    if isinstance(response_text, list):
        response_text = response_text[0] # Handle cache returning list
    try:
        # 去掉markdown的```json 和 ```，并strip空格
        clean_text = re.sub(r"^```json|```$", "", response_text.strip(), flags=re.MULTILINE).strip()
        data = json.loads(clean_text)
        return data
    except json.JSONDecodeError as e:
        # print(f"JSON解析错误: {e}")
        return {"error": "JSON解析失败", "raw": response_text}
    except Exception as e:
        return {"error": str(e)}

def generate_prompts():
    """生成 Prompt 文件"""
    print(colored("Generating Prompts...", "green"))
    
    # 读取 Prompt 模版
    templates = {}
    template_files = {
        "after_first": "after_first.txt",
        "before_after": "before_after.txt",
        "before_last": "before_last.txt",
        "equal_multi": "equal_multi.txt",
        "equal": "equal.txt",
        "first_last": "first_last.txt"
    }
    
    for key, filename in template_files.items():
        path = os.path.join(Config.PROMPT_DIR, filename)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Template file {path} not found.")
        else:
            with open(path, 'r', encoding='utf-8') as f:
                templates[key] = '\n'.join([line.strip() for line in f.readlines()])

    # 读取原始问题
    if not os.path.exists(Config.DATA_PATH):
        with open('../Datasets/MultiTQ/questions/test.json', 'r') as file:
            all_question_json = json.load(file)
        random.seed(42)
        question_json = random.sample(all_question_json, Config.SAMPLE_NUM)
        with open(Config.DATA_PATH, 'w') as file:
            json.dump(question_json, file, indent=4)
        
    else:
        with open(Config.DATA_PATH, 'r') as file:
            question_json = json.load(file)

    prompts = []
    for q in question_json:
        question = q['question']
        qtype = q['qtype']
        instruction = templates.get(qtype) # 默认 fallback
        
        prompt = instruction + f"Question: {question}\nOutput:\n"
        prompts.append(prompt)

    output_path = Config.PROMPTS_FILE
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(prompts, f, indent=2, ensure_ascii=False)
    
    print(f"Generated {len(prompts)} prompts. Saved to {output_path}")
    return output_path

# 定义在全局以便 multiprocessing pickle
def worker_query(rank, prompts_subset, api_key, base_url, output_dir, max_split, step):
    """子进程工作函数"""
    # print(f'Process rank {rank} PID {os.getpid()} begin...')
    reqor = OpenaiReq(api_key, base_url)
    
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f'rank_{rank}.json')

    try:
        with open(output_file, 'w', encoding='utf-8') as fout:
            # 只有 rank 0 显示进度条
            iterator = tqdm(range((len(prompts_subset) + step - 1) // step)) if rank == 0 else range((len(prompts_subset) + step - 1) // step)
            
            for idx in iterator:
                inputs = prompts_subset[idx * step : (idx + 1) * step]
                if not inputs:
                    break
                
                gpt_results = []
                for prompt in inputs:
                    # 核心请求
                    result = reqor.req2openai(prompt, max_tokens=8192, stop='\n\n')
                    gpt_results.append(result)

                # 写入结果
                for prompt, res in zip(inputs, gpt_results):
                    # print(f"Rank {rank}, writing result...")
                    output_item = json.dumps({'prompt': prompt, 'response': res}, ensure_ascii=False)
                    fout.write(output_item + '\n')
                    fout.flush()
    except Exception as err:
        print(f"Process {rank} error: {err}")

def run_inference(prompts_file):
    """并发执行推理"""
    print(colored("Running Inference (Multiprocessing)...", "green"))
    
    with open(prompts_file, 'r', encoding='utf-8') as f:
        prompts = json.load(f)
    
    print(f"Total prompts to process: {len(prompts)}")

    max_split = Config.MAX_SPLIT
    args_list = []
    
    # 准备切片参数
    for i in range(max_split):
        start = int(len(prompts) * i / max_split)
        end = int(len(prompts) * (i + 1) / max_split)
        subset = prompts[start:end]
        args_list.append((
            i, 
            subset, 
            Config.API_KEY, 
            Config.BASE_URL, 
            Config.OUTPUT_DIR,
            max_split,
            Config.STEP_SIZE
        ))

    # 启动进程池
    with Pool(max_split) as pool:
        pool.starmap(worker_query, args_list)
        
    print("Inference finished.")

def combine_results():
    """(原 2_combine.py) 合并结果"""
    print(colored("Combining Results...", "green"))
    output_dir = Config.OUTPUT_DIR
    data = []
    
    if not os.path.exists(output_dir):
        print("Output directory does not exist.")
        return

    # 遍历所有 rank_*.json 文件
    file_names = sorted([f for f in os.listdir(output_dir) if f.startswith("rank_") and f.endswith(".json")])
    
    for file_name in file_names:
        path = os.path.join(output_dir, file_name)
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    data.append(json.loads(line.strip()))

    output_path = os.path.join(output_dir, Config.PREDICTIONS_FILE)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        
    print(f"Combined {len(data)} items into {output_path}")
    return output_path

def parse_json(predictions_path):
    """解析 JSON 结构"""
    print(colored("Parsing JSON Responses...", "green"))
    minilm = SentenceTransformer(Config.MINILM, device=Config.DEVICE)
    model = ConcatBCEClassifier(embedding_dim=Config.EMBEDDING_DIM, dropout=0.3).to(Config.DEVICE)
    model.load_state_dict(torch.load(Config.BEST_MODEL_PATH, map_location=Config.DEVICE))
    model.eval()
    selector = BestSubquestionSelector(model, device=Config.DEVICE, encoder=minilm)
    
    with open(predictions_path, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)
    
    processed_data = []
    empty_responses = 0
    
    for item in tqdm(raw_data, desc="Parsing"):
        prompt = item['prompt']
        # 提取原始问题 (依赖 prompt 格式: ...\nQuestion: <question>\nOutput: )
        try:
            # 找到最后一次出现的 'Question: '
            q_start = prompt.rfind('\nQuestion: ')
            a_start = prompt.rfind('\nOutput:')
            if q_start != -1 and a_start != -1:
                question = prompt[q_start + len('\nQuestion: '): a_start].strip()
            else:
                # Fallback to original logic if format strict
                question = prompt.split('\n')[-2][len('Question: '):].strip()
        except:
             raise ValueError("Prompt format unexpected, cannot extract question.")

        hqdt = item.get('response')
        
        # 处理错误或空响应
        if not hqdt or "error" in hqdt or not isinstance(hqdt, list):
            # print(colored(f"Error parsing for: {question[:30]}...", 'red'))
            empty_responses += 1
            continue
        
        subquestions = []
        for step in hqdt:
            variations = step.get('variations', [])
            if len(variations) != 3:
                # print(colored(f"Invalid variations for: {question[:30]}...", 'red'))
                empty_responses += 1
                break
            best_subq, best_idx = selector.select_single(question, variations)
            step["best_subq"] = best_subq
            subquestions.append(step)

        processed_data.append({
            "question": question,
            "decomposition": subquestions
        })

    output_path = Config.BEST_SUBQ_FILE
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(processed_data, f, indent=2, ensure_ascii=False)

    print(f"Parsed {len(processed_data)} items. Empty/Error: {empty_responses}")

def normalize_date_in_question(question: str) -> str:
    """
    将英文自然语言中的时间表达转化为国际标准时间格式（YYYY-MM-DD 或 YYYY-MM）。
    """
    def convert_date(match):
        text = match.group(0)
        try:
            dt = parser.parse(text, fuzzy=True, default=None)
            # 判断是否包含日
            if re.search(r"\b\d{1,2}[a-z]{2}\b|\b\d{1,2}\b", text.lower()):
                return dt.strftime("%Y-%m-%d")
            elif any(month in text.lower() for month in MONTHS):
                return dt.strftime("%Y-%m")
            else:
                return dt.strftime("%Y")
        except Exception as e:
            return text  # 解析失败则返回原文

    # 支持的月份单词（缩写也匹配）
    MONTHS = [
        "january", "february", "march", "april", "may", "june",
        "july", "august", "september", "october", "november", "december",
        "jan", "feb", "mar", "apr", "jun", "jul", "aug", "sep", "sept", "oct", "nov", "dec"
    ]

    # 匹配常见时间表达（先匹配更复杂的）
    patterns = [
        r"\b\d{1,2}(st|nd|rd|th)? (of )?(January|February|March|April|May|June|July|August|September|October|November|December)( \d{4})?\b",
        r"\b(January|February|March|April|May|June|July|August|September|October|November|December) \d{1,2}(st|nd|rd|th)?,? \d{4}\b",
        r"\b(January|February|March|April|May|June|July|August|September|October|November|December) \d{4}\b",
        r"\b\d{4}\b"
    ]

    for pattern in patterns:
        question = re.sub(pattern, convert_date, question, flags=re.IGNORECASE)

    return question

def build_tree():
    print(colored("Building and Formatting Trees...", "green"))
    
    if not os.path.exists(Config.DATA_PATH) or not os.path.exists(Config.BEST_SUBQ_FILE):
        print(colored("Error: Input files for tree building not found.", "red"))
        return None

    with open(Config.DATA_PATH, 'r') as f:
        raw_questions = json.load(f)
    with open(Config.BEST_SUBQ_FILE, 'r') as f:
        decompositions = json.load(f)
        
    formatted_trees = []

    for item in raw_questions:
        tree = []
        question = item['question'].strip()
        for decom in decompositions:
            if decom['question'].strip() == question:
                subquestions = decom.get('decomposition')
                break
            else:
                subquestions = None

        idx = 0
        for sub in subquestions:
            subq_type = sub.get('subq_type').strip()
            question_text = sub.get('best_subq').strip()
            nor_subq = normalize_date_in_question(question_text)
            entities = sub.get('entities', [])
            tree.append({
                "idx": idx,
                "type": subq_type,
                "question_text": nor_subq,
                "entities": entities,
                "subquestions": [],
                "qd_logprob": 0 # Placeholder
            })
            idx += 1
        
        # 注入元数据
        tree.append({
            "idx": idx,
            "question_text": question,
            "entities": [],
            "subquestions": [i for i in range(idx)],
            "gold_answer": item.get("answers"),
            "answer_type": item.get("answer_type"),
            "qlabel": item.get("qlabel"),
            "time_level": item.get("time_level"),
            "qtype": item.get("qtype")
        })
        for sub_idx in range(idx):
            tree[sub_idx]["ori"] = idx
        formatted_trees.append(tree)

    with open(Config.SUBQ_FORMATTED_FILE, "w") as f:
        json.dump(formatted_trees, f, indent=2)
    
    print(f"Built {len(formatted_trees)} trees.")


def main():
    # 基本配置
    atexit.register(cleanup)
    start_time = time.time()
    
    # 1. 生成 Prompt
    prompts_file = generate_prompts()
    
    # # 2. 执行推理
    run_inference(prompts_file)
    
    # # 3. 合并结果
    predictions_file = combine_results()
    # predictions_file = os.path.join(Config.OUTPUT_DIR, Config.PREDICTIONS_FILE)
    
    # 4. 选择最优变体
    parse_json(predictions_file)

    # 5. 建立子问题树
    build_tree()

    # 结束运行
    end_time = time.time()
    print(colored(f"\nAll steps completed in {end_time - start_time:.2f} seconds.", "cyan"))


if __name__ == "__main__":
    main()