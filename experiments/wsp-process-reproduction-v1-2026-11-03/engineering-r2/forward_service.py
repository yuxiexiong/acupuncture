"""WSP forward service (reconstruction; the author's server is unpublished).

Implements the two pass types of the frozen task prompt (exp8 p50c t001):
  generate        vLLM, evaluation protocol, one seed per (item, sample) fixed by the item, optional "both" pairing
  teacher_forced  Hugging Face forward with explicit hooks (no generation)

Index conventions (written into every meta file):
  residual index r in 0..L : 0 = output of embed_tokens, r = output of decoder module r-1; r=L is after final norm (HF hidden_states convention)
  mlp / attention layer i  : decoder module i (0-based), mlp_act = input of layers.i.mlp.down_proj

Generation activations are computed by re-reading prompt + first 8,192 answer tokens with the same Hugging Face
reader used for teacher-forced passes (vLLM does not expose internals). This is an implementation choice, recorded.

Usage (observer/harness only; never inside the editor sandbox):
  python forward_service.py serve --profile 0p8b --request req.json --k 3 --work W --snapshot S --archive A
  python forward_service.py build --profile 0p8b --snapshot S --out CKPT
"""
import argparse
import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXT = Path(os.environ.get("WSP_EXT", "/workspace/acupuncture/external/wsp"))
PROFILES = {
    "0p8b": {"model": EXT / "text-Qwen3.5-0.8B"},
    "4b": {"model": EXT / "text-Qwen3.5-4B-r2"},
}
PRACTICE = EXT / "observer-upstream/exp8_math/practice"
MATHQA = EXT / "observer-upstream/exp8_math/code/mathqa.py"
INSTRUCTION = "Please reason step by step, and put your final answer within \\boxed{}."
SAMPLING = {"temperature": 0.6, "top_p": 0.95, "top_k": 20, "presence_penalty": 1.5}
LIMITS = {"gen_max": 512, "both_max": 256, "max_tokens": 32768, "tf_max_texts": 1024, "tf_max_tokens": 32768,
          "tf_total_tokens": 524288, "act_max_tokens": 8192, "topk_max": 50, "attn_max_texts": 2,
          "attn_max_tokens": 2048, "return_bytes": 6 * 10**9}
CKPT_CACHE = Path(os.environ.get("WSP_CKPT_CACHE", str(EXT / "forward-ckpt-cache")))


class RequestError(ValueError):
    """Rejected before running: does not count against the budget."""


def sha256_file(path):
    with open(path, "rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def profile(name):
    p = dict(PROFILES[name])
    cfg = json.loads((p["model"] / "config.json").read_text())
    p.update(name=name, n_layers=cfg["num_hidden_layers"], hidden=cfg["hidden_size"],
             inter=cfg["intermediate_size"], layer_types=cfg["layer_types"],
             full_attn=[i for i, t in enumerate(cfg["layer_types"]) if t == "full_attention"],
             n_heads=cfg["num_attention_heads"])
    return p


def load_mathqa():
    """Author's mathqa with only the unpublished mcqa import removed (as in scorer_probe.py)."""
    import ast
    src = MATHQA.read_text()
    tree = ast.parse(src)
    tree.body = [n for n in tree.body if not (isinstance(n, ast.Try) and any(
        isinstance(x, ast.ImportFrom) and x.module == "weightenv.lmo.tasks.mcqa" for x in n.body))]
    ns = {"__file__": str(MATHQA), "__name__": "wsp_mathqa"}
    exec(compile(tree, str(MATHQA), "exec"), ns)
    return ns


def practice_index():
    idx = {}
    for f in ("gsm8k_train.jsonl", "math_train.jsonl", "aime.jsonl"):
        for line in open(PRACTICE / f):
            r = json.loads(line)
            idx[r["id"]] = r
    return idx


def item_seed(key):
    return int(hashlib.sha256(key.encode()).hexdigest()[:8], 16) & 0x7FFFFFFF


# ----------------------------------------------------------------------------------------------------- checkpoints
def build_checkpoint(prof, snapshot, cache=CKPT_CACHE):
    """BF16 checkpoint = original text export with every validated snapshot tensor replaced (round-to-nearest-even).
    snapshot=None -> the original directory itself. Cached by snapshot manifest hash."""
    base = prof["model"]
    if snapshot is None:
        return base, {"identity": "original", "dir": str(base)}
    snapshot = Path(snapshot)
    man = json.loads((snapshot / "manifest.json").read_text())
    if man.get("status") != "validated" or Path(man["model"]).resolve() != base.resolve():
        raise RequestError("snapshot not validated")
    key = hashlib.sha256((snapshot / "manifest.json").read_bytes() + str(base).encode()).hexdigest()[:20]
    out = Path(cache) / f"{prof['name']}-{key}"
    if (out / "build.json").exists():
        info = json.loads((out / "build.json").read_text())
        if sha256_file(out / "model.safetensors") != info["model_sha256"]:
            raise RequestError("cached checkpoint hash mismatch")
        return out, info
    import numpy as np
    import torch
    from safetensors.torch import load_file, save_file
    tmp = out.with_name(out.name + ".partial")
    shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True)
    for f in base.iterdir():
        if f.is_file() and not f.name.endswith(".safetensors") and f.name != "text_export_receipt.json":
            shutil.copyfile(f, tmp / f.name)
    sd = load_file(str(base / "model.safetensors"))
    changed = {}
    for t in man["tensors"]:
        arr = np.load(snapshot / (t["name"] + ".npy"), allow_pickle=False)
        if sha256_file(snapshot / (t["name"] + ".npy")) != t["snapshot_sha256"]:
            raise RequestError(f"snapshot file hash mismatch: {t['name']}")
        new = torch.from_numpy(arr).to(sd[t["name"]].dtype).contiguous()
        assert new.shape == sd[t["name"]].shape
        eff = hashlib.sha256(new.view(torch.uint8).numpy().tobytes()).hexdigest()
        assert eff == t["effective_tensor_sha256"], t["name"]
        changed[t["name"]] = int((new != sd[t["name"]]).sum())
        sd[t["name"]] = new
    save_file(sd, str(tmp / "model.safetensors"), metadata={"format": "pt"})
    info = {"identity": "edited", "snapshot": str(snapshot), "snapshot_manifest_sha256": sha256_file(snapshot / "manifest.json"),
            "changed_values": changed, "model_sha256": sha256_file(tmp / "model.safetensors"), "dir": str(out)}
    (tmp / "build.json").write_text(json.dumps(info, indent=1))
    tmp.rename(out)
    return out, info


