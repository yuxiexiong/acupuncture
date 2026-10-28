#!/usr/bin/env python3
"""Check coverage, exact score/summary provenance, and unchanged source hashes."""
import json
from collections import Counter
from export_evidence import HERE, REPO, SCORE_FIELDS, SIX_CONDITIONS, Sources, scored_item, sha256


def main():
    evidence = json.loads((HERE / "evidence.json").read_text())
    manifest = json.loads((HERE / "evidence-manifest.json").read_text())
    source_data = {}
    for record in manifest["sources"]:
        raw = (REPO / record["path"]).read_bytes()
        assert sha256(raw) == record["sha256"], record["path"]
        assert len(raw) == record["bytes"]
        source = evidence["sources"][record["path"]]
        assert source["sha256"] == record["sha256"] and source["href"] == "/" + record["path"]
        if record["path"].endswith(".json"):
            source_data[record["path"]] = json.loads(raw)
        elif record["path"].endswith(".jsonl"):
            source_data[record["path"]] = [json.loads(line) for line in raw.splitlines() if line.strip()]

    def resolve(ref):
        value = source_data[ref["path"]]
        for part in ref["pointer"].split("/")[1:]:
            part = part.replace("~1", "/").replace("~0", "~")
            value = value[int(part)] if isinstance(value, list) else value[part]
        return value

    def check_items(items, conditions):
        assert len(items) == 64
        assert len({item["id"] for item in items}) == 64
        assert Counter(item["benchmark"] for item in items) == {"mmlu": 32, "arc_challenge": 32}
        for item in items:
            original = resolve(item["ref"])
            assert item["id"] == original["id"] and item["item_sha256"] == original["item_sha256"]
            assert set(item["conditions"]) == set(conditions)
            for score in item["conditions"].values():
                raw_score = resolve(score["ref"])
                assert score["status"] == "available"
                for field in SCORE_FIELDS:
                    assert score[field] == raw_score[field], (item["id"], field)

    root = evidence["root_cause"]
    assert root["independent_confirmation_run"] is False
    assert [c["id"] for c in root["candidates"]] == [f"C{i:02d}" for i in range(1, 11)]
    for candidate in root["candidates"]:
        check_items(candidate["items"], SIX_CONDITIONS)
        assert candidate["metadata"] == resolve(candidate["metadata_ref"])
        assert candidate["tasks"] == resolve(candidate["tasks_ref"])
        for task, result in candidate["tasks"].items():
            for condition, count in result["correct_counts"].items():
                assert count == sum(item["conditions"][condition]["correct"]
                                    for item in candidate["items"] if item["benchmark"] == task)
    decomp = root["decomposition"]
    assert len(decomp["correct_counts"]["mmlu"]) == 17
    check_items(decomp["items"], decomp["correct_counts"]["mmlu"])
    assert decomp["correct_counts"] == resolve(decomp["correct_counts_ref"])
    assert decomp["comparisons"] == resolve(decomp["comparisons_ref"])
    assert len(root["ranking"]["items"]) == 64
    for item in root["ranking"]["items"]:
        assert item["ranking"] == resolve(item["ref"])["ranking"]
    assert len(root["questions"]) == 64
    for question in root["questions"]:
        assert {k: v for k, v in question.items() if k != "ref"} == resolve(question["ref"])
    for target in evidence["transfer"]["targets"]:
        assert {k: v for k, v in target["mapping"].items() if k not in ("ref", "status")} == resolve(target["mapping"]["ref"])
        assert len(target["mapping"]["conditions"]) == 19
        assert target["benchmarks"] == resolve(target["benchmarks_ref"])
        assert {k: v["n"] for k, v in target["benchmarks"].items()} == {
            "mmlu": 1000, "arc_challenge": 200, "gsm8k": 100, "humaneval": 100}
        assert len(target["diagnostic"]["conditions"]) == 19
        assert {k: v for k, v in target["diagnostic"].items() if k != "ref"} == resolve(target["diagnostic"]["ref"])
    assert not manifest["missing_sources"]
    assert all(not any(word in s["path"].lower() for word in ("private", "identity", "blind_key")) for s in manifest["sources"])
    assert manifest["outputs"][0]["sha256"] == sha256((HERE / "evidence.json").read_bytes())
    assert manifest["exporter_sha256"] == sha256((HERE / "export_evidence.py").read_bytes())
    missing = scored_item(Sources(REPO), "missing-evidence-test-does-not-exist.json", SIX_CONDITIONS)
    assert missing["status"] == "missing" and missing["conditions"] is None
    print(f"PASS: 10 candidates, 640 six-condition items, 64 decomposition/ranking items, 2 × 19 diagnostics, 2 × 4 benchmarks; all {len(manifest['sources'])} source hashes and exported score fields match.")


if __name__ == "__main__":
    main()
