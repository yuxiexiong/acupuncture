"""Bounded root-cause stages. No model is loaded without an explicit launch record."""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import random
import statistics
import time
import traceback

from freeze import HERE, REPO, read, sha, verify, write
from metrics import candidate_comparisons, paired_effect, summarize
from prepare_data import functional_rows, read_rows

STAGES = ("preflight", "decompose", "rank", "validate", "function-dev", "confirm")
SIGN_BY_CONTENT_SLOT = [1, 1, -1, -1]


def utc():
    return datetime.now(timezone.utc).isoformat()


def digest(value):
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False).encode()
    return hashlib.sha256(raw).hexdigest()


def order(component):
    layer, kind = component.split(".")
    number = int(layer[1:])
    if kind not in ("attention", "mlp") or not (15 <= number <= 31 or (number == 14 and kind == "attention")):
        raise ValueError("Only declared downstream module contributions are available")
    return number, int(kind == "mlp")


def random_pairs(contract):
    rng = random.Random(contract["random_seed"])
    excluded = {13: 7956, 14: 8949}
    pools = {layer: [i for i in range(contract["source"]["intermediate_size"])
                     if i != excluded[layer]] for layer in excluded}
    draws = {layer: rng.sample(pool, contract["random_pairs"]) for layer, pool in pools.items()}
    return [{layer: values[i] for layer, values in draws.items()} for i in range(contract["random_pairs"])]


def conditions(engine, contract):
    result = {"clean": engine.make_condition("clean")}
    pairs = random_pairs(contract)
    for dose in contract["diagnostic_doses"]:
        for name in ("A", "B", "AB"):
            result[f"{name}_d{dose:g}"] = engine.make_condition(name, dose)
        for index, pair in enumerate(pairs, 1):
            name = f"R{index:02d}"
            result[f"{name}_d{dose:g}"] = engine.make_condition(name, dose, random_pair=pair)
    return result


def completed_receipt(path, stage, freeze_sha):
    path = Path(path)
    result = read(path)
    if result.get("status") != "completed" or result.get("stage") != stage:
        raise ValueError(f"Need a completed {stage} receipt")
    if result.get("freeze_sha256") != freeze_sha:
        raise ValueError("Prior stage belongs to another frozen implementation")
    for name, expected in result["files"].items():
        relative = Path(name)
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("Unsafe receipt file path")
        if sha(path.parent / relative) != expected:
            raise ValueError(f"Prior-stage evidence changed: {relative}")
    return result


def check_launch(path, contract):
    value = read(path)
    if value.get("status") != "authorized" or value.get("experiment") != contract["experiment"]:
        raise ValueError("A separate user launch authorization is required")
    if not value.get("user_instruction") or not value.get("granted_at"):
        raise ValueError("Launch record must preserve the actual user instruction and time")
    return value


def select_candidates(records, contract):
    groups = defaultdict(lambda: defaultdict(list))
    counts = Counter(row["benchmark"] for row in records)
    if len({row["id"] for row in records}) != len(records):
        raise ValueError("Duplicate question in ranking evidence")
    for row in records:
        for candidate in row["ranking"]:
            if candidate["active_position_count"]:
                key = candidate["component"], candidate["positions"]
                groups[row["benchmark"]][key].append(candidate["predicted_repair"])
    rankings = {task: sorted(values, key=lambda key: (-sum(values[key]) / counts[task], key))
                for task, values in groups.items()}
    if set(rankings) != {"mmlu", "arc_challenge"}:
        raise ValueError("Both tasks must contribute to candidate ranking")
    chosen, seen, cursors = [], set(), {task: 0 for task in rankings}
    while len(chosen) < contract["candidate_budget"]["ranked"]:
        progress = False
        for task in ("mmlu", "arc_challenge"):
            while cursors[task] < len(rankings[task]) and rankings[task][cursors[task]] in seen:
                cursors[task] += 1
            if cursors[task] < len(rankings[task]):
                key = rankings[task][cursors[task]]
                cursors[task] += 1
                chosen.append((key, "ranked", task))
                seen.add(key)
                progress = True
            if len(chosen) == contract["candidate_budget"]["ranked"]:
                break
        if not progress:
            break
    remaining = sorted(set().union(*(set(group) for group in rankings.values())) - seen)
    audit = random.Random(contract["random_seed"] + 1).sample(
        remaining, min(contract["candidate_budget"]["audit"], len(remaining)))
    chosen.extend((key, "audit", None) for key in audit)
    return [{"id": f"C{i:02d}", "component": key[0], "positions": key[1], "selection": method,
             "selected_by_task": task, "control_seed": contract["random_seed"] + i,
             "prediction": "Limited clean contribution will improve AB; AB contribution will damage clean",
             "mean_predicted_repair": {t: sum(groups[t][key]) / counts[t] for t in rankings},
             "active_question_count": {t: len(groups[t][key]) for t in rankings},
             "question_denominator": dict(counts)}
            for i, (key, method, task) in enumerate(chosen, 1)]


