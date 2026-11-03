"""CGV-01 CPU assets (no weights).  1) G2 new-scenario token ledger: same formation rules as LVK held-out acceptance (B1 = [b+1, n-2], a = 1.0;
codes 3 tokens with a shared first token and pairwise-distinct second tokens; no straddling; scenario self-reference calibration id);
2) mu_all for G2: per direction (N4146, N1210) the FP32 equal-weight mean of the six frozen QCO leave-one-scenario-out mu (old scenarios only);
3) random unit directions u for the same-angle random rotation: NumPy PCG64 seed 20261103, standard normal per (G layer ascending, k head
ascending) x 128, normalised in FP64.  Any failure stops (no rewording).
CUDA_VISIBLE_DEVICES= python cgv_assets.py OUT_DIR"""
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'cache-state-read-use-v1-2026-11-03'))
assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
import sru_run as SR  # noqa: E402

NEW_SCEN = HERE / 'data/source/new-scenarios-r01.json'
NEW_SCEN_SHA = None          # filled from the file at freeze time (recorded in the ledger)
G2_DIRS = ('N_L00_C4146_D-1', 'N_L00_C1210_D-1')
OLD_SCEN = ('NQ01', 'NQ02', 'NQ03', 'NQ04', 'NQ05', 'NQ06')
SEED = 20261103
N_KHEADS, HEAD_DIM = 16, 128


def g2_ledger(tok, encode_text):
    exp = SR.exp
    items = exp.read(NEW_SCEN)['items']
    assert len(items) == 27 and len({i['id'] for i in items}) == 27 and len({i['prompt'] for i in items}) == 27
    led, fails = {}, []
    for it in items:
        f = []
        if it['binding'][it['query']][1] != it['target'] or it['distractors'] != [c for c in it['listed_codes'] if c != it['target']]:
            f.append('binding/distractors')
        if it['listed_codes'][0] != it['first_listed'] or not it['prompt'].startswith(it['boundary_text']):
            f.append('listed/boundary')
        if it['reference_id'] != f"GEN-{it['scenario']}-ABC-A":
            f.append('reference id')
        enc = [tok.encode(c, add_special_tokens=False) for c in it['listed_codes']]
        if any(len(e) != 3 for e in enc) or len({e[0] for e in enc}) != 1 or len({e[1] for e in enc}) != 3:
            f.append(f'code tokens {enc}')
        q_shared, t2, d2 = SR.QSTR.shared_tokens(tok, it) if not f else (None, None, None)
        ctx = exp.contexts_for(tok, [it])[it['id']]
        seg = SR.PK.label_tokens(tok, ctx, it['boundary_text'], encode_text)
        if seg['straddling_tokens']:
            f.append('straddling tokens')
        b, n = seg['b'], seg['n']
        p_, e_ = b + 1, n - 2
        if not (0 < p_ <= e_ < n - 1):
            f.append('window')
        led[it['id']] = {'item': {**it, 'base_id': it['scenario']},
                         'plan': {'base_id': it['scenario'], 'b': b, 'n': n, 'p': p_, 'e': e_, 'L': e_ - p_ + 1, 'prompt_token_sha256': exp.digest(seg['ids'])},
                         'tokens': {'q_shared': q_shared, 'target_second': t2, 'distractor_second': d2}, 'failures': f}
        if f:
            fails.append((it['id'], f))
    tot = {'prefix_tokens': sum(v['plan']['b'] + 1 for v in led.values()), 'window_tokens': sum(v['plan']['L'] for v in led.values()),
           'max_n': max(v['plan']['n'] for v in led.values()), 'max_L': max(v['plan']['L'] for v in led.values())}
    return led, fails, tot


def mu_all():
    import torch
    v = SR.load_vectors()
    out = {}
    for d in G2_DIRS:
        out[d] = torch.stack([v['mu'][f'{s}|{d}'].float() for s in OLD_SCEN]).mean(0)
    return out


def random_u():
    import numpy as np
    import torch
    rng = np.random.Generator(np.random.PCG64(SEED))
    G = (13, 14, 16, 17, 18, 20, 21, 22, 24, 25, 26, 28, 29, 30)
    u = np.zeros((len(G), N_KHEADS, HEAD_DIM))
    for j in range(len(G)):
        for h in range(N_KHEADS):
            x = rng.standard_normal(HEAD_DIM)
            u[j, h] = x / np.linalg.norm(x)
    return torch.tensor(u, dtype=torch.float64)


def main(out_dir):
    import torch
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    exp = SR.exp
    sys.path.insert(0, str(SR.T1.SOURCE))
    from control_engine import encode_text
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(exp.read(SR.T1.SOURCE / 'contract.json')['source']['model_path'])
    led, fails, tot = g2_ledger(tok, encode_text)
    res = {'status': 'passed' if not fails else 'failed', 'new_scenarios_sha256': exp.sha(NEW_SCEN), 'n': len(led), 'failures': fails, 'totals': tot, 'items': led}
    with open(out / 'g2-ledger-r01.json', 'x') as f:
        f.write(json.dumps(res, ensure_ascii=False, indent=1) + '\n')
    mu = mu_all()
    torch.save({'mu_all': mu, 'directions': list(G2_DIRS), 'scenarios': list(OLD_SCEN)}, out / 'g2-mu-all-r01.pt')
    u = random_u()
    torch.save({'u': u, 'seed': SEED, 'layers': [13, 14, 16, 17, 18, 20, 21, 22, 24, 25, 26, 28, 29, 30], 'k_heads': N_KHEADS}, out / 'random-u-r01.pt')
    man = {'g2_ledger_sha256': exp.sha(out / 'g2-ledger-r01.json'), 'g2_mu_all_sha256': exp.sha(out / 'g2-mu-all-r01.pt'),
           'random_u_sha256': exp.sha(out / 'random-u-r01.pt'), 'qco_offsets_sha256': exp.sha(SR.QKFR.QCO_OFFSETS_PT),
           'mu_all_norms': {d: float(mu[d].norm()) for d in mu}, 'u_shape': list(u.shape), 'g2_status': res['status'], 'g2_totals': tot}
    with open(out / 'assets-manifest-r01.json', 'x') as f:
        f.write(json.dumps(man, ensure_ascii=False, indent=1) + '\n')
    print(json.dumps({k: v for k, v in res.items() if k != 'items'}, ensure_ascii=False))
    print(json.dumps(man))
    sys.exit(0 if not fails else 1)


if __name__ == '__main__':
    main(sys.argv[1])
