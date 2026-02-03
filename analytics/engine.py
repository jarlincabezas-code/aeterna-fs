from analytics.benford import BenfordAnalyst
from analytics.outliers import OutlierDetector
from analytics.patterns import PatternMatcher

class AnalyticsEngine:
    def __init__(self, data):
        self.data = data # Datos inmutables de entrada

    def run_full_audit(self):
        amounts = [float(r['amount']) for r in self.data]
        
        # Procesamiento estadístico
        benford_report = BenfordAnalyst.calculate_distribution(amounts)
        benford_score = BenfordAnalyst.get_anomaly_score(benford_report)
        z_scores = OutlierDetector.calculate_z_scores(amounts)
        splits = PatternMatcher.detect_split_transactions(self.data)
        
        # Construcción del set de Hallazgos (Findings)
        findings = []
        for i, record in enumerate(self.data):
            # Clonamos para proteger la evidencia original
            f = record.copy()
            f['z_score'] = round(z_scores[i], 2)
            f['is_outlier'] = OutlierDetector.flag_high_risk(z_scores[i])
            # Índice de Riesgo AETERNA (ARI)
            f['global_risk_index'] = (benford_score * 0.4) + (abs(z_scores[i]) / 10 * 0.6)
            findings.append(f)
            
        return {
            "summary": {
                "benford_score": benford_score,
                "outliers_count": sum(1 for x in findings if x['is_outlier'])
            },
            "detailed_findings": findings, # ESTA CLAVE ES EL CONTRATO DEFINITIVO
            "patterns": splits
        }
    