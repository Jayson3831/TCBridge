import os
import datetime

# 时间戳后缀
time_suffix = datetime.datetime.now().strftime("%m%d%H")

class Config:
    """模型配置类"""
    # 需要调节的参数
    SAMPLE_NUM = 5
    RETRIEVER = "bge"
    REBUILD_NEO4J = False
    FACTS_NUM = 100
    RERANK_NUM = 10
    ANCHOR_EVENT_NUM = 3
    
    # 数据配置
    DATA_PATH = f"../Datasets/MultiTQ/questions/test_{SAMPLE_NUM}.json"
    KG_PATH = "../Datasets/MultiTQ/kg/full.txt"
    OUTPUT_DIR = f"output_{SAMPLE_NUM}/"
    PROMPT_DIR = "prompt/"
    PROMPTS_FILE = f"temp/prompts_{SAMPLE_NUM}.json"
    PREDICTIONS_FILE = f"predictions_{SAMPLE_NUM}.json"
    BEST_SUBQ_FILE = f"temp/best_subquestions_{SAMPLE_NUM}.json"
    SUBQ_FORMATTED_FILE = f"temp/subq_{SAMPLE_NUM}_formatted.json"
    RESULT_FILE = f"results/test_{SAMPLE_NUM}_results_{RETRIEVER}_{time_suffix}.json"
    Q2A_FILE = f"results/q2a_{SAMPLE_NUM}_{RETRIEVER}_{time_suffix}.json"
    Q2A_FULL_FILE = f"results/q2a_full_tree_{SAMPLE_NUM}_{RETRIEVER}_{time_suffix}.json"
    PROMPT_PATHS = {
        "reason": "prompt/reason.txt",
        "ir": "prompt/IR_answer.txt",
        "ag": "prompt/augmented_generation.txt",
        "final": "prompt/final_answer.txt",
        "sub": "prompt/sub_answer.txt",
        "fc": "prompt/full_context_prompt.txt"
    }
    INDEX = f"index/{RETRIEVER}_indexfull.bin"
    NPY = f"index/{RETRIEVER}_indexfull.npy"

    # 模型配置
    LLM = "deepseek-chat"
    API_KEY = os.getenv("DEEPSEEK_API_KEY")  # DeepSeek API Key
    BASE_URL = "https://api.deepseek.com"  # DeepSeek API 基础URL
    MINILM = "sentence-transformers/all-MiniLM-L6-v2"  # 本地MiniLM模型路径
    BGE = "BAAI/bge-m3"
    RERANKER = "BAAI/bge-reranker-v2-m3"
    EMBEDDING_DIM = 384  # MiniLM模型的嵌入维度
    MAX_LENGTH = 256  # MiniLM模型的最大长度
    NUM_CLASSES = 2
    DROPOUT = 0.3
    MODEL_TYPE = "sentence_transformer"  # 模型类型
    POSITIVE_CLASS = 1  # 正类标签
    # 匹配特征选择：可选项 ["q", "s", "abs_diff", "elem_mul", "cos_sim"]
    MATCH_FEATURES = ["abs_diff", "cos_sim"]
    
    # 并发配置
    MAX_SPLIT = min(64, os.cpu_count() or 8)  # 最大进程数，限制在64以内
    STEP_SIZE = 4  # 每个进程处理的问题数
    CONCURRENCY = 8

    # 训练配置
    BATCH_SIZE = 16
    LEARNING_RATE = 0.001  # 3e-5
    EPOCHS = 30
    RANDOM_SEED = 42
    USE_WEIGHTED_SAMPLER = True  # 是否使用加权采样以平衡类别
    USE_CLASS_WEIGHTS = True     # 是否在损失函数中使用类别权重
    LOSS_TYPE = "focal"          # "ce" 或 "focal"
    FOCAL_GAMMA = 2.0            # focal loss 的gamma
    FOCAL_ALPHA = 0.25           # focal损失正类权重alpha
    
    # 数据集划分比例
    TEST_SIZE = 0.3
    VAL_SIZE = 0.15  # 从剩余30%中再划分50%
    
    # 设备配置
    DEVICE = "cuda"  # 自动检测
    GPU_ID = 4
    
    # 文件路径
    # 路径跨平台处理
    _ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
    _MODELS_DIR = os.path.join(_ROOT_DIR, "best_model")
    BEST_MODEL_PATH = os.path.join(_MODELS_DIR, "best_model.pth")
    TRAINING_HISTORY_PATH = os.path.join(_MODELS_DIR, "training_history.png")
    
    # 早停配置
    PATIENCE = 8
    MIN_DELTA = 0.001
    
    # 学习率调度配置
    SCHEDULER_STEP_SIZE = 3
    SCHEDULER_GAMMA = 0.1
    
    # 阈值搜索指标："f1" | "balanced_accuracy" | "mcc"
    THRESHOLD_METRIC = "balanced_accuracy"

    # NEO4J配置
    URI = "bolt://localhost:7687"
    USER = "neo4j"
    PASSWORD = "JS09098614"
    DATABASE = "TKGQA"