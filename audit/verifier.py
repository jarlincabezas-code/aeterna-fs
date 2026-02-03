import sqlite3
import hashlib
import json
import hmac

class AeternaShield:
    """Verificador Independiente de Integridad Forense."""
    
    def __init__(self, db_path, secret_key):
        self.db_path = db_path
        self.secret_key = secret_key.encode() if isinstance(secret_key, str) else secret_key
        self.hash_algo = hashlib.sha3_512

    def verify_chain(self):
        print(f"\n[SHIELD] Iniciando auditoría de integridad en: {self.db_path}")
        print("-" * 60)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            records = cursor.execute("SELECT * FROM chain_of_custody ORDER BY id ASC").fetchall()

        if not records:
            print("[!] La base de datos está vacía.")
            return False

        expected_prev_hash = "GENESIS_BLOCK_AETERNA_PLATINUM"
        
        for i, row in enumerate(records):
            # 1. Verificar encadenamiento (Hash Linking)
            if row['previous_hash'] != expected_prev_hash:
                print(f"[FALLO] Ruptura de cadena en ID {row['id']}. El eslabón no encaja con el anterior.")
                return False

            # 2. Re-calcular Hash del Bloque (Determinismo Estricto)
            # Reconstruimos exactamente como lo hizo el Engine
            block_content = f"{row['session_id']}{row['timestamp']}{row['event_type']}{row['payload']}{row['previous_hash']}{row['forensic_meta']}"
            recalculated_hash = self.hash_algo(block_content.encode('utf-8')).hexdigest()

            if row['block_hash'] != recalculated_hash:
                print(f"[FALLO] Integridad violada en ID {row['id']}. El contenido no coincide con el Hash.")
                return False

            # 3. Verificar Firma Digital (No-Repudio)
            recalculated_sig = hmac.new(self.secret_key, recalculated_hash.encode('utf-8'), self.hash_algo).hexdigest()
            if row['signature'] != recalculated_sig:
                print(f"[FALLO] Firma inválida en ID {row['id']}. La llave de autenticación no coincide.")
                return False

            # Avanzar el eslabón
            expected_prev_hash = recalculated_hash
            
        print(f"[ÉXITO] {len(records)} registros verificados matemáticamente.")
        print("[ESTADO] CADENA DE CUSTODIA INTACTA Y ADMISIBLE.")
        return True

if __name__ == "__main__":
    # El perito judicial ingresa la llave de seguridad (proporcionada por el Enclave)
    import os
    KEY = os.environ.get('AETERNA_KEY', 'NIST_800_86_PLATINUM_2026_PRO_SECURE_TOKEN')
    
    verifier = AeternaShield("vault/aeterna_vault.db", KEY)
    verifier.verify_chain()