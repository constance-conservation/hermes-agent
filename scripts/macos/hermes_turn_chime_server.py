#!/usr/bin/env python3
"""
Local HTTP listener on your Mac: play a system sound when Hermes on another host pings you.

Typical setup (Tailscale — no public ports):
  1. On Mac:  tailscale ip -4   → note 100.x.y.z
  2. Run:      ./hermes_turn_chime_server.py --bind 100.x.y.z --port 8765
  3. On VPS:   HERMES_TURN_DONE_NOTIFY_URL=http://100.x.y.z:8765/
     in ~/.hermes/.env (Hermes loads it; gateway/agent will GET this URL when a root turn completes)

Only devices on your tailnet can reach that IP. Optionally bind 127.0.0.1 and use
``ssh -R 8765:127.0.0.1:8765`` from Mac to VPS instead.

Default sound: /System/Library/Sounds/Funk.aiff (override with --sound or HERMES_TURN_DONE_SOUND).
"""
from __future__ import annotations

import argparse
import http.server
import os
import subprocess
import sys


def _play(sound_path: str) -> None:
    subprocess.run(
        ["afplay", sound_path],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


class _Handler(http.server.BaseHTTPRequestHandler):
    sound_path: str = "/System/Library/Sounds/Funk.aiff"

    def do_GET(self) -> None:  # noqa: N802
        _play(self.sound_path)
        self.send_response(204)
        self.end_headers()

    def do_POST(self) -> None:  # noqa: N802
        _play(self.sound_path)
        self.send_response(204)
        self.end_headers()

    def log_message(self, format: str, *args) -> None:  # noqa: A002
        sys.stderr.write(
            "hermes_turn_chime_server: %s - %s\n" % (self.address_string(), self.path)
        )


def main() -> None:
    p = argparse.ArgumentParser(description="Play macOS sound when Hermes pings this URL.")
    p.add_argument(
        "--bind",
        default=os.environ.get("HERMES_TURN_CHIME_BIND", "127.0.0.1"),
        help="Listen address (use your `tailscale ip -4` for VPS push over tailnet).",
    )
    p.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("HERMES_TURN_CHIME_PORT", "8765")),
    )
    p.add_argument(
        "--sound",
        default=os.environ.get(
            "HERMES_TURN_DONE_SOUND",
            "/System/Library/Sounds/Funk.aiff",
        ),
        help="Path to .aiff / audio file for afplay.",
    )
    args = p.parse_args()
    if not os.path.isfile(args.sound):
        print(f"Sound not found: {args.sound}", file=sys.stderr)
        sys.exit(1)
    _Handler.sound_path = args.sound
    server = http.server.HTTPServer((args.bind, args.port), _Handler)
    print(
        f"Listening on http://{args.bind}:{args.port}/  (GET/POST → afplay {args.sound})\n"
        f"Set on VPS: HERMES_TURN_DONE_NOTIFY_URL=http://<this-host-tailscale-ip>:{args.port}/",
        file=sys.stderr,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.", file=sys.stderr)


if __name__ == "__main__":
    main()
