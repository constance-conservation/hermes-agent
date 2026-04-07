"""Optional local OpenAI-compatible server for HF hub model ids (vLLM / TGI / llama.cpp server)."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


def _default_state_path() -> Path:
    # agent/local_inference.py -> repo root
    return Path(__file__).resolve().parent.parent / "local_models" / "hub" / "state.json"


def load_local_hub_state() -> Optional[Dict[str, Any]]:
    p = os.environ.get("HERMES_LOCAL_MODEL_STATE", "").strip()
    path = Path(p) if p else _default_state_path()
    if not path.is_file():
        return None
    try:
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)
        return raw if isinstance(raw, dict) else None
    except Exception as exc:
        logger.debug("local_inference: could not read %s: %s", path, exc)
        return None


def downloaded_hub_repo_ids() -> Optional[set[str]]:
    """Return hub ids marked downloaded in ``state.json``, or None if unknown."""
    state = load_local_hub_state()
    if not state:
        return None
    raw = state.get("downloaded") or state.get("repos") or []
    if isinstance(raw, dict):
        ids = [str(k).strip() for k in raw if str(k).strip()]
    elif isinstance(raw, list):
        ids = [str(x).strip() for x in raw if str(x).strip()]
    else:
        return None
    if not ids:
        return None
    return set(ids)


def filter_hub_model_ids_by_local_state(
    model_ids: list[str],
    *,
    enabled: bool = True,
) -> list[str]:
    """Drop tier hub ids that are not present in local ``state.json`` when enabled.

    When ``local_models/hub/state.json`` is missing or has no ``downloaded`` entries,
    returns *model_ids* unchanged. If filtering would remove every id, returns the
    original list so the tier router still has candidates.
    """
    if not enabled or not model_ids:
        return list(model_ids)
    have = downloaded_hub_repo_ids()
    if not have:
        return list(model_ids)
    filtered = [m.strip() for m in model_ids if m and str(m).strip() in have]
    if not filtered:
        return list(model_ids)
    return filtered


def _resolve_served_model_path(hub_id: str, state: dict) -> str:
    """Return the best local path to use as the ``model`` field in API calls.

    Prefers a 4-bit quantized variant (``<path>-mlx-4bit``) when present,
    then the original BF16 path from state.json, then the hub id unchanged.
    """
    repos = state.get("repos") or {}
    entry = repos.get(hub_id) if isinstance(repos, dict) else None
    base_path: Optional[str] = None
    if isinstance(entry, dict):
        base_path = (entry.get("path") or "").strip() or None

    if not base_path:
        # Derive from hub id: Qwen/QwQ-32B -> local_models/hub/Qwen__QwQ-32B
        derived = hub_id.replace("/", "__")
        candidate = Path(__file__).resolve().parent.parent / "local_models" / "hub" / derived
        if candidate.is_dir():
            base_path = str(candidate)

    if base_path:
        quant_path = base_path + "-mlx-4bit"
        if Path(quant_path).is_dir():
            return quant_path
        if Path(base_path).is_dir():
            return base_path

    return hub_id  # fallback: let the server resolve it


def local_inference_override_for_hub_model(fb_model: str) -> Optional[Tuple[str, str, str]]:
    """If ``HERMES_LOCAL_INFERENCE_BASE_URL`` is set and *fb_model* is in download state,
    return ``(base_url, api_key, served_model_name)``.

    *served_model_name* is the local filesystem path to pass as the ``model``
    field in OpenAI-compatible API calls (avoids the server re-downloading the
    hub model).  Prefers the 4-bit quantized variant when present.
    """
    base = os.environ.get("HERMES_LOCAL_INFERENCE_BASE_URL", "").strip()
    if not base:
        return None
    mid = (fb_model or "").strip()
    if not mid:
        return None
    state = load_local_hub_state()
    if not state:
        return None
    downloaded = state.get("downloaded") or state.get("repos") or []
    if isinstance(downloaded, dict):
        downloaded = list(downloaded.keys())
    if not isinstance(downloaded, list):
        return None
    if mid not in downloaded:
        return None
    b = base.rstrip("/")
    if not b.endswith("/v1"):
        b = f"{b}/v1"
    key = os.environ.get("HERMES_LOCAL_INFERENCE_API_KEY", "dummy-local").strip() or "dummy-local"
    served_name = _resolve_served_model_path(mid, state)
    return b, key, served_name
