"""WIN-01 CPU tests (no model).  Includes the 6.2 rehearsal: every criterion is shown to be satisfiable and not satisfiable
on synthetic data.  Run: python -m unittest test_win -v   (server .venv-bench, CPU)."""
import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import torch

import win_core as W
import win_analysis as A
import win_reading as RD

TYPES = (['linear_attention'] * 3 + ['full_attention']) * 8


class Layer:
    pass


class Cache:
    def __init__(self, seq, seed):
        g = torch.Generator().manual_seed(seed)
        self.layers = []
        for k in TYPES:
            lay = Layer()
            if k == 'full_attention':
                lay.keys = torch.randn(1, 2, seq, 4, generator=g)
                lay.values = torch.randn(1, 2, seq, 4, generator=g)
            else:
                lay.recurrent_states = torch.randn(1, 2, 4, 4, generator=g)
                lay.conv_states = torch.randn(1, 8, 3, generator=g)
            self.layers.append(lay)


def get(layer, f):
    return getattr(layer, f)


def set_(layer, f, t):
    setattr(layer, f, t)


def fields(cache):
    out = []
    for i, k in enumerate(TYPES):
        out += [(i, 'keys'), (i, 'values')] if k == 'full_attention' else [(i, 'recurrent_states'), (i, 'conv_states')]
    return out


class TestWindows(unittest.TestCase):
    def test_masks(self):
        n, b = 10, 3
        self.assertEqual(W.window_mask('W_all', n, b), [True] * 9)
        self.assertEqual(W.window_mask('W_pre', n, b), [True] * 4 + [False] * 5)
        self.assertEqual(W.window_mask('W_post', n, b), [False] * 4 + [True] * 5)
        pre, post = W.window_mask('W_pre', n, b), W.window_mask('W_post', n, b)
        self.assertEqual([a or c for a, c in zip(pre, post)], W.window_mask('W_all', n, b))
        self.assertFalse(any(a and c for a, c in zip(pre, post)))
        with self.assertRaises(AssertionError):
            W.window_mask('W_all', 10, 8)


class TestTargets(unittest.TestCase):
    def test_sets(self):
        lin = W.linear_layers(TYPES)
        att = W.attn_layers(TYPES)
        self.assertEqual(att, W.KV_LAYERS)
        self.assertEqual(len(lin), 24)
        self.assertEqual({l for l, f, _ in W.arm_targets('S_deep', TYPES)}, set(W.G14))
        self.assertEqual(W.arm_targets('T', TYPES), [])
        rk = W.arm_targets('R+KV_all', TYPES)
        self.assertEqual(len(rk), 24 + 16)
        kp = W.arm_targets(W.ATTR_ARM, TYPES, b=5)
        self.assertTrue(all(sl == ('pos', 5) for l, f, sl in kp if f in ('keys', 'values')))
        self.assertEqual(len(W.arm_targets('Bx_all', TYPES)), 24 + 24 + 16)


