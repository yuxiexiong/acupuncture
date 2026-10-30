"""Merge the fixed public parameter facts before collecting any responses."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def read(name):
    return json.loads((HERE / name).read_text())


def write(name, value):
    path = HERE / name
    assert not path.exists(), f"Preserve existing design: {path}"
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def generation(raw):
    sampled = float(raw.get("temperature", 0)) > 0
    return {
        "do_sample": sampled,
        "temperature": float(raw["temperature"]) if sampled else 1.0,
        "top_p": float(raw.get("top_p", 1)) if sampled else 1.0,
        "top_k": int(raw.get("top_k", 0)) if sampled else 0,
        "min_p": float(raw.get("min_p", 0)) if sampled else 0.0,
        "repetition_penalty": float(raw.get("repetition_penalty", 1)),
        "seed": int(raw.get("seed", 0)),
    }


def main():
    prior = read("prior_recipes.json")
    public = read("sources/neuronary_parameter_snapshot.json")
    variants = read("sources/additional_notes_variants.json")["variants"]
    design = read("question_design.json")
    questions = {q["id"]: q for q in design["questions"]}
    mapping = {m["source_key"]: m["question_ids"] for m in design["mappings"]}
    inputs = [("H-" + x["id"], x) for x in prior["recipes"]]
    inputs += [("N-" + x["id"], x) for x in public["entries"] if x["model"] == "Qwen/Qwen3.5-4B"]
    inputs += [("V-" + x["variant_id"], x) for x in variants]
    assert len(inputs) == len(mapping) == 232
    assert {key for key, _ in inputs} == set(mapping)
    recipes, signatures, source_mapping = [], {}, []
    for key, source in inputs:
        points = sorted([{"layer": p["layer"], "neuron": p["neuron"], "dose": float(p["dose"])}
                         for p in source["neurons"]], key=lambda p: (p["layer"], p["neuron"]))
        settings = generation(source.get("effective_generation", {}))
        mode = source.get("normalization", "fixed_reference")
        signature = json.dumps([points, mode, settings], sort_keys=True, separators=(",", ":"))
        label = source.get("label", source.get("name"))
        attribution = {"source_key": key, "label": label,
            "urls": source.get("source_urls", [source.get("url", source.get("source_url"))]),
            "source_status": source.get("source_claim_status", source.get("evidence_status", "external_author_report")),
            "author": source.get("author"), "notes": source.get("source_notes", source.get("technical_notes_zh_CN", source.get("technical_summary_zh_CN")))}
        if signature in signatures:
            recipe = signatures[signature]
            recipe["sources"].append(attribution)
        else:
            recipe = {"id": key, "label": label, "interventions": points,
                "normalization": mode, "generation": settings,
                "question_ids": mapping[key], "sources": [attribution],
                "configuration_sha256": hashlib.sha256(signature.encode()).hexdigest()}
            assert len(set(recipe["question_ids"])) == 5
            signatures[signature] = recipe
            recipes.append(recipe)
        source_mapping.append({"source_key": key, "recipe_id": recipe["id"], "label": label,
                               "question_ids": recipe["question_ids"]})
    used = {qid for r in recipes for qid in r["question_ids"]}
    assert used <= set(questions)
    final_questions = [q for q in design["questions"] if q["id"] in used]
    assert len({q["prompt"] for q in final_questions}) == len(final_questions)
    for recipe in recipes:
        assert all(0 <= p["layer"] < 32 and 0 <= p["neuron"] < 9216 and p["dose"] != 0
                   for p in recipe["interventions"])
    counts = {"historical_records": len(prior["recipes"]), "public_4b_records": 178,
        "explicit_notes_variants": len(variants), "source_records": len(inputs),
        "unique_conditions": len(recipes), "duplicate_source_records": len(inputs) - len(recipes),
        "modified_answers": len(recipes) * 5, "unique_questions": len(final_questions),
        "effective_generation_groups": len({json.dumps(r["generation"], sort_keys=True) for r in recipes})}
    write("recipes.json", recipes)
    write("questions.json", final_questions)
    write("catalog.json", {"counts": counts, "source_to_run": source_mapping,
        "deduplication": "Exact signed coordinates + normalization + effective decoder; historical source first fixes five questions; all source aliases retained.",
        "historical_defaults": "Missing normalization uses Explorer fixed REFERENCE_TEXT fallback; missing decoder uses greedy/rep=1. These are declared reproduction assumptions, not recovered historical settings.",
        "excluded_other_models": [{"id": x["id"], "model": x["model"], "url": x["url"]}
            for x in public["entries"] if x["model"] != "Qwen/Qwen3.5-4B"]})
    print(json.dumps(counts, ensure_ascii=False))


if __name__ == "__main__":
    main()
