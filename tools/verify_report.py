import json
import sys
import hashlib
import hmac
import os
from typing import Dict

from core.crypto import HASH_ALGO, SECRET_KEY

# ---- CONFIG ----
REPORT_CANONICAL_FIELDS = [
    "verdict",
    "verified_at",
    "instance_id",
    "instance_fingerprint",
    "customer",
    "license_type",
    "scope",
    "checked_events",
    "scope_status",
]

def load_report_payload_from_pdf(pdf_path: str) -> Dict:
    """
    Implementación mínima:
    En v1 asumimos que el PDF incluye un JSON embebido o
    que el verificador recibe también un .json exportado.
    """
    json_path = pdf_path.replace(".pdf", ".json")
    if not os.path.exists(json_path):
        raise FileNotFoundError("Missing companion JSON for verification")

    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)

def canonicalize_report(data: Dict) -> str:
    canonical = {k: data[k] for k in REPORT_CANONICAL_FIELDS}
    return json.dumps(canonical, sort_keys=True, separators=(",", ":"))

def compute_hmac(data_hash: str) -> str:
    key = SECRET_KEY.encode() if isinstance(SECRET_KEY, str) else SECRET_KEY
    return hmac.new(key, data_hash.encode(), HASH_ALGO).hexdigest()

def main():
    if len(sys.argv) != 2:
        print("Usage: python -m tools.verify_report <report.pdf>")
        sys.exit(1)

    pdf_path = sys.argv[1]

    data = load_report_payload_from_pdf(pdf_path)

    canonical_json = canonicalize_report(data)
    computed_hash = hashlib.sha3_512(canonical_json.encode()).hexdigest()
    computed_hmac = compute_hmac(computed_hash)

    ok_hash = computed_hash == data.get("report_hash")
    ok_hmac = computed_hmac == data.get("report_signature")

    print("AETERNA VERIFY")
    print(f"✓ Report hash matches content: {ok_hash}")
    print(f"✓ HMAC authentication VALID: {ok_hmac}")

    if ok_hash and ok_hmac:
        print("RESULT: VALID")
        sys.exit(0)
    else:
        print("RESULT: INVALID")
        sys.exit(2)

if __name__ == "__main__":
    main()
