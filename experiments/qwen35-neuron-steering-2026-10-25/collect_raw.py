"""Collect the approved 40 paired raw answers; no content scoring or interpretation."""
import argparse
from contextlib import nullcontext
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import time
import traceback

import torch

from probe import TARGETS, activation_offsets, digest, offsets_from_scales, residual_scales, tensor_digest


QUESTION_HASH = "d98a18071ff3dad4071ae86f2bb517d2aba1152e57f3c65588b454940f8c425f"
REVISION = "851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a"


def utc():
    return datetime.now(timezone.utc).isoformat()


def write_json(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    temporary.replace(path)


def object_hash(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


def end_reason(tokens, budget, eos_ids):
    if tokens and tokens[-1] in eos_ids:
        return "eos_token"
    return "length_limit" if len(tokens) >= budget else "other_stop"


def pair_attempts(generate, persist):
    """Save each arm before and after generation; rerun both only for length truncation."""
    attempts = []
    for budget in (512, 1024):
        attempt = {"max_new_tokens": budget, **{arm: {"status": "pending"} for arm in ("baseline", "modified")}}
        attempts.append(attempt)
        persist(attempts)
        for arm in ("baseline", "modified"):
            attempt[arm] = {"status": "running", "started_utc": utc()}
            persist(attempts)
            try:
                attempt[arm] = generate(arm, budget)
            except Exception as error:
                attempt[arm].update({"status": "failed", "ended_utc": utc(),
                                             "error": f"{type(error).__name__}: {error}", "traceback": traceback.format_exc()})
                persist(attempts)
                raise
            persist(attempts)
        if not any(attempt[arm]["end_reason"] == "length_limit" for arm in ("baseline", "modified")):
            break
    return attempts


def verify_assets(model_path):
    receipt_path = model_path / "download_receipt.json"
    receipt = json.loads(receipt_path.read_text())
    assert receipt["revision"] == REVISION and receipt["status"] == "all_files_verified"
    for entry in receipt["files"]:
        path = model_path / entry["file"]
        assert path.is_relative_to(model_path) and path.stat().st_size == entry["bytes"]
        sha = hashlib.sha256()
        with path.open("rb") as file:
            while chunk := file.read(8 * 1024 * 1024):
                sha.update(chunk)
        assert sha.hexdigest() == entry["sha256"], f"Changed model asset: {entry['file']}"
    return {"download_receipt_sha256": digest(receipt_path), "verified_files": receipt["files"]}


def compare_models(base, modified):
    base_parameters, modified_parameters = dict(base.named_parameters()), dict(modified.named_parameters())
    assert base_parameters.keys() == modified_parameters.keys()
    base_storage = {parameter.untyped_storage().data_ptr() for parameter in base_parameters.values()}
    modified_storage = {parameter.untyped_storage().data_ptr() for parameter in modified_parameters.values()}
    assert base_storage.isdisjoint(modified_storage), "Model instances share parameter storage"
    for name, parameter in base_parameters.items():
        assert torch.equal(parameter, modified_parameters[name]), f"Initial parameter mismatch: {name}"
    return {"parameter_tensors_checked": len(base_parameters), "initial_parameters_equal": True,
            "parameter_storages_disjoint": True, "parameter_count_per_model": sum(p.numel() for p in base_parameters.values())}


@torch.no_grad()
def run(args, questions, receipt):
    import safetensors
    import transformers
    from transformers import AutoTokenizer, Qwen3_5ForConditionalGeneration

    os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
    torch.set_num_threads(4)
    torch.manual_seed(0)
    torch.use_deterministic_algorithms(True)
    receipt["assets"] = verify_assets(args.model)
    receipt["versions"] = {"torch": torch.__version__, "transformers": transformers.__version__, "safetensors": safetensors.__version__}
    write_json(args.output / "receipt.json", receipt)
    tokenizer = AutoTokenizer.from_pretrained(str(args.model), local_files_only=True, trust_remote_code=False)
    loading = {"local_files_only": True, "trust_remote_code": False, "torch_dtype": torch.bfloat16, "attn_implementation": "eager"}
    base = Qwen3_5ForConditionalGeneration.from_pretrained(str(args.model), **loading).to(args.device).eval()
    modified = Qwen3_5ForConditionalGeneration.from_pretrained(str(args.model), **loading).to(args.device).eval()
    base.requires_grad_(False)
    modified.requires_grad_(False)
    receipt["identity_checks"] = compare_models(base, modified)
    receipt["model_class"] = type(base).__name__
    receipt["generation_config"] = base.generation_config.to_dict()
    assert base.generation_config.to_dict() == modified.generation_config.to_dict()
    receipt["parameter_dtypes"] = sorted({str(p.dtype) for p in base.parameters()})
    base_layers = base.model.language_model.layers
    modified_modules = {layer: modified.model.language_model.layers[layer].mlp.down_proj for layer, _, _ in TARGETS}
    base_modules = {layer: base_layers[layer].mlp.down_proj for layer, _, _ in TARGETS}
    for layer, neuron, _ in TARGETS:
        assert modified_modules[layer].weight.shape == (2560, 9216) and neuron < 9216
        assert base_modules[layer].bias is None and modified_modules[layer].bias is None
    before = {arm: {str(layer): tensor_digest(module.weight) for layer, module in modules.items()}
              for arm, modules in (("baseline", base_modules), ("modified", modified_modules))}
    receipt["target_weight_sha256_before"] = before
    write_json(args.output / "receipt.json", receipt)

    def encode(prompt):
        rendered = tokenizer.apply_chat_template([{"role": "user", "content": prompt}], tokenize=False,
                                                  add_generation_prompt=True, enable_thinking=False)
        inputs = tokenizer(rendered, return_tensors="pt", add_special_tokens=False).to(args.device)
        metadata = {"rendered_chat": rendered, "rendered_chat_sha256": hashlib.sha256(rendered.encode()).hexdigest(),
                    "tensors": {name: tensor.tolist() for name, tensor in inputs.items()}}
        metadata["tensors_sha256"] = object_hash(metadata["tensors"])
        return inputs, metadata

    def generate(model, inputs, budget):
        started, wall = time.monotonic(), utc()
        # Fresh tensor copies and a new generate() call: no history or cache is supplied/reused.
        arm_inputs = {key: value.clone() for key, value in inputs.items()}
        assert all(torch.equal(arm_inputs[key], value) for key, value in inputs.items())
        output = model.generate(**arm_inputs, do_sample=False, max_new_tokens=budget, use_cache=True,
                                logits_to_keep=1, pad_token_id=tokenizer.pad_token_id if tokenizer.pad_token_id is not None else tokenizer.eos_token_id)
        tokens = output[0, inputs["input_ids"].shape[-1]:].tolist()
        eos = model.generation_config.eos_token_id
        eos = [eos] if isinstance(eos, int) else (eos or [])
        return {"status": "completed", "started_utc": wall, "ended_utc": utc(), "seconds": time.monotonic() - started,
                "token_ids": tokens, "token_sha256": object_hash(tokens), "generated_token_count": len(tokens),
                "raw_text": tokenizer.decode(tokens, skip_special_tokens=False, clean_up_tokenization_spaces=False),
                "end_reason": end_reason(tokens, budget, eos), "max_new_tokens": budget,
                "input_tensors_sha256": object_hash({key: value.tolist() for key, value in arm_inputs.items()})}

    inputs, metadata = encode(questions[0]["prompt"])
    controls = {"input": metadata, "status": "running", "outputs": {}}
    control_path = args.output / "mechanical_checks.json"
    write_json(control_path, controls)
    try:
        control_scales = residual_scales(base, base_layers, {key: value.clone() for key, value in inputs.items()})
        control_offsets = offsets_from_scales(modified_modules, control_scales)
        controls.update({"residual_scales": control_scales, "activation_offsets": control_offsets})
        for label, model, context in (("baseline", base, nullcontext()), ("unmodified_clone", modified, nullcontext()),
                                      ("zero_dose_clone", modified, activation_offsets(modified_modules, {layer: 0.0 for layer in modified_modules})),
                                      ("nonzero_dose_clone", modified, activation_offsets(modified_modules, control_offsets)),
                                      ("restored_clone", modified, nullcontext())):
            controls["current_arm"] = label
            controls["outputs"][label] = {"status": "running", "started_utc": utc()}
            write_json(control_path, controls)
            with context:
                controls["outputs"][label] = generate(model, inputs, 32)
            write_json(control_path, controls)
        baseline_tokens = controls["outputs"]["baseline"]["token_ids"]
        identical_arms = ("unmodified_clone", "zero_dose_clone", "restored_clone")
        assert all(controls["outputs"][label]["token_ids"] == baseline_tokens for label in identical_arms), "Mechanical token identity check failed"
        assert all(not module._forward_pre_hooks for module in modified_modules.values())
        controls.update({"status": "completed", "baseline_identical_arms": list(identical_arms), "hooks_removed": True})
    except Exception as error:
        controls.update({"status": "failed", "error": f"{type(error).__name__}: {error}", "traceback": traceback.format_exc()})
        if controls.get("current_arm") and controls["outputs"][controls["current_arm"]]["status"] == "running":
            controls["outputs"][controls["current_arm"]].update({"status": "failed", "error": controls["error"]})
        raise
    finally:
        write_json(control_path, controls)

    for question in questions:
        record_path = args.output / f"{question['id']}.json"
        record = json.loads(record_path.read_text())
        record.update({"status": "running", "started_utc": utc()})
        write_json(record_path, record)
        receipt["current_question"] = question["id"]
        write_json(args.output / "receipt.json", receipt)
        try:
            inputs, metadata = encode(question["prompt"])
            scales = residual_scales(base, base_layers, {key: value.clone() for key, value in inputs.items()})
            offsets = offsets_from_scales(modified_modules, scales)
            record.update({"input": metadata, "residual_scales": scales, "activation_offsets": offsets, "targets": TARGETS})
            write_json(record_path, record)

            def generate_arm(arm, budget):
                if arm == "baseline":
                    return generate(base, inputs, budget)
                with activation_offsets(modified_modules, offsets):
                    return generate(modified, inputs, budget)

            def persist(attempts):
                record["attempts"] = attempts
                write_json(record_path, record)

            pair_attempts(generate_arm, persist)
            assert all(not module._forward_pre_hooks for module in modified_modules.values())
            record.update({"status": "completed", "ended_utc": utc()})
            receipt["completed_questions"].append(question["id"])
            print(json.dumps({"completed_question": question["id"], "count": len(receipt["completed_questions"]), "total": 40}), flush=True)
        except Exception as error:
            record.update({"status": "failed", "ended_utc": utc(), "error": f"{type(error).__name__}: {error}", "traceback": traceback.format_exc()})
            raise
        finally:
            write_json(record_path, record)
            write_json(args.output / "receipt.json", receipt)
    after = {arm: {str(layer): tensor_digest(module.weight) for layer, module in modules.items()}
             for arm, modules in (("baseline", base_modules), ("modified", modified_modules))}
    assert before == after, "Target weight parameters changed during inference"
    assert receipt["completed_questions"] == [question["id"] for question in questions]
    receipt.update({"status": "completed", "target_weight_sha256_after": after,
                    "question_record_sha256": {q["id"]: digest(args.output / f"{q['id']}.json") for q in questions}})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, required=True, help="Local verified Qwen3.5-4B checkpoint directory")
    parser.add_argument("--revision", default=REVISION, choices=(REVISION,))
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cpu")
    parser.add_argument("--questions", type=Path, default=Path(__file__).with_name("language_questions.zh-CN.json"))
    parser.add_argument("--output", type=Path, required=True, help="New directory; automatic resume is intentionally unsupported")
    args = parser.parse_args()
    questions = [{key: row[key] for key in ("id", "prompt", "topic")} for row in json.loads(args.questions.read_text())["questions"]]
    assert object_hash([{key: row[key] for key in ("id", "prompt")} for row in questions]) == QUESTION_HASH, "Question list differs from the approved 40 prompts"
    assert [q["id"] for q in questions] == [f"Q{i:02d}" for i in range(1, 41)]
    args.model = args.model.resolve(strict=True)
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / "questions.json").write_bytes(args.questions.read_bytes())
    started = time.monotonic()
    receipt = {"status": "started", "started_utc": utc(), "base_revision": REVISION,
               "arguments": {key: str(value) for key, value in vars(args).items()}, "question_list_sha256": QUESTION_HASH,
               "source_sha256": digest(Path(__file__)), "probe_helpers_sha256": digest(Path(__file__).with_name("probe.py")),
               "question_file_sha256": digest(args.questions), "expected_question_ids": [q["id"] for q in questions],
               "completed_questions": [], "targets": TARGETS,
               "fixed_settings": {"dtype": "bfloat16", "cpu_threads": 4, "seed": 0, "thinking": False, "do_sample": False,
                                  "first_max_new_tokens": 512, "paired_retry_max_new_tokens": 1024, "attention_backend": "eager"},
               "assumptions": ["Zero-based neuron/layer indices; additive down_proj-input offset", "Baseline full-prompt residual L2 median excludes first token", "Per-prompt scales held fixed for all modified-model prefill/decode positions", "No static bias arm; no training; no content analysis"]}
    for question in questions:
        write_json(args.output / f"{question['id']}.json", {**question, "status": "pending", "attempts": []})
    write_json(args.output / "receipt.json", receipt)
    try:
        run(args, questions, receipt)
    except Exception as error:
        receipt.update({"status": "failed", "error": f"{type(error).__name__}: {error}", "traceback": traceback.format_exc()})
        raise
    finally:
        receipt.update({"ended_utc": utc(), "elapsed_seconds": time.monotonic() - started,
                        "question_statuses": {q["id"]: json.loads((args.output / f"{q['id']}.json").read_text())["status"] for q in questions}})
        write_json(args.output / "receipt.json", receipt)


if __name__ == "__main__":
    main()
