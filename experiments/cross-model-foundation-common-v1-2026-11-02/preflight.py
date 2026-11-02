"""F1 preflight (PLAN r3 §8.7 and §8.4–8.6) for one model.

Phase 1 (`run`): A four-cell chain (Y and margin m) and B three-arm chain forked at the
answer boundary '<identifier>:' (r02, DECISIONS D5-r) on 2 dev scenarios,
3 layers x {native[0], direction R0} x {+1/64, -1/64}; all engineering gates;
one complete deep A package and one deep B package written, closed, re-read
and hashed; throughput and bytes measured.
Phase 2 (`replay`, separate process): reload saved snapshots from disk and
check that A readouts and B WITHDRAW continuation reproduce bit-for-bit.

Usage: python preflight.py run <model_key> <outdir> [cuda:N]
       python preflight.py replay <model_key> <outdir> [cuda:N]
"""
import copy
import json
import math
import os
import statistics
import sys
import time

import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import engine as E  # noqa: E402
import panel as P  # noqa: E402

PREFLIGHT_SCENARIOS = ["DEV-ea-00", "DEV-num-01"]
DOSE = 1.0 / 64
SOURCE_MAX = 80
ARM_MAX = 64
DEEP_B_STEPS = 8
Y_TOL = 0.005


def two_softmax(ll):
    a, b = ll
    m = max(a, b)
    ea, eb = math.exp(a - m), math.exp(b - m)
    return ea / (ea + eb), eb / (ea + eb)


def strip(r):
    return {k: v for k, v in r.items() if not k.startswith("_")}


def save_pt(obj, path):
    tmp = path + ".tmp"
    torch.save(obj, tmp)
    with open(tmp, "rb") as f:
        os.fsync(f.fileno())
    os.replace(tmp, path)
    with open(path, "rb") as f:
        data = f.read()
    return {"path": os.path.basename(path), "bytes": len(data), "sha256": E.sha256_bytes(data)}


def a_item_setup(eng, it):
    e = eng.encode(it)
    ids = e["ids"]
    Pids, q, qpos = ids[:-1], ids[-1], len(ids) - 1
    cands = [eng.cont_ids(it, c) for c in it["candidates_in_order"]]
    correct_idx = it["candidates_in_order"].index(it["correct"])
    return e, Pids, q, qpos, cands, correct_idx


def a_readout(eng, cacheP, q, qpos, cands, correct_idx, q_active):
    c = copy.deepcopy(cacheP)
    eng.active = {qpos} if q_active else set()
    lq, cq = eng.step([q], c, qpos)
    eng.active = set()
    r = eng.readout(lq)
    r["_logits32"] = lq.detach().clone()
    sc = eng.score_candidates(lq, cq, qpos + 1, cands)
    probs = two_softmax([s["loglik"] for s in sc])
    m = sc[correct_idx]["loglik"] - sc[1 - correct_idx]["loglik"]
    r.update(candidates=sc, Y=probs[correct_idx], m=m)
    return r, cq


