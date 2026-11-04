"""Offline audit only. No model imports or network calls.
Usage: python audit_existing.py REPO_ROOT OUTPUT_JSON
       python audit_existing.py --check-audit audit.json
Run source extraction against the source_commit recorded in the published audit.
"""
import hashlib
import json
import sys
from pathlib import Path

WIN = Path("experiments/window-recovery-win01-v1-2026-11-04")
NEEDLE = "N_L00_C4146_D-1"
ARMS = ("C", "T", "S_deep", "R_all")


def aggregate(items, writes):
    stats, norms = [], {}
    for task in ("fact", "code"):
        for arm in ARMS:
            a = [x for x in items if x["task"] == task and x["arm"] == arm]
            assert len(a) == 48
            stats.append(dict(task=task, arm=arm, n=len(a),
                correct=sum(x["y"] for x in a), first_stop=sum(x["stop"] for x in a),
                over32=sum(x["n"] > 32 for x in a),
                correct_over32=sum(x["y"] and x["n"] > 32 for x in a),
                max=max(x["n"] for x in a),
                length_limit=sum("limit" in x["end"] for x in a),
                correct_length_limit=sum(x["y"] and "limit" in x["end"] for x in a)))
        a = [x for x in writes if x["task"] == task]
        values = [x["nominal_write_norm"] for x in a]
        norms[task] = dict(n=len(a), min=min(values), max=max(values),
            mean=sum(values) / len(a), deltas=sorted(set(x["bf16_activation_delta"] for x in a)))
    return stats, norms


def extract(root):
    labels = json.loads((root / WIN / "reading/formal-r01/labels-uniform-v4.json").read_text())
    items, writes = [], []
    for worker in sorted((root / WIN / "runs/formal-r01").glob("worker-*")):
        if not worker.is_dir():
            continue
        receipt = json.loads((worker / "receipt.json").read_text())
        assert receipt["status"] == "completed"
        for rel, digest in receipt["record_hashes"].items():
            raw = (worker / rel).read_bytes()
            assert hashlib.sha256(raw).hexdigest() == digest, rel
            r = json.loads(raw)
            for w in r["gates"]["write"]:
                if w["needle"] == NEEDLE:
                    writes.append(dict(task=r["task"], unit=r["unit"]["base_id"], **w))
            versions = r["versions"].values() if r["task"] == "fact" else [dict(r, item_id=r["unit"]["item_id"])]
            for v in versions:
                res = dict(C=v["results"]["C"], **v["results"][NEEDLE]["W_post"])
                for arm in ARMS:
                    x = res[arm]
                    fact = r["task"] == "fact"
                    digest = hashlib.sha256(x["answer_text"].encode()).hexdigest() if fact else None
                    label = labels[v["item_id"] + "|" + digest] if fact else None
                    row = dict(task=r["task"], unit=r["unit"]["base_id"], item=v["item_id"],
                        arm=arm, y=int(label == "follows_fact") if fact else x["Y"],
                        n=len(x["token_ids"] if fact else x["N"]["ids"]),
                        end=x["end_reason"] if fact else x["N"]["termination"],
                        stop=x["first_step_stop"] if fact else x["first_stop"],
                        positions=v["window_positions"]["W_post"])
                    if fact:
                        row.update(text_sha256=digest, label=label)
                    items.append(row)
    stats, norms = aggregate(items, writes)
    return dict(stats=stats, norms=norms, items=items, writes=writes)


if __name__ == "__main__":
    if sys.argv[1] == "--check-audit":
        report = json.loads(Path(sys.argv[2]).read_text())
        stats, norms = aggregate(report["items"], report["writes"])
        assert stats == report["stats"]
        assert norms == report["norms"]
        assert len(report["items"]) == 384
        assert len({(x["task"], x["item"], x["arm"]) for x in report["items"]}) == 384
        print("Derived ledger aggregate checks passed; no source replay or new model calls.")
    else:
        report = extract(Path(sys.argv[1]))
        Path(sys.argv[2]).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
