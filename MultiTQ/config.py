import argparse
import os

def parse_args():
    parser = argparse.ArgumentParser(description='Configuration for TKGQA Retriever')

    # Model settings
    parser.add_argument('--best_model', type=str, default='best_model/best_model.pth',
                        help='Path to best model')
    parser.add_argument('--minilm', type=str, default='sentence-transformers/all-MiniLM-L6-v2',
                        help='Path to MiniLM model')
    parser.add_argument('--bge_model', type=str, default='BAAI/bge-m3',
                        help='Path to BGE encoder model')
    parser.add_argument('--reranker_model', type=str, default='BAAI/bge-reranker-v2-m3',
                        help='Path to reranker model')
    parser.add_argument('--llm', type=str, default='deepseek-chat',
                        help='LLM model')
    parser.add_argument('--api_key', type=str, default=os.getenv('DEEPSEEK_API_KEY'),
                        help='API key for llm')
    parser.add_argument('--base_url', type=str, default='https://api.deepseek.com',
                        help='Base URL for llm API')

    # Data settings
    parser.add_argument('--kg_path', type=str, default='../Datasets/multitq/kg/full.txt',
                        help='Path to knowledge graph data')
    parser.add_argument('--index_path', type=str, default='index/full_faiss.bin',
                        help='Path to FAISS index file')
    parser.add_argument('--suffix', type=str, default='',
                        help='Suffix for output files')
    parser.add_argument('--dataset', type=str, default='multitq',
                        help='Path to question file')
    parser.add_argument('--dataset_type', type=str, default='test',
                        help='Type of dataset (train/val/test)')

    # Model parameters
    parser.add_argument('--embedding_size', type=int, default=1024,
                        help='Embedding dimension size')
    parser.add_argument('--use_gpu', action='store_true', default=True,
                        help='Use GPU for inference')
    parser.add_argument('--gpu_id', type=int, default=4,
                        help='GPU device ID')
    parser.add_argument('--temperature', type=float, default=0.0,
                        help='Temperature for llm sampling')
    parser.add_argument('--max_length', type=int, default=8192,
                        help='Maximum length of llm input sequences')
    parser.add_argument('--concurrent_limit', type=int, default=8,
                        help='Maximum number of concurrent requests')

    # FAISS parameters
    parser.add_argument('--n_clusters', type=int, default=100,
                        help='Number of clusters for FAISS index')
    parser.add_argument('--nprobe', type=int, default=10,
                        help='Number of clusters to probe during FAISS search')

    # hyperparameters
    parser.add_argument('--top_k', type=int, default=60,
                        help='Number of top results to retrieve')
    parser.add_argument('--rerank_top_k', type=int, default=5,
                        help='Number of top results to rerank')
    parser.add_argument('--conf_threshold', type=float, default=0.6,
                        help='Threshold of confidence.')
    parser.add_argument('--entropy_threshold', type=float, default=0.4,
                        help='Threshold of entropy.')
    parser.add_argument('--temp', type=float, default=0.1,
                        help='Temperature of faiss entropy.')

    # Other parameters
    parser.add_argument('--sample', type=int, default=500,
                        help='Number of samples to draw')

    # evaluation parameters
    parser.add_argument('--hit_k', type=int, default=1,
                        help='Hit@k for evaluation')


    return parser.parse_args()

args = parse_args()


if __name__ == "__main__":
    pass