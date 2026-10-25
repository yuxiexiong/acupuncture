"""CPU-only checks for deterministic selection, complete-pair reuse and budgets."""
import copy
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from prepare_panel import COUNTS, freeze_reuse, read, read_rows, sample_items, sha, validate_pair, write
from run_panel import evaluate_pair, json_metadata


def rejected(call):
    try:
        call()
    except AssertionError:
        return
    raise AssertionError("Expected rejection")


pool = [{"id": f"{subject}:{i:03d}", "subject": subject, "target": i, "context": "unused"}
        for subject, size in (("a", 11), ("b", 7), ("c", 5)) for i in range(size)]
selected, population, allocation = sample_items(pool, 12, 20261026, "mmlu")
assert sum(allocation.values()) == len(selected) == 12 and set(allocation) == {"a", "b", "c"}
assert selected == sample_items(list(reversed(pool)), 12, 20261026, "mmlu")[0]
changed_answers = [{**row, "target": "different", "context": "a much longer prompt"} for row in pool]
assert [x["id"] for x in selected] == [x["id"] for x in sample_items(changed_answers, 12, 20261026, "mmlu")[0]]
assert [x["id"] for x in selected] != [x["id"] for x in sample_items(pool, 12, 20261027, "mmlu")[0]]
random_selected = sample_items(pool, 10, 20261026, "arc_challenge")[0]
assert random_selected == sample_items(list(reversed(pool)), 10, 20261026, "arc_challenge")[0]

metadata = {"targets": [[14, 8949, 1.0], [13, 7956, -1.0]], "column_norms": {"14": 2.0, "13": 4.0}, "batch_size": 1}
live_metadata = {**metadata, "targets": ((14, 8949, 1.0), (13, 7956, -1.0))}
assert live_metadata != metadata
assert json_metadata(live_metadata) == metadata
different_dose = {**live_metadata, "targets": ((14, 8949, 0.5), (13, 7956, -1.0))}
assert json_metadata(different_dose) != metadata
different_norm = {**live_metadata, "column_norms": {"14": 2.000001, "13": 4.0}}
assert json_metadata(different_norm) != metadata
context = "Question:\u2028preserve this\nAnswer:"
calibration = {"context_sha256": hashlib.sha256(context.encode()).hexdigest(), "input_token_count": 3,
               "input_token_sha256": "synthetic", "residual_scales": {"14": 4.0, "13": 8.0},
               "activation_offsets": {"14": 2.0, "13": -2.0}}
item = {"id": "mmlu:a:0", "subject": "a", "benchmark": "mmlu", "context": context,
        "context_sha256": calibration["context_sha256"], "request_type": "loglikelihood",
        "continuations": [" A", " B", " C", " D"], "target_index": 2}


class FakeEngine:
    def __init__(self):
        self.calls = []

    def calibrate(self, contexts):
        assert contexts == [context]
        self.calls.append("calibrate")
        return [copy.deepcopy(calibration)]

    def score(self, contexts, continuations, arm, calibrations):
        assert contexts == [context] * 4 and continuations == item["continuations"]
        assert calibrations == [calibration] * 4
        self.calls.append(arm)
        return [{"loglikelihood": -float(i + 1), "token_logprobs": [-float(i + 1)],
                 "continuation_token_ids": [i], "context_token_count": 3,
                 "input_token_sha256": "synthetic", "is_greedy": False} for i in range(4)]

    def generate(self, contexts, arm, calibrations, budget, stops):
        assert contexts == [context] and calibrations == [calibration]
        assert budget == 2048 and stops == ["Question:"]
        self.calls.append(arm)
        return [{"max_new_tokens": budget, "generated_token_count": 1, "token_ids": [248046],
                 "end_reason": "eos_token", "raw_text": "<|im_end|>", "answer_text": ""}]


