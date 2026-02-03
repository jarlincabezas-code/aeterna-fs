from core.engine import AeternaEngine

engine = AeternaEngine(session_id="TEST-SESSION-001")

engine.record_event(
    event_type="DELIVERABLE_SEAL",
    payload={
 
        "deliverable_hash": "0B78C005B98TUHASHCOMPLETOAQUI",
        "hash_algorithm": "SHA256",
        "description": "Freelance deliverable – demo file",
    }
)


license_info = {
    "customer": "Demo Company",
    "type": "PLATINUM",
    "scope": "Financial Audit"
}

pdf_path = engine.finalize_session(
    license_info=license_info,
    scope_status="OK"
)

print(pdf_path)
