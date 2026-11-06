from pathlib import Path
from uuid import uuid4
import fitz
from docx import Document as DocxDocument
import pandas as pd

from backend.app.config import DATA_DIR

UPLOAD_DIR = DATA_DIR / "uploads"
DOCUMENTS = {}

def extract_file(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        with fitz.open(path) as pdf:
            return "\n".join(page.get_text() for page in pdf)
    if suffix == ".docx":
        doc = DocxDocument(path)
        return "\n".join(p.text for p in doc.paragraphs)
    if suffix in (".xlsx", ".xls"):
        sheets = pd.read_excel(path, sheet_name=None)
        return "\n\n".join(f"Sheet: {name}\n{frame.to_string(index=False)}" for name, frame in sheets.items())
    if suffix == ".csv":
        return pd.read_csv(path).to_string(index=False)
    if suffix == ".txt":
        return path.read_text(encoding="utf-8", errors="ignore")
    raise ValueError("Supported formats: PDF, DOCX, XLSX, CSV, TXT")

def split_text(text: str, size: int = 900, overlap: int = 120):
    text = " ".join(text.split())
    if not text:
        return []
    chunks, start = [], 0
    while start < len(text):
        end = min(start + size, len(text))
        chunks.append(text[start:end])
        if end == len(text):
            break
        start = max(end - overlap, start + 1)
    return chunks

async def save_upload(filename: str, content: bytes):
    doc_id = str(uuid4())
    safe_name = Path(filename).name
    path = UPLOAD_DIR / f"{doc_id}_{safe_name}"
    path.write_bytes(content)
    DOCUMENTS[doc_id] = {"document_id": doc_id, "filename": safe_name, "path": str(path), "text": None}
    return DOCUMENTS[doc_id]

def get_document(document_id: str):
    if document_id not in DOCUMENTS:
        raise KeyError("Document not found in this running session. Upload it again after restarting the server.")
    return DOCUMENTS[document_id]

def extract_document(document_id: str):
    item = get_document(document_id)
    text = extract_file(Path(item["path"]))
    item["text"] = text
    item["chunks"] = split_text(text)
    return item
