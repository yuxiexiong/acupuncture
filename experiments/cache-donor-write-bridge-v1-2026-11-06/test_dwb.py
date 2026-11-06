"""CPU tests for DWB-01: frozen read-outs (offline rehearsal), plan and budget on the real ledger, cache-level arms on fabricated caches,
the t1 hook wiring (the LVK-01 hook is the one called, with the arguments LVK-01's L11 endpoint uses), and the consumer on fabricated records.
CUDA_VISIBLE_DEVICES= python test_dwb.py [RECEIPT]"""
import inspect
import json
import os
import subprocess
import sys
import types as pytypes
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import dwb_core as K  # noqa: E402
S = K.S


class Rules(unittest.TestCase):
    def test_rehearsal(self):
        p = subprocess.run([sys.executable, str(HERE / 'analysis' / 'rehearse.py')], capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stdout[-2000:] + p.stderr[-2000:])
        self.assertIn('REHEARSAL PASS', p.stdout)

    def test_statistic_is_the_frozen_spf_one(self):
        import spf_core
        self.assertIs(K.S, spf_core)
        self.assertEqual((K.M, K.DIRS), (spf_core.M, spf_core.DIRS))


class Design(unittest.TestCase):
    def test_plan_and_budget(self):
        import dwb_run as R
        items, order = R.panel()
        self.assertEqual(len(items), 48)
        tot = K.count_trajectories(items, order)
        self.assertEqual((tot['total'], tot['hooked_total']), (3816, 2184))
        lim, n_hook = R.limits('formal')
        self.assertEqual((lim['t1'], n_hook, lim['shadow']), (3816, 2184, 28 * 2184))
        lim, n_hook = R.limits('preflight')
        self.assertEqual((lim['t1'], n_hook), (174, 96))
        self.assertEqual([u['base_id'] for u in R.plan('preflight', 0, 1)], [R.PREFLIGHT_SCENARIO])
        self.assertEqual(sum(len(u['item_ids']) for u in R.plan('formal', 0, 1)), 48)
        self.assertEqual(R.MAX_WORKERS, {'preflight': 1, 'formal': 1})
        for u in R.all_units():
            for r in u['item_ids']:
                D = R.donors_of(r, items, order)
                self.assertIn(len(D), (5, 8))
                self.assertTrue(all(d['type'] != 'OS' and items[d['id']]['scenario'] == items[r]['scenario'] and d['id'] != r for d in D))
                runs = R.arm_runs(D, R.DIRS)
                self.assertEqual(len(runs), len(set(runs)))
                self.assertEqual(runs[0], (None, 'C0', None))
                for d in R.DIRS:
                    names = [a for dd, a, _dn in runs if dd == d]
                    self.assertEqual(names[:3], ['L00', 'OO', 'L11o'])                       # prerequisite / reference arms first
                    per = [a for dd, a, dn in runs if dd == d and dn == D[0]['id']]
                    self.assertEqual(per, ['DD', 'DO', 'OD', 'L11d', 'CSTd'])                # the reference DD precedes the hooked arms that are compared with it
        self.assertEqual(list(R.conditions()), list(R.DIRS))


def fake_cache(seed, n_pos=10):
    import torch
    g = torch.Generator().manual_seed(seed)
    layers = []
    for i in range(32):
        if i % 4 == 3:
            layers.append(pytypes.SimpleNamespace(keys=torch.randn(1, 2, n_pos, 4, generator=g).to(torch.bfloat16),
                                                  values=torch.randn(1, 2, n_pos, 4, generator=g).to(torch.bfloat16)))
        else:
            layers.append(pytypes.SimpleNamespace(recurrent_states=torch.randn(1, 2, 3, 3, generator=g),
                                                  conv_states=torch.randn(1, 8192, 4, generator=g).to(torch.bfloat16)))
    return pytypes.SimpleNamespace(layers=layers)


TYPES = ['full_attention' if i % 4 == 3 else 'linear_attention' for i in range(32)]


