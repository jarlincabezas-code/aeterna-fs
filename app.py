from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.responses import RedirectResponse, FileResponse, HTMLResponse
from pathlib import Path
from datetime import datetime
from typing import Optional
import uuid
import hashlib
import sqlite3
import stripe
import os
import json
import logging
from dotenv import load_dotenv

# -------------------------------------------------
# CONFIG
# -------------------------------------------------
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("aeterna")

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
PUBLIC_URL = os.getenv("PUBLIC_URL")  # OBLIGATORIO en Railway

PRICE_AMOUNT = 900  # $9 USD
MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", str(10 * 1024 * 1024)))

app = FastAPI(title="AETERNA-FS")

# -------------------------------------------------
# STORAGE
# -------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
VAULT_DIR = BASE_DIR / "vault"
INGEST_DIR = VAULT_DIR / "ingest"
REPORTS_DIR = VAULT_DIR / "reports"
DB_PATH = VAULT_DIR / "events.db"

INGEST_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# -------------------------------------------------
# DATABASE
# -------------------------------------------------
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_conn() as conn:
        conn.execute("""
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
        """)
        conn.commit()

def insert_event(event: dict):
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO events VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            event["id"],
            event["timestamp"],
            event["file"],
            event["hash"],
            event["declared_by"],
            event["purpose"],
            0,
            None,
            None
        ))
        conn.commit()

def get_event(event_id: str) -> Optional[dict]:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM events WHERE id = ?", (event_id,)
        ).fetchone()
        return dict(row) if row else None

def update_session(event_id: str, session_id: str):
    with get_conn() as conn:
        conn.execute(
            "UPDATE events SET session_id = ? WHERE id = ?",
            (session_id, event_id)
        )
        conn.commit()

def mark_paid(event_id: str, payment_intent: str):
    with get_conn() as conn:
        conn.execute("""
            UPDATE events
            SET paid = 1, payment_intent = ?
            WHERE id = ?
        """, (payment_intent, event_id))
        conn.commit()

# -------------------------------------------------
# UTILS
# -------------------------------------------------
def compute_sha3_512(path: Path) -> str:
    h = hashlib.sha3_512()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def save_upload_limited(src, dest: Path, max_bytes: int):
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

# -------------------------------------------------
# ROUTES
# -------------------------------------------------
@app.get("/", response_class=HTMLResponse)
def landing():
    return """
    <html>
    <body style="max-width:600px;margin:40px auto;font-family:Arial">
        <h1>AETERNA</h1>
        <form action="/preview" method="post" enctype="multipart/form-data">
            <input type="file" name="file" required><br><br>
            <input type="text" name="declared_by" placeholder="Declared by" required><br><br>
            <input type="text" name="purpose" placeholder="Purpose" required><br><br>
            <button>Generate integrity reference</button>
        </form>
    </body>
    </html>
    """

@app.post("/preview", response_class=HTMLResponse)
def preview(
    file: UploadFile = File(...),
    declared_by: str = Form(...),
    purpose: str = Form(...)
):
    event_id = str(uuid.uuid4())
    dest = INGEST_DIR / f"{event_id}_{Path(file.filename).name}"

    try:
        save_upload_limited(file.file, dest, MAX_UPLOAD_BYTES)
    except ValueError:
        return HTMLResponse("File too large", status_code=413)

    hash_val = compute_sha3_512(dest)

    insert_event({
        "id": event_id,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "file": file.filename,
        "hash": hash_val,
        "declared_by": declared_by,
        "purpose": purpose
    })

    return f"""
    <html><body>
        <h2>Integrity reference created</h2>
        <form action="/pay/{event_id}" method="post">
            <button>Pay $9 USD</button>
        </form>
    </body></html>
    """

@app.post("/pay/{event_id}")
def pay(event_id: str):
    event = get_event(event_id)
    if not event:
        return HTMLResponse("Invalid ID", status_code=404)

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": "usd",
                "product_data": {
                    "name": f"AETERNA Integrity Reference ({event_id[:8]})"
                },
                "unit_amount": PRICE_AMOUNT,
            },
            "quantity": 1,
        }],
        mode="payment",
        success_url=f"{PUBLIC_URL}/paid/{event_id}?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{PUBLIC_URL}/",
        metadata={"event_id": event_id},
    )

    update_session(event_id, session.id)
    return RedirectResponse(session.url, status_code=303)

@app.get("/paid/{event_id}")
def paid(event_id: str, session_id: Optional[str] = None):
    event = get_event(event_id)
    if not event or event["session_id"] != session_id:
        return HTMLResponse("Invalid session", status_code=400)

    session = stripe.checkout.Session.retrieve(session_id)
    if session.payment_status != "paid":
        return HTMLResponse("Payment not completed", status_code=402)

    mark_paid(event_id, session.payment_intent)
    return RedirectResponse(
    f"{PUBLIC_URL}/download/{event_id}",
    status_code=302
)


@app.get("/download/{event_id}")
def download(event_id: str):
    event = get_event(event_id)
    if not event or not event["paid"]:
        return HTMLResponse("Payment required", status_code=402)

    pdf_path = REPORTS_DIR / f"integrity_reference_{event_id}.pdf"

    if not pdf_path.exists():
        with open(pdf_path, "wb") as f:
            f.write(
                b"%PDF-1.4\n"
                b"1 0 obj<<>>endobj\n"
                b"trailer<<>>\n"
                b"%%EOF"
            )

    return FileResponse(
        path=pdf_path,
        filename="AETERNA_Integrity_Reference.pdf",
        media_type="application/pdf"
    )


# -------------------------------------------------
# INIT
# -------------------------------------------------
init_db()
