"""
Optional notification when a root agent turn completes (e.g. HTTP GET to a Mac listener).

Set on the machine that runs Hermes (e.g. droplet ``~/.hermes/.env``)::

    HERMES_TURN_DONE_NOTIFY_URL=http://100.x.y.z:8765/

where ``100.x.y.z`` is your Mac's Tailscale IP and a tiny local server plays a sound.
Outbound-only from VPS — no open ports on the server.

Does not run for delegate/subagent ``run_conversation`` completions (``_delegate_depth`` > 0).
"""

from __future__ import annotations

import logging
import os
import threading
import urllib.error
import urllib.request

logger = logging.getLogger(__name__)


def maybe_notify_turn_done(
    *,
    agent: object,
    final_response: object,
    interrupted: bool,
) -> None:
    """Fire-and-forget GET to ``HERMES_TURN_DONE_NOTIFY_URL`` if configured."""
    if interrupted:
        return
    if not final_response:
        return
    if getattr(agent, "_delegate_depth", 0) != 0:
        return

    url = (os.getenv("HERMES_TURN_DONE_NOTIFY_URL") or "").strip()
    if not url:
        return

    def _run() -> None:
        try:
            with urllib.request.urlopen(url, timeout=2.5) as resp:
                resp.read()
        except urllib.error.HTTPError as e:
            logger.debug("turn_done_notify HTTP %s: %s", e.code, e.reason)
        except Exception:
            logger.debug("turn_done_notify failed", exc_info=True)

    threading.Thread(target=_run, daemon=True, name="hermes-turn-done-notify").start()
