"""BaFin data acquisition helpers shared by the provider and HTTP server."""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Iterable, Optional, Sequence

import requests

LOGGER = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
CACHE_PATH = DATA_DIR / "bafin_cache.json"
FIRECRAWL_ENDPOINT = "https://api.firecrawl.dev/v1/scrape"

RSS_URL_ENV = "BAFIN_RSS_FEED_URLS"
FIRECRAWL_KEY_ENV = "FIRECRAWL_API_KEY"
CACHE_MAX_AGE_MINUTES_ENV = "MY_PROVIDER_CACHE_MAX_AGE_MINUTES"
DEFAULT_CACHE_MAX_AGE_MINUTES = 60
MAX_ITEMS_ENV = "MY_PROVIDER_MAX_ITEMS"
DEFAULT_MAX_ITEMS = 25

ISO_FORMAT = "%Y-%m-%dT%H:%M:%S%z"
PDF_HREF_PATTERN = re.compile(r'href=["\']([^"\']+\.pdf)["\']', re.IGNORECASE)


def _ensure_timezone(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def _now() -> datetime:
    return datetime.now(tz=UTC)


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", text.lower()).strip("-")
    return slug or "legal-act"


def _hash_link(link: str) -> str:
    digest = hashlib.sha1(link.encode("utf-8"), usedforsecurity=False).hexdigest()
    return digest[:16]


def _generate_identifier(title: str, link: str) -> str:
    return f"bafin-{_slugify(title)[:32]}-{_hash_link(link)}"


@dataclass(frozen=True)
class CachedLegalAct:
    """Representation persisted to disk for reuse by the provider and HTTP server."""

    identifier: str
    title: str
    summary: str
    source_url: str
    pdf_url: str
    publication_date: str  # ISO8601 with timezone
    document_type: str
    eurovoc_labels: Sequence[str]
    html_body: str

    @property
    def publication_datetime(self) -> datetime:
        return datetime.fromisoformat(self.publication_date)

    def to_dict(self) -> dict[str, object]:
        return {
            "identifier": self.identifier,
            "title": self.title,
            "summary": self.summary,
            "source_url": self.source_url,
            "pdf_url": self.pdf_url,
            "publication_date": self.publication_date,
            "document_type": self.document_type,
            "eurovoc_labels": list(self.eurovoc_labels),
            "html_body": self.html_body,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "CachedLegalAct":
        return cls(
            identifier=str(data["identifier"]),
            title=str(data["title"]),
            summary=str(data.get("summary", "")),
            source_url=str(data["source_url"]),
            pdf_url=str(data.get("pdf_url", "")),
            publication_date=str(data["publication_date"]),
            document_type=str(data.get("document_type", "notice")),
            eurovoc_labels=tuple(data.get("eurovoc_labels", [])),
            html_body=str(data["html_body"]),
        )


@dataclass(frozen=True)
class CachedDataset:
    fetched_at: datetime
    legal_acts: tuple[CachedLegalAct, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "fetched_at": self.fetched_at.strftime(ISO_FORMAT),
            "legal_acts": [item.to_dict() for item in self.legal_acts],
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "CachedDataset":
        fetched_at_str = str(data["fetched_at"])
        fetched_at = datetime.strptime(fetched_at_str, ISO_FORMAT).astimezone(UTC)
        acts_raw = data.get("legal_acts", [])
        acts = tuple(CachedLegalAct.from_dict(item) for item in acts_raw)
        return cls(fetched_at=fetched_at, legal_acts=acts)

    def is_stale(self, max_age: timedelta) -> bool:
        return self.fetched_at + max_age < _now()


def _parse_pub_date(raw: Optional[str]) -> Optional[datetime]:
    if not raw:
        return None
    try:
        return _ensure_timezone(parsedate_to_datetime(raw))
    except (TypeError, ValueError):
        LOGGER.warning("Failed to parse publication date %s", raw)
        return None


def _extract_pdf_url(html: str) -> str:
    match = PDF_HREF_PATTERN.search(html)
    if match:
        return match.group(1)
    return ""


def _resolve_feed_urls() -> list[str]:
    raw = os.environ.get(RSS_URL_ENV)
    if not raw:
        raise RuntimeError(
            f"Environment variable {RSS_URL_ENV} is required to fetch BaFin feeds."
        )
    return [entry.strip() for entry in raw.split(",") if entry.strip()]


def _resolve_max_items() -> int:
    raw = os.environ.get(MAX_ITEMS_ENV)
    if not raw:
        return DEFAULT_MAX_ITEMS
    try:
        value = int(raw)
    except ValueError as exc:
        raise RuntimeError(
            f"Invalid integer for {MAX_ITEMS_ENV}: {raw!r}"
        ) from exc
    return max(1, value)


def _resolve_cache_age() -> timedelta:
    raw = os.environ.get(CACHE_MAX_AGE_MINUTES_ENV)
    if not raw:
        return timedelta(minutes=DEFAULT_CACHE_MAX_AGE_MINUTES)
    try:
        value = int(raw)
    except ValueError as exc:
        raise RuntimeError(
            f"Invalid integer for {CACHE_MAX_AGE_MINUTES_ENV}: {raw!r}"
        ) from exc
    return timedelta(minutes=max(1, value))


def _fetch_text(url: str, timeout: int = 30) -> str:
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    response.encoding = response.encoding or "utf-8"
    return response.text


def _fetch_firecrawl_html(url: str, api_key: str, timeout: int = 60) -> str:
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {"url": url, "formats": ["html"]}
    response = requests.post(
        FIRECRAWL_ENDPOINT, headers=headers, json=payload, timeout=timeout
    )
    response.raise_for_status()
    data = response.json()
    html = ""

    # Firecrawl returns html either at top level or nested under data/html depending on plan.
    if isinstance(data, dict):
        if "html" in data:
            html = str(data["html"])
        elif "data" in data and isinstance(data["data"], dict):
            html = str(data["data"].get("html", ""))

    if not html:
        raise RuntimeError(f"Firecrawl response missing HTML for {url}")

    return html


def _render_article_html(title: str, summary: str, raw_html: str) -> str:
    """Wrap crawled HTML snippets into a normalised article body."""
    body_parts = [f"<h1>{title}</h1>"]
    if summary:
        body_parts.append(f"<p><strong>Summary:</strong> {summary}</p>")
    body_parts.append(raw_html)
    return "\n".join(body_parts)


def _fetch_feed_entries(feed_urls: Iterable[str]) -> list[dict[str, object]]:
    entries: list[dict[str, object]] = []
    for url in feed_urls:
        try:
            xml_text = _fetch_text(url)
        except Exception as exc:  # pragma: no cover - network errors
            LOGGER.error("Failed to download RSS feed %s: %s", url, exc)
            continue

        try:
            import xml.etree.ElementTree as ET

            root = ET.fromstring(xml_text)
        except ET.ParseError as exc:
            LOGGER.error("Failed to parse RSS XML from %s: %s", url, exc)
            continue

        channel = root.find("channel")
        items = channel.findall("item") if channel is not None else root.findall(".//item")

        for item in items:
            title = item.findtext("title") or ""
            link = item.findtext("link") or ""
            if not link:
                continue
            pub_date = _parse_pub_date(item.findtext("pubDate"))
            description = item.findtext("description") or ""
            entries.append(
                {
                    "title": title.strip(),
                    "link": link.strip(),
                    "pub_date": pub_date or _now(),
                    "summary": re.sub(r"<[^>]+>", "", description).strip(),
                }
            )
    # Deduplicate by link while preserving latest publish date ordering.
    deduped: dict[str, dict[str, object]] = {}
    for entry in sorted(entries, key=lambda item: item["pub_date"], reverse=True):
        deduped.setdefault(entry["link"], entry)
    return list(deduped.values())


def refresh_dataset() -> CachedDataset:
    """Fetch live data from BaFin and persist it to the on-disk cache."""
    api_key = os.environ.get(FIRECRAWL_KEY_ENV)
    if not api_key:
        raise RuntimeError(
            f"Environment variable {FIRECRAWL_KEY_ENV} is required to crawl BaFin content."
        )

    feed_urls = _resolve_feed_urls()
    max_items = _resolve_max_items()

    entries = _fetch_feed_entries(feed_urls)
    if not entries:
        raise RuntimeError("No entries discovered from BaFin RSS feeds.")

    acts: list[CachedLegalAct] = []
    for entry in entries[:max_items]:
        title = str(entry["title"])
        link = str(entry["link"])
        identifier = _generate_identifier(title, link)
        pub_date: datetime = entry["pub_date"]  # type: ignore[assignment]
        summary = str(entry["summary"])

        try:
            html = _fetch_firecrawl_html(link, api_key)
        except Exception as exc:  # pragma: no cover - network errors
            LOGGER.error("Failed to crawl %s: %s", link, exc)
            continue

        pdf_url = _extract_pdf_url(html)

        cleaned_html = _render_article_html(title, summary, html)
        act = CachedLegalAct(
            identifier=identifier,
            title=title,
            summary=summary,
            source_url=link,
            pdf_url=pdf_url,
            publication_date=_ensure_timezone(pub_date).isoformat(),
            document_type="notice",
            eurovoc_labels=("banking regulation", "bafin"),
            html_body=cleaned_html,
        )
        acts.append(act)

    if not acts:
        raise RuntimeError("No legal acts could be crawled from BaFin feeds.")

    dataset = CachedDataset(fetched_at=_now(), legal_acts=tuple(acts))
    save_dataset(dataset)
    return dataset


def load_dataset() -> Optional[CachedDataset]:
    if not CACHE_PATH.exists():
        return None
    try:
        data = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
        return CachedDataset.from_dict(data)
    except Exception as exc:  # pragma: no cover - corrupted cache
        LOGGER.error("Failed to load cached dataset: %s", exc)
        return None


def save_dataset(dataset: CachedDataset) -> None:
    CACHE_PATH.write_text(json.dumps(dataset.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")


def ensure_dataset(force_refresh: bool = False) -> CachedDataset:
    dataset = load_dataset()
    max_age = _resolve_cache_age()
    if force_refresh or dataset is None or dataset.is_stale(max_age):
        return refresh_dataset()
    return dataset


def build_expression_url(base_endpoint: str, identifier: str) -> str:
    base = base_endpoint.rstrip("/")
    return f"{base}/legal-acts/{identifier}"


def iter_cached_records(dataset: Optional[CachedDataset] = None) -> Iterable[CachedLegalAct]:
    target = dataset if dataset is not None else load_dataset()
    if not target:
        return ()
    return target.legal_acts
