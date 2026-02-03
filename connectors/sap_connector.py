import logging
from connectors.base_connector import BaseConnector

class SAPConnector(BaseConnector):
    def connect(self):
        try:
            from pyrfc import Connection
            self.connection = Connection(**self.config)
            self.is_connected = True
            return True
        except Exception as e:
            logging.error(f"Error de conexión SAP: {e}")
            return False

    def extract_data(self, table_name, fields=None, options=None, rowcount=1000):
        """
        Llamada RFC_READ_TABLE: El estándar para auditoría externa.
        """
        if not self.is_connected:
            raise ConnectionError("No hay conexión activa con SAP.")

        params = {
            'QUERY_TABLE': table_name,
            'DELIMITER': '|',
            'FIELDS': [{'FIELDNAME': f} for f in fields] if fields else [],
            'OPTIONS': [{'TEXT': options}] if options else [],
            'ROWCOUNT': rowcount
        }
        
        result = self.connection.call('RFC_READ_TABLE', **params)
        return self._parse_sap_result(result)

    def _parse_sap_result(self, result):
        # Lógica de parsing de strings delimitados a diccionarios
        data = []
        fields = [f['FIELDNAME'] for f in result['FIELDS']]
        for line in result['DATA']:
            values = line['WA'].split('|')
            data.append(dict(zip(fields, values)))
        return data