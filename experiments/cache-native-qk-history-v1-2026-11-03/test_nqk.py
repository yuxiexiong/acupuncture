"""CPU tests for NQK-01.  QK replacement takes only conv channels [:V_LO] (V kept); VSK takes conv [V_LO:] + S + KV (q/k kept); everything
else untouched; check_arm accepts both and rejects corruption of kept channels or shallow tensors.  Per-input pairing counts.  Analysis entry
point end to end with the real key structure (incl. NSR provenance check).  Budget.
CUDA_VISIBLE_DEVICES= python test_nqk.py [RECEIPT]"""
import copy
import json
import os
import sys
import types as TY
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import nqk_core as NQ  # noqa: E402

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


get = getattr


def set_(layer, f, t):
    setattr(layer, f, t)


def comps(c):
    return [(i, f) for i, lay in enumerate(c.layers) for f in vars(lay)]


def beq(a, b):
    import torch
    return (torch.equal(a, b), 0)


class Replacement(unittest.TestCase):
    def setUp(self):
        self.Cc, self.T = cache(1), cache(2)

    def test_qk_and_vsk(self):
        import torch
        for grp in ('QK', 'VSK'):
            tg = NQ.targets(grp, G, KL, VLO)
            C0, T0 = copy.deepcopy(self.Cc), copy.deepcopy(self.T)
            X = NQ.replace(self.Cc, self.T, tg, get, set_, copy.deepcopy)
            NQ.check_arm(X, self.Cc, self.T, tg, get, comps(self.Cc), beq)
            for l in G:
                cx, cc, ct = X.layers[l].conv_states, self.Cc.layers[l].conv_states, self.T.layers[l].conv_states
                if grp == 'QK':
                    self.assertTrue(torch.equal(cx[:, :VLO], ct[:, :VLO]) and torch.equal(cx[:, VLO:], cc[:, VLO:]))
                    self.assertTrue(torch.equal(X.layers[l].recurrent_states, self.Cc.layers[l].recurrent_states))
                else:
                    self.assertTrue(torch.equal(cx[:, VLO:], ct[:, VLO:]) and torch.equal(cx[:, :VLO], cc[:, :VLO]))
                    self.assertTrue(torch.equal(X.layers[l].recurrent_states, self.T.layers[l].recurrent_states))
            for l in KL:
                src = self.T if grp == 'VSK' else self.Cc
                self.assertTrue(torch.equal(X.layers[l].keys, src.layers[l].keys))
            for i in range(13):
                for f in vars(X.layers[i]):
                    self.assertTrue(torch.equal(getattr(X.layers[i], f), getattr(self.Cc.layers[i], f)))
            self.assertTrue(all(torch.equal(getattr(a, f), getattr(b, f)) for a, b in zip(self.Cc.layers, C0.layers) for f in vars(a)))
            self.assertTrue(all(torch.equal(getattr(a, f), getattr(b, f)) for a, b in zip(self.T.layers, T0.layers) for f in vars(a)))

    def test_check_arm_rejects(self):
        tg = NQ.targets('QK', G, KL, VLO)
        X = NQ.replace(self.Cc, self.T, tg, get, set_, copy.deepcopy)
        X.layers[13].conv_states[:, VLO:] = 0                        # kept V channels overwritten
        with self.assertRaises(AssertionError):
            NQ.check_arm(X, self.Cc, self.T, tg, get, comps(self.Cc), beq)
        X2 = NQ.replace(self.Cc, self.T, tg, get, set_, copy.deepcopy)
        X2.layers[2].recurrent_states = X2.layers[2].recurrent_states + 1   # shallow change
        with self.assertRaises(AssertionError):
            NQ.check_arm(X2, self.Cc, self.T, tg, get, comps(self.Cc), beq)


def r(y, et, text='x', b=0.0, fs=False):
    return {'Y': y, 'etype': et, 'text': text, 'B': b, 'first_stop': fs, 'cat': 'stop' if fs else 'code', 'N': {'text': text, 'ids': [1]}}


class Pairing(unittest.TestCase):
    def test_pairing(self):
        R = {'A': {i: (r(0, 'stop', 'E') if i.endswith(('-0', '-1')) else r(1, 'correct')) for i in IDS},
             'T': {i: (r(0, 'stop', 'E') if i.endswith(('-0', '-1', '-2')) else r(1, 'correct')) for i in IDS},
             'CJ': {i: (r(0, 'mixed', 'M') if i.endswith('-0') else r(1, 'correct')) for i in IDS}}
        p = NQ.pairing(R, 'A', {'T': 'T', 'CJ': 'CJ'}, IDS)
        self.assertEqual(p['n_broken'], 12)
        self.assertEqual(p['T'], {'n_ref_broken': 18, 'both_broken': 12, 'same_type': 12, 'same_text': 12, 'ref_broken_not_in_arm': 6})
        self.assertEqual(p['CJ'], {'n_ref_broken': 6, 'both_broken': 6, 'same_type': 0, 'same_text': 0, 'ref_broken_not_in_arm': 0})


class EndToEnd(unittest.TestCase):
    def test_analyse(self):
        import nqk_analysis as A
        recs, nsr = {}, {}
        for k, i in enumerate(IDS):
            res, nres = {'C': r(1, 'correct', 'V47')}, {}
            for d in A.NEEDLES:
                bad = k % 3 == 0
                res[d] = {'T': r(0, 'stop', '', fs=True), 'CQK': r(0 if bad else 1, 'stop' if bad else 'correct', '' if bad else 'V47', fs=bad),
                          'CVSK': r(1, 'correct', 'V47')}
                nres[d] = {'T': res[d]['T'], 'CS': r(1, 'correct'), 'CV': r(1, 'correct'), 'CK': r(1, 'correct'), 'CJ': r(0, 'stop', '', fs=True)}
            recs[i] = {'scenario': SCEN[i], 'results': res, 'nsr_record_sha256': f's{k}'}
            nsr[i] = {'results': nres, '_sha': f's{k}'}
        out = A.analyse(recs, nsr)
        b = out['needles']['N_L00_C4146_D-1']
        self.assertEqual(b['CQK']['Y'], 32)
        self.assertEqual(b['pairing']['CQK']['CJ']['same_type'], 16)
        self.assertEqual(b['CJ_broken_explained'], {'by_CQK': 16, 'by_CVSK': 0, 'by_either': 16, 'by_neither': 32, 'n_CJ_broken': 48})
        nsr[IDS[0]]['_sha'] = 'other'
        with self.assertRaises(AssertionError):
            A.analyse(recs, nsr)


class Wiring(unittest.TestCase):
    def test_budget(self):
        import nqk_run as R
        f, p = R.LIMITS['formal'], R.LIMITS['preflight']
        self.assertEqual((f['t1'], f['trajectories'], f['formations'], f['prefix_prefills'], f['formation_token_forwards']), (336, 336, 144, 48, 3834))
        self.assertEqual((p['t1'], p['engineering'], p['formation_token_forwards']), (14, 2, 162))
        self.assertEqual(R.ARMS, ('T', 'CQK', 'CVSK'))


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
