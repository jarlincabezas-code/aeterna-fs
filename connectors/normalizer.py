class ForensicNormalizer:
    @staticmethod
    def normalize(data, mapping):
        """
        data: lista de diccionarios crudos.
        mapping: dict que traduce { 'campo_erp': 'campo_aeterna' }
        """
        normalized = []
        for entry in data:
            new_entry = {}
            for erp_key, aeterna_key in mapping.items():
                val = entry.get(erp_key)
                # Limpieza de espacios y normalización de tipos
                if isinstance(val, str):
                    val = val.strip()
                new_entry[aeterna_key] = val
            normalized.append(new_entry)
        return normalized