# ------------------------------------------------------------------------------------------------------- validation
def validate(req, prof, practice):
    if not isinstance(req, dict) or req.get("type") not in ("generate", "teacher_forced"):
        raise RequestError('"type" must be "generate" or "teacher_forced"')
    L = prof["n_layers"]
    if req["type"] == "generate":
        model = req.get("model")
        if model not in ("original", "edited", "both"):
            raise RequestError('"model" must be "original", "edited" or "both"')
        probs, prompts = req.get("problems") or [], req.get("prompts") or []
        if not isinstance(probs, list) or not isinstance(prompts, list) or not (probs or prompts):
            raise RequestError("give a non-empty list of practice ids in \"problems\" and/or user messages in \"prompts\"")
        bad = [p for p in probs if not isinstance(p, str) or p not in practice]
        if bad:
            raise RequestError(f"unknown practice ids: {bad[:5]}")
        if len(set(probs)) != len(probs):
            raise RequestError("duplicate practice ids: use n for repeated samples")
        if not all(isinstance(p, str) and p for p in prompts):
            raise RequestError("prompts must be non-empty strings")
        n = req.get("n", 1)
        if type(n) is not int or n < 1:
            raise RequestError('"n" must be a positive integer')
        total = (len(probs) + len(prompts)) * n
        cap = LIMITS["both_max"] if model == "both" else LIMITS["gen_max"]
        if total > cap:
            raise RequestError(f"items x n = {total} exceeds {cap}" + (" per model with \"both\"" if model == "both" else ""))
        mt = req.get("max_tokens", LIMITS["max_tokens"])
        if type(mt) is not int or not 1 <= mt <= LIMITS["max_tokens"]:
            raise RequestError("max_tokens must be an integer in 1..32768")
        acts = req.get("activations")
        if acts is not None:
            if not isinstance(acts, dict):
                raise RequestError("activations must be an object")
            layers = acts.get("layers", [])
            if not isinstance(layers, list) or not all(isinstance(x, int) and 0 <= x <= L for x in layers):
                raise RequestError(f"activation layers must be residual indices 0..{L}")
        return {"type": "generate", "model": model, "problems": probs, "prompts": prompts, "n": n, "max_tokens": mt,
                "activations": None if acts is None else {"layers": sorted(set(acts.get("layers", []))),
                                                          "mlp": bool(acts.get("mlp", False))}}
    model = req.get("model")
    if model not in ("original", "edited"):
        raise RequestError('teacher_forced "model" must be "original" or "edited"')
    texts, chats = req.get("texts"), req.get("chats")
    if (texts is None) == (chats is None):
        raise RequestError('give exactly one of "texts" or "chats"')
    ret = req.get("return") or {}
    if not isinstance(ret, dict):
        raise RequestError("return must be an object")
    hs = ret.get("hidden_states", [])
    mlp = ret.get("mlp_act", [])
    attn = ret.get("attn_layers", [])
    topk = ret.get("topk", 0)
    if type(topk) is not int:
        raise RequestError("topk must be an integer")
    if not all(isinstance(x, list) for x in (hs, mlp, attn)):
        raise RequestError("layer selections must be lists")
    if not all(isinstance(x, int) and 0 <= x <= L for x in hs):
        raise RequestError(f"hidden_states are residual indices 0..{L}")
    if not all(isinstance(x, int) and 0 <= x < L for x in mlp):
        raise RequestError(f"mlp_act layers are module indices 0..{L - 1}")
    if not all(x in prof["full_attn"] for x in attn):
        raise RequestError(f"attn_layers must be full-attention layers {prof['full_attn']}")
    if not 0 <= topk <= LIMITS["topk_max"]:
        raise RequestError("topk must be at most 50")
    return {"type": "teacher_forced", "model": model, "texts": texts, "chats": chats,
            "enable_thinking": bool(req.get("enable_thinking", False)),
            "return": {"token_logprobs": bool(ret.get("token_logprobs", False)), "topk": topk,
                       "hidden_states": sorted(set(hs)), "mlp_act": sorted(set(mlp)), "attn_layers": sorted(set(attn))}}


