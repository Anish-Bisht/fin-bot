from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.db import init_db, init_qdrant
from app.routers import admin, chat


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup → yield → shutdown."""
    import time
    import logging
    logger = logging.getLogger(__name__)

    # 1. Validate config immediately — crash fast with a clear message
    try:
        settings.validate_keys()
        logger.info("✅ Configuration validated")
    except ValueError as e:
        logger.critical(f"❌ Invalid configuration: {e}")
        raise

    # 2. Initialize SQLite DB
    try:
        init_db()
        logger.info("✅ SQLite database initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize database: {e}")
        raise

    # 3. Initialize Qdrant with retries (it may take time to start in Docker)
    max_retries = 30
    retry_interval = 2
    for attempt in range(max_retries):
        try:
            init_qdrant()
            logger.info("✅ Qdrant vector database initialized")
            break
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(
                    f"⚠️  Qdrant attempt {attempt + 1}/{max_retries} failed: {e} — retrying in {retry_interval}s"
                )
                time.sleep(retry_interval)
            else:
                logger.error(f"❌ Qdrant unavailable after {max_retries} attempts: {e}")
                raise

    yield  # Application runs here
    # (shutdown hooks go below yield if needed)


app = FastAPI(title="FinBot API", version="1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://frontend:3000",   # Docker service-to-service
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])

@app.get("/health")
def health_check():
    return {"status": "ok"}