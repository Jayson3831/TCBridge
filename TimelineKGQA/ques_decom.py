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
        )
        self.classifier = nn.Linear(128 + 1, 1)

    def forward(self, q_emb: torch.Tensor, s_emb: torch.Tensor, batch_cosine: torch.Tensor) -> torch.Tensor:
        if q_emb.dim() == 1:
            q_emb = q_emb.unsqueeze(0)
        if s_emb.dim() == 1:
            s_emb = s_emb.unsqueeze(0)
        x = torch.cat([q_emb, s_emb], dim=-1)
        fea = self.net(x).squeeze(-1)
        batch_cosine = batch_cosine.unsqueeze(1)
        combined = torch.cat([fea, batch_cosine], dim=1)
        logit = self.classifier(combined).squeeze()
        return logit

class BestSubquestionSelector:
    def __init__(self, model, device, encoder, normalize=True, encode_bs=64):
        self.model = model
        self.device = device
        self.encoder = encoder
        self.normalize = normalize
        self.encode_bs = encode_bs

    @torch.no_grad()
    def _encode(self, texts):
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
        assert len(questions) == len(subquestions_list)
        N = len(questions)
        if N == 0:
            return [], torch.empty(0, dtype=torch.long), torch.empty(0, 3)

        q_emb = self._encode(questions)
        flat_subqs = [sq for trio in subquestions_list for sq in trio]
        s_emb = self._encode(flat_subqs)

        q_emb_rep = q_emb.repeat_interleave(3, dim=0)
        cosine = F.cosine_similarity(q_emb_rep, s_emb, dim=1)
        logits = self.model(q_emb_rep, s_emb, cosine)
        
        if logits.dim() == 2 and logits.size(1) == 1:
            logits = logits.squeeze(1)
        else:
            logits = logits.view(-1)

        logits_grouped = logits.view(N, 3)
        best_idx = torch.argmax(logits_grouped, dim=1)
        best_subqs = [subquestions_list[i][best_idx[i].item()] for i in range(N)]
        return best_subqs, best_idx

    @torch.no_grad()
    def select_single(self, question: str, variations: List[str]):
        best_subqs, best_idxs = self.select_batch([question], [variations])
        return best_subqs[0], best_idxs[0].item()

class SubQuestionStep(BaseModel):
    idx: Annotated[str, Field(description="The index of the sub-question step.")]
    entities: Annotated[List[str], Field(description="A list of entities involved.")]
    variations: Annotated[List[str], Field(min_length=3, max_length=3, description="A list of 3 distinct natural language variations.")]

class QuestionDecomposition(BaseModel):
    steps: Annotated[List[SubQuestionStep], Field(description="All sub-question steps.")]

