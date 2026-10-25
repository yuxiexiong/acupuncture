"""Paired English benchmark subsets: original versus screenshot-based EVO steering."""
import argparse
from collections import Counter
from contextlib import nullcontext
from decimal import Decimal
import json
import os
from pathlib import Path
import re
import time
import traceback


NUMBER = r"[+-]?(?:(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d*)?|\.\d+)"


def parse_answer(text, benchmark):
    text = text.strip().replace("−", "-")
    if benchmark == "gsm8k":
        # The requested final marker or an entirely numeric response; never a random last number.
        value = text.rsplit("####", 1)[-1].strip() if "####" in text else text
        if not re.fullmatch(NUMBER, value):
            return None
        return format(Decimal(value.replace(",", "")).normalize(), "f")
    match = re.fullmatch(r"(?:(?:the\s+)?(?:correct\s+|final\s+)?answer\s*(?:is\s*|:\s*))?\(?([A-D])\)?[.!]?", text, re.I)
    return match.group(1).upper() if match else None


def forced_letter_result(logits, target):
    prediction = "ABCD"[max(range(4), key=logits.__getitem__)]
    return {"logits": dict(zip("ABCD", logits)), "prediction": prediction, "correct": prediction == target}


def summarize(records, expected_counts):
    result = {"scope": "completed_pairs_only", "primary_metric": "strict_generated_accuracy", "benchmarks": {}}
    for benchmark, expected in expected_counts.items():
        rows = [r for r in records if r["benchmark"] == benchmark and r["status"] == "completed"]
        count = len(rows)
        entry = {"n": count, "expected_n": expected, "complete": count == expected}
        for arm in ("baseline", "evo"):
            outputs = [r["outputs"][arm] for r in rows]
            correct = sum(o["correct"] for o in outputs)
            entry[arm] = {"correct": correct, "accuracy": correct / count if count else None,
                          "invalid": sum(o["parsed_answer"] is None for o in outputs),
                          "truncated": sum(o["end_reason"] == "length_limit" for o in outputs)}
            forced = [o["first_token_forced_letter"] for o in outputs if "first_token_forced_letter" in o]
            if forced:
                entry[arm]["first_token_forced_letter_accuracy"] = {"correct": sum(o["correct"] for o in forced), "n": len(forced)}
        transitions = Counter(f"{int(r['outputs']['baseline']['correct'])}->{int(r['outputs']['evo']['correct'])}" for r in rows)
        entry["paired_transitions"] = {key: transitions[key] for key in ("0->0", "0->1", "1->0", "1->1")}
        entry["evo_minus_baseline_percentage_points"] = 100 * (entry["evo"]["accuracy"] - entry["baseline"]["accuracy"]) if count else None
        result["benchmarks"][benchmark] = entry
    return result


