from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Article(Base):
    __tablename__ = "articles"
    __table_args__ = (
        Index("ix_articles_source_published", "source", "published_at"),
        Index("ix_articles_sentiment_created", "sentiment_label", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    link: Mapped[str] = mapped_column(String(2000), nullable=False, unique=True, index=True)
    source: Mapped[str] = mapped_column(String(255), nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    sentiment_score: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    sentiment_label: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    raw_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class JobRun(Base):
    __tablename__ = "job_runs"
    __table_args__ = (
        UniqueConstraint("job_name", "run_key", name="uq_job_runs_job_name_run_key"),
        Index("ix_job_runs_job_name_run_key", "job_name", "run_key"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    job_name: Mapped[str] = mapped_column(String(64), nullable=False)
    run_key: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
