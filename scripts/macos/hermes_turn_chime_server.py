#!/usr/bin/env python3
"""
Local HTTP listener on your Mac: play a system sound when Hermes on another host pings you.

Typical setup (Tailscale — no public ports):
  1. On Mac:  tailscale ip -4   → note 100.x.y.z
  2. Run:      ./hermes_turn_chime_server.py --bind 0.0.0.0 --port 8765
     (0.0.0.0 listens on all interfaces; use your Tailscale IP in the VPS URL)
  3. On VPS:   HERMES_TURN_DONE_NOTIFY_URL=http://100.x.y.z:8765/
     in ~/.hermes/.env (Hermes loads it; gateway/agent will GET this URL when a root turn completes)

Only devices on your tailnet can reach that IP. Optionally bind 127.0.0.1 and use
``ssh -R 8765:127.0.0.1:8765`` from Mac to VPS instead.

Uses a small TCP server (not stdlib HTTPServer) so remote Tailscale clients do not hit
macOS/socket edge cases with BaseHTTPRequestHandler.

Run this process in Terminal.app, iTerm, or launchd — not only inside an IDE-embedded terminal,
if your environment sandboxes inbound connections (localhost may work while tailnet peers get RST).

Default sound: /System/Library/Sounds/Funk.aiff (override with --sound or HERMES_TURN_DONE_SOUND).
"""
from __future__ import annotations

import argparse
import os
import socket
import socketserver
import subprocess
import sys
import threading

RESP_204 = b"HTTP/1.1 204 No Content\r\nConnection: close\r\n\r\n"


def _play(sound_path: str) -> None:
    subprocess.run(
        ["afplay", sound_path],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def _first_request_line(data: bytes) -> bytes:
    if not data:
        return b""
    head = data.split(b"\r\n", 1)[0]
    if b"\n" in head and b"\r\n" not in data[:200]:
        head = data.split(b"\n", 1)[0]
    return head.strip()


def _handle_client(conn: socket.socket, addr: tuple, sound_path: str) -> None:
    try:
        conn.settimeout(20.0)
        parts: list[bytes] = []
        total = 0
        while total < 65537:
            try:
                chunk = conn.recv(8192)
            except socket.timeout:
                break
            if not chunk:
                break
            parts.append(chunk)
            total += len(chunk)
            blob = b"".join(parts)
            if b"\r\n\r\n" in blob or b"\n\n" in blob:
                break
        data = b"".join(parts)
        line = _first_request_line(data)
        chime = bool(line.upper().startswith((b"GET ", b"POST ", b"HEAD ")))
        # Reply immediately so remote HTTP clients do not idle while afplay runs.
        try:
            conn.sendall(RESP_204)
        except OSError:
            pass
        try:
            conn.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        conn.close()
        if chime:
            threading.Thread(
                target=_play,
                args=(sound_path,),
                daemon=True,
            ).start()
    except Exception as exc:  # noqa: BLE001 — log any handler bug; keep serving
        sys.stderr.write("hermes_turn_chime_server: error %s:%s %s\n" % (addr[0], addr[1], exc))
        try:
            conn.close()
        except OSError:
            pass
        return
    sys.stderr.write("hermes_turn_chime_server: %s:%s\n" % (addr[0], addr[1]))


class _ThreadingTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True


def main() -> None:
    p = argparse.ArgumentParser(description="Play macOS sound when Hermes pings this URL.")
    p.add_argument(
        "--bind",
        default=os.environ.get("HERMES_TURN_CHIME_BIND", "127.0.0.1"),
        help="Listen address (0.0.0.0 + Tailscale URL is typical for VPS push).",
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

    sound_path = args.sound

    def _req(handler: socketserver.BaseRequestHandler) -> None:
        _handle_client(handler.request, handler.client_address, sound_path)

    class _H(socketserver.BaseRequestHandler):
        def handle(self) -> None:
            _req(self)

    server = _ThreadingTCPServer((args.bind, args.port), _H)
    print(
        f"Listening on http://{args.bind}:{args.port}/  (GET/POST → afplay {args.sound})\n"
        f"Set on VPS: HERMES_TURN_DONE_NOTIFY_URL=http://<this-host-tailscale-ip>:{args.port}/",
        file=sys.stderr,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.", file=sys.stderr)
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
