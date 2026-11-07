"""CPU acceptance: real ledger, synthetic outcomes, parser, native-state numerical identities."""
import copy
import json
import os
import sys
import unittest
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import dwr_run as R
import dwr_core as K
import dwr_analysis as A
from test_sru import ReadUse  # unchanged original-kernel, FP64, DE and native-S2 tests


class Design(unittest.TestCase):
    def test_matrix_and_partition(self):
        items, order = R.panel()
        self.assertEqual(len(items), 48)
        pair_counts = {}
        for r in items:
            ds = R.donors_of(r, items, order)
            for d in ds:
                pair_counts[d['type']] = pair_counts.get(d['type'], 0) + 1
            self.assertEqual(len(R.arm_runs(ds, R.DIRS)), len(set(R.arm_runs(ds, R.DIRS))))
        self.assertEqual(pair_counts, dict(AL=84, KS=96, RS=84, BD=84))
        lim, ne = R.limits('formal')
        self.assertEqual((lim['trajectories'], lim['t1'], ne, lim['formations'], lim['c_t2']), (5112, 936, 792, 144, 792))
        allr = [r for w in range(2) for u in R.plan('formal', w, 2) for r in u['receivers']]
        self.assertEqual(len(allr), len(set(allr)))
        self.assertEqual(set(allr), set(items))
        pre = R.plan('preflight', 0, 1)
        self.assertEqual(len(pre), 6)
        self.assertTrue(all(u['receivers'] == sorted(u['item_ids'])[:1] for u in pre))
        self.assertEqual(sum(len(R.arm_runs(R.donors_of(r, items, order), R.DIRS)) for u in pre for r in u['receivers']), R.limits('preflight')[0]['trajectories'])
        self.assertEqual(R.GPU_CAP_S['formal'] + 2 * R.GPU_CAP_S['preflight'], 9000)

    def test_two_direction_hashes_against_four_direction_reference(self):
        keys = ['base_b', 'C_b'] + ['T_b|' + d for d in R.DIRS]
        actual = {k: 'digest-' + k for k in keys}
        ref = {**actual, 'T_b|R0_L00_D-1': 'other', 'T_b|N_L00_C1343_D-1': 'other'}
        R.check_formation(actual, ref)
        for k in keys:
            bad = {**actual, k: 'wrong'}
            with self.assertRaises(AssertionError):
                R.check_formation(bad, ref)
        with self.assertRaises(AssertionError):
            R.check_formation({k:v for k,v in actual.items() if k!='C_b'}, ref)

    def test_fixed_output_zero(self):
        items, order = R.panel()
        for r in items:
            ds = R.donors_of(r, items, order)
            for x in (0,1,2,'stop','other'):
                self.assertEqual(K.S.d_transfer(ds, {d['id']: x for d in ds}), 0)

    def test_all_decisions_and_boundary(self):
        b = lambda lo, hi: dict(lo=lo, hi=hi, mean=(lo+hi)/2)
        yes, no, undec, reverse = b(.4,.8), b(0,.2), b(.1,.4), b(-.8,-.4)
        positive, absent = b(.1,.3), b(-.1,.1)
        self.assertEqual(K.level(b(.25,.25)), 'indeterminate')
        self.assertEqual(K.level(b(.25,.4)), 'holds')
        self.assertEqual(K.level(b(0,.25)), 'indeterminate')
        for g,w,recovery,vg,vw,want in [
            (yes,yes,positive,True,True,'bidirectional_same_endpoint'),
            (yes,no,positive,True,True,'conditional_gain'),
            (no,yes,positive,True,True,'self_recovery_without_gain'),
            (no,yes,absent,True,True,'transfer_loss_without_self_recovery'),
            (no,no,positive,True,True,'below_margin'),
            (undec,no,positive,True,True,'indeterminate'),
            (reverse,no,positive,True,True,'opposite_direction'),
            (yes,yes,positive,False,True,'delivery_confounded')]:
            self.assertEqual(K.decision(g,w,recovery,vg,vw), want)

    def test_consumer_and_missing(self):
        items, order = R.panel()
        recs = {}
        for r, it in items.items():
            ds = R.donors_of(r, items, order)
            selfrow = K.S.row_of(it, it['target'])
            def ans(row):
                return {'x': 5, 'N': {'ids':[5,6,2], 'text':it['listed_codes'][row]+'<|im_end|>', 'termination':'stop', 'reached_t2':True}}
            rec = dict(text=r, scenario=it['scenario'], item={**it,'first_listed':it['listed_codes'][0]}, self_row=selfrow, donors=ds,
                       once={'C0':ans(selfrow)}, directions={})
            for direction in R.DIRS:
                arms = dict(L00=ans(selfrow), L11o=ans(selfrow))
                for d in ds:
                    for a in K.DONOR_ARMS:
                        follow = a == 'L11d' or a.startswith('gain')
                        # second direction has no gain: don't pool away heterogeneity
                        if direction == R.SECOND and a.startswith('gain'):
                            follow = False
                        arms[a+'|'+d['id']] = ans(d['row'] if follow else selfrow)
                rec['directions'][direction] = arms
            recs[r] = rec
        res = A.analyse(recs, n_boot=80, n_perm=0)
        for j in K.USES:
            main = res['directions'][R.MAIN]['uses'][j]
            self.assertEqual(main['decision'], 'bidirectional_same_endpoint')
            self.assertEqual(main['recovery_n'], 168)
            self.assertEqual(main['R']['mean'], 1)
            self.assertEqual(main['R']['clusters'], 6)
            self.assertEqual(res['directions'][R.SECOND]['uses'][j]['decision'], 'self_recovery_without_gain')
        recs[next(iter(recs))]['directions'][R.MAIN].pop(next(k for k in recs[next(iter(recs))]['directions'][R.MAIN] if k.startswith('gainD|')))
        with self.assertRaises(KeyError):
            A.analyse(recs, n_boot=80, n_perm=0)

    def test_truncated_answer_is_not_valid(self):
        items,_ = R.panel()
        it = next(iter(items.values()))
        nr = {'text': it['target'], 'termination':'budget', 'reached_t2':True}
        self.assertNotIn(A.A.row_out(nr, it), (0,1,2))


def main():
    assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
    res = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]))
    if len(sys.argv)>1:
        own = list(HERE.glob('*.py')) + list((HERE/'readiness').glob('*.py'))
        R.exp.write(sys.argv[1], {'status':'passed' if res.wasSuccessful() else 'failed', 'tests_run':res.testsRun,
                    'failures':len(res.failures), 'errors':len(res.errors),
                    'source_hashes':{str(p.relative_to(R.REPO)):R.exp.sha(p) for p in own}}, immutable=True)
    sys.exit(0 if res.wasSuccessful() else 1)


if __name__ == '__main__':
    main()
