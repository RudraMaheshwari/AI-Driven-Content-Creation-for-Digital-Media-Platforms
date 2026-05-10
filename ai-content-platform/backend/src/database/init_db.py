"""Create tables on startup (no Alembic for simple dev bootstrap)."""
from __future__ import annotations

from src.database.models import Base
from src.database.session import engine
from src.utils.logger import get_logger

logger = get_logger("database")


def init_database() -> None:
    logger.info("initializing database schema")
    Base.metadata.create_all(bind=engine)
