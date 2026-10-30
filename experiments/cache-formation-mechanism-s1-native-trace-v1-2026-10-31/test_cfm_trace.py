"""CPU tests on a tiny randomly initialised Qwen3.5 (layers 4-6 linear + 7 full stand in for L16-18 + L19); no checkpoint."""
import copy
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / 'early-input-control-v1-2026-10-29'))
import cfm_trace as TR  # noqa: E402
import account as A  # noqa: E402

L, S2 = TR.L, TR.S2
_spec = __import__('importlib.util').util.spec_from_file_location('cfm_t2', TR.STAGE2 / 'test_stage2.py')
T2 = __import__('importlib.util').util.module_from_spec(_spec)
_spec.loader.exec_module(T2)
import torch  # noqa: E402

OBS = (4, 5, 6)
BND = {'L16_in': (4, 'pre'), 'L19_in': (7, 'pre'), 'L19_out': (7, 'post')}
PROMPT = [9, 12, 20, 33, 41, 8, 17, 26, 30, 11, 14, 22]
CANDS = [[19, 23, 31], [19, 24, 7, 40]]
LABELS = ['head'] * 2 + ['fact'] * 4 + ['question'] * 3 + ['instruction'] + ['tail'] + ['last']


def native(layer=1, channel=7, dose=1.0):
    return {'id': f'n{layer}', 'kind': 'native', 'layer': layer, 'channel': channel, 'dose': dose}


CLEAN = {'id': 'clean', 'kind': 'clean', 'dose': 0.0}


class Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = T2.tiny()
        cls.engine = T2.fake_engine(cls.model)
        cls.run_T = TR.trajectory(cls.engine, native(), T2.REF, PROMPT, CANDS, OBS, BND)
        cls.run_C = TR.trajectory(cls.engine, CLEAN, T2.REF, PROMPT, CANDS, OBS, BND)


class RecorderTests(Base):
    def test_inert_against_unrecorded_path(self):
        for cond, (meta, _, _) in ((native(), self.run_T), (CLEAN, self.run_C)):
            self.assertEqual(TR.inertness_gate(self.engine, cond, T2.REF, PROMPT, CANDS, meta), 'passed')

    def test_candidate_scores_equal_stage1_score(self):
        meta, _, cache = self.run_T
        for j, c in enumerate(CANDS):
            s = L.score(self.model, cache, PROMPT[-1], len(PROMPT), c)
            self.assertEqual(s['token_logprobs'], meta['candidates'][j]['token_logprobs'])

    def test_call_counts(self):
        meta = self.run_T[0]
        fed = sum(c['fed_tokens'] for c in meta['candidates'])
        self.assertTrue(TR.check_calls(meta['recorder_calls'], OBS, fed))
        with self.assertRaises(AssertionError):
            TR.check_calls(meta['recorder_calls'], OBS, fed + 1)

    def test_restores_globals_and_hooks(self):
        qm = TR.qwen_module()
        before = (qm.torch_chunk_gated_delta_rule, qm.torch_recurrent_gated_delta_rule)
        with TR.Recorder(self.model, OBS, BND):
            self.assertIsNot(qm.torch_chunk_gated_delta_rule, before[0])
        self.assertIs(qm.torch_chunk_gated_delta_rule, before[0])
        self.assertIs(qm.torch_recurrent_gated_delta_rule, before[1])
        for m in self.model.modules():
            self.assertFalse(m._forward_hooks or m._forward_pre_hooks, type(m).__name__)

    def test_capture_consistency(self):
        out = TR.capture_consistency(self.engine, self.run_T[1], OBS)
        self.assertEqual(set(out.values()), {'identical'})

    def test_capture_shapes(self):
        tensors = self.run_T[1]
        cap = tensors['prefix']['4']
        n = len(PROMPT) - 1
        self.assertEqual(tuple(cap['q'][0].shape), (n, 2, 8))
        self.assertEqual(tuple(cap['norm_out'][0].shape), (n, 2, 8))
        self.assertEqual(len(tensors['cand1']['4']['q']), len(CANDS[1]) - 1)
        self.assertEqual(tuple(tensors['prefix']['boundary']['L19_out'][0].shape), (n, 32))

    def test_upstream_layers_identical(self):
        mT, mC = self.run_T[0]['prefix_manifest'], self.run_C[0]['prefix_manifest']
        self.assertEqual(mT['0:recurrent_states'], mC['0:recurrent_states'])
        self.assertNotEqual(mT['4:recurrent_states'], mC['4:recurrent_states'])

    def test_needle_only_on_prefix(self):
        meta = self.run_T[0]
        self.assertEqual(meta['needle_positions'], list(range(len(PROMPT) - 1)))
        self.assertEqual(self.run_C[0]['needle_positions'], [])

    def test_kernel_identity_reports_torch_paths(self):
        value = TR.kernel_identity()
        self.assertTrue(all(v['module'].endswith('modeling_qwen3_5') for k, v in value.items() if k != 'packages_present'))


