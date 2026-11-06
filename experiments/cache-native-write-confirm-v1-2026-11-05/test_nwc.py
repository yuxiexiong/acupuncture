"""CPU tests for NWC-01 r03: labels reachable; read_gen bit-equal to the frozen NWR-01 / SRU-01 read functions for the D, E and random arms;
constructed-donor identities; half amplitude; plan, partners and budget; the consumer runs on fabricated records.
CUDA_VISIBLE_DEVICES= python test_nwc.py [RECEIPT]"""
import json
import os
import random
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import nwc_core as K  # noqa: E402

FAM = [f'NQ0{k}' for k in range(1, 7)]
IDS = [(f, s, v) for f in FAM for s in range(4) for v in 'abc']
META = {i: (i[0], i[1], 'F' if i[2] == 'c' else 'N') for i in IDS}
ARMS = sorted(set(K.NAT_N) | set(K.NAT_F))
BASE = {'L00': (0.0, 0.0), 'L11': (0.75, 0.25), 'D00': (0.0, 1.0), 'E00': (0.9, 0.1), 'D10': (0.05, 0.95), 'DV': (0.72, 0.28), 'DX': (0.02, 0.98),
        'D00h': (0.3, 0.7), 'DXh': (0.33, 0.67)}
BASE.update({r: (0.7, 0.3) for r in K.RAND})
BASE.update({q: (0.72, 0.28) for q in K.QNAT})
DM = {'D00': -2.9, 'D10': -2.2, 'DV': -0.8, 'DX': -2.8}


def decide(over=None, dM=None, rand=None, ratio=1.6, unreached=0.0, pf=None, seed=1):
    p, m, f = dict(BASE), dict(DM), {'L11': 0.96, 'D00': 0.96}
    p.update(over or {})
    m.update(dM or {})
    f.update(pf or {})
    rng = random.Random(seed)
    Y, E = {a: {} for a in ARMS}, {a: {} for a in ARMS}
    for a in ARMS:
        for i in IDS:
            u = rng.random()
            pc, pw = (f.get(a, 0.9), 0.0) if META[i][2] == 'F' else p[a]
            Y[a][i], E[a][i] = float(u < pc), float(pc <= u < pc + pw)
    rr = random.Random(seed + 7)
    return K.decide(Y, E, META, m, rand if rand is not None else [rr.gauss(0.0, 0.5) for _ in range(40)], ratio, unreached, n_boot=800)


class Rules(unittest.TestCase):
    def test_labels(self):
        lab = lambda r: tuple(r[k] for k in ('P12', 'P3', 'P4M', 'P4Y', 'P5', 'P6'))   # noqa: E731
        self.assertEqual(lab(decide()), ('holds',) * 6)
        self.assertEqual(decide({r: (0.0, 1.0) for r in K.RAND})['P12'], 'fails')
        self.assertEqual(decide({'D00': (0.0, 0.1)})['P12'], 'fails')
        self.assertEqual(decide({'L11': (0.2, 0.8)})['P12'], 'unjudgeable')
        self.assertEqual(decide({'DV': (0.05, 0.95)})['P3'], 'fails')
        self.assertEqual(decide(dM={'DV': -2.0})['P3'], 'fails')
        self.assertEqual(decide(ratio=0.8)['P3'], 'unjudgeable')
        self.assertEqual(decide(rand=[-1.5] * 3 + [0.0] * 37)['P4M'], 'fails')
        self.assertEqual(decide(rand=[-1.5] * 2 + [0.0] * 38)['P4M'], 'holds')
        self.assertEqual(decide(dM={'D10': -0.2})['P4M'], 'unjudgeable')
        self.assertEqual(decide({'Q1': (0.2, 0.8), 'Q2': (0.2, 0.8)})['P4Y'], 'fails')
        self.assertEqual(decide(dM={'DX': -1.0})['P5'], 'fails')
        self.assertEqual(decide(dM={'DX': -4.5})['P5'], 'fails')
        self.assertEqual(decide({'DXh': (0.7, 0.3)})['P5'], 'fails')
        self.assertEqual(decide(dM={'D00': -0.3})['P5'], 'unjudgeable')
        self.assertEqual(decide(pf={'D00': 0.5})['P6'], 'fails')
        self.assertEqual(decide(pf={'L11': 0.5, 'D00': 0.5})['P6'], 'unjudgeable')
        r = decide(unreached=0.3)
        self.assertEqual((r['P12'], r['P3'], r['P4Y'], r['P5'], r['P6']), ('unjudgeable',) * 5)

    def test_bounds(self):
        self.assertAlmostEqual(K.cp_upper(0, 40), 0.0881, places=3)
        self.assertAlmostEqual(K.cp_upper(2, 40), 0.169, places=2)
        self.assertAlmostEqual(K.cp_upper(1, 20), 0.249, places=2)
        self.assertEqual(K.cp_upper(5, 5), 1.0)


