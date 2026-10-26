"""Freeze inputs without loading a model or consulting its answers."""
import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import random
import tarfile

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
SEED = 20261026
FAMILIES = ("reading", "comparison", "reporting")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_rows(path):
    raw = Path(path).read_bytes()
    if str(path).endswith(".gz"):
        raw = gzip.decompress(raw)
    return [json.loads(line) for line in raw.decode().split("\n") if line.strip()]


def save_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def save_rows(path, rows):
    path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows))


def exclusion_inventory(repo):
    """Read only IDs from archived output envelopes, including the stopped partial."""
    old = repo / "experiments/capability-damage-v2-2026-10-26"
    archive = old / "user-stop-20261026-r01/preserved-output-evidence.tar.gz"
    receipt = json.loads((archive.parent / "archive-manifest.json").read_text())
    if sha(archive) != receipt["archive_sha256"]:
        raise ValueError("Stopped-run archive hash changed")
    ids = set()
    completed, partial = 0, 0
    with tarfile.open(archive, "r:gz") as stream:
        for member in stream:
            if not member.isfile() or not member.name.startswith("outputs/"):
                continue
            if member.name.endswith(".jsonl"):
                rows = [json.loads(line) for line in stream.extractfile(member) if line.strip()]
                completed += len(rows)
            elif member.name.endswith(".partial.json"):
                rows = json.load(stream.extractfile(member))
                partial += len(rows)
            else:
                continue
            ids.update(row["id"] for row in rows)
    if completed != 10034 or partial != 1:
        raise ValueError("Unexpected historical exposure inventory; review before selection")
    evidence = {str(archive.relative_to(repo)): sha(archive)}
    v3 = repo / "experiments/capability-screen-v3-2026-10-26"
    panel = json.loads((v3 / "panel_manifest.json").read_text())
    evidence[str((v3 / "panel_manifest.json").relative_to(repo))] = sha(v3 / "panel_manifest.json")
    for task in ("mmlu", "arc_challenge"):
        ids.update(panel["selected_ids"][task])
    quick = repo / "experiments/qwen35-neuron-steering-2026-10-25/benchmark-quick-2026-10-26/items.json"
    quick_rows = json.loads(quick.read_text())
    ids.update(row["id"] for row in quick_rows)
    evidence[str(quick.relative_to(repo))] = sha(quick)
    return ids, {"evidence_files": evidence, "v2_completed": completed, "v2_partial": partial,
                 "excluded_policy": "All v2 completed/partial IDs, all scheduled v3 panel IDs (also reused by transfer), all quick-pilot IDs, and dev IDs",
                 "boundary": "Unexposed according to these archived project records; not a claim about unknown external runs or pretraining."}


def freeze_ability(repo=REPO, output=HERE / "data"):
    output.mkdir(parents=True, exist_ok=True)
    if (output / "ability_manifest.json").exists():
        raise ValueError("Existing frozen selection must not be overwritten")
    dev_source = repo / "experiments/transfer-toy-v1-2026-10-26/data/ability_diag.jsonl"
    dev = read_rows(dev_source)
    if Counter(row["benchmark"] for row in dev) != {"mmlu": 32, "arc_challenge": 32}:
        raise ValueError("Unexpected development panel")
    excluded, inventory = exclusion_inventory(repo)
    excluded.update(row["id"] for row in dev)
    source = repo / "experiments/capability-damage-v2-2026-10-26"
    source_manifest = json.loads((source / "task_manifest.json").read_text())
    confirm, pools = [], {}
    for task in ("mmlu", "arc_challenge"):
        path = source / "items" / (task + ".jsonl.gz")
        raw = gzip.decompress(path.read_bytes())
        if hashlib.sha256(raw).hexdigest() != source_manifest["files"][task]["sha256"]:
            raise ValueError("Pinned source item hash changed")
        pool = [json.loads(line) for line in raw.decode().split("\n") if line.strip()]
        available = sorted((row for row in pool if row["id"] not in excluded), key=lambda row: row["id"])
        selected = random.Random(f"{SEED}:root-confirm:{task}").sample(available, 32)
        confirm.extend(selected)
        pools[task] = {"source_count": len(pool), "available_count": len(available),
                       "source": str(path.relative_to(repo)), "source_sha256": sha(path),
                       "selected_ids": [row["id"] for row in selected]}
    for name, rows in (("ability_dev", dev), ("ability_confirm", confirm)):
        save_rows(output / f"{name}.jsonl", rows)
    save_rows(output / "excluded_ids.jsonl", [{"id": identity} for identity in sorted(excluded)])
    manifest = {"status": "frozen_before_root_cause_inference", "seed": SEED,
                "dev_source": str(dev_source.relative_to(repo)), "dev_source_sha256": sha(dev_source),
                "selection": "Sorted IDs, fixed task RNG; no correctness, output, length or target labels used",
                "confirm_source_split": "same pinned test splits; previously unrun remainder",
                "confirm_open_gate": "Frozen candidate/function contract required before confirm inference",
                "inventory": inventory, "pools": pools,
                "files": {name + ".jsonl": {"sha256": sha(output / (name + ".jsonl")), "count": count}
                          for name, count in (("ability_dev", 64), ("ability_confirm", 64), ("excluded_ids", len(excluded)))}}
    save_json(output / "ability_manifest.json", manifest)
    return manifest


