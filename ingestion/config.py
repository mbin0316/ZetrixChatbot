import os
from dotenv import load_dotenv

load_dotenv()

OLLAMA_BASE_URL  = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
LLM_MODEL        = os.getenv("LLM_MODEL", "qwen2.5:7b")
EMBEDDING_MODEL  = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
EMBEDDING_DIM    = 768   # nomic-embed-text output dimension

# Qdrant
QDRANT_URL       = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY   = os.getenv("QDRANT_API_KEY", "")
COLLECTION_NAME  = os.getenv("COLLECTION_NAME", "hh_income")

# Dataset
DATASETS_DIR     = os.path.join(os.path.dirname(__file__), "..", "datasets")

# Chunking
CHUNK_SIZE       = 800   # chars (~200 tokens)
CHUNK_OVERLAP    = 200   # chars (~50 tokens)
TOP_K            = 5