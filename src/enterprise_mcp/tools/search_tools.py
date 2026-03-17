"""Semantic search MCP tools — 3 tools for RAG-powered enterprise search."""

import json
import logging
from typing import Any

from mcp.types import Tool

from ..rag.embeddings import EmbeddingService
from ..rag.indexer import EnterpriseIndexer
from ..rag.vector_store import VectorStore
from .registry import register_tool

logger = logging.getLogger(__name__)


def register_search_tools(
    embedding_service: EmbeddingService,
    vector_store: VectorStore,
    indexer: EnterpriseIndexer,
) -> None:
    """Register all semantic search tools with the tool registry.

    Args:
        embedding_service: Configured EmbeddingService instance.
        vector_store: Configured VectorStore instance.
        indexer: Configured EnterpriseIndexer instance.
    """
    # ------------------------------------------------------------------ #
    # semantic_search
    # ------------------------------------------------------------------ #
    register_tool(
        Tool(
            name="semantic_search",
            description=(
                "Search across ALL enterprise content (Jira, Confluence, GitHub) by meaning. "
                "Unlike keyword search, this understands semantic similarity — searching for "
                "'payment failures' also finds 'checkout errors' and 'billing service down'."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Natural language search query",
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Maximum number of results to return (default 5)",
                        "default": 5,
                    },
                    "sources": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": ["jira", "confluence", "github"],
                        },
                        "description": (
                            "Filter results to specific sources "
                            "(default: all sources)"
                        ),
                    },
                },
                "required": ["query"],
            },
        ),
        _make_semantic_search(embedding_service, vector_store, indexer),
    )

    # ------------------------------------------------------------------ #
    # find_similar_issues
    # ------------------------------------------------------------------ #
    register_tool(
        Tool(
            name="find_similar_issues",
            description=(
                "Find Jira issues similar to a given description. "
                "Useful for detecting duplicates before creating a new issue."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "description": {
                        "type": "string",
                        "description": "Description of the issue to find matches for",
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Maximum number of similar issues to return (default 5)",
                        "default": 5,
                    },
                },
                "required": ["description"],
            },
        ),
        _make_find_similar_issues(embedding_service, vector_store),
    )

    # ------------------------------------------------------------------ #
    # knowledge_search
    # ------------------------------------------------------------------ #
    register_tool(
        Tool(
            name="knowledge_search",
            description=(
                "Search Confluence knowledge base by semantic meaning. "
                "Finds relevant documentation, runbooks, and wiki pages even when "
                "the exact keywords don't match."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Natural language search query for documentation",
                    },
                    "space_key": {
                        "type": "string",
                        "description": "Optional Confluence space key to restrict search",
                        "default": "",
                    },
                },
                "required": ["query"],
            },
        ),
        _make_knowledge_search(embedding_service, vector_store),
    )


# ---- Handler factory functions ------------------------------------------ #


def _make_semantic_search(
    embeddings: EmbeddingService,
    store: VectorStore,
    indexer: EnterpriseIndexer,
) -> Any:
    async def handler(
        query: str,
        top_k: int = 5,
        sources: list[str] | None = None,
    ) -> str:
        try:
            query_vec = await embeddings.embed_text(query)

            # Build filter if sources specified
            filter_dict: dict[str, Any] | None = None
            if sources and len(sources) == 1:
                filter_dict = {"source": sources[0]}

            results = await store.search(query_vec, top_k=top_k * 2, filter=filter_dict)

            # Post-filter for multiple sources
            if sources and len(sources) > 1:
                results = [r for r in results if r.metadata.get("source") in sources]

            results = results[:top_k]

            output = {
                "query": query,
                "results": [
                    {
                        "source": r.metadata.get("source", "unknown"),
                        "title": r.metadata.get("title", ""),
                        "snippet": r.text[:300],
                        "relevance_score": round(r.score, 4),
                        "url": r.metadata.get("url", ""),
                        "metadata": {
                            k: v
                            for k, v in r.metadata.items()
                            if k not in ("source", "title", "url")
                        },
                    }
                    for r in results
                ],
                "total_results": len(results),
                "index_stats": indexer.get_stats(),
            }
            return json.dumps(output, indent=2, default=str)
        except Exception as exc:
            logger.error(f"semantic_search failed: {exc}")
            return json.dumps({"error": str(exc)})

    return handler


def _make_find_similar_issues(
    embeddings: EmbeddingService,
    store: VectorStore,
) -> Any:
    async def handler(description: str, top_k: int = 5) -> str:
        try:
            query_vec = await embeddings.embed_text(description)
            results = await store.search(
                query_vec, top_k=top_k, filter={"source": "jira"}
            )

            output = {
                "query_description": description[:200],
                "similar_issues": [
                    {
                        "issue_key": r.metadata.get("issue_key", ""),
                        "title": r.metadata.get("title", ""),
                        "status": r.metadata.get("status", ""),
                        "priority": r.metadata.get("priority", ""),
                        "similarity_score": round(r.score, 4),
                        "url": r.metadata.get("url", ""),
                        "snippet": r.text[:200],
                    }
                    for r in results
                ],
                "total_found": len(results),
            }
            return json.dumps(output, indent=2, default=str)
        except Exception as exc:
            logger.error(f"find_similar_issues failed: {exc}")
            return json.dumps({"error": str(exc)})

    return handler


def _make_knowledge_search(
    embeddings: EmbeddingService,
    store: VectorStore,
) -> Any:
    async def handler(query: str, space_key: str = "") -> str:
        try:
            query_vec = await embeddings.embed_text(query)

            filter_dict: dict[str, Any] = {"source": "confluence"}
            if space_key:
                filter_dict["space_key"] = space_key

            results = await store.search(query_vec, top_k=10, filter=filter_dict)

            output = {
                "query": query,
                "results": [
                    {
                        "title": r.metadata.get("title", ""),
                        "page_id": r.metadata.get("page_id", ""),
                        "relevance_score": round(r.score, 4),
                        "url": r.metadata.get("url", ""),
                        "snippet": r.text[:400],
                    }
                    for r in results
                ],
                "total_results": len(results),
            }
            return json.dumps(output, indent=2, default=str)
        except Exception as exc:
            logger.error(f"knowledge_search failed: {exc}")
            return json.dumps({"error": str(exc)})

    return handler
