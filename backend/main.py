import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db.mongodb import connect_to_mongo, close_mongo_connection
from app.db.redis_client import connect_to_redis, close_redis_connection
from app.routers import health, score

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("vigilnet")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions
    logger.info("Initializing services...")
    try:
        await connect_to_mongo()
    except Exception as e:
        logger.error(f"MongoDB initialization error during startup: {e}")
        
    try:
        await connect_to_redis()
    except Exception as e:
        logger.error(f"Redis initialization error during startup: {e}")
        
    yield
    
    # Shutdown actions
    logger.info("Shutting down services...")
    await close_mongo_connection()
    await close_redis_connection()

app = FastAPI(
    title="VigilNet AI Backend",
    description="Closed-Loop Red-Team / Blue-Team AI System for Payment Fraud Defense",
    version="0.1.0",
    lifespan=lifespan
)

# CORS configuration
origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
if settings.FRONTEND_URL:
    origins.append(settings.FRONTEND_URL)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(health.router)
app.include_router(score.router)

@app.get("/")
async def root():
    return {
        "message": "Welcome to VigilNet AI API",
        "version": "0.1.0",
        "docs_url": "/docs"
    }
