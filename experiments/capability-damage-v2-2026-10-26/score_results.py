"""Score saved paired outputs with pinned official tasks; never execute model code here."""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import gzip
import json
from pathlib import Path

import numpy as np

from prepare_tasks import EXPECTED, HARNESS_COMMIT, HUMANEVAL_COMMIT, load_pinned_task

ARMS = ("baseline", "evo")
METRICS = {"mmlu": "acc", "arc_challenge": "acc_norm", "gsm8k": "strict-match", "humaneval": "pass@1"}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def completion_sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


def record_paths(paths):
    result = []
    for path in paths:
        result.extend(sorted(path.rglob("[0-9]*.jsonl*")) if path.is_dir() else [path])
    assert len(result) == len(set(result)) and result
    assert all(str(path).endswith((".jsonl", ".jsonl.gz")) for path in result)
    return result


def read_rows(path):
    opener = gzip.open if str(path).endswith(".gz") else open
    with opener(path, "rt") as handle:
        return [json.loads(line) for line in handle if line.strip()]


class OfficialScorer:
    def __init__(self, harness=None, cache_dir=None):
        self.harness, self.cache_dir, self.tasks = harness, cache_dir, {}

    def task(self, name):
        if name not in self.tasks:
            self.tasks[name] = load_pinned_task(name, self.harness, self.cache_dir)
        return self.tasks[name]

    def score(self, item, output):
        assert output["status"] == "completed"
        benchmark = item["benchmark"]
        assert benchmark != "humaneval", "HumanEval requires separately isolated execution"
        task = self.task(item["task_name"])
        assert task.doc_to_target(item["doc"]) == item["target"]
        if benchmark in ("mmlu", "arc_challenge"):
            choices = task.doc_to_choice(item["doc"])
            assert choices == item["choices"]
            lls = np.asarray(output["choice_loglikelihoods"], dtype=float)
            assert len(lls) == len(choices) and np.isfinite(lls).all()
            official = task.process_results(item["doc"], [(float(ll), False) for ll in lls])
            metric = METRICS[benchmark]
            values = lls if metric == "acc" else lls / np.asarray([len(choice) for choice in choices])
            predicted = int(np.argmax(values))
            assert bool(official[metric]) == (predicted == item["target_index"])
            return {"correct": bool(official[metric]), "prediction": predicted,
                    "metric": metric, "official_metrics": official, "parse_failed": False}

        # Use the task's actual configured filter ensemble, including official regex selection.
        text = output["answer_text"]
        from lm_eval.api.instance import Instance
        instance = Instance(request_type="generate_until", doc=item["doc"], arguments=(item["context"], item["gen_kwargs"]), idx=0)
        instance.resps = [text]
        scores, predictions = {}, {}
        for ensemble in task._filters:
            ensemble.apply([instance])
            extracted = instance.filtered_resps[ensemble.name]
            predictions[ensemble.name] = extracted
            scores[ensemble.name] = bool(task.process_results(item["doc"], [extracted])["exact_match"])
        assert set(scores) == {"strict-match", "flexible-extract"}
        return {"correct": scores["strict-match"], "metric": "strict-match",
                "prediction": predictions["strict-match"], "parse_failed": predictions["strict-match"] == "[invalid]",
                "auxiliary_flexible_correct": scores["flexible-extract"], "auxiliary_flexible_prediction": predictions["flexible-extract"]}


def paired_interval(rows, *, seed=20261026, repeats=10000):
    """Paired bootstrap; stratify MMLU and cluster exact shared contexts within strata."""
    rng = np.random.default_rng(seed)
    strata = defaultdict(list)
    for row in rows:
        strata[row.get("subject", "all")].append(row)
    draws = np.zeros(repeats)
    n = len(rows)
    for group in strata.values():
        clusters = defaultdict(list)
        for row in group:
            clusters[row.get("cluster_id", row["id"])].append(int(row["outputs"]["baseline"]["correct"]) - int(row["outputs"]["evo"]["correct"]))
        sums = np.asarray([sum(values) for values in clusters.values()])
        sizes = np.asarray([len(values) for values in clusters.values()])
        if np.all(sizes == 1):
            # Exactly the same bootstrap law as resampling individual paired outcomes,
            # without materializing 10,000 x 14,042 row indices.
            values, counts = np.unique(sums, return_counts=True)
            draws += rng.multinomial(len(group), counts / len(group), size=repeats).dot(values) / n
        else:
            for start in range(0, repeats, 128):
                indices = rng.integers(len(sums), size=(min(128, repeats - start), len(sums)))
                draws[start:start + len(indices)] += (sums[indices].sum(axis=1) / sizes[indices].sum(axis=1)) * len(group) / n
    discordant = sum(row["outputs"]["baseline"]["correct"] != row["outputs"]["evo"]["correct"] for row in rows)
    return {"level": 0.95, "repeats": repeats, "seed": seed,
            "lower_pp": float(np.quantile(draws, 0.025) * 100), "upper_pp": float(np.quantile(draws, 0.975) * 100),
            "discordant_pairs": discordant,
            "warning": "Sparse discordance; a degenerate interval does not establish no damage." if discordant <= 5 else None,
            "strata": {str(k): len(v) for k, v in strata.items()},
            "cluster_rule": "Exact common task context; MMLU stratified by subject with fixed original subject weights."}


