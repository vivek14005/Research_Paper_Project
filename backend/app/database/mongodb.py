from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class MongoDB:
    client: AsyncIOMotorClient = None
    db = None

    async def connect_to_storage(self):
        self.client = AsyncIOMotorClient(settings.MONGODB_URL)
        self.db = self.client[settings.DATABASE_NAME]
        logger.info(f"Connected to MongoDB at {settings.MONGODB_URL}")

    async def close_storage_connection(self):
        if self.client:
            self.client.close()
            logger.info("Closed MongoDB connection")

db = MongoDB()

async def get_database():
    return db.db
