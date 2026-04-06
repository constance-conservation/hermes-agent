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


def local_inference_override_for_hub_model(fb_model: str) -> Optional[Tuple[str, str]]:
    """If ``HERMES_LOCAL_INFERENCE_BASE_URL`` is set and *fb_model* is in download state, return (base_url, api_key)."""
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
    return b, key
