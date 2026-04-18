from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

_MAX_TRACE_FILE_BYTES = 5 * 1024 * 1024
_MAX_TRACE_FILE_LINES = 10000


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _append_jsonl(path: Path, obj: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(obj, ensure_ascii=False)
    # Atomic-ish append: write to temp then append to target to reduce partial writes.
    with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8", dir=str(path.parent)) as tf:
        tf.write(line + "\n")
        tmp_name = tf.name
    with open(path, "a", encoding="utf-8") as out:
        with open(tmp_name, "r", encoding="utf-8") as inp:
            out.write(inp.read())
    try:
        os.unlink(tmp_name)
    except OSError:
        pass


def _workspace_memory_root(hermes_home: Path) -> Path:
    return hermes_home / "workspace" / "memory"


def extract_tool_names_from_messages(messages: list[dict[str, Any]]) -> list[str]:
    names: list[str] = []
    for msg in messages:
        if msg.get("role") == "assistant":
            for tc in msg.get("tool_calls") or []:
                try:
                    fn = (tc or {}).get("function") or {}
                    n = fn.get("name")
                    if n:
                        names.append(str(n))
                except Exception:
                    continue
    # Stable unique preserving order
    return list(dict.fromkeys(names))


def _line_count(path: Path) -> int:
    try:
        with path.open("r", encoding="utf-8") as f:
            return sum(1 for _ in f)
    except Exception:
        return 0


def _rotate_if_needed(path: Path) -> None:
    """Best-effort rotation to bound trace growth in long-running environments."""
    try:
        if not path.exists():
            return
        size_ok = path.stat().st_size <= _MAX_TRACE_FILE_BYTES
        lines_ok = _line_count(path) <= _MAX_TRACE_FILE_LINES
        if size_ok and lines_ok:
            return
        archive = path.with_name(f"{path.stem}.{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}{path.suffix}")
        path.rename(archive)
    except Exception:
        # Non-fatal; append should still proceed.
        return


def append_trace(
    *,
    hermes_home: Path,
    session_id: str,
    user_message: str,
    assistant_response: str,
    model: str | None,
    provider: str | None,
    tool_names: Iterable[str],
    completed: bool,
) -> None:
    """Append a minimal per-turn trace into `episodic-ledger/`.

    This is intentionally lightweight: it preserves causal chronology and provenance
    without bloating always-loaded memory.
    """
    mem_root = _workspace_memory_root(hermes_home)
    if not mem_root.is_dir():
        return

    trace_path = mem_root / "episodic-ledger" / "traces" / "turn-traces.jsonl"
    _rotate_if_needed(trace_path)
    obj = {
        "type": "trace",
        "observed_at": _utc_now_iso(),
        "session_id": session_id,
        "model": model or "",
        "provider": provider or "",
        "completed": bool(completed),
        "tools_used": list(tool_names),
        "user_message": (user_message or "")[:12000],
        "assistant_response": (assistant_response or "")[:12000],
    }
    _append_jsonl(trace_path, obj)

