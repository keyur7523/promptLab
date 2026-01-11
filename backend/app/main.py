"""Main FastAPI application."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import hashlib
import asyncio
import httpx

from app.config import get_settings
from app.middleware.logging import LoggingMiddleware
from app.api import chat, feedback, health, setup
from app.database import engine, Base, SessionLocal
from app.models import User, Experiment

settings = get_settings()

# Keep-alive task for Render free tier
keep_alive_task = None

async def keep_alive_ping():
    """Ping the Rust token counter service every 10 minutes to prevent sleep."""
    while True:
        await asyncio.sleep(600)  # 10 minutes
        if settings.token_counter_enabled and settings.token_counter_url:
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(f"{settings.token_counter_url}/health")
                    if response.status_code == 200:
                        logging.info(f"Keep-alive ping to token counter: OK")
                    else:
                        logging.warning(f"Keep-alive ping failed: {response.status_code}")
            except Exception as e:
                logging.warning(f"Keep-alive ping error: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan - startup and shutdown."""
    global keep_alive_task

    # Startup
    Base.metadata.create_all(bind=engine)
    logging.info("Database tables verified/created on startup")

    # Seed initial data if database is empty
    db = SessionLocal()
    try:
        existing_user = db.query(User).first()
        if not existing_user:
            logging.info("Empty database detected, seeding initial data...")
            test_api_key = "test-key-123"
            api_key_hash = hashlib.sha256(test_api_key.encode()).hexdigest()
            user = User(api_key_hash=api_key_hash, rate_limit=100)
            db.add(user)
            experiment = Experiment(
                key="prompt_experiment_jan2024",
                description="Test concise vs detailed prompts",
                variants={"control": 34, "concise": 33, "friendly": 33},
                active=True
            )
            db.add(experiment)
            db.commit()
            logging.info("Database seeded with default user and experiment")
    except Exception as e:
        logging.error(f"Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()

    # Start keep-alive task for Render free tier
    keep_alive_task = asyncio.create_task(keep_alive_ping())
    logging.info("Keep-alive task started for token counter service")

    yield  # App runs here

    # Shutdown
    if keep_alive_task:
        keep_alive_task.cancel()
        try:
            await keep_alive_task
        except asyncio.CancelledError:
            pass
    logging.info("Shutting down PromptLab")

# Create FastAPI app
app = FastAPI(
    title="PromptLab",
    description="AI experimentation platform with prompt versioning and A/B testing",
    version="0.1.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan
)

# CORS middleware - Allow frontend origins
allowed_origins = [
    "http://localhost:5173",  # Local development
    "http://localhost:3000",  # Alternative local port
    settings.frontend_url,     # Production frontend
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Trace-ID", "X-RateLimit-Limit", "X-RateLimit-Remaining"]
)

# Logging middleware
app.add_middleware(LoggingMiddleware)

# Include routers
app.include_router(health.router, tags=["health"])
app.include_router(chat.router, tags=["chat"])
app.include_router(feedback.router, tags=["feedback"])
app.include_router(setup.router, tags=["setup"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "PromptLab",
        "version": "0.1.0",
        "docs": "/docs" if settings.debug else "disabled",
        "endpoints": {
            "health": "/health",
            "chat": "POST /chat",
            "feedback": "POST /feedback"
        }
    }





# uvicorn app.main:app --reload