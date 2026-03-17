"""GitHub REST API v3 connector."""

import logging
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from .base import BaseConnector

logger = logging.getLogger(__name__)


class GitHubConnector(BaseConnector):
    """GitHub REST API v3 connector.

    Authenticates via a Personal Access Token (Bearer token) and provides
    methods for common GitHub operations with automatic retry logic.
    """

    BASE_URL = "https://api.github.com"

    def __init__(self, token: str, default_owner: str = "") -> None:
        """Initialize the GitHub connector.

        Args:
            token: GitHub Personal Access Token.
            default_owner: Default owner (org or user) for repository operations.
        """
        self._token = token
        self.default_owner = default_owner
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Return a lazily-initialized async HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.BASE_URL,
                headers={
                    "Authorization": f"Bearer {self._token}",
                    "Accept": "application/vnd.github.v3+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
                timeout=30.0,
            )
        return self._client

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def get_repo(self, owner: str, repo: str) -> dict[str, Any]:
        """Get repository information including stars, forks, open issues, and PRs.

        Args:
            owner: Repository owner (organization or user).
            repo: Repository name.

        Returns:
            Repository metadata including description, stars, forks, open issues.
        """
        client = await self._get_client()
        response = await client.get(f"/repos/{owner}/{repo}")
        self._raise_for_status(response, f"get_repo({owner}/{repo})")
        return response.json()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def list_issues(
        self,
        owner: str,
        repo: str,
        state: str = "open",
        labels: str = "",
        assignee: str = "",
        max_results: int = 30,
    ) -> list[dict[str, Any]]:
        """List GitHub issues for a repository.

        Args:
            owner: Repository owner.
            repo: Repository name.
            state: Filter by state ('open', 'closed', or 'all'). Defaults to 'open'.
            labels: Comma-separated list of label names to filter by.
            assignee: GitHub username to filter issues by assignee.
            max_results: Maximum number of issues to return.

        Returns:
            List of issues with title, body, labels, assignee, and dates.
        """
        client = await self._get_client()
        params: dict[str, Any] = {
            "state": state,
            "per_page": min(max_results, 100),
        }
        if labels:
            params["labels"] = labels
        if assignee:
            params["assignee"] = assignee

        response = await client.get(f"/repos/{owner}/{repo}/issues", params=params)
        self._raise_for_status(response, f"list_issues({owner}/{repo})")
        # Exclude pull requests (GitHub returns them as issues too)
        return [i for i in response.json() if "pull_request" not in i]

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def create_issue(
        self,
        owner: str,
        repo: str,
        title: str,
        body: str = "",
        labels: list[str] | None = None,
        assignees: list[str] | None = None,
    ) -> dict[str, Any]:
        """Create a new GitHub issue.

        Args:
            owner: Repository owner.
            repo: Repository name.
            title: Issue title.
            body: Issue description in Markdown.
            labels: List of label names to apply.
            assignees: List of GitHub usernames to assign.

        Returns:
            Created issue data including number, URL, and state.
        """
        client = await self._get_client()
        payload: dict[str, Any] = {"title": title}
        if body:
            payload["body"] = body
        if labels:
            payload["labels"] = labels
        if assignees:
            payload["assignees"] = assignees

        response = await client.post(f"/repos/{owner}/{repo}/issues", json=payload)
        self._raise_for_status(response, f"create_issue({owner}/{repo})")
        return response.json()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def get_pull_request(
        self, owner: str, repo: str, pr_number: int
    ) -> dict[str, Any]:
        """Get detailed information about a pull request.

        Args:
            owner: Repository owner.
            repo: Repository name.
            pr_number: Pull request number.

        Returns:
            PR details including title, body, state, reviews, and checks.
        """
        client = await self._get_client()
        response = await client.get(f"/repos/{owner}/{repo}/pulls/{pr_number}")
        self._raise_for_status(response, f"get_pull_request({owner}/{repo}#{pr_number})")
        pr = response.json()

        # Fetch review status
        reviews_response = await client.get(
            f"/repos/{owner}/{repo}/pulls/{pr_number}/reviews"
        )
        if reviews_response.is_success:
            pr["reviews"] = reviews_response.json()

        return pr

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def list_pull_requests(
        self,
        owner: str,
        repo: str,
        state: str = "open",
        base: str = "",
        max_results: int = 30,
    ) -> list[dict[str, Any]]:
        """List pull requests for a repository.

        Args:
            owner: Repository owner.
            repo: Repository name.
            state: Filter by state ('open', 'closed', or 'all'). Defaults to 'open'.
            base: Filter PRs by base branch name.
            max_results: Maximum number of PRs to return.

        Returns:
            List of PRs with title, state, author, base/head branches, and dates.
        """
        client = await self._get_client()
        params: dict[str, Any] = {
            "state": state,
            "per_page": min(max_results, 100),
            "sort": "updated",
            "direction": "desc",
        }
        if base:
            params["base"] = base

        response = await client.get(f"/repos/{owner}/{repo}/pulls", params=params)
        self._raise_for_status(response, f"list_pull_requests({owner}/{repo})")
        return response.json()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def search_code(
        self, query: str, owner: str = "", repo: str = "", max_results: int = 30
    ) -> dict[str, Any]:
        """Search for code across GitHub repositories.

        Args:
            query: Search query string (GitHub code search syntax).
            owner: Restrict search to this owner/org.
            repo: Restrict search to this repository (requires owner).
            max_results: Maximum number of results to return.

        Returns:
            Search results with file paths, repository names, and match context.
        """
        client = await self._get_client()
        q = query
        if owner and repo:
            q += f" repo:{owner}/{repo}"
        elif owner:
            q += f" org:{owner}"

        response = await client.get(
            "/search/code",
            params={"q": q, "per_page": min(max_results, 100)},
        )
        self._raise_for_status(response, f"search_code({q!r})")
        return response.json()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def get_file_content(
        self, owner: str, repo: str, path: str, ref: str = ""
    ) -> dict[str, Any]:
        """Read the content of a file from a GitHub repository.

        Args:
            owner: Repository owner.
            repo: Repository name.
            path: File path within the repository (e.g., src/main.py).
            ref: Branch, tag, or commit SHA (defaults to the default branch).

        Returns:
            File content (decoded from base64), SHA, and metadata.
        """
        import base64

        client = await self._get_client()
        params: dict[str, Any] = {}
        if ref:
            params["ref"] = ref

        response = await client.get(
            f"/repos/{owner}/{repo}/contents/{path}", params=params
        )
        self._raise_for_status(response, f"get_file_content({owner}/{repo}/{path})")
        data = response.json()

        if isinstance(data, dict) and data.get("encoding") == "base64":
            content_bytes = base64.b64decode(data["content"].replace("\n", ""))
            try:
                data["decoded_content"] = content_bytes.decode("utf-8")
            except UnicodeDecodeError:
                data["decoded_content"] = f"[Binary file — {len(content_bytes)} bytes]"
        return data

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def create_review_comment(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        body: str,
        commit_id: str,
        path: str,
        line: int,
    ) -> dict[str, Any]:
        """Add a review comment to a specific line in a pull request diff.

        Args:
            owner: Repository owner.
            repo: Repository name.
            pr_number: Pull request number.
            body: Review comment text (supports Markdown).
            commit_id: SHA of the commit to comment on.
            path: Relative path to the file being commented on.
            line: Line number in the file to attach the comment to.

        Returns:
            Created review comment with ID, URL, and author information.
        """
        client = await self._get_client()
        payload = {
            "body": body,
            "commit_id": commit_id,
            "path": path,
            "line": line,
        }
        response = await client.post(
            f"/repos/{owner}/{repo}/pulls/{pr_number}/comments", json=payload
        )
        self._raise_for_status(
            response, f"create_review_comment({owner}/{repo}#{pr_number})"
        )
        return response.json()
