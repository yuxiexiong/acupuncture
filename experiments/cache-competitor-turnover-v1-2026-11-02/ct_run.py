"""CT-01 runner: zero model calls.  Reads NR-01 formal records + full-vocabulary logits (hash-checked), the tokenizer only.
python ct_run.py freeze PATH | run --freeze freeze-r01.json --out analysis/ct-readouts-r01.json
"""
import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
sys.path.insert(0, str(HERE))
import ct_core as K  # noqa: E402

PLAN_ID = 'CT-01-COMPETITOR-TURNOVER-v1'
NR = HERE.parent / 'cache-native-complement-recovery-v1-2026-11-02/runs/formal-r01'
PLAN_DOC = REPO / 'docs/cache-competitor-turnover-plan-v1-2026-11-02.zh-CN.md'
DIRECTIONS = ('N_L00_C4146_D-1', 'N_L00_C1210_D-1', 'R0_L00_D-1', 'N_L00_C1343_D-1')
CELLS = ('000', '100', '010', '001', '110', '101', '011', '111')
TOPK = 5


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for c in iter(lambda: f.read(1 << 20), b''):
            h.update(c)
    return h.hexdigest()


def frozen_paths():
    return sorted(HERE.glob('*.py')) + [HERE / 'CONTRACT.zh-CN.md', HERE / 'DECISIONS.zh-CN.md', PLAN_DOC, NR / 'verification.json']


def freeze(path):
    v = {'experiment': HERE.name, 'plan_id': PLAN_ID, 'files': {str(p.relative_to(REPO)): sha(p) for p in frozen_paths()}}
    with open(path, 'x') as f:
        f.write(json.dumps(v, indent=2) + '\n')
    return {'path': str(path), 'sha256': sha(path), 'files': len(v['files'])}


def check_freeze(path):
    v = json.load(open(path))
    assert v['files'] == {str(p.relative_to(REPO)): sha(p) for p in frozen_paths()}, 'frozen source changed'
    return sha(path)


def key(cell, d):
    return 'C_native' if cell == 'C' else (f'T_native|{d}' if cell == '000' else f'R{cell}|{d}')


