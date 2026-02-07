# app.py
# AETERNA-FS — Payment + Certificate Generation
# Python 3.9 / FastAPI
from dotenv import load_dotenv
from typing import Optional
from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.responses import RedirectResponse, FileResponse, HTMLResponse
from reports.pdf_generator import generate_audit_report
from pathlib import Path
from datetime import datetime
import uuid
import hashlib
import json
import logging
import sqlite3
import stripe
import os

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("aeterna")


# Amount in cents (900 = $9.00 USD)
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
PRICE_AMOUNT = 900
MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", str(10 * 1024 * 1024)))
# Public base URL used for Stripe redirects
PUBLIC_URL = os.getenv("PUBLIC_URL", "http://localhost:8000")

app = FastAPI(title="AETERNA-FS")

# -----------------------------
# File Paths
# -----------------------------
BASE_DIR = Path(__file__).parent
VAULT_DIR = BASE_DIR / "vault"
INGEST_DIR = VAULT_DIR / "ingest"
REPORTS_DIR = VAULT_DIR / "reports"
EVENTS_JSON = VAULT_DIR / "events.json"
EVENTS_DB_PATH = VAULT_DIR / "events.db"

# Create necessary directories
INGEST_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

if not EVENTS_JSON.exists():
    EVENTS_JSON.write_text("[]", encoding="utf-8")

# -----------------------------
# Utilities
# -----------------------------
def compute_sha3_512(file_path: Path) -> str:
    h = hashlib.sha3_512()
    with open(file_path, "rb") as f:
        while True:
            chunk = f.read(4096)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def get_conn():
    conn = sqlite3.connect(EVENTS_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                file TEXT NOT NULL,
                hash TEXT NOT NULL,
                declared_by TEXT NOT NULL,
                purpose TEXT NOT NULL,
                paid INTEGER NOT NULL,
                session_id TEXT,
                payment_intent TEXT
            )
            """
        )
        conn.commit()

def db_is_empty() -> bool:
    with get_conn() as conn:
        row = conn.execute("SELECT COUNT(1) AS cnt FROM events").fetchone()
        return row["cnt"] == 0

def migrate_events_json_to_db():
    if not EVENTS_JSON.exists():
        return
    if not db_is_empty():
        return
    try:
        events = json.loads(EVENTS_JSON.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return
    if not events:
        return
    with get_conn() as conn:
        for e in events:
            conn.execute(
                """
                INSERT OR IGNORE INTO events
                (id, timestamp, file, hash, declared_by, purpose, paid, session_id, payment_intent)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    e.get("id"),
                    e.get("timestamp"),
                    e.get("file"),
                    e.get("hash"),
                    e.get("declared_by"),
                    e.get("purpose"),
                    1 if e.get("paid") else 0,
                    e.get("session_id"),
                    e.get("payment_intent"),
                ),
            )
        conn.commit()

def row_to_event(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "timestamp": row["timestamp"],
        "file": row["file"],
        "hash": row["hash"],
        "declared_by": row["declared_by"],
        "purpose": row["purpose"],
        "paid": bool(row["paid"]),
        "session_id": row["session_id"],
        "payment_intent": row["payment_intent"],
    }

def get_event_by_id(event_id: str) -> Optional[dict]:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM events WHERE id = ?",
            (event_id,),
        ).fetchone()
        return row_to_event(row) if row else None

def get_event_by_session_id(session_id: str) -> Optional[dict]:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM events WHERE session_id = ?",
            (session_id,),
        ).fetchone()
        return row_to_event(row) if row else None

def insert_event(event: dict):
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO events
            (id, timestamp, file, hash, declared_by, purpose, paid, session_id, payment_intent)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event["id"],
                event["timestamp"],
                event["file"],
                event["hash"],
                event["declared_by"],
                event["purpose"],
                1 if event.get("paid") else 0,
                event.get("session_id"),
                event.get("payment_intent"),
            ),
        )
        conn.commit()

def update_event_payment(event_id: str, paid: bool, payment_intent: Optional[str]):
    with get_conn() as conn:
        conn.execute(
            """
            UPDATE events
            SET paid = ?, payment_intent = ?
            WHERE id = ?
            """,
            (1 if paid else 0, payment_intent, event_id),
        )
        conn.commit()

def update_event_session(event_id: str, session_id: str):
    with get_conn() as conn:
        conn.execute(
            """
            UPDATE events
            SET session_id = ?
            WHERE id = ?
            """,
            (session_id, event_id),
        )
        conn.commit()

init_db()
migrate_events_json_to_db()