class Kernel(unittest.TestCase):
    def test_read_gen(self):
        import torch
        import nwc_run as R
        QM = R.gdn_module()
        g = torch.Generator().manual_seed(11)
        rnd = lambda *s: torch.randn(*s, generator=g)   # noqa: E731
        q, k, v = [rnd(1, 1, 32, 128).to(torch.bfloat16) for _ in range(3)]
        gg, b = -torch.rand(1, 1, 32, generator=g), torch.rand(1, 1, 32, generator=g).to(torch.bfloat16)
        Sr, S0, S1 = [rnd(1, 32, 128, 128) * 0.1 for _ in range(3)]        # receiver L11, donors "L00", "L10"
        f = lambda x: x.to(torch.float32)   # noqa: E731
        d00, d10, dv = f(S0) - f(Sr), f(S1) - f(Sr), f(S0) - f(S1)
        o_nat, S_nat = QM.torch_recurrent_gated_delta_rule(q, k, v, g=gg, beta=b, initial_state=Sr.clone(), output_final_state=True, use_qk_l2norm_in_kernel=True)
        # D and E arms == frozen SRU read_use, bit for bit; stored state native
        for use, (a_, b_) in (('D', (1, 0)), ('E', (0, 1))):
            o_ref, S_ref, _, _, _ = R.S.read_use(q, k, v, gg, b, Sr.clone(), S0, a_, b_, QM.l2norm)
            o, S2, st, err, Dc = R.read_gen(q, k, v, gg, b, Sr.clone(), QM.l2norm, d00, use=use)
            self.assertTrue(torch.equal(o, o_ref) and R.bit_equal(S2, S_nat)[0])
            self.assertLessEqual(err, R.TOL)
        # random arm == frozen NWR read_use_rand, bit for bit
        u = R.unit_dir(202611053, 21, (1, 32, 128))
        o_ref, _, _, st_ref, _ = R.N.read_use_rand(q, k, v, gg, b, Sr.clone(), S0, u, QM.l2norm)
        o, _, st, err, _ = R.read_gen(q, k, v, gg, b, Sr.clone(), QM.l2norm, d00, unit=u)
        self.assertTrue(torch.equal(o, o_ref) and torch.equal(st, st_ref))
        self.assertLessEqual(err, R.TOL)
        # constructed donors: DV + D10 == D00 patch; half amplitude; zero difference injects nothing
        Dc = {n: R.read_gen(q, k, v, gg, b, Sr.clone(), QM.l2norm, d)[4] for n, d in (('D00', d00), ('D10', d10), ('DV', dv))}
        self.assertLessEqual(float((Dc['DV'] + Dc['D10'] - Dc['D00']).abs().max() / Dc['D00'].abs().max()), R.IDENT_TOL)
        oh, _, sth, errh, _ = R.read_gen(q, k, v, gg, b, Sr.clone(), QM.l2norm, d00, scale=0.5)
        _, _, st1, _, _ = R.read_gen(q, k, v, gg, b, Sr.clone(), QM.l2norm, d00)
        self.assertTrue(torch.allclose(sth[:, 1], 0.5 * st1[:, 1], rtol=1e-6) and errh <= R.TOL)
        oz, _, _, _, _ = R.read_gen(q, k, v, gg, b, Sr.clone(), QM.l2norm, torch.zeros_like(d00))
        self.assertTrue(R.bit_equal(oz, o_nat)[0])
        ozr, _, _, ez, _ = R.read_gen(q, k, v, gg, b, Sr.clone(), QM.l2norm, torch.zeros_like(d00), unit=u)
        self.assertTrue(R.bit_equal(ozr, o_nat)[0] and ez == 0.0)