def run(args, items, receipt):
    import torch
    import transformers
    from transformers import AutoTokenizer, Qwen3_5ForConditionalGeneration
    from collect_raw import compare_models, end_reason, object_hash, utc, verify_assets, write_json
    from probe import TARGETS, activation_offsets, offsets_from_scales, residual_scales, tensor_digest

    os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
    torch.set_num_threads(args.threads)
    torch.manual_seed(0)
    torch.use_deterministic_algorithms(True)
    receipt["assets"] = verify_assets(args.model)
    receipt["versions"] = {"torch": torch.__version__, "transformers": transformers.__version__}
    write_json(args.output / "receipt.json", receipt)
    tokenizer = AutoTokenizer.from_pretrained(str(args.model), local_files_only=True, trust_remote_code=False)
    letter_ids = [tokenizer.encode(letter, add_special_tokens=False) for letter in "ABCD"]
    assert all(len(ids) == 1 and tokenizer.decode(ids) == letter for letter, ids in zip("ABCD", letter_ids))
    letter_ids = [ids[0] for ids in letter_ids]
    receipt["forced_letter_token_ids"] = dict(zip("ABCD", letter_ids))
    loading = {"local_files_only": True, "trust_remote_code": False, "torch_dtype": torch.bfloat16, "attn_implementation": "eager"}
    models = {arm: Qwen3_5ForConditionalGeneration.from_pretrained(str(args.model), **loading).to(args.device).eval()
              for arm in ("baseline", "evo")}
    for model in models.values():
        model.requires_grad_(False)
    base, evo = models["baseline"], models["evo"]
    receipt["identity_checks"] = compare_models(base, evo)
    assert base.generation_config.to_dict() == evo.generation_config.to_dict()
    receipt["original_generation_config"] = base.generation_config.to_dict()
    configured_eos = base.generation_config.eos_token_id
    stop_ids = set([configured_eos] if isinstance(configured_eos, int) else configured_eos or [])
    if tokenizer.eos_token_id is not None:
        stop_ids.add(tokenizer.eos_token_id)
    im_end = tokenizer.convert_tokens_to_ids("<|im_end|>")
    assert isinstance(im_end, int) and tokenizer.convert_ids_to_tokens(im_end) == "<|im_end|>"
    assert tokenizer.encode("<|im_end|>", add_special_tokens=False) == [im_end]
    stop_ids.add(im_end)
    stop_ids = sorted(stop_ids)
    receipt["effective_stop_tokens"] = {str(i): tokenizer.convert_ids_to_tokens(i) for i in stop_ids}
    modules = {arm: {layer: model.model.language_model.layers[layer].mlp.down_proj for layer, _, _ in TARGETS}
               for arm, model in models.items()}
    for arm_modules in modules.values():
        assert all(m.weight.shape == (2560, 9216) and m.bias is None for m in arm_modules.values())
    before = {arm: {str(layer): tensor_digest(m.weight) for layer, m in arm_modules.items()} for arm, arm_modules in modules.items()}
    receipt["target_weight_sha256_before"] = before
    write_json(args.output / "receipt.json", receipt)

    def encode(prompt):
        rendered = tokenizer.apply_chat_template([{"role": "user", "content": prompt}], tokenize=False,
                                                  add_generation_prompt=True, enable_thinking=False)
        inputs = tokenizer(rendered, return_tensors="pt", add_special_tokens=False).to(args.device)
        tensors = {key: tensor.tolist() for key, tensor in inputs.items()}
        return inputs, {"rendered_chat": rendered, "tensors": tensors, "input_sha256": object_hash(tensors)}

    def generate(model, inputs, budget, mcq_target=None):
        if str(args.device).startswith("cuda"):
            torch.cuda.synchronize(args.device)
        started, wall = time.monotonic(), utc()
        captured = []
        def capture(_model, _inputs, output):
            if not captured:
                captured.append(output.logits[0, -1, letter_ids].detach().float().cpu().tolist())
        handle = model.register_forward_hook(capture) if mcq_target is not None else None
        try:
            output = model.generate(**{key: value.clone() for key, value in inputs.items()}, do_sample=False,
                                    max_new_tokens=budget, use_cache=True, logits_to_keep=1, eos_token_id=stop_ids,
                                    pad_token_id=tokenizer.pad_token_id if tokenizer.pad_token_id is not None else stop_ids[0])
        finally:
            if handle is not None:
                handle.remove()
        tokens = output[0, inputs["input_ids"].shape[-1]:].tolist()
        # Strip only an actual terminal stop token; retain any other special-token emissions.
        content_tokens = tokens[:-1] if tokens and tokens[-1] in stop_ids else tokens
        return {**({"first_token_forced_letter": forced_letter_result(captured[0], mcq_target)} if mcq_target is not None else {}),
                "status": "completed", "started_utc": wall, "ended_utc": utc(), "seconds": time.monotonic() - started,
                "token_ids": tokens, "generated_token_count": len(tokens), "max_new_tokens": budget,
                "raw_text": tokenizer.decode(tokens, skip_special_tokens=False, clean_up_tokenization_spaces=False),
                "answer_text": tokenizer.decode(content_tokens, skip_special_tokens=False, clean_up_tokenization_spaces=False),
                "end_reason": end_reason(tokens, budget, stop_ids)}

    with torch.inference_mode():
        inputs, metadata = encode(items[0]["prompt"])
        scales = residual_scales(base, base.model.language_model.layers, inputs)
        offsets = offsets_from_scales(modules["evo"], scales)
        checks = {"status": "running", "input": metadata, "residual_scales": scales, "activation_offsets": offsets, "outputs": {}}
        try:
            for label, model, context in (("baseline", base, nullcontext()), ("unmodified_clone", evo, nullcontext()),
                    ("zero_dose_clone", evo, activation_offsets(modules["evo"], {layer: 0.0 for layer in offsets})),
                    ("nonzero_clone", evo, activation_offsets(modules["evo"], offsets)), ("restored_clone", evo, nullcontext())):
                checks["current_arm"] = label
                write_json(args.output / "mechanical_checks.json", checks)
                with context:
                    checks["outputs"][label] = generate(model, inputs, 32)
            reference = checks["outputs"]["baseline"]["token_ids"]
            assert all(checks["outputs"][a]["token_ids"] == reference for a in ("unmodified_clone", "zero_dose_clone", "restored_clone"))
            assert all(not m._forward_pre_hooks for arm_modules in modules.values() for m in arm_modules.values())
            checks["status"] = "completed"
        except Exception as error:
            checks.update({"status": "failed", "error": str(error)})
            raise
        finally:
            write_json(args.output / "mechanical_checks.json", checks)

        records = []
        expected_counts = dict(Counter(item["benchmark"] for item in items))
        for index, item in enumerate(items):
            pair_start = time.monotonic()
            path = args.output / f"{index:04d}.json"
            record = {**item, "status": "running", "started_utc": utc(), "outputs": {}}
            receipt["current_item"] = item["id"]
            write_json(args.output / "receipt.json", receipt)
            write_json(path, record)
            try:
                inputs, metadata = encode(item["prompt"])
                scales = residual_scales(base, base.model.language_model.layers, inputs)
                offsets = offsets_from_scales(modules["evo"], scales)
                record.update({"input": metadata, "residual_scales": scales, "activation_offsets": offsets})
                budget = args.gsm_tokens if item["benchmark"] == "gsm8k" else args.mcq_tokens
                order = ("baseline", "evo") if index % 2 == 0 else ("evo", "baseline")
                record["arm_order"] = order
                for arm in order:
                    record["outputs"][arm] = {"status": "running", "started_utc": utc()}
                    write_json(path, record)
                    context = activation_offsets(modules["evo"], offsets) if arm == "evo" else nullcontext()
                    with context:
                        answer = generate(models[arm], inputs, budget, item["target"] if item["benchmark"] != "gsm8k" else None)
                    answer["input_sha256"] = metadata["input_sha256"]
                    answer["parsed_answer"] = parse_answer(answer["answer_text"], item["benchmark"])
                    answer["correct"] = answer["parsed_answer"] is not None and answer["parsed_answer"] == parse_answer(item["target"], item["benchmark"])
                    record["outputs"][arm] = answer
                    write_json(path, record)
                assert all(not m._forward_pre_hooks for arm_modules in modules.values() for m in arm_modules.values())
                record.update({"status": "completed", "ended_utc": utc(), "seconds": time.monotonic() - pair_start})
                records.append(record)
                receipt["completed_items"].append(item["id"])
                write_json(args.output / "summary.json", summarize(records, expected_counts))
                print(json.dumps({"completed": len(records), "total": len(items), "benchmark": item["benchmark"],
                                  "item": item["id"], "pair_seconds": record["seconds"]}), flush=True)
            except Exception as error:
                record.update({"status": "failed", "error": f"{type(error).__name__}: {error}", "traceback": traceback.format_exc()})
                for answer in record["outputs"].values():
                    if answer["status"] == "running":
                        answer.update({"status": "failed", "error": record["error"], "ended_utc": utc()})
                raise
            finally:
                write_json(path, record)
                write_json(args.output / "receipt.json", receipt)
    after = {arm: {str(layer): tensor_digest(m.weight) for layer, m in arm_modules.items()} for arm, arm_modules in modules.items()}
    assert before == after, "Target weights changed during inference"
    assert receipt["completed_items"] == [item["id"] for item in items]
    receipt.update({"status": "completed", "target_weight_sha256_after": after, "hooks_removed": True})


