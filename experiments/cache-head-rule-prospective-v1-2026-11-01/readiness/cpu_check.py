"""C1-P CPU readiness on real assets (no model forward):
1. tokenization / segment boundary of the 12 new inputs (real tokenizer);
2. the run's own select_scores on the OLD inputs (CONV N:TT drivers, safetensors weights) must reproduce the frozen B2
   H lists for all 12 old inputs, and the rebuild validations must pass;
3. random subsets layer-matched.
CUDA_VISIBLE_DEVICES= python readiness/cpu_check.py OUT_JSON"""
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
import c1p_run as V  # noqa: E402
import c1p_core as K  # noqa: E402
import torch  # noqa: E402

torch.set_num_threads(8)
MODEL = Path('/data/models/Qwen3.5-4B-851bf6e')
B2_SEL = HERE.parent / 'cache-b2-v-subset-q-dependence-design-v1-2026-11-01/head-selection-r01.json'


def main(out):
    from transformers import AutoTokenizer
    from safetensors import safe_open
    sys.path.insert(0, str(V.T1.SOURCE))
    from control_engine import encode_text
    src = V.exp.read(V.T1.SOURCE / 'contract.json')['source']
    tok = AutoTokenizer.from_pretrained(src['model_path'])
    rows = V.items()
    ctx = V.exp.contexts_for(tok, rows)
    res = {'segments': {}, 'reproduce_b2': {}, 'random': {}}
    ok = True
    for r in rows:
        s = K.label_tokens(tok, ctx[r['id']], r['record'], encode_text)
        res['segments'][r['id']] = {'n': s['n'], 'b': s['b'], 'window': s['n'] - 2 - s['b'], 'straddle': s['straddling_tokens'],
                                    'fact_tokens': s['labels'].count('fact')}
        ok &= not s['straddling_tokens']
    # weights
    idx = json.load(open(MODEL / 'model.safetensors.index.json'))['weight_map']
    eps = json.load(open(MODEL / 'config.json'))['text_config']['rms_norm_eps']

    def get(name):
        with safe_open(str(MODEL / idx[name]), framework='pt') as f:
            return f.get_tensor(name)
    E = get('model.language_model.embed_tokens.weight')
    mean_e = torch.zeros(E.shape[1], dtype=torch.float64)
    for i in range(0, E.shape[0], 16384):
        mean_e += E[i:i + 16384].double().sum(0)
    mean_e /= E.shape[0]
    wf = get('model.language_model.norm.weight').double()
    W = {}
    for l in K.G:
        p = f'model.language_model.layers.{l}.'
        W[l] = {'ln': get(p + 'input_layernorm.weight').double(), 'Wv': get(p + 'linear_attn.in_proj_qkv.weight')[4096:8192].double(),
                'cw': get(p + 'linear_attn.conv1d.weight')[4096:8192, 0, :].double(), 'gn': get(p + 'linear_attn.norm.weight').double(),
                'Wo': get(p + 'linear_attn.out_proj.weight').double()}
    b2 = V.exp.read(B2_SEL)['items']
    sys.path.insert(0, str(HERE.parent / 'cache-b2-v-subset-q-dependence-v1-2026-11-01'))
    import b2_run as B2R
    for item in V.CF.items():
        iid = item['id']
        _, old = V.CO.load_old(iid)
        _, cft, _ = B2R.cf_assets(iid)
        dr, ex, mo = cft['drivers']['N:TT'], cft['extras']['N:TT'], cft['module_out']['N:TT']
        hT = ex['final:h'].double()
        u = (E[K.S46].double() - mean_e) * (1 + wf) * torch.rsqrt(hT.pow(2).mean() + eps)
        sc, val = K.select_scores(lambda l: W[l], {l: dr[l] for l in K.G}, {l: ex[f'{l}:in'] for l in K.G},
                                  {l: old['deep']['T'][f'{l}:conv_states'][0, 4096:8192] for l in K.G},
                                  {l: old['deep']['C'][f'{l}:conv_states'][0, 4096:8192] for l in K.G}, u, eps,
                                  outproj_ref={l: mo[f'{l}:out_proj'] for l in K.G})
        Hn = K.top_heads(sc)
        same = Hn == b2[iid]['H']
        res['reproduce_b2'][iid] = {'identical_to_frozen_B2_H': same, 'validation': val,
                                    'overlap': len({tuple(x) for x in Hn} & {tuple(x) for x in b2[iid]['H']})}
        ok &= same and val['v_rel'] <= K.RULE['rebuild_rel'] and val['outproj_rel'] <= K.RULE['rebuild_rel']
        u1 = K.random_subset(iid, 1, Hn)
        res['random'][iid] = {'layer_matched': sorted(x[0] for x in u1) == sorted(x[0] for x in Hn), 'overlap_U1_H': len({tuple(x) for x in u1} & {tuple(x) for x in Hn})}
        ok &= res['random'][iid]['layer_matched']
        del old, cft
    res['passed'] = bool(ok)
    with open(out, 'x') as f:
        f.write(json.dumps(res, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'passed': res['passed'], 'segments': {k: (v['n'], v['b'], v['straddle']) for k, v in res['segments'].items()},
                      'reproduce': {k: v['identical_to_frozen_B2_H'] for k, v in res['reproduce_b2'].items()}}))
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main(sys.argv[1])
