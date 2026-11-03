"""CPU tests for NPC-01.  The three pair groups take exactly their tensors (V: channels [V_LO:] only, conv q/k kept clean) and nothing else;
corruption is rejected; per-input minimal-combination categories (single / pair sets / three / none, plus the inconsistency flag) both reachable
and not; analysis entry point end to end with the real key structure and provenance checks; budget.
CUDA_VISIBLE_DEVICES= python test_npc.py [RECEIPT]"""
import copy
import json
import os
import sys
import types as TY
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import npc_core as NP  # noqa: E402

SCN = [f'NQ0{k}' for k in range(1, 7)]
IDS = [f'{s}-{j}' for s in SCN for j in range(8)]
SCEN = {i: i.split('-')[0] for i in IDS}
G = (13, 14, 16, 17, 18, 20, 21, 22, 24, 25, 26, 28, 29, 30)
KL = (15, 19, 23, 27, 31)
VLO = 4


def cache(seed):
    import torch
    g = torch.Generator().manual_seed(seed)
    lay = []
    for i in range(32):
        if (i + 1) % 4 == 0:
            lay.append(TY.SimpleNamespace(keys=torch.randn(1, 2, 5, 3, generator=g), values=torch.randn(1, 2, 5, 3, generator=g)))
        else:
            lay.append(TY.SimpleNamespace(recurrent_states=torch.randn(1, 2, 3, 3, generator=g), conv_states=torch.randn(1, 7, 3, generator=g)))
    return TY.SimpleNamespace(layers=lay)


def set_(layer, f, t):
    setattr(layer, f, t)


def comps(c):
    return [(i, f) for i, lay in enumerate(c.layers) for f in vars(lay)]


def beq(a, b):
    import torch
    return (torch.equal(a, b), 0)


class Replacement(unittest.TestCase):
    def test_pairs(self):
        import torch
        Cc, T = cache(1), cache(2)
        want = {'SV': ('S', 'V'), 'SK': ('S', 'K'), 'VK': ('V', 'K')}
        for grp, parts in want.items():
            tg = NP.targets(grp, G, KL, VLO)
            X = NP.replace(Cc, T, tg, getattr, set_, copy.deepcopy)
            NP.check_arm(X, Cc, T, tg, getattr, comps(Cc), beq)
            for l in G:
                self.assertTrue(torch.equal(X.layers[l].conv_states[:, :VLO], Cc.layers[l].conv_states[:, :VLO]))      # q/k always clean
                srcV = T if 'V' in parts else Cc
                self.assertTrue(torch.equal(X.layers[l].conv_states[:, VLO:], srcV.layers[l].conv_states[:, VLO:]))
                srcS = T if 'S' in parts else Cc
                self.assertTrue(torch.equal(X.layers[l].recurrent_states, srcS.layers[l].recurrent_states))
            for l in KL:
                srcK = T if 'K' in parts else Cc
                self.assertTrue(torch.equal(X.layers[l].keys, srcK.layers[l].keys) and torch.equal(X.layers[l].values, srcK.layers[l].values))
            for i in range(13):
                for f in vars(X.layers[i]):
                    self.assertTrue(torch.equal(getattr(X.layers[i], f), getattr(Cc.layers[i], f)))
        X = NP.replace(Cc, T, NP.targets('SK', G, KL, VLO), getattr, set_, copy.deepcopy)
        X.layers[13].conv_states = X.layers[13].conv_states + 1          # V channels must stay clean in SK
        with self.assertRaises(AssertionError):
            NP.check_arm(X, Cc, T, NP.targets('SK', G, KL, VLO), getattr, comps(Cc), beq)


