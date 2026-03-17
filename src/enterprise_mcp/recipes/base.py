"""Recipe base types and registry for agent workflows."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class RecipeStep:
    """A single step within a recipe workflow."""

    tool_name: str
    description: str
    parameters_template: dict[str, Any] = field(default_factory=dict)
    condition: str | None = None


@dataclass(frozen=True)
class Recipe:
    """A pre-built agentic workflow combining multiple tools."""

    name: str
    description: str
    category: str
    system_prompt: str
    starter_prompt: str
    required_tools: list[str]
    steps: list[RecipeStep]
    expected_outputs: list[str]
    tags: list[str] = field(default_factory=list)


@dataclass
class RecipeResult:
    """Structured output from executing a recipe."""

    recipe_name: str
    steps_taken: list[dict[str, Any]] = field(default_factory=list)
    outputs: dict[str, Any] = field(default_factory=dict)
    duration_seconds: float = 0.0
    status: str = "pending"
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "recipe_name": self.recipe_name,
            "status": self.status,
            "steps_taken": self.steps_taken,
            "outputs": self.outputs,
            "duration_seconds": round(self.duration_seconds, 3),
            "error": self.error,
        }


class RecipeRegistry:
    """Registry for discovering and retrieving recipes."""

    _recipes: dict[str, Recipe] = {}

    @classmethod
    def register(cls, recipe: Recipe) -> Recipe:
        cls._recipes[recipe.name] = recipe
        return recipe

    @classmethod
    def get(cls, name: str) -> Recipe | None:
        return cls._recipes.get(name)

    @classmethod
    def list_all(cls) -> list[Recipe]:
        return list(cls._recipes.values())

    @classmethod
    def list_by_category(cls, category: str) -> list[Recipe]:
        return [r for r in cls._recipes.values() if r.category == category]

    @classmethod
    def names(cls) -> list[str]:
        return list(cls._recipes.keys())


async def execute_recipe(
    recipe: Recipe,
    context: dict[str, Any],
    tool_caller: Any,
) -> RecipeResult:
    """Execute a recipe by running each step through the tool caller.

    Args:
        recipe: The recipe to execute.
        context: User-provided context parameters (e.g. project key, PR number).
        tool_caller: An async callable(tool_name, **params) -> str that dispatches tool calls.

    Returns:
        RecipeResult with all step outputs and timing.
    """
    result = RecipeResult(recipe_name=recipe.name, status="running")
    start = time.monotonic()

    try:
        for step in recipe.steps:
            if step.condition and not _evaluate_condition(step.condition, context, result.outputs):
                result.steps_taken.append({
                    "tool": step.tool_name,
                    "description": step.description,
                    "skipped": True,
                    "reason": f"Condition not met: {step.condition}",
                })
                continue

            params = _resolve_parameters(step.parameters_template, context, result.outputs)

            step_start = time.monotonic()
            output = await tool_caller(step.tool_name, **params)
            step_duration = time.monotonic() - step_start

            step_record = {
                "tool": step.tool_name,
                "description": step.description,
                "parameters": params,
                "duration_seconds": round(step_duration, 3),
                "output": output,
            }
            result.steps_taken.append(step_record)
            result.outputs[step.tool_name] = output

        result.status = "completed"
    except Exception as exc:
        result.status = "failed"
        result.error = str(exc)

    result.duration_seconds = time.monotonic() - start
    return result


def _resolve_parameters(
    template: dict[str, Any],
    context: dict[str, Any],
    prior_outputs: dict[str, Any],
) -> dict[str, Any]:
    """Substitute {{context.key}} and {{outputs.tool_name}} placeholders."""
    resolved: dict[str, Any] = {}
    for key, value in template.items():
        if isinstance(value, str) and value.startswith("{{") and value.endswith("}}"):
            ref = value[2:-2].strip()
            if ref.startswith("context."):
                resolved[key] = context.get(ref[8:], value)
            elif ref.startswith("outputs."):
                resolved[key] = prior_outputs.get(ref[8:], value)
            else:
                resolved[key] = context.get(ref, value)
        else:
            resolved[key] = value
    return resolved


def _evaluate_condition(
    condition: str,
    context: dict[str, Any],
    prior_outputs: dict[str, Any],
) -> bool:
    """Evaluate a simple condition like 'outputs.pagerduty_list_incidents' (truthy check)."""
    if condition.startswith("outputs."):
        return bool(prior_outputs.get(condition[8:]))
    if condition.startswith("context."):
        return bool(context.get(condition[8:]))
    return bool(context.get(condition))