class OpenaiReq():
    def __init__(self, api_key, base_url):
        self.api_key = api_key
        self.base_url = base_url
        self.cache = {}
        self.cache_path = "temp/cache.jsonl"
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
        input_key = (prompt, model, max_tokens, stop, logprobs)
        
        if use_cache and temperature == 0 and input_key in self.cache:
            return self.cache[input_key]
            
        llm = ChatDeepSeek(
            model=model,
            api_key=self.api_key,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        # 增加重试次数以防万一
        struc_llm = llm.with_structured_output(QuestionDecomposition).with_retry(stop_after_attempt=3)
        messages = [{"role": "user", "content": prompt}]
        
        try:
            response = struc_llm.invoke(messages)
            if response is None:
                print(f"Warning: LLM returned None.")
                return {"error": "LLM returned None"}
            
            steps = response.steps
            response_content = []
            for step in steps:
                response_content.append({
                    "idx": step.idx,
                    "entities": step.entities,
                    "variations": step.variations
                })

            if response and temperature == 0:
                if input_key not in self.cache:
                    self.cache[input_key] = [response_content]
                    with open(self.cache_path, "a", encoding='utf-8') as f:
                        f.write(json.dumps({"input": input_key, "response": [response_content]}, ensure_ascii=False) + "\n")
             
            return response_content
        except Exception as e:
            print(f"Error calling LLM: {e}")
            return {"error": str(e)}

def cleanup():
    for process in multiprocessing.active_children():
        process.terminate()

def load_all_questions():
    if not os.path.exists(Config.FULL_DATA):
         raise FileNotFoundError("Raw questions file not found.")

    with open(Config.FULL_DATA, 'r') as file:
        return json.load(file)

def worker_query(rank, prompts_subset, api_key, base_url, output_dir, max_split, step):
    reqor = OpenaiReq(api_key, base_url)
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f'rank_{rank}.json')

    try:
        with open(output_file, 'w', encoding='utf-8') as fout:
            iterator = tqdm(range((len(prompts_subset) + step - 1) // step)) if rank == 0 else range((len(prompts_subset) + step - 1) // step)
            
            for idx in iterator:
                inputs = prompts_subset[idx * step : (idx + 1) * step]
                if not inputs:
                    break
                
                gpt_results = []
                for prompt in inputs:
                    # 确保 max_tokens 足够大
                    result = reqor.req2openai(prompt, max_tokens=8192, stop='\n\n')
                    gpt_results.append(result)

                for prompt, res in zip(inputs, gpt_results):
                    output_item = json.dumps({'prompt': prompt, 'response': res}, ensure_ascii=False)
                    fout.write(output_item + '\n')
                    fout.flush()
    except Exception as err:
        print(f"Process {rank} error: {err}")

def generate_prompts_for_batch(questions_batch, templates):
    prompts = []
    for q in questions_batch:
        question = q['question']
        question_level = q['question_level']
        instruction = templates.get(question_level, templates.get("simple"))
        prompt = instruction + f"\n\nQuestion: {question}\nOutput:\n"
        prompts.append({
            "text": prompt,
            "original_data": q
        })
    return prompts

def run_inference_batch(prompts_batch):
    temp_prompts_file = f"temp/temp_prompts_batch.json"
    os.makedirs("temp", exist_ok=True)
    
    prompt_texts = [p["text"] for p in prompts_batch]
    with open(temp_prompts_file, 'w', encoding='utf-8') as f:
        json.dump(prompt_texts, f, indent=2, ensure_ascii=False)

    max_split = Config.MAX_SPLIT
    prompts = prompt_texts
    args_list = []
    for i in range(max_split):
        start = int(len(prompts) * i / max_split)
        end = int(len(prompts) * (i + 1) / max_split)
        subset = prompts[start:end]
        if not subset: continue
        args_list.append((
            i, 
            subset, 
            Config.API_KEY, 
            Config.BASE_URL, 
            Config.OUTPUT_DIR,
            max_split,
            Config.STEP_SIZE
        ))

    with Pool(len(args_list)) as pool:
        pool.starmap(worker_query, args_list)
    
    batch_results = []
    output_dir = Config.OUTPUT_DIR
    for f_name in os.listdir(output_dir):
        if f_name.startswith("rank_") and f_name.endswith(".json"):
            path = os.path.join(output_dir, f_name)
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            try:
                                batch_results.append(json.loads(line.strip()))
                            except:
                                pass
            os.remove(path)
            
    return batch_results

def process_batch_results(batch_results, prompts_batch_dicts, selector):
    prompt_map = {p["text"]: p["original_data"] for p in prompts_batch_dicts}
    valid_data = [] 
    
    for item in batch_results:
        prompt_text = item.get('prompt')
        hqdt = item.get('response')
        
        if not hqdt or "error" in hqdt or not isinstance(hqdt, list):
            continue
            
        original_q_data = prompt_map.get(prompt_text)
        if not original_q_data:
            continue
            
        question_text = original_q_data['question']

        try:
            subquestions = []
            for step in hqdt:
                variations = step.get('variations', [])
                if len(variations) != 3:
                    raise ValueError("Variations count != 3")
                best_subq, best_idx = selector.select_single(question_text, variations)
                step["best_subq"] = best_subq
                subquestions.append(step)
            
            valid_data.append({
                "original_data": original_q_data,
                "decomposition": subquestions
            })
        except Exception:
            continue
            
    return valid_data

def build_formatted_tree_final(valid_items):
    print(colored(f"Building trees for {len(valid_items)} items...", "green"))
    formatted_trees = []

    for item in valid_items:
        original_data = item['original_data']
        subquestions = item['decomposition']
        
        tree = []
        idx = 0
        
        for sub in subquestions:
            question_text = sub.get('best_subq').strip()
            nor_subq = normalize_date_in_question(question_text)
            entities = sub.get('entities', [])
            tree.append({
                "idx": idx,
                "question_text": nor_subq,
                "entities": entities,
                "subquestions": [] 
            })
            idx += 1
        
        root_node = {
            "idx": idx,
            "question_text": original_data['question'],
            "entities": [],
            "subquestions": [i for i in range(idx)],
            "gold_answer": original_data.get("answer"),
            "events": original_data.get("events"),
            "answer_type": original_data.get("answer_type"),
            "question_level": original_data.get("question_level"),
            "question_type": original_data.get("question_type"),
            "temporal_relation": original_data.get("temporal_relation"),
            "qtype": original_data.get("qtype")
        }
        for sub_idx in range(idx):
            tree[sub_idx]["ori"] = idx
            
        tree.append(root_node)
        formatted_trees.append(tree)

    with open(Config.SUBQ_FORMATTED_FILE, "w", encoding='utf-8') as f:
        json.dump(formatted_trees, f, indent=2, ensure_ascii=False)
    
    raw_subset = [item['original_data'] for item in valid_items]
    with open(Config.DATA_PATH, 'w', encoding='utf-8') as f:
        json.dump(raw_subset, f, indent=4, ensure_ascii=False)
        
    print(f"Saved {len(formatted_trees)} trees to {Config.SUBQ_FORMATTED_FILE}")

def normalize_date_in_question(question: str) -> str:
    def convert_date(match):
        text = match.group(0)
        try:
            dt = parser.parse(text, fuzzy=True, default=None)
            if re.search(r"\b\d{1,2}[a-z]{2}\b|\b\d{1,2}\b", text.lower()):
                return dt.strftime("%Y-%m-%d")
            elif any(month in text.lower() for month in MONTHS):
                return dt.strftime("%Y-%m")
            else:
                return dt.strftime("%Y")
        except Exception as e:
            return text

    MONTHS = [
        "january", "february", "march", "april", "may", "june",
        "july", "august", "september", "october", "november", "december",
        "jan", "feb", "mar", "apr", "jun", "jul", "aug", "sep", "sept", "oct", "nov", "dec"
    ]

    patterns = [
        r"\b\d{1,2}(st|nd|rd|th)? (of )?(January|February|March|April|May|June|July|August|September|October|November|December)( \d{4})?\b",
        r"\b(January|February|March|April|May|June|July|August|September|October|November|December) \d{1,2}(st|nd|rd|th)?,? \d{4}\b",
        r"\b(January|February|March|April|May|June|July|August|September|October|November|December) \d{4}\b",
        r"\b\d{4}\b"
    ]

    for pattern in patterns:
        question = re.sub(pattern, convert_date, question, flags=re.IGNORECASE)

    return question

def main():
    atexit.register(cleanup)
    start_time = time.time()
    
    print(colored("Initializing models...", "green"))
    minilm = SentenceTransformer(Config.MINILM, device=Config.DEVICE)
    model = ConcatBCEClassifier(embedding_dim=Config.EMBEDDING_DIM, dropout=0.3).to(Config.DEVICE)
    model.load_state_dict(torch.load(Config.BEST_MODEL_PATH, map_location=Config.DEVICE))
    model.eval()
    selector = BestSubquestionSelector(model, device=Config.DEVICE, encoder=minilm)
    
    templates = {}
    for key, filename in {"simple": "simple.txt", "medium": "medium.txt", "complex": "complex.txt"}.items():
        with open(os.path.join(Config.PROMPT_DIR, filename), 'r') as f:
            templates[key] = f.read().strip()

    # 1. 加载所有数据
    all_questions = load_all_questions()
    
    # 2. 随机采样 Config.SAMPLE_NUM
    needed = Config.SAMPLE_NUM
    if len(all_questions) < needed:
        print(colored(f"Warning: Only {len(all_questions)} questions available, less than requested {needed}.", "yellow"))
        selected_questions = all_questions
    else:
        selected_questions = random.sample(all_questions, needed)

    print(colored(f"Selected {len(selected_questions)} questions via random sampling.", "cyan"))

    # 3. 生成 Prompts
    prompts_batch = generate_prompts_for_batch(selected_questions, templates)
    
    # 4. 推理
    batch_raw_results = run_inference_batch(prompts_batch)
    
    # 5. 解析 & 筛选 (成功率应该很高)
    valid_items = process_batch_results(batch_raw_results, prompts_batch, selector)
    
    print(colored(f"Successfully decomposed: {len(valid_items)} / {len(selected_questions)}", "green"))
    if len(valid_items) < len(selected_questions):
        print(colored(f"Warning: {len(selected_questions) - len(valid_items)} questions failed inference/parsing.", "red"))

    # 6. 构建树文件
    build_formatted_tree_final(valid_items)

    end_time = time.time()
    print(colored(f"\nAll steps completed in {end_time - start_time:.2f} seconds.", "cyan"))

if __name__ == "__main__":
    main()