def render_prompt(tok, user_message):
    return tok.apply_chat_template([{"role": "user", "content": user_message}], tokenize=False,
                                   add_generation_prompt=True, enable_thinking=True)


def tf_token_lists(tok, req, prof):
    if req["texts"] is not None:
        if not isinstance(req["texts"], list) or not all(isinstance(t, str) for t in req["texts"]):
            raise RequestError("texts must be strings")
        strings = list(req["texts"])
    else:
        if not isinstance(req["chats"], list) or not all(isinstance(c, list) and c for c in req["chats"]):
            raise RequestError("chats must be a non-empty list of conversations")
        strings = [tok.apply_chat_template(c, tokenize=False, add_generation_prompt=False,
                                           enable_thinking=req["enable_thinking"]) for c in req["chats"]]
    ids = [tok(s, add_special_tokens=False)["input_ids"] for s in strings]
    if not ids or len(ids) > LIMITS["tf_max_texts"]:
        raise RequestError(f"1..{LIMITS['tf_max_texts']} texts")
    if any(len(x) == 0 for x in ids):
        raise RequestError("empty text")
    if max(map(len, ids)) > LIMITS["tf_max_tokens"] or sum(map(len, ids)) > LIMITS["tf_total_tokens"]:
        raise RequestError("texts exceed 32,768 tokens each or 524,288 in total")
    r = req["return"]
    if r["attn_layers"] and (len(ids) > LIMITS["attn_max_texts"] or max(map(len, ids)) > LIMITS["attn_max_tokens"]):
        raise RequestError("attn_layers: at most 2 texts of at most 2,048 tokens")
    T, N = max(map(len, ids)), len(ids)
    per_tok = 2 * (len(r["hidden_states"]) * prof["hidden"] + len(r["mlp_act"]) * prof["inter"]) \
        + 4 * r["token_logprobs"] + 8 * r["topk"] + 8
    size = N * T * per_tok - N * 4 * r["token_logprobs"] + len(r["attn_layers"]) * N * prof["n_heads"] * T * T * 2
    size += 128 * (1 + bool(r["token_logprobs"]) + 2 * bool(r["topk"]) + len(r["hidden_states"]) + len(r["mlp_act"]) + len(r["attn_layers"]))
    if size > LIMITS["return_bytes"]:
        raise RequestError(f"requested results would take {size / 1e9:.2f} GB > 6 GB; request fewer layers or texts")
    return strings, ids, size