class ReplayTests(Base):
    def reference_row(self):
        meta = self.run_T[0]
        return {'reference_sha256': TR.exp.digest(T2.REF), 'prompt_token_sha256': TR.exp.digest(PROMPT),
                'cache_manifest': copy.deepcopy(meta['prefix_manifest']), 'first_step': copy.deepcopy(meta['first_step']),
                'candidates': [{'text': str(c), 'token_ids': c, 'token_logprobs': list(m['token_logprobs'])}
                               for c, m in zip(CANDS, meta['candidates'])]}

    def test_identical_passes_and_any_difference_fails(self):
        meta = self.run_T[0]
        self.assertEqual(TR.replay_check(meta, self.reference_row(), T2.REF, PROMPT)['candidate_token_logprobs'], 'identical')
        for mutate in (lambda r: r['candidates'][1]['token_logprobs'].__setitem__(2, r['candidates'][1]['token_logprobs'][2] + 1e-12),
                       lambda r: r['first_step'].__setitem__('logits_sha256', '0' * 64),
                       lambda r: r['cache_manifest'].__setitem__('5:conv_states', 'x'),
                       lambda r: r.__setitem__('reference_sha256', 'y')):
            row = self.reference_row()
            mutate(row)
            with self.assertRaises(AssertionError):
                TR.replay_check(meta, row, T2.REF, PROMPT)


class AccountTests(Base):
    def test_reconstruction_gate_on_kernel(self):
        for run in (self.run_T, self.run_C):
            g = A.reconstruction_gate(A.from_capture(run[1], OBS))
            self.assertEqual(g['status'], 'passed', g)
            for row in g['layers'].values():
                self.assertLess(max(row['state_rel'].values()), 1e-5)

    def test_reconstruction_gate_bf16_model(self):
        model = T2.tiny().to(torch.bfloat16)
        eng = T2.fake_engine(model)
        _, tensors, _ = TR.trajectory(eng, native(), T2.REF, PROMPT, CANDS, OBS, BND)
        g = A.reconstruction_gate(A.from_capture(tensors, OBS))
        self.assertEqual(g['status'], 'passed', g)

    def test_pair_identities_and_contraction(self):
        tT, tC = A.from_capture(self.run_T[1], OBS), A.from_capture(self.run_C[1], OBS)
        for layer in OBS:
            rows, heads = A.account_pair(tT, tC, LABELS, layer)
            self.assertEqual(len(rows), len(PROMPT) + sum(len(c) - 1 for c in CANDS))
            for r in rows:
                if r['dS2'] > 0:
                    self.assertLess(r['identity_rel'], 1e-10)
                    for a in A.ACCOUNTS:
                        self.assertLess(r[f'{a}_ZW_plus_ZR_rel_err'], 1e-9)
                    total = sum(r['sym_ip_ZW_seg_dS'].values()) + sum(r['sym_ip_ZR_seg_dS'].values())
                    self.assertAlmostEqual(total / r['dS2'], 1.0, places=9)
                    self.assertAlmostEqual(sum(r['PT_seg_share'].values()), 1.0, places=9)
                if r['do'] > 0:
                    self.assertLess(r['readout_identity_rel'], 1e-10)
                    self.assertLess(r['actual_vs_recon_do_rel'], 1e-3)
                self.assertLessEqual(r['contraction_max'], 1 + 1e-12)
            # Final recurrence state of the accounts equals the kernel state after the last token.
            last = next(r for r in rows if r['path'] == 'main' and r['segment'] == 'last')
            exposed = tT['layers'][str(layer)]['exposed']['last'] - tC['layers'][str(layer)]['exposed']['last']
            self.assertAlmostEqual(last['dS'], float(exposed.norm()), delta=1e-5 * max(1.0, last['dS']))

    def test_clean_vs_clean_is_zero(self):
        tC = A.from_capture(self.run_C[1], OBS)
        rows, _ = A.account_pair(tC, tC, LABELS, 4)
        self.assertTrue(all(r['dS'] == 0 and r['do'] == 0 for r in rows))
        res = A.classify([rows[len(PROMPT) - 1]], [0.0], A.RULES['main'])
        self.assertEqual(res['branch'], 'unresolved')

    def test_selftest(self):
        self.assertEqual(A.selftest()['status'], 'passed')


