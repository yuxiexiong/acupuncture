"""Step 3 (PLAN r3 §4): formal residual scale s per model x picked layer.

s = median pre-MLP residual RMS over clean runs of all 12 dev scenarios x 2 facts
(A prompts), positions >= 1 (D3).  Development data only.

Usage: python scales.py <model_key> <outdir> [cuda:N]
"""
import json
import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import engine as E  # noqa: E402
import panel as P  # noqa: E402


def main(key, outdir, device):
    os.makedirs(outdir, exist_ok=True)
    eng = E.Engine(key, device)
    items = [P.render_item(s, f, "A") for s in P.scenarios() if s["split"] == "dev" for f in (0, 1)]
    assert len(items) == 24
    per = {l: [] for l in eng.picks}
    per_item = {}
    for it in items:
        rms = eng.residual_rms(eng.encode(it)["ids"])
        per_item[it["item_id"]] = {str(l): statistics.median(rms[l][1:].tolist()) for l in eng.picks}
        for l in eng.picks:
            per[l].extend(rms[l][1:].tolist())
    out = {"model": key, "picks": eng.picks, "hidden": eng.H, "n_items": len(items),
           "scales": {str(l): statistics.median(per[l]) for l in eng.picks},
           "n_positions": {str(l): len(per[l]) for l in eng.picks},
           "item_medians": per_item, "panel_sha256": P.panel_sha256()}
    json.dump(out, open(os.path.join(outdir, "scales.json"), "w"), indent=1)
    print("SCALES_DONE", key, out["scales"])


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "cuda:0")
