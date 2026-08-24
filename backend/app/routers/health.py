from fastapi import APIRouter
from app.db.mongodb import db
from app.db.redis_client import redis_manager

router = APIRouter()

@router.get("/health")
async def health_check():
    mongodb_status = "disconnected"
    redis_status = "disconnected"
    
    # Check MongoDB
    if db.client:
        try:
            await db.client.admin.command('ping')
            mongodb_status = "connected"
        except Exception:
            mongodb_status = "error"
            
    # Check Redis
    if redis_manager.client:
        try:
            await redis_manager.client.ping()
            redis_status = "connected"
        except Exception:
            redis_status = "error"
            
    overall_status = "healthy" if mongodb_status == "connected" and redis_status == "connected" else "unhealthy"
    
    return {
        "status": overall_status,
        "mongodb": mongodb_status,
        "redis": redis_status
    }