# ---------------------------------------------------------------------------------------------------- HF reader
class Reader:
    """Hugging Face forward with explicit hooks. One instance per checkpoint."""

    def __init__(self, ckpt, device="cuda:0", eager_attn=False):
        import torch
        from transformers import AutoModelForCausalLM
        torch.set_grad_enabled(False)
        self.torch = torch
        self.model = AutoModelForCausalLM.from_pretrained(
            str(ckpt), dtype=torch.bfloat16, local_files_only=True,
            attn_implementation="eager" if eager_attn else "sdpa").to(device).eval()
        self.device = device
        m = self.model.model
        self.embed, self.layers, self.norm = m.embed_tokens, m.layers, m.norm
        self.lm_head = self.model.lm_head

    def run(self, batch_ids, hs=(), mlp=(), want_last=False, attn=()):
        """batch_ids: list of token lists. Returns dict of per-sample float32 cpu tensors (unpadded)."""
        torch = self.torch
        n, T = len(batch_ids), max(map(len, batch_ids))
        x = torch.zeros((n, T), dtype=torch.long)
        mask = torch.zeros((n, T), dtype=torch.long)
        for i, s in enumerate(batch_ids):
            x[i, :len(s)] = torch.tensor(s)
            mask[i, :len(s)] = 1
        x, mask = x.to(self.device), mask.to(self.device)
        cap, handles = {}, []
        if 0 in hs:
            handles.append(self.embed.register_forward_hook(lambda mod, a, o: cap.__setitem__(("hs", 0), o)))
        for r in hs:
            if 0 < r < len(self.layers):
                handles.append(self.layers[r - 1].register_forward_hook(
                    lambda mod, a, o, r=r: cap.__setitem__(("hs", r), o[0] if isinstance(o, tuple) else o)))
        for i in mlp:
            handles.append(self.layers[i].mlp.down_proj.register_forward_pre_hook(
                lambda mod, a, i=i: cap.__setitem__(("mlp", i), a[0])))
        try:
            out = self.model.model(input_ids=x, attention_mask=mask, output_attentions=bool(attn), use_cache=False)
        finally:
            for h in handles:
                h.remove()
        if len(self.layers) in hs:
            cap[("hs", len(self.layers))] = out.last_hidden_state
        # HF records only Qwen3_5Attention modules; GDN layers have no entry.
        full_layers = [i for i, layer in enumerate(self.layers) if layer.block_type == "full_attention"]
        attn_map = dict(zip(full_layers, out.attentions)) if attn else None
        if attn and (len(out.attentions) != len(full_layers) or any(attn_map[i] is None for i in attn)):
            raise RuntimeError("attention capture mapping mismatch")
        res = {"last": out.last_hidden_state if want_last else None, "cap": cap,
               "attn": attn_map, "lens": [len(s) for s in batch_ids]}
        return res

    def logprobs(self, last, ids_list, topk=0, chunk=2048):
        """token_logprobs[t] = log p(token t | tokens < t) (t=0 is NaN); topk at each position (next-token)."""
        torch = self.torch
        outs = []
        for i, ids in enumerate(ids_list):
            h = last[i, :len(ids)]
            lp_tok = torch.full((len(ids),), float("nan"))
            tk_ids = torch.zeros((len(ids), topk), dtype=torch.int32) if topk else None
            tk_lp = torch.zeros((len(ids), topk)) if topk else None
            tgt = torch.tensor(ids, device=h.device)
            for s in range(0, len(ids), chunk):
                lg = self.lm_head(h[s:s + chunk]).float().log_softmax(-1)
                e = min(s + chunk, len(ids))
                nxt = tgt[s + 1:e + 1]
                if len(nxt):
                    lp_tok[s + 1:s + 1 + len(nxt)] = lg[:len(nxt)].gather(1, nxt[:, None])[:, 0].cpu()
                if topk:
                    v, j = lg.topk(topk, -1)
                    tk_ids[s:e], tk_lp[s:e] = j.int().cpu(), v.cpu()
            outs.append((lp_tok, tk_ids, tk_lp))
        return outs


def batches_by_tokens(lengths, budget):
    order = sorted(range(len(lengths)), key=lambda i: -lengths[i])
    cur, out = [], []
    for i in order:
        if cur and (len(cur) + 1) * lengths[cur[0]] > budget:
            out.append(cur)
            cur = []
        cur.append(i)
    if cur:
        out.append(cur)
    return out


