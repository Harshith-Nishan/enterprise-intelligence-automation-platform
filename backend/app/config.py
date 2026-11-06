import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = Path(os.getenv("DATA_DIR", ROOT / "data"))
QDRANT_PATH = Path(os.getenv("QDRANT_PATH", DATA_DIR / "qdrant"))
SQLITE_PATH = Path(os.getenv("SQLITE_PATH", DATA_DIR / "approvals.db"))
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:1.5b")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
COLLECTION = "enterprise_documents"

for folder in (DATA_DIR, QDRANT_PATH, DATA_DIR / "uploads", DATA_DIR / "reports"):
    folder.mkdir(parents=True, exist_ok=True)