def safe_filename(original_name: str) -> str:
    # Strip any path components to avoid traversal
    return Path(original_name).name

def save_upload_limited(src, dest: Path, max_bytes: int) -> int:
    written = 0
    with open(dest, "wb") as f:
        while True:
            chunk = src.read(1024 * 1024)
            if not chunk:
                break
            written += len(chunk)
            if written > max_bytes:
                raise ValueError("File too large")
            f.write(chunk)
    return written

def db_health_ok() -> bool:
    try:
        with get_conn() as conn:
            conn.execute("SELECT 1").fetchone()
        return True
    except Exception:
        logger.exception("DB health check failed")
        return False

# -----------------------------
# VIEWS (English UI)
# -----------------------------

@app.get("/", response_class=HTMLResponse)
def landing():
    return """
    <html>
    <body style="font-family:Arial, sans-serif; max-width:600px; margin:40px auto; line-height:1.6; color:#333;">
        <h1>AETERNA</h1>
        <p><b>Generate a cryptographic integrity reference for a specific file version.</b></p>
        <p>
        AETERNA creates a deterministic cryptographic fingerprint (SHA3-512)
        of a file at a specific point in time and issues an integrity reference
        certificate that can be independently verified.
        </p>
        
        <form action="/preview" method="post" enctype="multipart/form-data" style="background:#f9f9f9; padding:20px; border-radius:8px; border:1px solid #eee;">
            <label><b>File in dispute:</b></label><br>
            <input type="file" name="file" required style="margin-top:10px;"><br><br>
            
            <label><b>Declared by:</b></label><br>
            <select name="declared_by" style="width:100%; padding:8px; margin-top:5px;">
                <option>Freelancer</option>
                <option>Client</option>
            </select><br><br>
            
            <label><b>Purpose / Case:</b></label><br>
            <input type="text" name="purpose" placeholder="e.g., Logo delivery v1" required style="width:100%; padding:8px; margin-top:5px;"><br><br>
            
            <button style="padding:12px 24px; background-color:#6772e5; color:white; border:none; border-radius:4px; cursor:pointer; font-weight:bold; width:100%;">
                Generate integrity reference
            </button>
        </form>
    </body>
    </html>
    """

@app.get("/health")
def health():
    checks = {
        "db": db_health_ok(),
        "stripe_key": bool(stripe.api_key),
        "webhook_secret": bool(STRIPE_WEBHOOK_SECRET),
    }
    ok = all(checks.values())
    if not ok:
        logger.error("Health check failed: %s", checks)
    status = 200 if ok else 503
    return HTMLResponse(
        content=json.dumps({"ok": ok, "checks": checks}),
        status_code=status,
        media_type="application/json",
    )

@app.get("/ready")
def ready():
    checks = {
        "db": db_health_ok(),
        "ingest_dir": INGEST_DIR.exists(),
        "reports_dir": REPORTS_DIR.exists(),
    }
    ok = all(checks.values())
    if not ok:
        logger.error("Readiness check failed: %s", checks)
    status = 200 if ok else 503
    return HTMLResponse(
        content=json.dumps({"ok": ok, "checks": checks}),
        status_code=status,
        media_type="application/json",
    )

@app.post("/preview", response_class=HTMLResponse)
def preview(
    file: UploadFile = File(...),
    declared_by: str = Form(...),
    purpose: str = Form(...)
):
    event_id = str(uuid.uuid4())
    safe_name = safe_filename(file.filename)
    dest = INGEST_DIR / f"{event_id}_{safe_name}"

    # Save the file physically with size guard
    try:
        save_upload_limited(file.file, dest, MAX_UPLOAD_BYTES)
    except ValueError:
        if dest.exists():
            dest.unlink(missing_ok=True)
        logger.warning("Upload rejected (too large): %s", safe_name)
        return HTMLResponse("File too large.", status_code=413)

    hash_val = compute_sha3_512(dest)

    event = {
        "id": event_id,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "file": safe_name,
        "hash": hash_val,
        "declared_by": declared_by,
        "purpose": purpose,
        "paid": False,
        "session_id": None,
        "payment_intent": None
    }
    insert_event(event)

    return f"""
    <html>
    <body style="font-family:Arial, sans-serif; max-width:600px; margin:40px auto; line-height:1.6;">
        <h2 style="color:#2ecc71;">File fixed</h2>

        <p>
        The exact file version has been fixed and timestamped.
        </p>

        <details style="margin-top:10px; background:#f4f4f4; padding:10px; border-radius:4px;">
            <summary style="cursor:pointer; font-weight:bold;">View technical fingerprint</summary>
            <pre style="word-break:break-all; white-space: pre-wrap; margin-top:10px; font-size:12px;">{hash_val}</pre>
        </details>

        <form action="/pay/{event_id}" method="post" style="margin-top:30px;">
            <button style="padding:14px 28px; background-color:#3ecf8e; color:white; border:none; border-radius:6px; cursor:pointer; font-size:16px; width:100%; font-weight:bold;">
                Download integrity reference certificate ($9 USD)
            </button>
        </form>

        <p style="font-size:0.9em; color:gray; margin-top:20px; text-align:center;">
        The certificate provides a cryptographic integrity reference.
        It does not constitute forensic evidence or a legal chain of custody.
        </p>
    </body>
    </html>
    """

