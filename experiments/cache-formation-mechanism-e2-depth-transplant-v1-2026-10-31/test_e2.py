"""CPU tests on a tiny randomly initialised Qwen3.5 (8 layers; needles at layer 1 and layer 4, split after layer 4)."""
import importlib.util
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / 'early-input-control-v1-2026-10-29'))
import e2_transplant as E  # noqa: E402
import e2_analysis as AN  # noqa: E402

S3, T1, L = E.S3, E.T1, E.L
_spec = importlib.util.spec_from_file_location('cfm_e2_t2', T1.STAGE2 / 'test_stage2.py')
T2 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(T2)

PROMPT = [9, 12, 20, 33, 41, 8, 17, 26, 30, 11, 14, 22]
CANDS = [[19, 23, 31], [19, 24, 7, 40]]
LABELS = ['head'] * 2 + ['fact'] * 4 + ['question'] * 3 + ['instruction'] + ['tail'] + ['last']
CONDS = {'00': {'id': 'clean', 'kind': 'clean', 'dose': 0.0},
         E.A0: {'id': 'n1', 'kind': 'native', 'layer': 1, 'channel': 7, 'dose': 1.0},
         E.A12: {'id': 'n4', 'kind': 'native', 'layer': 4, 'channel': 7, 'dose': 1.0}}


class Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = T2.tiny()
        cls.engine = T2.fake_engine(cls.model)
        cls.types = L.layer_types(cls.model)
        cls.body = E.run_item(cls.engine, {'id': 'tiny'}, None, T2.REF, PROMPT, CANDS, LABELS, None, n=8, split=5, needle=CONDS)


class TransplantTests(Base):
    def test_run_item_gates(self):
        self.assertIn('completeness', self.body['gates'])
        self.assertIn('structure', self.body['gates'])
        self.assertEqual(set(self.body['cells']), {'a', 'd', 'b', 'gate-00', 'gate-L12'})

    def test_gate_equalities(self):
        c, n = self.body['cells'], self.body['natives']
        self.assertTrue(E.same_outputs(c['gate-00'], n['00']))
        self.assertTrue(E.same_outputs(c['gate-L12'], n['L12-01']))

    def test_cells_are_not_trivial(self):
        c, n = self.body['cells'], self.body['natives']
        for name in ('a', 'd', 'b'):
            self.assertNotEqual(c[name]['first_step']['logits_sha256'], n['L0-01']['first_step']['logits_sha256'], name)
            self.assertNotEqual(c[name]['first_step']['logits_sha256'], n['00']['first_step']['logits_sha256'], name)

    def test_transplant_and_layer_checks(self):
        _, c00 = S3.run_once(self.engine, CONDS['00'], None, T2.REF, PROMPT, CANDS)
        _, c01 = S3.run_once(self.engine, CONDS[E.A0], E.S2T.arm_mask('01', LABELS), T2.REF, PROMPT, CANDS)
        _, c12 = S3.run_once(self.engine, CONDS[E.A12], E.S2T.arm_mask('01', LABELS), T2.REF, PROMPT, CANDS)
        self.assertTrue(E.layers_equal(c12, c00, range(0, 5), self.types))
        self.assertFalse(E.layers_equal(c12, c00, range(5, 8), self.types))
        self.assertFalse(E.layers_equal(c01, c00, range(2, 5), self.types))
        full = E.transplant(c01, c00, range(8), self.types)
        self.assertEqual(E.ST2.cache_manifest(full, self.types), E.ST2.cache_manifest(c00, self.types))
        part = E.transplant(c01, c00, range(0, 5), self.types)
        self.assertTrue(E.layers_equal(part, c01, range(5, 8), self.types))
        self.assertTrue(E.layers_equal(part, c00, range(0, 5), self.types))
        self.assertEqual(E.ST2.cache_manifest(c01, self.types), E.ST2.cache_manifest(c01, self.types))

    def test_real_split(self):
        types = list(T2.REAL_TYPES)
        self.assertEqual(E.shallow(), tuple(range(13)))
        self.assertEqual(E.deep(), tuple(range(13, 32)))
        self.assertEqual(types[12], 'linear_attention')
        self.assertEqual(len(E.cells()), 5)


class PlanTests(unittest.TestCase):
    def test_items_and_data(self):
        rows = E.items()
        self.assertEqual(len(rows), 12)
        seg = E.exp.read(E.SEGMENTS)['items']
        ref = E.exp.read(E.REFERENCE)
        self.assertEqual(set(seg), {r['id'] for r in rows})
        for r in rows:
            self.assertEqual(seg[r['id']]['prompt_token_sha256'], ref['rows'][f'{r["id"]}__clean']['prompt_token_sha256'])
            b = E.S2T.boundary_b(seg[r['id']]['labels'])
            self.assertEqual(seg[r['id']]['labels'][b + 1], 'question')
        self.assertEqual(sum(ref['rows'][f'{r["id"]}__{E.A0}']['first_step_eos'] for r in rows), 12)

    def test_plans(self):
        units = E.plan('formal', 0, 2) + E.plan('formal', 1, 2)
        self.assertEqual(len(units), 12)
        self.assertEqual(len({u['key'] for u in units}), 12)
        self.assertEqual([u['key'] for u in E.plan('preflight', 0, 1)], [E.PREFLIGHT_ITEM])

    def test_frozen_paths_exist(self):
        self.assertEqual([str(p) for p in E.frozen_paths() if not p.exists()], [])

    def test_analysis_selftest(self):
        self.assertEqual(AN.selftest()['status'], 'passed')


if __name__ == '__main__':
    unittest.main()
