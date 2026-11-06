"""CPU tests for FBR-01: labels and outcomes reachable; buffer helpers (mean, leave-scenario-out reference, random change norm); plan and budget;
the consumer runs on fabricated records.   CUDA_VISIBLE_DEVICES= python test_fbr.py [RECEIPT]"""
import json
import os
import random
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import fbr_core as K  # noqa: E402

FAM = [f'NQ0{k}' for k in range(1, 7)]
IDS = [(f, s, v) for f in FAM for s in range(4) for v in 'abc']
META = {i: (i[0], i[1]) for i in IDS}
BASE = {'T': 0.02, 'F_own': 0.98, 'F_mean': 0.95, 'F_one_s': 0.94, 'F_one_o': 0.94, 'VmK': 0.88, 'F_zero': 0.05, 'F_dmean': 0.03}
BASE.update({r: 0.04 for r in K.RAND})


def decide(over=None, seed=1):
    p = dict(BASE)
    p.update(over or {})
    rng = random.Random(seed)
    Y = {a: {i: float(rng.random() < p[a]) for i in IDS} for a in K.ARMS}
    return K.decide(Y, META, n_boot=800)


class Rules(unittest.TestCase):
    def test_outcomes_and_labels(self):
        self.assertEqual(decide()['outcome'], 'repair_beyond_random')
        self.assertTrue(all(v == 'holds' for v in decide()['labels'].values()))
        r = decide({x: 0.8 for x in K.RAND[:6]})
        self.assertEqual((r['outcome'], r['labels']['PB']), ('repair_any_change', 'fails'))
        self.assertEqual(decide({'F_mean': 0.55, 'F_one_s': 0.5, 'F_one_o': 0.5})['outcome'], 'input_specific')
        r = decide({'F_mean': 0.05, 'F_one_s': 0.05, 'F_one_o': 0.05, 'VmK': 0.05})
        self.assertEqual((r['outcome'], r['labels']['PB'], r['labels']['PD_s']), ('input_specific', 'unjudgeable', 'unjudgeable'))
        r = decide({'F_own': 0.4, 'F_mean': 0.35})
        self.assertEqual((r['outcome'], r['labels']['PA'], r['labels']['PE']), ('no_upper_bound', 'unjudgeable', 'unjudgeable'))
        r = decide({'T': 0.85})
        self.assertEqual(r['outcome'], 'no_damage')
        self.assertTrue(all(r['labels'][k] == 'unjudgeable' for k in ('PA', 'PB', 'PC', 'PD_s', 'PD_o', 'PE', 'PF')))
        self.assertEqual(decide({'F_zero': 0.9})['labels']['PC'], 'fails')
        self.assertEqual(decide({'F_one_o': 0.5})['labels']['PD_o'], 'fails')
        self.assertEqual(decide({'F_one_s': 0.5})['labels']['PD_s'], 'fails')
        self.assertEqual(decide({'VmK': 0.4})['labels']['PE'], 'fails')
        self.assertEqual(decide({'F_dmean': 0.9})['labels']['PF'], 'fails')
        self.assertAlmostEqual(K.cp_upper(0, 20), 0.168, places=2)


class Buffers(unittest.TestCase):
    def test_helpers(self):
        import torch
        import fbr_run as R
        g = torch.Generator().manual_seed(3)
        b = [torch.randn(14, 64, 4, generator=g).to(torch.bfloat16) for _ in range(5)]
        self.assertTrue(torch.equal(R.mean_buffer([b[0]]), b[0]))
        m = R.mean_buffer(b)
        self.assertEqual((m.dtype, tuple(m.shape)), (torch.bfloat16, (14, 64, 4)))
        self.assertTrue(torch.allclose(m.float(), torch.stack([x.float() for x in b]).mean(0), atol=2e-2))
        ch = R.rand_change(202611201, 21, (64, 4), 0.37)
        self.assertAlmostEqual(float(ch.norm()), 0.37, places=5)
        self.assertTrue(torch.equal(ch, R.rand_change(202611201, 21, (64, 4), 0.37)))
        self.assertFalse(torch.equal(ch, R.rand_change(202611201, 22, (64, 4), 0.37)))
        self.assertFalse(torch.equal(ch, R.rand_change(202611202, 21, (64, 4), 0.37)))
        self.assertAlmostEqual(R.cosf(b[0], b[0]), 1.0, places=6)

    def test_partners(self):
        import fbr_run as R
        led = R.LVKR.ledger()
        order = [(k, v['plan']['base_id']) for k, v in led.items()]
        scen = dict(order)
        for a in led:
            s, o, others = R.partners(a, order)
            self.assertTrue(s != a and scen[s] == scen[a] and scen[o] != scen[a])
            self.assertEqual(len(others), 48 - sum(1 for x in scen.values() if x == scen[a]))
            self.assertGreaterEqual(len(others), 30)
            self.assertTrue(all(scen[i] != scen[a] for i in others))


class Wiring(unittest.TestCase):
    def test_plan_and_budget(self):
        import fbr_run as R
        self.assertEqual(len(R.plan('calib', 0, 1)), 48)
        self.assertEqual(len(R.plan('formal', 0, 2)) + len(R.plan('formal', 1, 2)), 48)
        self.assertEqual(sorted(u['item_id'] for u in R.plan('preflight', 0, 1)), sorted(R.PREFLIGHT_ITEMS))
        self.assertEqual((len(R.ARMS), len(R.DIRS), tuple(R.ARMS), tuple(R.RAND)), (28, 4, tuple(K.ARMS), tuple(K.RAND)))
        self.assertEqual(R.LIMITS['formal']['trajectories'], 48 * (1 + 28 * 4))
        self.assertEqual(R.LIMITS['calib']['t1'], 0)
        self.assertEqual(len(set(R.SEEDS_R) & (set(R.W.SEEDS_R) | set(R.W.SEEDS_Q) | set(R.N.SEEDS))), 0)
        self.assertLessEqual(sum(R.GPU_CAP_S.values()), 3.0 * 3600)
        self.assertEqual(list(R.conditions()), list(R.DIRS))

    def test_consumer_on_fabricated_records(self):
        import fbr_analysis as A
        rng = random.Random(5)
        recs = {}
        for s in FAM:
            for j in range(8):
                i = f'X-{s}-{j}'
                item = {'target': 'U22', 'listed_codes': ['U11', 'U22', 'U33'], 'first_listed': 'U11', 'question': 'q'}
                ok = {'ids': [5, 6, 7, 2], 'termination': 'stop', 'reached_t2': True, 'text': 'U22<|im_end|>'}
                stop = {'ids': [2], 'termination': 'stop', 'reached_t2': False, 'text': '<|im_end|>'}
                dirs = {}
                for d in ('d1', 'd2'):
                    arms = {a: {'x': 5, 'N': dict(ok if rng.random() < BASE[a] else stop)} for a in K.ARMS}
                    dirs[d] = {'arms': arms, 'rand_norm_err_max': 1e-7,
                               'buffers': {k: 0.9 for k in ('cos_clean_qk', 'cos_clean_v', 'cos_damage_qk', 'cos_damage_v', 'norm_mean_minus_T', 'norm_own_minus_T', 'norm_mean_minus_own')}}
                recs[i] = {'text': i, 'scenario': s, 'item': item, 'clean': {'x': 5, 'N': dict(ok)}, 'directions': dirs}
        res = A.analyse(recs)
        self.assertEqual((res['n'], res['clean_correct']), (48, 48))
        self.assertEqual(res['outcomes']['d1'], 'repair_beyond_random')
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
