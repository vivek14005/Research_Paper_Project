from qdrant_client import QdrantClient
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class QdrantDB:
    client: QdrantClient = None

    def connect_to_storage(self):
        try:
            if settings.QDRANT_API_KEY:
                self.client = QdrantClient(
                    url=settings.QDRANT_HOST,
                    api_key=settings.QDRANT_API_KEY,
                )
            else:
                self.client = QdrantClient(
                    host=settings.QDRANT_HOST,
                    port=settings.QDRANT_PORT,
                )
            logger.info(f"Connected to Qdrant at {settings.QDRANT_HOST}")
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {e}")
            # For development, we might want to continue even if Qdrant is down
            # or maybe fail fast. Let's log it for now.

    def close_storage_connection(self):
        if self.client:
            self.client.close()
            logger.info("Closed Qdrant connection")

qdrant_db = QdrantDB()

def get_qdrant_client():
    return qdrant_db.client