def run(freeze_path, out):
    import torch
    from transformers import AutoTokenizer
    t0 = time.time()
    fsha = check_freeze(freeze_path)
    sys.path.insert(0, str(HERE.parent / 'cache-c2-cross-direction-v1-2026-11-01'))
    import c2_run as V
    tok = AutoTokenizer.from_pretrained(V.exp.read(V.T1.SOURCE / 'contract.json')['source']['model_path'])
    special = set(tok.all_special_ids) | set(getattr(tok, 'added_tokens_decoder', {}).keys())
    ver = json.load(open(NR / 'verification.json'))
    assert ver['status'] == 'passed' and ver['stage'] == 'formal'
    per, gates = {}, {'max_closure_err': 0.0, 'max_recon_err': 0.0}
    for w in sorted(NR.glob('worker-*')):
        if not w.is_dir():
            continue
        rc = json.load(open(w / 'receipt.json'))
        for rel, dg in rc['record_hashes'].items():
            assert sha(w / rel) == dg, rel
            rec = json.load(open(w / rel))
            iid = rec['item']['id']
            tp = w / f'tensors/{iid}.pt'
            assert sha(tp) == rc['tensor_hashes'][f'tensors/{iid}.pt'], ('tensor hash', iid)
            L = torch.load(tp, map_location='cpu', weights_only=False)['logits']
            ans, others = K.answer_and_distractors(rec['item']['record'])
            ans_ids, dis_ids = K.token_sets(tok, ans, others)
            cn = rec['cells']['C_native']['score']
            s0, q0 = cn['stop_winner'], cn['nonstop_winner']
            assert q0 == rec['a_token']

            def cat(t):
                return K.categorize(int(t), tok.decode([int(t)]), special, q0, ans_ids, dis_ids)
            per[iid] = {'answer': ans, 'distractors': others, 'q0': {'id': q0, 'text': tok.decode([q0]), 'category': cat(q0)}, 'dirs': {}}
            zC = L['C_native'].double()
            for d in DIRECTIONS:
                z = {c: L[key(c, d)].double() for c in CELLS}
                terms = {}
                for c in CELLS:
                    ro = rec['cells'][key(c, d)]['readout']
                    terms[c] = K.cell_terms(ro['raw']['s44'], ro['raw']['s46'], ro['raw']['a'], ro['D'], s0)
                    non = z[c].clone()
                    non[list(K.STOP)] = -float('inf')
                    rD = float(z[c][list(K.STOP)].max() - non.max())
                    gates['max_recon_err'] = max(gates['max_recon_err'], abs(rD - ro['D']))
                    assert abs(rD - ro['D']) <= 1e-6, ('D recon', iid, d, c)
                dec, err = K.decompose_interactions(terms)
                gates['max_closure_err'] = max(gates['max_closure_err'], err)
                assert err <= 1e-9, ('I_D = I_Q + I_A - I_B', iid, d)
                cells = {}
                for c in CELLS:
                    non = z[c].clone()
                    non[list(K.STOP)] = -float('inf')
                    top = torch.topk(non, TOPK)
                    order = torch.argsort(non, descending=True)
                    q0_rank = int((order == q0).nonzero()[0, 0]) + 1
                    cells[c] = {'winner': int(top.indices[0]), 'winner_text': tok.decode([int(top.indices[0])]), 'winner_category': cat(top.indices[0]),
                                'top5': [{'id': int(t), 'text': tok.decode([int(t)]), 'category': cat(t), 'z_minus_s0': float(z[c][int(t)] - z[c][s0])}
                                         for t in top.indices],
                                'q0_rank_nonstop': q0_rank, 'eos': bool(rec['cells'][key(c, d)]['score']['first_step_eos']), **terms[c]}
                aux = {c: K.edge_aux(z['000'], z[c], s0, cells['000']['winner'], cells[c]['winner']) for c in CELLS if c != '000'}
                aux_C = K.edge_aux(zC, z['000'], s0, q0, cells['000']['winner'])          # clean -> native T
                per[iid]['dirs'][d] = {'interactions': dec, 'cells': cells, 'aux_from_T': aux, 'aux_C_to_T': aux_C}
    ids = sorted(per)
    summary = {}
    mean = lambda xs: sum(xs) / len(xs)   # noqa: E731
    for d in DIRECTIONS:
        rows = {i: per[i]['dirs'][d] for i in ids}
        cats_T = {i: rows[i]['cells']['000']['winner_category'] for i in ids}
        p_ok, p_n = K.prediction_direction(cats_T)
        rec_cats = {}
        for i in ids:
            for c in CELLS[1:]:
                k_ = rows[i]['cells'][c]['winner_category']
                rec_cats[k_] = rec_cats.get(k_, 0) + 1
        summary[d] = {
            'P_T_direction': p_ok, 'P_T_scenarios': p_n,
            'T_winner_categories': {c: sum(v == c for v in cats_T.values()) for c in K.CATEGORIES},
            'T_winner_tokens': {i: rows[i]['cells']['000']['winner_text'] for i in ids},
            'recovered_winner_categories_7x12': rec_cats,
            'q0_rank_mean': {c: mean([rows[i]['cells'][c]['q0_rank_nonstop'] for i in ids]) for c in CELLS},
            'interaction_means': {q: {k: mean([rows[i]['interactions'][q][k] for i in ids]) for k in rows[ids[0]]['interactions'][q]} for q in ('D', 'Q', 'A', 'B')},
            'aux_C_to_T_mean': {k: mean([rows[i]['aux_C_to_T'][k] for i in ids]) for k in ('new_over_old_advantage', 'd_s0_minus_old', 'd_s0_minus_new')},
            'switch_counts_from_T': {c: sum(rows[i]['aux_from_T'][c]['switched'] for i in ids) for c in CELLS[1:]},
            'restored_to_q0_counts': {c: sum(rows[i]['cells'][c]['winner'] == per[i]['q0']['id'] for i in ids) for c in CELLS[1:]}}
    value = {'experiment': HERE.name, 'plan_id': PLAN_ID, 'freeze_sha256': fsha, 'gates': gates,
             'P_T_k_of_4': sum(summary[d]['P_T_direction'] for d in DIRECTIONS), 'summary': summary, 'per_input': per,
             'q0_categories': {i: per[i]['q0']['category'] for i in ids}, 'wall_seconds': time.time() - t0}
    with open(out, 'x') as f:
        f.write(json.dumps(value, ensure_ascii=False, indent=1) + '\n')
    return {'gates': gates, 'P_T_k_of_4': value['P_T_k_of_4'], 'wall_seconds': value['wall_seconds']}


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest='cmd', required=True)
    sub.add_parser('freeze').add_argument('path')
    q = sub.add_parser('run')
    q.add_argument('--freeze', required=True)
    q.add_argument('--out', required=True)
    a = p.parse_args()
    print(json.dumps(freeze(a.path) if a.cmd == 'freeze' else run(a.freeze, a.out), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
