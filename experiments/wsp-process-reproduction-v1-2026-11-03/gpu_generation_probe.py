"""Bounded engineering smoke test; outputs are observer-only, never search evidence."""
import argparse
import hashlib
import json
import os
import subprocess
import time
import traceback
from pathlib import Path


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--model", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--physical-gpu", type=int, default=1)
    args = p.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    started = time.time()
    receipt = {"status": "running", "started_unix": started, "model": str(args.model),
               "physical_gpu": args.physical_gpu, "purpose": "engineering only; not a benchmark or search pass",
               "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               "launch_environment": {k: os.environ.get(k) for k in ("CUDA_VISIBLE_DEVICES", "CUDA_HOME", "LIBRARY_PATH", "LD_LIBRARY_PATH", "FLASHINFER_WORKSPACE_BASE", "FLASHINFER_CUDA_ARCH_LIST", "HF_HUB_OFFLINE", "VLLM_WORKER_MULTIPROC_METHOD", "VLLM_CACHE_ROOT", "OMP_NUM_THREADS")},
               "runs": []}

    def flush():
        (args.out / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")

    flush()
    try:
        assert os.environ.get("CUDA_VISIBLE_DEVICES") == str(args.physical_gpu)
        used = int(subprocess.check_output(["nvidia-smi", f"--id={args.physical_gpu}",
                   "--query-gpu=memory.used", "--format=csv,noheader,nounits"], text=True).strip())
        if used >= 128:
            raise RuntimeError("Selected GPU occupied: postpone rather than share")
        from transformers import AutoTokenizer
        from vllm import LLM, SamplingParams
        tokenizer = AutoTokenizer.from_pretrained(args.model, local_files_only=True, trust_remote_code=False)
        receipt["tokenizer_class"] = type(tokenizer).__name__
        receipt["tokenizer_backend_sha256"] = hashlib.sha256(tokenizer.backend_tokenizer.to_str().encode()).hexdigest()
        engine_args = dict(model=str(args.model), tokenizer=str(args.model), dtype="bfloat16",
                           trust_remote_code=False, tensor_parallel_size=1, gpu_memory_utilization=0.5,
                           max_model_len=65536, max_num_batched_tokens=4096, max_num_seqs=8,
                           enforce_eager=True, enable_prefix_caching=False, seed=1729)
        receipt.update(engine_args=engine_args, stage="engine_initialization")
        flush()
        llm = LLM(**engine_args)
        receipt["initialization_seconds"] = time.time() - started
        fixtures = ["What is 2 + 3?", "Solve for x: 3x + 4 = 19."]
        prompts = []
        for problem in fixtures:
            messages = [{"role": "user", "content": problem + "\nPlease reason step by step, and put your final answer within \\boxed{}."}]
            ids = tokenizer.apply_chat_template(messages, tokenize=True, return_dict=False,
                                                add_generation_prompt=True, enable_thinking=True)
            prompts.append({"prompt_token_ids": ids})
        receipt["fixtures"] = fixtures
        receipt["input_token_ids"] = [p["prompt_token_ids"] for p in prompts]
        for name, batch, limit in (("warmup", prompts[:1], 32), ("measured", prompts, 1024)):
            receipt["stage"] = name
            flush()
            params = dict(n=1, temperature=0.6, top_p=0.95, top_k=20, presence_penalty=1.5,
                          max_tokens=limit, seed=1729)
            before = time.time()
            outputs = llm.generate(batch, SamplingParams(**params), use_tqdm=False)
            seconds = time.time() - before
            records = []
            for output in outputs:
                for sample in output.outputs:
                    assert sample.finish_reason in ("stop", "length")
                    records.append({"text": sample.text, "token_ids": list(sample.token_ids),
                                    "finish_reason": sample.finish_reason, "stop_reason": sample.stop_reason})
            count = sum(len(r["token_ids"]) for r in records)
            receipt["runs"].append({"name": name, "sampling": params, "seconds": seconds,
                                    "output_tokens": count, "tokens_per_second": count / seconds,
                                    "responses": records})
            flush()
        receipt["status"] = "smoke_passed_not_full_forward_acceptance"
    except BaseException:
        receipt.update(status="failed", error=traceback.format_exc())
    finally:
        receipt["wall_seconds"] = time.time() - started
        flush()
    print(json.dumps({"status": receipt["status"], "wall_seconds": receipt["wall_seconds"], "out": str(args.out)}))
    if receipt["status"] == "failed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
