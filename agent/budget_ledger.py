"""Persistent calendar-day spend tracking in USD (for API estimates), display in AUD.

Driven by ``routing_canon`` ``hard_budget`` (see ``agent/dynamic_routing_canon.yaml``).
State file: ``${HERMES_HOME}/workspace/operations/daily_budget_state.json``.
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

STATE_NAME = "daily_budget_state.json"


def _local_today() -> str:
    return date.today().isoformat()


def hours_until_local_midnight() -> float:
    """Hours from now until next local midnight (0–24)."""
    now = datetime.now().astimezone()
    nxt = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    return max(0.0, (nxt - now).total_seconds() / 3600.0)


def _state_path() -> Path:
    from hermes_constants import get_hermes_home

    d = get_hermes_home() / "workspace" / "operations"
    d.mkdir(parents=True, exist_ok=True)
    return d / STATE_NAME


@dataclass
class BudgetSnapshot:
    daily_budget_aud: float
    spent_usd_today: float
    spent_aud_today: float
    daily_cap_usd: float
    hours_to_reset: float
    turn_cost_usd: float
    enabled: bool


class BudgetLedger:
    """Tracks cumulative USD spend for the local calendar day."""

    def __init__(
        self,
        *,
        daily_budget_aud: float,
        aud_to_usd: float,
        path: Optional[Path] = None,
    ):
        self.daily_budget_aud = max(0.01, float(daily_budget_aud))
        self.aud_to_usd = max(1e-9, float(aud_to_usd))
        self.daily_cap_usd = self.daily_budget_aud * self.aud_to_usd
        self._path = path or _state_path()
        self._spent_today = 0.0
        self._loaded_date = ""
        self._load_or_roll()

    def _load_or_roll(self) -> None:
        today = _local_today()
        if not self._path.is_file():
            self._spent_today = 0.0
            self._loaded_date = today
            self._persist_unlocked()
            return
        try:
            with open(self._path, encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            logger.debug("budget_ledger: read failed %s: %s", self._path, e)
            self._spent_today = 0.0
            self._loaded_date = today
            self._persist_unlocked()
            return
        if not isinstance(data, dict):
            data = {}
        file_date = str(data.get("date") or "")
        if file_date != today:
            self._spent_today = 0.0
            self._loaded_date = today
            self._persist_unlocked()
            return
        try:
            self._spent_today = max(0.0, float(data.get("spent_usd") or 0.0))
        except (TypeError, ValueError):
            self._spent_today = 0.0
        self._loaded_date = today

    def _persist_unlocked(self) -> None:
        payload = {
            "date": self._loaded_date or _local_today(),
            "spent_usd": round(self._spent_today, 6),
            "daily_budget_aud": self.daily_budget_aud,
            "aud_to_usd": self.aud_to_usd,
        }
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            fd, tmp = tempfile.mkstemp(
                dir=str(self._path.parent), prefix=".daily_budget_", suffix=".tmp"
            )
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    json.dump(payload, f, indent=0)
                    f.write("\n")
                Path(tmp).replace(self._path)
            except Exception:
                try:
                    os.unlink(tmp)
                except OSError:
                    pass
                raise
        except Exception as e:
            logger.debug("budget_ledger: persist failed: %s", e)

    def refresh_if_new_day(self) -> None:
        if _local_today() != self._loaded_date:
            self._load_or_roll()

    def add_spend_usd(self, delta_usd: float) -> None:
        if delta_usd <= 0:
            return
        today = _local_today()
        try:
            import fcntl  # type: ignore
        except ImportError:
            fcntl = None  # type: ignore
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            self._path.touch(exist_ok=True)
            with open(self._path, "r+", encoding="utf-8") as f:
                if fcntl is not None:
                    try:
                        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                    except OSError:
                        pass
                try:
                    raw = (f.read() or "").strip()
                    data: Dict[str, Any] = {}
                    if raw:
                        try:
                            data = json.loads(raw)
                        except json.JSONDecodeError:
                            data = {}
                    file_date = str(data.get("date") or "")
                    spent = 0.0
                    if file_date == today:
                        try:
                            spent = max(0.0, float(data.get("spent_usd") or 0.0))
                        except (TypeError, ValueError):
                            spent = 0.0
                    spent += float(delta_usd)
                    self._spent_today = spent
                    self._loaded_date = today
                    payload = {
                        "date": today,
                        "spent_usd": round(spent, 6),
                        "daily_budget_aud": self.daily_budget_aud,
                        "aud_to_usd": self.aud_to_usd,
                    }
                    f.seek(0)
                    f.truncate()
                    json.dump(payload, f, indent=0)
                    f.write("\n")
                    f.flush()
                finally:
                    if fcntl is not None:
                        try:
                            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                        except OSError:
                            pass
        except Exception as e:
            logger.debug("budget_ledger: add_spend failed: %s", e)
            self.refresh_if_new_day()
            self._spent_today += float(delta_usd)
            self._persist_unlocked()

    @property
    def spent_usd_today(self) -> float:
        self.refresh_if_new_day()
        return self._spent_today

    def spent_aud_today(self) -> float:
        return self.spent_usd_today / self.aud_to_usd

    def is_daily_exhausted(self) -> bool:
        return self.spent_usd_today >= self.daily_cap_usd

    def snapshot(
        self,
        *,
        turn_cost_usd: float = 0.0,
        enabled: bool = True,
    ) -> BudgetSnapshot:
        self.refresh_if_new_day()
        su = self.spent_usd_today
        return BudgetSnapshot(
            daily_budget_aud=self.daily_budget_aud,
            spent_usd_today=su,
            spent_aud_today=su / self.aud_to_usd,
            daily_cap_usd=self.daily_cap_usd,
            hours_to_reset=hours_until_local_midnight(),
            turn_cost_usd=max(0.0, float(turn_cost_usd)),
            enabled=enabled,
        )


def format_budget_bar_text(snap: BudgetSnapshot, *, max_width: int = 120) -> str:
    if not snap.enabled:
        return ""
    h = snap.hours_to_reset
    h_int = int(h)
    m_int = int((h - h_int) * 60)
    line = (
        f"💳 turn ~${snap.turn_cost_usd:.3f} │ "
        f"daily {snap.spent_aud_today:.2f}/{snap.daily_budget_aud:.2f} AUD "
        f"(${snap.spent_usd_today:.2f}/${snap.daily_cap_usd:.2f}) │ "
        f"reset in {h_int}h{m_int:02d}m"
    )
    if len(line) > max_width:
        line = line[: max(0, max_width - 1)] + "…"
    return line
