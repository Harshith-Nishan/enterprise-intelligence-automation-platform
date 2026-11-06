# Enterprise Intelligence & Automation Platform

A local-first document intelligence application built with FastAPI, React, TypeScript, Ollama, Sentence Transformers, Qdrant, and LangGraph.

## Features

- Upload PDF, DOCX, XLSX, and CSV documents.
- Extract document text and split it into chunks.
- Generate embeddings and index document chunks in Qdrant.
- Search indexed content and ask questions using a local Ollama model.
- Extract financial information from purchase orders and invoices.
- Compare line items and document totals to surface discrepancies.
- Generate an investigation report and record a human review decision.

All processing is user-triggered. Uploading a document does not automatically run the full workflow. Financial outputs are for human review and must not be treated as autonomous payment authorization.

## Requirements

- Python 3.12
- Node.js 20+
- Ollama installed locally
- Qdrant client local mode (no separate Qdrant server required)

## Backend setup (Windows PowerShell)

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
ollama pull qwen2.5:1.5b
uvicorn backend.app.main:app --reload
```

Open `http://127.0.0.1:8000/docs`.

## Frontend setup

In a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open the local Vite URL shown in the terminal.

## Configuration

Review `.env.example`. The default paths are relative to the repository. Do not commit `.env`, uploaded documents, local databases, model weights, or Qdrant storage.

## Workflow

1. Upload a document.
2. Extract its text.
3. Generate embeddings and index it.
4. Search or ask questions against indexed documents.
5. Extract financial fields from a purchase order and invoice.
6. Compare the extracted records.
7. Run an investigation and review its report.
8. Approve or reject the report.

## Notes

- The local LLM may return incomplete or incorrect values. Validate extracted financial data against the original document.
- Scanned PDFs may require OCR; OCR is not included in this initial implementation.
- This is a portfolio/development application, not a production financial-control system.
