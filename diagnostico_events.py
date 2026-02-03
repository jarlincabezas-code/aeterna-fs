# diagnostico_events.py
# Verifica integridad de events.json y detecta problemas que causan 500 en /events

import json
from pathlib import Path

VAULT_DIR = Path(__file__).parent / "vault"
EVENTS_DB = VAULT_DIR / "events.json"

def main():
    print(f"Verificando {EVENTS_DB}...\n")

    if not EVENTS_DB.exists():
        print("❌ Archivo events.json NO existe.")
        return

    try:
        data = json.loads(EVENTS_DB.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"❌ JSON inválido: {e}")
        return

    if not isinstance(data, list):
        print(f"❌ El contenido de events.json NO es una lista: {type(data)}")
        return

    if not data:
        print("⚠️ events.json está vacío (lista vacía).")
        return

    print(f"✅ Se cargaron {len(data)} eventos.\n")

    problemas = False
    for i, e in enumerate(data, 1):
        print(f"Evento {i}: id={e.get('id','<sin id>')}, file={e.get('file','<sin file>')}")
        required_fields = ['id','file','type','hash','status','declared_by','purpose','timestamp']
        for field in required_fields:
            if field not in e:
                print(f"❌ Falta campo '{field}' en evento {e.get('id','<sin id>')}")
                problemas = True

    if not problemas:
        print("\n✅ Todos los eventos tienen los campos requeridos.")
    else:
        print("\n❌ Hay eventos con campos faltantes, lo que probablemente causa errores en /events.")

if __name__ == "__main__":
    main()
