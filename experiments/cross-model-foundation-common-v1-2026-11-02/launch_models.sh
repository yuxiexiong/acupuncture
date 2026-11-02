#!/bin/bash
# Run one python step for several models sequentially on one GPU.
# Usage: launch_models.sh <logdir> <cuda:N> "<python args with MODEL placeholder>" <model_key>...
# Example: launch_models.sh runs/f1-path cuda:0 "path_check.py MODEL runs/preflight-r02/MODEL runs/f1-path/MODEL cuda:0" llama32_3b
set -u
LOG=$1; DEV=$2; ARGS=$3; shift 3
mkdir -p "$LOG"
for m in "$@"; do
  a=${ARGS//MODEL/$m}
  echo "[$(date -u +%FT%TZ)] START $m on $DEV: $a"
  python $a > "$LOG/$m.log" 2>&1
  rc=$?
  echo "[$(date -u +%FT%TZ)] EXIT $m $rc"
done
echo "[$(date -u +%FT%TZ)] ALL_DONE $DEV"
