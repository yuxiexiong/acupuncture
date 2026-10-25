#!/usr/bin/env bash
set -eu
cd /workspace/claude-jump/qwen35-neuron-steering-20261025
# Authorized by the user's 2026-10-25 approval, for the raw 40-question pair only.
trap 'printf "%s\n" "$?" > raw40.exit' EXIT
export CUDA_VISIBLE_DEVICES="" HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 TOKENIZERS_PARALLELISM=false
.venv/bin/python test_probe.py > raw40-tests.log 2>&1
.venv/bin/python test_collect_raw.py >> raw40-tests.log 2>&1
.venv/bin/python -u collect_raw.py \
  --model /data/models/Qwen3.5-4B-851bf6e \
  --device cpu \
  --output raw-corpus-cpu-bf16-r01 > raw40-run.log 2>&1
