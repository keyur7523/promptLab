"""Main FastAPI application."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import hashlib

from app.config import get_settings
from app.middleware.logging import LoggingMiddleware
from app.api import chat, feedback, health, setup
from app.database import engine, Base, SessionLocal
from app.models import User, Experiment

settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title="AI Chat Platform",
    description="Production-grade AI chat backend with experimentation framework",
    version="0.1.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None
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


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    # Create database tables if they don't exist
    # This ensures tables exist even if the database was reset
    Base.metadata.create_all(bind=engine)
    logging.info("Database tables verified/created on startup")

    # Seed initial data if database is empty
    db = SessionLocal()
    try:
        existing_user = db.query(User).first()
        if not existing_user:
            logging.info("Empty database detected, seeding initial data...")

            # Create default user
            test_api_key = "test-key-123"
            api_key_hash = hashlib.sha256(test_api_key.encode()).hexdigest()
            user = User(api_key_hash=api_key_hash, rate_limit=100)
            db.add(user)

            # Create default experiment
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


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logging.info("Shutting down AI Chat Platform")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "AI Chat Platform",
        "version": "0.1.0",
        "docs": "/docs" if settings.debug else "disabled",
        "endpoints": {
            "health": "/health",
            "chat": "POST /chat",
            "feedback": "POST /feedback"
        }
    }
