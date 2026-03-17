"""MCP tools for listing and executing agent recipes."""

import json
import logging
from typing import Any

from mcp.types import Tool

from ..recipes.base import RecipeRegistry, execute_recipe
from .registry import get_handler, register_tool

logger = logging.getLogger(__name__)


def register_recipe_tools() -> None:
    """Register the recipe listing and execution tools."""

    # Ensure catalog is loaded (auto-registers recipes on import)
    import enterprise_mcp.recipes.catalog  # noqa: F401

    register_tool(
        Tool(
            name="list_recipes",
            description=(
                "List all available agent recipes (pre-built agentic workflows). "
                "Each recipe combines multiple tools into a structured multi-step workflow "
                "for common enterprise scenarios like incident triage, sprint reviews, and bug triage."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Optional category filter (e.g. 'incident_response', 'reporting', 'code_review', 'onboarding', 'bug_management')",
                    },
                },
                "required": [],
            },
        ),
        _make_list_recipes(),
    )

    register_tool(
        Tool(
            name="run_recipe",
            description=(
                "Execute an agent recipe by name. Runs each step in sequence, calling the "
                "required tools with the provided context parameters. Returns a structured "
                "result with all step outputs, timing, and status."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "recipe_name": {
                        "type": "string",
                        "description": "Name of the recipe to execute (use list_recipes to see available recipes)",
                    },
                    "context": {
                        "type": "object",
                        "description": "Context parameters for the recipe (e.g. project_key, repo, pr_number). Required keys depend on the recipe.",
                    },
                },
                "required": ["recipe_name", "context"],
            },
        ),
        _make_run_recipe(),
    )

    logger.info("Registered 2 recipe tools (list_recipes, run_recipe)")


def _make_list_recipes():  # noqa: ANN202
    async def handler(category: str | None = None) -> str:
        if category:
            recipes = RecipeRegistry.list_by_category(category)
        else:
            recipes = RecipeRegistry.list_all()

        result = []
        for r in recipes:
            result.append({
                "name": r.name,
                "description": r.description,
                "category": r.category,
                "required_tools": r.required_tools,
                "steps": len(r.steps),
                "expected_outputs": r.expected_outputs,
                "tags": r.tags,
                "system_prompt_preview": r.system_prompt[:150] + "...",
            })

        return json.dumps({"recipes": result, "total": len(result)}, indent=2)

    return handler


def _make_run_recipe():  # noqa: ANN202
    async def handler(recipe_name: str, context: dict[str, Any] | None = None) -> str:
        recipe = RecipeRegistry.get(recipe_name)
        if recipe is None:
            available = RecipeRegistry.names()
            return json.dumps({
                "error": f"Recipe {recipe_name!r} not found",
                "available_recipes": available,
            })

        context = context or {}

        async def tool_caller(tool_name: str, **params: Any) -> str:
            tool_handler = get_handler(tool_name)
            if tool_handler is None:
                return json.dumps({"error": f"Tool {tool_name!r} not available. Is the connector configured?"})
            return await tool_handler(**params)

        result = await execute_recipe(recipe, context, tool_caller)
        return json.dumps(result.to_dict(), indent=2, default=str)

    return handler