def validate_explanations(value, candidates, final=False):
    if value.get("family") not in ("reading", "comparison", "reporting"):
        raise ValueError("Choose one bounded functional family")
    known = {candidate["id"]: candidate for candidate in candidates}
    entries = value.get("explanations", [])
    if not 1 <= len(entries) <= 2 or len({entry["candidate_id"] for entry in entries}) != len(entries):
        raise ValueError("Freeze one or two distinct tested explanations")
    for entry in entries:
        candidate = known[entry["candidate_id"]]
        if candidate["positions"] != "prompt_last":
            raise ValueError("Single-label functional tasks cannot confirm an answer-tail-only explanation")
        if entry.get("candidate_sha256") != digest(candidate):
            raise ValueError("Explanation changed the selected candidate")
        for field in ("hypothesis", "task_relation", "expected_direction", "falsifier"):
            if not entry.get(field):
                raise ValueError(f"Missing explicit scientific prediction: {field}")
        reader = entry["reader"]
        if order(reader["component"]) <= order(candidate["component"]):
            raise ValueError("Reader must be downstream and not directly patched")
        if reader["positions"] != "prompt_last":
            raise ValueError("Functional content readout is fixed at the shared prompt-last position")
        if not final and "projection" in reader:
            raise ValueError("Functional development must record vectors before fitting its frozen readout")
        if not final and "projection_source_sha256" in entry:
            raise ValueError("Development projection provenance is computed from the new recorded activations")
        if final:
            direction = reader["projection"]
            if len(direction) != 2560 or not all(math.isfinite(x) for x in direction):
                raise ValueError("Frozen reader direction must match 4B hidden size")
            norm = math.sqrt(sum(x*x for x in direction))
            if not .999 <= norm <= 1.001 or not entry.get("projection_source_sha256"):
                raise ValueError("Reader direction lacks a normalized development source")
    return entries


def projected_observation(output, reader):
    # All functional continuations are single labels. Choice zero is used once;
    # duplicate identical prompt positions do not create extra statistical units.
    observed = output["observations"][0][reader["component"]]
    if len(observed["values"]) != 1:
        raise ValueError("Functional reader must measure one fixed prompt position")
    value = observed["values"][0]
    if isinstance(value, list):
        return sum(a*b for a, b in zip(value, reader["projection"]))
    return float(value)


def fit_reader(records, reader):
    positive, negative = [], []
    for row in records:
        if row["demand"] != "required":
            continue
        vector = row["conditions"]["clean"]["observations"][0][reader["component"]]["values"][0]
        (positive if SIGN_BY_CONTENT_SLOT[row["content_slot"]] > 0 else negative).append(vector)
    if not positive or len(positive) != len(negative):
        raise ValueError("Development content slots must be balanced")
    direction = [statistics.mean(v[i] for v in positive) - statistics.mean(v[i] for v in negative)
                 for i in range(len(positive[0]))]
    norm = math.sqrt(sum(x*x for x in direction))
    if norm <= 1e-12:
        raise ValueError("No measurable development content contrast; do not invent a readout")
    return [x / norm for x in direction]


def check_patch_output(output, expected_needles, item, condition):
    """Every real replacement must satisfy the same technical matching contract."""
    def fail(reason):
        error = ValueError(reason)
        error.evidence = {"item_id": item["id"], "condition": condition, "output": output}
        raise error
    audits = output.get("patch_audit", [])
    if len(audits) != len(item["continuations"]) or any(len(group) != 1 for group in audits):
        fail("Patch audit does not cover every continuation exactly once")
    for group in audits:
        audit = group[0]
        writes = audit["actual_source_writes"]
        if set(writes) != expected_needles or not audit["untouched_positions_identical"]:
            fail("Patch changed unselected positions or needle execution")
        if any(row["nonzero_positions"] <= 0 for row in writes.values()):
            fail("A required needle did not produce a measurable write")
        requested, actual = audit["requested_delta_norm"], audit["actual_delta_norm"]
        if len(requested) != len(actual):
            fail("Incomplete replacement norm audit")
        if any(not math.isfinite(x) for x in requested + actual):
            fail("Non-finite replacement norm")
        if any(not math.isclose(a, b, rel_tol=.03, abs_tol=1e-6) for a, b in zip(requested, actual)):
            fail("BF16 replacement exceeds the fixed 3% norm-matching tolerance")