class Edits(unittest.TestCase):
    def test_cache_level_arms(self):
        import torch
        import dwb_run as R
        C, T, Cd, Td = fake_cache(1), fake_cache(2), fake_cache(3, 12), fake_cache(4, 12)
        src = {'oc': C, 'd': Cd, 'dn': Td}
        X = R.SP.compose(T, R.TG['OO'], src)                                   # OO == FBR-01's F_own == LVK-01's F
        R.SP.check_arm(X, T, R.TG['OO'], src, TYPES, 'OO')
        Y = R.SP.FB.with_buf(T, R.SP.FB.get_buf(C, R.G14), R.G14)
        for i, _k, f in R.L.component_tensors(X, TYPES):
            self.assertTrue(torch.equal(R.L._get(X.layers[i], f), R.L._get(Y.layers[i], f)), ('OO', i, f))
        X = R.SP.compose(T, R.TG['DD'], src)                                   # DD == SPF-01's T_Bvd_Bqkown
        R.SP.check_arm(X, T, R.TG['DD'], src, TYPES, 'DD')
        Y = R.SP.compose(T, R.SP.comp_targets(R.SPF_DD_ARM), src)
        for i, _k, f in R.L.component_tensors(X, TYPES):
            self.assertTrue(torch.equal(R.L._get(X.layers[i], f), R.L._get(Y.layers[i], f)), ('DD', i, f))
        for l in R.G14:
            a = X.layers[l].conv_states
            self.assertTrue(torch.equal(a[:, R.V_LO:], Cd.layers[l].conv_states[:, R.V_LO:]) and torch.equal(a[:, :R.V_LO], C.layers[l].conv_states[:, :R.V_LO]))
        X = R.SP.compose(C, R.TG['CSTd'], src)                                 # only the deep recurrent state, taken from the donor's NEEDLE run
        R.SP.check_arm(X, C, R.TG['CSTd'], src, TYPES, 'CSTd')
        changed = {(i, f) for i, _k, f in R.L.component_tensors(X, TYPES) if not torch.equal(R.L._get(X.layers[i], f), R.L._get(C.layers[i], f))}
        self.assertEqual(changed, {(l, 'recurrent_states') for l in R.G14})
        self.assertTrue(all(torch.equal(X.layers[l].recurrent_states, Td.layers[l].recurrent_states) for l in R.G14))
        X.layers[13].conv_states = X.layers[13].conv_states + 1
        self.assertRaises(AssertionError, R.SP.check_arm, X, C, R.TG['CSTd'], src, TYPES, 'x')

    def test_hook_wiring(self):
        """The hooked arms call LVK-01's own hook and t1 wrapper; the L11 arguments are the ones LVK-01's formal run used."""
        import dwb_run as R
        self.assertTrue(inspect.isclass(R.LVKR.LHook) and callable(R.LVKR.t1L) and callable(R.LVKR.cache_equal_vmask))
        self.assertEqual(list(inspect.signature(R.LVKR.LHook.__init__).parameters), ['self', 'model', 'G', 'mode', 'a', 'b', 'vec', 'sign', 'cconv'])
        src = inspect.getsource(R.run_scenario)
        for must in ("hooked(Td, 1, 1, cconv[r], vec)", "hooked(Td, 1, 1, cconv[dn], vec)", "hooked(X_OO, 1, 0, cconv[dn], None)", "hooked(X_DD, 1, 0, cconv[r], None)",
                     "same_t1(c1, z, c1_DD, z_DD", "same_t1(c1, z, c1_OO, z_OO", "ARMS_ALL['Rk']", "QKFR.mask_vec(vecs[u_off]"):
            self.assertIn(must, src, must)
        lvk = inspect.getsource(R.LVKR.run_item)
        self.assertIn("LHook(model, G, 'cell', a=int(code[0]), b=int(code[1]), vec=vec, sign=sign, cconv=cconv)", lvk)
        self.assertIn("vec = QKFR.mask_vec(vecs[u][f'{s}|{d}'].float(), 'k')", lvk)
        self.assertIn("cconv = {l: L._get(C.layers[l], 'conv_states').clone() for l in G}", lvk)
        vecs = R.load_vectors()
        _, u, _sign = R.ARMS_ALL['Rk']
        items, order = R.panel()
        self.assertTrue(all(f'{s}|{d}' in vecs[u] for s in order for d in R.DIRS))


