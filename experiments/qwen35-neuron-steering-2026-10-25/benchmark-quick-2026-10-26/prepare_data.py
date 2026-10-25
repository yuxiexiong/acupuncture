"""Freeze 100 English test items per benchmark before collecting model answers.

Run with Python's standard library after downloading the SOURCES into sources/.
Reruns are offline and must reproduce identical items and manifest bytes.
"""
from collections import Counter
import hashlib
import json
from pathlib import Path
import random
import re
import tarfile


ROOT = Path(__file__).resolve().parent
SEED = 20261026
SOURCES = {
    "RACE.tar.gz": "https://www.cs.cmu.edu/~glai1/data/race/RACE.tar.gz",
    "gsm8k_test.jsonl": "https://raw.githubusercontent.com/openai/grade-school-math/3101c7d5072418e28b9008a6636bde82a006892c/grade_school_math/data/test.jsonl",
    "logiqa2_test.txt": "https://raw.githubusercontent.com/csitfun/LogiQA2.0/955e1d3df6c59d9bfb44d9913da1e1a27ec14e18/logiqa/DATA/LOGIQA/test.txt",
}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()


def save_exact(path, data):
    if path.exists():
        assert path.read_bytes() == data, f"Refusing to overwrite a different frozen artifact: {path}"
    else:
        path.write_bytes(data)


def mcq(benchmark, source_id, context, question, options, target, **metadata):
    assert len(options) == 4 and target in "ABCD"
    choices = "\n".join(f"{letter}. {option}" for letter, option in zip("ABCD", options))
    return {
        "id": f"{benchmark}:{source_id}", "benchmark": benchmark,
        "source_id": source_id, "context": context, "question": question,
        "options": options, "target": target,
        "prompt": f"Read the passage and answer the question.\n\nPassage:\n{context}\n\nQuestion:\n{question}\n\n{choices}\n\nAnswer with only the letter A, B, C, or D.",
        **metadata,
    }


def prepare():
    items, counts = [], {}
    # Separate fixed RNGs make every benchmark independently reproducible.
    rng = random.Random(SEED)
    with tarfile.open(ROOT / "sources/RACE.tar.gz", "r:gz") as archive:
        for stratum, take in (("middle", 29), ("high", 71)):
            members = sorted((m for m in archive.getmembers()
                              if m.isfile() and m.name.startswith(f"RACE/test/{stratum}/")
                              and m.name.endswith(".txt")), key=lambda m: m.name)
            rows = [(member.name, json.load(archive.extractfile(member))) for member in members]
            counts[f"race_{stratum}"] = {"test_passages": len(rows),
                "test_questions": sum(len(row["questions"]) for _, row in rows), "sample_questions": take}
            for name, row in rng.sample(rows, take):
                index = rng.randrange(len(row["questions"]))
                items.append(mcq("race", f"{name}#q{index}", row["article"], row["questions"][index],
                                 row["options"][index], row["answers"][index], stratum=stratum,
                                 passage_id=name, question_index=index))
    assert counts["race_middle"]["test_questions"] == 1436
    assert counts["race_high"]["test_questions"] == 3498
    assert len({row["passage_id"] for row in items}) == 100

    gsm = [json.loads(line) for line in (ROOT / "sources/gsm8k_test.jsonl").read_text().splitlines() if line.strip()]
    assert len(gsm) == 1319
    for index in random.Random(SEED).sample(range(len(gsm)), 100):
        row = gsm[index]
        target = row["answer"].rsplit("####", 1)[1].strip().replace(",", "")
        assert re.fullmatch(r"-?\d+(?:\.\d+)?", target), target
        source_id = f"test.jsonl:line{index + 1}"
        items.append({"id": f"gsm8k:{source_id}", "benchmark": "gsm8k", "source_id": source_id,
                      "question": row["question"], "target": target,
                      "prompt": row["question"] + '\n\nSolve the problem step by step. End your response with "#### <answer>".'})
    counts["gsm8k"] = {"test_questions": len(gsm), "sample_questions": 100}

    logiqa = [json.loads(line) for line in (ROOT / "sources/logiqa2_test.txt").read_text().splitlines() if line.strip()]
    assert len(logiqa) == 1572
    for index in random.Random(SEED).sample(range(len(logiqa)), 100):
        row = logiqa[index]
        assert row["answer"] in range(4)
        source_id = f"test.txt:line{index + 1}:id{row['id']}"
        items.append(mcq("logiqa2", source_id, row["text"], row["question"], row["options"],
                         "ABCD"[row["answer"]], reasoning_types=row.get("type", {})))
    counts["logiqa2"] = {"test_questions": len(logiqa), "sample_questions": 100,
                        "unique_source_ids": len({row["id"] for row in logiqa}),
                        "unique_context_question_options": len({(row["text"], row["question"], tuple(row["options"])) for row in logiqa})}
    assert Counter(row["benchmark"] for row in items) == {"race": 100, "gsm8k": 100, "logiqa2": 100}
    assert len({row["id"] for row in items}) == 300
    data = encode(items)
    manifest = {
        "status": "fixed_before_model_outputs", "scope": "quick_subset_not_full_benchmark",
        "seed": SEED, "language": "English", "split": "test", "counts": counts,
        "sampling": {
            "race": "Seeded sample of 29 distinct middle and 71 distinct high test passages; then uniformly choose one question in each selected passage. Members sorted by archive path. One RNG seeded 20261026, middle followed by high.",
            "race_limitation": "Passage sampling prevents repeated passages but is not a uniform sample of all questions. Report as a fixed passage-balanced subset, not the full official RACE score.",
            "gsm8k": "Uniform sample without replacement of 100 official test row indices using its own random.Random(20261026).",
            "logiqa2": "Uniform sample without replacement of 100 official English MRC test row indices using its own random.Random(20261026).",
            "logiqa2_source_note": "Upstream numeric IDs are not globally unique; source_id includes the original 1-based line number and numeric ID. No source rows are silently removed.",
            "ordering": "RACE middle then high, GSM8K, LogiQA2; sample order retained within each group.",
        },
        "sources": [{"file": f"sources/{name}", "url": url,
                     "bytes": (ROOT / "sources" / name).stat().st_size,
                     "sha256": sha256(ROOT / "sources" / name)} for name, url in SOURCES.items()],
        "selected_ids": [row["id"] for row in items],
        "items_sha256": hashlib.sha256(data).hexdigest(), "preparation_source_sha256": sha256(Path(__file__)),
    }
    save_exact(ROOT / "items.json", data)
    save_exact(ROOT / "data_manifest.json", encode(manifest))
    print(json.dumps({"status": "verified", "counts": counts, "items_sha256": manifest["items_sha256"]}))


if __name__ == "__main__":
    prepare()
