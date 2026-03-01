import hashlib
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import Article, JobRun
from app.services.ai_service import enrich_article
from app.services.email_service import send_alert, send_daily_digest
from app.services.rss_service import fetch_articles

settings = get_settings()


def _content_hash(title: str, link: str) -> str:
    raw = f"{title}|{link}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _now_local() -> datetime:
    try:
        tz = ZoneInfo(settings.timezone)
    except Exception:
        tz = timezone.utc
    return datetime.now(timezone.utc).astimezone(tz)


def ingest_once(db: Session) -> dict:
    raw_articles = fetch_articles(settings.rss_feeds, max_per_feed=settings.max_articles_per_feed)
    if not raw_articles:
        return {
            "status": "ok",
            "fetched": 0,
            "new_articles": 0,
            "alerts_sent": 0,
        }

    links = [item.link for item in raw_articles]
    existing_links = set(db.scalars(select(Article.link).where(Article.link.in_(links))).all())

    fetched = len(raw_articles)
    new_articles = 0
    alerts_sent = 0
    alert_candidates: list[Article] = []

    for item in raw_articles:
        if item.link in existing_links:
            continue

        enrichment = enrich_article(item.title, item.raw_content)
        article = Article(
            title=item.title,
            link=item.link,
            source=item.source,
            published_at=item.published_at,
            summary=enrichment.summary,
            category=enrichment.category,
            sentiment_score=enrichment.sentiment_score,
            sentiment_label=enrichment.sentiment_label,
            raw_content=item.raw_content,
            content_hash=_content_hash(item.title, item.link),
        )
        try:
            # Use a savepoint so duplicate link conflicts are skipped without failing the whole job.
            with db.begin_nested():
                db.add(article)
                db.flush()
            existing_links.add(item.link)
            new_articles += 1

            if enrichment.sentiment_score <= settings.alert_sentiment_threshold:
                alert_candidates.append(article)
        except IntegrityError:
            continue

    db.commit()

    if settings.alert_recipients:
        for candidate in alert_candidates:
            if send_alert(candidate):
                alerts_sent += 1

    return {
        "status": "ok",
        "fetched": fetched,
        "new_articles": new_articles,
        "alerts_sent": alerts_sent,
    }


def send_digest_for_last_24_hours(db: Session) -> dict:
    if not settings.digest_recipients:
        return {"status": "skipped", "reason": "No digest recipients configured.", "articles": 0}

    window_start = datetime.now(timezone.utc) - timedelta(hours=24)
    recent_articles = list(
        db.scalars(select(Article).where(Article.created_at >= window_start).order_by(Article.created_at.desc())).all()
    )

    if not recent_articles:
        return {"status": "skipped", "reason": "No new articles in the last 24 hours.", "articles": 0}

    sent = send_daily_digest(recent_articles, recipients=settings.digest_recipients)
    return {
        "status": "ok" if sent else "failed",
        "articles": len(recent_articles),
        "sent": sent,
    }


def send_digest_once_per_local_day(db: Session, job_name: str = "daily_digest") -> dict:
    now_local = _now_local()
    run_key = now_local.date().isoformat()

    already_sent = db.scalar(
        select(JobRun.id).where(JobRun.job_name == job_name, JobRun.run_key == run_key)
    )
    if already_sent:
        return {
            "status": "skipped",
            "reason": "Digest already sent for this local day.",
            "run_key": run_key,
            "local_time": now_local.isoformat(),
        }

    result = send_digest_for_last_24_hours(db)
    if result.get("sent"):
        db.add(JobRun(job_name=job_name, run_key=run_key))
        try:
            db.commit()
        except IntegrityError:
            db.rollback()

    result["run_key"] = run_key
    result["local_time"] = now_local.isoformat()
    return result
