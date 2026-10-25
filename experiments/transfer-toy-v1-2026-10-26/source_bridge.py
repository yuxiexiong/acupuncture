"""BF16 implementation bridge on frozen Q01-Q24 trajectories; no new generation."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import time
import traceback

from transfer_engine import (TransferEngine, LAYERS, SOURCE_NEURONS, SIGNS,
                             encode_text, text_hash, token_hash)
from run_benchmark import read, rows, sha, utc, write


def trim_at_first_eos(tokens, stops=(248044, 248046)):
    end = next((i + 1 for i, token in enumerate(tokens) if token in stops), len(tokens))
    return tokens[:end]


def segments(prompt_length, total_length):
    """Each logit row predicts the token after its input position."""
    assert 1 < prompt_length <= total_length
    return {"prompt_next_token": list(range(prompt_length - 1)),
            "answer_next_token": list(range(prompt_length - 1, total_length - 1)),
            "after_final_token": [total_length - 1]}


def compare_logits(channel, vector, prompt_length, chunk_size=16):
    import torch
    assert channel.shape == vector.shape and channel.ndim == 2
    values = {key: [] for key in ("kl_channel_to_vector", "kl_vector_to_channel", "argmax_equal", "max_abs_logit_difference")}
    for start in range(0, channel.shape[0], chunk_size):
        first, second = channel[start:start + chunk_size].float(), vector[start:start + chunk_size].float()
        assert torch.isfinite(first).all() and torch.isfinite(second).all()
        a, b = torch.log_softmax(first, -1), torch.log_softmax(second, -1)
        values["kl_channel_to_vector"].extend((a.exp() * (a - b)).sum(-1).cpu().tolist())
        values["kl_vector_to_channel"].extend((b.exp() * (b - a)).sum(-1).cpu().tolist())
        values["argmax_equal"].extend((first.argmax(-1) == second.argmax(-1)).cpu().tolist())
        values["max_abs_logit_difference"].extend((first - second).abs().amax(-1).cpu().tolist())
    summary = {}
    for name, indices in {"all_positions": list(range(channel.shape[0])), **segments(prompt_length, channel.shape[0])}.items():
        summary[name] = {"positions": len(indices)}
        for metric, measurements in values.items():
            summary[name][metric + "_mean"] = sum(measurements[i] for i in indices) / len(indices) if indices else None
            summary[name][metric + "_max"] = max((measurements[i] for i in indices), default=None)
    return {"per_position": values, "summary": summary, "logit_row_semantics": "Row i predicts input token i+1; last row predicts beyond the frozen trajectory."}


def local_difference(actual, base, ideal):
    """Subtract outputs in FP32; compare with the same-state intended increment."""
    actual_delta = actual.float() - base.float()
    ideal = ideal.float()
    error = actual_delta - ideal
    ideal_norm = ideal.norm(dim=-1)
    assert (ideal_norm > 0).all()
    return {"actual_increment_norm": actual_delta.norm(dim=-1).cpu().tolist(),
            "intended_increment_norm": ideal_norm.cpu().tolist(),
            "error_norm": error.norm(dim=-1).cpu().tolist(),
            "relative_error": (error.norm(dim=-1) / ideal_norm).cpu().tolist()}


def forward_with_local_audit(engine, tokens, arm, calibration):
    torch = engine.torch
    inputs = engine._inputs([tokens])
    locals_, incoming, handles = {}, {}, []
    intended = {}
    for layer in LAYERS:
        norm = float(engine.column_norms[str(layer)][SOURCE_NEURONS[layer]])
        column = engine.modules[layer].weight[:, SOURCE_NEURONS[layer]].float()
        intended[layer] = SIGNS[layer] * column / norm * calibration["residual_scales"][str(layer)]
    if str(engine.device).startswith("cuda"):
        torch.cuda.synchronize(engine.device)
    started = time.monotonic()
    with torch.inference_mode(), engine._intervention(arm, [calibration], inputs["attention_mask"]):
        try:
            for layer in LAYERS:
                if arm == "S_channel":
                    def before(_module, args, layer=layer):
                        incoming[layer] = args[0].detach().clone()
                    def after(module, _args, output, layer=layer):
                        # The unedited linear output is recomputed at the *same* incoming
                        # gated activation. At L14, the full preceding B intervention is on.
                        base = torch.nn.functional.linear(incoming[layer], module.weight, module.bias)
                        ideal = intended[layer].expand(output.shape[1], -1)
                        amount = (SIGNS[layer] * calibration["residual_scales"][str(layer)] /
                                  float(engine.column_norms[str(layer)][SOURCE_NEURONS[layer]]))
                        n = SOURCE_NEURONS[layer]
                        natural = incoming[layer][0, :, n]
                        edited = natural + module.weight.new_tensor(amount)
                        locals_[str(layer)] = {"operation": "down_proj_same_incoming_activation",
                            "preceding_B_active": layer == 14,
                            "activation_dtype": str(incoming[layer].dtype), "output_dtype": str(output.dtype),
                            "offset_before_bf16_cast": amount,
                            "offset_after_bf16_cast": float(module.weight.new_tensor(amount)),
                            "activation_increment": (edited.float() - natural.float()).cpu().tolist(),
                            **local_difference(output[0], base[0], ideal)}
                        del incoming[layer]
                    handles.append(engine.modules[layer].register_forward_pre_hook(before, prepend=True))
                    handles.append(engine.modules[layer].register_forward_hook(after))
                else:
                    def before_vector(_module, _args, output, layer=layer):
                        residual = output[0] if isinstance(output, tuple) else output
                        incoming[layer] = residual.detach().clone()
                    def after_vector(_module, _args, output, layer=layer):
                        residual = output[0] if isinstance(output, tuple) else output
                        ideal = intended[layer].expand(residual.shape[1], -1)
                        locals_[str(layer)] = {"operation": "layer_end_same_incoming_residual",
                            "preceding_B_active": layer == 14,
                            "residual_dtype": str(residual.dtype), "intended_increment_dtype": str(ideal.dtype),
                            **local_difference(residual[0], incoming[layer][0], ideal)}
                        del incoming[layer]
                    handles.append(engine.layers[layer].register_forward_hook(before_vector, prepend=True))
                    handles.append(engine.layers[layer].register_forward_hook(after_vector))
            output = engine.model(**inputs, use_cache=False, logits_to_keep=0)
            logits = output.logits[0].detach()
        finally:
            for handle in handles:
                handle.remove()
    if str(engine.device).startswith("cuda"):
        torch.cuda.synchronize(engine.device)
    assert logits.shape[0] == len(tokens) and set(locals_) == {"13", "14"}
    return logits, locals_, time.monotonic() - started


def run(args):
    data = args.data / "dev.jsonl"
    trajectories = rows(data)
    assert len(trajectories) == 48
    assert Counter(row["family"] for row in trajectories) == {"baseline": 24, "modified": 24}
    assert {row["question_id"] for row in trajectories} == {f"Q{i:02d}" for i in range(1, 25)}
    output = args.output
    output.mkdir(parents=True, exist_ok=False)
    receipt_path = output / "receipt.json"
    started = time.monotonic()
    receipt = {"status": "started", "started_utc": utc(), "expected_trajectories": 48,
               "expected_full_forwards": 96, "completed_trajectories": 0, "full_forwards": 0,
               "calibration_forwards": 0, "data_sha256": sha(data),
               "source_sha256": {name: sha(Path(__file__).with_name(name)) for name in ("source_bridge.py", "transfer_engine.py")},
               "scope": "Numerical implementation bridge only; no clamp, gradients, path search or new generation.",
               "local_linear_recomputations_per_channel_forward": 2}
    write(receipt_path, receipt)
    try:
        engine = TransferEngine(args.model, device=args.device)
        engine.conditions.update(engine.source_bundle()["conditions"])
        receipt["engine"] = engine.metadata
        calibrations, metadata = {}, []
        for index, row in enumerate(trajectories):
            question = row["question_id"]
            prompt, prefix, answer = row["prompt_rendered"], row["prompt_token_ids"], row["answer_token_ids"]
            assert encode_text(engine.tokenizer, prompt) == prefix
            assert answer == trim_at_first_eos(answer) and len(answer) <= 512
            tokens = prefix + answer
            assert len(tokens) <= engine.max_length
            if question not in calibrations:
                calibrations[question] = engine.calibrate([prompt])[0]
                receipt["calibration_forwards"] += 1
            calibration = calibrations[question]
            assert calibration["context_sha256"] == text_hash(prompt)
            assert calibration["input_token_sha256"] == token_hash(prefix)
            channel, local_channel, channel_seconds = forward_with_local_audit(engine, tokens, "S_channel", calibration)
            receipt["full_forwards"] += 1
            vector, local_vector, vector_seconds = forward_with_local_audit(engine, tokens, "S_vector", calibration)
            receipt["full_forwards"] += 1
            comparison = compare_logits(channel, vector, len(prefix))
            del channel, vector
            result = {"id": row["id"], "question_id": question, "family": row["family"],
                "input_token_sha256": token_hash(tokens), "prompt_token_count": len(prefix),
                "answer_token_count": len(answer), "total_token_count": len(tokens),
                "calibration": calibration, "channel_local": local_channel, "vector_local": local_vector,
                "comparison": comparison, "channel_forward_seconds": channel_seconds,
                "vector_forward_seconds": vector_seconds, "source_data_row_sha256":
                    hashlib.sha256(json.dumps(row, ensure_ascii=False, sort_keys=True).encode()).hexdigest()}
            path = output / f"{index:03d}-{row['id']}.json"
            write(path, result)
            metadata.append({"file": path.name, "sha256": sha(path), "family": row["family"],
                             "question_id": question, "total_token_count": len(tokens),
                             "summary": comparison["summary"]})
            receipt.update(completed_trajectories=len(metadata), last_id=row["id"], elapsed_seconds=time.monotonic() - started)
            write(receipt_path, receipt)
            print(json.dumps({"phase": "source_bridge", "completed": len(metadata), "total": 48,
                              "id": row["id"], "seconds": channel_seconds + vector_seconds}), flush=True)
        assert receipt["full_forwards"] == 96 and receipt["calibration_forwards"] == 24
        receipt.update(engine.verify_unchanged())
        assert sha(data) == receipt["data_sha256"]
        for name, digest in receipt["source_sha256"].items():
            assert sha(Path(__file__).with_name(name)) == digest
        write(output / "index.json", metadata)
        receipt.update(status="completed", index_sha256=sha(output / "index.json"))
    except Exception as error:
        receipt.update(status="failed", error=str(error), traceback=traceback.format_exc())
        raise
    finally:
        receipt.update(ended_utc=utc(), elapsed_seconds=time.monotonic() - started)
        write(receipt_path, receipt)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--device", default="cuda:0")
    run(parser.parse_args())