@app.post("/pay/{event_id}")
def pay(event_id: str):
    event = get_event_by_id(event_id)
    if not event:
        return HTMLResponse("Invalid reference ID", status_code=404)

    # Create Stripe Checkout Session
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": "usd",
                "product_data": {
                    "name": f"AETERNA - Integrity Reference Certificate - ID: {event_id[:8]}",
                },
                "unit_amount": PRICE_AMOUNT,
            },
            "quantity": 1,
        }],
        mode="payment",
        metadata={
            "event_id": event_id,
        },
        success_url=f"{PUBLIC_URL}/paid/{event_id}?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{PUBLIC_URL}/",
    )
    update_event_session(event_id, session.id)
    return RedirectResponse(session.url, status_code=303)

@app.get("/paid/{event_id}")
def paid(event_id: str, session_id: Optional[str] = None):
    event = get_event_by_id(event_id)
    if not event:
        return HTMLResponse("Invalid reference ID", status_code=404)

    if not session_id or session_id != event.get("session_id"):
        logger.warning("Invalid session for event %s", event_id)
        return HTMLResponse("Missing or invalid session.", status_code=400)

    session = stripe.checkout.Session.retrieve(session_id)
    if session.payment_status != "paid":
        logger.warning("Payment not completed for event %s", event_id)
        return HTMLResponse("Payment not completed.", status_code=402)
    if session.amount_total != PRICE_AMOUNT or session.currency != "usd":
        logger.warning("Payment amount mismatch for event %s", event_id)
        return HTMLResponse("Payment amount mismatch.", status_code=400)

    update_event_payment(event_id, True, session.payment_intent)
    return RedirectResponse(f"/download/{event_id}", status_code=302)

@app.post("/stripe/webhook")
async def stripe_webhook(request: Request):
    if not STRIPE_WEBHOOK_SECRET:
        return HTMLResponse("Webhook secret not configured.", status_code=500)

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=sig_header,
            secret=STRIPE_WEBHOOK_SECRET,
        )
    except Exception:
        logger.warning("Invalid Stripe webhook signature")
        return HTMLResponse("Invalid signature.", status_code=400)

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        session_id = session.get("id")
        payment_intent = session.get("payment_intent")
        event_id = None
        metadata = session.get("metadata") or {}
        if isinstance(metadata, dict):
            event_id = metadata.get("event_id")
        target = get_event_by_session_id(session_id)
        if not target and event_id:
            target = get_event_by_id(event_id)
        if target:
            update_event_payment(target["id"], True, payment_intent)

    return {"status": "ok"}

@app.get("/download/{event_id}")
def download(event_id: str):
    event = get_event_by_id(event_id)
    
    if not event:
        return HTMLResponse("Invalid reference ID", status_code=404)
    
    if not event.get("paid"):
        return HTMLResponse("Payment has not been processed.", status_code=402)

    pdf_path = REPORTS_DIR / f"integrity_reference_{event_id}.pdf"

    if not pdf_path.exists():
        # Generate the report using event data
        generate_audit_report(str(pdf_path), {
            "verified_at": event["timestamp"],
            "verdict": "PASS",
            "instance_id": f"AETERNA-{event_id[:8]}",
            "customer": event["declared_by"],
            "license_type": "Public",
            "scope": event["purpose"],
            "checked_events": 1,
            "deliverable_hash": event["hash"],
            "deliverable_hash_algorithm": "SHA3-512",
            "deliverable_purpose": event["purpose"],
            "deliverable_declared_by": event["declared_by"],
            "instance_fingerprint": event["hash"][:32],
            "report_hash": hashlib.sha3_512(event["hash"].encode()).hexdigest(),
            "report_signature": hashlib.sha3_512(
                (event["hash"] + "aeterna").encode()
            ).hexdigest()
        })

    return FileResponse(
        pdf_path,
        filename="AETERNA_Integrity_Reference_Certificate.pdf",
        media_type="application/pdf"
    )