class TestReplace(unittest.TestCase):
    def test_whole_and_slice(self):
        recv, donor = Cache(9, 1), Cache(9, 2)
        h = [get(recv.layers[i], f).clone() for i, f in fields(recv)]
        for arm in ('R_all', 'S_deep', 'KV_all', 'R+KV_all', 'Bx_all'):
            tg = W.arm_targets(arm, TYPES)
            X = W.replace(recv, donor, tg, get, set_, copy.deepcopy)
            W.check_replace(X, recv, donor, tg, fields(recv), get, torch.equal)
        tg = W.arm_targets(W.ATTR_ARM, TYPES, b=3)
        X = W.replace(recv, donor, tg, get, set_, copy.deepcopy)
        W.check_replace(X, recv, donor, tg, fields(recv), get, torch.equal)
        k = X.layers[3].keys
        self.assertTrue(torch.equal(k[:, :, :4], donor.layers[3].keys[:, :, :4]))
        self.assertTrue(torch.equal(k[:, :, 4:], recv.layers[3].keys[:, :, 4:]))
        self.assertTrue(all(torch.equal(a, get(recv.layers[i], f)) for a, (i, f) in zip(h, fields(recv))), 'receiver mutated')

    def test_check_catches_errors(self):
        recv, donor = Cache(9, 1), Cache(9, 2)
        tg = W.arm_targets('R_all', TYPES)
        X = W.replace(recv, donor, tg, get, set_, copy.deepcopy)
        X.layers[3].keys = X.layers[3].keys + 1          # non-target change
        with self.assertRaises(AssertionError):
            W.check_replace(X, recv, donor, tg, fields(recv), get, torch.equal)
        X = W.replace(recv, donor, W.arm_targets(W.ATTR_ARM, TYPES, b=3), get, set_, copy.deepcopy)
        X.layers[7].values[:, :, 6] += 1                   # outside the slice
        with self.assertRaises(AssertionError):
            W.check_replace(X, recv, donor, W.arm_targets(W.ATTR_ARM, TYPES, b=3), fields(recv), get, torch.equal)

    def test_shape_mismatch(self):
        with self.assertRaises(AssertionError):
            W.replace(Cache(9, 1), Cache(10, 2), W.arm_targets('KV_all', TYPES), get, set_, copy.deepcopy)


def synth(n_scen=6, per=8):
    units = [f's{s}u{i}' for s in range(n_scen) for i in range(per)]
    scen = {u: u.split('u')[0] for u in units}
    return units, scen


class TestCriteria(unittest.TestCase):
    """6.2 rehearsal: each label is reachable and each can fail."""

    def setUp(self):
        self.units, self.scen = synth()
        self.draws = W.boot_index(self.units, self.scen)

    def ys(self, frac):
        k = round(frac * 8)
        return {u: int(int(u.split('u')[1]) < k) for u in self.units}

    def test_bootstrap_groups(self):
        d = self.draws[0]
        self.assertEqual(len(d), 6)
        self.assertTrue(all(len(g) == 8 for g in d))
        self.assertEqual(self.draws, W.boot_index(self.units, self.scen))      # fixed seed

    def test_testable(self):
        self.assertTrue(W.testable(self.ys(0.0)))
        self.assertFalse(W.testable(self.ys(0.9)))

    def test_window_change(self):
        t = self.ys(0.0)
        r = W.window_contrast(self.ys(1.0), t, self.ys(0.25), t, self.units, self.scen, self.draws)
        self.assertEqual(r['label'], 'changes')

    def test_window_no_difference(self):
        t = self.ys(0.0)
        r = W.window_contrast(self.ys(0.5), t, self.ys(0.5), t, self.units, self.scen, self.draws)
        self.assertEqual(r['label'], 'no_detectable_difference')

    def test_window_indeterminate(self):
        import random
        rng = random.Random(3)
        t = self.ys(0.0)
        a = {u: rng.random() < 0.5 for u in self.units}
        c = {u: rng.random() < 0.4 for u in self.units}
        r = W.window_contrast({u: int(v) for u, v in a.items()}, t, {u: int(v) for u, v in c.items()}, t, self.units, self.scen, self.draws)
        self.assertEqual(r['label'], 'indeterminate')

    def test_window_not_applicable(self):
        r = W.window_contrast(self.ys(1.0), self.ys(0.9), self.ys(0.5), self.ys(0.0), self.units, self.scen, self.draws)
        self.assertEqual(r['label'], 'not_applicable')

    def test_effect_uses_T(self):
        # same arm counts but different T in the two windows -> the effect differs
        r = W.window_contrast(self.ys(1.0), self.ys(0.875), self.ys(1.0), self.ys(0.0), self.units, self.scen, self.draws)
        self.assertEqual(r['label'], 'not_applicable')          # 6/48 errors under T: below the testability floor
        r = W.window_contrast(self.ys(1.0), self.ys(0.75), self.ys(1.0), self.ys(0.0), self.units, self.scen, self.draws)
        self.assertEqual(r['label'], 'changes')                 # exactly 12/48 errors: testable
        r = W.window_contrast(self.ys(1.0), self.ys(0.5), self.ys(1.0), self.ys(0.0), self.units, self.scen, self.draws)
        self.assertEqual(r['label'], 'changes')
        self.assertAlmostEqual(r['mean'], -0.5)

    def test_same_window(self):
        t = self.ys(0.0)
        self.assertEqual(W.same_window_contrast(self.ys(0.75), self.ys(0.25), t, self.units, self.scen, self.draws)['label'], 'has_effect')
        self.assertEqual(W.same_window_contrast(self.ys(0.25), self.ys(0.25), t, self.units, self.scen, self.draws)['label'], 'no_detectable_difference')

    def test_transfer(self):
        hi = W.describe(self.ys(0.75), self.units, self.scen, self.draws)
        lo = W.describe(self.ys(0.0), self.units, self.scen, self.draws)
        mid = W.describe(self.ys(0.25), self.units, self.scen, self.draws)
        self.assertEqual(W.transfer_label(hi, 0.0), 'transferred')
        self.assertEqual(W.transfer_label(lo, 0.0), 'not_transferred')
        self.assertEqual(W.transfer_label(mid, 0.0), 'indeterminate')
        self.assertEqual(W.transfer_label(hi, 0.6), 'indeterminate')     # the null D0 moves the bar


