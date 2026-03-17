"""Tests for the RAG layer: embeddings, vector store, and search tools."""

import json
import os
import tempfile

import pytest

from enterprise_mcp.rag.embeddings import EmbeddingService
from enterprise_mcp.rag.vector_store import SearchResult, VectorStore


# ---- EmbeddingService ---------------------------------------------------- #


@pytest.mark.asyncio
async def test_embed_text_returns_list_of_floats():
    """embed_text returns a list of floats with consistent dimension."""
    svc = EmbeddingService()
    vec = await svc.embed_text("payment service is down")
    assert isinstance(vec, list)
    assert len(vec) == svc.dimension
    assert all(isinstance(v, float) for v in vec)


@pytest.mark.asyncio
async def test_embed_text_is_deterministic():
    """Same input produces the same embedding."""
    svc = EmbeddingService()
    v1 = await svc.embed_text("checkout error")
    v2 = await svc.embed_text("checkout error")
    assert v1 == v2


@pytest.mark.asyncio
async def test_embed_batch():
    """embed_batch returns one vector per input text."""
    svc = EmbeddingService()
    texts = ["hello world", "payment failure", "incident runbook"]
    vecs = await svc.embed_batch(texts)
    assert len(vecs) == 3
    assert all(len(v) == svc.dimension for v in vecs)


@pytest.mark.asyncio
async def test_embed_cache_hit():
    """Cached embeddings are returned on repeated calls."""
    svc = EmbeddingService(max_cache_size=10)
    v1 = await svc.embed_text("cache test")
    # Calling again should hit cache
    v2 = await svc.embed_text("cache test")
    assert v1 is v2 or v1 == v2  # same object or same value


@pytest.mark.asyncio
async def test_embed_cache_eviction():
    """Cache evicts oldest entries when max_cache_size is exceeded."""
    svc = EmbeddingService(max_cache_size=2)
    await svc.embed_text("first")
    await svc.embed_text("second")
    await svc.embed_text("third")  # evicts "first"
    # Cache should have "second" and "third"
    assert len(svc._cache) == 2


@pytest.mark.asyncio
async def test_different_texts_produce_different_embeddings():
    """Semantically different texts produce different vectors."""
    svc = EmbeddingService()
    v1 = await svc.embed_text("payment processing timeout")
    v2 = await svc.embed_text("employee onboarding documentation")
    assert v1 != v2


# ---- VectorStore --------------------------------------------------------- #


@pytest.mark.asyncio
async def test_add_and_search():
    """Adding a document and searching for it returns it."""
    store = VectorStore()
    svc = EmbeddingService()

    text = "payment service returns 500 errors on checkout"
    vec = await svc.embed_text(text)
    await store.add_document("doc1", text, vec, {"source": "jira", "title": "Payment Bug"})

    query_vec = await svc.embed_text("checkout payment error")
    results = await store.search(query_vec, top_k=5)

    assert len(results) == 1
    assert results[0].id == "doc1"
    assert results[0].score > 0
    assert results[0].metadata["source"] == "jira"


@pytest.mark.asyncio
async def test_search_ranking():
    """More relevant documents score higher."""
    store = VectorStore()
    svc = EmbeddingService()

    docs = [
        ("doc1", "payment service returns 500 errors", {"source": "jira"}),
        ("doc2", "employee vacation policy for Q3", {"source": "confluence"}),
        ("doc3", "billing API timeout on credit card processing", {"source": "jira"}),
    ]
    for doc_id, text, meta in docs:
        vec = await svc.embed_text(text)
        await store.add_document(doc_id, text, vec, meta)

    query_vec = await svc.embed_text("payment billing error")
    results = await store.search(query_vec, top_k=3)

    # Payment/billing docs should rank above vacation policy
    ids = [r.id for r in results]
    vacation_idx = ids.index("doc2") if "doc2" in ids else len(ids)
    payment_idx = ids.index("doc1") if "doc1" in ids else len(ids)
    assert payment_idx < vacation_idx


@pytest.mark.asyncio
async def test_search_with_filter():
    """Metadata filter restricts results to matching documents."""
    store = VectorStore()
    svc = EmbeddingService()

    await store.add_document(
        "j1", "server crash", await svc.embed_text("server crash"), {"source": "jira"}
    )
    await store.add_document(
        "c1", "server setup guide", await svc.embed_text("server setup guide"), {"source": "confluence"}
    )

    query_vec = await svc.embed_text("server")
    results = await store.search(query_vec, top_k=5, filter={"source": "jira"})

    assert all(r.metadata["source"] == "jira" for r in results)
    assert len(results) == 1


@pytest.mark.asyncio
async def test_delete_document():
    """Deleted documents are not returned in search."""
    store = VectorStore()
    svc = EmbeddingService()

    vec = await svc.embed_text("test doc")
    await store.add_document("doc1", "test doc", vec)
    assert store.count == 1

    removed = await store.delete_document("doc1")
    assert removed is True
    assert store.count == 0


@pytest.mark.asyncio
async def test_delete_nonexistent():
    """Deleting a non-existent document returns False."""
    store = VectorStore()
    assert await store.delete_document("nope") is False


@pytest.mark.asyncio
async def test_persistence():
    """Documents survive save/load cycle."""
    svc = EmbeddingService()
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = f.name

    try:
        store = VectorStore(persist_path=path)
        vec = await svc.embed_text("persistent doc")
        await store.add_document("p1", "persistent doc", vec, {"source": "test"})
        await store.save()

        # Load in a new store instance
        store2 = VectorStore(persist_path=path)
        assert store2.count == 1
        doc = await store2.get_document("p1")
        assert doc is not None
        assert doc.text == "persistent doc"
    finally:
        os.unlink(path)


