"""Recipe catalog — auto-registers all built-in recipes on import."""

from . import (
    bug_triage,
    incident_triage,
    onboarding_checklist,
    pr_review_assistant,
    sprint_review,
    weekly_digest,
)

__all__ = [
    "bug_triage",
    "incident_triage",
    "onboarding_checklist",
    "pr_review_assistant",
    "sprint_review",
    "weekly_digest",
]
