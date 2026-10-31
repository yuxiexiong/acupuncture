"""CPU tests on a tiny randomly initialised Qwen3.5 (8 layers, needle at layer 1); no checkpoint is loaded."""
import importlib.util
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / 'early-input-control-v1-2026-10-29'))
import s3_intervene as S  # noqa: E402
import s3_analysis as AN  # noqa: E402

T1, L, S2T = S.T1, S.L, S.S2T
_spec = importlib.util.spec_from_file_location('cfm_s3_t2', T1.STAGE2 / 'test_stage2.py')
T2 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(T2)
import torch  # noqa: E402

PROMPT = [9, 12, 20, 33, 41, 8, 17, 26, 30, 11, 14, 22]
CANDS = [[19, 23, 31], [19, 24, 7, 40]]
LABELS = ['head'] * 2 + ['fact'] * 4 + ['question'] * 3 + ['instruction'] + ['tail'] + ['last']
CLEAN = {'id': 'clean', 'kind': 'clean', 'dose': 0.0}
NEEDLE = {'id': 'n1', 'kind': 'native', 'layer': 1, 'channel': 7, 'dose': 1.0}
S.NEEDLE_LAYER['tiny'] = 1


class Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = T2.tiny()
        cls.engine = T2.fake_engine(cls.model)
        cls.lay = S.layout(cls.model)
        cls.layers = tuple(range(2, 8))
        cls.refs = {}
        for arm in ('00', '10', '01', '11'):
            mask = None if arm == '00' else S2T.arm_mask(arm, LABELS)
            iv = S.Intervener(cls.model, cls.layers, capture=True)
            res, cache = S.run_once(cls.engine, CLEAN if arm == '00' else NEEDLE, mask, T2.REF, PROMPT, CANDS, iv)
            cls.refs[arm] = {'result': res, 'cache': cache, 'prefix': iv.store['prefix'], 'post': S.split_post(iv.store)}

    def cell_run(self, cell, window='E'):
        donor, _ = S.WINDOWS[window]
        rows = S.positions(window, LABELS)
        ops = S.build_prefix_ops(cell, {'donor': self.refs[donor]['prefix'], 'T': self.refs['11']['prefix']}, self.lay, self.layers, rows, 7)
        iv = S.Intervener(self.model, self.layers, ops=ops)
        res, cache = S.run_once(self.engine, NEEDLE, S2T.arm_mask('11', LABELS), T2.REF, PROMPT, CANDS, iv)
        return res, cache, iv

    def same(self, a, b):
        return (a['prefix_manifest'] == b['prefix_manifest'] and a['first_step']['logits_sha256'] == b['first_step']['logits_sha256']
                and [c['token_logprobs'] for c in a['candidates']] == [c['token_logprobs'] for c in b['candidates']])


class InterventionTests(Base):
    def test_hooks_inert(self):
        iv = S.Intervener(self.model, self.layers)
        res, _ = S.run_once(self.engine, NEEDLE, S2T.arm_mask('11', LABELS), T2.REF, PROMPT, CANDS, iv)
        self.assertTrue(self.same(res, self.refs['11']['result']))
        plain, _ = S.run_once(self.engine, NEEDLE, S2T.arm_mask('11', LABELS), T2.REF, PROMPT, CANDS)
        self.assertTrue(self.same(plain, self.refs['11']['result']))
        for m in self.model.modules():
            self.assertFalse(m._forward_hooks or m._forward_pre_hooks)

    def test_completeness_E_equals_01(self):
        res, _, iv = self.cell_run({'set': {g: 'donor' for g in S.GROUPS}}, 'E')
        self.assertTrue(self.same(res, self.refs['01']['result']))
        self.assertTrue(iv.applied)

    def test_completeness_L_equals_10(self):
        res, _, _ = self.cell_run({'set': {g: 'donor' for g in S.GROUPS}}, 'L')
        self.assertTrue(self.same(res, self.refs['10']['result']))

    def test_incomplete_sets_do_not_reproduce(self):
        for drop in S.GROUPS:
            res, _, _ = self.cell_run({'set': {g: 'donor' for g in S.GROUPS if g != drop}}, 'E')
            self.assertNotEqual(res['prefix_manifest'], self.refs['01']['result']['prefix_manifest'], drop)

    def test_keep_all_T_equals_11(self):
        res, _, _ = self.cell_run({'set': {g: 'T' for g in S.GROUPS}}, 'E')
        self.assertTrue(self.same(res, self.refs['11']['result']))

    def test_remove_changes_result(self):
        res, _, _ = self.cell_run({'set': {'V': 'donor'}}, 'E')
        self.assertNotEqual(res['prefix_manifest'], self.refs['11']['result']['prefix_manifest'])

    def test_scope_union_equals_complete(self):
        org = S.origin_layers(self.lay, 1)
        self.assertEqual(org, (2, 3))
        res, _, _ = self.cell_run({'set': {g: 'donor' for g in S.GROUPS}, 'layers': self.layers}, 'L')
        self.assertTrue(self.same(res, self.refs['10']['result']))

    def test_random_null_magnitude(self):
        rows = S.positions('E', LABELS)
        refs = {'donor': self.refs['00']['prefix'], 'T': self.refs['11']['prefix']}
        cell = {'set': {'K': 'donor'}, 'null': 'random', 'null_groups': ('K',)}
        ops = S.build_prefix_ops(cell, refs, self.lay, self.layers, rows, 3)
        layer = 4
        parts = [ops[('prefix', layer, 'qkv')][0][3], ops[('prefix', layer, 'b')][0][3]]
        got = torch.cat(parts, -1).norm(dim=-1)
        kd = self.lay['kd']
        idx = torch.tensor(rows)
        want = torch.cat([(refs['donor'][(layer, 'qkv')][idx, kd:2 * kd].float() - refs['T'][(layer, 'qkv')][idx, kd:2 * kd].float()),
                          (refs['donor'][(layer, 'b')][idx].float() - refs['T'][(layer, 'b')][idx].float())], -1).norm(dim=-1)
        self.assertTrue(torch.allclose(got, want, atol=1e-5))
        self.assertTrue(all(o[0] == 'offset' for o in ops[('prefix', layer, 'qkv')]))

    def test_perm_null_is_derangement(self):
        p = S.derangement(6, torch.Generator().manual_seed(1))
        self.assertTrue(bool((p != torch.arange(6)).all()))