class Wiring(unittest.TestCase):
    def test_plan_and_budget(self):
        import nwc_run as R
        f0, f1, pre = R.plan('formal', 0, 2), R.plan('formal', 1, 2), R.plan('preflight', 0, 1)
        self.assertEqual(len(f0) + len(f1), 72)
        self.assertEqual({u['base_id'] for u in f0} & {u['base_id'] for u in f1}, set())
        self.assertEqual(sorted(u['item_id'] for u in pre), sorted(R.PREFLIGHT_ITEMS))
        self.assertEqual([u['panel'] for u in pre], ['old', 'old', 'new', 'new'])
        led = R.nwc_ledger()
        strata = [v['plan']['stratum'] for v in led.values()]
        self.assertEqual((strata.count('N'), strata.count('F')), (48, 24))
        for k, v in led.items():
            p = v['plan']
            if p['stratum'] == 'N':
                o = led[p['partner_id']]['plan']
                self.assertTrue(o['base_id'] == p['base_id'] and o['version'] == p['version'] and o['situation'] != p['situation'] and o['stratum'] == 'N')
            else:
                self.assertIsNone(p['partner_id'])
            self.assertEqual(v['item']['target'] == v['item']['first_listed'], p['stratum'] == 'F')
        self.assertEqual((len(R.ARMS_F), len(R.ARMS_N), len(R.SEEDS_Q), len(set(R.SEEDS_Q) & set(R.SEEDS_R))), (17, 42, 40, 0))
        self.assertEqual((len(R.SEEDS_R), len(set(R.SEEDS_R) & set(R.N.SEEDS)), len(set(R.SEEDS_Q) & set(R.N.SEEDS))), (10, 0, 0))
        self.assertEqual(tuple(R.RAND), tuple(K.RAND))
        self.assertEqual(list(R.conditions()), list(R.DIRS3))
        f = R.LIMITS['formal']
        self.assertEqual(f['c_t2'], 48 * 99 * 3 + 24 * 14 * 3)
        self.assertEqual(f['trajectories'], 48 * (1 + 41 * 3) + 24 * (1 + 16 * 3))
        self.assertLessEqual(R.GPU_CAP_S['formal'] + R.GPU_CAP_S['preflight'], 2.5 * 3600)

    def test_consumer_on_fabricated_records(self):
        import nwc_analysis as A
        rng = random.Random(3)
        recs = {}
        for (f, s, v) in IDS:
            i = f'NWC-{f}-S{s + 1}-{v}'
            codes = ['U11', 'U22', 'U33']
            slot = {'a': 1, 'b': 2, 'c': 0}[v]
            item = {'target': codes[slot], 'listed_codes': codes, 'first_listed': codes[0], 'question': 'q'}
            stratum = 'F' if v == 'c' else 'N'
            dirs = {}
            for d in A.DIRS3:
                def arm(p_correct, m):
                    c = codes[slot] if rng.random() < p_correct else (codes[0] if slot else codes[1])
                    return {'N': {'text': c + '<|im_end|>', 'termination': 'stop', 'ids': [1, {'U11': 5, 'U22': 6, 'U33': 7}[c], 9, 2], 'reached_t2': True}, 'C': {'M': m}}
                arms = {'C': arm(1.0, 0), 'L00': {'N': {'text': '<|im_end|>', 'termination': 'stop', 'ids': [2], 'reached_t2': False}}, 'L10': arm(0.3, 0),
                        'L11': arm(0.8 if stratum == 'N' else 1.0, 2.0), 'D00': arm(0.0 if stratum == 'N' else 1.0, -1.0), 'E00': arm(0.95, 2.5), 'D10': arm(0.05, -0.3)}
                arms.update({r: arm(0.8, 1.8) for r in K.RAND})
                x = {'reached_t2': True, 'arms': arms, 'structure_t1': {'13': {'q': True, 'k': True, 'g': True, 'beta': True, 'S0': True, 'v': False}},
                     'patch_norm': {'D00': 0.09, 'D10': 0.047, 'DV': 0.075, 'DX': 0.085}, 'M_Qk': None, 'M_Qn': None}
                if stratum == 'N':
                    arms.update({'DV': arm(0.75, 1.3), 'DX': arm(0.02, -0.9), 'D00h': arm(0.4, 0.4), 'DXh': arm(0.42, 0.5), 'D10h': arm(0.5, 0.8)})
                    arms.update({q: arm(0.78, 2.0 + rng.gauss(0, 0.3)) for q in K.QNAT})
                    x['M_Qk'] = [arms[q]['C']['M'] for q in K.QNAT] + [2.0 + rng.gauss(0, 0.3) for _ in range(20)]
                    x['M_Qn'] = [2.0 + rng.gauss(0, 0.6) for _ in range(40)]
                dirs[d] = x
            recs[i] = {'text': i, 'panel': 'new', 'stratum': stratum, 'scenario': f, 'situation': f'{f}-S{s + 1}', 'item': item,
                       'code_tokens': {'U11': 5, 'U22': 6, 'U33': 7}, 'directions': dirs, 'err_max': 1e-8, 'signed_zero_exceptions': 0,
                       '_tensor_path': '/nonexistent'}
        res = A.analyse(recs)
        self.assertEqual(res['strata'], {'N': 48, 'F': 24})
        self.assertEqual(res['confirmation'], 'confirmed_both_main_directions')
        self.assertEqual(res['labels'][A.DIRS3[0]]['P6'], 'holds')
        self.assertIn('unavailable', res['directions'][A.DIRS3[0]]['descriptive']['patch_cosine_D00'])
        json.dumps(res)


def main():
    assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
    receipt = sys.argv[1] if len(sys.argv) > 1 else None
    res = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]))
    if receipt:
        import hashlib
        repo = HERE.parent.parent
        src = {str(p.relative_to(repo)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(HERE.glob('*.py')) + sorted((HERE / 'readiness').glob('*.py'))}
        import torch
        with open(receipt, 'x') as f:
            json.dump({'status': 'passed' if res.wasSuccessful() else 'failed', 'tests_run': res.testsRun, 'failures': len(res.failures),
                       'errors': len(res.errors), 'source_hashes': src, 'torch': torch.__version__}, f, indent=2)
            f.write('\n')
    sys.exit(0 if res.wasSuccessful() else 1)


if __name__ == '__main__':
    main()
