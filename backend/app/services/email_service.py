import smtplib
import logging
from datetime import datetime
from email.message import EmailMessage

from app.config import get_settings
from app.models import Article

settings = get_settings()
logger = logging.getLogger(__name__)


def _can_send_email() -> bool:
    return bool(settings.gmail_username and settings.gmail_app_password)


def send_email(subject: str, body: str, recipients: list[str]) -> tuple[bool, str | None]:
    clean_recipients = [email.strip() for email in recipients if email and email.strip()]
    if not clean_recipients:
        return False, "No recipient emails provided."
    if not _can_send_email():
        return False, "Gmail credentials are not configured."

    message = EmailMessage()
    message["From"] = settings.gmail_username
    message["To"] = ", ".join(clean_recipients)
    message["Subject"] = subject
    message.set_content(body)

    try:
        with smtplib.SMTP_SSL(
            host=settings.gmail_smtp_host,
            port=settings.gmail_smtp_port,
            timeout=20,
        ) as smtp:
            smtp.login(settings.gmail_username, settings.gmail_app_password)
            smtp.send_message(message)
        return True, None
    except Exception as exc:
        logger.exception("Email sending failed. subject=%s recipients=%s", subject, clean_recipients)
        return False, f"{type(exc).__name__}: {exc}"


def send_alert(article: Article) -> tuple[bool, str | None]:
    subject = f"[AI News Alert] Negative sentiment detected ({article.sentiment_score:.2f})"
    published = article.published_at.isoformat() if article.published_at else "Unknown"
    body = (
        "Potentially high-risk article detected.\n\n"
        f"Title: {article.title}\n"
        f"Source: {article.source}\n"
        f"Category: {article.category}\n"
        f"Sentiment: {article.sentiment_label} ({article.sentiment_score:.2f})\n"
        f"Published: {published}\n"
        f"Link: {article.link}\n\n"
        f"Summary:\n{article.summary}\n"
    )
    return send_email(subject=subject, body=body, recipients=settings.alert_recipients)


def send_daily_digest(articles: list[Article], recipients: list[str] | None = None) -> tuple[bool, str | None]:
    target_recipients = recipients if recipients is not None else settings.digest_recipients
    if not articles:
        return False, "No articles available for digest."

    today = datetime.utcnow().strftime("%Y-%m-%d")
    subject = f"[AI News Digest] {today} ({len(articles)} articles)"

    lines = [
        "AI News Intelligence & Sentiment Radar - Daily Digest",
        "",
        f"Date: {today}",
        f"Articles: {len(articles)}",
        "",
    ]
    for index, item in enumerate(articles, start=1):
        lines.extend(
            [
                f"{index}. {item.title}",
                f"   Source: {item.source}",
                f"   Category: {item.category}",
                f"   Sentiment: {item.sentiment_label} ({item.sentiment_score:.2f})",
                f"   Link: {item.link}",
                f"   Summary: {item.summary}",
                "",
            ]
        )

    body = "\n".join(lines)
    return send_email(subject=subject, body=body, recipients=target_recipients)


def send_test_email(recipients: list[str] | None = None) -> tuple[bool, str | None]:
    target_recipients = recipients if recipients is not None else settings.digest_recipients
    subject = "[AI News Radar] Test Email"
    body = (
        "This is a connectivity test email from AI News Intelligence & Sentiment Radar.\n\n"
        "If you received this message, Gmail SMTP settings are working."
    )
    return send_email(subject=subject, body=body, recipients=target_recipients)
