from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RetrievalPlan:
    """Per-turn retrieval plan for Cortical Lattice ephemeral context."""

    include_infrastructure: bool = False
    include_state: bool = False
    include_skills: bool = False
    include_bootstrap: bool = False
    include_routing_indexes: bool = False
    include_promotion: bool = False
    include_observability: bool = False
    include_semantic: bool = False
    include_cases: bool = False
    include_hazards: bool = False
    include_prospective: bool = False
    include_social_roles: bool = False


def _contains_any(msg: str, terms: tuple[str, ...]) -> bool:
    return any(t in msg for t in terms)


def plan_retrieval(*, user_message: str) -> RetrievalPlan:
    """Return a compact retrieval plan based on the user's intent.

    Heuristic goals:
    - Keep default resident context minimal.
    - Pull in deeper layers only when the turn semantics require them.
    - Prefer operationally useful indexes (routing/promotion) over broad dumps.
    """
    msg = (user_message or "").lower()

    include_infra = _contains_any(
        msg,
        (
            "infrastructure.md",
            "infrastructure file",
            "memory infrastructure",
            "cortical lattice infrastructure",
            "diagram requirement",
            "full inventory",
        ),
    )

    include_state = _contains_any(
        msg,
        (
            "current state",
            "working memory",
            "blocker",
            "next actions",
            "active files",
            "live task",
            "continuity",
        ),
    )

    include_skills = _contains_any(
        msg,
        (
            "skill",
            "procedural memory",
            "skill atlas",
            "repeatable procedure",
            "promotion to skill",
        ),
    )

    include_bootstrap = _contains_any(
        msg,
        (
            "bootstrap",
            "initialization",
            "migration",
            "reconstruction",
            "compiler support",
        ),
    )

    include_routing_indexes = _contains_any(
        msg,
        (
            "retrieve",
            "retrieval",
            "routing",
            "index",
            "context selection",
            "resident set",
            "prompt loading",
            "selective",
        ),
    )

    include_promotion = _contains_any(
        msg,
        (
            "promotion",
            "trace",
            "episode",
            "fact",
            "case",
            "doctrine",
            "compounding",
            "writeback",
        ),
    )

    include_observability = _contains_any(
        msg,
        (
            "trace",
            "observability",
            "regression",
            "failure mode",
            "evaluation",
            "run history",
            "postmortem",
        ),
    )

    include_semantic = _contains_any(
        msg,
        (
            "semantic",
            "stable fact",
            "entity",
            "relationship",
            "provenance",
            "supersession",
            "temporal validity",
            "knowledge graph",
        ),
    )

    include_cases = _contains_any(
        msg,
        (
            "case memory",
            "case",
            "pattern",
            "intervention",
            "analog",
            "analogical",
            "transfer condition",
            "playbook",
        ),
    )

    include_hazards = _contains_any(
        msg,
        (
            "hazard",
            "anti-pattern",
            "dangerous",
            "do not retry",
            "invalid assumption",
            "failure lesson",
            "unsafe",
        ),
    )

    include_prospective = _contains_any(
        msg,
        (
            "prospective",
            "commitment",
            "deadline",
            "reminder",
            "future action",
            "open loop",
            "follow-up",
            "pending",
        ),
    )

    include_social_roles = _contains_any(
        msg,
        (
            "social",
            "role",
            "persona",
            "authority",
            "delegation trust",
            "communication preference",
            "user model",
        ),
    )

    return RetrievalPlan(
        include_infrastructure=include_infra,
        include_state=include_state,
        include_skills=include_skills,
        include_bootstrap=include_bootstrap,
        include_routing_indexes=include_routing_indexes,
        include_promotion=include_promotion,
        include_observability=include_observability,
        include_semantic=include_semantic,
        include_cases=include_cases,
        include_hazards=include_hazards,
        include_prospective=include_prospective,
        include_social_roles=include_social_roles,
    )

