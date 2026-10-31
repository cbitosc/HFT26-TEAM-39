from app.routes.incidents import router as incidents_router
from app.routes.evidence import router as evidence_router
from app.routes.timeline import router as timeline_router
from app.routes.video import router as video_router
from app.routes.analysis import router as analysis_router

__all__ = [
    "incidents_router",
    "evidence_router",
    "timeline_router",
    "video_router",
    "analysis_router",
]
