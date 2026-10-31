"""CPU tests on a tiny randomly initialised Qwen3.5 (layers 4-6 linear + 7 full stand in for L16-18 + L19); no checkpoint."""
import copy
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / 'early-input-control-v1-2026-10-29'))
import s2_trace as S  # noqa: E402
import formation as F  # noqa: E402

T1, L, A1 = S.T1, S.L, F.A1
_spec = importlib.util.spec_from_file_location('cfm_s2_t2', T1.STAGE2 / 'test_stage2.py')
T2 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(T2)
import torch  # noqa: E402

OBS = (4, 5, 6)
BND = {'L16_in': (4, 'pre'), 'L19_in': (7, 'pre'), 'L19_out': (7, 'post')}
PROMPT = [9, 12, 20, 33, 41, 8, 17, 26, 30, 11, 14, 22]
CANDS = [[19, 23, 31], [19, 24, 7, 40]]
LABELS = ['head'] * 2 + ['fact'] * 4 + ['question'] * 3 + ['instruction'] + ['tail'] + ['last']
CLEAN = {'id': 'clean', 'kind': 'clean', 'dose': 0.0}


def native(layer=1, channel=7, dose=1.0):
    return {'id': f'n{layer}', 'kind': 'native', 'layer': layer, 'channel': channel, 'dose': dose}


class Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = T2.tiny()
        cls.engine = T2.fake_engine(cls.model)
        cls.b = S.boundary_b(LABELS)
        cls.runs = {}
        for arm in ('00', '10', '01', '11'):
            cond = CLEAN if arm == '00' else native()
            mask = None if arm == '00' else S.arm_mask(arm, LABELS)
            cls.runs[arm] = S.trajectory(cls.engine, cond, mask, T2.REF, PROMPT, CANDS, OBS, BND)


class MaskTests(Base):
    def test_boundary_and_masks(self):
        self.assertEqual(self.b, 5)
        self.assertEqual(S.arm_mask('10', LABELS), [True] * 6 + [False] * 5)
        self.assertEqual(S.arm_mask('01', LABELS), [False] * 6 + [True] * 5)
        self.assertEqual(S.arm_mask('11', LABELS), [True] * 11)
        with self.assertRaises(AssertionError):
            S.boundary_b(['head', 'fact', 'question', 'fact', 'tail', 'last'])

    def test_masked_all_true_equals_s1_path(self):
        s1_meta, s1_tensors, _ = T1.trajectory(self.engine, native(), T2.REF, PROMPT, CANDS, OBS, BND)
        meta = self.runs['11'][0]
        self.assertEqual(meta['prefix_manifest'], s1_meta['prefix_manifest'])
        self.assertEqual(meta['first_step'], s1_meta['first_step'])
        self.assertEqual([c['token_logprobs'] for c in meta['candidates']], [c['token_logprobs'] for c in s1_meta['candidates']])

    def test_needle_audit(self):
        self.assertEqual(self.runs['10'][0]['needle_positions'], list(range(6)))
        self.assertEqual(self.runs['01'][0]['needle_positions'], list(range(6, 11)))
        self.assertEqual(self.runs['00'][0]['needle_positions'], [])
        self.assertNotEqual(self.runs['10'][0]['prefix_manifest'], self.runs['11'][0]['prefix_manifest'])
        self.assertNotEqual(self.runs['01'][0]['prefix_manifest'], self.runs['00'][0]['prefix_manifest'])

    def test_masked_inertness(self):
        for arm in ('10', '01'):
            meta = self.runs[arm][0]
            self.assertEqual(S.masked_inertness(self.engine, native(), S.arm_mask(arm, LABELS), T2.REF, PROMPT, CANDS, meta), 'passed')


