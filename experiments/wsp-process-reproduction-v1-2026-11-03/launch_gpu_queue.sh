#!/bin/sh
set -eu
wsp_root=/workspace/acupuncture/external/wsp
wsp_python=/workspace/acupuncture/.venv-wsp/bin/python
"$wsp_python" -c 'import json; assert json.load(open("/workspace/acupuncture/external/wsp/compile-sampling-r3.json"))["status"] == "compiled_and_loaded_no_gpu"'
export CUDA_VISIBLE_DEVICES=1
export CUDA_HOME=/workspace/acupuncture/.venv-wsp/lib/python3.11/site-packages/nvidia/cu13
export PATH=/workspace/acupuncture/.venv-wsp/bin:$CUDA_HOME/bin:$PATH
export LD_LIBRARY_PATH=$wsp_root/tools/cuda-compat-local/usr/local/cuda-13.4/compat:$CUDA_HOME/lib
export LIBRARY_PATH=$wsp_root/tools/cuda-link-lib
export FLASHINFER_CUDA_ARCH_LIST=9.0a
export FLASHINFER_WORKSPACE_BASE=$wsp_root/flashinfer-cache
export MAX_JOBS=4
export HF_HUB_OFFLINE=1
export VLLM_WORKER_MULTIPROC_METHOD=spawn
export VLLM_CACHE_ROOT=$wsp_root/vllm-cache
export OMP_NUM_THREADS=8
exec "$wsp_python" "$wsp_root/tools/queue_gpu_probe.py" \
  --root "$wsp_root" --python "$wsp_python" \
  --probe "$wsp_root/tools/gpu_generation_probe.py" --out "$wsp_root/preflight-queue-r1"
