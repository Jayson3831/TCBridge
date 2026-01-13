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
    def __init__(self, d, encoder_model, reranker_model, triple_list, embedding_size=1024, use_gpu=True, gpu_id=3):
        self.device = f'cuda:{gpu_id}' if torch.cuda.is_available() and use_gpu else 'cpu'
        self.encoder = None
        self.reranker = None
        self.encoder_model = encoder_model
        self.reranker_model = reranker_model
        self.embedding_size = embedding_size
        self.triple_list = triple_list
        # 构建事实文本
        self.fact_list = [f'{f[0]} {f[1]} {f[2]} in {f[3]}.' for f in triple_list]
        self.full_time = [triple[3] for triple in triple_list]
        self.index = None

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
            self.triplet_embeddings = embeddings_dict['dense_vecs']
            self.triplet_embeddings = self.triplet_embeddings.astype(np.float32)

            self.dim = self.triplet_embeddings.shape[-1]

            self.index = self.build_faiss_index()
            
            if not self.index.is_trained:
                self.index.train(self.triplet_embeddings)
            self.index.add(self.triplet_embeddings)
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

    async def get_result(self, question, distances, corpus_ids, re_rank=False):
        if re_rank:
            result = await self.re_rank_single_result(question, distances, corpus_ids)
        else:
            result = await self.basic_result(question, distances, corpus_ids)
        return result

    async def re_rank_single_result(self, question, distances, corpus_ids):
        target_time = extract_dates(question)
        time_list = [10 for _ in range(len(self.full_time))]
        
        if target_time and target_time != "None":
            target_time = datetime.strptime(target_time, "%Y-%m-%d")
            self.adjust_time_scores(question, target_time, time_list)
        
        result = {'question': question}
        hits = [{'corpus_id': id, 'score': score, 'final_score': score * 0.4 - time_list[id] * 0.6}
                for id, score in zip(corpus_ids, distances)]
        hits = sorted(hits, key=lambda x: x['final_score'], reverse=True)

        result['scores'] = [str(hit['score']) for hit in hits][:15]
        result['final_score'] = [str(hit['final_score']) for hit in hits][:15]
        result['triple'] = [self.triple_list[hit['corpus_id']] for hit in hits]
        result['fact'] = [self.fact_list[hit['corpus_id']] for hit in hits]
        return result

    async def basic_result(self, question, distances, corpus_ids):
        result = {'question': question}
        hits = [{'corpus_id': id, 'score': score} for id, score in zip(corpus_ids, distances)]
        hits = sorted(hits, key=lambda x: x['score'], reverse=True)

        result['scores'] = [str(hit['score']) for hit in hits]
        result['triple'] = [self.triple_list[hit['corpus_id']] for hit in hits]
        result['fact'] = [self.fact_list[hit['corpus_id']] for hit in hits]
        return result

    def save_results(self, result_list, output_path):
        with open(output_path, "w", encoding='utf-8') as json_file:
            json.dump(result_list, json_file, indent=4)

