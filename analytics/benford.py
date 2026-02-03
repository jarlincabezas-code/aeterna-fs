import math
from collections import Counter

class BenfordAnalyst:
    """Valida si un conjunto de datos financieros ha sido manipulado humanamente."""
    
    @staticmethod
    def calculate_distribution(data_list):
        # Extraer primer dígito significativo
        first_digits = []
        for val in data_list:
            try:
                s_val = str(abs(float(val))).replace('0', '').replace('.', '')
                if s_val:
                    first_digits.append(int(s_val[0]))
            except (ValueError, TypeError):
                continue

        if not first_digits:
            return None

        total = len(first_digits)
        counts = Counter(first_digits)
        
        # Frecuencias observadas vs esperadas
        report = {}
        for d in range(1, 10):
            observed = counts.get(d, 0) / total
            expected = math.log10(1 + 1/d)
            report[d] = {
                "observed": round(observed, 4),
                "expected": round(expected, 4),
                "deviation": round(abs(observed - expected), 4)
            }
        return report

    @staticmethod
    def get_anomaly_score(report):
        """Calcula una desviación global. Si supera 0.05, hay sospecha de fraude."""
        if not report: return 0
        avg_dev = sum(d['deviation'] for d in report.values()) / 9
        return min(avg_dev * 10, 1.0) # Escala de 0 a 1