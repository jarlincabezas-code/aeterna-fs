from collections import defaultdict
import datetime

class PatternMatcher:
    @staticmethod
    def detect_split_transactions(records, time_window_hours=24, amount_threshold=1000):
        """
        Busca múltiples transacciones al mismo proveedor por el mismo usuario 
        en un periodo corto de tiempo.
        """
        # Agrupar por (Usuario, Proveedor)
        buckets = defaultdict(list)
        for r in records:
            key = (r['user_id'], r['vendor_id'])
            buckets[key].append(r)
            
        anomalies = []
        for key, transactions in buckets.items():
            if len(transactions) < 2: continue
            
            # Ordenar por tiempo (asumiendo formato ISO)
            transactions.sort(key=lambda x: x['date'])
            
            for i in range(len(transactions) - 1):
                t1 = datetime.datetime.fromisoformat(transactions[i]['date'])
                t2 = datetime.datetime.fromisoformat(transactions[i+1]['date'])
                
                diff = (t2 - t1).total_seconds() / 3600
                if diff <= time_window_hours:
                    anomalies.append({
                        "type": "SPLIT_TRANSACTION",
                        "user": key[0],
                        "vendor": key[1],
                        "records": [transactions[i]['tx_id'], transactions[i+1]['tx_id']]
                    })
        return anomalies