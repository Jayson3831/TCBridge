import os, sys
import json
import asyncio
import numpy as np
import multiprocessing as mp
from config import Config
from datetime import datetime
from termcolor import colored
import faiss
import torch
from FlagEmbedding import BGEM3FlagModel, FlagReranker
from sentence_transformers import SentenceTransformer, util
import spacy
from neo4j import AsyncGraphDatabase
import time


# os.chdir(sys.path[0])
nlp = spacy.load("en_core_web_sm")

def parse_date(date_str):
    formats = ["%Y-%m-%d", "%d %B %Y", "%B %Y"]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            pass
    return None

def extract_dates(text):
    if not nlp: return None
    doc = nlp(text)
    dates = ""
    for ent in doc.ents:
        if ent.label_ == "DATE":
            dates += ent.text + " "
    processed_dates = parse_date(dates.strip())
    return processed_dates

class Retrieval_BGE:
    def __init__(self, d, encoder_model, reranker_model, event_list, embedding_size=1024, use_gpu=True, gpu_id=3):
        self.device = f'cuda:{gpu_id}' if torch.cuda.is_available() and use_gpu else 'cpu'
        self.encoder = None
        self.reranker = None
        self.encoder_model = encoder_model
        self.reranker_model = reranker_model
        self.embedding_size = embedding_size
        self.fact_list = []
        self.event_list = []
        self.index = None
        self.load_datas(event_list)

    def load_datas(self, events):
        for event in events:
            sub, rel, obj, start_time, end_time = event['subject'], event['predicate'], event['object'], event['start_time'], event['end_time']
            if start_time == end_time:
                event_str = f"{sub} {rel} {obj} on {start_time}."
            else:
                event_str = f"{sub} {rel} {obj} from {start_time} to {end_time}."
            self.fact_list.append(event_str)
            self.event_list.append(f"{sub}|{rel}|{obj}|{start_time}|{end_time}")

    async def load(self):
        print(colored("Loading Embedding Model...", "cyan"))
        # 注意：这里假设使用 GPU，如无 GPU 需修改 devices
        devices = [self.device] if 'cuda' in self.device else None
        self.encoder = BGEM3FlagModel(self.encoder_model, use_fp16=False, devices=devices)
        self.reranker = FlagReranker(self.reranker_model, use_fp16=True, devices=devices)
        
        if os.path.exists(Config.INDEX):
            print(colored("Loading Existing FAISS Index...", "cyan"))
            self.index = faiss.read_index(Config.INDEX)
            print("FAISS Index Loaded.")
        else:
            print(colored("Encoding Corpus (This may take a while)...", "cyan"))
            embeddings_dict = self.encoder.encode_corpus(
                self.fact_list,
                convert_to_numpy=True,
                batch_size=1024, 
                return_dense=True,
                return_sparse=True,
                return_colbert_vecs=True
            )
            self.event_embeddings = embeddings_dict['dense_vecs']
            self.event_embeddings = self.event_embeddings.astype(np.float32)

            self.dim = self.event_embeddings.shape[-1]

            self.index = self.build_faiss_index()
            
            if not self.index.is_trained:
                self.index.train(self.event_embeddings)
            self.index.add(self.event_embeddings)
            faiss.write_index(self.index, Config.INDEX)
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

    async def compute_similarity(self, question, n):
        self.question_embedding = await self.get_embedding([question]) 

        if self.question_embedding.dtype != np.float32:
            self.question_embedding = self.question_embedding.astype(np.float32)

        distances, corpus_ids = self.index.search(self.question_embedding, n)
        return distances[0], corpus_ids[0]

    async def get_faiss_similarity(self, question, n):
        question_embedding = await self.get_embedding([question]) 

        if question_embedding.dtype != np.float32:
            question_embedding = question_embedding.astype(np.float32)

        distances, corpus_ids = self.index.search(question_embedding, n)
    
        result = {'question': question}
        hits = [{'corpus_id': id, 'score': score} for id, score in zip(corpus_ids[0], distances[0])]
        hits = sorted(hits, key=lambda x: x['score'], reverse=True)

        result['scores'] = [str(hit['score']) for hit in hits]
        result['fact'] = [self.fact_list[hit['corpus_id']] for hit in hits]
        result['event'] = [self.event_list[hit['corpus_id']] for hit in hits]
        return result

    async def rerank_facts(self, question, top_k=3):
        fact_result = await self.get_faiss_similarity(question, n=100)
        fact_list = fact_result.get('fact')
        qf_pairs = [[question, fact] for fact in fact_list]
        scores = await asyncio.to_thread(
            self.reranker.compute_score,
            qf_pairs,
            normalize=True,
        )
        ranked_indices = np.argsort(-np.array(scores))[:top_k]
        ranked_facts = [fact_list[i] for i in ranked_indices]
        ranked_scores = [scores[i] for i in ranked_indices]
        return ranked_facts, ranked_scores

    async def ori_rerank_facts(self, question, sub_facts, top_k=15):
        fact_result = await self.get_faiss_similarity(question, n=100)
        retrieved_facts = fact_result.get('fact')
        
        combined_facts = retrieved_facts + sub_facts
        fact_list = list(set(combined_facts))
        qf_pairs = [[question, fact] for fact in fact_list]
        scores = await asyncio.to_thread(
            self.reranker.compute_score,
            qf_pairs,
            normalize=True,
        )
        ranked_indices = np.argsort(-np.array(scores))[:top_k]
        ranked_facts = [fact_list[i] for i in ranked_indices]
        ranked_scores = [scores[i] for i in ranked_indices]
        return ranked_facts, ranked_scores

    async def get_result(self, question, distances, corpus_ids):
        result = await self.basic_result(question, distances, corpus_ids)
        return result

    async def basic_result(self, question, distances, corpus_ids):
        result = {'question': question}
        hits = [{'corpus_id': id, 'score': score} for id, score in zip(corpus_ids, distances)]
        hits = sorted(hits, key=lambda x: x['score'], reverse=True)

        result['scores'] = [str(hit['score']) for hit in hits]
        result['event'] = [self.event_list[hit['corpus_id']] for hit in hits]
        result['fact'] = [self.fact_list[hit['corpus_id']] for hit in hits]
        return result

    def save_results(self, result_list, output_path):
        with open(output_path, "w", encoding='utf-8') as json_file:
            json.dump(result_list, json_file, indent=4)


if __name__ == "__main__":
    pass