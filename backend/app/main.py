import os
import logging

from fastapi import Depends, FastAPI, HTTPException, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import Base, SessionLocal, engine, get_db
from app.models import Article
from app.schemas import ArticleRead, StatsRead
from app.services.pipeline import ingest_once, send_digest_for_last_24_hours, send_digest_once_per_local_day
from app.services.scheduler import start_scheduler, stop_scheduler

settings = get_settings()
is_vercel = bool(os.getenv("VERCEL"))
logger = logging.getLogger(__name__)
startup_db_error: str | None = None

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    global startup_db_error
    startup_db_error = None

    if settings.auto_create_tables:
        try:
            Base.metadata.create_all(bind=engine)
        except Exception as exc:
            startup_db_error = f"{type(exc).__name__}: {exc}"
            logger.exception("Database initialization failed during startup.")

    if settings.enable_local_scheduler and not is_vercel:
        start_scheduler(SessionLocal)


@app.on_event("shutdown")
def on_shutdown():
    if settings.enable_local_scheduler and not is_vercel:
        stop_scheduler()


@app.get("/")
def root():
    return {"message": settings.app_name, "api_prefix": settings.api_prefix}


@app.get("/health")
def health():
    if startup_db_error:
        return {
            "status": "degraded",
            "serverless": is_vercel,
            "database": "error",
            "message": "Database initialization failed. Check DATABASE_URL and backend logs.",
            "detail": startup_db_error,
        }
    return {"status": "ok", "serverless": is_vercel}


def _verify_cron_secret(request: Request) -> None:
    if not settings.cron_secret:
        return
    auth_header = request.headers.get("authorization", "")
    expected = f"Bearer {settings.cron_secret}"
    if auth_header != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid cron authorization token.",
        )


def _ensure_db_ready() -> None:
    if startup_db_error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not ready. Check DATABASE_URL and backend logs.",
        )


@app.post(f"{settings.api_prefix}/jobs/ingest")
def run_ingestion(db: Session = Depends(get_db)):
    _ensure_db_ready()
    return ingest_once(db)


@app.post(f"{settings.api_prefix}/jobs/digest")
def run_digest(db: Session = Depends(get_db)):
    _ensure_db_ready()
    return send_digest_for_last_24_hours(db)


@app.get(f"{settings.api_prefix}/cron/ingest")
def run_ingestion_cron(request: Request, db: Session = Depends(get_db)):
    _verify_cron_secret(request)
    _ensure_db_ready()
    return ingest_once(db)


@app.get(f"{settings.api_prefix}/cron/digest")
def run_digest_cron(request: Request, db: Session = Depends(get_db)):
    _verify_cron_secret(request)
    _ensure_db_ready()
    return send_digest_once_per_local_day(db)


@app.get(f"{settings.api_prefix}/articles", response_model=list[ArticleRead])
def list_articles(
    limit: int = Query(default=50, ge=1, le=250),
    sentiment: str | None = Query(default=None),
    category: str | None = Query(default=None),
    source: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    _ensure_db_ready()
    stmt = select(Article)
    if sentiment:
        stmt = stmt.where(Article.sentiment_label == sentiment.strip().lower())
    if category:
        stmt = stmt.where(Article.category == category.strip())
    if source:
        stmt = stmt.where(Article.source == source.strip())

    stmt = stmt.order_by(Article.published_at.desc(), Article.created_at.desc()).limit(limit)
    return list(db.scalars(stmt).all())


@app.get(f"{settings.api_prefix}/articles/{{article_id}}", response_model=ArticleRead)
def get_article(article_id: int, db: Session = Depends(get_db)):
    _ensure_db_ready()
    article = db.get(Article, article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article


@app.get(f"{settings.api_prefix}/stats", response_model=StatsRead)
def get_stats(db: Session = Depends(get_db)):
    _ensure_db_ready()
    total_articles = db.scalar(select(func.count()).select_from(Article)) or 0
    sources = db.scalar(select(func.count(func.distinct(Article.source)))) or 0
    avg_sentiment = db.scalar(select(func.avg(Article.sentiment_score))) or 0.0

    sentiment_rows = db.execute(
        select(Article.sentiment_label, func.count())
        .group_by(Article.sentiment_label)
        .order_by(Article.sentiment_label)
    ).all()
    sentiment_breakdown = {label: count for label, count in sentiment_rows}
    for key in ("positive", "neutral", "negative"):
        sentiment_breakdown.setdefault(key, 0)

    category_rows = db.execute(
        select(Article.category, func.count())
        .group_by(Article.category)
        .order_by(func.count().desc())
    ).all()
    categories = {category: count for category, count in category_rows}

    return StatsRead(
        total_articles=total_articles,
        sources=sources,
        avg_sentiment=round(float(avg_sentiment), 3),
        sentiment_breakdown=sentiment_breakdown,
        categories=categories,
    )
