#!/usr/bin/env bash
set -u
cd /workspace/claude-jump/qwen35-neuron-steering-20261025
task_dir=benchmark-quick-2026-10-26
test ! -e "$task_dir/math-run.log" || exit 3
test ! -e "$task_dir/results-math" || exit 3
gpu_used=$(nvidia-smi -i 1 --query-gpu=memory.used --format=csv,noheader,nounits) || exit 4
test "$gpu_used" -lt 1024 || exit 4
printf '%s\n' "$$" > "$task_dir/math-launcher.pid"
export CUBLAS_WORKSPACE_CONFIG=:4096:8
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export PYTHONUNBUFFERED=1
timeout 3600 .venv/bin/python benchmark_quick_batched.py \
  --model /data/models/Qwen3.5-4B-851bf6e \
  --items "$task_dir/items-math.json" --output "$task_dir/results-math" \
  --device cuda:1 --batch-size 16 --gsm-tokens 512 \
  > "$task_dir/math-run.log" 2>&1
run_code=$?
printf '%s\n' "$run_code" > "$task_dir/math.exit"
exit "$run_code"
