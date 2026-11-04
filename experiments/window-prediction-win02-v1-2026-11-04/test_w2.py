"""WIN-02 CPU tests (no model), including the 6.2 rehearsal: every label is reachable and every criterion can fail.
python -m unittest test_w2 -v   (server .venv-bench, CPU)"""
import random
import unittest

import w2_core as W
import w2_analysis as A
import w2_reading as RD


def synth(n_scen=6, per=8):
    units = [f's{s}u{i}' for s in range(n_scen) for i in range(per)]
    return units, {u: u.split('u')[0] for u in units}


UNITS, SCEN = synth()


def ys(frac, offset=0):
    k = round(frac * 8)
    return {u: int((int(u.split('u')[1]) + offset) % 8 < k) for u in UNITS}


class TestDirectional(unittest.TestCase):
    def d(self, vals):
        return W.describe(vals, UNITS, SCEN, W.boot_index(UNITS, SCEN))

    def test_labels(self):
        self.assertEqual(W.directional_label(self.d(ys(0.5)), +1), 'holds')
        self.assertEqual(W.directional_label(self.d({u: -v for u, v in ys(0.5).items()}), +1), 'reverse')
        self.assertEqual(W.directional_label(self.d({u: -v for u, v in ys(0.5).items()}), -1), 'holds')
        self.assertEqual(W.directional_label(self.d({u: 0 for u in UNITS}), +1), 'no_detectable_difference')
        rng = random.Random(5)
        self.assertEqual(W.directional_label(self.d({u: rng.choice([-1, 0, 0, 1, 1]) for u in UNITS}), +1), 'indeterminate')


class TestStops(unittest.TestCase):
    def stops(self, pre, allw, post, r=0):
        st = {}
        for w, n in (('W_pre', pre), ('W_all', allw), ('W_post', post)):
            st[('fact', 'X', w, 'T')] = n
            st[('fact', 'X', w, 'R_all')] = r
        return st

    def test_p1(self):
        self.assertEqual(W.p1(self.stops(0, 48, 40), 'fact', 'X')['label'], 'holds')
        self.assertEqual(W.p1(self.stops(30, 48, 40), 'fact', 'X')['label'], 'reverse')
        self.assertEqual(W.p1(self.stops(6, 48, 40), 'fact', 'X')['label'], 'indeterminate')
        self.assertEqual(W.p1(self.stops(0, 3, 5), 'fact', 'X')['label'], 'no_information')

    def test_p2(self):
        out = W.p2(self.stops(0, 48, 40, r=1), 'fact', 'X')
        self.assertEqual({w: v['label'] for w, v in out.items()}, {'W_all': 'holds', 'W_post': 'holds'})
        out = W.p2(self.stops(0, 48, 40, r=20), 'fact', 'X')
        self.assertEqual(out['W_all']['label'], 'reverse')
        self.assertEqual(W.p2(self.stops(0, 3, 3), 'fact', 'X')['label'], 'not_applicable')


class TestRelationM(unittest.TestCase):
    def test_positive_holds(self):
        t = {u: 0 for u in UNITS}
        r = ys(0.5)                        # R_all rescues half
        rk = {u: 1 for u in UNITS}         # adding KV_pre rescues the rest, breaks none
        m = W.relation_m(t, r, rk, UNITS, SCEN)
        self.assertEqual((m['U_plus'], m['U_minus']), (24, 24))
        self.assertEqual(m['positive']['label'], 'holds')
        self.assertFalse(m['break']['counter_example'])
        self.assertEqual(m['label'], 'holds')
        self.assertEqual(len(m['transitions']), 48)

    def test_positive_fails(self):
        t, r = {u: 0 for u in UNITS}, ys(0.5)
        m = W.relation_m(t, r, dict(r), UNITS, SCEN)    # no extra rescue
        self.assertEqual(m['positive']['label'], 'no_detectable_difference')

    def test_ceiling_and_break(self):
        t = {u: 0 for u in UNITS}
        r = ys(0.875)                      # R_all rescues 42/48 -> U+ = 6 < 10: ceiling
        m = W.relation_m(t, r, dict(r), UNITS, SCEN)
        self.assertEqual(m['positive']['label'], 'ceiling')
        self.assertEqual(m['label'], 'ceiling')
        rk = {u: (0 if r[u] == 1 and int(u.split('u')[1]) < 3 else r[u]) for u in UNITS}   # breaks ~18 of 42
        m = W.relation_m(t, r, rk, UNITS, SCEN)
        self.assertTrue(m['break']['counter_example'])
        self.assertEqual(m['label'], 'counter_example')

    def test_not_applicable(self):
        m = W.relation_m({u: 1 for u in UNITS}, {u: 1 for u in UNITS}, {u: 1 for u in UNITS}, UNITS, SCEN)
        self.assertEqual(m['label'], 'not_applicable')

    def test_break_denominator_includes_T_correct(self):
        t = ys(0.5)                        # half correct under T already
        r = {u: 1 for u in UNITS}
        rk = {u: 0 if t[u] == 1 else 1 for u in UNITS}   # breaks only inputs that T had right
        m = W.relation_m(t, r, rk, UNITS, SCEN)
        self.assertEqual(m['U_minus'], 48)
        self.assertTrue(m['break']['counter_example'])


