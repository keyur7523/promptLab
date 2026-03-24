"""Main FastAPI application."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import asyncio
import httpx

from app.config import get_settings
from app.middleware.logging import LoggingMiddleware
from app.api import chat, feedback, health, setup, analytics, experiments, conversations, prompts, api_keys, export
from app.services.token_counter import close_token_counter
from app.database import engine, Base

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
                        logging.info("Keep-alive ping to token counter: OK")
                    else:
                        logging.warning("Keep-alive ping failed: %d", response.status_code)
            except Exception as e:
                logging.warning("Keep-alive ping error: %s", e)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan - startup and shutdown."""
    global keep_alive_task

    # Startup — ensure all tables exist (safe: checkfirst=True is default)
    Base.metadata.create_all(bind=engine)
    logging.info("PromptLab starting up")

    # Start keep-alive task for Render free tier
    keep_alive_task = asyncio.create_task(keep_alive_ping())
    logging.info("Keep-alive task started for token counter service")

    yield  # App runs here

    # Shutdown
    await close_token_counter()
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

# CORS middleware - Origins driven by configuration
allowed_origins = [settings.frontend_url]
if settings.debug:
    allowed_origins += ["http://localhost:5173", "http://localhost:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Trace-ID", "X-RateLimit-Limit", "X-RateLimit-Remaining"]
)

# Security headers middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        if not settings.debug:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

app.add_middleware(SecurityHeadersMiddleware)


# Request body size limit middleware (1MB max)
MAX_BODY_SIZE = 1_048_576  # 1 MB

class BodySizeLimitMiddleware(BaseHTTPMiddleware):
    """Reject requests with bodies larger than MAX_BODY_SIZE."""

    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > MAX_BODY_SIZE:
            return Response(
                content='{"detail":"Request body too large"}',
                status_code=413,
                media_type="application/json",
            )
        return await call_next(request)

app.add_middleware(BodySizeLimitMiddleware)

# Logging middleware
app.add_middleware(LoggingMiddleware)

# Include routers
app.include_router(health.router, tags=["health"])
app.include_router(chat.router, tags=["chat"])
app.include_router(feedback.router, tags=["feedback"])
app.include_router(setup.router, tags=["setup"])
app.include_router(analytics.router)
app.include_router(experiments.router)
app.include_router(conversations.router)
app.include_router(prompts.router)
app.include_router(api_keys.router)
app.include_router(export.router)


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