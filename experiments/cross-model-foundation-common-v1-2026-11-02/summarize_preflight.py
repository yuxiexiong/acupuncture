"""Summarize preflight.json (+ replay.json) for one or more model dirs into gate verdicts and resources."""
import json
import os
import statistics
import sys

Y_TOL = 0.005
WRITE_TOL = 0.01


def summarize(d):
    rep = json.load(open(os.path.join(d, "preflight.json")))
    g = rep["gates"]
    A, B = g["A"], g["B"]
    s = {"model": rep["model"], "wall_s": round(rep["wall_seconds"], 1), "load_s": round(rep["load_seconds"], 1),
         "peak_gpu_GiB": round(rep["peak_gpu_bytes"] / 2**30, 2)}
    s["weights_unchanged"] = g["weights_unchanged"]
    for name in ("P_reuse_bitwise", "recorder_inert_bitwise", "hook_inert_bitwise", "zero_dose_bitwise", "cache_isolation"):
        v = A.get(name, [])
        s[name] = f"{sum(v)}/{len(v)}"
    seg = A.get("segmented_vs_whole", [])
    s["segmented_vs_whole"] = {"bitwise": f"{sum(x['bitwise'] for x in seg)}/{len(seg)}",
                               "max_abs_logit_diff": max(x["max_abs_logit_diff"] for x in seg),
                               "max_Y_diff": max(x["Y_diff"] for x in seg),
                               "greedy_equal": f"{sum(x['greedy_equal'] for x in seg)}/{len(seg)}",
                               "pass": all(x["Y_diff"] <= Y_TOL and x["greedy_equal"] for x in seg)}
    wa = A.get("write_audit", [])
    s["write_audit_A"] = {"inactive_max_abs_change": max(x["inactive_max_abs_change"] for x in wa),
                          "ratio_min": min(x["ratio_min"] for x in wa), "ratio_max": max(x["ratio_max"] for x in wa),
                          "within_1pct_fraction_min": min(x["within_1pct_fraction"] for x in wa)}
    rv = B.get("rebuild_vs_incremental", [])
    if rv:
        s["rebuild_vs_incremental"] = {"n": len(rv), "bitwise": f"{sum(x['bitwise'] for x in rv)}/{len(rv)}",
                                       "max_abs_logit_diff": max(x["max_abs_logit_diff"] for x in rv),
                                       "greedy8_equal": f"{sum(x['greedy8_equal'] for x in rv)}/{len(rv)}"}
    cells = json.load(open(os.path.join(d, "A_cells.json")))
    summ = [c for c in cells if c.get("summary")]
    clean = [c for c in cells if c.get("cell") == "00"]
    s["A_clean_Y"] = [round(c["Y"], 3) for c in clean]
    s["A_clean_eos_prob_max"] = max(c["eos_set_prob"] for c in clean)
    s["A_absH_median"] = statistics.median(abs(c["H"]) for c in summ)
    s["A_absC_median"] = statistics.median(abs(c["C"]) for c in summ)
    s["A_absJ_max"] = max(abs(c["J"]) for c in summ)
    recs = json.load(open(os.path.join(d, "B_records.json")))
    src = [r for r in recs if "forks" in r]
    clean_b = [r for r in recs if r.get("arm") == "CLEAN"]
    s["B_clean_parse"] = [r["parse"][0] for r in clean_b]
    s["B_clean_text"] = [r["text"][:60] for r in clean_b]
    s["B_sources"] = len(src)
    for k in ("4", "16"):
        reach = [r for r in src if r["forks"][k]["reachable"]]
        s[f"B_k{k}_reachable"] = f"{len(reach)}/{len(src)}"
        for arm in ("CONT", "WITHDRAW", "REBUILD"):
            s[f"B_k{k}_{arm}_delivered"] = sum(1 for r in reach if r["forks"][k]["arms"][arm]["parse"][1])
    s["B_source_parse"] = {}
    for r in src:
        s["B_source_parse"][r["source_parse"][0]] = s["B_source_parse"].get(r["source_parse"][0], 0) + 1
    wb = [r["write_audit"] for r in src]
    s["write_audit_B"] = {"inactive_max_abs_change": max(x["inactive_max_abs_change"] for x in wb),
                          "ratio_min": min(x["ratio_min"] for x in wb if x["ratio_min"] is not None),
                          "ratio_max": max(x["ratio_max"] for x in wb if x["ratio_max"] is not None)}
    t = rep["timing"]
    def tmed(rows, name):
        v = [r[1] for r in rows if r[0] == name]
        return round(statistics.median(v), 3) if v else None
    s["time_s"] = {"A_needle_P_plus_3cells": tmed(t["A"], "A_needle_P_plus_3cells"),
                   "A_clean_P_plus_00": tmed(t["A"], "A_clean_P_plus_00"),
                   "B_source": tmed(t["B"], "B_source"), "B_withdraw": tmed(t["B"], "B_withdraw"),
                   "B_rebuild": tmed(t["B"], "B_rebuild"), "B_clean_80": tmed(t["B"], "B_clean_80")}
    s["deep_A_bytes"] = rep.get("deep_A", {}).get("package_bytes")
    s["deep_A_files"] = {f["path"]: f["bytes"] for f in rep.get("deep_A", {}).get("files", [])}
    s["deep_B_bytes"] = rep.get("deep_B", {}).get("package_bytes")
    if "deep_B" in rep:
        s["deep_B_files"] = {f["path"]: f["bytes"] for fk in rep["deep_B"]["forks"].values() for f in fk["files"]}
        s["deep_B_forks"] = sorted(rep["deep_B"]["forks"])
    s["light_logits_bytes_per_readout"] = rep.get("light_logits_bytes_per_readout")
    rp = os.path.join(d, "replay.json")
    if os.path.exists(rp):
        r = json.load(open(rp))
        s["replay"] = {"A_files_sha_ok": all(r["A"].get("file_sha_ok", [])),
                       "A_cells_bitwise": {c: v["bitwise"] for c, v in r["A"]["cells"].items()},
                       "B": {k: v for k, v in r["B"].items() if k != "file_sha_ok"},
                       "B_files_sha_ok": all(r["B"].get("file_sha_ok", [True]))}
    return s


if __name__ == "__main__":
    out = [summarize(d) for d in sys.argv[1:]]
    print(json.dumps(out, indent=1, ensure_ascii=False))
