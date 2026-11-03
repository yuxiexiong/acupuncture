#!/bin/sh
set -eu
wsp_root=/workspace/acupuncture/external/wsp
export CUDA_HOME=/workspace/acupuncture/.venv-wsp/lib/python3.11/site-packages/nvidia/cu13
export PATH=/workspace/acupuncture/.venv-wsp/bin:$CUDA_HOME/bin:$PATH
export LD_LIBRARY_PATH=$wsp_root/tools/cuda-compat-local/usr/local/cuda-13.4/compat:$CUDA_HOME/lib
export LIBRARY_PATH=$wsp_root/tools/cuda-link-lib
export FLASHINFER_CUDA_ARCH_LIST=9.0a
export FLASHINFER_WORKSPACE_BASE=$wsp_root/flashinfer-cache
export MAX_JOBS=4 HF_HUB_OFFLINE=1 VLLM_WORKER_MULTIPROC_METHOD=spawn OMP_NUM_THREADS=8
export VLLM_CACHE_ROOT=$wsp_root/vllm-cache
unset CUDA_VISIBLE_DEVICES
exec /workspace/acupuncture/.venv-wsp/bin/python "$@"
