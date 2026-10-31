import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings

logger = logging.getLogger(__name__)

# Configure connect_args for SQLite
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False,
    future=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI database session dependency with guaranteed closure."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initializes tables in database."""
    # Import all models to register with Base
    import app.models  # noqa: F401
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized successfully.")