class CommonHistoryTests(Base):
    def test_same_start_pairs_certified_bitwise(self):
        for x, y in (('01', '00'), ('11', '10')):
            cert = S.common_history(self.runs[y][1], self.runs[x][1], self.b, OBS)
            self.assertEqual(cert['status'], 'certified_bitwise', (x, y, cert))
            self.assertFalse(all(cert['4']['after_b_identical'].values()))

    def test_different_start_pair_not_certified(self):
        self.assertEqual(S.common_history(self.runs['00'][1], self.runs['10'][1], self.b, OBS)['status'], 'not_certified')

    def test_offline_start_identical(self):
        X, Y = A1.from_capture(self.runs['01'][1], OBS), A1.from_capture(self.runs['00'][1], OBS)
        for layer in OBS:
            rows, start = F.pair_process(X, Y, LABELS, layer, self.b)
            self.assertEqual(start['dS_b'], 0.0)
            self.assertEqual(rows[0]['carry_dS_prev'], 0.0)


class AssetTests(Base):
    def test_mtau_roundtrip(self):
        meta, _, cache = self.runs['10']
        with tempfile.TemporaryDirectory() as d:
            out = S.mtau_roundtrip(self.engine, cache, Path(d) / 'm.pt', PROMPT)
        self.assertTrue(out['reload_first_step_identical'])

    def test_full_cache_contents(self):
        cache = self.runs['11'][2]
        fc = S.full_cache(cache, L.layer_types(self.model))
        self.assertEqual(len(fc['tensors']), 2 * 8)
        self.assertEqual(fc['manifest'], self.runs['11'][0]['prefix_manifest'])

    def test_s1_repeat_check(self):
        meta, tensors, _ = self.runs['11']
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'worker-0' / 'tensors' / 'x.pt'
            sha = T1.save_tensors(p, tensors)
            spec = {'item_id': 'I', 'anchor': 'A', 'arm': '11'}
            recs = {'I__A': {'_dir': str(Path(d) / 'worker-0'), 'tensor_file': 'tensors/x.pt', 'tensor_sha256': sha, 'spec': {'key': 'I__A'}}}
            self.assertEqual(S.s1_repeat_check(spec, tensors, recs)['status'], 'bitwise_identical')
            bad = copy.deepcopy(tensors)
            bad['prefix']['5']['v'][0][3, 0, 0] += 1e-3
            with self.assertRaises(AssertionError):
                S.s1_repeat_check(spec, bad, recs)


class ExecutionPathTests(Base):
    def test_check_limits(self):
        self.assertTrue(S.check_limits({'records': 3, 'prefixes': 3, 'last_reads': 3, 'candidate_reads': 6}, 'preflight'))
        self.assertTrue(S.check_limits({'records': 84, 'prefixes': 84, 'last_reads': 84, 'candidate_reads': 168}, 'formal'))
        with self.assertRaises(AssertionError):
            S.check_limits({'records': 4, 'prefixes': 4, 'last_reads': 3, 'candidate_reads': 6}, 'preflight')

    def test_certify_ready_writes_and_releases(self):
        item = {'id': 'I'}
        with tempfile.TemporaryDirectory() as d:
            out, receipt = Path(d), {'record_hashes': {}}
            kept = {'I__clean__00': self.runs['00'][1]}
            for a in S.ANCHORS:
                for arm in ('10', '01', '11'):
                    kept[f'I__{a}__{arm}'] = self.runs[arm][1]
                    S._certify_ready(out, item, LABELS, kept, receipt, OBS)
            self.assertEqual(len(receipt['record_hashes']), 2 * len(S.ANCHORS))
            self.assertEqual(kept, {})
            for rel in receipt['record_hashes']:
                self.assertEqual(T1.exp.read(out / rel)['status'], 'certified_bitwise')
        with tempfile.TemporaryDirectory() as d:
            bad = {'I__clean__00': self.runs['10'][1], f'I__{S.ANCHORS[0]}__01': self.runs['01'][1]}
            with self.assertRaises(AssertionError):
                S._certify_ready(Path(d), item, LABELS, bad, {'record_hashes': {}}, OBS)


