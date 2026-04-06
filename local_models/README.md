# Local model weights (Hugging Face Hub)

Downloaded checkpoints live under `hub/` (gitignored). This directory keeps **only** tracked metadata (`manifest.yaml`, this file).

## Budget

The default Hermes tier list includes models that **cannot all fit** in 200GB at full precision. `scripts/local_models/download_models.py` queries Hugging Face for **total LFS size per repo**, then downloads in **ascending size order** until `budget_gb` would be exceeded. Repos that do not fit are listed in `logs/skipped_budget.json`.

## Gated models (e.g. Gemma)

Repos such as `google/gemma-3-27b-it` require a Hugging Face account that has accepted the license on the model page, plus a token:

```bash
export HF_TOKEN=hf_...   # or: huggingface-cli login
```

Without `HF_TOKEN`, those downloads fail with **401** (see `logs/failures.jsonl`). Re-run the script after exporting the token; it will resume other repos and retry failed ones.

## Downloads (resume + parallelism)

```bash
source venv/bin/activate
pip install 'huggingface_hub>=0.26' hf_transfer
export HF_HUB_ENABLE_HF_TRANSFER=1
python scripts/local_models/download_models.py --budget-gb 200 --max-workers 32
```

- **Resume**: `snapshot_download` always resumes partial files under `hub/`; safe to stop and re-run.
- **Speed**: `hf_transfer` + high `max_workers` for parallel file shards.
- **Logs**: `logs/download.log`, `logs/failures.jsonl`, `hub/state.json`.

## Sync to droplet (repo tree only)

```bash
./scripts/local_models/sync_to_droplet.sh
```

Requires the same `~/.env/.env` SSH variables as `scripts/core/droplet_run.sh`. Syncs **`local_models/hub/`** to `/home/hermesuser/hermes-agent/local_models/hub/` (no `~/.hermes`).

## Runtime wiring (local OpenAI server)

Hermes fallbacks use the Hugging Face hub id as the OpenAI `model` name. Run **vLLM**, **text-generation-inference**, or similar with `--served-model-name` matching the hub id (e.g. `google/gemma-3-27b-it`), then:

```bash
export HERMES_LOCAL_INFERENCE_BASE_URL=http://127.0.0.1:8000/v1
```

If `hub/state.json` lists a hub id as downloaded, the agent uses the local base URL for that fallback (see `run_agent.py` hook). Override list path with `HERMES_LOCAL_MODEL_STATE` if needed.

Google **Gemini / Gemma API** models are not served from this tree; keep using `GEMINI_API_KEY` for `optional_gemini` when applicable.
