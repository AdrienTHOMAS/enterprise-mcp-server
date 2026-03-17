"""Enterprise content indexer for Jira, Confluence, and GitHub.

Indexes enterprise content into the vector store for semantic search.
Supports incremental indexing (only new/updated documents since last run)
and background periodic re-indexing.
"""

from __future__ import annotations

import asyncio
import logging
import re
import time
from typing import Any

from .embeddings import EmbeddingService
from .vector_store import VectorStore

logger = logging.getLogger(__name__)


def _extract_plain_text(description: Any) -> str:
    """Extract plain text from Jira's Atlassian Document Format (ADF)."""
    if isinstance(description, str):
        return description
    if not isinstance(description, dict):
        return ""
    parts: list[str] = []
    for block in description.get("content", []):
        for inline in block.get("content", []):
            if inline.get("type") == "text":
                parts.append(inline.get("text", ""))
    return " ".join(parts)


def _strip_html(html: str) -> str:
    """Strip HTML tags to extract plain text from Confluence storage format."""
    return re.sub(r"<[^>]+>", " ", html).strip()


class EnterpriseIndexer:
    """Indexes Jira issues, Confluence pages, and GitHub READMEs.

    Args:
        embedding_service: Service for generating text embeddings.
        vector_store: Store for persisting document vectors.
        jira_connector: Optional JiraConnector instance.
        confluence_connector: Optional ConfluenceConnector instance.
        github_connector: Optional GitHubConnector instance.
    """

    def __init__(
        self,
        embedding_service: EmbeddingService,
        vector_store: VectorStore,
        jira_connector: Any = None,
        confluence_connector: Any = None,
        github_connector: Any = None,
    ) -> None:
        self._embeddings = embedding_service
        self._store = vector_store
        self._jira = jira_connector
        self._confluence = confluence_connector
        self._github = github_connector
        self._last_indexed: dict[str, float] = {}
        self._background_task: asyncio.Task[None] | None = None
        self._running = False

    # -- public API -------------------------------------------------------- #

    async def index_all(self) -> dict[str, Any]:
        """Run a full indexing pass across all configured sources.

        Returns:
            Summary with counts per source and total indexed.
        """
        stats: dict[str, int] = {}

        if self._jira:
            count = await self._index_jira()
            stats["jira"] = count

        if self._confluence:
            count = await self._index_confluence()
            stats["confluence"] = count

        if self._github:
            count = await self._index_github()
            stats["github"] = count

        await self._store.save()
        total = sum(stats.values())
        logger.info("indexing_complete", stats=stats, total=total)
        return {"indexed": stats, "total": total, "store_size": self._store.count}

    def start_background_indexing(self, interval_seconds: int = 600) -> None:
        """Start periodic background indexing.

        Args:
            interval_seconds: Time between indexing runs (default 10 minutes).
        """
        if self._running:
            return
        self._running = True
        self._background_task = asyncio.create_task(
            self._background_loop(interval_seconds)
        )
        logger.info("background_indexing_started", interval=interval_seconds)

    def stop_background_indexing(self) -> None:
        """Stop the background indexing task."""
        self._running = False
        if self._background_task and not self._background_task.done():
            self._background_task.cancel()
        logger.info("background_indexing_stopped")

    def get_stats(self) -> dict[str, Any]:
        """Return indexing statistics."""
        return {
            **self._store.stats(),
            "last_indexed": {
                source: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ts))
                for source, ts in self._last_indexed.items()
            },
            "background_running": self._running,
        }

    # -- background loop --------------------------------------------------- #

    async def _background_loop(self, interval: int) -> None:
        while self._running:
            try:
                await asyncio.sleep(interval)
                if self._running:
                    await self.index_all()
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error("background_indexing_error", error=str(exc))

    # -- Jira indexing ----------------------------------------------------- #

    async def _index_jira(self) -> int:
        """Index Jira issues updated since last run."""
        count = 0
        try:
            last = self._last_indexed.get("jira", 0)
            jql = 'updated >= "-30d" ORDER BY updated DESC'
            if last > 0:
                # Only fetch issues updated since last indexing
                ts = time.strftime("%Y-%m-%d %H:%M", time.gmtime(last))
                jql = f'updated >= "{ts}" ORDER BY updated DESC'

            result = await self._jira.search_issues(jql, max_results=100)
            issues = result.get("issues", [])

            texts: list[str] = []
            ids: list[str] = []
            metadatas: list[dict[str, Any]] = []

            for issue in issues:
                fields = issue.get("fields", {})
                summary = fields.get("summary", "")
                description = _extract_plain_text(fields.get("description", ""))
                text = f"{summary}\n{description}".strip()
                if not text:
                    continue

                issue_key = issue.get("key", "")
                texts.append(text)
                ids.append(f"jira:{issue_key}")
                metadatas.append({
                    "source": "jira",
                    "title": summary,
                    "issue_key": issue_key,
                    "status": fields.get("status", {}).get("name", ""),
                    "priority": fields.get("priority", {}).get("name", ""),
                    "issue_type": fields.get("issuetype", {}).get("name", ""),
                    "url": f"{self._jira.base_url}/browse/{issue_key}",
                })

            if texts:
                embeddings = await self._embeddings.embed_batch(texts)
                for doc_id, text, embedding, metadata in zip(
                    ids, texts, embeddings, metadatas
                ):
                    await self._store.add_document(doc_id, text, embedding, metadata)
                count = len(texts)

            self._last_indexed["jira"] = time.time()
            logger.info("jira_indexed", count=count)
        except Exception as exc:
            logger.error("jira_indexing_failed", error=str(exc))
        return count

    # -- Confluence indexing ------------------------------------------------ #

    async def _index_confluence(self) -> int:
        """Index Confluence pages."""
        count = 0
        try:
            result = await self._confluence.search(
                'type = "page" ORDER BY lastmodified DESC', max_results=50
            )
            pages = result.get("results", [])

            texts: list[str] = []
            ids: list[str] = []
            metadatas: list[dict[str, Any]] = []

            for page in pages:
                title = page.get("title", "")
                excerpt = page.get("excerpt", "")
                body_raw = ""
                if "body" in page:
                    storage = page["body"].get("storage", {})
                    body_raw = _strip_html(storage.get("value", ""))

                text = f"{title}\n{excerpt}\n{body_raw}".strip()
                if not text:
                    continue

                page_id = str(page.get("id", ""))
                web_link = page.get("_links", {}).get("webui", "")
                url = f"{self._confluence.base_url}/wiki{web_link}" if web_link else ""

                texts.append(text)
                ids.append(f"confluence:{page_id}")
                metadatas.append({
                    "source": "confluence",
                    "title": title,
                    "page_id": page_id,
                    "url": url,
                })

            if texts:
                embeddings = await self._embeddings.embed_batch(texts)
                for doc_id, text, embedding, metadata in zip(
                    ids, texts, embeddings, metadatas
                ):
                    await self._store.add_document(doc_id, text, embedding, metadata)
                count = len(texts)

            self._last_indexed["confluence"] = time.time()
            logger.info("confluence_indexed", count=count)
        except Exception as exc:
            logger.error("confluence_indexing_failed", error=str(exc))
        return count

    # -- GitHub indexing --------------------------------------------------- #

    async def _index_github(self) -> int:
        """Index GitHub repository READMEs."""
        count = 0
        try:
            owner = self._github.default_owner
            if not owner:
                logger.warning("github_indexing_skipped", reason="no default_owner configured")
                return 0

            # List repos for the org/user
            client = await self._github._get_client()
            response = await client.get(
                f"/orgs/{owner}/repos",
                params={"per_page": 30, "sort": "updated", "direction": "desc"},
            )

            if not response.is_success:
                # Try user repos endpoint
                response = await client.get(
                    f"/users/{owner}/repos",
                    params={"per_page": 30, "sort": "updated", "direction": "desc"},
                )

            if not response.is_success:
                return 0

            repos = response.json()
            texts: list[str] = []
            ids: list[str] = []
            metadatas: list[dict[str, Any]] = []

            for repo in repos:
                repo_name = repo.get("name", "")
                description = repo.get("description", "") or ""
                try:
                    file_data = await self._github.get_file_content(
                        owner, repo_name, "README.md"
                    )
                    readme_text = file_data.get("decoded_content", "")
                except Exception:
                    readme_text = ""

                text = f"{repo_name}\n{description}\n{readme_text}".strip()
                if not text:
                    continue

                texts.append(text[:2000])  # Truncate long READMEs
                ids.append(f"github:{owner}/{repo_name}")
                metadatas.append({
                    "source": "github",
                    "title": repo_name,
                    "description": description,
                    "repo": f"{owner}/{repo_name}",
                    "url": repo.get("html_url", ""),
                })

            if texts:
                embeddings = await self._embeddings.embed_batch(texts)
                for doc_id, text, embedding, metadata in zip(
                    ids, texts, embeddings, metadatas
                ):
                    await self._store.add_document(doc_id, text, embedding, metadata)
                count = len(texts)

            self._last_indexed["github"] = time.time()
            logger.info("github_indexed", count=count)
        except Exception as exc:
            logger.error("github_indexing_failed", error=str(exc))
        return count
