"""Hard budget operator approval gate (session-scoped)."""

from __future__ import annotations

import pytest

from agent.budget_ledger import (
    HARD_BUDGET_APPROVE_CHOICE,
    HARD_BUDGET_DENY_CHOICE,
    HardBudgetBlockedError,
)
from run_agent import AIAgent


def test_hard_budget_no_gate_when_not_exhausted(monkeypatch):
    a = object.__new__(AIAgent)
    a._hard_budget_operator_approval_required = True
    a._budget_ledger = None
    a._hard_budget_operator_decision = None
    a.clarify_callback = lambda q, c: (_ for _ in ()).throw(AssertionError("no prompt"))
    AIAgent._hard_budget_check_before_llm_call(a)  # no ledger → no-op


def test_hard_budget_blocks_without_callback_when_exhausted(monkeypatch):
    a = object.__new__(AIAgent)
    a._hard_budget_operator_approval_required = True

    class _Led:
        def is_daily_exhausted(self):
            return True

    a._budget_ledger = _Led()
    a._hard_budget_operator_decision = None
    a.clarify_callback = None
    with pytest.raises(HardBudgetBlockedError):
        AIAgent._hard_budget_check_before_llm_call(a)


def test_hard_budget_approve_via_clarify(monkeypatch):
    a = object.__new__(AIAgent)
    a._hard_budget_operator_approval_required = True

    class _Led:
        def is_daily_exhausted(self):
            return True

    a._budget_ledger = _Led()
    a._hard_budget_operator_decision = None

    def _cb(q, choices):
        assert HARD_BUDGET_APPROVE_CHOICE in choices
        return HARD_BUDGET_APPROVE_CHOICE

    a.clarify_callback = _cb
    AIAgent._hard_budget_check_before_llm_call(a)
    assert a._hard_budget_operator_decision == HARD_BUDGET_APPROVE_CHOICE
    AIAgent._hard_budget_check_before_llm_call(a)  # second call: no prompt


def test_hard_budget_deny_via_clarify(monkeypatch):
    a = object.__new__(AIAgent)
    a._hard_budget_operator_approval_required = True

    class _Led:
        def is_daily_exhausted(self):
            return True

    a._budget_ledger = _Led()
    a._hard_budget_operator_decision = None
    a.clarify_callback = lambda q, c: HARD_BUDGET_DENY_CHOICE
    with pytest.raises(HardBudgetBlockedError):
        AIAgent._hard_budget_check_before_llm_call(a)
    assert a._hard_budget_operator_decision == HARD_BUDGET_DENY_CHOICE