def fake_records(fact_y, code_y, b_label='other_fact'):
    """Minimal synthetic records in the runner's format; fact answers carry their label in the text."""
    recs = []
    for s in range(3):
        for kind in ('fact',):
            versions = {}
            for v in ('f0', 'f1'):
                u = f'F{s}-{v}'

                def ans(lab):
                    return {'answer_text': f'{u}:{lab}', 'first_step_stop': lab == 'not_delivered'}
                res = {'C': ans('follows_fact')}
                for d in W.NEEDLES:
                    res[d] = {}
                    for w in W.WINDOWS:
                        arms = W.ARMS + ((W.ATTR_ARM,) if w == 'W_all' else ())
                        res[d][w] = {a: ans(fact_y(d, w, a, s, v)) for a in arms}
                versions[v] = {'item_id': u, 'results': res}
            B = {v: {a: {'answer_text': f'F{s}-{v}:{b_label}'} for a in W.B_ARMS} for v in ('f0', 'f1')}
            recs.append({'task': 'fact', 'unit': {'base_id': f'F{s}', 'panel': 'p', 'aligned': True}, 'versions': versions, 'B': B})
    for s in range(3):
        for i in range(4):
            u = f'C{s}-{i}'
            res = {'C': {'Y': 1}}
            for d in W.NEEDLES:
                res[d] = {}
                for w in W.WINDOWS:
                    arms = W.ARMS + ((W.ATTR_ARM,) if w == 'W_all' else ())
                    res[d][w] = {a: {'Y': code_y(d, w, a, s, i), 'first_stop': False, 'cat': 'x'} for a in arms}
            recs.append({'task': 'code', 'unit': {'item_id': u}, 'scenario': f'N{s}', 'results': res})
    return recs


def label_map(recs):
    out = {}
    for r in recs:
        if r['task'] != 'fact':
            continue
        for v in ('f0', 'f1'):
            ver = r['versions'][v]
            texts = [ver['results']['C']['answer_text']] + [x['answer_text'] for d in W.NEEDLES for w in W.WINDOWS for x in ver['results'][d][w].values()]
            texts += [x['answer_text'] for x in r['B'][v].values()]
            for t in texts:
                out[A.text_key(ver['item_id'], t)] = t.split(':')[1]
    return out