def verify_ability(output=HERE / "data"):
    manifest = json.loads((output / "ability_manifest.json").read_text())
    rows = {}
    for filename, entry in manifest["files"].items():
        if sha(output / filename) != entry["sha256"]:
            raise ValueError(f"Frozen data changed: {filename}")
        rows[filename] = read_rows(output / filename)
        if len(rows[filename]) != entry["count"]:
            raise ValueError("Frozen data count mismatch")
    excluded = {row["id"] for row in rows["excluded_ids.jsonl"]}
    dev = {row["id"] for row in rows["ability_dev.jsonl"]}
    confirm = {row["id"] for row in rows["ability_confirm.jsonl"]}
    if len(dev) != 64 or len(confirm) != 64 or confirm & excluded or confirm & dev:
        raise ValueError("Confirmation uniqueness or exposure exclusion failed")
    for split in ("dev", "confirm"):
        items = rows[f"ability_{split}.jsonl"]
        if Counter(row["benchmark"] for row in items) != {"mmlu": 32, "arc_challenge": 32}:
            raise ValueError("Frozen benchmark split changed")
        if any(hashlib.sha256(row["context"].encode()).hexdigest() != row["context_sha256"] for row in items):
            raise ValueError("Context hash mismatch")
    return {"status": "passed", "dev": 64, "confirm": 64, "excluded_id_count": len(excluded),
            "confirm_excluded_overlap": 0, "confirm_dev_overlap": 0}