def patched_conditions(engine, item, calibration, arms, candidate, reader=None, natural=False):
    capture = [reader] if reader else None
    outputs = {name: engine.score_item(item, arms[name], calibration, capture=capture)
               for name in ("clean", "AB_d1")}
    base = {"component": candidate["component"], "positions": candidate["positions"],
            "seed": candidate["control_seed"]}
    for label, recipient, donor, mode in (("repair", "AB_d1", "clean", "donor"),
            ("replay", "clean", "AB_d1", "donor"),
            ("control_repair", "AB_d1", "clean", "matched"),
            ("control_replay", "clean", "AB_d1", "matched")):
        patch = {**base, "donor_arm": arms[donor], "mode": mode}
        outputs[label] = engine.score_item(item, arms[recipient], calibration, patch=patch, capture=capture)
        check_patch_output(outputs[label], {"13", "14"} if recipient == "AB_d1" else set(), item, label)
    if natural:
        for label, mode in (("natural_swap", "donor"), ("control_natural_swap", "matched")):
            patch = {**base, "donor_arm": arms["clean"], "mode": mode,
                     "donor_context": item["donor_context"], "require_same_input_length": True}
            outputs[label] = engine.score_item(item, arms["clean"], calibration, patch=patch, capture=capture)
            check_patch_output(outputs[label], set(), item, label)
        for output in outputs.values():
            output["donor_target_correct"] = int(output["prediction"] == item["donor_target_index"])
            output["donor_preference"] = output["scores"][item["donor_target_index"]] - output["scores"][item["target_index"]]
    return outputs


def row_envelope(item, calibration, outputs):
    result = {key: item[key] for key in ("id", "benchmark", "pair_id", "demand", "label_variant", "content_slot")
              if key in item}
    return {**result, "item_sha256": digest(item), "calibration": calibration, "conditions": outputs}


def evidence_manifest(output):
    return {str(path.relative_to(output)): sha(path) for path in sorted(output.rglob("*"))
            if path.is_file() and path.name != "receipt.json"}


def natural_summary(records):
    """Required-vs-direct interaction uses pairs, not duplicated label variants."""
    grouped = defaultdict(lambda: defaultdict(list))
    for row in records:
        grouped[row["pair_id"]][row["demand"]].append(row)
    interactions = []
    for identity, demands in grouped.items():
        if set(demands) != {"required", "direct"} or any(len(rows) != 2 for rows in demands.values()):
            raise ValueError("Natural test requires both demands and label variants for every pair")
        outputs = {}
        for mode in ("natural_swap", "control_natural_swap"):
            differences = {}
            for metric in ("correct", "margin"):
                damage = {demand: statistics.mean(row["conditions"]["clean"][metric] -
                                                 row["conditions"][mode][metric] for row in rows)
                          for demand, rows in demands.items()}
                differences[metric] = damage["required"] - damage["direct"]
            outputs[mode] = differences
        outputs["zero"] = {"correct": 0.0, "margin": 0.0}
        interactions.append({"id": identity, "benchmark": "functional_demand_interaction", "conditions": outputs})
    required = [row for row in records if row["demand"] == "required"]
    return {"demand_interaction": summarize(interactions,
                [("natural_required_minus_direct", "natural_swap", "zero"),
                 ("natural_interaction_vs_matched", "natural_swap", "control_natural_swap")]),
            "required_donor_preference": {
                "swap_vs_clean": paired_effect(required, "natural_swap", "clean", "donor_preference"),
                "swap_vs_control": paired_effect(required, "natural_swap", "control_natural_swap", "donor_preference")},
            "interpretation": "Natural-role evidence needs task dependence and donor-content response; this does not establish a unique module function."}