class TestAnalysis(unittest.TestCase):
    def test_end_to_end(self):
        def fy(d, w, a, s, v):
            if a == 'T':
                return 'not_delivered'
            if w == 'W_post' or a in ('R+KV_all', W.ATTR_ARM):
                return 'follows_fact'
            return 'other_wrong'

        def cy(d, w, a, s, i):
            return 0 if a == 'T' else 1
        recs = fake_records(fy, cy)
        out = A.analyse(recs, label_map(recs))
        self.assertEqual(out['cells']['fact|C']['correct'], 6)
        c = out['cells'][f'fact|{W.NEEDLES[0]}|W_post|R_all']
        self.assertEqual((c['correct'], c['rescued'], c['broken']), (6, 6, 0))
        self.assertEqual(out['cells'][f'fact|{W.NEEDLES[0]}|W_all|R_all']['correct'], 0)
        self.assertEqual(out['B']['Bx_R']['donor_fact'], 6)
        self.assertEqual(out['B']['Bx_R']['label'], 'transferred')
        self.assertIn('M1|L0|R_all|W_post-W_all', out['main']['fact'])
        self.assertIn('M2|L0|S_deep|W_post-W_all', out['main']['code'])

    def test_missing_label_stops(self):
        recs = fake_records(lambda *a: 'follows_fact', lambda *a: 1)
        labels = label_map(recs)
        labels.pop(next(iter(labels)))
        with self.assertRaises(AssertionError):
            A.analyse(recs, labels)


class TestReading(unittest.TestCase):
    def test_collect_reuse_cells(self):
        recs = fake_records(lambda *a: 'follows_fact', lambda *a: 1)
        rows = RD.collect(recs)
        reuse = [r for r in rows if r[4] is not None]
        # per version: C + 4 W_all bridge arms x 2 needles
        self.assertEqual(len(reuse), 6 * (1 + 4 * 2))
        self.assertEqual(len(rows), 6 * (1 + 2 * (3 * 5 + 1) + 4))

    def test_join(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            for sub in ('labels', 'second', 'second-packets'):
                (d / sub).mkdir()
            key = {'Wa': {'text_key': 'i|1', 'item_id': 'i', 'cells': []}, 'Wb': {'text_key': 'i|2', 'item_id': 'i', 'cells': []}}
            json.dump(key, open(d / 'key.json', 'w'))
            json.dump({'i|0': 'follows_fact'}, open(d / 'reused.json', 'w'))
            json.dump({'items': [{'responses': [{'id': 'Wa'}]}]}, open(d / 'second-packets/X.json', 'w'))
            (d / 'labels/X.jsonl').write_text('{"id":"Wa","fact":"follows_fact"}\n{"id":"Wb","fact":"other_fact"}\n')
            (d / 'second/X.jsonl').write_text('{"id":"Wa","fact":"other_wrong"}\n')
            with self.assertRaises(AssertionError):           # disagreement without adjudication
                RD.join(d)
            json.dump({'Wa': {'label': 'follows_fact', 'reason': 'last conclusion is the expected fact'}}, open(d / 'adjudication.json', 'w'))
            res = RD.join(d)
            lab = json.load(open(d / 'labels.json'))
            self.assertEqual(lab, {'i|0': 'follows_fact', 'i|1': 'follows_fact', 'i|2': 'other_fact'})
            self.assertEqual(res['disagreements'], ['Wa'])


class TestPlan(unittest.TestCase):
    def test_units(self):
        import win_run as WR
        fu, cu = WR.fact_units(), WR.code_units()
        self.assertEqual((len(fu), len(cu)), (24, 48))
        self.assertEqual(sum(u['aligned'] for u in fu), 22)
        a, b = WR.plan('formal', 0, 2), WR.plan('formal', 1, 2)
        self.assertEqual(len(a) + len(b), 72)
        self.assertFalse({u['key'] for u in a} & {u['key'] for u in b})
        pre = WR.plan('preflight', 0, 1)
        self.assertEqual([u['task'] for u in pre], ['fact', 'code', 'code'])
        self.assertEqual(WR.PER_ITEM, 33)


if __name__ == '__main__':
    unittest.main()