def run_A(eng, items, scales, needles, deep_dir, report):
    cells, gates, timing = [], {}, []
    deep_written = False
    for it in items:
        e, Pids, q, qpos, cands, ci = a_item_setup(eng, it)
        rec_pos = e["record_positions"]
        # clean P cache, shared by 00 and 01
        eng.active = set()
        t0 = time.monotonic()
        _, cacheP0 = eng.step(Pids, None, 0)
        fp0 = E.cache_fingerprint(cacheP0)
        r00, _ = a_readout(eng, cacheP0, q, qpos, cands, ci, False)
        timing.append(("A_clean_P_plus_00", time.monotonic() - t0))
        # gate: P reuse / determinism — fresh P prefill again gives identical 00
        _, cacheP0b = eng.step(Pids, None, 0)
        r00b, _ = a_readout(eng, cacheP0b, q, qpos, cands, ci, False)
        gates.setdefault("P_reuse_bitwise", []).append(r00b["logits_sha256"] == r00["logits_sha256"])
        # gate: whole-prompt prefill vs P+q segmented
        lw, cw = eng.step(e["ids"], None, 0)
        rw = eng.readout(lw)
        scw = eng.score_candidates(lw, cw, qpos + 1, cands)
        Yw = two_softmax([s["loglik"] for s in scw])[ci]
        mw = scw[ci]["loglik"] - scw[1 - ci]["loglik"]
        gates.setdefault("segmented_vs_whole", []).append({
            "item": it["item_id"], "bitwise": rw["logits_sha256"] == r00["logits_sha256"],
            "max_abs_logit_diff": float((lw - r00["_logits32"]).abs().max()),
            "Y_diff": abs(Yw - r00["Y"]), "m_diff": abs(mw - r00["m"]), "m_clean": r00["m"],
            "greedy_equal": rw["greedy"] == r00["greedy"]})
        del cw
        # gate: recorder inert
        with eng.record({qpos, rec_pos[0]}):
            _, cP = eng.step(Pids, None, 0)
            rr, _ = a_readout(eng, cP, q, qpos, cands, ci, False)
        gates.setdefault("recorder_inert_bitwise", []).append(rr["logits_sha256"] == r00["logits_sha256"])
        cells.append({"item": it["item_id"], "cell": "00", **strip(r00)})
        for layer in eng.picks:
            for nd in needles[layer]:
                # gates: hooks installed but nothing active; and zero dose fully active
                with eng.needle(layer, nd, scales[layer], DOSE):
                    eng.active = set()
                    _, cz = eng.step(Pids, None, 0)
                    rz, _ = a_readout(eng, cz, q, qpos, cands, ci, False)
                gates.setdefault("hook_inert_bitwise", []).append(rz["logits_sha256"] == r00["logits_sha256"])
                with eng.needle(layer, nd, scales[layer], 0.0):
                    eng.active = set(rec_pos)
                    _, cz = eng.step(Pids, None, 0)
                    rz, _ = a_readout(eng, cz, q, qpos, cands, ci, True)
                gates.setdefault("zero_dose_bitwise", []).append(rz["logits_sha256"] == r00["logits_sha256"])
                for sign in (+1, -1):
                    dose = sign * DOSE
                    deep = (not deep_written and layer == eng.picks[0] and nd["kind"] == "native" and sign > 0)
                    t0 = time.monotonic()
                    eng.audit = []
                    with eng.needle(layer, nd, scales[layer], dose):
                        n3 = len(rec_pos)
                        deep_pos = {rec_pos[0], rec_pos[n3 // 3], rec_pos[(2 * n3) // 3], rec_pos[-1], qpos}
                        recs = {}
                        eng.active = set(rec_pos)
                        if deep:
                            with eng.record(deep_pos) as rp1:
                                _, cacheP1 = eng.step(Pids, None, 0)
                            recs["P_needle"] = rp1
                            eng.active = set()
                            with eng.record(deep_pos) as rp0:
                                _, cP0d = eng.step(Pids, None, 0)
                            del cP0d
                            recs["P_clean"] = rp0
                        else:
                            _, cacheP1 = eng.step(Pids, None, 0)
                        eng.active = set()
                        fp1 = E.cache_fingerprint(cacheP1)
                        out = {}
                        for cell, base, qa in (("10", cacheP1, False), ("11", cacheP1, True), ("01", cacheP0, True)):
                            if deep:
                                with eng.record({qpos}) as rq:
                                    out[cell], _ = a_readout(eng, base, q, qpos, cands, ci, qa)
                                recs[f"q_{cell}"] = rq
                            else:
                                out[cell], _ = a_readout(eng, base, q, qpos, cands, ci, qa)
                        gates.setdefault("cache_isolation", []).append(
                            E.cache_fingerprint(cacheP1)["sha256"] == fp1["sha256"]
                            and E.cache_fingerprint(cacheP0)["sha256"] == fp0["sha256"])
                    timing.append(("A_needle_P_plus_3cells", time.monotonic() - t0))
                    aud = summarize_audit(eng.audit)
                    gates.setdefault("write_audit", []).append(aud)
                    Y = {"00": r00["Y"], **{c: out[c]["Y"] for c in out}}
                    mm = {"00": r00["m"], **{c: out[c]["m"] for c in out}}
                    for c in ("10", "11", "01"):
                        cells.append({"item": it["item_id"], "cell": c, "layer": layer, "needle": nd["name"],
                                      "dose": dose, **strip(out[c])})
                    cells.append({"item": it["item_id"], "summary": True, "layer": layer, "needle": nd["name"],
                                  "dose": dose, "H": Y["10"] - Y["00"], "C": Y["01"] - Y["00"],
                                  "J": Y["11"] - Y["10"] - Y["01"] + Y["00"], "Y": Y,
                                  "H_m": mm["10"] - mm["00"], "C_m": mm["01"] - mm["00"],
                                  "J_m": mm["11"] - mm["10"] - mm["01"] + mm["00"], "m": mm, "write": aud})
                    if deep:
                        files = [save_pt(cacheP0, os.path.join(deep_dir, "A_P_clean_cache.pt")),
                                 save_pt(cacheP1, os.path.join(deep_dir, "A_P_needle_cache.pt")),
                                 save_pt(recs, os.path.join(deep_dir, "A_records.pt")),
                                 save_pt({c: out[c]["_logits"] for c in out} | {"00": r00["_logits"]},
                                         os.path.join(deep_dir, "A_logits.pt"))]
                        report["deep_A"] = {"item": it["item_id"], "layer": layer, "needle": nd["name"],
                                            "dose": dose, "files": files,
                                            "package_bytes": sum(f["bytes"] for f in files),
                                            "deep_positions": sorted(deep_pos),
                                            "expected": {c: {"logits_sha256": out[c]["logits_sha256"],
                                                             "Y": out[c]["Y"]} for c in out}
                                            | {"00": {"logits_sha256": r00["logits_sha256"], "Y": r00["Y"]}},
                                            "q": q, "qpos": qpos, "cands": cands, "correct_idx": ci,
                                            "scale": scales[layer]}
                        deep_written = True
                    del cacheP1
        # light-record size per readout (full logits fp16)
        report["light_logits_bytes_per_readout"] = r00["_logits"].numel() * 2
        del cacheP0, cacheP0b
    return cells, gates, timing


def summarize_audit(audit):
    ratios, cos, proj, err, inactive, n_active = [], [], [], [], 0.0, 0
    for a in audit:
        inactive = max(inactive, a["inactive_max_abs_change"])
        for v in a["realized_norms"]:
            ratios.append(v / a["requested_norm"] if a["requested_norm"] > 0 else float("nan"))
            n_active += 1
        cos.extend(a.get("cos_to_target", []))
        proj.extend(a.get("signed_projection_ratio", []))
        err.extend(a.get("error_vector_ratio", []))
    def st(v):
        return {"min": min(v), "median": statistics.median(v), "max": max(v)} if v else None
    return {"n_active_positions": n_active, "inactive_max_abs_change": inactive,
            "ratio_min": min(ratios) if ratios else None, "ratio_max": max(ratios) if ratios else None,
            "ratio_median": statistics.median(ratios) if ratios else None,
            "within_1pct_fraction": (sum(abs(r - 1) <= 0.01 for r in ratios) / len(ratios)) if ratios else None,
            "cos_to_target": st(cos), "signed_projection_ratio": st(proj), "error_vector_ratio": st(err)}


def cache_len(cache):
    try:
        return int(cache.get_seq_length())
    except Exception:
        return None


def top_gap(logits):
    v = torch.topk(torch.log_softmax(logits, dim=-1), 2).values
    return float(v[0] - v[1])


def run_B(eng, items, scales, needles, deep_dir, report):
    """Fork at the answer boundary (DECISIONS D5-r): the generated text ends exactly at
    '<identifier>:'.  The colon token is chosen but not yet processed; WITHDRAW/REBUILD
    process it without the needle, so the first answer token is chosen needle-free."""
    out, gates, timing = [], {}, []
    deep_written = False
    for it in items:
        e = eng.encode(it)
        ids, qpos, n = e["ids"], e["q"], e["n_tokens"]
        Pids, q = ids[:-1], ids[-1]
        eng.active = set()
        t0 = time.monotonic()
        _, c = eng.step(Pids, None, 0)
        lg, c = eng.step([q], c, qpos)
        toks, reads, *_ = eng.greedy(lg, c, n, SOURCE_MAX)
        timing.append(("B_clean_80", time.monotonic() - t0, len(toks)))
        text = eng.tok.decode(toks, skip_special_tokens=True)
        kb_clean = next((j for j in range(1, len(toks) + 1)
                         if P.at_boundary(it, eng.tok.decode(toks[:j], skip_special_tokens=True))), None)
        out.append({"item": it["item_id"], "arm": "CLEAN", "tokens": toks, "text": text,
                    "parse": P.parse_b(it, text), "boundary_index": kb_clean})
        del c
        for layer in eng.picks:
            for nd in needles[layer]:
                for sign in (+1, -1):
                    dose = sign * DOSE
                    deep = (not deep_written and layer == eng.picks[0] and nd["kind"] == "native" and sign > 0)
                    fork = {}
                    deep_positions = set()

                    def on_step(i, t, cache, toks_so_far):
                        if "cache" in fork:
                            return
                        if any(x in eng.stop_ids for x in toks_so_far):
                            return
                        if P.at_boundary(it, eng.tok.decode(toks_so_far, skip_special_tokens=True)):
                            kb = len(toks_so_far)
                            fork.update(cache=copy.deepcopy(cache), pending=t, kb=kb,
                                        cache_len=cache_len(cache))
                            if deep:
                                deep_positions.update(n + kb - 1 + j for j in range(DEEP_B_STEPS))
                    t0 = time.monotonic()
                    eng.audit = []
                    with eng.needle(layer, nd, scales[layer], dose):
                        ctx = eng.record(deep_positions) if deep else None
                        rec_src = ctx.__enter__() if ctx else None
                        try:
                            eng.active = set(e["record_positions"])
                            _, c = eng.step(Pids, None, 0)
                            eng.active = {qpos}
                            lg, c = eng.step([q], c, qpos)
                            eng.active = set()
                            src, src_reads, *_ = eng.greedy(lg, c, n, SOURCE_MAX, on_step=on_step, active_from=n)
                        finally:
                            if ctx:
                                ctx.__exit__(None, None, None)
                        eng.active = set()
                        src_text = eng.tok.decode(src, skip_special_tokens=True)
                        rec = {"item": it["item_id"], "layer": layer, "needle": nd["name"], "dose": dose,
                               "source_tokens": src, "source_text": src_text,
                               "source_parse": P.parse_b(it, src_text),
                               "write_audit": summarize_audit(eng.audit), "fork": {}}
                        timing.append(("B_source", time.monotonic() - t0, len(src)))
                        if "cache" not in fork:
                            reason = ("stop_before_boundary" if any(x in eng.stop_ids for x in src)
                                      else "no_boundary_within_budget")
                            rec["fork"] = {"reachable": False, "reason": reason}
                            out.append(rec)
                            continue
                        kb, pend = fork["kb"], fork["pending"]
                        pos_p = n + kb - 1
                        gates.setdefault("boundary", []).append({
                            "pending_matches_source": pend == src[kb - 1],
                            "cache_len": fork["cache_len"], "expected_cache_len": n + kb - 1,
                            "cache_len_ok": fork["cache_len"] in (None, n + kb - 1),
                            "pending_text": eng.tok.decode([pend])})
                        arms = {"CONT": {"tokens": src[:kb + ARM_MAX]}}
                        t1 = time.monotonic()
                        cw = copy.deepcopy(fork["cache"])
                        eng.active = set()
                        ctxw = eng.record(deep_positions) if deep else None
                        recw = ctxw.__enter__() if ctxw else None
                        try:
                            lgw, cw = eng.step([pend], cw, pos_p)
                            first_w = eng.readout(lgw, False)
                            tw, rw, *_ = eng.greedy(lgw, cw, pos_p + 1, ARM_MAX)
                        finally:
                            if ctxw:
                                ctxw.__exit__(None, None, None)
                        arms["WITHDRAW"] = {"tokens": src[:kb] + tw,
                                            "first_logits_sha256": first_w["logits_sha256"],
                                            "step_logits_sha256": [r["logits_sha256"] for r in rw]}
                        timing.append(("B_withdraw", time.monotonic() - t1, len(tw)))
                        del cw
                        rec["fork"] = {"reachable": True, "kb": kb, "pending": pend, "arms": arms,
                                       "fork_cache": E.cache_fingerprint(fork["cache"])}
                    # REBUILD outside the needle context
                    t1 = time.monotonic()
                    eng.active = set()
                    ctxr = eng.record(deep_positions) if deep else None
                    recr = ctxr.__enter__() if ctxr else None
                    try:
                        _, cr = eng.step(ids + src[:kb - 1], None, 0)
                        cr_fork = copy.deepcopy(cr) if deep else None
                        lgr, cr = eng.step([pend], cr, pos_p)
                        first_r = eng.readout(lgr, False)
                        tr, rr, *_ = eng.greedy(lgr, cr, pos_p + 1, ARM_MAX)
                    finally:
                        if ctxr:
                            ctxr.__exit__(None, None, None)
                    rec["fork"]["arms"]["REBUILD"] = {"tokens": src[:kb] + tr}
                    timing.append(("B_rebuild", time.monotonic() - t1, len(tr)))
                    for arm in ("CONT", "WITHDRAW", "REBUILD"):
                        a = rec["fork"]["arms"][arm]
                        a["text"] = eng.tok.decode(a["tokens"], skip_special_tokens=True)
                        a["answer_text"] = eng.tok.decode(a["tokens"][kb:], skip_special_tokens=True)
                        a["parse"] = P.parse_b(it, a["text"])
                    # G13: clean incremental vs clean prefill at the first-answer-token readout
                    _, ci_ = eng.step(Pids, None, 0)
                    lgi, ci_ = eng.step([q], ci_, qpos)
                    p = n
                    for t in src[:kb - 1]:
                        lgi, ci_ = eng.step([t], ci_, p)
                        p += 1
                    lgi, ci_ = eng.step([pend], ci_, pos_p)
                    ti, _, *_ = eng.greedy(lgi, ci_, pos_p + 1, 8)
                    a_tok = first_r["greedy"]
                    lpi, lpr = torch.log_softmax(lgi, -1), torch.log_softmax(lgr, -1)
                    gates.setdefault("rebuild_vs_incremental", []).append({
                        "bitwise": eng.readout(lgi, False)["logits_sha256"] == first_r["logits_sha256"],
                        "max_abs_logit_diff": float((lgi - lgr).abs().max()),
                        "first_answer_token_equal": int(lgi.argmax()) == a_tok,
                        "first_answer_token_logprob_diff": float((lpi[a_tok] - lpr[a_tok]).abs()),
                        "top_gap_rebuild": top_gap(lgr), "top_gap_incremental": top_gap(lgi),
                        "greedy8_equal": ti == tr[:len(ti)]})
                    del ci_, cr
                    out.append(rec)
                    if deep:
                        files = [save_pt(fork["cache"], os.path.join(deep_dir, "B_fork_source_cache.pt")),
                                 save_pt(cr_fork, os.path.join(deep_dir, "B_fork_rebuild_cache.pt")),
                                 save_pt({"source": rec_src, "withdraw": recw, "rebuild": recr},
                                         os.path.join(deep_dir, "B_fork_records.pt"))]
                        report["deep_B"] = {"item": it["item_id"], "layer": layer, "needle": nd["name"],
                                            "dose": dose, "files": files,
                                            "package_bytes": sum(f["bytes"] for f in files),
                                            "pending": pend, "pos_pending": pos_p, "kb": kb,
                                            "expected_withdraw": {
                                                "first_logits_sha256": rec["fork"]["arms"]["WITHDRAW"]["first_logits_sha256"],
                                                "step_logits_sha256": rec["fork"]["arms"]["WITHDRAW"]["step_logits_sha256"],
                                                "tokens_after_pending": rec["fork"]["arms"]["WITHDRAW"]["tokens"][kb:]}}
                        deep_written = True
                        del cr_fork
                    fork.pop("cache", None)
    return out, gates, timing


def run(key, outdir, device):
    os.makedirs(outdir, exist_ok=True)
    deep_dir = os.path.join(outdir, "deep")
    os.makedirs(deep_dir, exist_ok=True)
    t_all = time.monotonic()
    eng = E.Engine(key, device)
    report = {"model": key, "device": device, "torch": torch.__version__,
              "transformers": __import__("transformers").__version__,
              "gpu": torch.cuda.get_device_name(device), "load_seconds": eng.load_seconds,
              "picks": eng.picks, "hidden": eng.H, "intermediate": eng.intermediate,
              "down_multiplier": eng.mult, "stop_ids": eng.stop_ids, "panel_sha256": P.panel_sha256(),
              "dose": DOSE}
    report["weight_hash_before"] = eng.weight_hash()
    sc = {s["id"]: s for s in P.scenarios()}
    A_items = [P.render_item(sc[s], f, "A") for s in PREFLIGHT_SCENARIOS for f in (0, 1)]
    B_items = [P.render_item(sc[s], 0, "B") for s in PREFLIGHT_SCENARIOS]
    report["max_prompt_tokens_seen"] = max(eng.encode(it)["n_tokens"] for it in A_items + B_items)
    # residual scale from the preflight clean items (formal scale comes from calibration)
    per = {l: [] for l in eng.picks}
    for it in A_items:
        rms = eng.residual_rms(eng.encode(it)["ids"])
        for l in eng.picks:
            per[l].extend(rms[l][1:].tolist())
    scales = {l: statistics.median(per[l]) for l in eng.picks}
    report["preflight_scales"] = {str(l): v for l, v in scales.items()}
    needles = {}
    for l in eng.picks:
        ns = E.needle_set(key, l, eng.intermediate, eng.H)
        needles[l] = [ns[0], ns[4]]
    report["needles"] = {str(l): [{k: v for k, v in nd.items() if k != "vector"} for nd in needles[l]]
                         for l in eng.picks}
    report["all_needles"] = {str(l): [{k: v for k, v in nd.items() if k != "vector"}
                                      for nd in E.needle_set(key, l, eng.intermediate, eng.H)] for l in eng.picks}
    cellsA, gatesA, timeA = run_A(eng, A_items, scales, needles, deep_dir, report)
    recsB, gatesB, timeB = run_B(eng, B_items, scales, needles, deep_dir, report)
    report["weight_hash_after"] = eng.weight_hash()
    report["gates"] = {"A": gatesA, "B": gatesB,
                       "weights_unchanged": report["weight_hash_before"] == report["weight_hash_after"]}
    report["timing"] = {"A": timeA, "B": timeB}
    report["peak_gpu_bytes"] = torch.cuda.max_memory_allocated(device)
    report["wall_seconds"] = time.monotonic() - t_all
    json.dump(cellsA, open(os.path.join(outdir, "A_cells.json"), "w"))
    json.dump(recsB, open(os.path.join(outdir, "B_records.json"), "w"))
    json.dump(report, open(os.path.join(outdir, "preflight.json"), "w"), indent=1, default=str)
    print("RUN_DONE", key, round(report["wall_seconds"], 1), "s")


def replay(key, outdir, device):
    rep = json.load(open(os.path.join(outdir, "preflight.json")))
    deep_dir = os.path.join(outdir, "deep")
    eng = E.Engine(key, device)
    res = {"model": key, "A": {}, "B": {}}
    # A: reload P caches, recompute four readouts
    dA = rep["deep_A"]
    for f in dA["files"]:
        data = open(os.path.join(deep_dir, f["path"]), "rb").read()
        res["A"].setdefault("file_sha_ok", []).append(E.sha256_bytes(data) == f["sha256"])
    c0 = torch.load(os.path.join(deep_dir, "A_P_clean_cache.pt"), map_location=device, weights_only=False)
    c1 = torch.load(os.path.join(deep_dir, "A_P_needle_cache.pt"), map_location=device, weights_only=False)
    layer = dA["layer"]
    nd = [x for x in E.needle_set(key, layer, eng.intermediate, eng.H) if x["name"] == dA["needle"]][0]
    q, qpos, cands, ci = dA["q"], dA["qpos"], dA["cands"], dA["correct_idx"]
    got = {}
    got["00"], _ = a_readout(eng, c0, q, qpos, cands, ci, False)
    with eng.needle(layer, nd, dA["scale"], dA["dose"]):
        got["10"], _ = a_readout(eng, c1, q, qpos, cands, ci, False)
        got["11"], _ = a_readout(eng, c1, q, qpos, cands, ci, True)
        got["01"], _ = a_readout(eng, c0, q, qpos, cands, ci, True)
    res["A"]["cells"] = {c: {"bitwise": got[c]["logits_sha256"] == dA["expected"][c]["logits_sha256"],
                             "Y_diff": abs(got[c]["Y"] - dA["expected"][c]["Y"])} for c in got}
    # B: reload the boundary fork cache, run WITHDRAW, compare
    dB = rep.get("deep_B")
    if dB:
        for f in dB["files"]:
            data = open(os.path.join(deep_dir, f["path"]), "rb").read()
            res["B"].setdefault("file_sha_ok", []).append(E.sha256_bytes(data) == f["sha256"])
        c = torch.load(os.path.join(deep_dir, "B_fork_source_cache.pt"), map_location=device, weights_only=False)
        eng.active = set()
        lg, c = eng.step([dB["pending"]], c, dB["pos_pending"])
        first = eng.readout(lg, False)
        toks, reads, *_ = eng.greedy(lg, c, dB["pos_pending"] + 1, ARM_MAX)
        exp = dB["expected_withdraw"]
        res["B"]["boundary"] = {"first_bitwise": first["logits_sha256"] == exp["first_logits_sha256"],
                                "steps_bitwise": [r["logits_sha256"] for r in reads] == exp["step_logits_sha256"],
                                "tokens_equal": toks == exp["tokens_after_pending"]}
    json.dump(res, open(os.path.join(outdir, "replay.json"), "w"), indent=1)
    print("REPLAY_DONE", key, json.dumps(res))


if __name__ == "__main__":
    mode, key, outdir = sys.argv[1:4]
    dev = sys.argv[4] if len(sys.argv) > 4 else "cuda:0"
    {"run": run, "replay": replay}[mode](key, outdir, dev)
