from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db import init_db, init_qdrant
from app.routers import admin, chat

app = FastAPI(title="FinBot API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://localhost:3001", 
        "http://127.0.0.1:3000", 
        "http://127.0.0.1:3001"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    import time
    import logging

    logger = logging.getLogger(__name__)

    # Initialize SQLite DB
    try:
        init_db()
        logger.info("✅ SQLite database initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize database: {e}")
        raise

    # Initialize Qdrant with retries (it may take time to start)
    max_retries = 15
    retry_interval = 2

    for attempt in range(max_retries):
        try:
            init_qdrant()
            logger.info("✅ Qdrant vector database initialized")
            return
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"⚠️  Qdrant initialization attempt {attempt + 1}/{max_retries} failed: {e}")
                time.sleep(retry_interval)
            else:
                logger.error(f"❌ Failed to initialize Qdrant after {max_retries} attempts: {e}")
                raise

app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])

@app.get("/health")
def health_check():
    return {"status": "ok"}