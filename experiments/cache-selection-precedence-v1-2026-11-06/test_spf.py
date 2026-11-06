"""CPU tests for SPF-01: frozen read-outs (offline rehearsal), design table and budget on the real ledger, cache edits on fabricated caches
(against the NCC-01 helpers they must reproduce), the template tail on the real tokenizer, and the consumer on fabricated records.
CUDA_VISIBLE_DEVICES= python test_spf.py [RECEIPT]"""
import copy
import json
import os
import subprocess
import sys
import types as pytypes
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import spf_core as K  # noqa: E402


class Rules(unittest.TestCase):
    def test_rehearsal(self):
        """Every outcome and label value reachable and avoidable; margin check; exact null under donor-independent outputs."""
        p = subprocess.run([sys.executable, str(HERE / 'analysis' / 'rehearse.py')], capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stdout[-2000:] + p.stderr[-2000:])
        self.assertIn('REHEARSAL PASS', p.stdout)
        p = subprocess.run([sys.executable, str(HERE / 'analysis' / 'design_table.py')], capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stdout[-2000:] + p.stderr[-2000:])


class Design(unittest.TestCase):
    def test_panel_plan_budget(self):
        import spf_run as R
        items, order = R.panel()
        self.assertEqual((len(items), order), (48, [f'NQ0{k}' for k in range(1, 7)]))
        tot = K.count_trajectories(items, order)
        got = {None: 0, R.MAIN: 0, R.SECOND: 0}
        for u in R.all_units():
            tabs, os_ids = R.unit_tables(u, items, order)
            self.assertEqual(len(os_ids), 3)
            for r in tabs:
                runs = R.arm_runs(tabs[r], R.DIRS)
                self.assertEqual(len(runs), len(set(runs)))
                for d, arm, dn, dn2 in runs:
                    got[d] += 1
                    self.assertTrue(dn is None or dn != r)
                # prerequisite arms run before any donor arm of the same block
                for blk in (None, R.MAIN, R.SECOND):
                    names = [a for d, a, _dn, _d2 in runs if d == blk]
                    pre = [a for a in names if a in R.PRE_ARMS]
                    self.assertEqual(names[:len(pre)], pre)
        self.assertEqual((got[None], got[R.MAIN], got[R.SECOND]), (tot['once'], tot[R.MAIN], tot[R.SECOND]))
        self.assertEqual(tot['total'], 6780)
        self.assertEqual(R.limits('formal')['t1'], 6780)
        w0, w1 = R.plan('formal', 0, 2), R.plan('formal', 1, 2)
        self.assertEqual((sum(len(u['item_ids']) for u in w0), sum(len(u['item_ids']) for u in w1)), (27, 21))
        pre = R.plan('preflight', 0, 1)
        self.assertEqual([u['base_id'] for u in pre], [R.PREFLIGHT_SCENARIO])
        self.assertEqual(R.dirs_for('preflight'), (R.MAIN,))
        self.assertLess(R.limits('preflight')['t1'], 800)
        self.assertEqual(list(R.conditions()), list(R.DIRS))
        self.assertEqual((R.G14, R.G4, R.KL, R.V_LO, R.TAIL), (tuple(K.G), (16, 17, 18), (15, 19, 23, 27, 31), 4096, 4))
        self.assertLessEqual(sum(R.GPU_CAP_S.values()), 2.3 * 3600)


