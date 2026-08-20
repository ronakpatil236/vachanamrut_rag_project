# src/config.py
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Base Directories
SRC_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SRC_DIR.parent

# Data Directories
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
VECTOR_STORE_DIR = DATA_DIR / "vector_store"
RESULTS_DIR = PROJECT_ROOT / "results"

# Vector DB Paths (Distinct directories for chunking strategy comparisons)
RECURSIVE_DB_PATH = VECTOR_STORE_DIR / "recursive_db"
LLM_CHROMA_DB_PATH = VECTOR_STORE_DIR / "llm_chunked_db"
CHROMA_DB_PATH = VECTOR_STORE_DIR / "chroma_db"

# Auto-create necessary directories if they do not exist
for path in [RAW_DATA_DIR, PROCESSED_DATA_DIR, VECTOR_STORE_DIR, RESULTS_DIR]:
    path.mkdir(parents=True, exist_ok=True)

# API Keys & Models
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Primary RAG Models
EMBEDDING_MODEL = "text-embedding-3-small"
LLM_MODEL = "gpt-4o-mini"

# Evaluation Model
EVAL_MODEL = "gemini-1.5-flash"

# Retrieval & Reranking Parameters
RETRIEVAL_K = 10      # Number of candidates fetched from initial vector search
TOP_K_RERANK = 3      # Top reranked chunks sent to final answer LLM