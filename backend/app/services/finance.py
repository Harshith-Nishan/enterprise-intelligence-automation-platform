import json
import re
from decimal import Decimal, InvalidOperation
from backend.app.services.llm import generate
from backend.app.services.documents import get_document

EXTRACTION_PROMPT = '''Extract financial information from the following business document.
Return ONLY valid JSON with this structure:
{
 "document_number": "",
 "vendor": "",
 "buyer": "",
 "currency": "INR",
 "reference_number": "",
 "line_items": [{"description":"","quantity":0,"unit_price":0,"line_total":0}],
 "subtotal": 0,
 "tax": 0,
 "shipping": 0,
 "discount": 0,
 "grand_total": 0
}
Use numbers without currency symbols or commas. Use null when a value is not available.
Document type: {doc_type}
Document text:
{text}
'''

def _number(value):
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return float(value)
    raw = str(value).strip().replace(",", "").replace("₹", "").replace("$", "").replace("€", "").replace("£", "")
    raw = raw.replace("%", "")
    if raw.startswith("(") and raw.endswith(")"):
        raw = "-" + raw[1:-1]
    raw = re.sub(r"[^0-9.\\-]", "", raw)
    try:
        return float(Decimal(raw))
    except (InvalidOperation, ValueError):
        return None

def extract_financial(document_id: str, doc_type: str):
    item = get_document(document_id)
    if not item.get("text"):
        raise ValueError("Extract document text before financial extraction.")
    raw = generate(EXTRACTION_PROMPT.format(doc_type=doc_type, text=item["text"][:14000]))
    match = re.search(r"\\{.*\\}", raw, re.S)
    if not match:
        raise ValueError("The local model did not return a JSON object.")
    data = json.loads(match.group())
    for field in ("subtotal", "tax", "shipping", "discount", "grand_total"):
        data[field] = _number(data.get(field))
    for line in data.get("line_items", []):
        for field in ("quantity", "unit_price", "line_total"):
            line[field] = _number(line.get(field))
    data["document_id"] = document_id
    data["document_type"] = doc_type
    return data

def compare_financial(po: dict, invoice: dict):
    discrepancies = []
    po_lines = po.get("line_items", [])
    inv_lines = invoice.get("line_items", [])
    for idx, (a, b) in enumerate(zip(po_lines, inv_lines)):
        if (a.get("quantity") or 0) != (b.get("quantity") or 0):
            discrepancies.append({"type": "quantity_mismatch", "line": idx + 1,
                                  "purchase_order": a, "invoice": b})
        if (a.get("line_total") or 0) != (b.get("line_total") or 0):
            discrepancies.append({"type": "line_total_mismatch", "line": idx + 1,
                                  "purchase_order": a, "invoice": b})
    if len(po_lines) != len(inv_lines):
        discrepancies.append({"type": "line_item_count_mismatch",
                              "purchase_order_count": len(po_lines), "invoice_count": len(inv_lines)})
    for field in ("subtotal", "tax", "shipping", "grand_total"):
        if po.get(field) is not None and invoice.get(field) is not None and po[field] != invoice[field]:
            discrepancies.append({"type": f"{field}_mismatch", "purchase_order": po[field], "invoice": invoice[field]})
    return {"status": "discrepancy_detected" if discrepancies else "no_discrepancies",
            "discrepancies": discrepancies, "discrepancy_count": len(discrepancies)}
