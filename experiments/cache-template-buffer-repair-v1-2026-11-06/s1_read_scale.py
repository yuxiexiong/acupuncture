"""FBR-01 side measurement S1 (CONTRACT §8; descriptive, no gate, enters no reading).
How large is the native-source patch of NWC-01 relative to the direct-read term it perturbs?
For every stratum-N input of the NWC-01 panel and each of its three directions: rebuild the receiver L11 at t1 (NWC-01 runner functions), run ONE
t2 forward with the shared first token and record, per G layer and head, |alpha S1^T q| (the receiver's own direct-read term).  The patch norms
|alpha (S1[L00] - S1[L11])^T q| are read from the stored NWC-01 formal tensors.  Nothing is injected (scale 0).
python s1_read_scale.py OUT_JSON [GPU]"""
import copy
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import fbr_run as R  # noqa: E402

W = R.W
NWC_FORMAL = R.NWC_DIR / 'runs/formal-r01'


def main(out, gpu=0):
    import torch
    exp, L, B = R.exp, R.L, R.B
    assert exp.read(NWC_FORMAL / 'verification.json')['status'] == 'passed'
    tens = {}
    for w in sorted(NWC_FORMAL.glob('worker-*')):
        if w.is_dir():
            r = exp.read(w / 'receipt.json')
            for rel, dg in r['record_hashes'].items():
                rec = exp.read(w / rel)
                if rec['panel'] == 'new' and rec['stratum'] == 'N':
                    assert exp.sha(w / rec['tensor_file']) == r['tensor_hashes'][rec['tensor_file']]
                    tens[rec['text']] = str(w / rec['tensor_file'])
    led = W.nwc_ledger()
    ids = [k for k, v in led.items() if v['plan']['stratum'] == 'N']
    assert len(ids) == 48 and set(ids) == set(tens)
    sys.path.insert(0, str(R.T1.SOURCE))
    from control_engine import ControlEngine
    t0 = time.monotonic()
    source = exp.read(R.T1.SOURCE / 'contract.json')['source']
    engine = ControlEngine(source['model_path'], exp.model_spec(), f'cuda:{gpu}')
    exp.metadata_check(engine)
    model = engine.model
    types = L.layer_types(model)
    G = B.g_layers(types, R.SPLIT)
    QM = R.gdn_module()
    R.KRDR.QHOOK_ORIG[0] = QM.torch_recurrent_gated_delta_rule
    conds, vecs = W.conditions(), R.load_vectors()
    contexts = exp.contexts_for(engine.tokenizer, [v['item'] for v in led.values()])
    _, u, sign = R.ARMS_ALL['Rk']
    counts = {k: 0 for k in R.COUNT_KEYS}
    rows, calib = [], {}
    for a in ids:
        le = led[a]
        rid = f"{le['plan']['base_id']}-ABC-A"
        if rid not in calib:
            calib[rid], _ = R.QCR.nq_calibration(rid)
        C, T, info = R.form_new(engine, le, contexts, calib[rid], conds, counts)
        cconv = {l: L._get(C.layers[l], 'conv_states').clone() for l in G}
        st = torch.load(tens[a], map_location='cpu')
        for d in conds:
            vec = R.QKFR.mask_vec(vecs[u][f"{info['scenario']}|{d}"].float(), 'k')
            bT, _ = R.QKFR.edited_arm(T[d], T[d], T[d], G, None, 1)
            hk = R.LHook(model, G, 'cell', a=1, b=1, vec=vec, sign=sign, cconv=cconv)
            c11, z1 = R.t1L(engine, copy.deepcopy(bT), info['last'], info['n'], counts, 't1', hk)
            assert R.bit_equal(z1.to(torch.bfloat16).cpu(), st[f't1|L11|{d}'])[0], ('t1 L11 != NWC record', a, d)
            S1 = {l: L._get(c11.layers[l], 'recurrent_states').clone() for l in G}
            gh = W.GHook(model, G, {l: S1[l].to(torch.float32) for l in G}, S1, scale=0.0)
            R.fwd(engine, c11, le['tokens']['q_shared'], info['n'], counts, 'c_t2', hook=gh)
            read = torch.stack([gh.stats[l][:, 0] for l in G]).double()                    # [14, H]  |alpha S1^T q|
            patch = st[f'stats|C|D00|{d}'][:, :, 1].double()                               # [14, H]  |patch|, NWC-01 formal
            rl, pl = read.pow(2).sum(1).sqrt(), patch.pow(2).sum(1).sqrt()
            rows.append({'input': a, 'direction': d, 'read_layer': [float(x) for x in rl], 'patch_layer': [float(x) for x in pl],
                         'ratio_layer': [float(p / r) if r > 0 else None for p, r in zip(pl, rl)],
                         'ratio_total': float(pl.pow(2).sum().sqrt() / rl.pow(2).sum().sqrt())})
            del c11, S1, bT
        del C, T
        torch.cuda.empty_cache()
    R.F.assert_no_hooks(model)
    import statistics as stt
    summ = {}
    for d in conds:
        x = [r for r in rows if r['direction'] == d]
        summ[d] = {'ratio_total_median': stt.median(r['ratio_total'] for r in x), 'ratio_total_min': min(r['ratio_total'] for r in x),
                   'ratio_total_max': max(r['ratio_total'] for r in x),
                   'ratio_layer_median': [stt.median(r['ratio_layer'][j] for r in x if r['ratio_layer'][j] is not None) for j in range(len(G))]}
    res = {'what': 'patch norm / direct-read term norm at t2, receiver L11, NWC-01 stratum N; descriptive, enters no reading', 'layers': list(G),
           'n_inputs': len(ids), 'summary': summ, 'rows': rows, 'device_seconds': time.monotonic() - t0, 'counts': counts}
    with open(out, 'x') as f:
        f.write(json.dumps(res, ensure_ascii=False, indent=1) + '\n')
    print(json.dumps({d: {k: (round(v, 4) if isinstance(v, float) else [round(y, 3) for y in v]) for k, v in s.items()} for d, s in summ.items()}, ensure_ascii=False))


if __name__ == '__main__':
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 0)
