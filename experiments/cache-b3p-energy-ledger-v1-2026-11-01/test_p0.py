"""CPU tests for B3-P0 (no weights).  CUDA_VISIBLE_DEVICES= python test_p0.py [RECEIPT_JSON]"""
import json
import zlib
import math
import os
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import torch  # noqa: E402
import p0_core as K  # noqa: E402
import p0_run as R  # noqa: E402

torch.manual_seed(0)


def vec(*xs):
    return torch.tensor(xs, dtype=torch.float64)


class Energy(unittest.TestCase):
    def test_reviewer_counterexample_aligned_only(self):
        c, a, b = vec(1, 2, 0), vec(0.5, 0.5, 0), vec(0.4, 0.6, 0)
        y = {'00': c, '10': c + a, '01': c + b, '11': c + a + b}            # K(h) = 0
        e = K.energy(y)
        self.assertAlmostEqual(e['KE'], 2 * float(a @ b))
        self.assertAlmostEqual(e['inter'], 0.0)
        self.assertEqual(K.classify([e['aligned'] / e['KE']] * 4)[0], 'aligned_main')

    def test_pure_vector_interaction(self):
        c, a, b, k = vec(1, 0, 0, 0), vec(0, 1, 0, 0), vec(0, 0, 1, 0), vec(0.3, 0, 0, 0.2)
        y = {'00': c, '10': c + a, '01': c + b, '11': c + a + b + k}
        e = K.energy(y)
        self.assertAlmostEqual(e['aligned'], 0.0)
        self.assertAlmostEqual(e['KE'], e['inter'])
        self.assertEqual(K.classify([0.0] * 4)[0], 'vector_interaction')
        self.assertEqual(K.classify([0.5] * 4)[0], 'mixed')
        self.assertEqual(K.classify([None, None, 0.9, 0.9])[0], 'not_formable')

    def test_identity_random(self):
        y = {c: torch.randn(50, dtype=torch.float64) for c in K.CELLS}
        e = K.energy(y, torch.randn(50, dtype=torch.float64).div_(10))
        self.assertLess(abs(e['identity_err']) / e['identity_scale'], 1e-12)

    def test_attribution_sums(self):
        incs = [(f'b{j}', {c: torch.randn(20, dtype=torch.float64) for c in K.CELLS}) for j in range(5)]
        entry = torch.randn(20, dtype=torch.float64)
        y = {c: entry + sum(d[c] for _, d in incs) for c in K.CELLS}
        rows = K.attribution(incs, y)
        e = K.energy(y)
        self.assertAlmostEqual(sum(r['aligned'] for r in rows.values()), e['aligned'])
        self.assertAlmostEqual(sum(r['inter'] for r in rows.values()), e['inter'])


class Rules(unittest.TestCase):
    def scen(self, i, e):
        return {f'S{s}': (i, i, e, e, True, True) for s in range(6)}

    def test_branch_qualifies(self):
        self.assertTrue(K.branch_qualifies({d: self.scen(30.0, 100.0) for d in range(4)})[0])
        self.assertFalse(K.branch_qualifies({d: self.scen(20.0, 100.0) for d in range(4)})[0])      # 20% < 25%
        self.assertFalse(K.branch_qualifies({d: self.scen(-30.0, 100.0) for d in range(4)})[0])
        two = {0: self.scen(30.0, 100.0), 1: self.scen(30.0, 100.0), 2: self.scen(1.0, 100.0), 3: self.scen(1.0, 100.0)}
        self.assertFalse(K.branch_qualifies(two)[0])

    def test_prediction_card(self):
        good = {d: {f'S{s}': ((0.1, 0.05, 0.02), (0.1, 0.06, 0.03)) for s in range(6)} for d in range(4)}
        self.assertTrue(K.prediction_card(good)[0])
        moves_p = {d: {f'S{s}': ((0.1, 0.05, 0.3), (0.1, 0.06, 0.03)) for s in range(6)} for d in range(4)}
        self.assertFalse(K.prediction_card(moves_p)[0])
        small = {d: {f'S{s}': ((0.1, 0.09, 0.02), (0.1, 0.09, 0.03)) for s in range(6)} for d in range(4)}
        self.assertFalse(K.prediction_card(small)[0])

    def test_registered(self):
        p = K.registered_predictions([0.6] * 4, [0.5] * 4, [0.1] * 4, [0.2] * 4)
        self.assertTrue(p['P1_aligned_share_ge_half'] and p['P2_fix_cos_exceeds_random'])
        p = K.registered_predictions([0.2] * 4, [0.1] * 4, [0.1] * 4, [0.2] * 4)
        self.assertFalse(p['P1_aligned_share_ge_half'] or p['P2_fix_cos_exceeds_random'])


# ---------------------------------------------------------------- synthetic end-to-end consumer

DIM = 32


class StubMLPs:
    def __init__(self):
        g = torch.Generator().manual_seed(1)
        self.eps = 1e-6
        self.W = {l: (torch.randn(DIM, DIM, generator=g, dtype=torch.float64) / 6, torch.randn(DIM, DIM, generator=g, dtype=torch.float64) / 6)
                  for l in range(13, 32)}

    def mlp(self, l, x):
        w1, w2 = self.W[l]
        return w2 @ torch.tanh(w1 @ x.double()) * 2.0


