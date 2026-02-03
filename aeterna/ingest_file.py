# aeterna/ingest_file.py
# Funciones reutilizables para sellar evidencia en AETERNA-FS
# Compatible con FastAPI

import hashlib
import datetime
import json
from pathlib import Path
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet

BASE_DIR = Path(__file__).parent.parent
VAULT_DIR = BASE_DIR / "vault"
INGEST_DIR = VAULT_DIR / "ingest"
REPORTS_DIR = VAULT_DIR / "reports"
EVENTS_DB = VAULT_DIR / "events.json"

INGEST_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
if not EVENTS_DB.exists():
    EVENTS_DB.write_text("[]", encoding="utf-8")


def compute_sha3_512(file_path: Path) -> str:
    h = hashlib.sha3_512()
    with open(file_path, "rb") as f:
        while chunk := f.read(4096):
            h.update(chunk)
    return h.hexdigest()


def load_events() -> list:
    return json.loads(EVENTS_DB.read_text(encoding="utf-8"))


def save_events(events: list):
    EVENTS_DB.write_text(json.dumps(events, indent=2), encoding="utf-8")


def generate_pdf(event: dict) -> Path:
    pdf_file = REPORTS_DIR / f"audit_{event['id']}.pdf"
    doc = SimpleDocTemplate(str(pdf_file), pagesize=A4)
    styles = getSampleStyleSheet()
    story = [
        Paragraph("<b>AETERNA – Certificate of Integrity</b>", styles["Title"]),
        Spacer(1, 12),
        Paragraph(f"Archivo: {event['file']}", styles["Normal"]),
        Paragraph(f"Declarado por: {event['declared_by']}", styles["Normal"]),
        Paragraph(f"Propósito: {event['purpose']}", styles["Normal"]),
        Paragraph(f"Timestamp UTC: {event['timestamp']}", styles["Normal"]),
        Paragraph(f"SHA3-512: {event['hash']}", styles["Normal"])
    ]
    doc.build(story)
    return pdf_file


def seal_file(file_path: Path, declared_by: str, purpose: str) -> dict:
    """Sellar archivo: hash, registrar evento y generar PDF"""
    file_path = Path(file_path)
    hash_val = compute_sha3_512(file_path)
    events = load_events()
    event_id = str(len(events) + 1)
    event = {
        "id": event_id,
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "type": "FILE_INGEST",
        "file": file_path.name,
        "hash": hash_val,
        "status": "OK",
        "declared_by": declared_by,
        "purpose": purpose
    }
    events.append(event)
    save_events(events)
    generate_pdf(event)
    return event
