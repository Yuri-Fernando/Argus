"""Crawl4AI wrapper — local-dev ingestion of live web content into the RAG pipeline.

Built per ADR-011, as the local-first counterpart of `rag/parsing/`'s Snowflake `AI_PARSE_DOCUMENT`
ingestion. Solves one named problem (ARCHITECTURE.md §1): turning a live web page into clean,
LLM-ready Markdown without hand-writing a headless-browser scraper per source. This module never
talks to Snowflake — see `rag/local_stack/README.md` for how this stage maps onto the cloud path.

Used by `agents/knowledge_ingestion/agent.py`, which decides per-source whether to call this
wrapper, `document_parser.py` (Docling), or read a static file from `data/documents/` directly.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class CrawlResult:
    """One crawled page, normalized to the shape the rest of the RAG pipeline expects.

    Mirrors the chunk-ready shape `rag/parsing/` produces from `AI_PARSE_DOCUMENT`, so
    `vector_store.py` doesn't need to special-case where a document came from.
    """

    url: str
    markdown: str
    title: str | None
    fetched_at: datetime
    success: bool
    metadata: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


class Crawl4AICrawler:
    """Thin wrapper around Crawl4AI's `AsyncWebCrawler`.

    Kept intentionally small: this class owns exactly one responsibility (fetch a URL, return
    clean Markdown + metadata) and delegates everything else — chunking, embedding, indexing — to
    `document_parser.py` / `vector_store.py`, matching the "every tool solves one named problem"
    principle in ARCHITECTURE.md §1.
    """

    def __init__(self, *, max_pages_per_domain: int = 20, timeout_seconds: int = 30) -> None:
        """
        Args:
            max_pages_per_domain: safety bound so a misconfigured crawl can't fan out unbounded —
                this project only ever crawls a handful of policy-style pages, never a full site.
            timeout_seconds: per-page fetch timeout passed through to Crawl4AI's crawler config.
        """
        self.max_pages_per_domain = max_pages_per_domain
        self.timeout_seconds = timeout_seconds

    async def crawl_url(self, url: str) -> CrawlResult:
        """Fetch a single URL and return it as clean Markdown.

        TODO(Sprint 12 extension): replace the stub below with a real call:

            from crawl4ai import AsyncWebCrawler

            async with AsyncWebCrawler() as crawler:
                result = await crawler.arun(url=url, page_timeout=self.timeout_seconds * 1000)
                return CrawlResult(
                    url=url,
                    markdown=result.markdown,
                    title=result.metadata.get("title"),
                    fetched_at=datetime.now(timezone.utc),
                    success=result.success,
                    metadata={"status_code": result.status_code},
                )

        This stub keeps the final contract stable so `agents/knowledge_ingestion/agent.py` and
        `vector_store.py` can be built and tested against it today, matching the pattern already
        used by `mcp/tools/customer.py`'s stubs.
        """
        return CrawlResult(
            url=url,
            markdown="",
            title=None,
            fetched_at=datetime.now(timezone.utc),
            success=False,
            error="Crawl4AI client not wired yet — see TODO in crawler.py",
        )

    async def crawl_many(self, urls: list[str]) -> list[CrawlResult]:
        """Crawl multiple URLs, bounded by `max_pages_per_domain`.

        Args:
            urls: candidate URLs to fetch, e.g. a documented public policy page a bank/e-commerce
                site publishes — used here to demonstrate ingesting content this platform's own
                synthetic documents (`data/documents/`) don't cover, per add2.txt's "web scraping
                to feed knowledge pipelines" requirement.

        Returns:
            One `CrawlResult` per URL, in the same order, truncated to `max_pages_per_domain`.
        """
        bounded = urls[: self.max_pages_per_domain]
        return [await self.crawl_url(url) for url in bounded]
