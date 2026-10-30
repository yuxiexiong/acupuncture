"""Exploratory, outside contract r01 (decision log item 10): the same accounting on a natural input difference.
Pairs the two clean trajectories of each base (fact f1 as "T", fact f0 as "C"); token positions align when the
segment labels are identical. Zero GPU; reads the verified formal-r01 tensors only."""
import json, sys
from pathlib import Path
sys.path.insert(0, "../early-input-control-v1-2026-10-29"); sys.path.insert(0, ".")
import experiment as ex, account as A, torch
recs = {(r["item"]["id"], r["spec"]["condition_id"]): r for r in A.load_records(["runs/formal-r01"])}
out = {"schema": 1, "status": "exploratory_outside_contract", "pairs": {}}
for base in ("VAR01", "VAR02", "VRD01", "VRD02", "VRL01", "VRL02"):
    r0, r1 = recs[(f"{base}-f0-required", "clean")], recs[(f"{base}-f1-required", "clean")]
    lab0, lab1 = r0["segments"]["labels"], r1["segments"]["labels"]
    if lab0 != lab1:
        out["pairs"][base] = {"skipped": "segment labels differ"}; continue
    t = {}
    for k, r in (("f0", r0), ("f1", r1)):
        p = Path(r["_dir"]) / r["tensor_file"]; assert ex.sha(p) == r["tensor_sha256"]
        t[k] = A.from_capture(torch.load(p, map_location="cpu", weights_only=False))
    cells = []
    for layer in A.LAYERS:
        rows, _ = A.account_pair(t["f1"], t["f0"], lab0, layer)
        cells.append(next(x for x in rows if x["path"] == "main" and x["segment"] == "last"))
    p = A.pooled(cells)
    seg = {kind: {s: sum(c[f"sym_ip_Z{kind}_seg_dS"][s] for c in cells) / p["dS2"] for s in A.SEGMENTS} for kind in ("W", "R")}
    out["pairs"][base] = {"pooled": p, "classify_main": A.classify(cells, [0.0] * 3, A.RULES["main"])["branch"],
                          "sym_seg_shares": seg, "dS_over_SC": sum(c["dS"] for c in cells) / sum(c["S_C"] for c in cells),
                          "fact_tokens_differ": [i for i, (a, b) in enumerate(zip(r0["prompt_token_ids"], r1["prompt_token_ids"])) if a != b]}
ex.write("analysis/exploratory-natural-pair-r01.json", out, immutable=True)
for b, v in out["pairs"].items():
    if "pooled" in v:
        p = v["pooled"]; print(b, v["classify_main"], "dS/SC=%.3f" % v["dS_over_SC"], " ".join("%s=%.2f" % (k, p[k]) for k in ("sym_W", "sym_R", "bgT_W", "bgC_W", "sym_W_early", "sym_R_late", "rho_state", "cancel")), "diff tokens", v["fact_tokens_differ"])
        print("   W", {s: round(x, 2) for s, x in v["sym_seg_shares"]["W"].items() if s != "cand"}, "\n   R", {s: round(x, 2) for s, x in v["sym_seg_shares"]["R"].items() if s != "cand"})
    else: print(b, v)
