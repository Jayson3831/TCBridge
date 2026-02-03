# TCBridge: Temporal Knowledge Graph Question Answering

A comprehensive framework for **Temporal Knowledge Graph Question Answering (TKGQA)** that combines question decomposition, event retrieval, and temporal reasoning to answer complex time-based questions over knowledge graphs.

## Installation

### Prerequisites

- Python 3.8+
- CUDA-compatible GPU (recommended)
- DeepSeek API key

### Setup

```bash
# Clone the repository
git clone https://github.com/Jayson3831/TCBridge.git
cd TCBridge

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Linux/Mac
# or
venv\Scripts\activate     # On Windows

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Set your DeepSeek API key as an environment variable:

```bash
export DEEPSEEK_API_KEY="your_api_key_here"
```

Or create a `.env` file:

```
DEEPSEEK_API_KEY=your_api_key_here
```

## Usage

### MultiTQ Dataset

```bash
cd MultiTQ
python src.py --dataset multitq --sample 500 --llm deepseek-chat --api_key 'your_api_key' --base_url https://api.deepseek.com --temperature 0 --top_k 60 --conf_threshold 0.7 --entropy_threshold 0.6 --temp 1.0 --concurrent_limit 8 --hit_k 1
```

### TimelineKGQA Datasets

```bash
cd TimelineKGQA

# CronQuestions dataset
python src.py --dataset cron --sample 500 --llm deepseek-chat --api_key 'your_api_key' --base_url https://api.deepseek.com --temperature 0 --top_k 60 --conf_threshold 0.7 --entropy_threshold 0.6 --temp 1.0 --concurrent_limit 8 --hit_k 1

# ICEWS Actor dataset
python src.py --dataset icews_actor --sample 500 --llm deepseek-chat --api_key 'your_api_key' --base_url https://api.deepseek.com --temperature 0 --top_k 60 --conf_threshold 0.7 --entropy_threshold 0.6 --temp 1.0 --concurrent_limit 8 --hit_k 1
```

### Command Line Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `--llm` | LLM model | deepseek-chat |
| `--api_key` | API key for llm | your_api_key |
| `--base_url` | Base URL for llm API | https://api.deepseek.com |
| `--dataset` | Dataset name | multitq / cron / icews_actor |
| `--sample` | Number of samples | 500 |
| `--top_k` | Top-k retrieval results | 60 |
| `--rerank_top_k` | Top-k re-ranking results | 5 |
| `--conf_threshold` | Threshold of confidence | 0.7 |
| `--entropy_threshold` | Threshold of entropy | 0.6 |
| `--temp` | Temperature of faiss entropy | 1.0 |
| `--concurrent_limit` | Concurrent request limit | 8 |
| `--hit_k'` | Hit@k for evaluation | 1 |

## Project Structure

```
tcbridge/
├── MultiTQ/                   # MultiTQ dataset module
│   ├── config.py              # Configuration
│   ├── src.py                 # Main entry point
│   ├── Retriever.py           # FAISS retriever
│   ├── eval.py                # Evaluation module
│   ├── prompts.py             # Prompt templates
│   ├── utils.py               # Utility functions
│   ├── index/                 # FAISS indexes
│   ├── outputs/               # Output results
│   └── results/               # Evaluation metrics
├── TimelineKGQA/              # TimelineKGQA datasets module
│   └── (same structure as MultiTQ/)
├── Datasets/                  # Data storage
│   ├── multitq/               # MultiTQ data
│   ├── cron/                  # CronQuestions data
│   ├── icews_actor/           # ICEWS Actor data
│   └── scripts/               # Data processing scripts
└── requirements.txt           # Dependencies
```

## Dependencies

- **faiss_gpu** - Vector similarity search
- **FlagEmbedding** - BGE embedding & reranker models
- **torch** - Deep learning framework
- **sentence_transformers** - Sentence embeddings
- **openai** - LLM API client
- **pandas** - Data processing
- **python_dateutil** - Date parsing

## Output

Results are saved in:
- `outputs/` - Detailed predictions and intermediate results
- `results/` - Evaluation metrics and accuracy scores

## Citation

If you use this code in your research, please cite:

```bibtex

```