def main():
    from collect_raw import REVISION, utc, write_json
    from probe import TARGETS, digest

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--items", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--mcq-tokens", type=int, default=64)
    parser.add_argument("--gsm-tokens", type=int, default=512)
    args = parser.parse_args()
    assert re.fullmatch(r"cpu|cuda(?::\d+)?", args.device)
    assert min(args.threads, args.mcq_tokens, args.gsm_tokens) > 0
    items = json.loads(args.items.read_text())
    assert items and len({item["id"] for item in items}) == len(items)
    for item in items:
        assert item["benchmark"] in ("race", "gsm8k", "logiqa2") and isinstance(item["prompt"], str) and item["prompt"].strip()
        assert isinstance(item["target"], str) and parse_answer(item["target"], item["benchmark"]) is not None
    args.model = args.model.resolve(strict=True)
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / "items.json").write_bytes(args.items.read_bytes())
    receipt = {"status": "started", "started_utc": utc(), "base_revision": REVISION, "targets": TARGETS,
               "authorization": "User requested a quick paired run of RACE, GSM8K and LogiQA2.0 for original and EVO Qwen3.5-4B.",
               "evaluation_scope": "Fixed English test subsets; not full benchmark leaderboard scores",
               "arguments": {key: str(value) for key, value in vars(args).items()}, "completed_items": [],
               "expected_counts": dict(Counter(item["benchmark"] for item in items)), "items_sha256": digest(args.items),
               "source_sha256": {name: digest(Path(__file__).with_name(name)) for name in ("benchmark_quick.py", "probe.py", "collect_raw.py")},
               "settings": {"dtype": "bfloat16", "seed": 0, "do_sample": False, "enable_thinking": False,
                            "attention_backend": "eager", "mcq_tokens": args.mcq_tokens, "gsm_tokens": args.gsm_tokens,
                            "fresh_conversation_per_item": True, "independent_model_instances": True},
               "scoring": "Strict generated final answers. Invalid and length-limited answers remain in denominator. No retries.",
               "secondary_metric": "MCQ first_token_forced_letter_accuracy: read-only first-forward A/B/C/D logits; not official full-answer likelihood scoring; no extra forward or constrained generation.",
               "intervention": "Same prior zero-based additive down_proj-input offsets; baseline prompt residual median excluding first token; fixed throughout each generation."}
    started = time.monotonic()
    write_json(args.output / "receipt.json", receipt)
    try:
        run(args, items, receipt)
    except Exception as error:
        receipt.update({"status": "failed", "error": f"{type(error).__name__}: {error}", "traceback": traceback.format_exc()})
        raise
    finally:
        receipt.update({"ended_utc": utc(), "elapsed_seconds": time.monotonic() - started})
        write_json(args.output / "receipt.json", receipt)


if __name__ == "__main__":
    main()
