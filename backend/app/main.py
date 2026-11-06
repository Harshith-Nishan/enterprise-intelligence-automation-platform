from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from backend.app.schemas import AskRequest, SearchRequest, FinancialExtractRequest, CompareRequest, DecisionRequest
from backend.app.services.documents import save_upload, extract_document, get_document
from backend.app.services.retrieval import index_chunks, search_chunks
from backend.app.services.llm import generate
from backend.app.services.finance import extract_financial, compare_financial
from backend.app.services.storage import initialize, save_report, get_report, save_decision, get_decision

app = FastAPI(title="Enterprise Intelligence & Automation Platform", version="1.0.0")
app.add_middleware(
    CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"]
)
FINANCIAL_RECORDS = {}

@app.on_event("startup")
def startup():
    initialize()

@app.get("/api/health")
def health():
    return {"status": "ok", "service": "enterprise-intelligence-platform"}

@app.post("/api/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    try:
        item = await save_upload(file.filename or "uploaded_file", await file.read())
        return {"document_id": item["document_id"], "filename": item["filename"], "status": "uploaded"}
    except Exception as exc:
        raise HTTPException(400, str(exc))

@app.post("/api/documents/{document_id}/extract")
def extract(document_id: str):
    try:
        item = extract_document(document_id)
        return {"document_id": document_id, "filename": item["filename"],
                "character_count": len(item["text"]), "chunk_count": len(item["chunks"]),
                "preview": item["text"][:1200]}
    except Exception as exc:
        raise HTTPException(400, str(exc))

@app.post("/api/documents/{document_id}/index")
def index_document(document_id: str):
    try:
        item = get_document(document_id)
        if not item.get("chunks"):
            raise ValueError("Extract the document before indexing.")
        count = index_chunks(document_id, item["filename"], item["chunks"])
        return {"document_id": document_id, "indexed_chunks": count}
    except Exception as exc:
        raise HTTPException(400, str(exc))

@app.post("/api/documents/search")
def search(request: SearchRequest):
    try:
        return {"results": search_chunks(request.query, request.top_k, request.document_id)}
    except Exception as exc:
        raise HTTPException(400, str(exc))

@app.post("/api/documents/ask")
def ask(request: AskRequest):
    try:
        hits = search_chunks(request.question, request.top_k, request.document_id)
        if not hits:
            return {"answer": "No indexed document passages were found for this question.", "sources": []}
        context = "\n\n".join(
            f"[Source {i+1}: {h['filename']} | chunk {h['chunk_index']}]\n{h['text']}"
            for i, h in enumerate(hits)
        )
        prompt = ("Answer the question using only the supplied context. If the context does not contain "
                  "the answer, say so. Cite source numbers in your answer.\n\n"
                  f"Context:\n{context}\n\nQuestion: {request.question}\nAnswer:")
        answer = generate(prompt)
        return {"answer": answer, "sources": hits}
    except Exception as exc:
        raise HTTPException(400, str(exc))

@app.post("/api/financial/extract")
def financial_extract(request: FinancialExtractRequest):
    try:
        record = extract_financial(request.document_id, request.document_type)
        FINANCIAL_RECORDS[request.document_id] = record
        return record
    except Exception as exc:
        raise HTTPException(400, str(exc))

@app.post("/api/financial/compare")
def financial_compare(request: CompareRequest):
    try:
        po = FINANCIAL_RECORDS[request.purchase_order_id]
        invoice = FINANCIAL_RECORDS[request.invoice_id]
        return compare_financial(po, invoice)
    except KeyError:
        raise HTTPException(404, "Extract both financial documents in this server session before comparing.")
    except Exception as exc:
        raise HTTPException(400, str(exc))

@app.post("/api/financial/investigate")
def investigate(request: CompareRequest):
    try:
        po = FINANCIAL_RECORDS[request.purchase_order_id]
        invoice = FINANCIAL_RECORDS[request.invoice_id]
        comparison = compare_financial(po, invoice)
        report = save_report({
            "purchase_order": po, "invoice": invoice, "comparison": comparison,
            "summary": f"Investigation completed. {comparison['discrepancy_count']} discrepancy item(s) identified."
        })
        return report
    except KeyError:
        raise HTTPException(404, "Extract both financial documents in this server session before investigation.")
    except Exception as exc:
        raise HTTPException(400, str(exc))

@app.get("/api/financial/reports/{report_id}")
def report(report_id: str):
    try:
        return get_report(report_id)
    except KeyError as exc:
        raise HTTPException(404, str(exc))

@app.post("/api/financial/reports/{report_id}/decision")
def decision(report_id: str, request: DecisionRequest):
    try:
        get_report(report_id)
        return save_decision(report_id, request.decision, request.reviewer, request.comments)
    except KeyError as exc:
        raise HTTPException(404, str(exc))

@app.get("/api/financial/reports/{report_id}/decision")
def read_decision(report_id: str):
    return {"decision": get_decision(report_id)}
