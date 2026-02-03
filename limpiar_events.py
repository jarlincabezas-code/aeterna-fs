# limpiar_events.py
import json
from pathlib import Path

VAULT_DIR = Path(__file__).parent / "vault"
EVENTS_DB = VAULT_DIR / "events.json"

def main():
    if not EVENTS_DB.exists():
        print("❌ events.json no existe.")
        return

    with open(EVENTS_DB, "r", encoding="utf-8") as f:
        try:
            events = json.load(f)
        except json.JSONDecodeError as e:
            print(f"❌ JSON inválido: {e}")
            return

    updated = False
    for e in events:
        if "type" not in e:
            e["type"] = "FILE_INGEST"
            updated = True
        if "status" not in e:
            e["status"] = "OK"
            updated = True

    if updated:
        with open(EVENTS_DB, "w", encoding="utf-8") as f:
            json.dump(events, f, indent=2)
        print("✅ Campos faltantes rellenados.")
    else:
        print("⚠️ No se detectaron campos faltantes.")

if __name__ == "__main__":
    main()
