# app.py
# AETERNA-FS — Payment + Certificate Generation
# Python 3.9 / FastAPI

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import RedirectResponse, FileResponse, HTMLResponse
from reports.pdf_generator import generate_audit_report
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import uuid
import hashlib
import json
import stripe
import os

load_dotenv()


# Amount in cents (900 = $9.00 USD)
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
PRICE_AMOUNT = 900 
# Local server URLs
PUBLIC_URL = "http://localhost:8000"

app = FastAPI(title="AETERNA-FS")

# -----------------------------
# File Paths
# -----------------------------
BASE_DIR = Path(__file__).parent
VAULT_DIR = BASE_DIR / "vault"
INGEST_DIR = VAULT_DIR / "ingest"
REPORTS_DIR = VAULT_DIR / "reports"
EVENTS_DB = VAULT_DIR / "events.json"

# Create necessary directories
INGEST_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

if not EVENTS_DB.exists():
    EVENTS_DB.write_text("[]", encoding="utf-8")

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

def load_events():
    return json.loads(EVENTS_DB.read_text(encoding="utf-8"))

def save_events(events):
    EVENTS_DB.write_text(json.dumps(events, indent=2), encoding="utf-8")

# -----------------------------
# VIEWS (English UI)
# -----------------------------

@app.get("/", response_class=HTMLResponse)
def landing():
    return """
    <html>
    <body style="font-family:Arial, sans-serif; max-width:600px; margin:40px auto; line-height:1.6; color:#333;">
        <h1>AETERNA-FS</h1>
        <p>Freeze the exact version of a file in dispute and generate a neutral integrity reference.</p>
        
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
                Fix File
            </button>
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
    dest = INGEST_DIR / f"{event_id}_{file.filename}"

    # Save the file physically
    with open(dest, "wb") as f:
        f.write(file.file.read())

    hash_val = compute_sha3_512(dest)

    events = load_events()
    events.append({
        "id": event_id,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "file": file.filename,
        "hash": hash_val,
        "declared_by": declared_by,
        "purpose": purpose,
        "paid": False
    })
    save_events(events)

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
                Download integrity certificate ($9 USD)
            </button>
        </form>

        <p style="font-size:0.9em; color:gray; margin-top:20px; text-align:center;">
        The certificate is generated only after successful payment.
        </p>
    </body>
    </html>
    """

@app.post("/pay/{event_id}")
def pay(event_id: str):
    # Create Stripe Checkout Session
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": "usd",
                "product_data": {
                    "name": f"AETERNA Integrity Certificate - ID: {event_id[:8]}",
                },
                "unit_amount": PRICE_AMOUNT,
            },
            "quantity": 1,
        }],
        mode="payment",
        success_url=f"{PUBLIC_URL}/paid/{event_id}",
        cancel_url=f"{PUBLIC_URL}/",
    )
    return RedirectResponse(session.url, status_code=303)

@app.get("/paid/{event_id}")
def paid(event_id: str):
    events = load_events()
    for e in events:
        if e["id"] == event_id:
            e["paid"] = True
    save_events(events)
    return RedirectResponse(f"/download/{event_id}", status_code=302)

@app.get("/download/{event_id}")
def download(event_id: str):
    events = load_events()
    event = next((e for e in events if e["id"] == event_id), None)
    
    if not event:
        return HTMLResponse("Invalid reference ID", status_code=404)
    
    if not event.get("paid"):
        return HTMLResponse("Payment has not been processed.", status_code=402)

    pdf_path = REPORTS_DIR / f"audit_{event_id}.pdf"

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
        filename="AETERNA_Integrity_Certificate.pdf",
        media_type="application/pdf"
    )