import math

class OutlierDetector:
    @staticmethod
    def calculate_z_scores(data_list):
        if len(data_list) < 2:
            return [0] * len(data_list)
        
        mean = sum(data_list) / len(data_list)
        variance = sum((x - mean) ** 2 for x in data_list) / len(data_list)
        std_dev = math.sqrt(variance) if variance > 0 else 1
        
        return [(x - mean) / std_dev for x in data_list]

    @staticmethod
    def flag_high_risk(z_score, threshold=3.0):
        """Un Z-Score > 3 indica una anomalía estadística severa (99.7% de confianza)."""
        return abs(z_score) > threshold