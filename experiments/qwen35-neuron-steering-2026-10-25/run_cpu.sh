#!/usr/bin/env bash
set -eu
# The user explicitly requires reviewing the plan and approving model execution.
if [[ "${1:-}" != "--approved-by-user" ]]; then
  echo "Model execution is blocked pending explicit user approval of the plan." >&2
  exit 2
fi
cd /workspace/claude-jump/qwen35-neuron-steering-20261025
trap 'printf "%s\n" "$?" > pipeline.exit' EXIT
export LD_LIBRARY_PATH="$PWD/download-tools/unpacked/usr/lib/x86_64-linux-gnu${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
timeout 3600 download-tools/unpacked/usr/bin/aria2c --no-conf=true \
  --input-file=weights-download.txt --dir=/data/models/Qwen3.5-4B-851bf6e \
  --max-concurrent-downloads=2 --split=4 --max-connection-per-server=4 \
  --min-split-size=32M --timeout=180 --connect-timeout=20 --max-tries=5 \
  --retry-wait=5 --continue=true --file-allocation=none --auto-file-renaming=false \
  --summary-interval=30 --download-result=full > download-r04.log 2>&1
timeout 600 .venv/bin/python verify_model.py /data/models/Qwen3.5-4B-851bf6e qwen35-files.json > verification.log 2>&1
.venv/bin/python test_probe.py > test.log 2>&1
export CUDA_VISIBLE_DEVICES="" HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 TOKENIZERS_PARALLELISM=false
timeout 3600 .venv/bin/python -u probe.py \
  --model /data/models/Qwen3.5-4B-851bf6e \
  --revision 851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a \
  --device cpu --dtype bfloat16 --threads 4 --max-tokens 96 \
  --output results-cpu-bf16-r01 > run.log 2>&1
