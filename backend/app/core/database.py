import time
import logging
from typing import Generator, Dict, Any
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.core.config import settings

logger = logging.getLogger(__name__)

# SQLAlchemy 2.0 Base class
class Base(DeclarativeBase):
    pass


# Configure Engine with production-ready connection pooling
engine_kwargs: Dict[str, Any] = {
    "pool_pre_ping": True,
}

if not settings.sync_database_uri.startswith("sqlite"):
    engine_kwargs.update({
        "pool_size": settings.DB_POOL_SIZE,
        "max_overflow": settings.DB_MAX_OVERFLOW,
        "pool_timeout": settings.DB_POOL_TIMEOUT,
        "pool_recycle": settings.DB_POOL_RECYCLE,
        "connect_args": {
            "connect_timeout": 3,
        },
    })

engine = create_engine(settings.sync_database_uri, **engine_kwargs)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator:
    """Dependency generator that provides an active database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_health(timeout_seconds: float = 2.0) -> Dict[str, Any]:
    """
    Checks the connectivity and responsiveness of the configured database.
    Does not crash the server if PostgreSQL is not currently running.
    """
    start_time = time.time()
    try:
        # Create a short-lived connection with connection timeout
        with engine.connect() as conn:
            # Execute ping query
            result = conn.execute(text("SELECT 1"))
            val = result.scalar()
            latency_ms = round((time.time() - start_time) * 1000, 2)
            if val == 1:
                return {
                    "status": "connected",
                    "latency_ms": latency_ms,
                    "database_url": settings.POSTGRES_DB,
                    "driver": engine.dialect.name,
                }
            return {
                "status": "unexpected_result",
                "latency_ms": latency_ms,
                "detail": f"Expected 1, got {val}",
            }
    except Exception as exc:
        latency_ms = round((time.time() - start_time) * 1000, 2)
        logger.warning("Database health check failed: %s", exc)
        return {
            "status": "disconnected",
            "latency_ms": latency_ms,
            "error": str(exc),
            "target": f"{settings.POSTGRES_SERVER}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}",
        }
