#!/usr/bin/env bash
# Serve locally-downloaded models via an OpenAI-compatible HTTP server.
#
# Platform selection:
#   macOS (Apple Silicon) → mlx_lm.server  (pip install mlx-lm)
#   Linux with NVIDIA GPU → vllm            (pip install vllm)
#   Linux CPU-only        → vllm --device cpu  (slow)
#
# Usage:
#   ./scripts/local_models/serve_local_models.sh [--model <hub_id>] [--port <N>]
#
# Default model: Qwen/QwQ-32B
#   - Prefers quantized 4-bit version: local_models/hub/Qwen__QwQ-32B-mlx-4bit
#   - Falls back to BF16:              local_models/hub/Qwen__QwQ-32B
# Default port: 8000
#
# Hermes config (profile .env):
#   HERMES_LOCAL_INFERENCE_BASE_URL=http://localhost:8000
#   HERMES_LOCAL_INFERENCE_API_KEY=dummy-local   # optional
#
# To quantize the model first (recommended, ~18GB vs 64GB):
#   ./venv/bin/python -m mlx_lm convert \
#     --hf-path local_models/hub/Qwen__QwQ-32B \
#     --mlx-path local_models/hub/Qwen__QwQ-32B-mlx-4bit \
#     --quantize --q-bits 4
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
HUB_DIR="$REPO_ROOT/local_models/hub"
STATE_JSON="$HUB_DIR/state.json"

# ── Defaults ──────────────────────────────────────────────────────────────────
MODEL_HUB_ID="${HERMES_SERVE_MODEL:-Qwen/QwQ-32B}"
PORT="${HERMES_SERVE_PORT:-8000}"
GPU_UTIL="${HERMES_SERVE_GPU_UTIL:-0.90}"        # vLLM only
MAX_MODEL_LEN="${HERMES_SERVE_MAX_MODEL_LEN:-}"  # vLLM only, empty = default

# ── Parse flags ───────────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    --model)         MODEL_HUB_ID="$2"; shift 2 ;;
    --port)          PORT="$2"; shift 2 ;;
    --gpu-memory-util) GPU_UTIL="$2"; shift 2 ;;
    --max-model-len) MAX_MODEL_LEN="$2"; shift 2 ;;
    *) echo "Unknown arg: $1" >&2; exit 1 ;;
  esac
done

# ── Activate venv if available ────────────────────────────────────────────────
if [[ -f "$REPO_ROOT/venv/bin/activate" ]]; then
  # shellcheck source=/dev/null
  source "$REPO_ROOT/venv/bin/activate"
fi

# ── Detect platform ───────────────────────────────────────────────────────────
OS="$(uname -s)"
USE_MLX=false
if [[ "$OS" == "Darwin" ]]; then
  # Apple Silicon: prefer mlx_lm
  if python -c "import mlx_lm" 2>/dev/null; then
    USE_MLX=true
  else
    echo "mlx-lm not installed. Run: pip install mlx-lm" >&2
    exit 1
  fi
fi

# ── Resolve local model path ──────────────────────────────────────────────────
DERIVED_BASE="${MODEL_HUB_ID//\//__}"

# Prefer 4-bit MLX-quantized version when it exists
QUANT_PATH="$HUB_DIR/${DERIVED_BASE}-mlx-4bit"
BF16_PATH=""

# Try state.json first for the BF16 path
if [[ -f "$STATE_JSON" ]]; then
  BF16_PATH="$(python - <<PYEOF
import json
with open("$STATE_JSON") as f:
    s = json.load(f)
entry = s.get("repos", {}).get("$MODEL_HUB_ID")
if entry and entry.get("path"):
    print(entry["path"])
PYEOF
  )"
fi
[[ -z "$BF16_PATH" && -d "$HUB_DIR/$DERIVED_BASE" ]] && BF16_PATH="$HUB_DIR/$DERIVED_BASE"

if [[ -d "$QUANT_PATH" ]]; then
  MODEL_PATH="$QUANT_PATH"
  echo "==> Using 4-bit quantized model: $QUANT_PATH"
elif [[ -n "$BF16_PATH" && -d "$BF16_PATH" ]]; then
  MODEL_PATH="$BF16_PATH"
  echo "==> Using BF16 model: $BF16_PATH"
  if $USE_MLX; then
    echo "    Tip: quantize to 4-bit first for ~4x lower memory usage:"
    echo "    python -m mlx_lm convert --hf-path $BF16_PATH --mlx-path ${QUANT_PATH} -q --q-bits 4"
  fi
else
  echo "ERROR: Model not found locally for hub id '$MODEL_HUB_ID'." >&2
  echo "  Run: python scripts/local_models/download_models.py --skip-size-check --max-workers 2" >&2
  exit 1
fi

echo "    Port: $PORT"
echo ""

# ── Start server ──────────────────────────────────────────────────────────────
if $USE_MLX; then
  echo "Starting mlx_lm.server (Apple Silicon, OpenAI-compatible)…"
  exec python -m mlx_lm server \
    --model "$MODEL_PATH" \
    --host "0.0.0.0" \
    --port "$PORT"
else
  # Linux: vLLM
  VLLM_CMD=(
    python -m vllm.entrypoints.openai.api_server
    --model "$MODEL_PATH"
    --served-model-name "$MODEL_HUB_ID"
    --host "0.0.0.0"
    --port "$PORT"
    --trust-remote-code
    --gpu-memory-utilization "$GPU_UTIL"
  )
  [[ -n "$MAX_MODEL_LEN" ]] && VLLM_CMD+=(--max-model-len "$MAX_MODEL_LEN")
  if ! python -c "import torch; assert torch.cuda.is_available()" 2>/dev/null; then
    echo "No CUDA GPU detected — adding --device cpu (inference will be slow)."
    VLLM_CMD+=(--device cpu)
  fi
  echo "Starting vLLM server…"
  exec "${VLLM_CMD[@]}"
fi
