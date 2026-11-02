"""CPU tests for KHC-01: every frozen class reachable and failing cases (small h, overshoot, S, KV, both, joint_only, mixed, diag_only),
interaction tolerances, P1 and hand-over; budget arithmetic.  CUDA_VISIBLE_DEVICES= python test_khc.py [RECEIPT]"""
import json
import os
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import khc_core as K  # noqa: E402

SC = [f'NQ0{k}' for k in range(1, 7)]
IDS = [f'{s}-{j}' for s in SC for j in range(8)]
SCEN = {i: i.split('-')[0] for i in IDS}
ALL = set(IDS)


def const(v):
    return {i: v(i) if callable(v) else v for i in IDS}


def ycount(k):                                    # first k inputs of every scenario correct
    return const(lambda i: int(int(i.split('-')[1]) < k))


def case(m10, m01, m11=-2.0, y=(0, 3, 0, 3)):
    M = {'00': const(0.0), '10': const(m10), '01': const(m01), '11': const(m11)}
    Y = {c: ycount(k) for c, k in zip(('00', '10', '01', '11'), y)}
    return K.classify(M, Y, SCEN, ALL)


class Classes(unittest.TestCase):
    def test_labels(self):
        self.assertEqual(case(-1.8, -0.1)['label'], 'S')                                   # pS 0.9, pKV 0.05
        self.assertEqual(case(-0.1, -1.8, y=(0, 0, 3, 3))['label'], 'KV')
        self.assertEqual(case(-1.6, -1.6, y=(0, 3, 3, 3))['label'], 'both')
        self.assertEqual(case(-0.2, -0.2, y=(0, 0, 0, 3))['label'], 'joint_only')
        self.assertEqual(case(-1.0, -1.0, y=(0, 1, 1, 3))['label'], 'mixed')               # 0.5 / 0.5
        self.assertEqual(case(-3.0, -0.1)['label'], 'overshoot_or_sign')                   # pS 1.5
        self.assertEqual(case(-1.8, +0.6)['label'], 'overshoot_or_sign')                   # pKV -0.3
        self.assertEqual(case(-0.1, -0.1, m11=-0.4)['label'], 'small_h')

    def test_behaviour_needed(self):
        self.assertEqual(case(-1.8, -0.1, y=(0, 1, 0, 3))['label'], 'S')                   # Y net 6 >= 2
        self.assertEqual(case(-1.8, -0.1, y=(0, 0, 0, 3))['label'], 'mixed')               # S has no Y support
        self.assertEqual(case(-1.8, -0.1, y=(3, 3, 3, 3))['label'], 'S_diag_only')         # Y end-point gap zero
        three = const(lambda i: -3.4 if SCEN[i] in SC[:3] else 0.2)                       # pS 0.8 but 3/6 scenarios -> no S diag
        r = K.classify({'00': const(0.0), '10': three, '01': const(-0.1), '11': const(-2.0)}, {c: ycount(3 if c in ('10', '11') else 0) for c in ('00', '10', '01', '11')}, SCEN, ALL)
        self.assertEqual((r['label'], r['effects']['10']['n_scen_same']), ('joint_only', 3))

    def test_interaction(self):
        r = case(-1.8, -1.8, y=(0, 3, 3, 3))
        self.assertTrue(r['interaction']['M_practical'])                                   # I = -2 + 3.6 = 1.6
        self.assertTrue(r['interaction']['Y_practical'])                                   # 18 - 18 - 18 + 0 = -18
        r = case(-1.0, -1.0, y=(0, 1, 1, 2))
        self.assertFalse(r['interaction']['M_practical'])                                  # 0.0
        self.assertFalse(r['interaction']['Y_practical'])                                  # 12 - 6 - 6 = 0

    def test_p1_handover(self):
        lab = {'Rk<-V': 'S', 'V<-Rk': 'S', 'Ak<-F': 'S', 'F<-Ak': 'mixed', 'Ark<-F': 'KV', 'F<-Ark': 'KV'}
        self.assertEqual(K.p1(lab)['label'], 'holds')
        self.assertEqual(K.p1({**lab, 'Ak<-F': 'joint_only'})['label'], 'fails')
        self.assertEqual(K.p1({**lab, 'Rk<-V': 'small_h', 'V<-Rk': 'small_h'})['label'], 'not_evaluable')
        h = K.handover(lab)
        self.assertEqual((h['Rk<-V|V<-Rk'], h['Ak<-F|F<-Ak'], h['Ark<-F|F<-Ark']), ('S', 'joint_or_asymmetric', 'KV'))


class Wiring(unittest.TestCase):
    def test_budget(self):
        import khc_run as R
        f, p = R.LIMITS['formal'], R.LIMITS['preflight']
        self.assertEqual((f['t1'], f['c_t2'], f['q_extra'], f['trajectories'], f['n_steps'], f['n_bridge']),
                         (48 * 4 * 5, 48 * 4 * (5 + 6 * 4), 48 * 4 * 6, 48 * 4 * 6 * 2, 48 * 4 * 6 * 2 * 31, 48 * 4 * 6 * 2))
        self.assertEqual(f['decode_forwards'], f['t1'] + f['c_t2'] + f['q_extra'] + f['n_steps'] + f['n_bridge'])
        self.assertEqual(f['decode_forwards'] - f['n_bridge'], 79104)
        self.assertEqual((p['t1'], p['c_t2'], p['q_extra'], p['trajectories'], p['n_steps'], p['engineering']),
                         (40, 232, 48, 96 + 96, 2 * 2976, 96))
        self.assertEqual(p['decode_forwards'], p['t1'] + p['c_t2'] + p['q_extra'] + p['n_steps'] + p['engineering'])
        self.assertEqual(p['decode_forwards'], 6368)
        self.assertEqual(2 * 4 * 5 * 2, 80)                                                # engineering forwards actually used <= 96
        self.assertEqual(R.GPU_CAP_S['formal'] + 2 * R.GPU_CAP_S['preflight'], 1.5 * 3600)
        self.assertEqual(len(R.ORDERED), 6)
        self.assertEqual(tuple(R.ARMS), ('V', 'F', 'Rk', 'Ak', 'Ark'))


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
