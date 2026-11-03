"""CPU tests for SRU-01: read_use with a=b=0 == original kernel bit for bit (output and S2); returned S2 is always the receiver's native update;
cell 11 local output == replicated original fed Sd within 1e-5; FP64 oracle for 10/01/11; frozen labels pass and fail; budget.
CUDA_VISIBLE_DEVICES= python test_sru.py [RECEIPT]"""
import json
import os
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import sru_core as K  # noqa: E402

SC = [f'NQ0{k}' for k in range(1, 7)]
IDS = [f'{s}-{j}' for s in SC for j in range(8)]
SCEN = {i: i.split('-')[0] for i in IDS}
ALL = set(IDS)


def const(v):
    return {i: v(i) if callable(v) else v for i in IDS}


def ycount(k):
    return const(lambda i: int(int(i.split('-')[1]) < k))


def case(m10, m01, m11, y=(0, 0, 0, 3), pname='gain'):
    M = {'00': const(0.0), '10': const(m10), '01': const(m01), '11': const(m11)}
    Y = {c: ycount(k) for c, k in zip(('00', '10', '01', '11'), y)}
    return K.pair(M, Y, SCEN, ALL, pname, Mdonor00=const(2.0 if pname == 'gain' else -2.0))


class Rules(unittest.TestCase):
    def test_labels(self):
        self.assertEqual(case(1.6, 0.1, 1.8, y=(0, 3, 0, 3))['label'], 'direct_dominant')
        self.assertEqual(case(0.1, 1.6, 1.8, y=(0, 0, 3, 3))['label'], 'correction_dominant')
        self.assertEqual(case(1.0, 1.0, 1.8, y=(0, 2, 2, 3))['label'], 'both_single')
        self.assertEqual(case(0.1, 0.1, 1.8)['label'], 'joint_only')
        self.assertEqual(case(0.1, 0.1, 1.8, y=(0, 0, 0, 0))['label'], 'diag_only')
        self.assertEqual(case(0.1, 0.1, 0.2)['label'], 'weak')
        self.assertEqual(case(-0.5, 0.1, 1.8)['label'], 'opposite')
        self.assertEqual(case(-1.6, -0.1, -1.8, y=(3, 0, 3, 0), pname='withdraw')['label'], 'direct_dominant')
        self.assertEqual(case(1.2, 0.1, 1.8, y=(0, 3, 0, 3))['label'], 'joint_only')                 # r10 = 0.67 < 0.75, and joint 10 present? -> not direct

    def test_ratios_and_direction(self):
        r = case(1.6, 0.1, 1.8, y=(0, 3, 0, 3))
        self.assertAlmostEqual(r['r10'], 1.6 / 1.8)
        self.assertAlmostEqual(r['d11_over_g'], 0.9)
        w = case(-1.6, -0.1, -1.8, y=(3, 0, 3, 0), pname='withdraw')
        self.assertTrue(K.direction({'gain': r, 'withdraw': w})['bidirectional_direct'])
        self.assertFalse(K.direction({'gain': r, 'withdraw': case(-0.1, -0.1, -0.2, pname='withdraw')})['bidirectional_direct'])


class ReadUse(unittest.TestCase):
    def test_kernel_identities(self):
        import torch
        import sru_run as R
        QM = R.gdn_module()
        orig = QM.torch_recurrent_gated_delta_rule
        g = torch.Generator().manual_seed(4)
        rnd = lambda *s: torch.randn(*s, generator=g)   # noqa: E731
        q, k, v = [rnd(1, 1, 32, 128).to(torch.bfloat16) for _ in range(3)]
        gg, b = -torch.rand(1, 1, 32, generator=g), torch.rand(1, 1, 32, generator=g).to(torch.bfloat16)
        Sr, Sd = rnd(1, 32, 128, 128) * 0.1, rnd(1, 32, 128, 128) * 0.1
        o0, S0 = orig(q, k, v, g=gg, beta=b, initial_state=Sr.clone(), output_final_state=True, use_qk_l2norm_in_kernel=True)
        o00, S00, _, _, _ = R.read_use(q, k, v, gg, b, Sr.clone(), Sd, 0, 0, QM.l2norm)
        self.assertTrue(R.bit_equal(o0, o00)[0] and R.bit_equal(S0, S00)[0])
        od, Sdd = orig(q, k, v, g=gg, beta=b, initial_state=Sd.clone(), output_final_state=True, use_qk_l2norm_in_kernel=True)
        _, _, pre_d, _, _ = R.read_use(q, k, v, gg, b, Sd.clone(), Sd, 0, 0, QM.l2norm)
        for a_, b_ in ((1, 0), (0, 1), (1, 1)):
            o, S2, pre, st, err = R.read_use(q, k, v, gg, b, Sr.clone(), Sd, a_, b_, QM.l2norm, oracle=True)
            self.assertTrue(R.bit_equal(S2, S0)[0])                                   # stored state is always the receiver's native update
            self.assertLessEqual(err, R.ORACLE_TOL)
            self.assertEqual(tuple(st.shape), (32, 3))
            if (a_, b_) == (1, 1):
                rel = float((pre.double() - pre_d.double()).abs().max() / max(1.0, float(pre_d.double().abs().max())))
                self.assertLessEqual(rel, R.ORACLE_TOL)
                self.assertLess(float((o.float() - od.float()).abs().max()), 0.05)
            else:
                self.assertFalse(torch.equal(o, o0))


class Wiring(unittest.TestCase):
    def test_budget(self):
        import sru_run as R
        f, p = R.LIMITS['formal'], R.LIMITS['preflight']
        self.assertEqual((f['t1'], f['trajectories'], f['c_t2'], f['refs'], f['shadow']), (48 * 4 * 2, 48 * 4 * 2 * 4, 48 * 4 * 2 * 4, 1536, 48 * 4 * 42))
        self.assertEqual(f['decode_forwards'], 51072)
        self.assertEqual(p['decode_forwards'], 2128)
        self.assertEqual(f['formation_token_forwards'], 6390)
        self.assertAlmostEqual(R.GPU_CAP_S['formal'] + 2 * R.GPU_CAP_S['preflight'], 1.5 * 3600)
        self.assertEqual(len(R.plan('formal', 0, 2)) + len(R.plan('formal', 1, 2)), 48)
        self.assertEqual(sorted(u['item_id'] for u in R.plan('preflight', 0, 1)), sorted(R.PREFLIGHT_ITEMS))


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
