"""
Pre-LLM JSON state fingerprint for cron jobs.

When a job defines ``state_skip_gate`` (path + keys), ``tick()`` hashes those keys
from the state file and skips ``run_job`` / the provider if the digest matches
``last_state_gate_fingerprint`` from the previous successful observation.

Use semantic keys only (e.g. ``last_status_key``, ``connected_platforms``) — not
volatile fields like ``last_sent_message_hash`` or run timestamps, or you will
never skip after a send.
"""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


def _gate_spec(job: dict) -> Optional[dict]:
    g = job.get("state_skip_gate")
    if not isinstance(g, dict):
        return None
    if g.get("enabled") is False:
        return None
    return g


def fingerprint_for_state_skip_gate(job: dict) -> Optional[str]:
    """
    SHA-256 hex of a canonical JSON object built from *keys* in the state file.

    Returns None if the gate is off, misconfigured, or the file cannot be read as JSON
    (caller should run the LLM — fail open except for stable missing-file sentinel).
    """
    g = _gate_spec(job)
    if not g:
        return None
    path = g.get("path")
    keys = g.get("keys")
    if not path or not isinstance(path, str):
        logger.warning("Job '%s': state_skip_gate.path missing or invalid", job.get("id", "?"))
        return None
    if not isinstance(keys, list) or not keys:
        logger.warning("Job '%s': state_skip_gate.keys must be a non-empty list", job.get("id", "?"))
        return None
    key_list = sorted({str(k).strip() for k in keys if str(k).strip()})
    if not key_list:
        return None

    p = Path(path).expanduser()
    if not p.is_file():
        blob = json.dumps({"__state_file__": "<missing>"}, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()

    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError) as e:
        logger.warning("Job '%s': cannot read state file %s: %s", job.get("id", "?"), p, e)
        return None
    except json.JSONDecodeError as e:
        logger.warning("Job '%s': invalid JSON in state file %s: %s", job.get("id", "?"), p, e)
        return None

    if not isinstance(data, dict):
        logger.warning("Job '%s': state file root must be a JSON object", job.get("id", "?"))
        return None

    subset: dict[str, Any] = {k: data.get(k) for k in key_list}
    blob = json.dumps(subset, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def should_skip_llm_for_unchanged_state(job: dict) -> tuple[bool, Optional[str]]:
    """
    Return (skip_llm, current_fingerprint).

    *skip_llm* is True when the gate is active, the current fingerprint is known,
    and it equals *last_state_gate_fingerprint* (previous run stored it).

    *current_fingerprint* is the digest just computed, or None if the gate is off
    or fingerprinting failed (run LLM).
    """
    if not _gate_spec(job):
        return False, None
    cur = fingerprint_for_state_skip_gate(job)
    if cur is None:
        return False, None
    prev = job.get("last_state_gate_fingerprint")
    if prev is None:
        return False, cur
    if prev == cur:
        return True, cur
    return False, cur
