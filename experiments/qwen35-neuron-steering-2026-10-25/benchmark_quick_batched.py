"""GSM8K-only paired batching; unpadded per-prompt calibration and fixed EVO doses."""
import argparse
from contextlib import nullcontext
import json
import os
from pathlib import Path
import re
import time
import traceback

from benchmark_quick import parse_answer, summarize


def trim_generated(returned, stop_ids, pad_id, budget):
    first = next((i for i, token in enumerate(returned) if token in stop_ids), None)
    if first is None:
        assert len(returned) == budget
        return returned, 0, "length_limit"
    assert all(token == pad_id for token in returned[first + 1:]), "Unexpected continuation after row EOS"
    return returned[:first + 1], len(returned) - first - 1, "eos_token"


def run(args, items, receipt):
    import torch
    import transformers
    from transformers import AutoTokenizer, Qwen3_5ForConditionalGeneration
    from collect_raw import compare_models, object_hash, utc, verify_assets, write_json
    from probe import TARGETS, activation_offsets, offsets_from_scales, residual_scales, tensor_digest

    os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
    torch.set_num_threads(args.threads)
    torch.manual_seed(0)
    torch.use_deterministic_algorithms(True)
    receipt["assets"] = verify_assets(args.model)
    receipt["versions"] = {"torch": torch.__version__, "transformers": transformers.__version__}
    tokenizer = AutoTokenizer.from_pretrained(str(args.model), local_files_only=True, trust_remote_code=False)
    tokenizer.padding_side = "left"
    loading = {"local_files_only": True, "trust_remote_code": False, "torch_dtype": torch.bfloat16, "attn_implementation": "eager"}
    models = {arm: Qwen3_5ForConditionalGeneration.from_pretrained(str(args.model), **loading).to(args.device).eval()
              for arm in ("baseline", "evo")}
    for model in models.values():
        model.requires_grad_(False)
    base, evo = models["baseline"], models["evo"]
    receipt["identity_checks"] = compare_models(base, evo)
    assert base.generation_config.to_dict() == evo.generation_config.to_dict()
    receipt["original_generation_config"] = base.generation_config.to_dict()
    configured = base.generation_config.eos_token_id
    stop_ids = set([configured] if isinstance(configured, int) else configured or [])
    if tokenizer.eos_token_id is not None:
        stop_ids.add(tokenizer.eos_token_id)
    im_end = tokenizer.convert_tokens_to_ids("<|im_end|>")
    assert tokenizer.convert_ids_to_tokens(im_end) == "<|im_end|>" and tokenizer.encode("<|im_end|>", add_special_tokens=False) == [im_end]
    stop_ids.add(im_end)
    stop_ids = sorted(stop_ids)
    assert tokenizer.pad_token_id is not None
    pad_id = tokenizer.pad_token_id
    receipt["effective_stop_tokens"] = {str(i): tokenizer.convert_ids_to_tokens(i) for i in stop_ids}
    receipt["pad_token_id"] = pad_id
    modules = {arm: {layer: model.model.language_model.layers[layer].mlp.down_proj for layer, _, _ in TARGETS}
               for arm, model in models.items()}
    assert all(m.weight.shape == (2560, 9216) and m.bias is None for group in modules.values() for m in group.values())
    before = {arm: {str(layer): tensor_digest(m.weight) for layer, m in group.items()} for arm, group in modules.items()}
    receipt["target_weight_sha256_before"] = before
    write_json(args.output / "receipt.json", receipt)

    def rendered(prompt):
        return tokenizer.apply_chat_template([{"role": "user", "content": prompt}], tokenize=False,
                                             add_generation_prompt=True, enable_thinking=False)

    def calibrate(prompt):
        text = rendered(prompt)
        inputs = tokenizer(text, return_tensors="pt", add_special_tokens=False).to(args.device)
        scales = residual_scales(base, base.model.language_model.layers, inputs)
        return {"rendered_chat": text, "calibration_input_tensors": {key: value.tolist() for key, value in inputs.items()},
                "residual_scales": scales, "activation_offsets": offsets_from_scales(modules["evo"], scales)}

    def batch_inputs(calibrations):
        return tokenizer([c["rendered_chat"] for c in calibrations], return_tensors="pt", padding=True,
                         add_special_tokens=False).to(args.device)

    def stacked_offsets(calibrations, zero=False):
        return {layer: module.weight.new_tensor([0.0 if zero else c["activation_offsets"][layer] for c in calibrations]).unsqueeze(1)
                for layer, module in modules["evo"].items()}

    def generate(model, inputs, budget):
        if args.device.startswith("cuda"):
            torch.cuda.synchronize(args.device)
        started, wall = time.monotonic(), utc()
        output = model.generate(**{key: value.clone() for key, value in inputs.items()}, do_sample=False,
                                max_new_tokens=budget, use_cache=True, logits_to_keep=1, eos_token_id=stop_ids, pad_token_id=pad_id)
        returned = output[:, inputs["input_ids"].shape[-1]:].tolist()
        seconds, ended = time.monotonic() - started, utc()
        answers = []
        for row, token_stream in enumerate(returned):
            tokens, pad_count, reason = trim_generated(token_stream, stop_ids, pad_id, budget)
            content = tokens[:-1] if reason == "eos_token" else tokens
            answers.append({"status": "completed", "started_utc": wall, "ended_utc": ended,
                            "batch_seconds": seconds, "seconds": seconds / len(returned), "timing_note": "seconds is amortized batch generation time",
                            "token_ids": tokens, "batched_returned_token_ids": token_stream, "returned_padding_count": pad_count,
                            "generated_token_count": len(tokens), "max_new_tokens": budget, "end_reason": reason,
                            "raw_text": tokenizer.decode(tokens, skip_special_tokens=False, clean_up_tokenization_spaces=False),
                            "answer_text": tokenizer.decode(content, skip_special_tokens=False, clean_up_tokenization_spaces=False),
                            "input_sha256": object_hash({key: value[row:row + 1].tolist() for key, value in inputs.items()})})
        return answers

    def control_outputs(calibrations, padded):
        inputs = batch_inputs(calibrations)
        outputs = {}
        scalar = calibrations[0]["activation_offsets"]
        offsets = stacked_offsets(calibrations) if padded else scalar
        zero = stacked_offsets(calibrations, zero=True) if padded else {layer: 0.0 for layer in scalar}
        for label, model, context in (("baseline", base, nullcontext()), ("unmodified_clone", evo, nullcontext()),
                ("zero_dose_clone", evo, activation_offsets(modules["evo"], zero)),
                ("nonzero_clone", evo, activation_offsets(modules["evo"], offsets)), ("restored_clone", evo, nullcontext())):
            with context:
                outputs[label] = generate(model, inputs, 16)
        return outputs

    with torch.inference_mode():
        probes = ["What is 2 + 3? Answer with only the number.",
                  "A public library has three shelves. Each shelf holds ten books, and five books are borrowed. How many books remain? Answer with only the number."]
        checks = {"status": "running", "prompts": probes, "single": [], "batched": {}}
        try:
            calibrations = [calibrate(prompt) for prompt in probes]
            checks["calibrations"] = calibrations
            assert len(calibrations[0]["calibration_input_tensors"]["input_ids"][0]) != len(calibrations[1]["calibration_input_tensors"]["input_ids"][0])
            for calibration in calibrations:
                checks["single"].append(control_outputs([calibration], padded=False))
                write_json(args.output / "mechanical_checks.json", checks)
            batch_calibrations = [calibrations[i % 2] for i in range(args.batch_size)]
            checks["batched"] = control_outputs(batch_calibrations, padded=True)
            mismatches = []
            for index in range(args.batch_size):
                for label, outputs in checks["batched"].items():
                    if outputs[index]["token_ids"] != checks["single"][index % 2][label][0]["token_ids"]:
                        mismatches.append({"row": index, "label": label})
                for label in ("unmodified_clone", "zero_dose_clone", "restored_clone"):
                    assert checks["batched"][label][index]["token_ids"] == checks["batched"]["baseline"][index]["token_ids"]
                    assert checks["single"][index % 2][label][0]["token_ids"] == checks["single"][index % 2]["baseline"][0]["token_ids"]
            checks["single_vs_batch_mismatches"] = mismatches
            assert not mismatches, f"Single/padded-batch greedy tokens differ: {mismatches}"
            assert all(not m._forward_pre_hooks for group in modules.values() for m in group.values())
            checks.update({"status": "completed", "single_vs_batch_exact": True, "rows_checked": args.batch_size})
        except Exception as error:
            checks.update({"status": "failed", "error": str(error), "traceback": traceback.format_exc()})
            raise
        finally:
            write_json(args.output / "mechanical_checks.json", checks)

        records = []
        for start in range(0, len(items), args.batch_size):
            batch_start = time.monotonic()
            selected = items[start:start + args.batch_size]
            batch = [{**item, "status": "running", "batch_index": start // args.batch_size, "outputs": {}} for item in selected]
            paths = [args.output / f"{start + i:04d}.json" for i in range(len(batch))]
            receipt["current_batch_ids"] = [item["id"] for item in selected]
            write_json(args.output / "receipt.json", receipt)
            try:
                calibrations = [calibrate(item["prompt"]) for item in selected]
                inputs = batch_inputs(calibrations)
                for index, (row, calibration, path) in enumerate(zip(batch, calibrations, paths)):
                    tensors = {key: value[index:index + 1].tolist() for key, value in inputs.items()}
                    row.update({"residual_scales": calibration["residual_scales"], "activation_offsets": calibration["activation_offsets"],
                                "input": {"raw_prompt": row["prompt"], "rendered_chat": calibration["rendered_chat"], "tensors": tensors,
                                          "input_sha256": object_hash(tensors), "calibration_input_tensors": calibration["calibration_input_tensors"]}})
                    write_json(path, row)
                order = ("baseline", "evo") if (start // args.batch_size) % 2 == 0 else ("evo", "baseline")
                for arm in order:
                    for row, path in zip(batch, paths):
                        row["outputs"][arm] = {"status": "running"}
                        row["arm_order"] = order
                        write_json(path, row)
                    context = activation_offsets(modules["evo"], stacked_offsets(calibrations)) if arm == "evo" else nullcontext()
                    with context:
                        answers = generate(models[arm], inputs, args.gsm_tokens)
                    for row, answer, path in zip(batch, answers, paths):
                        assert answer["input_sha256"] == row["input"]["input_sha256"]
                        answer["parsed_answer"] = parse_answer(answer["answer_text"], "gsm8k")
                        answer["correct"] = answer["parsed_answer"] is not None and answer["parsed_answer"] == parse_answer(row["target"], "gsm8k")
                        row["outputs"][arm] = answer
                        write_json(path, row)
                assert all(not m._forward_pre_hooks for group in modules.values() for m in group.values())
                for row in batch:
                    row.update({"status": "completed", "ended_utc": utc(), "batch_pair_seconds": time.monotonic() - batch_start})
                    records.append(row)
                    receipt["completed_items"].append(row["id"])
                write_json(args.output / "summary.json", summarize(records, {"gsm8k": len(items)}))
                print(json.dumps({"completed": len(records), "total": len(items), "batch_pair_seconds": time.monotonic() - batch_start}), flush=True)
            except Exception as error:
                for row in batch:
                    row.update({"status": "failed", "error": str(error), "traceback": traceback.format_exc()})
                    for answer in row["outputs"].values():
                        if answer["status"] == "running":
                            answer.update({"status": "failed", "error": str(error)})
                raise
            finally:
                for row, path in zip(batch, paths):
                    write_json(path, row)
                write_json(args.output / "receipt.json", receipt)
    after = {arm: {str(layer): tensor_digest(m.weight) for layer, m in group.items()} for arm, group in modules.items()}
    assert before == after and receipt["completed_items"] == [item["id"] for item in items]
    receipt.update({"status": "completed", "target_weight_sha256_after": after, "hooks_removed": True})


def main():
    from collect_raw import REVISION, utc, write_json
    from probe import TARGETS, digest
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("model", "items", "output"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--gsm-tokens", type=int, default=512)
    args = parser.parse_args()
    assert re.fullmatch(r"cpu|cuda(?::\d+)?", args.device) and args.batch_size >= 2 and min(args.threads, args.gsm_tokens) > 0
    items = json.loads(args.items.read_text())
    assert items and len({item["id"] for item in items}) == len(items)
    assert all(item["benchmark"] == "gsm8k" and parse_answer(item["target"], "gsm8k") is not None for item in items)
    args.model = args.model.resolve(strict=True)
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / "items.json").write_bytes(args.items.read_bytes())
    receipt = {"status": "started", "started_utc": utc(), "base_revision": REVISION, "targets": TARGETS,
               "authorization": "User requested quick paired benchmarks; GSM8K batching preserves fixed items, doses, generation budget and scoring.",
               "evaluation_scope": "Fixed English GSM8K test subset; not full benchmark leaderboard score",
               "arguments": {key: str(value) for key, value in vars(args).items()}, "completed_items": [],
               "expected_counts": {"gsm8k": len(items)}, "items_sha256": digest(args.items),
               "source_sha256": {name: digest(Path(__file__).with_name(name)) for name in ("benchmark_quick_batched.py", "benchmark_quick.py", "probe.py", "collect_raw.py")},
               "settings": {"dtype": "bfloat16", "seed": 0, "do_sample": False, "enable_thinking": False, "attention_backend": "eager",
                            "gsm_tokens": args.gsm_tokens, "batch_size": args.batch_size, "padding_side": "left", "fresh_conversation_per_item": True,
                            "independent_model_instances": True, "calibration": "individual unpadded baseline full prompt"},
               "scoring": "Strict generated final numeric answer; invalid and truncated retained; no retries; post-EOS returned padding removed.",
               "intervention": "Unchanged per-prompt residual median; row-specific Bx1 additive offsets at each down_proj input."}
    started = time.monotonic()
    write_json(args.output / "receipt.json", receipt)
    try:
        run(args, items, receipt)
    except Exception as error:
        receipt.update({"status": "failed", "error": str(error), "traceback": traceback.format_exc()})
        raise
    finally:
        receipt.update({"ended_utc": utc(), "elapsed_seconds": time.monotonic() - started})
        write_json(args.output / "receipt.json", receipt)


if __name__ == "__main__":
    main()