def fake_cache(seed, n_pos):
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
    def test_compose_matches_declared_components(self):
        import torch
        import spf_run as R
        sys.path.insert(0, str(R.NCC_DIR))
        import ncc_core as NC
        C, Tn, Dn, D2 = fake_cache(1, 10), fake_cache(2, 10), fake_cache(3, 12), fake_cache(4, 9)
        src = {'oc': C, 'on': Tn, 'd': Dn, 'd2': D2}
        for arm in K.ARMS:
            base = C if arm[0] == 'C' else Tn
            tg = R.comp_targets(arm)
            if not tg:
                continue
            X = R.compose(base, tg, src)
            R.check_arm(X, base, tg, src, TYPES, arm)
            touched = {(l, f) for l, f, _sl, _s in tg}
            for i, _k, f in R.L.component_tensors(X, TYPES):
                self.assertEqual(torch.equal(R.L._get(X.layers[i], f), R.L._get(base.layers[i], f)), (i, f) not in touched, (arm, i, f))
        # the three operations that repeat NCC-01 must equal its helper bit for bit
        for arm, grp in (('T_Sown', 'S'), ('T_Bvown', 'V'), ('T_Kown', 'K')):
            X = R.compose(Tn, R.comp_targets(arm), src)
            Y = NC.replace(Tn, C, NC.targets(grp, R.G14, R.KL, R.V_LO), R.L._get, R.L._set, copy.deepcopy)
            for i, _k, f in R.L.component_tensors(X, TYPES):
                self.assertTrue(torch.equal(R.L._get(X.layers[i], f), R.L._get(Y.layers[i], f)), (arm, i, f))
        # whole donor buffer == FBR-01's with_buf
        X = R.compose(Tn, R.comp_targets('T_Bd'), src)
        Y = R.FB.with_buf(Tn, R.FB.get_buf(Dn, R.G14), R.G14)
        for i, _k, f in R.L.component_tensors(X, TYPES):
            self.assertTrue(torch.equal(R.L._get(X.layers[i], f), R.L._get(Y.layers[i], f)), ('T_Bd', i, f))
        # slices: V / qk channels, state subsets, the last 4 cached positions of the donor KV
        X = R.compose(Tn, R.comp_targets('T_Bvd_Bqkown'), src)
        for l in R.G14:
            a = X.layers[l].conv_states
            self.assertTrue(torch.equal(a[:, R.V_LO:], Dn.layers[l].conv_states[:, R.V_LO:]) and torch.equal(a[:, :R.V_LO], C.layers[l].conv_states[:, :R.V_LO]))
        X = R.compose(C, R.comp_targets('C_S4d'), src)
        self.assertEqual({l for l in R.G14 if not torch.equal(X.layers[l].recurrent_states, C.layers[l].recurrent_states)}, set(R.G4))
        X = R.compose(C, R.comp_targets('C_Sod'), src)
        self.assertEqual({l for l in R.G14 if not torch.equal(X.layers[l].recurrent_states, C.layers[l].recurrent_states)}, set(R.GO))
        X = R.compose(Tn, R.comp_targets('T_Kd'), src)
        for l in R.KL:
            for f in ('keys', 'values'):
                a, b, r = getattr(X.layers[l], f), getattr(Dn.layers[l], f), getattr(Tn.layers[l], f)
                self.assertEqual(a.shape, r.shape)
                self.assertTrue(torch.equal(a[:, :, -4:], b[:, :, -4:]) and torch.equal(a[:, :, :-4], r[:, :, :-4]))
        self.assertTrue(all(torch.equal(X.layers[l].keys, Tn.layers[l].keys) for l in (3, 7, 11)))
        # sources and base are never modified
        for seed, c, n in ((1, C, 10), (2, Tn, 10), (3, Dn, 12), (4, D2, 9)):
            ref = fake_cache(seed, n)
            for i, _k, f in R.L.component_tensors(c, TYPES):
                self.assertTrue(torch.equal(getattr(c.layers[i], f), getattr(ref.layers[i], f)))

    def test_check_arm_detects_tampering(self):
        import spf_run as R
        C, Tn, Dn = fake_cache(1, 10), fake_cache(2, 10), fake_cache(3, 12)
        src = {'oc': C, 'on': Tn, 'd': Dn}
        tg = R.comp_targets('T_Bd')
        X = R.compose(Tn, tg, src)
        X.layers[13].recurrent_states = X.layers[13].recurrent_states + 1          # a tensor the arm must not touch
        self.assertRaises(AssertionError, R.check_arm, X, Tn, tg, src, TYPES, 'x')
        X = R.compose(Tn, tg, src)
        X.layers[16].conv_states[0, 5000, 1] += 1                                   # a targeted slice that no longer equals its source
        self.assertRaises(AssertionError, R.check_arm, X, Tn, tg, src, TYPES, 'x')
        X = R.compose(Tn, R.comp_targets('T_Kd'), src)
        X.layers[19].keys[0, 0, 2, 0] += 1                                          # a position outside the last 4
        self.assertRaises(AssertionError, R.check_arm, X, Tn, R.comp_targets('T_Kd'), src, TYPES, 'x')


