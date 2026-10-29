"""Engineering speed trial for early-state-localization-stage2 (not experimental data).

Adoption criterion, fixed before any run: an option is adopted only if, against the current batch-1 path,
every step's full-vocabulary logits hash, every generated token and every candidate log-likelihood is
bitwise identical. Any difference rejects the option. Workload: development items already used in stage 1,
condition N_L00_C4146_D+1 (stage-1 anchor), all eight G codes; no new G condition is run or read.

python speedtrial.py REPO_COPY MODE GPU ITEMS OUT_JSON      MODE = single | batched
"""
import copy
import json
from pathlib import Path
import sys
import time

repo, mode, gpu, n_items, out = Path(sys.argv[1]), sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
sys.path.insert(0, str(repo / 'experiments/early-state-localization-stage2-v2-2026-10-30'))
sys.path.insert(0, str(repo / 'experiments/early-input-control-v1-2026-10-29'))
import stage2 as S  # noqa: E402
L, exp = S.L, S.exp
import torch  # noqa: E402
from control_engine import ControlEngine, exact_pair, encode_text  # noqa: E402

CID = 'N_L00_C4146_D+1'


def stack(caches, types):
    new = copy.deepcopy(caches[0])
    for i, _, field in L.component_tensors(new, types):
        L._set(new.layers[i], field, torch.cat([L._get(c.layers[i], field) for c in caches], 0))
    return new


def fwd(model, ids, pos, cache):
    b = len(ids)
    dev = next(model.parameters()).device
    out = model(input_ids=torch.tensor(ids, device=dev).view(b, 1), position_ids=torch.full((b, 1), pos, device=dev),
                attention_mask=torch.ones((b, pos + 1), device=dev, dtype=torch.long), past_key_values=cache,
                use_cache=True, logits_to_keep=1)
    return out


def decode_batch(model, caches, types, last, n_prompt, stop, max_new=128):
    cache, b = stack(caches, types), len(caches)
    cur, pos, done = [last] * b, n_prompt - 1, [False] * b
    toks, hashes = [[] for _ in range(b)], [[] for _ in range(b)]
    with torch.inference_mode():
        for _ in range(max_new):
            out = fwd(model, cur, pos, cache)
            cache = out.past_key_values
            logits = out.logits[:, -1].float()
            for r in range(b):
                if done[r]:
                    continue
                t = int(logits[r].argmax())
                toks[r].append(t)
                hashes[r].append(L.tensor_hash(logits[r]))
                done[r] = t in stop
                cur[r] = t
            if all(done):
                break
            cur = [stop[0] if done[r] else cur[r] for r in range(b)]
            pos += 1
    return toks, hashes


def score_batch(model, caches, types, last, n_prompt, cand):
    cache, b = stack(caches, types), len(caches)
    cur, pos, lp = [last] * b, n_prompt - 1, [0.0] * b
    with torch.inference_mode():
        for target in cand:
            out = fwd(model, cur, pos, cache)
            cache = out.past_key_values
            ls = torch.log_softmax(out.logits[:, -1].float(), -1)
            for r in range(b):
                lp[r] += float(ls[r, target])
            cur, pos = [target] * b, pos + 1
    return lp


def main():
    source = exp.read(S.SOURCE / 'contract.json')['source']
    t0 = time.monotonic()
    engine = ControlEngine(source['model_path'], exp.model_spec(), f'cuda:{gpu}')
    exp.metadata_check(engine)
    load = time.monotonic() - t0
    model, types, stop = engine.model, L.layer_types(engine.model), engine.stop_ids
    groups = S.check_contract_groups(types)
    rows = exp.items('development')[:n_items]
    contexts = exp.contexts_for(engine.tokenizer, exp.items('development'))
    result, gens, started = {}, 0, time.monotonic()
    for item in rows:
        ref = engine.calibrate([contexts[item['reference_id']]])[0]
        prompt = encode_text(engine.tokenizer, contexts[item['id']])
        prefix, last = prompt[:-1], prompt[-1]
        cands = [exact_pair(engine.tokenizer, contexts[item['id']], c)[1] for c in item['choices']]
        C, _ = L._clean_cache(engine, prefix)
        T, _, _ = L._build_T(engine, S.engine_condition(CID), ref, prefix)
        caches = {code: S.compose_swaps(T, C, types, 'C' if code == 'CCC' else 'T',
                                        frozenset() if code == 'CCC' else S.swaps_for(groups, None, S.code_cleaned(code)))
                  for code in S.G_CODES}
        if mode == 'single':
            for code, cache in caches.items():
                g = L.decode(model, cache, last, len(prompt), stop, hash_all=True)
                lls = [L.score(model, cache, last, len(prompt), c)['loglikelihood'] for c in cands]
                result[f'{item["id"]}|{code}'] = {'tokens': g['token_ids'], 'hashes': [r['logits_sha256'] for r in g['readouts']], 'lls': lls}
                gens += 1
        else:
            codes = list(caches)
            toks, hashes = decode_batch(model, [caches[c] for c in codes], types, last, len(prompt), stop)
            lls = [score_batch(model, [caches[c] for c in codes], types, last, len(prompt), cand) for cand in cands]
            for r, code in enumerate(codes):
                result[f'{item["id"]}|{code}'] = {'tokens': toks[r], 'hashes': hashes[r], 'lls': [lls[0][r], lls[1][r]]}
                gens += 1
    wall = time.monotonic() - started
    json.dump({'mode': mode, 'gpu': gpu, 'load_seconds': load, 'wall_seconds': wall, 'generations': gens,
               'seconds_per_generation': wall / gens,
               'mean_tokens': sum(len(v['tokens']) for v in result.values()) / gens,
               'versions': engine.metadata['versions'], 'records': result}, open(out, 'w'))
    print(mode, gpu, f'{wall / gens:.2f} s/gen', gens)


if __name__ == '__main__':
    main()
