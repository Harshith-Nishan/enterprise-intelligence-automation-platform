import json
import sqlite3
from datetime import datetime, timezone
from uuid import uuid4
from backend.app.config import SQLITE_PATH

def connect():
    conn = sqlite3.connect(SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def initialize():
    with connect() as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS reviews (
            report_id TEXT PRIMARY KEY,
            decision TEXT,
            reviewer TEXT,
            comments TEXT,
            updated_at TEXT
        )''')

def save_report(report: dict):
    report_id = str(uuid4())
    report["report_id"] = report_id
    report["created_at"] = datetime.now(timezone.utc).isoformat()
    path = __import__("pathlib").Path(__file__).resolve().parents[2] / "data" / "reports"
    path.mkdir(parents=True, exist_ok=True)
    (path / f"{report_id}.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report

def get_report(report_id: str):
    from pathlib import Path
    path = Path(__file__).resolve().parents[2] / "data" / "reports" / f"{report_id}.json"
    if not path.exists():
        raise KeyError("Report not found")
    return json.loads(path.read_text(encoding="utf-8"))

def save_decision(report_id: str, decision: str, reviewer: str, comments: str):
    with connect() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO reviews VALUES (?, ?, ?, ?, ?)",
            (report_id, decision, reviewer, comments, datetime.now(timezone.utc).isoformat())
        )
    return {"report_id": report_id, "decision": decision, "reviewer": reviewer, "comments": comments}

def get_decision(report_id: str):
    with connect() as conn:
        row = conn.execute("SELECT * FROM reviews WHERE report_id=?", (report_id,)).fetchone()
    return dict(row) if row else None
