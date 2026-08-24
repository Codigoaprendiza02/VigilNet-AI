import logging
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings

logger = logging.getLogger(__name__)

class MongoDB:
    client: AsyncIOMotorClient = None

db = MongoDB()

async def connect_to_mongo():
    if not settings.MONGODB_URI:
        logger.warning("MONGODB_URI is not set. MongoDB operations will fail.")
        return
    
    try:
        logger.info("Connecting to MongoDB Atlas...")
        db.client = AsyncIOMotorClient(settings.MONGODB_URI)
        # Verify connection by triggering a simple admin command
        await db.client.admin.command('ping')
        logger.info("Successfully connected to MongoDB Atlas.")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB Atlas: {e}")
        db.client = None
        raise e

async def close_mongo_connection():
    if db.client:
        logger.info("Closing MongoDB connection...")
        db.client.close()
        db.client = None
        logger.info("MongoDB connection closed.")

def get_database():
    if not db.client:
        raise RuntimeError("MongoDB client is not initialized.")
    return db.client[settings.MONGODB_DB_NAME]
