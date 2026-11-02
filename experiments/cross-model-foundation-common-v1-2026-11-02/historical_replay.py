"""Step 2 (PLAN r3 §8.1): historical protocol replay of L2/N5063 +1 on Qwen3.5-4B.

Uses the frozen 2026-10-29 code unchanged (early-input-control-v1, freeze-r03), the
archived context and reference (calibration) stored inside each old record, and the
old engine's generate_one / branch.  First 4 mechanism-development items by ID
(Q01..Q04): full source for each; continue/withdraw/rebuild at k=4/16 where the old
record was completed.  Compares token ids and per-step logits hashes with the old
records.  Exact same model/code/decoding -> mismatches are engineering issues first.

Usage: python historical_replay.py <outdir> [cuda:N]
"""
import glob
import hashlib
import json
import os
import sys

OLD = "/workspace/acupuncture/experiments/early-input-control-v1-2026-10-29"
RUN = os.path.join(OLD, "runs/mechanism-development-r01")
COND = "N_L02_C5063_D+1"
ITEMS = ["Q01", "Q02", "Q03", "Q04"]


def sha_file(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def find(name):
    hits = glob.glob(os.path.join(RUN, "worker-*/records", name))
    assert len(hits) == 1, (name, hits)
    return json.load(open(hits[0]))


def step_hashes(gen):
    out = []
    for r in gen.get("step_readouts", []):
        out.append(r.get("logits_sha256") or r.get("raw_logits_sha256"))
    return out


def main(outdir, device):
    outdir = os.path.abspath(outdir)
    os.makedirs(outdir, exist_ok=True)
    res = {"freeze": {}, "items": {}}
    # 1. freeze check: every file listed in freeze-r03 must still hash to its frozen value
    freeze_path = os.path.join(OLD, "freeze-r03.json")
    res["freeze"]["freeze_sha256"] = sha_file(freeze_path)
    freeze = json.load(open(freeze_path))
    root = "/workspace/acupuncture"
    bad = {rel: exp for rel, exp in freeze["files"].items() if sha_file(os.path.join(root, rel)) != exp}
    res["freeze"]["files_checked"] = len(freeze["files"])
    res["freeze"]["mismatched"] = bad
    model_cfg = "/data/models/Qwen3.5-4B-851bf6e/config.json"
    res["freeze"]["model_config_sha256_ok"] = sha_file(model_cfg) == "ddc63e1c717afa86c865bb5e01313d89d72bb53b97ad4a8a03ba8510c0621670"
    if bad or not res["freeze"]["model_config_sha256_ok"]:
        json.dump(res, open(os.path.join(outdir, "historical_replay.json"), "w"), indent=1)
        print("REPLAY_ABORT freeze mismatch", list(bad)[:5])
        return
    # 2. old engine, unchanged
    sys.path.insert(0, OLD)
    os.chdir(OLD)
    import experiment as X  # noqa: E402  (old module)
    import execution as XE  # noqa: E402
    from control_engine import ControlEngine  # noqa: E402
    meta = json.load(open(os.path.join(RUN, "worker-0/metadata.json")))
    eng = ControlEngine(meta["model_path"], X.model_spec(), device)
    for item_id in ITEMS:
        full = find(f"{item_id}__{COND}__full.json")
        context, reference, item = full["context"], full["reference"], full["item"]
        cond = full["effective_condition"]
        targets = XE._targets(eng.tokenizer, context, item)
        gen = eng.generate_one(context, reference, cond, mode="full", target_token_ids=targets)
        old = full["generation"]
        r = {"source": {"tokens_equal": gen["token_ids"] == old["token_ids"],
                        "n_old": len(old["token_ids"]), "n_new": len(gen["token_ids"]),
                        "step_hashes_equal": step_hashes(gen) == step_hashes(old),
                        "step_hashes_present": any(step_hashes(old))},
             "branches": {}}
        for k in (4, 16):
            for kind in ("continue", "withdraw", "rebuild"):
                rec = find(f"{item_id}__{COND}__fork{k:03d}_{kind}.json")
                prefix = gen["token_ids"][:k]
                if rec["status"] != "completed":
                    reach = len(prefix) >= k and not any(t in eng.stop_ids for t in prefix)
                    r["branches"][f"{k}_{kind}"] = {"old_status": rec["status"], "new_reachable": reach,
                                                    "status_consistent": not reach}
                    continue
                b = eng.branch(context, reference, cond, prefix, kind=kind, target_token_ids=targets,
                               retain_fork_logits=True)
                b.pop("_fork_logits", None)
                ob = rec["generation"]
                r["branches"][f"{k}_{kind}"] = {"old_status": "completed",
                                                "tokens_equal": b["token_ids"] == ob["token_ids"],
                                                "step_hashes_equal": step_hashes(b) == step_hashes(ob),
                                                "n_old": len(ob["token_ids"]), "n_new": len(b["token_ids"])}
        res["items"][item_id] = r
        json.dump(res, open(os.path.join(outdir, "historical_replay.json"), "w"), indent=1)
    print("REPLAY_DONE", json.dumps(res["items"])[:2000])


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "cuda:0")
