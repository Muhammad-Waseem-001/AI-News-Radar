import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import NullPool

from app.config import get_settings

settings = get_settings()

database_url = settings.database_url.strip()
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql+psycopg://", 1)
elif database_url.startswith("postgresql://") and "+psycopg" not in database_url:
    database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)

is_sqlite = database_url.startswith("sqlite")
connect_args = {"check_same_thread": False} if is_sqlite else {}

engine_kwargs = {
    "pool_pre_ping": True,
    "connect_args": connect_args,
}

# Vercel serverless functions should not keep long-lived pooled connections.
if os.getenv("VERCEL"):
    engine_kwargs["poolclass"] = NullPool

engine = create_engine(database_url, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