def run_preflight(engine, items, arms):
    findings = []
    for task in ("mmlu", "arc_challenge"):
        item = next(row for row in items if row["benchmark"] == task)
        calibration = engine.calibrate([item["context"]])[0]
        baseline = engine.score_item(item, arms["clean"], calibration)
        legacy = engine.score([item["context"]] * len(item["continuations"]), item["continuations"],
                              arms["clean"], [calibration] * len(item["continuations"]))
        from root_engine import encode_pair
        legacy_inputs = set()
        for continuation in item["continuations"]:
            prefix, suffix = encode_pair(engine.tokenizer, item["context"], continuation)
            legacy_inputs.add(tuple(prefix + suffix[:-1]))
        engine.counts["forward"] += len(legacy_inputs)
        engine.counts["legacy_scoring_forward"] = engine.counts.get("legacy_scoring_forward", 0) + len(legacy_inputs)
        deltas = [abs(a["loglikelihood"] - b["loglikelihood"])
                  for a, b in zip(baseline["choice_details"], legacy)]
        if max(deltas) > 1e-4:
            raise ValueError("Root likelihood differs from pinned transfer scoring")
        identity = engine.score_item(item, arms["clean"], calibration,
            patch={"component": "L15.attention", "positions": "prompt_last",
                   "donor_arm": arms["clean"], "mode": "donor"})
        if identity["scores"] != baseline["scores"]:
            raise ValueError("Identity contribution replacement changed scores")
        candidate = {"component": "L15.attention", "positions": "prompt_last", "control_seed": 20261026}
        changed = patched_conditions(engine, item, calibration, arms, candidate)
        for label in ("repair", "control_repair"):
            for audits in changed[label]["patch_audit"]:
                for audit in audits:
                    if set(audit["actual_source_writes"]) != {"13", "14"} or not audit["untouched_positions_identical"]:
                        raise ValueError("Scoped patch removed needles or changed other positions")
                    for expected, actual in zip(audit["requested_delta_norm"], audit["actual_delta_norm"]):
                        if not math.isclose(expected, actual, rel_tol=.03, abs_tol=1e-6):
                            raise ValueError("BF16 matched replacement exceeds 3% norm tolerance")
        ranking = engine.rank_item(item, calibration)
        if not ranking or not all(math.isfinite(row["predicted_repair"]) for row in ranking):
            raise ValueError("No finite gradient candidates")
        findings.append({"id": item["id"], "legacy_max_loglikelihood_difference": max(deltas),
                         "identity_exact": True, "finite_rank_entries": len(ranking),
                         "scoped_patch_audit": changed["control_repair"]["patch_audit"]})
    return findings