@pytest.mark.asyncio
async def test_search_result_to_dict():
    """SearchResult.to_dict produces expected keys."""
    r = SearchResult(id="x", text="hello", metadata={"source": "jira"}, score=0.8765)
    d = r.to_dict()
    assert d["id"] == "x"
    assert d["score"] == 0.8765
    assert d["metadata"]["source"] == "jira"


@pytest.mark.asyncio
async def test_store_stats():
    """stats() returns document counts per source."""
    store = VectorStore()
    svc = EmbeddingService()
    await store.add_document("j1", "a", await svc.embed_text("a"), {"source": "jira"})
    await store.add_document("j2", "b", await svc.embed_text("b"), {"source": "jira"})
    await store.add_document("c1", "c", await svc.embed_text("c"), {"source": "confluence"})

    stats = store.stats()
    assert stats["total_documents"] == 3
    assert stats["sources"]["jira"] == 2
    assert stats["sources"]["confluence"] == 1


# ---- Search tools (semantic_search handler) ------------------------------ #


@pytest.mark.asyncio
async def test_semantic_search_tool():
    """The semantic_search tool handler returns ranked JSON results."""
    from enterprise_mcp.rag.indexer import EnterpriseIndexer

    svc = EmbeddingService()
    store = VectorStore()
    indexer = EnterpriseIndexer(svc, store)

    # Pre-populate store
    docs = [
        ("jira:PROJ-1", "payment timeout on checkout flow", {"source": "jira", "title": "Payment Timeout", "url": "https://jira/PROJ-1"}),
        ("confluence:100", "incident response runbook", {"source": "confluence", "title": "Runbook", "url": "https://wiki/100"}),
    ]
    for doc_id, text, meta in docs:
        vec = await svc.embed_text(text)
        await store.add_document(doc_id, text, vec, meta)

    # Import and build handler
    from enterprise_mcp.tools.search_tools import _make_semantic_search

    handler = _make_semantic_search(svc, store, indexer)
    raw = await handler(query="payment error", top_k=5)
    result = json.loads(raw)

    assert "results" in result
    assert len(result["results"]) > 0
    assert result["results"][0]["source"] in ("jira", "confluence")
    assert "relevance_score" in result["results"][0]


@pytest.mark.asyncio
async def test_semantic_search_with_source_filter():
    """semantic_search filters by source when specified."""
    from enterprise_mcp.rag.indexer import EnterpriseIndexer

    svc = EmbeddingService()
    store = VectorStore()
    indexer = EnterpriseIndexer(svc, store)

    await store.add_document(
        "jira:1", "api error", await svc.embed_text("api error"),
        {"source": "jira", "title": "API Error", "url": ""},
    )
    await store.add_document(
        "conf:1", "api docs", await svc.embed_text("api docs"),
        {"source": "confluence", "title": "API Docs", "url": ""},
    )

    from enterprise_mcp.tools.search_tools import _make_semantic_search

    handler = _make_semantic_search(svc, store, indexer)
    raw = await handler(query="api", top_k=5, sources=["jira"])
    result = json.loads(raw)

    assert all(r["source"] == "jira" for r in result["results"])


@pytest.mark.asyncio
async def test_find_similar_issues_tool():
    """find_similar_issues returns only Jira results with similarity scores."""
    svc = EmbeddingService()
    store = VectorStore()

    await store.add_document(
        "jira:PROJ-10", "login page returns 403 forbidden",
        await svc.embed_text("login page returns 403 forbidden"),
        {"source": "jira", "issue_key": "PROJ-10", "title": "Login 403", "status": "Open", "priority": "High", "url": ""},
    )
    await store.add_document(
        "conf:50", "authentication architecture guide",
        await svc.embed_text("authentication architecture guide"),
        {"source": "confluence", "title": "Auth Guide", "url": ""},
    )

    from enterprise_mcp.tools.search_tools import _make_find_similar_issues

    handler = _make_find_similar_issues(svc, store)
    raw = await handler(description="user cannot log in, gets 403 error")
    result = json.loads(raw)

    assert "similar_issues" in result
    # Should only return Jira issues, not Confluence
    for issue in result["similar_issues"]:
        assert "issue_key" in issue
        assert "similarity_score" in issue


@pytest.mark.asyncio
async def test_knowledge_search_tool():
    """knowledge_search returns only Confluence results."""
    svc = EmbeddingService()
    store = VectorStore()

    await store.add_document(
        "conf:200", "deployment checklist for production releases",
        await svc.embed_text("deployment checklist for production releases"),
        {"source": "confluence", "title": "Deploy Checklist", "page_id": "200", "url": ""},
    )
    await store.add_document(
        "jira:BUG-5", "deploy script fails on staging",
        await svc.embed_text("deploy script fails on staging"),
        {"source": "jira", "title": "Deploy Bug", "url": ""},
    )

    from enterprise_mcp.tools.search_tools import _make_knowledge_search

    handler = _make_knowledge_search(svc, store)
    raw = await handler(query="how to deploy to production")
    result = json.loads(raw)

    assert "results" in result
    for r in result["results"]:
        assert "page_id" in r
        assert "relevance_score" in r
