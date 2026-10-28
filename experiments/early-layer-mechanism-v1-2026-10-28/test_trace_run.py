"""CPU checks for frozen coverage, deterministic preflight and fail-closed gates."""
import copy
from collections import Counter, defaultdict
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import trace_run as run


class SourceChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = run.build_source_inventory()

    def test_exact_scope_and_disjoint_complete_shards(self):
        self.assertEqual(Counter(item['model'] for item in self.rows), {'2b': 616, '4b': 616, '9b': 920})
        self.assertEqual(len({item['trace_id'] for item in self.rows}), 2152)
        for model, end in [('2b', 3), ('4b', 3), ('9b', 5)]:
            shards = [{i['trace_id'] for i in run.split_records(self.rows, model, s)} for s in (0, 1)]
            self.assertFalse(shards[0] & shards[1])
            self.assertEqual(shards[0] | shards[1], {i['trace_id'] for i in self.rows if i['model'] == model})
            by_condition = defaultdict(set)
            for item in (i for i in self.rows if i['model'] == model):
                key = run.identity(item['record'])
                self.assertTrue(key[1] is None or 0 <= key[1] <= end)
                by_condition[key[1:4]].add(key[-1])
                self.assertTrue(item['references'])
            self.assertEqual(len(by_condition), (end + 1) * 19 + 1)
            self.assertTrue(all(q == {f'Q{i:02}' for i in range(1, 9)} for q in by_condition.values()))
        for model, shard in [('llama', 0), ('2b', 2)]:
            with self.assertRaises(AssertionError):
                run.split_records(self.rows, model, shard)

    def test_preflight_is_bounded_distinct_and_deterministic(self):
        total = 0
        for model in run.MODELS:
            for shard in (0, 1):
                cases = run.select_preflight(self.rows, model, shard)
                again = run.select_preflight(list(reversed(self.rows)), model, shard)
                self.assertEqual(cases, again)
                self.assertEqual([c['name'] for c in cases], ['baseline', 'short_eos', 'long_positive', 'negative', 'low_positive', 'zero', 'restored'])
                self.assertEqual(len({c['record']['trace_id'] for c in cases[1:5]}), 4)
                self.assertTrue(all(c['record']['shard'] == shard for c in cases[1:5]))
                self.assertEqual(cases[0]['record']['record']['question_id'], 'Q01')
                self.assertIsNone(cases[0]['record']['record']['layer'])
                self.assertLess(run.identity(cases[3]['record']['record'])[3], 0)
                self.assertTrue(0 < run.identity(cases[4]['record']['record'])[3] < 1)
                self.assertEqual(cases[5]['arm_override'][2], 0)
                self.assertEqual(cases[6]['arm_override'], 'baseline')
                self.assertEqual(cases[0]['record'], cases[5]['record'])
                self.assertEqual(cases[0]['record'], cases[6]['record'])
                pool = run.split_records(self.rows, model, shard)
                lengths = [len(i['record']['output']['token_ids']) for i in pool if i['record']['layer'] is not None]
                self.assertEqual(len(cases[1]['record']['record']['output']['token_ids']), min(lengths))
                total += len(cases)
        self.assertEqual(total, 42)

    def test_conflicting_duplicate_source_is_rejected(self):
        first = copy.deepcopy(self.rows[0]['record'])
        changed = copy.deepcopy(first)
        changed['output']['token_ids'][0] += 1
        with tempfile.TemporaryDirectory() as temporary:
            paths = [Path(temporary) / f'{i}.jsonl' for i in range(3)]
            for path, row in zip(paths, (first, changed, first)):
                path.write_text(json.dumps(row) + '\n')
            contract = run.read(run.ROOT / 'contract.json')
            contract['sources'] = [{'path': str(p), 'sha256': run.sha(p)} for p in paths]
            with patch.object(run, 'read', return_value=contract):
                with self.assertRaisesRegex(AssertionError, 'Conflicting source'):
                    run.build_source_inventory(paths)