def synth_input(mods, iid, corrupt=False):
    g = torch.Generator().manual_seed(zlib.crc32(iid.encode()) % 10000)
    entry = (torch.randn(DIM, generator=g) * 3).to(torch.bfloat16)
    u = torch.randn(DIM, generator=g, dtype=torch.float64)
    off = {name: torch.randn(DIM, generator=g, dtype=torch.float64) * 0.3 for name in ('A', 'B', 'U1', 'U1c', 'U2', 'U2c')}
    groups = {'N:CC': (), 'N:CFIX': ('A',), 'N:CREST': ('B',), 'N:CT': ('A', 'B'), 'N:CUF1': ('U1',), 'N:CUF1c': ('U1c',),
              'N:CUF2': ('U2',), 'N:CUF2c': ('U2c',)}
    ten = {'extras': {}, 'trace': {}, 'readout_vectors': {'stop': u, 'answer': -u, 'eps': 1e-6}}
    rec = {'item': {'id': iid}, 'cells': {}}
    for d in R.DIRECTIONS:
        for name, gs in groups.items():
            key = f'{name}|{d}'
            h = entry
            ex, tr = {}, {}
            for l in range(13, 32):
                o = sum((off[x] for x in gs), torch.zeros(DIM, dtype=torch.float64))
                if name == 'N:CT':
                    o = off['A'] + off['B'] + 0.2 * torch.tanh(off['A'] * off['B'])
                m = (0.1 * torch.tanh(h.double()) + o / 19).to(torch.bfloat16)
                a = h + m
                f = mods.mlp(l, a).to(torch.bfloat16)
                if corrupt and l == 20 and name == 'N:CT':
                    f = (f.double() * 1.5).to(torch.bfloat16)
                out = a + f
                ex[f'{l}:in'], ex[f'{l}:out'], tr[f'{l}:mix'], tr[f'{l}:mlp'] = h, out, m, f
                h = out
            ex['final:h'] = h
            ten['extras'][key], ten['trace'][key] = ex, tr
            hh = h.double()
            z = float(u @ hh) / math.sqrt(float(hh @ hh) / DIM + 1e-6)
            rec['cells'][key] = {'readout': {'primary': {'cz_s46': z}}}
    return rec, ten


class Consumer(unittest.TestCase):
    def test_end_to_end(self):
        mods = StubMLPs()
        res, gates = {}, {}
        for s in range(1, 7):
            for f in (0, 1):
                iid = f'P0{s}-f{f}'
                rec, ten = synth_input(mods, iid)
                rv = ten['readout_vectors']
                res[iid] = {d: {sp: R.analyse_split(mods, ten, rec, d, sp, rv['eps'], rv['stop'], rv['answer'], gates) for sp in R.SPLITS}
                            for d in R.DIRECTIONS}
        summary = R.summarise(res)
        cand = R.select_candidate(res)
        self.assertIn(summary['FIX']['class'], ('aligned_main', 'vector_interaction', 'mixed', 'not_formable'))
        self.assertIn(R.exit_label(summary, cand), ('no_candidate', 'layer31_exact_answer_prediction_met', 'layer31_exact_answer_prediction_not_met',
                                                   'shadow_card_passes_needs_gpu_contract', 'shadow_card_fails_exit'))
        self.assertLess(gates['max_identity_rel'], 1e-9)
        self.assertLess(gates['max_mlp_recompute_rel'], R.RECOMPUTE_REL)
        b = res['P01-f0'][R.DIRECTIONS[0]]['FIX']
        self.assertEqual(b['branches']['31:mix']['cf']['kind'], 'exact')
        self.assertEqual(b['branches']['20:mlp']['cf']['kind'], 'shadow_frozen_downstream')
        tot = sum(x['aligned'] + x['inter'] for x in b['branches'].values())
        self.assertAlmostEqual(tot / b['final']['KE'], 1.0, places=6)

    def test_recompute_gate_fails(self):
        mods = StubMLPs()
        rec, ten = synth_input(mods, 'P01-f0', corrupt=True)
        rv = ten['readout_vectors']
        with self.assertRaises(AssertionError):
            R.analyse_split(mods, ten, rec, R.DIRECTIONS[0], 'FIX', rv['eps'], rv['stop'], rv['answer'], {})


def main():
    assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
    receipt = sys.argv[1] if len(sys.argv) > 1 else None
    res = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]))
    if receipt:
        import hashlib
        repo = HERE.parent.parent
        src = {str(p.relative_to(repo)): hashlib.sha256(p.read_bytes()).hexdigest()
               for p in sorted(HERE.glob('*.py')) + sorted((HERE / 'readiness').glob('*.py'))}
        with open(receipt, 'x') as f:
            json.dump({'status': 'passed' if res.wasSuccessful() else 'failed', 'tests_run': res.testsRun, 'failures': len(res.failures),
                       'errors': len(res.errors), 'source_hashes': src, 'torch': torch.__version__}, f, indent=2)
            f.write('\n')
    sys.exit(0 if res.wasSuccessful() else 1)


if __name__ == '__main__':
    main()
