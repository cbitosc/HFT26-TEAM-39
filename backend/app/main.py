import logging
import sys
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import init_db
from app.routes.incidents import router as incidents_router
from app.routes.evidence import router as evidence_router
from app.routes.timeline import router as timeline_router
from app.routes.video import router as video_router
from app.routes.analysis import router as analysis_router

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger("trace_ai")

# Initialize FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "TRACE AI is an AI-powered road accident investigation and kinematic reconstruction prototype. "
        "It provides deterministic telemetry validation, multi-vehicle event sequencing, "
        "computer vision motion tracking, objective contradiction analysis, and server-side Featherless AI integration."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Configure Cross-Origin Resource Sharing (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if "*" in settings.CORS_ORIGINS else settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    """Initializes SQLite database tables and verifies filesystem storage."""
    logger.info("Initializing TRACE AI database and storage...")
    init_db()
    settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    logger.info("TRACE AI Backend successfully started.")


# Exception handler for unhandled exceptions to return consistent JSON
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled server exception at %s %s: %s", request.method, request.url.path, str(exc), exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "INTERNAL_SERVER_ERROR",
            "message": "An internal server error occurred during processing.",
            "detail": str(exc) if settings.DEBUG else None,
            "path": request.url.path,
        },
    )


# Mount routers
app.include_router(incidents_router)
app.include_router(evidence_router)
app.include_router(timeline_router)
app.include_router(video_router)
app.include_router(analysis_router)


@app.get("/", tags=["Root"])
def root_status():
    """Root entry point providing API metadata and links to documentation."""
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "OPERATIONAL",
        "documentation": "/docs",
        "health_check": "/api/health",
        "ai_status": "/api/ai/status",
    }
