import os
import random
import re
import sys
import asyncio
import json
from copy import deepcopy
from sentence_transformers import SentenceTransformer
from termcolor import colored
from tqdm.asyncio import tqdm_asyncio
from tqdm import tqdm
from typing import List
import torch
import torch.nn.functional as F
import torch.nn as nn
from config import args
from utils import *
import prompts
from Retriever import Retrieval_BGE
from eval import evaluate

os.chdir(sys.path[0])  # 设置工作目录为脚本所在目录

class ConcatBCEClassifier(nn.Module):
    """将 q_emb 与 s_emb 拼接后，通过MLP输出单logit。"""
    def __init__(self, embedding_dim: int, dropout: float = 0.3):
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
    def select_single(self, question: str, variants: List[str]):
        """处理单个问题及其3个变体"""
        # 包装成列表调用 select_batch
        best_subqs, best_idxs = self.select_batch([question], [variants])
        # 解包返回
        return best_subqs[0], best_idxs[0].item()


async def process_single_question(data, selector, retriever, total_tokens, reranker_lock):
    """处理单个问题的完整流程"""
    question = data['question']
    qtype = data['qtype']
    answer_type = data['answer_type']
    time_level = data['time_level']
    qlabel = data['qlabel']

    # 问题类型标记
    time_constraint = "before" if "before" in qtype else "after" if "after" in qtype else None

    # 问题分解
    dec_prompt = getattr(prompts, qtype)
    dec_messages = [{"role": "system", "content": dec_prompt},
                    {"role": "user", "content": question}]
    dec_response = await llm_invoke(dec_messages, total_tokens)

    if not dec_response:
        print(colored(f"Decomposition failed for question: {question}", "red"))
        return None

    # 选择最佳子问题变体
    dec_questions = deepcopy(dec_response)
    for sub_decq in dec_questions:
        variants = sub_decq.get('variants', [])
        if len(variants) != 3:
            print(colored(f"Expected 3 variants for subquestion: {sub_decq.get('subq_idx')}", "red"))
            continue

        best_subq, _ = selector.select_single(question, variants)
        sub_decq['best_subq'] = best_subq

    # 相关事件检索
    for decq in dec_questions:
        # 找占位符
        idx = decq.get('subq_idx')
        cur_question = decq['best_subq']
        ref_tokens = re.findall(r"#\d+", cur_question)
        if ref_tokens:
            cur_question = await tcbridge_module(ref_tokens, cur_question, dec_questions, retriever, reranker_lock)
            decq['best_subq'] = cur_question

        # 子问题事件检索
        facts = await retriever.get_faiss_facts(cur_question, args.top_k)
        decq['facts'] = facts

    # 根据子问题相关事件进行推理
    last_subq = dec_questions[-1]
    last_facts = last_subq['facts']
    facts_text = '\n'.join(last_facts)
    human_message = f"Relevant facts:\n{facts_text}\nQuestion: {last_subq['best_subq']}"
    inf_messages = [{"role": "system", "content": prompts.inference},
                    {"role": "user", "content": human_message}]
    inf_response = await llm_invoke(inf_messages, total_tokens)

    reason = inf_response.get('reason', 'No reason generated.')
    answers = inf_response.get('answers', [])

    # fallback
    if not answers:
        fallback_facts = await retriever.get_faiss_facts(question, args.top_k)
        if fallback_facts:
            facts_text = '\n'.join(fallback_facts)
            human_message = f"Relevant facts (fallback):\n{facts_text}\nQuestion: {last_subq['best_subq']}"
            inf_messages = [{"role": "system", "content": prompts.inference},
                            {"role": "user", "content": human_message}]
            inf_response = await llm_invoke(inf_messages, total_tokens)

            reason = inf_response.get('reason', 'No reason generated.')
            answers = inf_response.get('answers', [])

    return {
        "question": question,
        "gold_answers": data['answers'],
        "qtype": qtype,
        "answer_type": answer_type,
        "time_level": time_level,
        "qlabel": qlabel,
        "decomposition": dec_questions,
        "inference": {
            "reason": reason,
            "answers": answers
        }
    }


async def main():
    reranker_lock = asyncio.Lock()

    # 加载最优选择器
    minilm = SentenceTransformer(args.minilm, device='cuda')
    model = ConcatBCEClassifier(embedding_dim=384, dropout=0.3).to('cuda')
    model.load_state_dict(torch.load(args.best_model, map_location='cuda'))
    model.eval()
    selector = BestSubquestionSelector(model, device='cuda', encoder=minilm)

    # 加载检索器
    retriever = Retrieval_BGE(
        encoder_model=args.bge_model,
        reranker_model=args.reranker_model,
        embedding_size=args.embedding_size,
        use_gpu=args.use_gpu,
        gpu_id=args.gpu_id
    )
    await retriever.load()

    # 加载测试数据
    sample_path = f'../Datasets/{args.dataset}/questions/test_{args.sample}.json'
    if os.path.exists(sample_path):
        with open(sample_path, 'r') as file:
            datas = json.load(file)
    else:
        with open(f'../Datasets/{args.dataset}/questions/test.json', 'r') as file:
            test_data = json.load(file)
            random.seed(42)
            datas = random.sample(test_data, args.sample)
        with open(sample_path, 'w') as file:
            json.dump(datas, file, indent=4)

    # 统计 tokens 用量（使用可变对象在协程间共享）
    total_tokens = {
        "completion": 0,
        "prompt": 0,
        "total": 0
    }

    # 并发限制
    concurrent_limit = getattr(args, 'concurrent_limit', 8)
    semaphore = asyncio.Semaphore(concurrent_limit)

    async def process_with_limit(data):
        async with semaphore:
            return await process_single_question(data, selector, retriever, total_tokens, reranker_lock)

    # 并行处理所有问题
    tasks = [process_with_limit(data) for data in datas]
    results_raw = await tqdm_asyncio.gather(*tasks, desc="Processing questions concurrently")

    # 过滤掉失败的结果（None）
    results = [r for r in results_raw if r is not None]
    failed_dec = len(datas) - len(results)

    # 保存所有结果
    print(f"\n{failed_dec} questions failed during decomposition.")
    print("\n===============================================\n")
    print(f"Total tokens used: {total_tokens}")
    print("\n===============================================\n")

    output_path, error_path, result_path = get_result_paths(
        args.dataset,
        args.sample,
        top_k=args.top_k,
        rerank_top_k=args.rerank_top_k
    )
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    os.makedirs(os.path.dirname(error_path), exist_ok=True)
    os.makedirs(os.path.dirname(result_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, ensure_ascii=False, indent=4)

    # 评估准确率
    evaluate(output_path, error_path, result_path, total_tokens)

if __name__ == "__main__":
    asyncio.run(main())
