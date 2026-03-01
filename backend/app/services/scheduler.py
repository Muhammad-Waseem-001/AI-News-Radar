import logging
from collections.abc import Callable
from zoneinfo import ZoneInfo

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session

from app.config import get_settings
from app.services.pipeline import ingest_once, send_digest_for_last_24_hours

settings = get_settings()
logger = logging.getLogger(__name__)

scheduler: BackgroundScheduler | None = None


def _run_with_session(session_factory: Callable[[], Session], task: Callable[[Session], dict], job_name: str):
    db = session_factory()
    try:
        result = task(db)
        logger.info("%s finished with result: %s", job_name, result)
    except Exception:
        logger.exception("%s failed", job_name)
    finally:
        db.close()


def start_scheduler(session_factory: Callable[[], Session]) -> None:
    global scheduler
    if scheduler and scheduler.running:
        return

    try:
        tz = ZoneInfo(settings.timezone)
    except Exception:
        tz = ZoneInfo("UTC")

    scheduler = BackgroundScheduler(timezone=tz)
    scheduler.add_job(
        lambda: _run_with_session(session_factory, ingest_once, "Ingestion Job"),
        trigger="interval",
        minutes=settings.ingest_interval_minutes,
        id="ingestion_job",
        replace_existing=True,
        coalesce=True,
        max_instances=1,
    )
    scheduler.add_job(
        lambda: _run_with_session(session_factory, send_digest_for_last_24_hours, "Digest Job"),
        trigger="cron",
        hour=settings.digest_hour_24,
        minute=0,
        id="digest_job",
        replace_existing=True,
        coalesce=True,
        max_instances=1,
    )
    scheduler.start()
    logger.info("Scheduler started: ingest every %s minutes, digest at %02d:00",
                settings.ingest_interval_minutes, settings.digest_hour_24)


def stop_scheduler() -> None:
    global scheduler
    if scheduler and scheduler.running:
        scheduler.shutdown(wait=False)
    scheduler = None
    logger.info("Scheduler stopped")