with TemporaryDirectory() as directory:
    root = Path(directory)
    engine = FakeEngine()
    row = evaluate_pair(engine, item, 0, {}, root / "partial.json")
    assert engine.calls == ["calibrate", "baseline", "evo"]
    validate_pair(row, item, metadata)
    pending = read(root / "partial.json")
    assert len(pending) == 1 and pending[0]["status"] == "started"
    assert set(pending[0]["outputs"]) == {"baseline", "evo"}
    bad = copy.deepcopy(row)
    bad["outputs"]["evo"]["status"] = "started"
    rejected(lambda: validate_pair(bad, item, metadata))
    bad = copy.deepcopy(row)
    bad["calibration"]["context_sha256"] = "wrong"
    rejected(lambda: validate_pair(bad, item, metadata))
    generation_item = {**item, "id": "gsm8k:0", "benchmark": "gsm8k", "request_type": "generate_until",
                       "gen_kwargs": {"max_gen_toks": 2048, "until": ["Question:"]}}
    engine = FakeEngine()
    generated = evaluate_pair(engine, generation_item, 1, {"max_new_tokens": {"gsm8k": 2048}}, root / "gen.partial.json")
    validate_pair(generated, generation_item, metadata)
    assert engine.calls == ["calibrate", "evo", "baseline"]

    source, panel_root = root / "v2", root / "v3"
    old_output = source / "outputs" / "mmlu-shard0-r01"
    old_output.mkdir(parents=True)
    panel_root.mkdir()
    write(source / "task_manifest.json", {"files": {"mmlu": {"sha256": "original-items"}}})
    old_protocol = {"task_manifest_sha256": sha(source / "task_manifest.json"), "source_sha256": {}}
    write(source / "protocol.json", old_protocol)
    write(old_output / "receipt.json", {"protocol_sha256": sha(source / "protocol.json"), "source_sha256": {},
        "items_sha256": "original-items", "engine": metadata, "assets": {}, "status": "started"})
    original_bytes = (json.dumps(row, ensure_ascii=False) + "\n").encode()
    (old_output / "00000.jsonl").write_bytes(original_bytes)
    (old_output / "00001.partial.json").write_text("{unfinished")
    (panel_root / "mmlu.jsonl").write_text(json.dumps(item, ensure_ascii=False) + "\n")
    write(panel_root / "panel_manifest.json", {"source_root": "../v2", "source_protocol_sha256": sha(source / "protocol.json"),
        "files": {"mmlu": {"file": "mmlu.jsonl", "sha256": sha(panel_root / "mmlu.jsonl")}}})
    write(panel_root / "protocol.json", {"status": "draft_before_source_freeze"})
    stop = source / "stop.json"
    write(stop, {"status": "stopped_by_user", "remaining_live_processes": ["still-running"],
                 "protocol_sha256": sha(source / "protocol.json")})
    rejected(lambda: freeze_reuse(source, panel_root, stop))
    write(stop, {"status": "stopped_by_user", "remaining_live_processes": [],
                 "protocol_sha256": sha(source / "protocol.json")})
    reuse = freeze_reuse(source, panel_root, stop)
    assert reuse["counts"]["mmlu"] == 1 and len(reuse["entries"]) == 1
    assert reuse["entries"][item["id"]]["sha256"] == hashlib.sha256(original_bytes).hexdigest()
    assert not reuse["source_receipts"]["outputs/mmlu-shard0-r01/receipt.json"]["final_immutability_check_present"]
    assert (old_output / "00001.partial.json").read_text() == "{unfinished"
    assert (old_output / "00000.jsonl").read_bytes() == original_bytes

manifest_path = Path(__file__).parent / "panel_manifest.json"
if manifest_path.exists():
    panel = read(manifest_path)
    assert panel["counts"] == COUNTS and panel["status"] == "frozen_before_inference"
    assert len(panel["mmlu_population_subject_counts"]) == len(panel["mmlu_sample_subject_counts"]) == 57
    assert sum(panel["mmlu_population_subject_counts"].values()) == 14042
    assert sum(panel["mmlu_sample_subject_counts"].values()) == 1000
    for task, specification in panel["files"].items():
        path = manifest_path.parent / specification["file"]
        assert sha(path) == specification["sha256"]
        rows = read_rows(path)
        assert len(rows) == len({row["id"] for row in rows}) == COUNTS[task]
        assert [row["id"] for row in rows] == panel["selected_ids"][task]
print("PASS: fixed stratified/random panel, answer/length independence, exact pair reuse and user-stop gate, unchanged generation budget")
