import hashlib
import datetime

class GlobalWitness:
    """Implementa la validación de tiempo externo para evitar manipulación de reloj local."""
    
    @staticmethod
    def get_external_timestamp(block_hash: str):
        """
        Simula una llamada a una Autoridad de Sellado de Tiempo (RFC 3161).
        En un peritaje real, esto devuelve un token firmado por una entidad certificadora.
        """
        # Simulamos la latencia de red y respuesta de autoridad (DigiCert/GlobalSign)
        tsa_id = "TSA_SERVER_01_NETHERLANDS"
        external_time = datetime.datetime.now(datetime.UTC).isoformat()
        
        # El testigo firma el hash que nosotros le enviamos
        witness_sig = hashlib.sha3_512SS(f"{block_hash}{external_time}{tsa_id}".encode()).hexdigest()
        
        return {
            "tsa_id": tsa_id,
            "verified_utc": external_time,
            "tsa_signature": witness_sig.upper()
        }