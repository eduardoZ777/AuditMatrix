import os
from urllib.parse import urlparse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.config import settings
from app.models import Base

# Ensure directory for database exists if it's SQLite
if settings.DATABASE_URL.startswith("sqlite:///"):
    # Strip sqlite:/// to get the file path
    db_file_path = settings.DATABASE_URL[9:]
    db_dir = os.path.dirname(db_file_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

# Create engine with safety configurations
# pool_pre_ping=True helps detect disconnected sessions (especially useful for real DBs like SQL Server)
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    echo=False
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db() -> None:
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)

def get_db() -> Session:
    """Provide db session with automatic closing context."""
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()