class FormationTests(Base):
    def test_bound_validity_on_kernel(self):
        for arm, run in self.runs.items():
            tr = A1.from_capture(run[1], OBS)
            for layer in OBS:
                v = F.bound_validity(tr, layer)
                self.assertTrue(v['valid'], (arm, layer, v))

    def test_identities_on_real_captures(self):
        caps = {a: A1.from_capture(r[1], OBS) for a, r in self.runs.items()}
        for pname, (x, y, same) in F.PAIRS.items():
            for layer in OBS:
                rows, start = F.pair_process(caps[x], caps[y], LABELS, layer, self.b)
                self.assertEqual(len(rows), (len(PROMPT) - 1 - self.b) + sum(len(c) - 1 for c in CANDS))
                for r in rows:
                    if r['dS'] > 0:
                        self.assertLess(r['HN_sum_rel'], 1e-10)
                        for c in ('b', 'tau'):
                            for bg in F.BACKGROUNDS:
                                if r.get(f'{c}_{bg}'):
                                    self.assertLess(r[f'{c}_{bg}']['sum_rel'], 1e-9)
                    if r['dH'] > 0:
                        self.assertLess(r['dH_identity_rel'], 1e-10)
                    if r['dN'] > 0:
                        self.assertLess(r['dN_identity_rel'], 1e-10)
                    if r['dA_Sbar'] > 0:
                        self.assertLess(r['uH_plus_uN_vs_dA_Sbar_rel'], 1e-10)
                    if r['do'] > 0:
                        self.assertLess(r['readout_identity_rel'], 1e-10)
                c = F.cell_summary(rows, start, same)
                self.assertIn('refutations', c)
                if same:
                    self.assertFalse(c['first_step']['start_resolved'])
            # The final state difference matches the kernel's own post-last states.
            last = next(r for r in rows if r['path'] == 'main' and r['segment'] == 'last')
            kernel = caps[x]['layers'][str(layer)]['exposed']['last'] - caps[y]['layers'][str(layer)]['exposed']['last']
            self.assertAlmostEqual(last['dS'], float(kernel.norm()), delta=1e-5 * max(1.0, last['dS']))

    def test_selftest(self):
        self.assertEqual(F.selftest()['status'], 'passed')


class PlanTests(unittest.TestCase):
    def test_counts(self):
        formal = S.plan('formal', 0, 2) + S.plan('formal', 1, 2)
        self.assertEqual(len(formal), 84)
        self.assertEqual(len({s['key'] for s in formal}), 84)
        self.assertEqual(sum(s['arm'] in ('10', '01') for s in formal), 48)
        self.assertEqual(sum(S.reference_key(s) is not None for s in formal), 36)
        ref = T1.exp.read(T1.REFERENCE)['rows']
        self.assertEqual({S.reference_key(s) for s in formal if S.reference_key(s)}, set(ref))
        pre = S.plan('preflight', 0, 1)
        self.assertEqual([s['key'] for s in pre], [f'{S.PREFLIGHT_ITEM}__clean__00'] + [f'{S.PREFLIGHT_ITEM}__{a}__11' for a in S.ANCHORS])
        for w in (0, 1):
            self.assertEqual(len({s['base_id'] for s in S.plan('formal', w, 2)}), 3)

    def test_real_segments_have_boundary(self):
        seg = T1.exp.read(T1.SEGMENTS)['items']
        for iid, v in seg.items():
            b = S.boundary_b(v['labels'])
            self.assertEqual(v['labels'][b], 'fact')
            self.assertEqual(v['labels'][b + 1], 'question')

    def test_frozen_paths_exist(self):
        paths = S.frozen_paths()
        missing = [str(p) for p in paths if not p.exists()]
        self.assertEqual(missing, [])
        self.assertIn(S.PLAN_DOC, paths)
        self.assertIn(T1.HERE / 'cfm_trace.py', paths)


if __name__ == '__main__':
    unittest.main()
