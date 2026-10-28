"""CPU-only timing and storage scenarios from verified, bounded preflight evidence."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import statistics

import experiment as ex

STAGES = ("development", "mechanism_development", "patch_development", "confirmation",
          "mechanism_confirmation", "patch_confirmation")
SCIENTIFIC_COUNTS = dict(zip(STAGES, (4632, 1536, 768, 3480, 1152, 576)))
FAMILIES = ("reading", "arithmetic", "relation")
GIB = 1024 ** 3


def numbers(value):
    if isinstance(value, dict):
        return [n for item in value.values() for n in numbers(item)]
    if isinstance(value, (tuple, list)):
        return [n for item in value for n in numbers(item)]
    return [float(value)] if isinstance(value, (int, float)) and not isinstance(value, bool) else []


def mean(values, default=0.):
    values = list(values)
    return statistics.fmean(values) if values else default


def json_bytes(value):
    return len(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False).encode())


def window(layer):
    return "early" if layer < 4 else "middle" if layer < 16 else "late"


def dimensions(condition, family):
    dose = condition.get("dose", 0.)
    return {"kind": condition["kind"], "window": window(condition["layer"]) if "layer" in condition else "none",
            "sign": -1 if dose < 0 else 1 if dose > 0 else 0, "dose": abs(dose), "family": family}


def role_of(name, row):
    out = row.get("output", {})
    if out.get("patch_audit"):
        return "patch"
    if name.startswith("fork-"):
        return "branch_" + out.get("branch_kind", "unknown")
    if row.get("mode", "full") != "full":
        return row["mode"]
    return "full"


def load_worker(path):
    """Only call after experiment.verify_worker has accepted these files."""
    path = Path(path)
    receipt, preflight = ex.read(path / "receipt.json"), ex.read(path / "preflight.json")
    saves = preflight.get("save_seconds_by_record", {})
    average_save = mean(numbers(saves), None)
    samples, all_model_seconds = [], 0.
    for relative in receipt["record_hashes"]:
        row = ex.read(path / relative)
        if "legacy_output" in row:
            all_model_seconds += row["legacy_output"].get("batch_seconds", 0.)
        if "incremental" in row:
            all_model_seconds += row["incremental"].get("seconds", 0.)
        out = row.get("output")
        if not out or out.get("status") != "completed":
            continue
        choices = row.get("choices", [])
        generation_seconds = float(out["seconds"])
        candidate_seconds = sum(c["seconds"] for c in choices)
        all_model_seconds += generation_seconds + candidate_seconds
        name = Path(relative).stem
        save_seconds = saves.get(relative, saves.get(name, average_save)) if isinstance(saves, dict) else average_save
        actual_bytes = (path / relative).stat().st_size
        generation_bytes, candidate_bytes = json_bytes(out), json_bytes(choices)
        sample = {**dimensions(row["condition"], row["item"]["family"]), "base_id": row["item"]["base_id"],
            "role": role_of(name, row), "benchmark": relative in preflight["benchmark_records"],
            "tokens": out["generated_token_count"], "generation_seconds": generation_seconds,
            "candidate_seconds": candidate_seconds, "candidate_count": len(choices),
            "other_seconds": max(0., row["wall_seconds"] - generation_seconds - candidate_seconds),
            "save_seconds": save_seconds, "bytes": actual_bytes, "generation_bytes": generation_bytes,
            "candidate_bytes": candidate_bytes,
            "envelope_bytes": max(0, actual_bytes - generation_bytes - candidate_bytes)}
        assert sample["tokens"] > 0 and generation_seconds > 0
        samples.append(sample)
    assert sum(s["benchmark"] for s in samples) == 60
    donor_seconds = numbers(preflight["donor_replay_seconds"])
    calibration_table = preflight.get("calibration_seconds_by_base", {})
    calibration_seconds = numbers(calibration_table)
    calibration_families = {family: [float(value) for base, value in calibration_table.items()
        if base.startswith(prefix)] for family, prefix in
        (("reading", "RD"), ("arithmetic", "AR"), ("relation", "RL"), ("open", "Q"))}
    donor_paths = [path / name for name in receipt["asset_hashes"] if name.startswith("donors/")]
    donor_metadata = [a["donor_metadata"] for relative in receipt["record_hashes"]
                      for a in ex.read(path / relative).get("output", {}).get("patch_audit", [])]
    unknown = []
    if average_save is None:
        unknown.append("record_serialization_write_and_hash_seconds_not_separately_measured")
    if not calibration_seconds:
        unknown.append("clean_calibration_seconds_not_separately_measured")
    if not preflight.get("donor_save_seconds"):
        unknown.append("donor_tensor_serialization_seconds_not_separately_measured")
    known = (receipt["load_and_identity_seconds"] + all_model_seconds + sum(donor_seconds)
             + sum(calibration_seconds) + sum(numbers(saves)) + sum(numbers(preflight.get("donor_save_seconds", {}))))
    return {"samples": samples, "load_seconds": receipt["load_and_identity_seconds"],
        "calibration_seconds_per_base": mean(calibration_seconds, None),
        "calibration_seconds_by_family": calibration_families,
        "save_seconds_per_record": average_save,
        "donor_seconds_at_preflight_step": mean(donor_seconds), "donor_prediction_step_observed": 0,
        "donor_save_seconds": mean(numbers(preflight.get("donor_save_seconds", {})), None),
        "donor_archive_bytes": mean(p.stat().st_size for p in donor_paths) + mean(json_bytes(m) for m in donor_metadata),
        "unattributed_preflight_seconds": max(0., receipt["wall_seconds"] - known),
        "unknown_overheads": unknown, "receipt_sha256": ex.sha(path / "receipt.json")}


def pool(samples, request, role="full"):
    selected = [s for s in samples if (s["benchmark"] if role == "full" else s["role"] == role)]
    if not selected:
        selected = [s for s in samples if s["role"] == role]
    assert selected, f"No measured evidence for role {role}"
    levels = (("kind", "window", "sign", "dose", "family"),
              ("kind", "window", "sign", "dose"), ("kind", "window", "family"),
              ("kind", "window"), ("kind", "family"), ("kind",), ("family",), ())
    # Full-grid clean has no benchmark; use its actual technical clean controls.
    if request.get("kind") == "clean" and role == "full":
        selected = [s for s in samples if s["kind"] == "clean" and s["role"] == "full"]
        assert selected
    for keys in levels:
        chosen = [s for s in selected if all(s[k] == request.get(k) for k in keys)]
        if len(chosen) >= 2 or (not keys and chosen):
            return chosen, {"matching": list(keys), "sample_rows": len(chosen),
                            "base_scenarios": len({s["base_id"] for s in chosen}), "role": role}
    raise AssertionError("No timing pool")


def sample_cost(profile, request, role, has_candidates, all_128):
    rows, evidence = pool(profile["samples"], request, role)
    token_seconds = sum(r["generation_seconds"] for r in rows) / sum(r["tokens"] for r in rows)
    generation = token_seconds * 128 if all_128 else mean(r["generation_seconds"] for r in rows)
    candidates = [r for r in profile["samples"] if r["candidate_count"] == 2 and r["family"] == request["family"]]
    if has_candidates:
        assert candidates, f"No candidate timings for {request['family']}"
    candidate = mean(r["candidate_seconds"] for r in candidates) if has_candidates else 0.
    candidate_bytes = mean(r["candidate_bytes"] for r in candidates) if has_candidates else 0.
    generation_bytes = (sum(r["generation_bytes"] for r in rows) / sum(r["tokens"] for r in rows) * 128
                        if all_128 else mean(r["generation_bytes"] for r in rows))
    return {"generation_seconds": generation, "candidate_seconds": candidate,
            "validation_and_python_seconds": mean(r["other_seconds"] for r in rows),
            "save_seconds": mean((r["save_seconds"] for r in rows if r["save_seconds"] is not None), 0.),
            "output_bytes": generation_bytes + candidate_bytes + mean(r["envelope_bytes"] for r in rows)}, evidence


def requests(stage, gpu):
    if stage in ("development", "confirmation"):
        for item in ex.assigned(ex.items(stage), gpu):
            for condition in ex.conditions(stage):
                yield {"dimensions": dimensions(condition, item["family"]), "role": "full", "count": 1,
                       "candidates": True, "scientific": True, "technical": None}
        return
    families = FAMILIES + (("open",) if stage.endswith("development") else ())
    for family in families:
        # Six locked conditions and four inputs per family/worker at the maximum scope.
        dim = {"family": family, "kind": "native"}
        if stage.startswith("mechanism"):
            for mode, count in (("full", 24), ("prefill", 24), ("decode", 24),
                                ("prompt_last", 12), ("prompt_except_last", 12),
                                ("branch_withdraw", 48), ("branch_rebuild", 48), ("branch_continue", 48)):
                yield {"dimensions": dim, "role": mode, "count": count,
                       "candidates": family != "open" and mode in ("full", "prefill", "decode", "prompt_last", "prompt_except_last"),
                       "scientific": mode != "branch_continue", "technical": "continue_replay" if mode == "branch_continue" else None}
        else:
            yield {"dimensions": dim, "role": "patch", "count": 64, "candidates": False,
                   "scientific": True, "technical": None}
            yield {"dimensions": {**dim, "kind": "clean"}, "role": "patch", "count": 32, "candidates": False,
                   "scientific": True, "technical": None}
            yield {"dimensions": dim, "role": "full", "count": 16, "candidates": False,
                   "scientific": False, "technical": "patch_source_replay"}


def donor_timing(profile, donor_count, all_128):
    prefill = profile["donor_seconds_at_preflight_step"]
    if not all_128 or not donor_count:
        return donor_count * prefill, {"mode": "observed_step_zero_donor", "seconds_per_donor": prefill}
    total, evidence = 0., []
    # Six patch arms use four clean donors and two treated donors. One prefill per replay.
    for kind, fraction in (("clean", 2/3), ("native", 1/3)):
        rows = [r for r in profile["samples"] if r["kind"] == kind and r["role"] == "full"
                and (r["benchmark"] or kind == "clean")]
        assert rows, f"No same-kind donor timing proxy: {kind}"
        longer = [r for r in rows if r["tokens"] > 1]
        increments = sum(r["tokens"] - 1 for r in longer)
        tail_seconds = sum(r["generation_seconds"] - prefill for r in longer)
        if increments and tail_seconds > 0:
            rate = tail_seconds / increments
            method = "same_kind_generation_minus_pooled_donor_prefill_over_incremental_tokens"
        else:
            rate = sum(r["generation_seconds"] for r in rows) / sum(r["tokens"] for r in rows)
            method = "fallback_same_kind_amortized_generation_seconds_per_token"
        seconds = prefill + 127 * rate
        total += donor_count * fraction * seconds
        evidence.append({"kind": kind, "donor_fraction": fraction, "prefill_seconds": prefill,
            "incremental_seconds_per_token_proxy": rate, "seconds_per_128_position_donor": seconds,
            "method": method, "sample_rows": len(rows)})
    return total, {"mode": "one_measured_prefill_plus_127_estimated_increments", "pools": evidence,
                   "measured_long_donor": False, "hard_upper_bound": False}


def estimate_worker(profile, jobs, *, all_128=False, base_count=6, donor_count=0):
    totals = Counter(scientific_generations=0, technical_replay_generations=0, candidate_groups=0)
    pools = {}
    for job in jobs:
        cost, evidence = sample_cost(profile, job["dimensions"], job["role"], job["candidates"], all_128)
        for key, value in cost.items():
            totals[key] += value * job["count"]
        totals["scientific_generations" if job["scientific"] else "technical_replay_generations"] += job["count"]
        totals["candidate_groups"] += job["count"] if job["candidates"] else 0
        key = json.dumps({"request": job["dimensions"], **evidence}, sort_keys=True)
        pools.setdefault(key, {"request": job["dimensions"], **evidence, "projected_records": 0})["projected_records"] += job["count"]
    totals["candidate_continuations"] = totals["candidate_groups"] * 2
    totals["load_and_identity_seconds"] = profile["load_seconds"]
    calibration_families = profile.get("calibration_seconds_by_family", {})
    totals["calibration_seconds"] = sum(2 * mean(calibration_families.get(family, []),
        profile["calibration_seconds_per_base"] or 0.) for family in FAMILIES)
    if base_count > 6:
        totals["calibration_seconds"] += (base_count - 6) * mean(calibration_families.get("open", []),
            profile["calibration_seconds_per_base"] or 0.)
    totals["donor_replays"] = donor_count
    # Donor preflight only measured prediction step zero. This is a scenario, not an actual selected patch cost.
    totals["donor_seconds"], donor_evidence = donor_timing(profile, donor_count, all_128)
    totals["donor_save_seconds"] = donor_count * (profile["donor_save_seconds"] or 0.)
    totals["donor_archive_bytes"] = donor_count * profile["donor_archive_bytes"]
    totals["output_bytes"] += totals["donor_archive_bytes"]
    time_keys = ("generation_seconds", "candidate_seconds", "validation_and_python_seconds", "save_seconds",
                 "load_and_identity_seconds", "calibration_seconds", "donor_seconds", "donor_save_seconds")
    totals["known_wall_seconds"] = sum(totals[k] for k in time_keys)
    return {**dict(totals), "pools": list(pools.values()), "donor_timing_evidence": donor_evidence,
        "unknown_overheads": profile["unknown_overheads"] + ["final_weight_verification_and_export_not_timed_separately"],
        "preflight_unattributed_seconds_not_scaled": profile["unattributed_preflight_seconds"]}


def estimate(profiles, *, completed_stages=(), server_free_gib=None, local_free_gib=None):
    assert set(completed_stages) <= set(STAGES) and len(profiles) == 2
    scenarios = {}
    for name, all_128 in (("observed_preflight_lengths", False), ("all_remaining_generation_streams_128", True)):
        stages, total_seconds, output_bytes = {}, 0., 0.
        for stage in STAGES:
            if stage in completed_stages:
                stages[stage] = {"status": "already_completed_not_counted", "remaining_generations": 0,
                                 "known_wall_seconds": 0., "output_bytes": 0.}
                continue
            workers = []
            for gpu, profile in enumerate(profiles):
                jobs = list(requests(stage, gpu))
                assert sum(j["count"] for j in jobs if j["scientific"]) == SCIENTIFIC_COUNTS[stage] // 2
                bases = 10 if stage.endswith("development") and stage != "development" else 6
                donors = (384 if stage.endswith("development") else 288) if stage.startswith("patch") else 0
                workers.append(estimate_worker(profile, jobs, all_128=all_128, base_count=bases, donor_count=donors))
            wall = max(w["known_wall_seconds"] for w in workers)
            size = sum(w["output_bytes"] for w in workers)
            stages[stage] = {"status": "fixed_grid_scenario" if stage in ("development", "confirmation") else "unselected_maximum_workload_scenario",
                "scientific_generations": SCIENTIFIC_COUNTS[stage], "workers": workers,
                "known_wall_seconds": wall, "output_bytes": size}
            total_seconds += wall
            output_bytes += size
        anchor_costs = [sample_cost(profile, {"kind": "clean", "family": "open"}, "full", False, all_128)[0]
                        for profile in profiles]
        anchor_seconds = max(4 * sum(v for k, v in cost.items() if k.endswith("seconds")) for cost in anchor_costs)
        scenarios[name] = {"stages": stages, "known_compute_setup_and_measured_io_seconds": total_seconds,
            "known_hours": total_seconds / 3600, "projected_raw_evidence_gib": output_bytes / GIB,
            "optional_eight_anchor_clean_if_not_reused": {"additional_generations": 8,
                "additional_parallel_known_seconds": anchor_seconds,
                "additional_raw_bytes": sum(4 * c["output_bytes"] for c in anchor_costs),
                "included_in_total": False, "assumption": "run in the mechanism stage, without an extra model load"},
            "server_free_gib": server_free_gib, "local_free_gib": local_free_gib,
            "server_raw_space_sufficient_under_scenario": None if server_free_gib is None else output_bytes / GIB <= server_free_gib,
            "local_raw_archive_sufficient_under_scenario": None if local_free_gib is None else output_bytes / GIB <= local_free_gib}
    return {"schema": 1, "created_at": datetime.now(timezone.utc).isoformat(), "status": "timing_scenarios_from_verified_preflight",
        "scientific_counts": SCIENTIFIC_COUNTS, "maximum_scientific_generations": sum(SCIENTIFIC_COUNTS.values()),
        "optional_anchor_clean_generations": 8, "completed_stages_excluded": list(completed_stages),
        "scenarios": scenarios,
        "assumptions_and_limits": [
            "Each stage runs two base-partitioned workers in parallel; stage time is their maximum, stages add serially.",
            "Formal jobs are not authorized or started by this estimator. Mechanism/patch conditions and sites are not selected.",
            "New confirmation structures use development family timing proxies; no confirmation model output was opened.",
            "Sparse pools merge family or dose only as the per-pool matching fields explicitly report; counts are not confidence intervals.",
            "Observed-length estimates assume future lengths resemble measured pools; depth, facts and selected abnormal conditions can change them.",
            "All-128 uses pooled observed generation seconds/token including prefill; it is neither a confidence bound nor a hard upper bound.",
            "Branch output.seconds already includes forced-prefix reconstruction. Continue validation is extra technical computation, not extra scientific answers.",
            "No full-generation reuse or unreachable branch/patch discounts are assumed; NA is retained, not treated as technical failure.",
            "Every patch arm prepares its own donor. Main donor scenario assumes measured step zero. Long donors use one pooled measured donor prefill plus 127 same-kind generation increments, estimated after subtracting the pooled prefill proxy; unavailable increments fall back to amortized generation seconds/token. This is not a measured long-donor time or upper bound.",
            "Patch source full replays are additional computation. No arbitrary safety multiplier is applied.",
            "Timing excludes review waiting, human/model-assisted reading, transfers, export, and unmeasured final verification; no ETA invented for them.",
            "Storage estimates use actual record bytes, separate candidate and donor bytes; HTML/export duplication and review artifacts remain unmeasured.",
            "Server and local capacities are evaluated separately; filesystem aliases must not be summed."]}


def verified_profiles(run):
    run = Path(run)
    controller, verification = ex.read(run / "controller.json"), ex.read(run / "verification.json")
    execution = ex.read(run / "execution.json")
    assert controller["status"] == "completed" and verification["status"] == "passed"
    assert controller["stage"] == execution["stage"] == "preflight"
    for key in ("freeze_sha256", "authorization_sha256", "pid", "started_at"):
        assert controller[key] == execution[key]
    assert verification["freeze_sha256"] == controller["freeze_sha256"]
    profiles = []
    for gpu in (0, 1):
        assert controller["workers"][str(gpu)]["returncode"] == 0
        ex.verify_worker(run / f"worker-{gpu}")
        profiles.append(load_worker(run / f"worker-{gpu}"))
    return profiles


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("run", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--completed-stage", action="append", default=[], choices=STAGES)
    parser.add_argument("--server-free-gib", type=float)
    parser.add_argument("--local-free-gib", type=float)
    args = parser.parse_args()
    profiles = verified_profiles(args.run)
    result = estimate(profiles, completed_stages=args.completed_stage,
        server_free_gib=args.server_free_gib, local_free_gib=args.local_free_gib)
    result["source"] = {"run": str(args.run.resolve()), "controller_sha256": ex.sha(args.run / "controller.json"),
        "verification_sha256": ex.sha(args.run / "verification.json"),
        "worker_receipt_sha256": [p["receipt_sha256"] for p in profiles]}
    ex.write(args.output, result, immutable=True)
    print(json.dumps({"output": str(args.output), "maximum_scientific_generations": result["maximum_scientific_generations"],
        "scenarios": {name: {k: v for k, v in value.items() if k != "stages"}
                      for name, value in result["scenarios"].items()}}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
