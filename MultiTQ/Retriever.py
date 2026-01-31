import os
import asyncio
import numpy as np
from termcolor import colored
import faiss
import torch
from FlagEmbedding import BGEM3FlagModel, FlagReranker
from config import args


class Retrieval_BGE:
    def __init__(self, encoder_model, reranker_model, embedding_size=1024, use_gpu=True, gpu_id=3):
        self.device = f'cuda:{gpu_id}' if torch.cuda.is_available() and use_gpu else 'cpu'
        self.encoder = None
        self.reranker = None
        self.encoder_model = encoder_model
        self.reranker_model = reranker_model
        self.embedding_size = embedding_size
        self.fact_list = []
        self.index = None

    async def load(self):
        print(colored("Loading Embedding Model...", "cyan"))
        # 注意：这里假设使用 GPU，如无 GPU 需修改 devices
        devices = [self.device] if 'cuda' in self.device else None
        self.encoder = BGEM3FlagModel(self.encoder_model, use_fp16=False, devices=devices)
        self.reranker = FlagReranker(self.reranker_model, use_fp16=True, devices=devices)

        print(colored("Loading Knowledge Graph...", "cyan"))
        with open(args.kg_path, 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.strip().replace("_", " ").split('\t')
                if len(parts) >= 4:
                    self.fact_list.append(f'{parts[0]} {parts[1]} {parts[2]} in {parts[3]}.')

        if os.path.exists(args.index_path):
            print(colored("Loading Existing FAISS Index...", "cyan"))
            self.index = faiss.read_index(args.index_path)
            print("FAISS Index Loaded.")
        else:
            print(colored("Encoding Corpus (This may take a while)...", "cyan"))
            os.makedirs(os.path.dirname(args.index_path), exist_ok=True)
            embeddings_dict = self.encoder.encode_corpus(
                self.fact_list,
                convert_to_numpy=True,
                batch_size=1024, 
                return_dense=True,
                return_sparse=True,
                return_colbert_vecs=True
            )
            self.triplet_embeddings = embeddings_dict['dense_vecs']
            self.triplet_embeddings = self.triplet_embeddings.astype(np.float32)

            self.dim = self.triplet_embeddings.shape[-1]

            self.index = self.build_faiss_index()
            
            if not self.index.is_trained:
                self.index.train(self.triplet_embeddings)
            self.index.add(self.triplet_embeddings)
            faiss.write_index(self.index, args.index_path)
            print("FAISS Index Built.")

    def build_faiss_index(self, n_clusters=100, nprobe=10): # Reduced clusters for stability
        quantizer = faiss.IndexFlatIP(self.embedding_size)
        index = faiss.IndexIVFFlat(quantizer, self.embedding_size, n_clusters, faiss.METRIC_INNER_PRODUCT)
        index.nprobe = nprobe
        if self.device == 'cuda':
            ngpu = 1
            resources = [faiss.StandardGpuResources() for _ in range(ngpu)]
            vres = faiss.GpuResourcesVector()
            vdev = faiss.Int32Vector()
            for i, res in zip(range(ngpu), resources):
                vdev.push_back(i)
                vres.push_back(res)
            index_gpu = faiss.index_cpu_to_gpu_multiple(vres, vdev, index)          
            return index_gpu
        else:
            return index

    async def get_embedding(self, corpus_list):
        result =  await asyncio.to_thread(
            self.encoder.encode_queries,
            corpus_list,
            convert_to_numpy=True,
            return_dense=True,
            return_sparse=True,
            return_colbert_vecs=True
        )
        return result['dense_vecs']

    async def get_faiss_facts(self, question, top_k):
        question_embedding = await self.get_embedding([question]) 

        if question_embedding.dtype != np.float32:
            question_embedding = question_embedding.astype(np.float32)

        distances, corpus_ids = self.index.search(question_embedding, top_k)
    
        hits = [{'corpus_id': id, 'score': score} for id, score in zip(corpus_ids[0], distances[0])]
        hits = sorted(hits, key=lambda x: x['score'], reverse=True)

        scores = [float(hit['score']) for hit in hits]
        facts = [self.fact_list[hit['corpus_id']] for hit in hits]
        return {
            'facts': facts,
            'scores': scores
        }

    async def rerank_facts(self, question, facts, rerank_top_k=3):
        qf_pairs = [[question, fact] for fact in facts]
        scores = await asyncio.to_thread(
            self.reranker.compute_score,
            qf_pairs,
            normalize=True,
        )
        ranked_indices = np.argsort(-np.array(scores))[:rerank_top_k]
        ranked_facts = [facts[i] for i in ranked_indices]
        ranked_scores = [scores[i] for i in ranked_indices]
        return {
            'facts': ranked_facts,
            'scores': ranked_scores
        }


async def main():
    retriever = Retrieval_BGE(
        encoder_model=args.bge_model,
        reranker_model=args.reranker_model,
        embedding_size=args.embedding_size,
        use_gpu=args.use_gpu,
        gpu_id=args.gpu_id
    )
    await retriever.load()

    question = "Which entity paid a visit to China on 2013-05-08?"

    faiss_facts = await retriever.get_faiss_facts(question, top_k=args.top_k)
    rerank_facts = await retriever.rerank_facts(question, faiss_facts, rerank_top_k=args.rerank_top_k)
    print(f"faiss facts: {rerank_facts}")

if __name__ == "__main__":
    asyncio.run(main())