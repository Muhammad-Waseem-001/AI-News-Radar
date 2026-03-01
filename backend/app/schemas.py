from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ArticleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    link: str
    source: str
    published_at: datetime | None
    summary: str
    category: str
    sentiment_score: float
    sentiment_label: str
    created_at: datetime
    updated_at: datetime


class StatsRead(BaseModel):
    total_articles: int
    sources: int
    avg_sentiment: float
    sentiment_breakdown: dict[str, int]
    categories: dict[str, int]

