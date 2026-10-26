#!/usr/bin/env bash
set -euo pipefail
cd /workspace/acupuncture/experiments/root-cause-toy-v1-2026-10-26
trap 'status=$?; printf "%s\n" "$status" > runs/root-r01/pipeline-r01.exit' EXIT

# Do not start a second worker or take an occupied GPU.
test ! -e runs/root-r01/decompose-r01
gpu_state=$(nvidia-smi -i 0 --query-gpu=memory.used,utilization.gpu --format=csv,noheader,nounits)
test "$(printf '%s' "$gpu_state" | tr -d ' ')" = '0,0'
date -u +%Y-%m-%dT%H:%M:%SZ > runs/root-r01/pipeline-r01.started
export CUDA_VISIBLE_DEVICES=0
runner=(/workspace/acupuncture/.venv-bench/bin/python run_root.py --execute
  --launch-authorization launch-authorization-20261026.json
  --model /data/models/Qwen3.5-4B-851bf6e --device cuda:0
  --prior runs/root-r01/preflight-r01/receipt.json)

"${runner[@]}" --stage decompose --output runs/root-r01/decompose-r01 \
  > runs/root-r01/decompose-r01.log 2>&1
"${runner[@]}" --stage rank --output runs/root-r01/rank-r01 \
  --prior runs/root-r01/decompose-r01/receipt.json > runs/root-r01/rank-r01.log 2>&1
"${runner[@]}" --stage validate --output runs/root-r01/validate-r01 \
  --prior runs/root-r01/rank-r01/receipt.json > runs/root-r01/validate-r01.log 2>&1
