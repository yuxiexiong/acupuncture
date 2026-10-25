"""Freeze official task requests without loading a model or inspecting model answers."""
import argparse
import gzip
import hashlib
import importlib.metadata
import json
from pathlib import Path
import subprocess
import urllib.request

SEED = 20261026
HARNESS_COMMIT = "d6de81643928d653435c431bae19945d41d32520"
HUMANEVAL_COMMIT = "b9453e8f1865df0a0057a1383767caa400acfbcf"
DATA_REVISIONS = {
    "cais/mmlu": "c30699e8356da336a370243923dbaf21066bb9fe",
    "allenai/ai2_arc": "210d026faf9955653af8916fad021475a3f00453",
    "openai/gsm8k": "740312add88f781978c0658806c59bc2815b9866",
}
EXPECTED = {"mmlu": 14042, "arc_challenge": 1172, "gsm8k": 1319, "humaneval": 164}


def encode(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save_once(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        assert path.read_bytes() == content, f"Refusing to overwrite changed frozen file: {path}"
    else:
        path.write_bytes(content)


def dataset_identity(dataset):
    h = hashlib.sha256()
    for doc in dataset:
        h.update(encode(doc) + b"\n")
    return {"count": len(dataset), "fingerprint": dataset._fingerprint, "content_sha256": h.hexdigest()}


def task_paths(harness):
    root = harness / "lm_eval/tasks"
    mmlu = sorted((root / "mmlu/default").glob("mmlu_*.yaml"))
    assert len(mmlu) == 57
    return [("mmlu", path, 5) for path in mmlu] + [
        ("arc_challenge", root / "arc/arc_challenge.yaml", 25),
        ("gsm8k", root / "gsm8k/gsm8k.yaml", 5),
    ]


def instantiate_task(path, num_fewshot, cache_dir=None):
    from lm_eval.api.task import ConfigurableTask
    from lm_eval.tasks._yaml_loader import load_yaml

    config = load_yaml(path)
    for key in ("tag", "group", "task_list"):
        config.pop(key, None)
    config["num_fewshot"] = num_fewshot
    config["dataset_kwargs"] = {**config.get("dataset_kwargs", {}), "revision": DATA_REVISIONS[config["dataset_path"]]}
    if cache_dir:
        config["dataset_kwargs"]["cache_dir"] = str(cache_dir)
    if config["task"] == "gsm8k":
        config["generation_kwargs"]["max_gen_toks"] = 2048
    task = ConfigurableTask(config=config)
    task.set_fewshot_seed(SEED)
    return task


def load_pinned_task(name, harness_root=None, cache_dir=None):
    """Reuse exactly the same pinned official task when scoring saved outputs."""
    import lm_eval

    harness = Path(harness_root) if harness_root else Path(lm_eval.__file__).resolve().parent.parent
    actual = subprocess.check_output(["git", "-C", str(harness), "rev-parse", "HEAD"], text=True).strip()
    assert actual == HARNESS_COMMIT
    matches = [(path, shots) for _, path, shots in task_paths(harness) if path.stem == name]
    assert len(matches) == 1, name
    path, shots = matches[0]
    return instantiate_task(path, shots, cache_dir)


def make_record(benchmark, task, doc_id, instances, exposed_questions):
    instances.sort(key=lambda instance: instance.idx)
    doc = instances[0].doc
    contexts = {instance.args[0] for instance in instances}
    assert len(contexts) == 1, "Candidates must share their entire calibration context"
    context = next(iter(contexts))
    row = {"id": f"{task.config.task}:{doc_id}", "benchmark": benchmark,
           "task_name": task.config.task, "doc_id": doc_id, "context": context,
           "context_sha256": hashlib.sha256(context.encode()).hexdigest(),
           "doc": doc, "target": task.doc_to_target(doc)}
    if task.OUTPUT_TYPE == "multiple_choice":
        row.update({"request_type": "loglikelihood", "choices": task.doc_to_choice(doc),
                    "continuations": [instance.args[1] for instance in instances],
                    "target_index": int(task.doc_to_target(doc))})
        assert len(row["choices"]) == len(row["continuations"])
        assert 0 <= row["target_index"] < len(row["choices"])
    else:
        assert len(instances) == 1 and task.OUTPUT_TYPE == "generate_until"
        row.update({"request_type": "generate_until", "gen_kwargs": instances[0].args[1],
                    "exposed_in_quick_eval": doc["question"].strip() in exposed_questions})
    if benchmark == "mmlu":
        row["subject"] = task.config.dataset_name
    return row


def export_task(benchmark, task, exposed_questions):
    task.build_all_requests(cache_requests=False, apply_chat_template=False)
    grouped = {}
    for instance in task.instances:
        grouped.setdefault(instance.doc_id, []).append(instance)
    records = [make_record(benchmark, task, doc_id, instances, exposed_questions)
               for doc_id, instances in grouped.items()]
    assert len(records) == len(task.eval_docs)
    return records


def development_items(benchmark, task, shots):
    split = "validation" if "validation" in task.dataset else "train"
    rows = []
    for index in range(2):
        doc = task.dataset[split][index]
        context = task.fewshot_context(doc, num_fewshot=shots, apply_chat_template=False)
        instances = task.construct_requests(doc=doc, ctx=context,
            metadata=(task.config.task, index, 1), apply_chat_template=False)
        if not isinstance(instances, list):
            instances = [instances]
        row = make_record(benchmark, task, index, instances, set())
        row.update({"id": f"technical:{task.config.task}:{split}:{index}",
                    "source_split": split, "non_test_technical": True})
        rows.append(row)
    task.set_fewshot_seed(SEED)  # Technical requests must not advance formal few-shot sampling.
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--harness", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--cache-dir", type=Path)
    parser.add_argument("--quick-items", type=Path, required=True)
    parser.add_argument("--humaneval-data", type=Path, required=True)
    args = parser.parse_args()
    harness = args.harness.resolve()
    actual = subprocess.check_output(["git", "-C", str(harness), "rev-parse", "HEAD"], text=True).strip()
    assert actual == HARNESS_COMMIT, (actual, HARNESS_COMMIT)
    import lm_eval
    from lm_eval.tasks._yaml_loader import load_yaml

    assert Path(lm_eval.__file__).resolve().is_relative_to(harness), "Install this exact local harness checkout"
    quick = json.loads(args.quick_items.read_text())
    exposed = {row["question"].strip() for row in quick if row["benchmark"] == "gsm8k"}
    assert len(exposed) == 100
    source_paths, development = [], []
    task_records, task_configs, split_identities = {key: [] for key in EXPECTED}, {}, {}
    for benchmark, path, shots in task_paths(harness):
        task = instantiate_task(path, shots, args.cache_dir)
        source_paths.append(path)
        if benchmark != "mmlu" or task.config.task == "mmlu_abstract_algebra":
            development.extend(development_items(benchmark, task, shots))
        task_records[benchmark].extend(export_task(benchmark, task, exposed))
        task_configs[task.config.task] = task.dump_config()
        fewshot_split = (task.fewshot_cfg.split or task.config.training_split
                         or task.config.validation_split or task.config.test_split)
        used_splits = {task.config.test_split, fewshot_split}
        split_identities[task.config.task] = {name: dataset_identity(task.dataset[name]) for name in sorted(used_splits)}
        print(f"Prepared {task.config.task}: {len(task.eval_docs)} test items", flush=True)
    human_url = f"https://raw.githubusercontent.com/openai/human-eval/{HUMANEVAL_COMMIT}/data/HumanEval.jsonl.gz"
    if not args.humaneval_data.exists():
        args.humaneval_data.parent.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(human_url, timeout=60) as response:
            save_once(args.humaneval_data, response.read())
    human_path = harness / "lm_eval/tasks/humaneval/humaneval.yaml"
    human_config = load_yaml(human_path, resolve_func=False)
    human_gen = human_config["generation_kwargs"]
    assert human_gen["max_gen_toks"] == 1024
    with gzip.open(args.humaneval_data, "rt") as stream:
        for doc_id, line in enumerate(stream):
            doc = json.loads(line)
            task_records["humaneval"].append({"id": doc["task_id"], "benchmark": "humaneval",
                "task_name": "humaneval", "doc_id": doc_id, "context": doc["prompt"],
                "context_sha256": hashlib.sha256(doc["prompt"].encode()).hexdigest(),
                "request_type": "generate_until", "gen_kwargs": human_gen,
                "doc": doc, "target": doc["canonical_solution"]})
    source_paths += [harness / "lm_eval/tasks/mmlu/default/_default_template_yaml",
                     *sorted((harness / "lm_eval/tasks/mmlu/default").glob("_mmlu*.yaml")),
                     harness / "lm_eval/tasks/arc/arc_easy.yaml", human_path,
                     harness / "lm_eval/api/task.py", harness / "lm_eval/api/samplers.py",
                     harness / "lm_eval/tasks/_yaml_loader.py"]
    counts = {key: len(rows) for key, rows in task_records.items()}
    assert counts == EXPECTED, counts
    assert len({row["id"] for rows in task_records.values() for row in rows}) == sum(EXPECTED.values())
    assert sum(row["exposed_in_quick_eval"] for row in task_records["gsm8k"]) == 100
    assert len(development) == 6
    development_path = args.output / "development.jsonl"
    save_once(development_path, b"".join(encode(row) + b"\n" for row in development))
    files = {}
    for benchmark, rows in task_records.items():
        relative = f"items/{benchmark}.jsonl"
        path = args.output / relative
        save_once(path, b"".join(encode(row) + b"\n" for row in rows))
        files[benchmark] = {"file": relative, "sha256": sha(path), "bytes": path.stat().st_size, "count": len(rows)}
    manifest = {"status": "frozen_before_inference", "counts": counts, "files": files,
        "development": {"file": "development.jsonl", "count": 6, "sha256": sha(development_path), "scope": "Non-test technical checks only; not scored in formal denominators"},
        "fewshot_seed": SEED, "harness_commit": HARNESS_COMMIT, "dataset_revisions": DATA_REVISIONS,
        "source_sha256": {str(path.relative_to(harness)): sha(path) for path in source_paths},
        "task_configs": task_configs, "split_identities": split_identities,
        "mmlu_aggregation": "Mean over all 14042 test items; official group weight_by_size=True; keep subject counts for paired stratified bootstrap.",
        "arc_normalization": "Sum of continuation loglikelihood divided by len(task.doc_to_choice(doc)[i]) in Unicode characters, excluding target_delimiter.",
        "humaneval": {"repository_commit": HUMANEVAL_COMMIT, "data_url": human_url,
                      "data_sha256": sha(args.humaneval_data), "generation_kwargs": human_gen},
        "quick_items_sha256": sha(args.quick_items), "gsm8k_exposed": 100, "gsm8k_unexposed": 1219,
        "preparation_sha256": sha(__file__),
        "versions": {name: importlib.metadata.version(name) for name in ["lm_eval", "datasets", "numpy", "pyyaml", "jinja2"]}}
    save_once(args.output / "task_manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True).encode() + b"\n")
    print(json.dumps({"status": "frozen", "counts": counts, "files": files}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
