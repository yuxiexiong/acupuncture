#!/usr/bin/env bash
cd /workspace/acupuncture/experiments/capability-damage-v2-2026-10-26 || exit 1
date -u +%FT%TZ > prepare-r03-offline.started
HF_HOME=/workspace/acupuncture/.cache/hf HF_ENDPOINT=https://hf-mirror.com HF_HUB_DISABLE_XET=1 HF_HUB_OFFLINE=1 HF_DATASETS_OFFLINE=1 timeout 600 /workspace/acupuncture/.venv-bench/bin/python -u prepare_tasks.py --harness /workspace/acupuncture/.runtime/lm-evaluation-harness --output . --cache-dir /workspace/acupuncture/.cache/hf/datasets --quick-items /workspace/claude-jump/qwen35-neuron-steering-20261025/benchmark-quick-2026-10-26/items.json --humaneval-data /workspace/acupuncture/.runtime/human-eval/data/HumanEval.jsonl.gz > prepare-r03-offline.log 2>&1
result=$?
printf '%s\n' "$result" > prepare-r03-offline.exit
date -u +%FT%TZ > prepare-r03-offline.ended
exit "$result"