class TestP4P5(unittest.TestCase):
    def test_p4(self):
        t = {u: 0 for u in UNITS}
        self.assertEqual(W.p4(t, {u: 1 for u in UNITS}, ys(0.25), UNITS, SCEN)['label'], 'holds')
        self.assertEqual(W.p4(t, ys(0.25), {u: 1 for u in UNITS}, UNITS, SCEN)['label'], 'reverse')
        self.assertEqual(W.p4({u: 1 for u in UNITS}, t, t, UNITS, SCEN)['label'], 'not_applicable')

    def test_p5(self):
        z, one = {u: 0 for u in UNITS}, {u: 1 for u in UNITS}
        cells = {('fact', W.RANDOM, 'W_post', 'T'): z, ('fact', W.RANDOM, 'W_post', 'R_all'): one,
                 ('fact', W.RANDOM, 'W_all', 'T'): z, ('fact', W.RANDOM, 'W_all', 'R_all'): ys(0.25)}
        self.assertEqual(W.p5(cells, 'fact', UNITS, SCEN)['label'], 'holds')
        cells[('fact', W.RANDOM, 'W_post', 'R_all')], cells[('fact', W.RANDOM, 'W_all', 'R_all')] = ys(0.25), one
        self.assertEqual(W.p5(cells, 'fact', UNITS, SCEN)['label'], 'reverse')
        cells[('fact', W.RANDOM, 'W_post', 'T')] = one
        self.assertEqual(W.p5(cells, 'fact', UNITS, SCEN)['label'], 'not_applicable')


class TestNode(unittest.TestCase):
    def cell(self, pos, counter=False):
        return {'label': 'counter_example' if counter else pos, 'positive': {'label': pos}}

    def test_branches(self):
        good = {i: self.cell('holds') for i in range(4)}
        good.update({i: {'label': 'not_applicable'} for i in range(4, 8)})
        self.assertEqual(W.node(good)['branch'], 'supported_in_these_conditions')
        few = {0: self.cell('holds'), 1: self.cell('holds'), 2: self.cell('ceiling'), 3: {'label': 'not_applicable'}}
        self.assertEqual(W.node(few)['branch'], 'mostly_untestable')
        fork = dict(good)
        fork[5] = self.cell('ceiling', counter=True)
        self.assertEqual(W.node(fork)['branch'], 'fork')
        weak = {i: self.cell('indeterminate') for i in range(5)}
        weak[0] = self.cell('holds')
        self.assertEqual(W.node(weak)['branch'], 'insufficient')
        mixed = {i: self.cell('holds') for i in range(3)}
        mixed.update({i: self.cell('no_detectable_difference') for i in range(3, 5)})
        self.assertEqual(W.node(mixed)['branch'], 'mixed')


def fake_records():
    recs = []
    for s in range(3):
        versions = {}
        for v in ('f0', 'f1'):
            u = f'F{s}-{v}'
            res = {'C': {'answer_text': f'{u}:follows_fact', 'first_step_stop': False}}
            for d in W.NEEDLES:
                res[d] = {}
                for w in W.WINDOWS:
                    arms = W.ARMS + ((W.ATTR_ARM,) if w == 'W_all' else ())
                    res[d][w] = {a: {'answer_text': f'{u}:{"not_delivered" if a == "T" else "follows_fact"}', 'first_step_stop': a == 'T' and w != 'W_pre'} for a in arms}
            versions[v] = {'item_id': u, 'results': res}
        recs.append({'task': 'fact', 'unit': {'base_id': f'F{s}', 'panel': 'p'}, 'versions': versions})
    for s in range(3):
        for i in range(4):
            res = {'C': {'Y': 1}}
            for d in W.NEEDLES:
                res[d] = {w: {a: {'Y': int(a != 'T'), 'first_stop': False, 'cat': 'x'} for a in W.ARMS + ((W.ATTR_ARM,) if w == 'W_all' else ())} for w in W.WINDOWS}
            recs.append({'task': 'code', 'unit': {'item_id': f'C{s}-{i}'}, 'scenario': f'N{s}', 'results': res})
    return recs


def labels_for(recs):
    out = {}
    for r in recs:
        if r['task'] == 'fact':
            for v in ('f0', 'f1'):
                ver = r['versions'][v]
                ts = [ver['results']['C']['answer_text']] + [x['answer_text'] for d in W.NEEDLES for w in W.WINDOWS for x in ver['results'][d][w].values()]
                for t in ts:
                    out[A.text_key(ver['item_id'], t)] = t.split(':')[1]
    return out


class TestAnalysis(unittest.TestCase):
    def test_end_to_end(self):
        recs = fake_records()
        out = A.analyse(recs, labels_for(recs))
        self.assertEqual(out['cells']['fact|C']['correct'], 6)
        self.assertEqual(set(out['P3_M']), {f'{t}|{d}' for t in W.TASKS for d in W.NEEDLES})
        self.assertIn('branch', out['node_M'])
        self.assertIn('P1', out['evidence'])

    def test_missing_label(self):
        recs = fake_records()
        lab = labels_for(recs)
        lab.pop(next(iter(lab)))
        with self.assertRaises(AssertionError):
            A.analyse(recs, lab)

    def test_reading_collect(self):
        rows = RD.collect(fake_records())
        reuse = [r for r in rows if r[4] is not None]
        self.assertEqual(len(reuse), 6 * (1 + 4 * 3))          # C + 4 bridged arms x 3 native needles (R0 excluded)
        self.assertEqual(len(rows), 6 * (1 + 4 * (3 * 4 + 1)))


class TestPlan(unittest.TestCase):
    def test_units(self):
        import w2_run as WR
        self.assertEqual(WR.PER_ITEM, 53)
        a, b = WR.plan('formal', 0, 2), WR.plan('formal', 1, 2)
        self.assertEqual(len(a) + len(b), 72)
        self.assertFalse({u['key'] for u in a} & {u['key'] for u in b})
        self.assertEqual([u['task'] for u in WR.plan('preflight', 0, 1)], ['fact', 'code', 'code'])
        self.assertEqual(WR.needle_condition('N_L03_C7666_D-1', 'code')['channel'], 7666)


if __name__ == '__main__':
    unittest.main()
