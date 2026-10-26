"""Freeze the label-rotation and judgment/reporting tasks without loading a model."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import random
import re

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
SOURCE = REPO / "experiments/root-cause-toy-v1-2026-10-26/data/ability_dev.jsonl"
SEED = 20261026
LABELS = [" A", " B", " C", " D"]


def text_sha(value):
    return hashlib.sha256(value.encode()).hexdigest()


def file_sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_rows(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def option_block(choices):
    return "\n".join(f"{chr(65 + i)}. {choice}" for i, choice in enumerate(choices)) + "\nAnswer:"


def reference_flags(choices):
    """Flag position/letter references; never remove a question based on this check."""
    pattern = r"\b(?:above|below|both\s+[a-d]|neither\s+[a-d]|[a-d]\s+(?:and|or)\s+[a-d])\b"
    return [i for i, choice in enumerate(choices) if re.search(pattern, choice, re.I)]


def make_row(base_id, panel, demand, rotation, options, target, context, reference_context):
    order = [(i + rotation) % 4 for i in range(4)]
    return {"id": f"{base_id}-{demand}-r{rotation}", "base_id": base_id,
        "pair_id": base_id, "panel": panel, "benchmark": "mmlu" if panel == "mmlu_rotation" else "functional_comparison",
        "demand": demand, "rotation": rotation, "order": order,
        "target_index": order.index(target), "target_content_index": target,
        "choices": [options[i] for i in order], "original_choices": options,
        "continuations": LABELS.copy(), "context": context, "context_sha256": text_sha(context),
        "reference_context": reference_context, "reference_context_sha256": text_sha(reference_context),
        "request_type": "loglikelihood", "split": "development_diagnostic"}


def mmlu_rows(source=SOURCE):
    originals = [row for row in read_rows(source) if row["benchmark"] == "mmlu"]
    if len(originals) != 32 or len({row["id"] for row in originals}) != 32:
        raise ValueError("Exactly the original 32 distinct MMLU questions are required")
    rows = []
    for item in originals:
        options = item["doc"]["choices"]
        target = item["target_index"]
        if len(options) != 4 or target != item["doc"]["answer"]:
            raise ValueError("Source choices/target mismatch")
        context, old_block = item["context"], option_block(options)
        if item["context_sha256"] != text_sha(context) or not context.endswith(old_block):
            raise ValueError("Final source option block must match exactly")
        # Everything before the last option block, including all few-shot examples,
        # remains byte-for-byte identical. The source question may end in a newline.
        prefix = context[:-len(old_block)]
        for rotation in range(4):
            order = [(i + rotation) % 4 for i in range(4)]
            changed = prefix + option_block([options[i] for i in order])
            row = make_row(item["id"], "mmlu_rotation", "required", rotation,
                           options, target, changed, context)
            row.update(source_id=item["id"], source_context_sha256=item["context_sha256"],
                source_prefix_sha256=text_sha(prefix), subject=item["subject"],
                option_reference_flags=reference_flags(options))
            rows.append(row)
    return rows


def comparison_rows():
    rng = random.Random(SEED)
    options = ["box p", "box q", "box r", "box s"]
    rows = []
    for number in range(16):
        target = number % 4
        amounts = rng.sample(range(11, 40), 4)
        largest = max(range(4), key=amounts.__getitem__)
        amounts[target], amounts[largest] = amounts[largest], amounts[target]
        facts = "; ".join(f"{name} has {amount} counters" for name, amount in zip(options, amounts)) + "."
        instructions = {
            "required": "Which box has the most counters? Select that box.",
            "direct": f"The correct answer is {options[target]}. Report that same box.",
        }
        prefix = "Use only the supplied information. Answer with one option letter.\n" + facts + "\n"
        reference = prefix + instructions["required"] + "\n" + option_block(options)
        for demand in ("required", "direct"):
            for rotation in range(4):
                order = [(i + rotation) % 4 for i in range(4)]
                context = prefix + instructions[demand] + "\n" + option_block([options[i] for i in order])
                row = make_row(f"comparison-{number + 1:02d}", "comparison", demand,
                               rotation, options, target, context, reference)
                row.update(amounts=amounts, facts=facts,
                    explicit_answer=options[target] if demand == "direct" else None,
                    option_reference_flags=[])
                rows.append(row)
    return rows


def build(source=SOURCE):
    rows = mmlu_rows(source) + comparison_rows()
    validate_rows(rows)
    return rows


def validate_rows(rows):
    if len(rows) != 256 or len({row["id"] for row in rows}) != 256:
        raise ValueError("Expected 256 unique variants")
    if Counter(row["panel"] for row in rows) != {"mmlu_rotation": 128, "comparison": 128}:
        raise ValueError("Panel budget changed")
    groups = defaultdict(list)
    for row in rows:
        groups[row["base_id"]].append(row)
        if row["base_id"] != row["pair_id"] or row["continuations"] != LABELS:
            raise ValueError("Statistical unit or scoring labels changed")
        if sorted(row["order"]) != list(range(4)):
            raise ValueError("Permutation is not bijective")
        if row["order"] != [(i + row["rotation"]) % 4 for i in range(4)]:
            raise ValueError("Not the specified cyclic rotation")
        if row["choices"] != [row["original_choices"][i] for i in row["order"]]:
            raise ValueError("Semantic choice correspondence changed")
        if row["order"][row["target_index"]] != row["target_content_index"]:
            raise ValueError("Answer content did not follow the rotation")
        for name in ("context", "reference_context"):
            if text_sha(row[name]) != row[name + "_sha256"]:
                raise ValueError("Context hash mismatch")
        if row["panel"] == "comparison":
            if len(set(row["amounts"])) != 4 or max(range(4), key=row["amounts"].__getitem__) != row["target_content_index"]:
                raise ValueError("Comparison must have a unique known maximum")
            answer = row["original_choices"][row["target_content_index"]]
            if row["explicit_answer"] != (answer if row["demand"] == "direct" else None):
                raise ValueError("Direct task must supply the answer content")
    if len(groups) != 48:
        raise ValueError("Expected 48 base units")
    for variants in groups.values():
        panel = variants[0]["panel"]
        demands = ["required"] if panel == "mmlu_rotation" else ["required", "direct"]
        if Counter((r["demand"], r["rotation"]) for r in variants) != Counter((d, r) for d in demands for r in range(4)):
            raise ValueError("Missing/duplicated demand or rotation")
        if len({r["reference_context"] for r in variants}) != 1:
            raise ValueError("Dose reference must remain fixed within each base")
        canonical = next(r for r in variants if r["demand"] == "required" and r["rotation"] == 0)
        if canonical["context"] != canonical["reference_context"]:
            raise ValueError("Reference must be the canonical required task")
        for demand in demands:
            if Counter(r["target_index"] for r in variants if r["demand"] == demand) != Counter(range(4)):
                raise ValueError("Each base/demand must put its target at all four labels")
    return {"status": "passed", "base_units": 48, "mmlu_questions": 32,
            "comparison_bases": 16, "variants": 256}


def write(output=HERE / "data", source=SOURCE):
    rows = build(source)
    raw = "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows)
    flagged = sorted({row["base_id"] for row in rows if row["option_reference_flags"]})
    manifest = {"status": "prepared_no_model_execution", "seed": SEED,
        "source": str(Path(source).resolve().relative_to(REPO)), "source_sha256": file_sha(source),
        "files": {"items.jsonl": {"sha256": text_sha(raw), "count": len(rows)}},
        "base_counts": {"mmlu_rotation": 32, "comparison": 16},
        "variant_counts": {"mmlu_rotation": 128, "comparison": 128},
        "rotation_order": "display_index -> (display_index + rotation) mod 4 = original content index",
        "calibration_reference": "One clean required/rotation0 context per base; reuse its scales in every demand/rotation and intervention condition",
        "selection": "All 32 historical development MMLU questions; 16 deterministic synthetic comparison bases. No model outputs or accuracy used.",
        "statistical_unit": "base_id; average rotations within base before resampling; demands are paired",
        "position_reference_flagged_base_ids": flagged,
        "flag_policy": "Retain all questions; flagged semantic ambiguity is disclosed, not silently excluded.",
        "boundary": "Exploratory label dependence/task demand diagnosis, not an independent confirmation or a full mechanism test. Direct tasks still require reading and content-to-label mapping; option rotation changes both display order and label association."}
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    payloads = {"items.jsonl": raw, "manifest.json": json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"}
    for name, value in payloads.items():
        path = output / name
        if path.exists() and path.read_text() != value:
            raise ValueError(f"Refusing to overwrite different frozen data: {path}")
    for name, value in payloads.items():
        path = output / name
        if not path.exists():
            path.write_text(value)
    return manifest


def verify(output=HERE / "data", source=SOURCE):
    output = Path(output)
    manifest = json.loads((output / "manifest.json").read_text())
    if file_sha(source) != manifest["source_sha256"]:
        raise ValueError("Original development source changed")
    if file_sha(output / "items.jsonl") != manifest["files"]["items.jsonl"]["sha256"]:
        raise ValueError("Frozen variant file changed")
    rows = read_rows(output / "items.jsonl")
    if rows != build(source):
        raise ValueError("Variants no longer reproduce the fixed source/rule")
    return validate_rows(rows)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "verify"))
    parser.add_argument("--output", type=Path, default=HERE / "data")
    args = parser.parse_args()
    result = write(args.output) if args.mode == "prepare" else verify(args.output)
    print(json.dumps(result, ensure_ascii=False, indent=2))
