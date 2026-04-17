from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RetrievalPlan:
    """Minimal first-pass planner (will expand in later steps)."""

    include_infrastructure: bool = False


def plan_retrieval(*, user_message: str) -> RetrievalPlan:
    """Return a per-turn retrieval plan.

    Current implementation is conservative: only opts into large artifacts
    (like INFRASTRUCTURE.md) on explicit user intent.
    """
    msg = (user_message or "").lower()
    include_infra = any(
        k in msg
        for k in (
            "infrastructure.md",
            "infrastructure file",
            "memory infrastructure",
            "cortical lattice infrastructure",
            "diagram requirement",
        )
    )
    return RetrievalPlan(include_infrastructure=include_infra)

