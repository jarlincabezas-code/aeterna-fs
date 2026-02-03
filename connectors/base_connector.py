from abc import ABC, abstractmethod
import datetime

class BaseConnector(ABC):
    def __init__(self, config):
        self.config = config
        self.connection = None
        self.is_connected = False

    @abstractmethod
    def connect(self):
        pass

    @abstractmethod
    def extract_data(self, query_params):
        pass

    def get_context(self):
        """Metadatos de la conexión para la cadena de custodia."""
        return {
            "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
            "connector": self.__class__.__name__,
            "target": self.config.get("host", "unknown")
        }