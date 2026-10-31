"""CPU tests on a tiny randomly initialised Qwen3.5 (8 layers; needle at layer 0; split after layer 4; G = (5, 6),
deep full attention (7,)). A tiny bridge run provides the 'old' caches; its tensors go through a torch.save/load
(weights_only=True) round trip like the real assets."""
import copy
import importlib.util
import io
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / 'early-input-control-v1-2026-10-29'))
import combo as CB  # noqa: E402
import combo_analysis as AN  # noqa: E402
import stage0_offline as S0  # noqa: E402

B, F, L, T1 = CB.B, CB.F, CB.L, CB.T1
_spec = importlib.util.spec_from_file_location('cfm_combo_t2', T1.STAGE2 / 'test_stage2.py')
T2 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(T2)
TOKENS = list(T2.STOP) + [3, 5]

PROMPT = [9, 12, 20, 33, 41, 8, 17, 26, 30, 11, 14, 22]
LABELS = ['head'] * 2 + ['fact'] * 4 + ['question'] * 3 + ['instruction'] + ['tail'] + ['last']
NEEDLE = {'id': 'n0', 'kind': 'native', 'layer': 0, 'channel': 7, 'dose': 1.0}


def roundtrip(t):
    import torch
    buf = io.BytesIO()
    torch.save(t, buf)
    buf.seek(0)
    return torch.load(buf, map_location='cpu', weights_only=True)


class Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = T2.tiny()
        cls.engine = T2.fake_engine(cls.model)
        cls.types = L.layer_types(cls.model)
        cls.rec_old, t = B.run_item(cls.engine, T2.REF, PROMPT, LABELS, 'tiny', TOKENS, n=8, split=5, needle=NEEDLE)
        cls.old = roundtrip(t)
        cls.body, cls.tensors = CB.run_item(cls.engine, T2.REF, PROMPT, LABELS, 'tiny', TOKENS, cls.old, cls.rec_old,
                                            n=8, split=5, preflight_extras=True)


class ComboTests(Base):
    def test_cells_and_counts(self):
        cells = CB.unique_cells()
        self.assertEqual(len(cells), 22)
        self.assertEqual(sum(1 for c in cells if len(set(c)) == 1), 4)
        self.assertEqual(self.body['counts'], {'prefixes': 4, 'scores': 34})
        CB.check_limits(self.body['counts'], 'preflight')
        CB.check_limits({'prefixes': 3 * 12, 'scores': 25 * 12}, 'formal')
        with self.assertRaises(AssertionError):
            CB.check_limits({'prefixes': 36, 'scores': 301}, 'formal')

    def test_gates(self):
        for g in ('stage_B_formation', 'groups_cover_deep', 'stage_A_scoring', 'preflight_inert'):
            self.assertIn(g, self.body['gates'])

    def test_complement_identity(self):
        for pair in CB.PAIRS:
            for m in CB.subsets():
                self.assertEqual(CB.assignment(pair, m), CB.assignment((pair[1], pair[0]), frozenset(CB.GROUPS) - m))

    def test_cells_not_trivial(self):
        s = self.body['scores']
        hashes = {k: v['logits_sha256'] for k, v in s.items() if not k.startswith('B:')}
        self.assertEqual(len(set(hashes.values())), 22)
        self.assertNotEqual(s['B:CR0']['logits_sha256'], s['B:C']['logits_sha256'])
        self.assertNotEqual(s['B:CR0']['logits_sha256'], s['B:CR1']['logits_sha256'])

    def test_decomposition_on_record(self):
        fr = AN.fact_readout(self.body, [3], stop=(5, 5))
        for p in AN.PAIRS:
            for met in ('D', 'D_fix'):
                for base in ('decomp_base_a', 'decomp_base_b'):
                    self.assertLess(abs(fr['pairs'][p][met][base]['identity_residual']), 1e-9)
        # C|T and C|CT share the C endpoint
        self.assertEqual(fr['pairs']['C|T']['D']['d']['0'], fr['pairs']['C|CT']['D']['d']['0'])
        prof = fr['profile_CT_vs_T']['D']
        small = min(abs(fr['pairs'][p]['D']['delta']) for p in ('C|CT', 'C|T')) < AN.SHOW_MIN
        self.assertEqual(prof.get('status') == 'delta_too_small', small)   # display rule follows |Delta|

    def test_displacement_record(self):
        for k in ('CR0', 'CR1'):
            for i, d in self.body['stage_B']['displacement'][k].items():
                self.assertAlmostEqual(d['actual_norm_mean'], d['target_norm_mean'], places=3)

    def test_conv_slot_consumption(self):
        """Single scoring step reads the 3 most recent conv slots: changing the oldest slot is inert, slot 1 is not."""
        import torch
        tmpl, _ = L._clean_cache(self.engine, PROMPT[:-1])
        cell = CB.build(tmpl, self.old, ('T', 'T', 'T'), self.types, 5, torch.device('cpu'))
        base, _ = F.score(self.engine, cell, PROMPT[-1], len(PROMPT), keep_logits=False)
        for slot, inert in ((0, True), (1, False)):
            c = copy.deepcopy(cell)
            cs = L._get(c.layers[5], 'conv_states').clone()
            cs[..., slot] += 3.0
            L._set(c.layers[5], 'conv_states', cs)
            r, _ = F.score(self.engine, c, PROMPT[-1], len(PROMPT), keep_logits=False)
            self.assertEqual(r['logits_sha256'] == base['logits_sha256'], inert, slot)

    def test_stage0_offline(self):
        res = S0.analyse_tensor(self.old, self.rec_old, range(5, 8))
        self.assertEqual(set(res), {f'{j}|{r}' for j, r in S0.J_PAIRS})
        for v in res.values():
            self.assertEqual(set(v['G']), {'5', '6'})
            self.assertGreater(v['G']['5']['d_old'], 0)


class PlanTests(unittest.TestCase):
    def test_assets_and_plans(self):
        assets = CB.bridge_assets()
        self.assertEqual(set(assets), {r['id'] for r in CB.items()})
        self.assertEqual(len(CB.plan('formal', 0, 2) + CB.plan('formal', 1, 2)), 12)
        self.assertEqual([u['key'] for u in CB.plan('preflight', 0, 1)], [CB.PREFLIGHT_ITEM])

    def test_frozen_paths_exist(self):
        self.assertEqual([str(p) for p in CB.frozen_paths() if not p.exists()], [])

    def test_analysis_selftest(self):
        self.assertEqual(AN.selftest()['status'], 'passed')


if __name__ == '__main__':
    unittest.main()
