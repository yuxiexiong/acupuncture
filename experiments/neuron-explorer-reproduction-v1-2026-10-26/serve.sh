#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/upstream"
export EXPLORER_MODEL="${EXPLORER_MODEL:-/data/models/Qwen3.5-4B-851bf6e}"
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"
export PORT="${PORT:-8791}"
export HF_HUB_OFFLINE=1 HF_DATASETS_OFFLINE=1 TOKENIZERS_PARALLELISM=false
for file in layout_writes.npz connections.npz lens_index.npz steer_index.npz act_scale.npz vocab.json; do
    test -f "explorer/cache/$file" || { echo "Missing original cache: $file" >&2; exit 1; }
done
test -f "$EXPLORER_MODEL/config.json" || { echo "Model directory is unavailable: $EXPLORER_MODEL" >&2; exit 1; }
exec "${EXPLORER_PYTHON:-/workspace/acupuncture/.venv-bench/bin/python}" explorer/server.py