def teacher_forced(req, prof, ckpt, outdir, tok, device="cuda:0", token_budget=65536):
    import numpy as np
    import torch
    strings, ids, est = tf_token_lists(tok, req, prof)
    r = req["return"]
    reader = Reader(ckpt, device, eager_attn=bool(r["attn_layers"]))
    N, T = len(ids), max(map(len, ids))
    outdir.mkdir(parents=True, exist_ok=False)
    arrays = {}

    def mm(name, shape, dtype):
        arrays[name] = np.lib.format.open_memmap(outdir / f"{name}.npy", mode="w+", dtype=dtype, shape=shape)
        return arrays[name]

    tokens = mm("input_ids", (N, T), np.int64)
    tokens[:] = tok.pad_token_id or 0
    for i, s in enumerate(ids):
        tokens[i, :len(s)] = s
    if r["token_logprobs"]:
        mm("token_logprobs", (N, max(T - 1, 0)), np.float32)[:] = np.nan
    if r["topk"]:
        mm("topk_ids", (N, T, r["topk"]), np.int32)[:] = -1
        mm("topk_logprobs", (N, T, r["topk"]), np.float32)[:] = np.nan
    for l in r["hidden_states"]:
        mm(f"hidden_{l}", (N, T, prof["hidden"]), np.float16)[:] = 0
    for l in r["mlp_act"]:
        mm(f"mlp_act_{l}", (N, T, prof["inter"]), np.float16)[:] = 0
    for l in r["attn_layers"]:
        mm(f"attn_{l}", (N, prof["n_heads"], T, T), np.float16)[:] = 0
    t0 = time.time()
    for b in batches_by_tokens([len(x) for x in ids], token_budget if not r["attn_layers"] else 1):
        bid = [ids[i] for i in b]
        res = reader.run(bid, hs=r["hidden_states"], mlp=r["mlp_act"],
                         want_last=bool(r["token_logprobs"] or r["topk"]), attn=r["attn_layers"])
        if res["last"] is not None:
            lps = reader.logprobs(res["last"], bid, r["topk"])
        for j, i in enumerate(b):
            n = len(ids[i])
            if r["token_logprobs"]:
                arrays["token_logprobs"][i, :max(n-1, 0)] = lps[j][0].numpy()[1:]
            if r["topk"]:
                arrays["topk_ids"][i, :n] = lps[j][1].numpy()
                arrays["topk_logprobs"][i, :n] = lps[j][2].numpy()
            for l in r["hidden_states"]:
                arrays[f"hidden_{l}"][i, :n] = res["cap"][("hs", l)][j, :n].float().cpu().numpy()
            for l in r["mlp_act"]:
                arrays[f"mlp_act_{l}"][i, :n] = res["cap"][("mlp", l)][j, :n].float().cpu().numpy()
            for l in r["attn_layers"]:
                a = res["attn"][l]
                arrays[f"attn_{l}"][i, :, :n, :n] = a[j, :, :n, :n].float().cpu().numpy()
        del res
        torch.cuda.empty_cache()
    for a in arrays.values():
        a.flush()
    if sum(p.stat().st_size for p in outdir.glob("*.npy")) > LIMITS["return_bytes"]:
        raise RuntimeError("serialized return exceeded 6 GB")
    meta = {"n_texts": N, "padded_length": T, "lengths": [len(x) for x in ids], "padding": "right; input_ids=pad_token_id, activations=0, logprobs=NaN",
            "files": {k: list(v.shape) for k, v in arrays.items()}, "dtypes": {k: str(v.dtype) for k, v in arrays.items()},
            "conventions": {"hidden_states_r": "r=0 embeddings, r=l output of decoder layer l-1; final r=L after final norm; r in 0..%d" % prof["n_layers"],
                            "mlp_act_i": "input of layers.i.mlp.down_proj (0-based layer i)",
                            "token_logprobs": "column t = log p(input_ids[t+1] | input_ids[:t+1]); shape N,T-1",
                            "topk": "top-k of the next-token distribution at each position",
                            "attn_l": "attention probabilities of full-attention layer l [heads, query, key]"},
            "texts": strings, "model": req["model"], "edited_tensors": len(json.loads((Path(ckpt)/"build.json").read_text())["changed_values"]) if (Path(ckpt)/"build.json").exists() else 0, "estimated_bytes": est,
            "mean_token_logprob": [float(np.nanmean(arrays["token_logprobs"][i,:max(len(ids[i])-1,0)])) if len(ids[i])>1 else None for i in range(N)] if r["token_logprobs"] else None,
            "seconds": round(time.time() - t0, 2)}
    (outdir / "meta.json").write_text(json.dumps(meta, indent=1))
    del reader
    return meta


# ---------------------------------------------------------------------------------------------------- generation
def vllm_worker(args):
    """Subprocess: generate for one checkpoint. Writes one jsonl line per (item, sample)."""
    from vllm import LLM, SamplingParams
    items = json.loads(Path(args.items).read_text())
    llm = LLM(model=str(args.ckpt), tokenizer=str(args.ckpt), dtype="bfloat16", seed=0, tensor_parallel_size=1,
              gpu_memory_utilization=args.mem, max_model_len=args.max_len, max_num_seqs=args.max_seqs,
              enable_prefix_caching=False, enforce_eager=args.eager, trust_remote_code=False)
    reqs, params, keys = [], [], []
    for it in items:
        for s in range(it["n"]):
            reqs.append({"prompt_token_ids": it["prompt_ids"]})
            params.append(SamplingParams(n=1, seed=it["seed"] + s, max_tokens=it["max_tokens"], **SAMPLING))
            keys.append((it["key"], s, it["seed"] + s))
    t0 = time.time()
    outs = llm.generate(reqs, params, use_tqdm=False)
    sec = time.time() - t0
    with open(args.out, "w") as f:
        for (key, s, seed), o in zip(keys, outs):
            x = o.outputs[0]
            if x.finish_reason not in ("stop", "length"):
                raise RuntimeError(f"unfinished generation {key}/{s}: {x.finish_reason}")
            f.write(json.dumps({"key": key, "sample": s, "seed": seed, "text": x.text, "token_ids": list(x.token_ids),
                                "finish_reason": x.finish_reason}) + "\n")
    Path(args.out + ".done").write_text(json.dumps({"seconds": sec, "answers": len(keys),
                                                    "tokens": sum(len(o.outputs[0].token_ids) for o in outs)}))