class GateChecks(unittest.TestCase):
    def test_authorization_requires_exact_budget_and_clean_cpu_receipt(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'queue_run.py').write_text('frozen queue')
            cpu = dict(status='passed', failures=0, errors=0, skipped=0, freeze_sha256='frozen')
            run.write(root / 'cpu.json', cpu)
            auth = dict(status='authorized', purpose='early_layer_trace_queue', experiment=root.name,
                        user_instruction='Run after tests and predecessor release.', freeze_sha256='frozen',
                        models=list(run.MODELS), maximum_records={'preflight': 42, 'survey': 2152},
                        maximum_generations={'preflight': 114, 'survey': 4304},
                        cpu_test_receipt={'path': 'cpu.json', 'sha256': run.sha(root / 'cpu.json')},
                        queue_sha256=run.sha(root / 'queue_run.py'))
            path = root / 'auth.json'
            run.write(path, auth)
            with patch.object(run, 'ROOT', root), patch.object(run, 'validate_freeze', return_value='frozen'):
                self.assertEqual(run.validate_authorization(path), auth)
                for field, bad in [('maximum_records', {'preflight': 42, 'survey': 2153}), ('freeze_sha256', 'other'), ('models', ['4b'])]:
                    broken = dict(auth, **{field: bad})
                    run.write(path, broken)
                    with self.assertRaises(AssertionError):
                        run.validate_authorization(path)
                for field in ('failures', 'errors', 'skipped'):
                    run.write(root / 'cpu.json', dict(cpu, **{field: 1}))
                    auth['cpu_test_receipt']['sha256'] = run.sha(root / 'cpu.json')
                    run.write(path, auth)
                    with self.assertRaises(AssertionError):
                        run.validate_authorization(path)

    def test_freeze_rejects_changed_input(self):
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            root = repo / 'experiment'
            root.mkdir()
            (root / 'source').write_text('original')
            run.write(root / 'freeze.json', {'experiment': root.name, 'files': {'experiment/source': run.sha(root / 'source')}})
            with patch.object(run, 'ROOT', root), patch.object(run, 'REPO', repo):
                run.validate_freeze()
                (root / 'source').write_text('modified')
                with self.assertRaisesRegex(AssertionError, 'Frozen file changed'):
                    run.validate_freeze()

    def test_failed_worker_and_incomplete_three_model_gate_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            run.write(root / 'receipt.json', {'status': 'failed', 'checks_passed': False})
            with self.assertRaises(AssertionError):
                run.verify_worker(root, 'preflight', '4b', 0)
            run.write(root / 'preflight-accepted.json', {'status': 'passed', 'freeze_sha256': 'frozen', 'workers': {'4b-shard-0': {}}})
            with self.assertRaises(AssertionError):
                run.require_preflight_acceptance(root / 'survey' / '4b-shard-0', {'freeze_sha256': 'frozen'})

    def test_trace_rejects_missing_component_changed_control_and_wrong_history(self):
        row = dict(model_id='2b', layer=None, channel=None, question_id='Q01',
                   output={'token_ids': [248046]}, calibration={'input_token_count': 1, 'input_token_sha256': 'input'})
        item = {'record': row, 'model': '2b'}
        sites = [dict(layer=layer, component=component, clean_norm=[1.0], steer_norm=[1.0],
                      delta_norm=[0.0], relative_delta=[0.0], cosine=[1.0])
                 for layer in range(24) for component in ('attention', 'mlp', 'residual')]
        trace = dict(generated_token_ids=[248046], source_token_ids_match=True, input_token_sha256='input',
                     observed_position_count=1, observed_input_token_ids=[7], input_token_ids=[7],
                     prompt_token_count=1, forward_steps=[{}], sites=sites,
                     clean_shadow={'fresh_cache': True, 'token_ids': [248046], 'prefixes_verified': 1},
                     logits={'steps': [{'step': 0, 'generated_token_id': 248046, 'candidates': [
                         dict(clean_logit=1.0, steer_logit=1.0, clean_logprob=-1.0, steer_logprob=-1.0)]}]})
        self.assertTrue(run.check_trace(trace, item, 'baseline'))
        for kind in ('missing_site', 'changed_control', 'wrong_history', 'nonfinite', 'undefined_without_zero'):
            broken = copy.deepcopy(trace)
            if kind == 'missing_site':
                broken['sites'].pop()
            elif kind == 'changed_control':
                broken['sites'][0]['delta_norm'][0] = 0.1
            elif kind == 'wrong_history':
                broken['clean_shadow']['token_ids'] = [9]
            elif kind == 'nonfinite':
                broken['sites'][0]['clean_norm'][0] = float('nan')
            else:
                broken['sites'][0]['relative_delta'][0] = None
            with self.subTest(kind=kind), self.assertRaises(AssertionError):
                run.check_trace(broken, item, 'baseline')


if __name__ == '__main__':
    unittest.main()
