"""
FastAPI Application — AI SQL Agent.

This is the main application module that:
    - Creates the FastAPI app with metadata
    - Configures CORS middleware
    - Sets up logging
    - Initializes the database on startup
    - Registers all API routes
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db, get_row_counts
from app.routes.query import router as query_router

# ─── Logging Configuration ───────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)-8s │ %(name)s │ %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


# ─── App Lifespan (startup / shutdown) ───────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup."""
    logger.info("🚀 Starting AI SQL Agent...")
    init_db()
    counts = get_row_counts()
    logger.info("📊 Database loaded — %s", counts)
    yield
    logger.info("👋 Shutting down AI SQL Agent.")


# ─── App Factory ─────────────────────────────────────────────────
app = FastAPI(
    title="AI SQL Agent",
    description=(
        "An AI-powered Natural Language to SQL Agent that converts "
        "plain English questions into SQL queries, executes them against "
        "a company database, and returns clean, structured results."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ─── CORS Middleware ─────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Register Routes ────────────────────────────────────────────
app.include_router(query_router, tags=["Query"])


# ─── Root & Health Endpoints ────────────────────────────────────
@app.get("/")
async def root():
    """API information and available endpoints."""
    return {
        "name": "AI SQL Agent",
        "version": "1.0.0",
        "description": "Natural Language to SQL Agent powered by Groq Llama 3",
        "endpoints": {
            "POST /query": "Convert a natural language question to SQL and get results",
            "GET /health": "Health check",
            "GET /docs": "Interactive API documentation (Swagger UI)",
            "GET /redoc": "Alternative API documentation (ReDoc)",
        },
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        counts = get_row_counts()
        return {
            "status": "healthy",
            "database": "connected",
            "tables": counts,
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
        }
