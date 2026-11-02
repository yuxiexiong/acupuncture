"""Summarize preflight.json (+ replay.json, A_cells.json, B_records.json) per model dir.

r02 additions: margin m and its four-cell differences; write direction cosine,
signed projection and +/- symmetry; numerical noise floor for m (segmented vs
whole); B answer-boundary fork; first-answer-token checks in G13.
"""
import json
import os
import statistics
import sys

Y_TOL = 0.005


def st(v):
    v = [x for x in v if x is not None]
    return {"min": min(v), "median": statistics.median(v), "max": max(v), "n": len(v)} if v else None


def summarize(d):
    rep = json.load(open(os.path.join(d, "preflight.json")))
    g = rep["gates"]
    A, B = g["A"], g["B"]
    s = {"model": rep["model"], "wall_s": round(rep["wall_seconds"], 1),
         "peak_gpu_GiB": round(rep["peak_gpu_bytes"] / 2**30, 2), "weights_unchanged": g["weights_unchanged"]}
    for name in ("P_reuse_bitwise", "recorder_inert_bitwise", "hook_inert_bitwise", "zero_dose_bitwise", "cache_isolation"):
        v = A.get(name, [])
        s[name] = f"{sum(v)}/{len(v)}"
    seg = A.get("segmented_vs_whole", [])
    s["G9_segmented_vs_whole"] = {"greedy_equal": f"{sum(x['greedy_equal'] for x in seg)}/{len(seg)}",
                                  "max_abs_logit_diff": max(x["max_abs_logit_diff"] for x in seg),
                                  "max_Y_diff": max(x["Y_diff"] for x in seg),
                                  "max_m_diff": max(x.get("m_diff", float("nan")) for x in seg),
                                  "clean_m": st([x.get("m_clean") for x in seg])}
    s["m_noise_floor"] = s["G9_segmented_vs_whole"]["max_m_diff"]
    wa = A.get("write_audit", [])
    s["write_A"] = {"inactive_max_abs_change": max(x["inactive_max_abs_change"] for x in wa),
                    "norm_ratio": st([x["ratio_min"] for x in wa] + [x["ratio_max"] for x in wa]),
                    "within_1pct_fraction_min": min(x["within_1pct_fraction"] for x in wa),
                    "cos_to_target_min": min(x["cos_to_target"]["min"] for x in wa if x.get("cos_to_target")),
                    "signed_projection_ratio": st([x["signed_projection_ratio"]["median"] for x in wa
                                                   if x.get("signed_projection_ratio")])}
    cells = json.load(open(os.path.join(d, "A_cells.json")))
    summ = [c for c in cells if c.get("summary")]
    # +/- symmetry of the realized write: pair (item, layer, needle) across dose signs
    pairs = {}
    for c in summ:
        pairs.setdefault((c["item"], c["layer"], c["needle"]), {})[c["dose"] > 0] = c["write"]["signed_projection_ratio"]["median"]
    asym = [abs(v[True] - v[False]) for v in pairs.values() if True in v and False in v]
    s["write_A_sign_asymmetry"] = st(asym)
    s["A_clean_Y"] = [c["Y"] for c in cells if c.get("cell") == "00"]
    s["A_absH_Y"] = st([abs(c["H"]) for c in summ])
    s["A_absH_m"] = st([abs(c["H_m"]) for c in summ])
    s["A_absC_m"] = st([abs(c["C_m"]) for c in summ])
    s["A_absJ_m"] = st([abs(c["J_m"]) for c in summ])
    if s["m_noise_floor"] == s["m_noise_floor"]:
        s["A_H_m_above_noise_floor"] = f"{sum(abs(c['H_m']) > s['m_noise_floor'] for c in summ)}/{len(summ)}"
    recs = json.load(open(os.path.join(d, "B_records.json")))
    clean_b = [r for r in recs if r.get("arm") == "CLEAN"]
    src = [r for r in recs if "fork" in r]
    s["B_clean"] = [(r["parse"][0], r["boundary_index"], r["text"][:40]) for r in clean_b]
    reach = [r for r in src if r["fork"].get("reachable")]
    s["B_boundary_reachable"] = f"{len(reach)}/{len(src)}"
    s["B_unreachable_reasons"] = {}
    for r in src:
        if not r["fork"].get("reachable"):
            k = r["fork"]["reason"]
            s["B_unreachable_reasons"][k] = s["B_unreachable_reasons"].get(k, 0) + 1
    s["B_boundary_index"] = st([r["fork"]["kb"] for r in reach])
    for arm in ("CONT", "WITHDRAW", "REBUILD"):
        s[f"B_{arm}_delivered"] = f"{sum(1 for r in reach if r['fork']['arms'][arm]['parse'][1])}/{len(reach)}"
    s["B_answer_examples"] = [(r["fork"]["arms"]["WITHDRAW"]["text"][:30]) for r in reach[:2]]
    bd = B.get("boundary", [])
    s["G12_boundary"] = {"pending_matches": f"{sum(x['pending_matches_source'] for x in bd)}/{len(bd)}",
                         "cache_len_ok": f"{sum(x['cache_len_ok'] for x in bd)}/{len(bd)}",
                         "cache_len_reported": f"{sum(x['cache_len'] is not None for x in bd)}/{len(bd)}",
                         "pending_texts": sorted({x["pending_text"] for x in bd})}
    rv = B.get("rebuild_vs_incremental", [])
    if rv:
        s["G13_rebuild_vs_incremental"] = {
            "n": len(rv), "greedy8_equal": f"{sum(x['greedy8_equal'] for x in rv)}/{len(rv)}",
            "first_answer_token_equal": f"{sum(x['first_answer_token_equal'] for x in rv)}/{len(rv)}",
            "max_abs_logit_diff": max(x["max_abs_logit_diff"] for x in rv),
            "first_answer_token_logprob_diff": st([x["first_answer_token_logprob_diff"] for x in rv]),
            "top_gap_rebuild": st([x["top_gap_rebuild"] for x in rv])}
    wb = [r["write_audit"] for r in src]
    s["write_B"] = {"inactive_max_abs_change": max(x["inactive_max_abs_change"] for x in wb),
                    "cos_to_target_min": min(x["cos_to_target"]["min"] for x in wb if x.get("cos_to_target"))}
    t = rep["timing"]

    def tmed(rows, name):
        v = [r[1] for r in rows if r[0] == name]
        return round(statistics.median(v), 3) if v else None
    s["time_s"] = {k: tmed(t[x], k) for x, k in (("A", "A_needle_P_plus_3cells"), ("B", "B_source"),
                                                    ("B", "B_withdraw"), ("B", "B_rebuild"))}
    s["deep_A_bytes"] = rep.get("deep_A", {}).get("package_bytes")
    s["deep_B_bytes"] = rep.get("deep_B", {}).get("package_bytes")
    s["max_prompt_tokens_seen"] = rep.get("max_prompt_tokens_seen")
    rp = os.path.join(d, "replay.json")
    if os.path.exists(rp):
        r = json.load(open(rp))
        s["replay"] = {"A_files_sha_ok": all(r["A"].get("file_sha_ok", [])),
                       "A_cells_bitwise": all(v["bitwise"] for v in r["A"]["cells"].values()),
                       "B": r["B"].get("boundary"), "B_files_sha_ok": all(r["B"].get("file_sha_ok", [True]))}
    return s


if __name__ == "__main__":
    print(json.dumps([summarize(d) for d in sys.argv[1:]], indent=1, ensure_ascii=False))