class Consumer(unittest.TestCase):
    def test_on_fabricated_records(self):
        import dwb_analysis as A
        import dwb_run as R
        items = json.load(open(Path(K.SPF_DIR) / 'data' / 'panel-items-lvk48.json'))['items']
        order = sorted({v['scenario'] for v in items.values()})
        follow = {'DD': True, 'DO': True, 'OD': False, 'L11d': True, 'CSTd': False}
        recs = {}
        for r, it in items.items():
            D = K.same_donors(S.donor_table(it, items, order))
            self_row = S.row_of(it, it['target'])
            item = {'target': it['target'], 'listed_codes': it['listed_codes'], 'first_listed': it['listed_codes'][0], 'question': 'q'}

            def ans(row):
                if row == 'stop':
                    return {'x': 2, 'N': {'ids': [2], 'termination': 'stop', 'reached_t2': False, 'text': '<|im_end|>'}}
                return {'x': 5, 'N': {'ids': [5, 6, 7, 2], 'termination': 'stop', 'reached_t2': True, 'text': it['listed_codes'][row] + '<|im_end|>'}}
            once, by_dir = {}, {d: {} for d in K.DIRS}
            for d, arm, dn in R.arm_runs(D, K.DIRS):
                if arm == 'C0':
                    once['C0'] = ans(self_row)
                elif dn is None:
                    by_dir[d][arm] = ans('stop' if arm == 'L00' else self_row)
                else:
                    row = {x['id']: x['row'] for x in D}[dn]
                    by_dir[d][R.run_key(arm, dn)] = ans(row if follow[arm] else self_row)
            recs[r] = {'text': r, 'scenario': it['scenario'], 'item': item, 'self_row': self_row, 'donors': D, 'once': once, 'directions': by_dir}
        res = A.analyse(recs, n_boot=400, n_perm=60)
        self.assertEqual(res['n'], 48)
        for d in K.DIRS:
            self.assertEqual(res['readings'][d], {'bridge_2x2': 'write_carries', 'local_form': 'local_write_redirects', 'needle_state': 'own_answer_without_own_state'})
        dm = res['directions'][K.MAIN]['decision']
        self.assertEqual((dm['Y']['L00'], dm['Y']['OO'], dm['labels']['margin_check']), (0.0, 1.0, 'passed'))
        self.assertEqual(res['directions'][K.MAIN]['by_donor_type']['DD']['AL']['row'], res['directions'][K.MAIN]['by_donor_type']['DD']['AL']['n'])
        json.dumps(res, default=str)


def main():
    assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
    receipt = sys.argv[1] if len(sys.argv) > 1 else None
    res = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]))
    if receipt:
        import hashlib
        repo = HERE.parent.parent
        src = {str(p.relative_to(repo)): hashlib.sha256(p.read_bytes()).hexdigest()
               for p in sorted(HERE.glob('*.py')) + sorted((HERE / 'readiness').glob('*.py')) + sorted((HERE / 'analysis').glob('*.py'))}
        import torch
        with open(receipt, 'x') as f:
            json.dump({'status': 'passed' if res.wasSuccessful() else 'failed', 'tests_run': res.testsRun, 'failures': len(res.failures),
                       'errors': len(res.errors), 'source_hashes': src, 'torch': torch.__version__}, f, indent=2)
            f.write('\n')
    sys.exit(0 if res.wasSuccessful() else 1)


if __name__ == '__main__':
    main()
