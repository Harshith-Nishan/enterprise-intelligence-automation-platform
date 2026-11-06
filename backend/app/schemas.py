from pydantic import BaseModel, Field
from typing import Optional, Literal

class AskRequest(BaseModel):
    question: str
    top_k: int = Field(default=5, ge=1, le=20)
    document_id: Optional[str] = None

class SearchRequest(BaseModel):
    query: str
    top_k: int = Field(default=5, ge=1, le=20)
    document_id: Optional[str] = None

class FinancialExtractRequest(BaseModel):
    document_id: str
    document_type: Literal["purchase_order", "invoice"]

class CompareRequest(BaseModel):
    purchase_order_id: str
    invoice_id: str

class DecisionRequest(BaseModel):
    decision: Literal["approved", "rejected"]
    reviewer: str
    comments: str = ""
