import logging
import redis.asyncio as aioredis
from app.config import settings

logger = logging.getLogger(__name__)

class RedisManager:
    client: aioredis.Redis = None

redis_manager = RedisManager()

async def connect_to_redis():
    if not settings.REDIS_URL:
        logger.warning("REDIS_URL is not set. Redis operations will fail.")
        return
    
    try:
        logger.info(f"Connecting to Redis at {settings.REDIS_URL}...")
        redis_manager.client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        # Test connection
        await redis_manager.client.ping()
        logger.info("Successfully connected to Redis.")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        redis_manager.client = None
        raise e

async def close_redis_connection():
    if redis_manager.client:
        logger.info("Closing Redis connection...")
        await redis_manager.client.close()
        redis_manager.client = None
        logger.info("Redis connection closed.")

def get_redis():
    if not redis_manager.client:
        raise RuntimeError("Redis client is not initialized.")
    return redis_manager.client
