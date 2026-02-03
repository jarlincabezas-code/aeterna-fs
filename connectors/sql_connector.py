from sqlalchemy import create_engine, text
from connectors.base_connector import BaseConnector

class SQLConnector(BaseConnector):
    def connect(self):
        try:
            # db_url ejemplo: 'oracle+cx_oracle://user:pass@host:port/service'
            self.engine = create_engine(self.config['db_url'])
            self.connection = self.engine.connect()
            self.is_connected = True
            return True
        except Exception as e:
            print(f"Error de conexión SQL: {e}")
            return False

    def extract_data(self, query):
        if not self.is_connected:
            raise ConnectionError("Base de datos no conectada.")
        
        result = self.connection.execute(text(query))
        return [dict(row._mapping) for row in result]