def run_vllm(ckpt, items, out, gpu, eager=False, mem=0.85, max_seqs=256):
    env = dict(os.environ, CUDA_VISIBLE_DEVICES=str(gpu))
    max_len = max(len(it["prompt_ids"]) for it in items) + max(it["max_tokens"] for it in items) + 16
    Path(out + ".items.json").write_text(json.dumps(items))
    cmd = [sys.executable, str(Path(__file__).resolve()), "_vllm", "--ckpt", str(ckpt), "--items", out + ".items.json",
           "--out", out, "--mem", str(mem), "--max-len", str(max_len), "--max-seqs", str(max_seqs)] + (["--eager"] if eager else [])
    with open(out + ".log", "w") as log:
        return subprocess.Popen(cmd, env=env, stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL)


def grade_records(records, items_by_key, Q):
    for r in records:
        it = items_by_key[r["key"]]
        r["id"], r["source"] = it.get("id"), it.get("source")
        r["n_tokens"] = len(r["token_ids"])
        r["cut"] = r["finish_reason"] == "length"
        if it.get("answer") is None:
            r["pred"], r["correct"] = None, None
            continue
        pred, _ = Q["extract"](r["text"])
        r["pred"] = pred
        r["correct"] = bool(Q["is_correct"](pred, it["answer"]))
    return records


def summarize(records):
    g = [r for r in records if r["correct"] is not None]
    s = {"answers": len(records), "mean_length": round(sum(r["n_tokens"] for r in records) / len(records), 1),
         "cut_share": round(sum(r["cut"] for r in records) / len(records), 4)}
    if g:
        s["accuracy"] = round(sum(r["correct"] for r in g) / len(g), 4)
        s["graded"] = len(g)
        by = {}
        for r in g:
            by.setdefault(r["source"], []).append(r["correct"])
        s["accuracy_by_source"] = {k: {"accuracy": round(sum(v) / len(v), 4), "n": len(v)} for k, v in sorted(by.items())}
        s["failures"] = {"correct": sum(r["correct"] for r in g),
                         "wrong_answer": sum((not r["correct"]) and r["pred"] is not None and not r["cut"] for r in g),
                         "no_answer_finished": sum(r["pred"] is None and not r["cut"] for r in g),
                         "cut_at_max_tokens": sum(r["cut"] and not r["correct"] for r in g)}
    return s


def paired(orig, edit):
    """Item-clustered paired difference edited - original; transitions per (item, sample)."""
    o = {(r["key"], r["sample"]): r for r in orig if r["correct"] is not None}
    e = {(r["key"], r["sample"]): r for r in edit if r["correct"] is not None}
    if set(o) != set(e):
        raise RuntimeError("paired result coverage mismatch")
    keys = sorted(o)
    if not keys:
        return None
    per = {}
    for k in keys:
        per.setdefault(k[0], []).append(int(e[k]["correct"]) - int(o[k]["correct"]))
    d = [sum(v) / len(v) for v in per.values()]
    m = sum(d) / len(d)
    se = math.sqrt(sum((x - m) ** 2 for x in d) / (len(d) - 1) / len(d)) if len(d) > 1 else None
    return {"accuracy_difference": round(m, 4), "standard_error": None if se is None else round(se, 4),
            "items": len(d), "answers": len(keys), "wrong_to_right": sum(not o[k]["correct"] and e[k]["correct"] for k in keys),
            "right_to_wrong": sum(o[k]["correct"] and not e[k]["correct"] for k in keys),
            "identical_texts": sum(o[k]["text"] == e[k]["text"] for k in keys)}


