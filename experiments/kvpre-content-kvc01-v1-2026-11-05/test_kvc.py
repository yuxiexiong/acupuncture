"""KVC-01 CPU tests (no model) incl. the 6.2 rehearsal.  python -m unittest test_kvc -v"""
import copy
import random
import unittest

import torch

import kvc_core as K
import kvc_analysis as A

UNITS = [f's{s}u{i}' for s in range(11) for i in range(4)]       # 44 receivers, 11 scenarios
SCEN = {u: u.split('u')[0] for u in UNITS}


def labs(frac_d, frac_r, seed=0):
    rng = random.Random(seed)
    out = {}
    for u in UNITS:
        x = rng.random()
        out[u] = 'D' if x < frac_d else ('R' if x < frac_d + frac_r else 'O')
    return out


class TestMOther(unittest.TestCase):
    def test_directed_transfer(self):
        same = {u: 'R' for u in UNITS}
        self.assertEqual(K.m_other_label(same, {u: 'D' for u in UNITS}, UNITS, SCEN)['label'], 'directed_transfer')

    def test_recovery_kept(self):
        same = {u: 'R' for u in UNITS}
        self.assertEqual(K.m_other_label(same, dict(same), UNITS, SCEN)['label'], 'recovery_kept_not_following')

    def test_recovery_reduced(self):
        same = {u: 'R' for u in UNITS}
        self.assertEqual(K.m_other_label(same, {u: 'O' for u in UNITS}, UNITS, SCEN)['label'], 'recovery_reduced_not_following')

    def test_indeterminate(self):
        same = {u: 'R' for u in UNITS}
        self.assertEqual(K.m_other_label(same, labs(0.15, 0.7, 3), UNITS, SCEN)['label'], 'indeterminate')

    def test_d0_moves_bar(self):
        same = labs(0.6, 0.4, 1)
        r = K.m_other_label(same, labs(0.7, 0.3, 2), UNITS, SCEN)
        self.assertNotEqual(r['label'], 'directed_transfer')


class TestTransferAndDiff(unittest.TestCase):
    def test_transfer(self):
        base = {u: 'R' for u in UNITS}
        self.assertEqual(K.transfer_label({u: 'D' for u in UNITS}, base, UNITS, SCEN)['label'], 'transferred')
        self.assertEqual(K.transfer_label(base, base, UNITS, SCEN)['label'], 'not_transferred')
        self.assertEqual(K.transfer_label(labs(0.15, 0.85, 4), base, UNITS, SCEN)['label'], 'indeterminate')

    def test_paired(self):
        d, r = {u: 'D' for u in UNITS}, {u: 'R' for u in UNITS}
        self.assertEqual(K.paired_difference(d, r, UNITS, SCEN)['label'], 'responses_differ')
        self.assertEqual(K.paired_difference(d, dict(d), UNITS, SCEN)['label'], 'no_detected_difference')
        self.assertEqual(K.paired_difference(labs(0.5, 0.5, 5), labs(0.4, 0.6, 6), UNITS, SCEN)['label'], 'indeterminate')

    def test_three_way(self):
        self.assertEqual([K.three_way(x) for x in ('follows_fact', 'other_fact', 'other_wrong', 'not_delivered', 'unclear')], list('RDOOO'))


class Layer:
    pass


class Cache:
    def __init__(self, seed, seq=10):
        g = torch.Generator().manual_seed(seed)
        self.layers = []
        for k in TYPES:
            lay = Layer()
            if k == 'full_attention':
                lay.keys, lay.values = torch.randn(1, 2, seq, 4, generator=g), torch.randn(1, 2, seq, 4, generator=g)
            else:
                lay.recurrent_states, lay.conv_states = torch.randn(1, 2, 4, 4, generator=g), torch.randn(1, 8, 3, generator=g)
            self.layers.append(lay)


TYPES = (['linear_attention'] * 3 + ['full_attention']) * 8


class TestTargets(unittest.TestCase):
    def test_kvpre_only(self):
        tg = K.kvpre_targets(TYPES, 5)
        self.assertEqual({l for l, f, s in tg}, set(K.attn_layers(TYPES)))
        self.assertTrue(all(s == ('pos', 5) for _, _, s in tg))
        get = lambda lay, f: getattr(lay, f)      # noqa: E731
        set_ = lambda lay, f, t: setattr(lay, f, t)   # noqa: E731
        recv, donor = Cache(1), Cache(2)
        X = K.replace(recv, donor, tg, get, set_, copy.deepcopy)
        fields = [(i, f) for i, k in enumerate(TYPES) for f in (('keys', 'values') if k == 'full_attention' else ('recurrent_states', 'conv_states'))]
        K.check_replace(X, recv, donor, tg, fields, get, torch.equal)
        self.assertTrue(torch.equal(X.layers[3].keys[:, :, :6], donor.layers[3].keys[:, :, :6]))
        self.assertTrue(torch.equal(X.layers[3].keys[:, :, 6:], recv.layers[3].keys[:, :, 6:]))
        self.assertTrue(torch.equal(X.layers[0].recurrent_states, recv.layers[0].recurrent_states))


def fake_records():
    recs = []
    for s in range(3):
        versions = {}
        for v, o in (('f0', 'f1'), ('f1', 'f0')):
            u = f'X{s}-{v}'
            res = {'C': {'answer_text': f'{u}:follows_fact'}, 'B_pre': {'answer_text': f'{u}:other_fact'}}
            for d in K.NEEDLES:
                res[d] = {'M_same': {'answer_text': f'{u}:follows_fact'}, 'M_other': {'answer_text': f'{u}:other_fact'}}
            versions[v] = {'item_id': u, 'donor_item_id': f'X{s}-{o}', 'results': res}
        recs.append({'unit': {'base_id': f'X{s}'}, 'versions': versions})
    return recs


def label_map(recs):
    out = {}
    for r in recs:
        for v in ('f0', 'f1'):
            ver = r['versions'][v]
            ts = [ver['results']['C'], ver['results']['B_pre']] + [ver['results'][d][c] for d in K.NEEDLES for c in K.CELLS]
            for x in ts:
                out[A.text_key(ver['item_id'], x['answer_text'])] = x['answer_text'].split(':')[1]
    return out


class TestAnalysis(unittest.TestCase):
    def test_end_to_end(self):
        recs = fake_records()
        out = A.analyse(recs, label_map(recs))
        self.assertEqual(out['n_receivers'], 6)
        self.assertEqual(out['cells']['B_pre']['RDO']['D'], 6)
        self.assertEqual(set(out['M_other']), set(K.NEEDLES))
        self.assertEqual(len(out['differences']), 6)

    def test_missing(self):
        recs = fake_records()
        lab = label_map(recs)
        lab.pop(next(iter(lab)))
        with self.assertRaises(AssertionError):
            A.analyse(recs, lab)


class TestPlan(unittest.TestCase):
    def test_plan(self):
        import kvc_run as KR
        a, b = KR.plan('formal', 0, 2), KR.plan('formal', 1, 2)
        self.assertEqual(len(a) + len(b), 22)
        self.assertFalse({u['key'] for u in a} & {u['key'] for u in b})
        self.assertEqual([u['base_id'] for u in KR.plan('preflight', 0, 1)], ['RD01'])
        self.assertEqual(KR.PER_PAIR, 16)


if __name__ == '__main__':
    unittest.main()