def run(args, engine_factory=None):
    contract = read(HERE / "contract.json")
    verify(args.freeze)
    freeze_sha = sha(args.freeze)
    if not args.execute:
        raise ValueError("No model action without --execute and a separate launch authorization")
    check_launch(args.launch_authorization, contract)
    priors = {}
    for path in args.prior:
        stage = read(path)["stage"]
        if stage in priors:
            raise ValueError("Ambiguous prior stage receipts")
        priors[stage] = (Path(path), completed_receipt(path, stage, freeze_sha))
    required = {"preflight": (), "decompose": ("preflight",), "rank": ("preflight", "decompose"),
                "validate": ("preflight", "rank"), "function-dev": ("preflight", "validate"),
                "confirm": ("preflight", "validate", "function-dev")}[args.stage]
    if any(stage not in priors for stage in required):
        raise ValueError(f"Missing completed prerequisite stage(s): {required}")
    if args.stage == "confirm" and not args.explanations:
        raise ValueError("Confirmation requires frozen explanations")
    dev = read_rows(HERE / "data/ability_dev.jsonl")
    if Counter(row["benchmark"] for row in dev) != contract["dev_counts"]:
        raise ValueError("Development count changed")
    candidates = []
    if args.stage in ("validate", "function-dev", "confirm"):
        origin = priors["rank"][0].parent if "rank" in priors else priors["validate"][0].parent
        candidates = read(origin / "candidates.json")
        if len(candidates) > contract["candidate_budget"]["total"]:
            raise ValueError("Candidate budget exceeded")
    explanation = read(args.explanations) if args.explanations else None
    entries = []
    if args.stage in ("function-dev", "confirm"):
        entries = validate_explanations(explanation, candidates, final=args.stage == "confirm")
        if explanation.get("validation_receipt_sha256") != sha(priors["validate"][0]):
            raise ValueError("Explanation is not bound to the completed development validation")
        if args.stage == "confirm":
            if explanation.get("function_dev_receipt_sha256") != sha(priors["function-dev"][0]):
                raise ValueError("Confirmation lacks its completed functional development source")
            if explanation.get("status") != "frozen_before_confirmation":
                raise ValueError("Explanations must be frozen before confirmation")
            expected = read(priors["function-dev"][0].parent / "explanations.frozen.json")
            # Receipt hash is inserted only after functional outputs are complete.
            expected["function_dev_receipt_sha256"] = sha(priors["function-dev"][0])
            if explanation != expected:
                raise ValueError("Frozen explanation differs from functional development output")
            if digest(functional_rows(explanation["family"])) != explanation["functional_data_sha256"]:
                raise ValueError("Confirmation functional questions changed after freezing")
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    receipt = {"stage": args.stage, "status": "running", "started_at": utc(),
               "freeze_sha256": freeze_sha, "authorization_sha256": sha(args.launch_authorization),
               "prerequisites": {stage: sha(path) for stage, (path, _) in priors.items()},
               "explanations_sha256": sha(args.explanations) if args.explanations else None,
               "model_loaded": False}
    write(output / "receipt.json", receipt)
    engine = None
    try:
        if engine_factory is None:
            from root_engine import RootEngine
            engine_factory = RootEngine
        engine = engine_factory(args.model, device=args.device, threads=contract["torch_threads"])
        receipt["model_loaded"] = True
        if engine.metadata["dtype"] != contract["source"]["dtype"]:
            raise ValueError("Unexpected model precision")
        for package in ("torch", "transformers"):
            if engine.metadata["versions"][package] != contract["source"][package + "_version"]:
                raise ValueError(f"Unvalidated {package} version")
        if engine.weight_hashes != contract["source"]["target_weight_sha256"]:
            raise ValueError("Source needle weights do not match the frozen 4B checkpoint")
        receipt["model_metadata"] = engine.metadata
        arms = conditions(engine, contract)
        calibration_cache = {}
        for prior_stage in ("decompose", "rank"):
            if prior_stage in priors:
                for path in priors[prior_stage][0].parent.glob("item-*.json"):
                    prior_row = read(path)
                    calibration_cache[prior_row["calibration"]["context_sha256"]] = prior_row["calibration"]
        def calibration_for(item):
            key = item["context_sha256"]
            if key not in calibration_cache:
                calibration_cache[key] = engine.calibrate([item["context"]])[0]
            return calibration_cache[key]
        write(output / "conditions.json", {"arms": arms, "random_pairs": random_pairs(contract)})
        if candidates:
            write(output / "candidates.json", candidates)
        if args.stage == "preflight":
            write(output / "checks.json", run_preflight(engine, dev, arms))
        elif args.stage in ("decompose", "rank"):
            records = []
            for number, item in enumerate(dev):
                calibration = calibration_for(item)
                if args.stage == "decompose":
                    values = {name: engine.score_item(item, arm, calibration) for name, arm in arms.items()}
                    row = row_envelope(item, calibration, values)
                else:
                    row = {"id": item["id"], "benchmark": item["benchmark"], "item_sha256": digest(item),
                           "calibration": calibration, "ranking": engine.rank_item(item, calibration)}
                write(output / f"item-{number:03d}.json", row)
                records.append(row)
            if args.stage == "rank":
                write(output / "candidates.json", select_candidates(records, contract))
            else:
                comparisons = [(name + "_damage", "clean", name) for name in arms if name != "clean"]
                comparisons.extend((f"AB_extra_damage_vs_{single}_d{dose:g}", f"{single}_d{dose:g}", f"AB_d{dose:g}")
                                   for dose in contract["diagnostic_doses"] for single in ("A", "B"))
                write(output / "summary.json", summarize(records, comparisons))
        else:
            selected = candidates if args.stage == "validate" else [
                next(row for row in candidates if row["id"] == entry["candidate_id"]) for entry in entries]
            if args.stage == "validate":
                sets = {"ability": dev}
            else:
                split = "dev" if args.stage == "function-dev" else "confirm"
                sets = {"functional": [row for row in functional_rows(explanation["family"]) if row["split"] == split]}
                if args.stage == "confirm":
                    sets["ability"] = read_rows(HERE / "data/ability_confirm.jsonl")
            final_explanation = json.loads(json.dumps(explanation)) if explanation else None
            for candidate in selected:
                entry = next((row for row in entries if row["candidate_id"] == candidate["id"]), None)
                folder = output / candidate["id"]
                folder.mkdir()
                for group, items in sets.items():
                    records = []
                    for number, item in enumerate(items):
                        calibration = calibration_for(item)
                        reader = entry["reader"] if entry and group == "functional" else None
                        values = patched_conditions(engine, item, calibration, arms, candidate,
                                                    reader=reader, natural=group == "functional")
                        row = row_envelope(item, calibration, values)
                        write(folder / f"{group}-{number:03d}.json", row)
                        records.append(row)
                    write(folder / f"{group}-summary.json", summarize(records, candidate_comparisons()))
                    if group == "functional":
                        if args.stage == "function-dev":
                            direction = fit_reader(records, entry["reader"])
                            frozen_entry = next(row for row in final_explanation["explanations"]
                                                if row["candidate_id"] == candidate["id"])
                            frozen_entry["reader"]["projection"] = direction
                            frozen_entry["projection_source_sha256"] = digest(records)
                            reader = frozen_entry["reader"]
                        else:
                            reader = entry["reader"]
                        readouts = []
                        for row in records:
                            values = {arm: SIGN_BY_CONTENT_SLOT[row["content_slot"]] * projected_observation(value, reader)
                                      for arm, value in row["conditions"].items()}
                            readouts.append({"id": row["id"], "pair_id": row["pair_id"],
                                "demand": row["demand"], "label_variant": row["label_variant"],
                                "content_slot": row["content_slot"], "signed_content_readout": values})
                        write(folder / "content-readouts.json", readouts)
                        readout_records = [{"id": row["id"], "pair_id": row["pair_id"],
                            "benchmark": "unpatched_content_relation",
                            "conditions": {arm: {"correct": float(value > 0), "margin": value}
                                           for arm, value in row["signed_content_readout"].items()}}
                                           for row in readouts]
                        write(folder / "content-relation-summary.json", {
                            "measure_names": {"correct": "positive_signed_readout_fraction", "margin": "signed_readout"},
                            "results": summarize(readout_records, candidate_comparisons()),
                            "boundary": "This frozen scalar is a task-content association independent of the report label; it is not a proof of a unique function."})
                        for label in (0, 1):
                            ids = {row["id"] for row in records if row["label_variant"] == label}
                            write(folder / f"label-{label}-summary.json", {
                                "task": summarize([row for row in records if row["id"] in ids], candidate_comparisons()),
                                "unpatched_content_relation": summarize(
                                    [row for row in readout_records if row["id"] in ids], candidate_comparisons()),
                                "boundary": "Inspect both fixed label arrangements; pooled improvement alone does not exclude report-label bias."})
                        write(folder / "natural-specificity-summary.json", natural_summary(records))
                        for demand in ("required", "direct"):
                            subset = [row for row in records if row["demand"] == demand]
                            write(folder / f"natural-{demand}-summary.json", summarize(subset,
                                [("natural_damage", "clean", "natural_swap"),
                                 ("natural_damage_vs_matched", "control_natural_swap", "natural_swap")]))
            if args.stage == "function-dev":
                final_explanation["status"] = "frozen_before_confirmation"
                final_explanation["content_sign_by_slot"] = SIGN_BY_CONTENT_SLOT
                final_explanation["functional_data_sha256"] = digest(functional_rows(explanation["family"]))
                write(output / "explanations.frozen.json", final_explanation)
        receipt["verification"] = engine.verify_unchanged()
        receipt["status"] = "completed"
    except Exception as exc:
        receipt["status"] = "failed"
        receipt["error"] = {"type": type(exc).__name__, "message": str(exc)}
        if hasattr(exc, "evidence"):
            write(output / "technical-failure-evidence.json", exc.evidence)
        (output / "failure.log").write_text(traceback.format_exc())
        raise
    finally:
        receipt["finished_at"] = utc()
        receipt["wall_seconds"] = time.monotonic() - started
        receipt["counts"] = engine.counts if engine is not None else {}
        receipt["files"] = evidence_manifest(output)
        write(output / "receipt.json", receipt)
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=STAGES, required=True)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--launch-authorization", type=Path)
    parser.add_argument("--freeze", type=Path, default=HERE / "freeze.json")
    parser.add_argument("--model", type=Path, default=Path("/data/models/Qwen3.5-4B-851bf6e"))
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--prior", type=Path, action="append", default=[])
    parser.add_argument("--explanations", type=Path)
    args = parser.parse_args()
    if not args.execute or args.launch_authorization is None:
        parser.error("Prepared code only. A user launch record and --execute are required before model loading.")
    result = run(args)
    print(json.dumps({"stage": result["stage"], "status": result["status"],
                      "wall_seconds": result["wall_seconds"]}))


if __name__ == "__main__":
    main()
