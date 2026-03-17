"""Pagination helpers for connector list operations."""

from collections.abc import Callable, Coroutine
from typing import Any


class PaginatedResponse:
    """Standard paginated response wrapper."""

    def __init__(
        self,
        items: list[Any],
        next_cursor: str | None = None,
        total: int | None = None,
        has_more: bool = False,
    ) -> None:
        self.items = items
        self.next_cursor = next_cursor
        self.total = total
        self.has_more = has_more

    def to_dict(self) -> dict[str, Any]:
        return {
            "items": self.items,
            "next_cursor": self.next_cursor,
            "total": self.total,
            "has_more": self.has_more,
        }


async def paginate_all(
    fetch_page: Callable[..., Coroutine[Any, Any, PaginatedResponse]],
    max_items: int = 1000,
    page_size: int = 50,
    **kwargs: Any,
) -> list[Any]:
    """Auto-paginate through all pages of a paginated API.

    Args:
        fetch_page: Async function that accepts cursor and page_size kwargs
                    and returns a PaginatedResponse.
        max_items: Maximum total items to collect.
        page_size: Number of items per page request.
        **kwargs: Additional arguments passed to fetch_page.

    Returns:
        Flat list of all collected items.
    """
    all_items: list[Any] = []
    cursor: str | None = None

    while len(all_items) < max_items:
        response = await fetch_page(cursor=cursor, page_size=page_size, **kwargs)
        all_items.extend(response.items)

        if not response.has_more or response.next_cursor is None:
            break
        cursor = response.next_cursor

    return all_items[:max_items]