class PostTests(Base):
    def post_run(self, donor_arm, factors, null=False):
        ops = S.build_post_ops(factors, self.refs[donor_arm]['post'], self.refs['11']['post'], self.lay, self.layers, 5, null=null)
        iv = S.Intervener(self.model, self.layers, ops=ops)
        mtau = __import__('copy').deepcopy(self.refs['11']['cache'])
        res, _ = S.run_once(self.engine, NEEDLE, S2T.arm_mask('11', LABELS), T2.REF, PROMPT, CANDS, iv, mtau=mtau)
        return res, iv

    def test_self_donor_is_identity(self):
        res, iv = self.post_run('11', ('Wr', 'Rd'))
        self.assertTrue(self.same(res, self.refs['11']['result']))
        self.assertTrue(any(k[0] == 'post' and k[2].startswith('rule:') for k in iv.applied))
        self.assertTrue(any(k[0] == 'post' and k[2] in ('q', 'k', 'v') for k in iv.applied))

    def test_clean_donor_changes(self):
        for f in (('Wr',), ('Rd',), ('Wr', 'Rd')):
            res, _ = self.post_run('00', f)
            self.assertNotEqual(res['first_step']['logits_sha256'], self.refs['11']['result']['first_step']['logits_sha256'], f)
            self.assertEqual(res['prefix_manifest'], self.refs['11']['result']['prefix_manifest'])

    def test_post_null_runs(self):
        res, iv = self.post_run('00', ('Wr', 'Rd'), null=True)
        self.assertTrue(iv.applied)

    def test_capture_keys(self):
        post = self.refs['00']['post']
        self.assertIn(('last',), post)
        self.assertIn(('cand', 1, 2), post)
        self.assertIn((4, 'rule:beta'), post[('last',)])
        self.assertIn((3, 'q'), post[('last',)])


class PlanTests(unittest.TestCase):
    def test_real_layout(self):
        lay = {'types': list(T2.REAL_TYPES), 'kd': 2048, 'vd': 4096}
        self.assertEqual(S.origin_layers(lay, 0), (1, 2, 3))
        self.assertEqual(S.origin_layers(lay, 12), (13, 14, 15))
        slots = [s for g in S.GROUPS for s in S.group_slots(g, lay, 16)]
        cols = sorted(c for m, c in slots if m == 'qkv')
        self.assertEqual(cols, [(0, 2048), (2048, 4096), (4096, 8192)])
        self.assertEqual(sorted(m for m, _ in slots if m != 'qkv'), ['a', 'b'])
        self.assertEqual(sorted(m for g in S.GROUPS for m, _ in S.group_slots(g, lay, 19)), ['k', 'v'])

    def test_cells(self):
        lay = {'types': list(T2.REAL_TYPES), 'kd': 2048, 'vd': 4096}
        for a in S.ANCHORS:
            cells = S.cells_for(a, lay)
            self.assertEqual(len(cells), 130)
            names = {c['name'] for c in cells}
            self.assertTrue(set(S.PREFLIGHT_CELLS) <= names)
            self.assertEqual(sum(1 for c in cells if c['family'] == 'post'), 10)

    def test_plans(self):
        units = [u for w in range(8) for u in S.plan('formal', w, 8)]
        self.assertEqual(len(units), 24)
        self.assertEqual(len({u['key'] for u in units}), 24)
        self.assertEqual(len(S.plan('preflight', 0, 1)), 2)

    def test_frozen_paths_exist(self):
        missing = [str(p) for p in S.frozen_paths() if not p.exists()]
        self.assertEqual(missing, [])

    def test_analysis_selftest(self):
        self.assertEqual(AN.selftest()['status'], 'passed')


if __name__ == '__main__':
    unittest.main()
