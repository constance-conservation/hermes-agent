#!/usr/bin/env bash
set -euo pipefail

echo "Restart governance runtime using your target execution mode."
echo
echo "CLI:"
echo "  hermes tui"
echo
echo "Gateway (profile-aware):"
echo "  ./venv/bin/python -m hermes_cli.main -p chief-orchestrator gateway restart"
echo
echo "Verify:"
echo "  ./venv/bin/python -m hermes_cli.main -p chief-orchestrator gateway watchdog-check"
