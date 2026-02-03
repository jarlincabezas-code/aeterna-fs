import datetime
import json
import platform
import uuid
import hashlib

from core.crypto import generate_hash, sign_data
from core.vault_manager import VaultManager
from reports.pdf_generator import generate_audit_report


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


class AeternaEngine:
    def __init__(self, session_id: str):
        self.vault = VaultManager()
        self.session_id = session_id

        # Hardware fingerprint
        hw_fingerprint = f"{platform.node()}{uuid.getnode()}"
        self.hw_id = hashlib.sha3_512(
            hw_fingerprint.encode("utf-8")
        ).hexdigest()

        # Instance fingerprint (derived, stable)
        self.instance_fingerprint = hashlib.sha3_512(
            f"{self.session_id}{self.hw_id}".encode("utf-8")
        ).hexdigest()[:12]

    def record_event(self, event_type: str, payload: dict, meta: dict = None):
        """
        Records an event into the cryptographically chained audit vault.
        """
        # ✅ CORRECCIÓN (Python 3.9 compatible)
        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()

        payload_str = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":")
        )

        previous_hash = self.vault.get_last_hash()

        current_hash = generate_hash(
            f"{self.session_id}{timestamp}{payload_str}{previous_hash}"
        )

        signature = sign_data(current_hash)

        metadata = meta.copy() if meta else {}
        metadata.update({
            "hw_id": self.hw_id,
            "session_id": self.session_id,
            "instance_fingerprint": self.instance_fingerprint
        })

        metadata_str = json.dumps(metadata, sort_keys=True)

        self.vault.persist((
            self.session_id,
            timestamp,
            event_type,
            payload_str,
            previous_hash,
            current_hash,
            signature,
            metadata_str
        ))

    def finalize_session(self, license_info: dict, scope_status: str) -> str:
        """
        Finalizes the audit session and generates the official PDF report.
        """
        events = self.vault.get_events_by_session(self.session_id)
        total_events = len(events)

        verdict = "VALID" if total_events > 0 else "NO DATA"

        # ✅ CORRECCIÓN (Python 3.9 compatible)
        verification_time = datetime.datetime.now(datetime.timezone.utc).isoformat()

        # ---- Report logical payload ----
        report_data = {
            "verdict": verdict,
            "verified_at": verification_time,
            "instance_id": self.session_id,
            "instance_fingerprint": self.instance_fingerprint,
            "customer": license_info["customer"],
            "license_type": license_info["type"],
            "scope": license_info["scope"],
            "checked_events": total_events,
            "scope_status": scope_status,
        }

        # ---- Canonical hash (STRICT CONTRACT) ----
        canonical = {k: report_data[k] for k in REPORT_CANONICAL_FIELDS}

        report_hash = hashlib.sha3_512(
            json.dumps(
                canonical,
                sort_keys=True,
                separators=(",", ":")
            ).encode("utf-8")
        ).hexdigest()

        report_signature = sign_data(report_hash)

        report_data["report_hash"] = report_hash
        report_data["report_signature"] = report_signature

        # ---- Output paths ----
        safe_time = verification_time.replace(":", "-")
        output_path = (
            f"vault/reports/"
            f"audit_{self.session_id}_{safe_time}.pdf"
        )

        # ---- Persist verification payload (v1 contract) ----
        json_path = output_path.replace(".pdf", ".json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, sort_keys=True)

        # ---- Generate PDF ----
        generate_audit_report(output_path, report_data)

        return output_path