class TemporalKnowledgeGraph:
    def __init__(self, uri, user, password, database, use_gpu=True, gpu_id=Config.GPU_ID, rebuild_graph=Config.REBUILD_NEO4J):
        """
        :param rebuild_graph: bool, 是否在启动时清空数据库并重新导入数据
        """
        self.driver = AsyncGraphDatabase.driver(uri, auth=(user, password))
        self.database = database
        self.device = f'cuda:{gpu_id}' if torch.cuda.is_available() and use_gpu else 'cpu'
        self.rebuild_graph = rebuild_graph  # 是否需要导入知识图谱
        self.fact_list = []

        # 用于持有内存映射的向量数据
        self.vector_cache = None

    async def load(self, kg_path, encoder, reranker):
        # 初始化模型（无论是否重构图谱，模型都需要加载）
        devices = [self.device] if 'cuda' in self.device else None
        self.reranker = FlagReranker(reranker, use_fp16=True, devices=devices)
        self.encoder = BGEM3FlagModel(encoder, use_fp16=False, devices=devices)

        # 加载知识图谱
        try:
            with open(kg_path, 'r', encoding='utf-8') as f:
                for line in f:
                    parts = line.strip().replace("_", " ").split('\t')
                    if len(parts) >= 4:
                        self.fact_list.append(f"{parts[0]} {parts[1]} {parts[2]} in {parts[3]}")
        except Exception as e:
            print(f"Error loading KG from {kg_path}: {e}")
            raise

        # 根据 rebuild_graph 参数决定是否重置数据库
        if self.rebuild_graph:
            print(f"重置数据库...")
            await self.clean_database()         # 清空原有数据
            await self.init_schema()            # 初始化索引和约束
            await self.import_data(Config.KG_PATH)   # 导入数据

        # 加载向量缓存 (.npy)
        if os.path.exists(Config.NPY):
            print(f"Loading vectors from {Config.NPY} (Memmap)...")
            # 使用 mmap 模式读取，速度快且不占内存
            self.vector_cache = np.load(Config.NPY, mmap_mode='r')
        else:
            # 如果不重建图谱，又没有 npy 文件，那是没法跑的
            raise FileNotFoundError(f"未找到向量文件 {Config.NPY}，请先设置 REBUILD_NEO4J=True 生成数据。")

        # 处理 FAISS 索引
        if os.path.exists(Config.INDEX):
            print("Loading Existing FAISS Index...")
            self.index = faiss.read_index(Config.INDEX)
        else:
            print(colored("Encoding Corpus (This may take a while)...", "cyan"))

            if self.vector_cache.dtype != np.float32:
                 # 通常不需要这一步，因为保存时就是 float32
                 embeddings_for_index = self.vector_cache.astype(np.float32)
            else:
                 embeddings_for_index = self.vector_cache

            self.dim = embeddings_for_index.shape[-1]
            self.index = self._build_faiss_index()
            
            if not self.index.is_trained:
                self.index.train(self.vector_cache)
            self.index.add(self.vector_cache)
            faiss.write_index(self.index, Config.INDEX)
            print("FAISS Index Built.")

    async def close(self):
        await self.driver.close()

    async def clean_database(self):
        """清空数据库所有节点和关系"""
        print("正在执行全库删除 (MATCH (n) DETACH DELETE n)...")
        async with self.driver.session(database=self.database) as session:
            try:
                # 注意：如果数据量达到千万级，直接 delete n 可能会 OOM，建议分批删除
                # 这里为了简化，使用标准删除
                await session.run("MATCH (n) DETACH DELETE n")
                print("数据库已清空。")
            except Exception as e:
                print(f"清空数据库时发生错误: {e}")

    async def init_schema(self):
        """初始化索引和约束（包含强制等待索引生效）"""
        async with self.driver.session(database=self.database) as session:
            # --- 1. 基础约束 ---
            print("正在检查基础约束...")
            try:
                await session.run("CREATE CONSTRAINT FOR (e:Entity) REQUIRE e.name IS UNIQUE")
            except Exception as e:
                pass # 忽略已存在的错误

            # --- 2. 全文索引 (重建模式) ---
            print("正在重建全文索引...")
            try:
                await session.run("DROP INDEX entityNameIndex IF EXISTS")
            except Exception as e:
                print(f"删除旧索引提示: {e}")

            await session.run("""
                CREATE FULLTEXT INDEX entityNameIndex
                FOR (n:Entity) ON EACH [n.name]
            """)
            
            # --- 3. 等待索引上线 ---
            print("正在等待索引构建生效(db.awaitIndexes)...")
            try:
                await session.run("CALL db.awaitIndexes()")
            except Exception as e:
                print(f"等待命令警告: {e}, 改为手动异步等待 5 秒...")
                await asyncio.sleep(5)
                
            print("索引初始化完成！")

    async def import_data(self, file_path):
        """读取文件并批量导入四元组"""
        if not os.path.exists(file_path):
            print(f"错误: 文件 {file_path} 不存在")
            return

        print(f"开始导入并计算 Embedding {file_path} ...")
        
        batch_size = 512
        total_count = 0
        all_embeddings_list = []
        global_idx_counter = 0

        async with self.driver.session(database=self.database) as session:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
                # 分批处理
                for i in range(0, len(lines), batch_size):
                    batch_lines = lines[i : i + batch_size]
                    text_to_embed = []
                    parsed_triples = []

                    for line in batch_lines:
                        line = line.strip()
                        if not line: continue
                        parts = line.split('\t')
                        if len(parts) >= 4:
                            subj, pred, obj, date = parts[0], parts[1], parts[2], parts[3]
                            subj = subj.replace("_", " ")
                            obj = obj.replace("_", " ")
                            pred_clean = pred.replace("_", " ")

                            # 构造用于 Embedding 的自然语言句子 (保持和检索时一致)
                            fact_text = f"{subj} {pred_clean} {obj} in {date}"
                            text_to_embed.append(fact_text)
                            parsed_triples.append({"subj": subj, "pred": pred, "obj": obj, "date": date})

                    if not parsed_triples:
                        continue

                    # 1. 批量计算 Embedding (调用你现有的 self.encoder)
                    # 注意：这里需要确保在 import 时 model 已经 load 了
                    # BGE 返回的是 numpy array，需要转成 list 才能存入 Neo4j
                    embeddings = self.encoder.encode_corpus(text_to_embed,
                                                   batch_size=len(text_to_embed),
                                                   return_dense=True,
                                                   return_sparse=False,
                                                   return_colbert_vecs=False)['dense_vecs']
                    all_embeddings_list.append(embeddings)

                    # 2. 准备写入 Neo4j 的数据
                    batch_params = []
                    for j, triple in enumerate(parsed_triples):
                        current_idx = global_idx_counter + j
                        batch_params.append({
                            "subj": triple["subj"],
                            "obj": triple["obj"],
                            "date": triple["date"],
                            "emb_idx": current_idx      # 只能存list
                        })

                    global_idx_counter += len(parsed_triples)

                    # 3. 执行写入 
                    # 关系名作为类型传入
                    # Cypher 语法限制，关系类型（Relationship Type）不能作为参数（Parameter）传递
                    for j, params in enumerate(batch_params):
                        pred = parsed_triples[j]["pred"]
                        query = f"""
                        MERGE (s:Entity {{name: $subj}})
                        MERGE (o:Entity {{name: $obj}})
                        MERGE (s)-[r:`{pred}` {{date: $date}}]->(o)
                        SET r.emb_idx = $emb_idx
                        """
                        await session.run(query, **params)

                    total_count += len(batch_params)
                    print(f"已处理 {total_count} 条数据...")

        # 4. 所有批次处理完后，保存 .npy 文件
        print("正在合并向量并保存到本地 .npy 文件...")
        if all_embeddings_list:
            # 将 list of arrays 堆叠成一个大矩阵 (N, 1024)
            full_matrix = np.vstack(all_embeddings_list).astype(np.float32)
            np.save(Config.NPY, full_matrix)
            print(f"向量已保存至 {Config.NPY}, Shape: {full_matrix.shape}")
        else:
            print("警告：没有生成任何向量数据。")

        print(f"导入完成，共导入 {global_idx_counter} 条四元组。")

    async def _execute_batch(self, session, batch_queries):
        """辅助函数：在一个事务中执行多个写操作"""
        async def work(tx):
            for query, params in batch_queries:
                await tx.run(query, **params)
        
        await session.execute_write(work)

    def _build_faiss_index(self, n_clusters=100, nprobe=10, embedding_size=1024): # Reduced clusters for stability
        quantizer = faiss.IndexFlatIP(embedding_size)
        index = faiss.IndexIVFFlat(quantizer, embedding_size, n_clusters, faiss.METRIC_INNER_PRODUCT)
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

    async def retrieve_facts_by_name(self, entity_names):
        """
        根据实体列表，从 Neo4j 中检索相关的一跳子图事实。
        包含针对双实体的性能优化。
        """
        unique_facts_map = {}
        flag = True
        
        # 去重并转为列表
        unique_names = list(set([n for n in entity_names if n]))
        
        async with self.driver.session(database=self.database) as session:
            
            if len(unique_names) == 2:
                name1, name2 = unique_names[0], unique_names[1]
                
                # 直接查询两个实体之间的关系 (无向)
                # 这种查询对于 Neo4j 来说是瞬间完成的
                query = """
                MATCH (n1:Entity {name: $name1})-[r]-(n2:Entity {name: $name2})
                RETURN 
                    startNode(r).name AS source, 
                    TYPE(r) AS rel, 
                    endNode(r).name AS target, 
                    r.date AS date,
                    r.emb_idx as idx
                """
                result = await session.run(query, name1=name1, name2=name2)
                records = []
                async for record in result: records.append(record)

                # 两个实体间不存在关联时，采用单一实体查询
                if len(records) > 0:
                    for record in records:
                        self._process_record(record, unique_facts_map)
                    flag = False
            if flag:
                for name in unique_names:
                    # 原有的单点发散查询
                    query = """
                    MATCH (n:Entity {name: $name})-[r]-(neighbor)
                    RETURN 
                        startNode(r).name AS source, 
                        TYPE(r) AS rel, 
                        endNode(r).name AS target, 
                        r.date AS date,
                        r.emb_idx as idx
                    """
                    result = await session.run(query, name=name)
                    records = []
                    async for record in result: records.append(record)

                    # 模糊匹配回退
                    if not records:
                        similar_name = await self.find_similarity_entity(session, name)
                        if similar_name:
                             result = await session.run(query, name=similar_name)
                             async for record in result:
                                 records.append(record)

                    for record in records:
                        self._process_record(record, unique_facts_map)

        return list(unique_facts_map.values())

    def _process_record(self, record, unique_facts_map):
        rel = record['rel'].replace("_", " ")
        fact_str = f"{record['source']} {rel} {record['target']} in {record['date']}"
        
        # 获取 ID
        idx = record.get('idx')
        if idx is None: return # 容错

        if fact_str not in unique_facts_map:
            unique_facts_map[fact_str] = {
                "text": fact_str,
                "idx": idx  # 存 ID 而不是 Embedding
            }

    async def find_similarity_entity(self, session, query_text, threshold=0.7):
        lucene_query = f"{query_text}~"
        cql = """
        CALL db.index.fulltext.queryNodes("entityNameIndex", $search_text) YIELD node, score
        WHERE score > $threshold
        RETURN node.name as name, score
        ORDER BY score DESC
        LIMIT 1
        """
        # 注意：这里不需要再 with session，因为是用外部传入的 session
        result = await session.run(cql, search_text=lucene_query, threshold=threshold)
        records = [r async for r in result]
        
        if not records:
            # print(f"未找到与 '{query_text}' 相似的实体")
            return None
        return records[0]['name']

    async def get_embedding(self, corpus_list):
        result =  await asyncio.to_thread(
            self.encoder.encode_queries,
            corpus_list,
            return_dense=True,
            return_sparse=False,
            return_colbert_vecs=False
        )
        return result['dense_vecs']
    
    async def compute_similarity(self, question, entity_names, n):
        facts_data = await self.retrieve_facts_by_name(entity_names)

        # 边界情况处理：如果没有找到任何事实，直接返回空
        if not facts_data:
            print(f"未找到关于 {entity_names} 的任何事实")
            return []

        # 2. 分离文本和 ID
        fact_texts = [item['text'] for item in facts_data]
        fact_indices = [item['idx'] for item in facts_data]

        if self.vector_cache is None:
             raise ValueError("Vector cache not loaded!")
             
        facts_embeddings = self.vector_cache[fact_indices]
        question_embedding = await self.get_embedding([question])

        # 计算余弦相似度
        scores = util.cos_sim(question_embedding, facts_embeddings)[0]

        # 排序并取 Top N
        results = []
        for idx, score in enumerate(scores):
            results.append({
                "fact": fact_texts[idx],
                "score": float(score)
            })

        # 按分数降序排列
        results.sort(key=lambda x: x["score"], reverse=True)

        return results[:n]
    
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
        return result


async def main():
    print("============================== 从图数据库中查询的结果 =================================")
    retriever = TemporalKnowledgeGraph(uri=Config.URI,
                                    user=Config.USER,
                                    password=Config.PASSWORD,
                                    database=Config.DATABASE
                                    )
    await retriever.load(kg_path=Config.KG_PATH, encoder=Config.BGE, reranker=Config.RERANKER)

    question = "Which entity paid a visit to China on 2013-05-08?"
    entity_names = ["China"]

    graph_facts = await retriever.compute_similarity(question, entity_names, n=10)
    index_facts = await retriever.get_faiss_similarity(question, n=10)
    print(f"neo4j facts: {graph_facts}\nfaiss facts: {index_facts}")
    await retriever.close()

if __name__ == "__main__":
    asyncio.run(main())