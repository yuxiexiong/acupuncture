"""FA-01 forward-service acceptance (engineering; contract in FORWARD_ACCEPTANCE_CONTRACT.zh-CN.md).

  python forward_acceptance.py demo                      # offline: every judge must both PASS and FAIL on synthetic data
  python forward_acceptance.py run --profile 0p8b --out D # GPU acceptance on the real model (observer-only fixtures)

All outputs are observer-side engineering evidence; nothing is shown to any search editor.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

# ------------------------------------------------------------------------------------------- frozen thresholds
TH = {
    "F2_mean_abs": 0.05,       # nats, cross-engine mean |dlogprob|
    "F2_share_gt": 0.01,       # share of tokens with |dlogprob| > 0.5
    "F2_gt": 0.5,
    "F4_logprob_max": 1e-3,    # recomputed logprob from hidden_states[L] vs token_logprobs
    "F4_mlp_rel": 1e-2,        # ||down_proj(mlp_act) - mlp_out|| / ||mlp_out||
    "F6_max": 0.1,             # r1 only (bf16); replaced by F6_fp32_max in r2 (deviation D1)
    "F6_mean": 0.005,
    "F6_fp32_max": 1e-3,       # float32 batched vs single max |dlogprob|
    "F7_identical": 0.9,       # r1 only; not achievable (vLLM GDN has no batch-invariant mode), deviation D3
    "F7_z": 2.5,               # r2: A/A paired difference within 2.5 standard errors of 0
    "F8_rel": 2e-2,            # gen activation vs independent teacher-forced recomputation
}


def judge_cross(a, b):
    d = np.abs(np.asarray(a, float) - np.asarray(b, float))
    d = d[np.isfinite(d)]
    m, s = float(d.mean()), float((d > TH["F2_gt"]).mean())
    return {"pass": m <= TH["F2_mean_abs"] and s <= TH["F2_share_gt"], "mean_abs": m, "share_gt": s, "n": int(d.size)}


def judge_maxabs(a, b, tol):
    d = np.abs(np.asarray(a, float) - np.asarray(b, float))
    d = d[np.isfinite(d)]
    return {"pass": float(d.max()) <= tol, "max_abs": float(d.max()), "n": int(d.size)}


def judge_rel(a, b, tol):
    a, b = np.asarray(a, float), np.asarray(b, float)
    r = float(np.linalg.norm(a - b) / max(np.linalg.norm(b), 1e-30))
    return {"pass": r <= tol, "rel": r}


def judge_padding(a, b):
    d = np.abs(np.asarray(a, float) - np.asarray(b, float))
    d = d[np.isfinite(d)]
    return {"pass": float(d.max()) <= TH["F6_max"] and float(d.mean()) <= TH["F6_mean"],
            "max_abs": float(d.max()), "mean_abs": float(d.mean())}


def judge_identical(share):
    return {"pass": share >= TH["F7_identical"], "identical_share": share}


def judge_aa(diff, se):
    ok = diff == 0 if not se else abs(diff) <= TH["F7_z"] * se
    return {"pass": bool(ok), "difference": diff, "se": se}


def demo():
    """6.2: each judge must be satisfiable and violable on synthetic data."""
    rng = np.random.default_rng(0)
    base = rng.normal(-2, 1, 5000)
    out = {}
    cases = {
        "F2": (judge_cross(base, base + rng.normal(0, 0.01, 5000)), judge_cross(base, base + rng.normal(0, 1, 5000))),
        "F4_logprob": (judge_maxabs(base, base + 1e-5, TH["F4_logprob_max"]), judge_maxabs(base, base + 1e-2, TH["F4_logprob_max"])),
        "F4_mlp": (judge_rel(base, base * (1 + 1e-3), TH["F4_mlp_rel"]), judge_rel(base, base * 1.1, TH["F4_mlp_rel"])),
        "F6": (judge_padding(base, base + rng.normal(0, 1e-3, 5000)), judge_padding(base, base + rng.normal(0, 0.05, 5000))),
        "F7": (judge_aa(0.01, 0.02), judge_aa(0.15, 0.03)),
        "F8": (judge_rel(base, base + 1e-4, TH["F8_rel"]), judge_rel(base, base[::-1], TH["F8_rel"])),
    }
    ok = True
    for k, (p, f) in cases.items():
        out[k] = {"should_pass": p, "should_fail": f}
        ok &= p["pass"] and not f["pass"]
    out["status"] = "passed" if ok else "failed"
    return out


# ------------------------------------------------------------------------------------------------- GPU run
def run(a):
    import torch
    import forward_service as FS
    from transformers import AutoTokenizer
    prof = FS.profile(a.profile)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=False)
    rec = {"profile": a.profile, "thresholds": TH, "checks": {}, "measurements": {}, "started": time.time(),
           "script_sha256": FS.sha256_file(__file__), "service_sha256": FS.sha256_file(FS.__file__)}

    def flush():
        (out / "receipt.json").write_text(json.dumps(rec, indent=1, default=float))

    def check(name, res):
        rec["checks"][name] = res
        flush()
        print(name, json.dumps(res, default=float), flush=True)

    tok = AutoTokenizer.from_pretrained(str(prof["model"]), local_files_only=True)
    practice = FS.practice_index()
    Q = FS.load_mathqa()
    # Fixture texts: eval prompt + "<think>\n" + reference solution of 8 MATH practice items (engineering fixture only).
    math_ids = sorted(k for k in practice if k.startswith("math_train_"))[:: 900][:8]
    texts = [FS.render_prompt(tok, practice[i]["problem"] + "\n" + FS.INSTRUCTION) + practice[i]["solution"] for i in math_ids]
    ids = [tok(t, add_special_tokens=False)["input_ids"] for t in texts]
    rec["fixture_ids"] = math_ids
    rec["fixture_lengths"] = [len(x) for x in ids]

    # Fixture edit: dense Gaussian noise on one mid-layer down_proj, 50% of its norm (must change behaviour clearly).
    from safetensors import safe_open
    mid = prof["n_layers"] // 2 - 2
    name = f"model.language_model.layers.{mid}.mlp.down_proj.weight"
    with safe_open(str(prof["model"] / "model.safetensors"), "pt") as f:
        W = f.get_tensor(name).float()
    g = torch.Generator().manual_seed(7)
    noise = torch.randn(W.shape, generator=g)
    Wn = W + 0.5 * noise * (W.norm() / noise.norm())
    edits = out / "fixture_edits"
    edits.mkdir()
    np.save(edits / (name + ".npy"), Wn.numpy())
    import snapshot_edits as SE
    snap = out / "fixture_snapshot"
    SE.snapshot(prof["model"], edits, snap)
    empty_edits = out / "empty_edits"
    empty_edits.mkdir()
    empty_snap = out / "empty_snapshot"
    SE.snapshot(prof["model"], empty_edits, empty_snap)

    # F1 checkpoint identity
    cache = out / "ckpt"
    ck_empty, info_empty = FS.build_checkpoint(prof, empty_snap, cache)
    ck_fix, info_fix = FS.build_checkpoint(prof, snap, cache)
    orig_sha = FS.sha256_file(prof["model"] / "model.safetensors")
    from safetensors.torch import load_file
    sd_o, sd_f = load_file(str(prof["model"] / "model.safetensors")), load_file(str(ck_fix / "model.safetensors"))
    diff_names = [k for k in sd_o if not torch.equal(sd_o[k], sd_f[k])]
    man = json.loads((snap / "manifest.json").read_text())
    f1 = {"empty_build_sha_equals_original": info_empty["model_sha256"] == orig_sha,
          "fixture_changed_tensors": diff_names,
          "fixture_changed_values": info_fix["changed_values"],
          "manifest_effective_changed": {t["name"]: t["effective_changed_values"] for t in man["tensors"]}}
    f1["pass"] = f1["empty_build_sha_equals_original"] and diff_names == [name] and \
        f1["fixture_changed_values"] == f1["manifest_effective_changed"]
    del sd_o, sd_f
    check("F1_checkpoint_identity", f1)

    # HF readouts (GPU 0)
    os.environ["CUDA_VISIBLE_DEVICES"] = "0"
    R = FS.Reader(prof["model"], "cuda:0")
    L = prof["n_layers"]
    hs_req, mlp_req = [0, L // 2, L], [mid]
    single = []
    for s in ids:
        r = R.run([s], hs=hs_req, mlp=mlp_req, want_last=True)
        single.append({"lp": R.logprobs(r["last"], [s])[0][0].numpy(),
                       "hs": {l: r["cap"][("hs", l)][0].float().cpu() for l in hs_req},
                       "mlp": r["cap"][("mlp", mid)][0].float().cpu(), "last": r["last"][0].float().cpu()})
    # F5 hook neutrality: no hooks
    plain = [R.logprobs(R.run([s], want_last=True)["last"], [s])[0][0].numpy() for s in ids]
    check("F5_hook_neutral", {"pass": all(np.array_equal(p, s["lp"], equal_nan=True) for p, s in zip(plain, single))})
    # F4 index identity
    worst_lp, worst_mlp, emb_ok = 0.0, 0.0, True
    for s, x in zip(ids, single):
        h = x["hs"][L].to("cuda:0").to(torch.bfloat16)
        lp = R.lm_head(R.norm(h[None])[0]).float().log_softmax(-1)[:-1].gather(1, torch.tensor(s[1:], device="cuda:0")[:, None])[:, 0].cpu().numpy()
        worst_lp = max(worst_lp, float(np.abs(lp - x["lp"][1:]).max()))
        emb = R.embed(torch.tensor(s, device="cuda:0")).float().cpu()
        emb_ok &= torch.equal(emb, x["hs"][0])
        cap = {}
        hk = R.layers[mid].mlp.register_forward_hook(lambda m, i, o: cap.__setitem__("o", o))
        R.run([s])
        hk.remove()
        y = R.layers[mid].mlp.down_proj(x["mlp"].to("cuda:0").to(torch.bfloat16)).float().cpu()
        o = cap["o"][0].float().cpu()
        worst_mlp = max(worst_mlp, float((y - o).norm() / o.norm()))
    f4 = {"logprob_from_hidden_L_max_abs": worst_lp, "mlp_down_proj_rel": worst_mlp, "embedding_equal": bool(emb_ok)}
    f4["pass"] = worst_lp <= TH["F4_logprob_max"] and worst_mlp <= TH["F4_mlp_rel"] and emb_ok
    check("F4_index_identity", f4)
    # F6 (r2, deviation D1): padding logic tested in float32; the bfloat16 batch-shape difference is only measured
    # (it is the batch null for F2; r1 showed bf16 max 0.33 while float32 max was 4e-5)
    r = R.run(ids, want_last=True)
    batched = [x[0].numpy() for x in R.logprobs(r["last"], ids)]
    d16 = np.abs(np.concatenate([b[1:] for b in batched]) - np.concatenate([s["lp"][1:] for s in single]))
    rec["measurements"]["bf16_batch_null"] = {"max": float(np.nanmax(d16)), "mean": float(np.nanmean(d16)),
                                              "p99": float(np.nanpercentile(d16, 99)),
                                              "share_gt_0.5": float(np.nanmean(d16 > 0.5))}
    hf_orig = np.concatenate([s["lp"][1:] for s in single])
    del R, r
    torch.cuda.empty_cache()
    R32 = FS.Reader(prof["model"], "cuda:0")
    R32.model.to(torch.float32)
    s32 = np.concatenate([R32.logprobs(R32.run([s], want_last=True)["last"], [s])[0][0].numpy()[1:] for s in ids])
    r = R32.run(ids, want_last=True)
    b32 = np.concatenate([x[0].numpy()[1:] for x in R32.logprobs(r["last"], ids)])
    check("F6_padding_fp32", judge_maxabs(b32, s32, TH["F6_fp32_max"]))
    del R32, r
    torch.cuda.empty_cache()
    R2 = FS.Reader(ck_fix, "cuda:0")
    hf_fix = np.concatenate([R2.logprobs(R2.run([s], want_last=True)["last"], [s])[0][0].numpy()[1:] for s in ids])
    del R2
    torch.cuda.empty_cache()

    # vLLM prompt logprobs (subprocess, GPU 0)
    def vllm_prompt_lp(ckpt, tag):
        script = out / f"vllm_lp_{tag}.py"
        script.write_text(
            "import json,sys\nfrom vllm import LLM, SamplingParams\nif __name__ == '__main__':\n"
            f"    ids=json.load(open({str(out / 'ids.json')!r}))\n"
            f"    llm=LLM(model={str(ckpt)!r},dtype='bfloat16',seed=0,gpu_memory_utilization=0.6,max_model_len=8192,enable_prefix_caching=False)\n"
            "    o=llm.generate([{'prompt_token_ids':s} for s in ids],SamplingParams(max_tokens=1,prompt_logprobs=0,temperature=0),use_tqdm=False)\n"
            "    res=[[None]+[d[t].logprob for d,t in zip(x.prompt_logprobs[1:],s[1:])] for x,s in zip(o,ids)]\n"
            f"    json.dump(res,open({str(out / f'vllm_lp_{tag}.json')!r},'w'))\n")
        (out / "ids.json").write_text(json.dumps(ids))
        t0 = time.time()
        subprocess.run([sys.executable, str(script)], check=True, env=dict(os.environ, CUDA_VISIBLE_DEVICES="0"),
                       stdout=open(out / f"vllm_lp_{tag}.log", "w"), stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL)
        rec["measurements"][f"vllm_lp_{tag}_seconds"] = time.time() - t0
        return np.concatenate([np.array(x[1:], float) for x in json.loads((out / f"vllm_lp_{tag}.json").read_text())])

    v_orig = vllm_prompt_lp(prof["model"], "orig")
    v_fix = vllm_prompt_lp(ck_fix, "fixture")
    f2 = judge_cross(v_orig, hf_orig)
    f2["negative_control_vllm_orig_vs_hf_fixture"] = judge_cross(v_orig, hf_fix)
    f2["fixture_effect_hf_mean_abs"] = float(np.nanmean(np.abs(hf_fix - hf_orig)))
    f2["pass"] = f2["pass"] and not f2["negative_control_vllm_orig_vs_hf_fixture"]["pass"]
    check("F2_cross_engine_original", f2)
    check("F3_cross_engine_edited", judge_cross(v_fix, hf_fix))

    # F7 A/A both (empty snapshot) + F8 activation consistency, via the real serve path
    work, arch = out / "work", out / "archive"
    work.mkdir()
    gsm = sorted(k for k in practice if k.startswith("gsm8k_"))[::233][:32]
    req = {"type": "generate", "model": "both", "problems": gsm, "n": 2, "max_tokens": 1024,
           "activations": {"layers": [L // 2], "mlp": False}}
    (out / "req_aa.json").write_text(json.dumps(req))
    t0 = time.time()
    env = dict(os.environ)
    env.pop("CUDA_VISIBLE_DEVICES", None)
    subprocess.run([sys.executable, str(HERE / "forward_service.py"), "serve", "--profile", a.profile, "--request",
                    str(out / "req_aa.json"), "--k", "1", "--work", str(work), "--archive", str(arch), "--snapshot",
                    str(empty_snap)], check=True, env=env, stdout=open(out / "serve_aa.log", "w"),
                   stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL)
    rec["measurements"]["aa_serve_seconds"] = time.time() - t0
    res = json.loads((arch / "pass_1.result.json").read_text())
    pr = res["paired"]
    f7 = judge_aa(pr["accuracy_difference"], pr["standard_error"])
    f7["identical_share_descriptive"] = pr["identical_texts"] / pr["answers"]
    ro = {(r["key"], r["sample"]): r["token_ids"] for r in map(json.loads, open(arch / "gen_1_original.raw.jsonl"))}
    re_ = {(r["key"], r["sample"]): r["token_ids"] for r in map(json.loads, open(arch / "gen_1_edited.raw.jsonl"))}
    f7["first_divergence_descriptive"] = sorted(next((i for i, (x, y) in enumerate(zip(ro[k], re_[k])) if x != y),
                                                     min(len(ro[k]), len(re_[k]))) for k in ro)
    f7["paired"] = pr
    f7["arms"] = res["arms"]
    check("F7_aa_both", f7)
    # F8: recompute 4 activation rows with an independent teacher-forced pass (original arm)
    os.environ["CUDA_VISIBLE_DEVICES"] = "0"
    idx = json.loads((work / "gen_1_acts/original/index.json").read_text())
    acts = np.load(work / f"gen_1_acts/original/residual_{L // 2}.npy")
    rows = [json.loads(l) for l in open(arch / "gen_1_original.raw.jsonl")]
    R = FS.Reader(prof["model"], "cuda:0")
    worst = 0.0
    for row in range(4):
        rr = rows[row]
        p_ids = tok(FS.render_prompt(tok, practice[rr["key"]]["problem"] + "\n" + FS.INSTRUCTION), add_special_tokens=False)["input_ids"]
        seq = p_ids + rr["token_ids"][:8192]
        h = R.run([seq], hs=[L // 2])["cap"][("hs", L // 2)][0].float().cpu().numpy()
        ref = np.stack([h[len(p_ids) - 1], h[len(p_ids):].mean(0)])
        worst = max(worst, judge_rel(acts[row], ref, TH["F8_rel"])["rel"])
        assert idx["samples"][row]["key"] == rr["key"]
    check("F8_activation_consistency", {"pass": worst <= TH["F8_rel"], "worst_rel": worst})
    del R
    torch.cuda.empty_cache()

    # F9 measurements: long teacher-forced text and full-batch generation throughput
    longtxt = texts[0]
    while len(tok(longtxt, add_special_tokens=False)["input_ids"]) < 32000:
        longtxt += "\n" + practice[math_ids[1]]["solution"]
    longids = tok(longtxt, add_special_tokens=False)["input_ids"][:32768]
    R = FS.Reader(prof["model"], "cuda:0")
    torch.cuda.reset_peak_memory_stats()
    t0 = time.time()
    r = R.run([longids], hs=[L // 2, L], mlp=[mid], want_last=True)
    R.logprobs(r["last"], [longids])
    torch.cuda.synchronize()
    rec["measurements"]["tf_32k_seconds"] = time.time() - t0
    rec["measurements"]["tf_32k_peak_gb"] = torch.cuda.max_memory_allocated() / 1e9
    del R, r
    torch.cuda.empty_cache()
    flush()
    reqt = {"type": "generate", "model": "original", "problems": sorted(k for k in practice if k.startswith("math_train_"))[::28][:256],
            "n": 1, "max_tokens": 4096}
    (out / "req_tp.json").write_text(json.dumps(reqt))
    t0 = time.time()
    subprocess.run([sys.executable, str(HERE / "forward_service.py"), "serve", "--profile", a.profile, "--request",
                    str(out / "req_tp.json"), "--k", "2", "--work", str(work), "--archive", str(arch)], check=True, env=env,
                   stdout=open(out / "serve_tp.log", "w"), stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL)
    tp = json.loads((arch / "pass_2.result.json").read_text())
    eng = tp["arms"]["original"]["engine"]
    rec["measurements"]["throughput_256x4096"] = {"serve_seconds": time.time() - t0, **eng,
                                                  "tokens_per_second": eng["tokens"] / eng["seconds"],
                                                  "cut_share": tp["arms"]["original"]["cut_share"]}
    rec["status"] = "passed" if all(c["pass"] for c in rec["checks"].values()) else "failed"
    rec["wall_seconds"] = time.time() - rec["started"]
    flush()
    print(json.dumps({"status": rec["status"], "wall_seconds": rec["wall_seconds"]}))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["demo", "run"])
    ap.add_argument("--profile")
    ap.add_argument("--out")
    a = ap.parse_args()
    if a.cmd == "demo":
        r = demo()
        print(json.dumps(r, indent=1, default=float))
        sys.exit(0 if r["status"] == "passed" else 1)
    run(a)
