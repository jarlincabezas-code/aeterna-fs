import uuid
from core.engine import AeternaEngine
from connectors.sql_connector import SQLConnector
from connectors.normalizer import ForensicNormalizer
from analytics.engine import AnalyticsEngine
from i18n.manager import I18nManager
from reports.pdf_generator import ForensicReport

def run_aeterna_audit():
    # Identidad Única de la Auditoría
    SID = f"AUDIT-{uuid.uuid4().hex[:8].upper()}"
    i18n = I18nManager("es")
    engine = AeternaEngine(SID) # Solución definitiva al TypeError

    print(f"\n[AETERNA-FS] SESIÓN INICIADA: {SID}")

    # Flujo de Datos
    conn = SQLConnector({'db_url': 'sqlite:///empresa_auditada.db'})
    if not conn.connect(): return

    raw = conn.extract_data("SELECT id, monto as amount, fecha as date, usuario as user_id, proveedor as vendor_id FROM transacciones")
    clean = ForensicNormalizer.normalize(raw, {'id': 'tx_id', 'amount': 'amount', 'date': 'date', 'user_id': 'user_id', 'vendor_id': 'vendor_id'})
    
    # Análisis
    results = AnalyticsEngine(clean).run_full_audit()

    # Persistencia con el contrato 'detailed_findings'
    print("Sellando registros en la Bóveda...")
    for record in results['detailed_findings']: # Solución definitiva al KeyError
        engine.record_event("FORENSIC_ENTRY", record, meta=conn.get_context())

    # Reporte
    print("Generando Informe de Peritaje...")
    with engine.vault as vault:
        data = vault.fetch_all()
        ForensicReport(i18n).generate(data, "REPORTE_AETERNA_PLATINUM.pdf")

    print(f"\n[V] AUDITORÍA FINALIZADA CON ÉXITO. SID: {SID}")

if __name__ == "__main__":
    run_aeterna_audit()