def summarize(rows):
    n = len(rows)
    assert n
    result = {"n": n}
    for arm in ARMS:
        outputs = [row["outputs"][arm] for row in rows]
        correct = sum(output["correct"] for output in outputs)
        result[arm] = {"correct": correct, "score_percent": correct / n * 100,
                       "truncated": sum(output["end_reason"] == "length_limit" for output in outputs),
                       "parse_failed": sum(output["parse_failed"] for output in outputs),
                       "execution_categories": dict(Counter(output["execution_category"] for output in outputs if "execution_category" in output))}
        if "auxiliary_flexible_correct" in outputs[0]:
            result[arm]["auxiliary_flexible_correct"] = sum(output["auxiliary_flexible_correct"] for output in outputs)
            result[arm]["auxiliary_flexible_percent"] = result[arm]["auxiliary_flexible_correct"] / n * 100
    result["damage_percentage_points"] = result["baseline"]["score_percent"] - result["evo"]["score_percent"]
    result["paired_interval"] = paired_interval(rows)
    result["paired_transitions"] = dict(Counter(f'{int(row["outputs"]["baseline"]["correct"])}->{int(row["outputs"]["evo"]["correct"])}' for row in rows))
    return result


def validate_records(records, expected=EXPECTED):
    assert len({row["id"] for row in records}) == len(records), "Duplicate pair IDs"
    assert Counter(row["benchmark"] for row in records) == expected, "Incomplete full benchmark collection"
    for row in records:
        assert row["status"] == "completed" and row["id"] == row["item"]["id"]
        assert row["benchmark"] == row["item"]["benchmark"] and set(row["outputs"]) == set(ARMS)
        assert all(row["outputs"][arm]["status"] == "completed" for arm in ARMS)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--records", type=Path, nargs="+", required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--human-results", type=Path, required=True)
    parser.add_argument("--harness", type=Path, required=True)
    parser.add_argument("--cache-dir", type=Path)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    paths = record_paths(args.records)
    records = [row for path in paths for row in read_rows(path)]
    validate_records(records)
    manifest = json.loads(args.manifest.read_text())
    assert manifest["status"] == "frozen_before_inference" and manifest["counts"] == EXPECTED
    assert manifest["harness_commit"] == HARNESS_COMMIT
    frozen = {}
    for entry in manifest["files"].values():
        path = args.manifest.parent / entry["file"]
        assert sha(path) == entry["sha256"]
        items = read_rows(path)
        assert len(items) == entry["count"]
        frozen.update({item["id"]: item for item in items})
    assert set(frozen) == {row["id"] for row in records}
    assert all(row["item"] == frozen[row["id"]] for row in records)
    human_rows = read_rows(args.human_results)
    human_receipt_path = args.human_results.with_suffix(args.human_results.suffix + ".receipt.json")
    human_receipt = json.loads(human_receipt_path.read_text())
    assert human_receipt["status"] == "completed" and human_receipt["controls_passed"]
    assert not human_receipt["self_test"] and human_receipt["count"] == 328
    assert human_receipt["humaneval_commit"] == HUMANEVAL_COMMIT
    assert human_receipt["output_sha256"] == sha(args.human_results)
    assert human_receipt["driver_sha256"] == sha(Path(__file__).with_name("humaneval_sandbox.py"))
    assert human_receipt["worker_sha256"] == sha(Path(__file__).with_name("humaneval_worker.py"))
    controls = args.human_results.with_suffix(args.human_results.suffix + ".controls.jsonl")
    assert human_receipt["controls_sha256"] == sha(controls)
    human = {(row["id"], row["arm"]): row for row in human_rows}
    assert len(human) == len(human_rows) == 164 * 2
    scorer, scored = OfficialScorer(args.harness, args.cache_dir), []
    for row in records:
        item = row["item"]
        result = {"id": row["id"], "benchmark": row["benchmark"], "cluster_id": item["context_sha256"], "outputs": {}}
        if "subject" in item:
            result["subject"] = item["subject"]
        if "exposed_in_quick_eval" in item:
            result["exposed_in_quick_eval"] = item["exposed_in_quick_eval"]
        for arm in ARMS:
            output = row["outputs"][arm]
            if item["benchmark"] == "humaneval":
                execution = human[row["id"], arm]
                assert execution["status"] == "completed", "HumanEval infrastructure failure is not a wrong answer"
                assert execution["completion_sha256"] == completion_sha(output["answer_text"])
                assert execution["problem_sha256"] == completion_sha(json.dumps(item["doc"], ensure_ascii=False, sort_keys=True, separators=(",", ":")))
                parsed = {"correct": execution["passed"], "metric": "pass@1", "parse_failed": False,
                          "execution_category": execution["category"], "execution_result": execution["result"]}
            else:
                parsed = scorer.score(item, output)
            result["outputs"][arm] = {**parsed, "end_reason": output.get("end_reason", "loglikelihood")}
        scored.append(result)
    benchmarks = {}
    for name in EXPECTED:
        selected = [row for row in scored if row["benchmark"] == name]
        benchmarks[name] = {"metric": METRICS[name], "expected_n": EXPECTED[name], **summarize(selected)}
    unseen = [row for row in scored if row["benchmark"] == "gsm8k" and not row["exposed_in_quick_eval"]]
    assert len(unseen) == 1219
    result = {"status": "completed", "created_utc": datetime.now(timezone.utc).isoformat(),
              "harness_commit": HARNESS_COMMIT, "humaneval_commit": HUMANEVAL_COMMIT,
              "scorer_sha256": sha(__file__), "inputs_sha256": {str(path): sha(path) for path in paths + [args.manifest, args.human_results, human_receipt_path]},
              "benchmarks": benchmarks, "gsm8k_unexposed": summarize(unseen)}
    args.out_dir.mkdir(parents=True, exist_ok=True)
    for name, content in (("scores.jsonl", "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in scored)),
                          ("summary.json", json.dumps(result, ensure_ascii=False, indent=2) + "\n")):
        path = args.out_dir / name
        assert not path.exists(), f"Refusing to overwrite {path}"
        path.write_text(content)
    print(json.dumps(result["benchmarks"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