class PlanTests(unittest.TestCase):
    def test_observed_layers_in_real_layout(self):
        types = T2.REAL_TYPES
        self.assertTrue(all(types[i] == 'linear_attention' for i in TR.OBS_LAYERS))
        self.assertEqual(types[19], 'full_attention')
        self.assertEqual(TR.BOUNDARY, {'L16_in': (16, 'pre'), 'L19_in': (19, 'pre'), 'L19_out': (19, 'post')})

    def test_items_and_conditions(self):
        rows = TR.items()
        self.assertEqual(len(rows), 12)
        self.assertEqual(sorted({r['base_id'] for r in rows}), sorted(TR.BASES))
        self.assertEqual(TR.engine_condition('N_L12_C3621_D-1'), {'id': 'N_L12_C3621_D-1', 'kind': 'native', 'layer': 12, 'channel': 3621, 'dose': -1.0})
        self.assertEqual(TR.engine_condition('N_L00_C4146_D-1')['channel'], 4146)

    def test_plans(self):
        pre = TR.plan('preflight', 0, 1)
        self.assertEqual([s['key'] for s in pre], [f'{TR.PREFLIGHT_ITEM}__{c}' for c in TR.CONDITIONS])
        formal = TR.plan('formal', 0, 2) + TR.plan('formal', 1, 2)
        self.assertEqual(len(formal), 36)
        self.assertEqual(len({s['key'] for s in formal}), 36)
        for w in (0, 1):
            bases = {s['base_id'] for s in TR.plan('formal', w, 2)}
            self.assertEqual(len(bases), 3)
        ref = TR.exp.read(TR.REFERENCE)['rows']
        self.assertEqual({s['key'] for s in formal}, set(ref))

    def test_reference_matches_plan_panel(self):
        ref = TR.exp.read(TR.REFERENCE)
        eos = {c: sum(r['first_step_eos'] for r in ref['rows'].values() if r['condition_id'] == c) for c in TR.CONDITIONS}
        self.assertEqual(eos, {'clean': 0, 'N_L00_C4146_D-1': 12, 'N_L12_C3621_D-1': 0})  # plan §2
        for r in ref['rows'].values():
            self.assertEqual(r['condition'], TR.engine_condition(r['condition_id']))

    def test_segment_rule(self):
        item = next(r for r in TR.items() if r['id'] == 'VAR01-f0-required')
        context = '<|im_start|>user\n' + item['prompt'] + '<|im_end|>\n<|im_start|>assistant\n'
        spans = TR.segment_spans(context, item['prompt'])
        self.assertEqual(context[slice(*spans['fact'])], '车上原有15名乘客，到站时下车4人，又上车3人，途中没有其他人上下。')
        self.assertTrue(context[slice(*spans['question'])].startswith('\n问题：'))
        self.assertTrue(context[slice(*spans['instruction'])].startswith('\n请根据'))
        self.assertEqual(spans['tail'][1], len(context))

    def test_label_tokens_with_char_tokenizer(self):
        class Tok:
            bos_token_id = None
            eos_token_id = 0

            def decode(self, i):
                return '\x00'

            def encode(self, text, **kw):
                return [ord(c) for c in text]

            def __call__(self, text, add_special_tokens=False, return_offsets_mapping=False):
                return {'input_ids': [ord(c) for c in text], 'offset_mapping': [(i, i + 1) for i in range(len(text))]}
        prompt = '甲有3个。\n问题：几个？\n请根据上述信息回答。'
        context = '<u>' + prompt + '</u>'
        lab = TR.label_tokens(Tok(), context, prompt)
        self.assertEqual(lab['labels'][:3], ['head'] * 3)
        self.assertEqual(lab['labels'][3:8], ['fact'] * 5)
        self.assertEqual(lab['labels'][-1], 'last')
        self.assertEqual(lab['labels'][-2], 'tail')

    def test_frozen_paths_exist(self):
        paths = TR.frozen_paths()
        missing = [str(p) for p in paths if not p.exists() and p.name != 'segments-r01.json']
        self.assertEqual(missing, [])
        self.assertIn(TR.PLAN_DOC, paths)
        self.assertIn(TR.STAGE2 / 'stage2.py', paths)


if __name__ == '__main__':
    unittest.main()
