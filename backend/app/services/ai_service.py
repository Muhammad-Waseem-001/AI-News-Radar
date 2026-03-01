import json
import math
import re
import warnings
from dataclasses import dataclass

with warnings.catch_warnings():
    warnings.simplefilter("ignore", FutureWarning)
    import google.generativeai as genai

from app.config import get_settings

settings = get_settings()

CATEGORIES = [
    "AI Research",
    "Product Launch",
    "Policy & Regulation",
    "Funding & M&A",
    "Security",
    "Ethics",
    "Infrastructure",
    "General",
]


@dataclass(slots=True)
class EnrichedArticle:
    summary: str
    category: str
    sentiment_score: float
    sentiment_label: str


def _clamp_sentiment(value: float) -> float:
    return max(-1.0, min(1.0, value))


def _label_from_score(value: float) -> str:
    if value >= 0.2:
        return "positive"
    if value <= -0.2:
        return "negative"
    return "neutral"


def _guess_category(text: str) -> str:
    lowered = text.lower()
    if any(token in lowered for token in ("regulation", "law", "compliance", "government")):
        return "Policy & Regulation"
    if any(token in lowered for token in ("funding", "raised", "acquisition", "investor", "series a")):
        return "Funding & M&A"
    if any(token in lowered for token in ("vulnerability", "attack", "breach", "cyber")):
        return "Security"
    if any(token in lowered for token in ("ethics", "bias", "fairness", "safety")):
        return "Ethics"
    if any(token in lowered for token in ("launch", "release", "announced", "feature")):
        return "Product Launch"
    if any(token in lowered for token in ("gpu", "infrastructure", "datacenter", "cloud")):
        return "Infrastructure"
    if any(token in lowered for token in ("study", "paper", "benchmark", "research")):
        return "AI Research"
    return "General"


def _simple_sentiment_score(text: str) -> float:
    positive_words = {
        "growth",
        "improve",
        "success",
        "positive",
        "benefit",
        "innovation",
        "breakthrough",
        "strong",
        "gain",
        "win",
    }
    negative_words = {
        "risk",
        "failure",
        "negative",
        "harm",
        "lawsuit",
        "breach",
        "decline",
        "loss",
        "concern",
        "ban",
    }

    tokens = [t.strip(".,:;!?()[]{}\"'").lower() for t in text.split()]
    pos = sum(1 for token in tokens if token in positive_words)
    neg = sum(1 for token in tokens if token in negative_words)
    if pos == 0 and neg == 0:
        return 0.0

    score = (pos - neg) / max(1, pos + neg)
    return _clamp_sentiment(score)


def _heuristic_enrichment(title: str, body: str) -> EnrichedArticle:
    text = f"{title}\n{body}".strip()
    trimmed = " ".join(text.split())
    summary = trimmed[:350] + ("..." if len(trimmed) > 350 else "")
    category = _guess_category(text)
    score = _simple_sentiment_score(text)
    label = _label_from_score(score)
    return EnrichedArticle(summary=summary, category=category, sentiment_score=score, sentiment_label=label)


def _extract_json_payload(text: str) -> str:
    candidate = (text or "").strip()
    if not candidate:
        return "{}"

    fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", candidate, flags=re.DOTALL)
    if fenced:
        return fenced.group(1).strip()
    return candidate


def _call_gemini(title: str, body: str) -> dict:
    genai.configure(api_key=settings.gemini_api_key)
    model = genai.GenerativeModel(
        model_name=settings.gemini_model,
        generation_config={"temperature": 0.1},
    )

    prompt = (
        "You are a precise news intelligence analyst.\n"
        "Return strict JSON only with keys: summary, category, sentiment_score.\n"
        "Rules:\n"
        "- summary: <= 80 words.\n"
        f"- category: one of {CATEGORIES}.\n"
        "- sentiment_score: float between -1 and 1.\n"
        "- Do not include markdown or code fences.\n"
        "- Focus on the article's overall impact/tone.\n\n"
        f"Title:\n{title}\n\nBody:\n{body}"
    )

    response = model.generate_content(prompt)
    content = getattr(response, "text", "") or ""
    parsed = json.loads(_extract_json_payload(content))
    if not isinstance(parsed, dict):
        raise ValueError("Gemini response is not a JSON object.")
    return parsed


def enrich_article(title: str, body: str) -> EnrichedArticle:
    if not settings.gemini_api_key:
        return _heuristic_enrichment(title, body)

    try:
        parsed = _call_gemini(title, body)
        summary = str(parsed.get("summary", "")).strip()
        if not summary:
            summary = _heuristic_enrichment(title, body).summary

        category = str(parsed.get("category", "General")).strip()
        if category not in CATEGORIES:
            category = "General"

        score = float(parsed.get("sentiment_score", 0.0))
        if math.isnan(score) or math.isinf(score):
            score = 0.0
        score = _clamp_sentiment(score)

        return EnrichedArticle(
            summary=summary,
            category=category,
            sentiment_score=score,
            sentiment_label=_label_from_score(score),
        )
    except Exception:
        return _heuristic_enrichment(title, body)
