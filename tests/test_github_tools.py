"""Tests for the GitHub connector and tools."""

import httpx
import pytest
import respx

from enterprise_mcp.connectors.github import GitHubConnector

GITHUB_API = "https://api.github.com"
ORG = "test-org"
REPO = "test-repo"


# ---- get_repo ------------------------------------------------------------ #


@pytest.mark.asyncio
async def test_get_repo_success(github_repo_payload):
    """get_repo returns repository metadata on HTTP 200."""
    async with respx.mock:
        respx.get(f"{GITHUB_API}/repos/{ORG}/{REPO}").mock(
            return_value=httpx.Response(200, json=github_repo_payload)
        )
        connector = GitHubConnector("ghp_test_token", ORG)
        result = await connector.get_repo(ORG, REPO)

    assert result["name"] == REPO
    assert result["stargazers_count"] == 42


@pytest.mark.asyncio
async def test_get_repo_not_found():
    """get_repo raises HTTPStatusError on HTTP 404."""
    async with respx.mock:
        respx.get(f"{GITHUB_API}/repos/{ORG}/nonexistent").mock(
            return_value=httpx.Response(404, json={"message": "Not Found"})
        )
        connector = GitHubConnector("ghp_test_token", ORG)
        with pytest.raises(httpx.HTTPStatusError):
            await connector.get_repo(ORG, "nonexistent")


@pytest.mark.asyncio
async def test_get_repo_rate_limit():
    """get_repo raises HTTPStatusError when rate-limited (HTTP 403 + message)."""
    async with respx.mock:
        respx.get(f"{GITHUB_API}/repos/{ORG}/{REPO}").mock(
            return_value=httpx.Response(
                403,
                json={"message": "API rate limit exceeded"},
                headers={"X-RateLimit-Remaining": "0"},
            )
        )
        connector = GitHubConnector("ghp_test_token", ORG)
        with pytest.raises(httpx.HTTPStatusError):
            await connector.get_repo(ORG, REPO)


# ---- list_issues --------------------------------------------------------- #


@pytest.mark.asyncio
async def test_list_issues_success(github_issues_payload):
    """list_issues returns open issues, excluding pull requests."""
    async with respx.mock:
        respx.get(f"{GITHUB_API}/repos/{ORG}/{REPO}/issues").mock(
            return_value=httpx.Response(200, json=github_issues_payload)
        )
        connector = GitHubConnector("ghp_test_token", ORG)
        result = await connector.list_issues(ORG, REPO)

    assert len(result) == 1
    assert result[0]["number"] == 1
    assert "pull_request" not in result[0]


@pytest.mark.asyncio
async def test_list_issues_excludes_prs():
    """list_issues filters out pull requests from the response."""
    mixed = [
        {"number": 1, "title": "Bug", "state": "open"},
        {"number": 2, "title": "PR fix", "state": "open", "pull_request": {"url": "..."}},
    ]
    async with respx.mock:
        respx.get(f"{GITHUB_API}/repos/{ORG}/{REPO}/issues").mock(
            return_value=httpx.Response(200, json=mixed)
        )
        connector = GitHubConnector("ghp_test_token", ORG)
        result = await connector.list_issues(ORG, REPO)

    assert len(result) == 1
    assert result[0]["number"] == 1


@pytest.mark.asyncio
async def test_list_issues_server_error():
    """list_issues raises HTTPStatusError on HTTP 500."""
    async with respx.mock:
        respx.get(f"{GITHUB_API}/repos/{ORG}/{REPO}/issues").mock(
            return_value=httpx.Response(500, json={"message": "Server error"})
        )
        connector = GitHubConnector("ghp_test_token", ORG)
        with pytest.raises(httpx.HTTPStatusError):
            await connector.list_issues(ORG, REPO)


# ---- get_pull_request ---------------------------------------------------- #


@pytest.mark.asyncio
async def test_get_pull_request_success(github_pr_payload):
    """get_pull_request returns PR details with review info on HTTP 200."""
    async with respx.mock:
        respx.get(f"{GITHUB_API}/repos/{ORG}/{REPO}/pulls/42").mock(
            return_value=httpx.Response(200, json=github_pr_payload)
        )
        respx.get(f"{GITHUB_API}/repos/{ORG}/{REPO}/pulls/42/reviews").mock(
            return_value=httpx.Response(200, json=[])
        )
        connector = GitHubConnector("ghp_test_token", ORG)
        result = await connector.get_pull_request(ORG, REPO, 42)

    assert result["number"] == 42
    assert result["title"] == "Fix payment timeout"
    assert "reviews" in result


@pytest.mark.asyncio
async def test_get_pull_request_not_found():
    """get_pull_request raises HTTPStatusError on HTTP 404."""
    async with respx.mock:
        respx.get(f"{GITHUB_API}/repos/{ORG}/{REPO}/pulls/9999").mock(
            return_value=httpx.Response(404, json={"message": "Not Found"})
        )
        connector = GitHubConnector("ghp_test_token", ORG)
        with pytest.raises(httpx.HTTPStatusError):
            await connector.get_pull_request(ORG, REPO, 9999)


# ---- create_issue -------------------------------------------------------- #


@pytest.mark.asyncio
async def test_create_issue_success():
    """create_issue returns the created issue on HTTP 201."""
    created = {
        "number": 10,
        "title": "New issue",
        "state": "open",
        "html_url": f"https://github.com/{ORG}/{REPO}/issues/10",
    }
    async with respx.mock:
        respx.post(f"{GITHUB_API}/repos/{ORG}/{REPO}/issues").mock(
            return_value=httpx.Response(201, json=created)
        )
        connector = GitHubConnector("ghp_test_token", ORG)
        result = await connector.create_issue(ORG, REPO, "New issue", "Body text")

    assert result["number"] == 10


# ---- get_file_content ---------------------------------------------------- #


@pytest.mark.asyncio
async def test_get_file_content_success():
    """get_file_content decodes base64 file content correctly."""
    import base64

    raw_content = "print('hello world')\n"
    encoded = base64.b64encode(raw_content.encode()).decode()

    payload = {
        "name": "main.py",
        "path": "src/main.py",
        "sha": "abc123",
        "encoding": "base64",
        "content": encoded + "\n",
        "size": len(raw_content),
    }
    async with respx.mock:
        respx.get(f"{GITHUB_API}/repos/{ORG}/{REPO}/contents/src/main.py").mock(
            return_value=httpx.Response(200, json=payload)
        )
        connector = GitHubConnector("ghp_test_token", ORG)
        result = await connector.get_file_content(ORG, REPO, "src/main.py")

    assert result["decoded_content"] == raw_content


@pytest.mark.asyncio
async def test_get_file_content_not_found():
    """get_file_content raises HTTPStatusError on HTTP 404."""
    async with respx.mock:
        respx.get(f"{GITHUB_API}/repos/{ORG}/{REPO}/contents/missing.py").mock(
            return_value=httpx.Response(404, json={"message": "Not Found"})
        )
        connector = GitHubConnector("ghp_test_token", ORG)
        with pytest.raises(httpx.HTTPStatusError):
            await connector.get_file_content(ORG, REPO, "missing.py")