def gen_activations(records, items_by_key, ckpt, layers, mlp, prof, outdir, device, token_budget=16384):
    """Author-shaped arrays; HF replay of exact generated token ids, not retokenized text."""
    import numpy as np
    reader = Reader(ckpt, device)
    outdir.mkdir(parents=True, exist_ok=False)
    A = LIMITS["act_max_tokens"]
    seqs = [items_by_key[r["key"]]["prompt_ids"] + r["token_ids"][:A] for r in records]
    plen = [len(items_by_key[r["key"]]["prompt_ids"]) for r in records]
    mlp_layers = [l for l in layers if l < prof["n_layers"]] if mlp else []
    N = len(records)
    arrays = {"hidden_last_prompt": np.zeros((N, len(layers), prof["hidden"]), np.float32),
              "hidden_mean_answer": np.zeros((N, len(layers), prof["hidden"]), np.float32)}
    if mlp:
        arrays.update(mlp_last_prompt=np.zeros((N, len(mlp_layers), prof["inter"]), np.float32),
                      mlp_mean_answer=np.zeros((N, len(mlp_layers), prof["inter"]), np.float32))
    for b in batches_by_tokens([len(s) for s in seqs], token_budget):
        res = reader.run([seqs[i] for i in b], hs=layers, mlp=mlp_layers)
        for j, i in enumerate(b):
            p, n = plen[i], len(seqs[i])
            for kind, selected in (("hs", layers), ("mlp", mlp_layers)):
                prefix = "hidden" if kind == "hs" else "mlp"
                for col, l in enumerate(selected):
                    v = res["cap"][(kind, l)][j].float()
                    arrays[prefix+"_last_prompt"][i,col] = v[p-1].cpu().numpy()
                    arrays[prefix+"_mean_answer"][i,col] = v[p:n].mean(0).cpu().numpy() if n > p else np.nan
        del res
    for name, values in arrays.items():
        np.save(outdir / (name+".npy"), values)
    index = {"layers": layers, "mlp_layers": mlp_layers,
             "files": {name+".npy": list(v.shape) for name,v in arrays.items()},
             "samples": [{"item": r["id"] or r["key"], "sample": r["sample"], "correct": r["correct"],
                          "tokens": min(len(r["token_ids"]), A)} for r in records],
             "implementation": "HF BF16 replay of exact generated ids; final hidden after final norm; generation aggregate float32"}
    (outdir / "index.json").write_text(json.dumps(index, indent=1))
    return {"dir": "/work/" + str(outdir.relative_to(outdir.parents[1] if outdir.name in ("original", "edited") else outdir.parent)) + "/",
            "files": index["files"]}


def generate(req, prof, ckpts, work, k, archive, tok, gpus=(0, 1), eager=False):
    if len(gpus) < (2 if req["model"] == "both" else 1):
        raise RequestError("both requires two reserved GPUs in this validated runner")
    Q = load_mathqa()
    practice = practice_index()
    items = []
    for pid in req["problems"]:
        r = practice[pid]
        items.append({"key": pid, "id": pid, "source": r["source"], "answer": r["answer"],
                      "user": r["problem"] + "\n" + INSTRUCTION, "seed": item_seed(pid)})
    for j, text in enumerate(req["prompts"]):
        items.append({"key": f"prompt_{j}", "id": None, "source": "own_prompt", "answer": None, "user": text,
                      "seed": item_seed("prompt:" + text)})
    for it in items:
        it["prompt_ids"] = tok(render_prompt(tok, it["user"]), add_special_tokens=False)["input_ids"]
        it["n"], it["max_tokens"] = req["n"], req["max_tokens"]
    by_key = {it["key"]: it for it in items}
    arms = ["original", "edited"] if req["model"] == "both" else [req["model"]]
    archive.mkdir(parents=True, exist_ok=True)
    procs = {}
    for g, arm in zip(gpus, arms):
        procs[arm] = run_vllm(ckpts[arm], items, str(archive / f"gen_{k}_{arm}.raw.jsonl"), g, eager=eager)
    try:
        for arm, p in procs.items():
            if p.wait() != 0:
                raise RuntimeError(f"vLLM worker failed for {arm}; see {archive}/gen_{k}_{arm}.raw.jsonl.log")
    finally:
        for child in procs.values():
            if child.poll() is None:
                child.terminate()
                try:
                    child.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    child.kill(); child.wait()
    result = {"pass": k, "type": "generate", "model": req["model"], "items": len(items), "n": req["n"],
              "max_tokens": req["max_tokens"], "arms": {}}
    recs = {}
    for arm in arms:
        raw = str(archive / f"gen_{k}_{arm}.raw.jsonl")
        recs[arm] = grade_records([json.loads(l) for l in open(raw)], by_key, Q)
        result["arms"][arm] = summarize(recs[arm])
        result["arms"][arm]["engine"] = json.loads(Path(raw + ".done").read_text())
        name = f"gen_{k}.jsonl" if len(arms) == 1 else f"gen_{k}_{arm}.jsonl"
        grouped = []
        for it in items:
            samples = [{"text": r["text"], "pred": r["pred"], "correct": r["correct"],
                        "tokens": r["n_tokens"], "cut": r["cut"]} for r in recs[arm] if r["key"] == it["key"]]
            if len(samples) != req["n"]:
                raise RuntimeError("generation result coverage mismatch")
            grouped.append({"id": it["id"] or it["key"], "source": it["source"], "answer": it["answer"], "samples": samples})
        with open(work / name, "x") as f:
            for row in grouped:
                f.write(json.dumps(row) + "\n")
        result["arms"][arm]["file"] = "/work/"+name
    if req["model"] == "both":
        result["paired"] = paired(recs["original"], recs["edited"])
    if req["activations"]:
        for g, arm in zip(gpus, arms):
            d = work / (f"gen_{k}_acts" if len(arms) == 1 else f"gen_{k}_acts/{arm}")
            result["arms"][arm]["activations"] = gen_activations(recs[arm], by_key, ckpts[arm], req["activations"]["layers"], req["activations"]["mlp"],
                            prof, d, f"cuda:{g}")
    return result