class Minimal(unittest.TestCase):
    def b(self, **kw):
        base = {a: False for a in ('CS', 'CV', 'CK', 'CSV', 'CSK', 'CVK', 'CVSK')}
        base.update(kw)
        return base

    def test_categories(self):
        self.assertEqual(NP.minimal(self.b(CS=True, CSV=True, CVSK=True))[0], 'single')
        self.assertEqual(NP.minimal(self.b(CSV=True, CVSK=True))[:2], ('pair', ['CSV']))
        self.assertEqual(NP.minimal(self.b(CSV=True, CVK=True, CVSK=True))[:2], ('pair', ['CSV', 'CVK']))
        self.assertEqual(NP.minimal(self.b(CVSK=True))[0], 'three')
        self.assertEqual(NP.minimal(self.b())[0], 'none')
        cat, mins, fl = NP.minimal(self.b(CSK=True))
        self.assertEqual((cat, mins, fl), ('pair', ['CSK'], ['pair_broken_but_VSK_correct']))
        self.assertNotEqual(NP.minimal(self.b(CVSK=True))[0], 'pair')


def r(y, et='correct', text='V47'):
    return {'Y': y, 'etype': et, 'text': text, 'B': 0.0, 'first_stop': et == 'stop', 'cat': 'stop' if et == 'stop' else 'code',
            'N': {'text': text, 'ids': [1]}}


class EndToEnd(unittest.TestCase):
    def test_analyse(self):
        import npc_analysis as A
        recs, nsr, nqk = {}, {}, {}
        for k, i in enumerate(IDS):
            res, ns_, nq_ = {'C': r(1)}, {}, {}
            for d in A.NEEDLES:
                kind = k % 4            # 0: CSV minimal, 1: CSK minimal, 2: needs three, 3: none
                T = r(0, 'stop', '')
                res[d] = {'T': T, 'CSV': r(0 if kind == 0 else 1, 'mixed' if kind == 0 else 'correct'),
                          'CSK': r(0 if kind == 1 else 1, 'mixed' if kind == 1 else 'correct'), 'CVK': r(1)}
                ns_[d] = {'T': T, 'CS': r(1), 'CV': r(1), 'CK': r(1), 'CJ': r(0 if kind < 3 else 1, 'mixed' if kind < 3 else 'correct')}
                nq_[d] = {'T': T, 'CVSK': r(0 if kind < 3 else 1, 'mixed' if kind < 3 else 'correct')}
            recs[i] = {'scenario': SCEN[i], 'results': res, 'nsr_record_sha256': f's{k}', 'nqk_record_sha256': f'q{k}'}
            nsr[i] = {'results': ns_, '_sha': f's{k}'}
            nqk[i] = {'results': nq_, '_sha': f'q{k}'}
        out = A.analyse(recs, nsr, nqk)
        m = out['needles']['N_L00_C4146_D-1']['minimal']
        self.assertEqual(m['categories'], {'single': 0, 'pair': 24, 'three': 12, 'none': 12})
        self.assertEqual(m['pair_counts'], {'CSV': 12, 'CSK': 12, 'CVK': 0})
        self.assertEqual(out['needles']['N_L00_C4146_D-1']['pairing']['CSV']['CVSK']['both_broken'], 12)
        nqk[IDS[0]]['_sha'] = 'x'
        with self.assertRaises(AssertionError):
            A.analyse(recs, nsr, nqk)


class Wiring(unittest.TestCase):
    def test_budget(self):
        import npc_run as R
        f, p = R.LIMITS['formal'], R.LIMITS['preflight']
        self.assertEqual((f['t1'], f['trajectories'], f['formations'], f['formation_token_forwards']), (432, 432, 144, 3834))
        self.assertEqual((p['t1'], p['engineering']), (18, 2))
        self.assertEqual(R.ARMS, ('T', 'CSV', 'CSK', 'CVK'))


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
            json.dump({'status': 'passed' if res.wasSuccessful() and not res.skipped else 'failed', 'tests_run': res.testsRun, 'failures': len(res.failures),
                       'errors': len(res.errors), 'skipped': len(res.skipped), 'source_hashes': src, 'torch': torch.__version__}, f, indent=2)
            f.write('\n')
    sys.exit(0 if (res.wasSuccessful() and not res.skipped) else 1)


if __name__ == '__main__':
    main()
