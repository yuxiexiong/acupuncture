#!/bin/sh
cd /workspace/acupuncture/experiments/capability-damage-v2-2026-10-26 || exit 2
export HF_HOME=/workspace/acupuncture/.cache/hf
export HF_HUB_DISABLE_XET=1
export HF_ENDPOINT=https://hf-mirror.com
date -u +%FT%TZ > prepare-r02.started
timeout 3600 /workspace/acupuncture/.venv-bench/bin/python -u prepare_tasks.py --harness /workspace/acupuncture/.runtime/lm-evaluation-harness --output . --cache-dir /workspace/acupuncture/.cache/hf/datasets --quick-items /workspace/claude-jump/qwen35-neuron-steering-20261025/benchmark-quick-2026-10-26/items.json --humaneval-data /workspace/acupuncture/.runtime/human-eval/data/HumanEval.jsonl.gz > prepare-r02.log 2>&1
prepare_code=$?
printf '%s\n' "$prepare_code" > prepare-r02.exit
date -u +%FT%TZ > prepare-r02.ended
exit "$prepare_code"