def public_result(result, meta=None):
    """Keep author-facing fields separate from observer-only engine/build receipts."""
    out = {"ok": True, "type": result["type"], "s": result["seconds"]}
    if meta is not None:
        out.update(lengths=meta["lengths"], files=meta["files"], edited_tensors=meta["edited_tensors"],
                   mean_token_logprob=meta["mean_token_logprob"])
        return out
    out["model"] = result["model"]
    summaries = {}
    for arm, r in result["arms"].items():
        summaries[arm] = {"generations": r["answers"], "graded": r.get("graded", 0),
            "accuracy": r.get("accuracy"), "accuracy_by_source": {k:v["accuracy"] for k,v in r.get("accuracy_by_source",{}).items()},
            "mean_tokens": r["mean_length"], "cut_share": r["cut_share"],
            "failures": {k:v for k,v in r.get("failures",{}).items() if k != "correct"}}
    if result["model"] == "both":
        out.update(summaries)
        out["files"] = {a:r["file"] for a,r in result["arms"].items()}
        acts = {a:r["activations"] for a,r in result["arms"].items() if "activations" in r}
        out["activations"] = acts or None
        p = result["paired"]
        out["paired"] = None if p is None else {"items":p["items"], "accuracy_difference":p["accuracy_difference"],
            "standard_error":p["standard_error"], "samples_wrong_to_right":p["wrong_to_right"],
            "samples_right_to_wrong":p["right_to_wrong"]}
    else:
        arm = result["model"]
        out.update(summaries[arm], file=result["arms"][arm]["file"], activations=result["arms"][arm].get("activations"))
    return out


# --------------------------------------------------------------------------------------------------------- serve
def serve(a):
    from transformers import AutoTokenizer
    prof = profile(a.profile)
    tok = AutoTokenizer.from_pretrained(str(prof["model"]), local_files_only=True)
    req = validate(json.loads(Path(a.request).read_text()), prof, practice_index())
    work, archive = Path(a.work), Path(a.archive)
    work.mkdir(parents=True, exist_ok=True)
    archive.mkdir(parents=True, exist_ok=True)
    snap = Path(a.snapshot) if a.snapshot else None
    t0 = time.time()
    ckpts, builds = {"original": prof["model"]}, {"original": {"identity": "original"}}
    if req["model"] in ("edited", "both"):
        if snap is None:
            ckpts["edited"], builds["edited"] = prof["model"], {"identity": "edited (no tensors edited)"}
        else:
            ckpts["edited"], builds["edited"] = build_checkpoint(prof, snap)
    if req["type"] == "generate":
        res = generate(req, prof, ckpts, work, a.k, archive, tok, gpus=tuple(a.gpus), eager=a.eager)
    else:
        meta = teacher_forced(req, prof, ckpts[req["model"]], work / f"fwd_{a.k}", tok, device=f"cuda:{a.gpus[0]}")
        res = {"pass": a.k, "type": "teacher_forced", "model": req["model"], "folder": f"/work/fwd_{a.k}",
               "n_texts": meta["n_texts"], "padded_length": meta["padded_length"], "files": meta["files"]}
    res["seconds"] = round(time.time() - t0, 1)
    res["builds"] = builds
    out = json.dumps(res, indent=1)
    (archive / f"pass_{a.k}.result.json").write_text(out)
    public = public_result(res, meta if req["type"] == "teacher_forced" else None)
    (archive / f"pass_{a.k}.public.json").write_text(json.dumps(public, indent=1))
    print(json.dumps(public))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("serve")
    s.add_argument("--profile", choices=sorted(PROFILES), required=True)
    s.add_argument("--request", required=True)
    s.add_argument("--k", type=int, required=True)
    s.add_argument("--work", required=True)
    s.add_argument("--archive", required=True)
    s.add_argument("--snapshot")
    s.add_argument("--eager", action="store_true")
    s.add_argument("--gpus", nargs="+", type=int, default=[0, 1])
    b = sub.add_parser("build")
    b.add_argument("--profile", choices=sorted(PROFILES), required=True)
    b.add_argument("--snapshot", required=True)
    w = sub.add_parser("_vllm")
    w.add_argument("--ckpt", required=True)
    w.add_argument("--items", required=True)
    w.add_argument("--out", required=True)
    w.add_argument("--mem", type=float, default=0.85)
    w.add_argument("--max-len", type=int, required=True)
    w.add_argument("--max-seqs", type=int, default=256)
    w.add_argument("--eager", action="store_true")
    a = ap.parse_args()
    if a.cmd == "serve":
        serve(a)
    elif a.cmd == "build":
        print(json.dumps(build_checkpoint(profile(a.profile), a.snapshot)[1], indent=1))
    else:
        vllm_worker(a)


if __name__ == "__main__":
    main()

