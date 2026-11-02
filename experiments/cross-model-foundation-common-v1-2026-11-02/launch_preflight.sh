#!/bin/bash
# Run preflight (run + replay in a separate process) for a list of models on one GPU, sequentially.
# Usage: launch_preflight.sh <outroot> <cuda:N> <model_key> [<model_key> ...]
set -u
OUT=$1; DEV=$2; shift 2
mkdir -p "$OUT"
for m in "$@"; do
  echo "[$(date -u +%FT%TZ)] START $m on $DEV"
  python preflight.py run "$m" "$OUT/$m" "$DEV" > "$OUT/$m.run.log" 2>&1
  rc=$?
  echo "[$(date -u +%FT%TZ)] RUN_EXIT $m $rc"
  if [ $rc -eq 0 ]; then
    python preflight.py replay "$m" "$OUT/$m" "$DEV" > "$OUT/$m.replay.log" 2>&1
    echo "[$(date -u +%FT%TZ)] REPLAY_EXIT $m $?"
  fi
done
echo "[$(date -u +%FT%TZ)] ALL_DONE $DEV"
