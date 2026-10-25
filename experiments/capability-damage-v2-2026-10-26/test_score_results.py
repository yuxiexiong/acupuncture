"""CPU checks for paired scoring, full denominators, weighting, and isolated-code commands."""
import ast
import argparse
import gzip
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from score_results import OfficialScorer, paired_interval, read_rows, record_paths, summarize, validate_records
from humaneval_sandbox import command, synthetic_cases


def row(i, before, after, subject="a", cluster=None):
    return {"id": str(i), "subject": subject, "cluster_id": str(i) if cluster is None else cluster,
            "outputs": {arm: {"correct": value, "parse_failed": False, "end_reason": "loglikelihood"}
                        for arm, value in (("baseline", before), ("evo", after))}}


# Subject weights follow their original question counts rather than a macro average.
rows = [row(0, True, False, "small")] + [row(i, False, True, "large") for i in range(1, 10)]
result = summarize(rows)
assert result["baseline"]["score_percent"] == 10 and result["evo"]["score_percent"] == 90
assert result["damage_percentage_points"] == -80
assert result["paired_interval"]["lower_pp"] == result["paired_interval"]["upper_pp"] == -80
assert result["paired_transitions"] == {"1->0": 1, "0->1": 9}
equal = paired_interval([row(i, True, True) for i in range(10)])
assert equal["lower_pp"] == equal["upper_pp"] == 0 and equal["warning"]
mixed = [row(i, i % 3 == 0, i % 5 == 0) for i in range(100)]
assert paired_interval(mixed) == paired_interval(mixed)
clustered = paired_interval([row(0, True, False, cluster="same"), row(1, False, True, cluster="same")])
assert clustered["lower_pp"] == clustered["upper_pp"] == 0

good = {"id": "one", "benchmark": "gsm8k", "status": "completed", "item": {"id": "one", "benchmark": "gsm8k"},
        "outputs": {arm: {"status": "completed"} for arm in ("baseline", "evo")}}
validate_records([good], {"gsm8k": 1})
for records, counts in (([good, good], {"gsm8k": 2}), ([good], {"gsm8k": 2})):
    try:
        validate_records(records, counts)
    except AssertionError:
        pass
    else:
        raise AssertionError("Duplicate/missing output accepted")

with TemporaryDirectory() as directory:
    root = Path(directory)
    data = json.dumps(good) + "\n"
    (root / "0000.jsonl").write_text(data)
    with gzip.open(root / "0001.jsonl.gz", "wt") as handle:
        handle.write(data)
    (root / "partial.json").write_text("{}")
    paths = record_paths([root])
    assert len(paths) == 2 and all(read_rows(path) == [good] for path in paths)

cmd = command(Path("/isolated/bwrap"), Path("/official"), Path("/python-prefix"))
assert all(flag in cmd for flag in ("--unshare-all", "--die-with-parent", "--cap-drop", "--uid", "--ro-bind"))
assert cmd[cmd.index("--uid") + 1] == "65534"
assert "/root" not in cmd and "/workspace" not in cmd
assert len(synthetic_cases()) == 5
for name in ("score_results.py", "humaneval_sandbox.py", "humaneval_worker.py"):
    ast.parse(Path(__file__).with_name(name).read_text())
print("PASS: paired denominators, original subject weights, clustered bootstrap, negative damage, archive reading, isolation command")

parser = argparse.ArgumentParser()
parser.add_argument("--harness", type=Path)
parser.add_argument("--cache-dir", type=Path)
args = parser.parse_args()
if args.harness:
    scorer = OfficialScorer(args.harness, args.cache_dir)
    for benchmark, name in (("mmlu", "mmlu_abstract_algebra"), ("arc_challenge", "arc_challenge")):
        task = scorer.task(name)
        doc = task.dataset["validation" if "validation" in task.dataset else "train"][0]
        choices, target = task.doc_to_choice(doc), task.doc_to_target(doc)
        item = {"benchmark": benchmark, "task_name": name, "doc": doc, "target": target, "target_index": int(target), "choices": choices}
        for index in range(len(choices)):
            output = {"status": "completed", "choice_loglikelihoods": [0.0 if i == index else -1000.0 for i in range(len(choices))]}
            result = scorer.score(item, output)
            assert result["prediction"] == index and result["correct"] == (index == target)
    item = {"benchmark": "gsm8k", "task_name": "gsm8k", "doc": {"question": "Synthetic arithmetic.", "answer": "Synthetic derivation.\n#### 42"},
            "context": "Question: Synthetic arithmetic.\nAnswer:", "gen_kwargs": {}}
    item["target"] = scorer.task("gsm8k").doc_to_target(item["doc"])
    cases = [("#### 42", True, True), ("#### 41\n#### 42", False, True), ("#### $42", False, True),
             ("The answer is 42.", False, True), ("#### 42.0", False, False), ("No number.", False, False)]
    for text, strict, flexible in cases:
        result = scorer.score(item, {"status": "completed", "answer_text": text})
        assert result["correct"] == strict and result["auxiliary_flexible_correct"] == flexible, (text, result)
    print("PASS: pinned official task.process_results and actual strict/flexible filter ensembles on non-test/synthetic controls")
