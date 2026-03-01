from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import urlparse

import feedparser
from dateutil import parser as date_parser


@dataclass(slots=True)
class RawArticle:
    title: str
    link: str
    source: str
    published_at: datetime | None
    raw_content: str


def _clean_text(value: str) -> str:
    return " ".join((value or "").split())


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = date_parser.parse(value)
        if not parsed.tzinfo:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except (ValueError, TypeError):
        return None


def fetch_articles(feed_urls: list[str], max_per_feed: int = 25) -> list[RawArticle]:
    articles: list[RawArticle] = []
    seen_links: set[str] = set()

    for feed_url in feed_urls:
        parsed = feedparser.parse(feed_url)
        feed_title = parsed.feed.get("title") if hasattr(parsed, "feed") else ""
        source = _clean_text(feed_title) or urlparse(feed_url).netloc or "Unknown Source"

        for entry in parsed.entries[:max_per_feed]:
            title = _clean_text(entry.get("title", "Untitled"))
            link = _clean_text(entry.get("link", ""))
            if not link or link in seen_links:
                continue

            published_at = _parse_datetime(entry.get("published") or entry.get("updated"))

            raw_content = _clean_text(entry.get("summary", "") or entry.get("description", ""))
            if not raw_content:
                entry_content = entry.get("content")
                if isinstance(entry_content, list) and entry_content:
                    raw_content = _clean_text(entry_content[0].get("value", ""))

            if not raw_content:
                raw_content = title

            seen_links.add(link)
            articles.append(
                RawArticle(
                    title=title,
                    link=link,
                    source=source,
                    published_at=published_at,
                    raw_content=raw_content,
                )
            )

    return articles

