"""Integration tests for GitHub connector with full mock server routes."""

import base64

import httpx
import pytest
import respx

from enterprise_mcp.connectors.github import GitHubConnector

GITHUB_API = "https://api.github.com"
OWNER = "integration-org"
REPO = "integration-repo"


@pytest.fixture
def github_connector():
    return GitHubConnector("ghp_integration_token", OWNER)


@pytest.fixture
def mock_github_api():
    """Set up a full GitHub mock API with all routes."""
    with respx.mock:
        # GET /repos/{owner}/{repo}
        respx.get(f"{GITHUB_API}/repos/{OWNER}/{REPO}").mock(
            return_value=httpx.Response(200, json={
                "id": 1,
                "name": REPO,
                "full_name": f"{OWNER}/{REPO}",
                "description": "Integration test repository",
                "stargazers_count": 100,
                "forks_count": 25,
                "open_issues_count": 5,
                "default_branch": "main",
                "topics": ["python", "mcp"],
                "html_url": f"https://github.com/{OWNER}/{REPO}",
            })
        )

        # GET /repos/{owner}/{repo}/issues
        respx.get(f"{GITHUB_API}/repos/{OWNER}/{REPO}/issues").mock(
            return_value=httpx.Response(200, json=[
                {
                    "number": 1,
                    "title": "Bug: API timeout",
                    "state": "open",
                    "labels": [{"name": "bug"}],
                    "assignee": {"login": "dev1"},
                    "body": "The API times out under load.",
                    "created_at": "2024-06-01T10:00:00Z",
                    "updated_at": "2024-06-01T12:00:00Z",
                },
                {
                    "number": 2,
                    "title": "Feature: Add caching",
                    "state": "open",
                    "labels": [{"name": "enhancement"}],
                    "assignee": None,
                    "body": "Add Redis caching layer.",
                    "created_at": "2024-06-02T10:00:00Z",
                    "updated_at": "2024-06-02T12:00:00Z",
                },
            ])
        )

        # POST /repos/{owner}/{repo}/issues (create)
        respx.post(f"{GITHUB_API}/repos/{OWNER}/{REPO}/issues").mock(
            return_value=httpx.Response(201, json={
                "number": 3,
                "title": "New integration test issue",
                "state": "open",
                "html_url": f"https://github.com/{OWNER}/{REPO}/issues/3",
            })
        )

        # GET /repos/{owner}/{repo}/pulls
        respx.get(f"{GITHUB_API}/repos/{OWNER}/{REPO}/pulls").mock(
            return_value=httpx.Response(200, json=[
                {
                    "number": 10,
                    "title": "Add caching layer",
                    "state": "open",
                    "user": {"login": "dev1"},
                    "head": {"ref": "feature/caching"},
                    "base": {"ref": "main"},
                    "created_at": "2024-06-03T10:00:00Z",
                },
            ])
        )

        # GET /repos/{owner}/{repo}/pulls/10
        respx.get(f"{GITHUB_API}/repos/{OWNER}/{REPO}/pulls/10").mock(
            return_value=httpx.Response(200, json={
                "number": 10,
                "title": "Add caching layer",
                "state": "open",
                "body": "Implements Redis caching.",
                "user": {"login": "dev1"},
                "head": {"ref": "feature/caching", "sha": "abc123"},
                "base": {"ref": "main"},
                "mergeable": True,
                "additions": 200,
                "deletions": 10,
            })
        )

        # GET /repos/{owner}/{repo}/pulls/10/reviews
        respx.get(f"{GITHUB_API}/repos/{OWNER}/{REPO}/pulls/10/reviews").mock(
            return_value=httpx.Response(200, json=[
                {
                    "id": 1,
                    "user": {"login": "reviewer1"},
                    "state": "APPROVED",
                    "body": "LGTM!",
                },
            ])
        )

        # GET /repos/{owner}/{repo}/contents/{path}
        file_content = base64.b64encode(b"print('hello world')").decode()
        respx.get(f"{GITHUB_API}/repos/{OWNER}/{REPO}/contents/src/main.py").mock(
            return_value=httpx.Response(200, json={
                "name": "main.py",
                "path": "src/main.py",
                "sha": "def456",
                "size": 20,
                "encoding": "base64",
                "content": file_content,
            })
        )

        # GET /search/code
        respx.get(f"{GITHUB_API}/search/code").mock(
            return_value=httpx.Response(200, json={
                "total_count": 1,
                "items": [
                    {
                        "name": "main.py",
                        "path": "src/main.py",
                        "repository": {"full_name": f"{OWNER}/{REPO}"},
                    }
                ],
            })
        )

        yield


@pytest.mark.asyncio
async def test_repo_and_issues_workflow(github_connector, mock_github_api):
    """Test reading repo info, listing issues, and creating an issue."""
    # Get repo info
    repo = await github_connector.get_repo(OWNER, REPO)
    assert repo["stargazers_count"] == 100
    assert repo["name"] == REPO

    # List issues
    issues = await github_connector.list_issues(OWNER, REPO)
    assert len(issues) == 2
    assert issues[0]["title"] == "Bug: API timeout"

    # Create issue
    created = await github_connector.create_issue(
        OWNER, REPO, "New integration test issue", "Test body"
    )
    assert created["number"] == 3


@pytest.mark.asyncio
async def test_pull_request_workflow(github_connector, mock_github_api):
    """Test listing PRs and getting PR details with reviews."""
    prs = await github_connector.list_pull_requests(OWNER, REPO)
    assert len(prs) == 1

    pr = await github_connector.get_pull_request(OWNER, REPO, 10)
    assert pr["title"] == "Add caching layer"
    assert pr["reviews"][0]["state"] == "APPROVED"


@pytest.mark.asyncio
async def test_file_content(github_connector, mock_github_api):
    """Test reading file content from repository."""
    content = await github_connector.get_file_content(OWNER, REPO, "src/main.py")
    assert content["decoded_content"] == "print('hello world')"


@pytest.mark.asyncio
async def test_code_search(github_connector, mock_github_api):
    """Test searching for code across repositories."""
    results = await github_connector.search_code("hello", OWNER, REPO)
    assert results["total_count"] == 1