class Tokens(unittest.TestCase):
    def test_template_tail_identical_across_inputs(self):
        """The donor-KV arm and the conv buffer both rely on the last 4 cached positions being the same template tokens in every input."""
        import spf_run as R
        sys.path.insert(0, str(R.T1.SOURCE))
        from control_engine import encode_text
        from transformers import AutoTokenizer
        tok = AutoTokenizer.from_pretrained(R.exp.read(R.T1.SOURCE / 'contract.json')['source']['model_path'])
        led = R.LVKR.ledger()
        ctx = R.exp.contexts_for(tok, [v['item'] for v in led.values()])
        tails = set()
        for k, v in led.items():
            seg = R.PK.label_tokens(tok, ctx[k], v['item']['boundary_text'], encode_text)
            self.assertEqual(len(seg['ids']), v['plan']['n'])
            self.assertEqual(R.exp.digest(seg['ids']), v['plan']['prompt_token_sha256'])
            tails.add(tuple(seg['ids'][-1 - R.TAIL:-1]))
        self.assertEqual(len(tails), 1)
        print('template tail tokens:', list(tails)[0], repr(tok.decode(list(list(tails)[0]), skip_special_tokens=False)))


class Consumer(unittest.TestCase):
    def test_on_fabricated_records(self):
        import spf_analysis as A
        items = json.load(open(HERE / 'data' / 'panel-items-lvk48.json'))['items']
        order = sorted({v['scenario'] for v in items.values()})
        recs = {}
        for r, it in items.items():
            D = K.donor_table(it, items, order)
            self_row = K.row_of(it, it['target'])
            item = {'target': it['target'], 'listed_codes': it['listed_codes'], 'first_listed': it['listed_codes'][0], 'question': 'q'}

            def ans(row):
                if row == 'stop':
                    return {'x': 2, 'N': {'ids': [2], 'termination': 'stop', 'reached_t2': False, 'text': '<|im_end|>'}}
                return {'x': 5, 'N': {'ids': [5, 6, 7, 2], 'termination': 'stop', 'reached_t2': True, 'text': it['listed_codes'][row] + '<|im_end|>'}}

            def world(arm, dn, dn2):                 # the hypothesised pattern: an own-clean or donor state decides; otherwise a clean buffer decides
                S, Bv, Bqk, _k, _d, _s = K.ARMS[arm]
                base = 'oc' if arm[0] == 'C' else 'on'
                S, Bv, Bqk = (base if x == '-' else x for x in (S, Bv, Bqk))
                row = {x['id']: x['row'] for x in D}
                if S in ('oc', 'do'):
                    return self_row
                if S in ('d', 'd4'):
                    return row[dn]
                if Bv != 'on' and Bqk != 'on':
                    return self_row if Bv == 'oc' else row[dn2 if Bv == 'd2' else dn]
                return 0 if Bv != 'on' else 'stop'
            once, by_dir = {}, {d: {} for d in K.DIRS}
            import spf_run as R
            for d, arm, dn, dn2 in R.arm_runs(D, K.DIRS):
                (once if d is None else by_dir[d])[R.run_key(arm, dn, dn2)] = ans(world(arm, dn, dn2))
            recs[r] = {'text': r, 'scenario': it['scenario'], 'item': item, 'self_row': self_row, 'donors': D, 'once': once, 'directions': by_dir}
        res = A.analyse(recs, n_boot=500, n_perm=100)
        self.assertEqual(res['n'], 48)
        self.assertEqual(res['outcomes'], {K.MAIN: 'source_modulates', K.SECOND: 'source_modulates'})
        dm = res['directions'][K.MAIN]['decision']
        self.assertEqual((dm['labels']['R_S'], dm['labels']['R_QK'], dm['labels']['V'], dm['labels']['READ'], dm['labels']['margin_check']),
                         ('holds', 'holds', 'holds', 'row', 'passed'))
        self.assertEqual(dm['Y']['T0'], 0.0)
        self.assertEqual(res['directions'][K.MAIN]['categories']['T0']['stop'], 48)
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