def functional_rows(family):
    """32 independent base pairs, each with demand/control and two labelings.

    Semantic answers/content vary across base pairs. Label identity is crossed
    within each pair. The 32 pairs, not the 128 items, are statistical units.
    """
    if family not in FAMILIES:
        raise ValueError("Choose exactly one declared function family")
    rows = []
    for number in range(32):
        pair_id = f"F-{family}-{number + 1:02d}"
        split = "dev" if number < 16 else "confirm"
        objects = [f"box{number + 1}x", f"box{number + 1}y", f"box{number + 1}z", f"box{number + 1}w"]
        values = [f"code{4 * number + j + 1}" for j in range(4)]
        target = number % 4
        counterfactual = (target + 1) % 4
        if family == "reading":
            facts = "; ".join(f"{name} contains {value}" for name, value in zip(objects, values)) + "."
            swapped = values.copy()
            swapped[target], swapped[counterfactual] = swapped[counterfactual], swapped[target]
            donor_facts = "; ".join(f"{name} contains {value}" for name, value in zip(objects, swapped)) + "."
            query = f"Which code is in {objects[target]}?"
            options, answer = values, values[target]
        elif family == "comparison":
            amounts = [10 + j for j in range(4)]
            amounts[target] = 20 + number
            facts = "; ".join(f"{name} has {amount} counters" for name, amount in zip(objects, amounts)) + "."
            swapped = amounts.copy()
            swapped[target], swapped[counterfactual] = swapped[counterfactual], swapped[target]
            donor_facts = "; ".join(f"{name} has {amount} counters" for name, amount in zip(objects, swapped)) + "."
            query = "Which box has the most counters?"
            options, answer = objects, objects[target]
        else:
            facts = f"Report north has answer {values[target]}; report south has answer {values[(target + 1) % 4]}."
            donor_facts = f"Report north has answer {values[counterfactual]}; report south has answer {values[target]}."
            query = "What answer is already given for report north?"
            options, answer = values, values[target]
        for label in (0, 1):
            order = list(range(4)) if label == 0 else [2, 3, 0, 1]
            listed = "\n".join(f"{chr(65 + j)}. {options[index]}" for j, index in enumerate(order))
            for demand in ("required", "direct"):
                instruction = query if demand == "required" else f"The answer is {answer}. Report that answer."
                context = f"Use only the supplied facts.\n{facts}\n{instruction}\n{listed}\nAnswer:"
                donor_context = f"Use only the supplied facts.\n{donor_facts}\n{instruction}\n{listed}\nAnswer:"
                donor_target = counterfactual if demand == "required" else target
                rows.append({"id": f"{pair_id}-l{label}-{demand}", "pair_id": pair_id,
                    "benchmark": f"functional_{family}", "split": split, "family": family,
                    "label_variant": label, "demand": demand, "content_slot": target,
                    "context": context, "context_sha256": hashlib.sha256(context.encode()).hexdigest(),
                    "donor_context": donor_context, "donor_context_sha256": hashlib.sha256(donor_context.encode()).hexdigest(),
                    "donor_target_index": order.index(donor_target), "donor_content_slot": donor_target,
                    "continuations": [" A", " B", " C", " D"], "choices": [options[i] for i in order],
                    "target_index": order.index(target), "request_type": "loglikelihood"})
    return rows


def freeze_function(contract_path, output=HERE / "data"):
    """Candidate, function and unpatched relation must exist before task materialization."""
    contract = json.loads(Path(contract_path).read_text())
    if contract.get("status") != "frozen_before_confirmation":
        raise ValueError("A frozen explanation contract is required")
    for field in ("candidate_ids", "family", "function_hypothesis", "reader", "relation", "expected_direction", "falsifier"):
        if not contract.get(field):
            raise ValueError(f"Missing function contract field: {field}")
    if not 1 <= len(contract["candidate_ids"]) <= 2:
        raise ValueError("Freeze only one or two final explanations")
    if (output / "functional_manifest.json").exists():
        raise ValueError("Existing functional freeze must not be overwritten")
    rows = functional_rows(contract["family"])
    output.mkdir(parents=True, exist_ok=True)
    files = {}
    for split in ("dev", "confirm"):
        selected = [row for row in rows if row["split"] == split]
        path = output / f"functional_{split}.jsonl"
        save_rows(path, selected)
        files[path.name] = {"sha256": sha(path), "pair_count": 16, "item_count": len(selected)}
    manifest = {"status": "frozen_before_functional_inference", "contract_sha256": sha(contract_path),
                "family": contract["family"], "files": files,
                "design": "demand/direct x answer-label permutation; 4 items per base pair; varying content balanced across pairs",
                "unit": "base task pair", "donor_cost": "Each item also specifies a fact-swapped unscored donor context for natural-role replacement; it adds donor forwards, not samples. Exact token-length/position alignment must pass at runtime.",
                "limit": "Matched wording is approximate. Fact swapping changes the required task answer while the direct task keeps its explicit answer. The reader probe alone is predictive; natural-role causal evidence requires the actual donor replacement and matched control."}
    save_json(output / "functional_manifest.json", manifest)
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("ability", "functional"))
    parser.add_argument("--function-contract", type=Path)
    args = parser.parse_args()
    result = freeze_ability() if args.mode == "ability" else freeze_function(args.function_contract)
    print(json.dumps({"status": result["status"], "files": result["files"]}, ensure_ascii=False))
