"""Pure orchestration tests: fake model outputs are never scientific evidence."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import execution as run
import experiment as exp
from control_engine import bind_reference, token_hash, text_hash


class Tokenizer:
    bos_token_id = None
    eos_token_id = None
    def encode(self, text, **kwargs):
        return [ord(c) for c in text]
    def apply_chat_template(self, messages, **kwargs):
        return messages[0]['content'] + '\nAnswer:'


class FakeLogits:
    def __getitem__(self, index):
        return float(index) / 1000


class FakeEngine:
    def __init__(self):
        self.tokenizer, self.stop_ids, self.calls = Tokenizer(), [248044, 248046], []
        self.torch = SimpleNamespace(save=lambda value, path: Path(path).write_bytes(json.dumps(value).encode()),
                                    log_softmax=lambda value, dim: value)
    def calibrate(self, contexts):
        self.calls.append(('calibrate', contexts))
        return [{'context_sha256': text_hash(c), 'input_token_sha256': token_hash(self.tokenizer.encode(c)),
                 'input_token_count': len(c), 'residual_scales': {str(i): 1.0 for i in range(32)}} for c in contexts]
    def output(self, context, reference, condition, mode='full', tokens=None, prefix=(), patch=None):
        tokens = tokens if tokens is not None else list(range(100, 116)) + [248044]
        input_tokens = self.tokenizer.encode(context)
        return {'status': 'completed', 'token_ids': tokens, 'generated_token_count': len(tokens),
            'max_new_tokens': 128,
            'token_sha256': token_hash(tokens), 'input_token_sha256': token_hash(input_tokens),
            'calibration': bind_reference(context, reference, self.tokenizer), 'condition': condition,
            'mode': mode, 'end_reason': 'eos_token' if tokens[-1] in self.stop_ids else 'length_limit',
            'raw_text': 'FAKE CPU OUTPUT', 'answer_text': 'FAKE CPU OUTPUT', 'seconds': 0.0,
            'forced_prefix_tokens': list(prefix),
            'step_readouts': [{'actual_token_id': t, 'prefix_token_sha256': token_hash(input_tokens + tokens[:i])}
                             for i, t in enumerate(tokens)],
            'cache_fingerprints': {'4': {'sha256': 'same4'}, '16': {'sha256': 'same16'}},
            'patch_audit': [{'donor_id': patch['donor']['id']}] if patch else []}
    def generate_one(self, context, reference, condition, mode='full', **kwargs):
        self.calls.append(('generate', condition['id'], mode))
        return self.output(context, reference, condition, mode)
    def score_one(self, context, continuation, reference, condition, mode='full'):
        self.calls.append(('score', continuation))
        tokens = self.tokenizer.encode(continuation)
        result = self.output(context, reference, condition, mode, tokens=tokens, prefix=tokens)
        result.update(continuation_token_ids=tokens, token_logprobs=[-1.0]*len(tokens),
                      loglikelihood=-float(len(tokens)), max_new_tokens=len(tokens))
        return result
    def branch(self, context, reference, condition, prefix_tokens, kind='continue', mode='full', **kwargs):
        self.calls.append(('branch', condition['id'], kind, len(prefix_tokens)))
        result = self.output(context, reference, condition, mode, prefix=prefix_tokens, patch=kwargs.get('patch'))
        if kwargs.get('retain_fork_logits'):
            result['_fork_logits'] = FakeLogits()
        return result
    def prepare_donor(self, context, reference, condition, **kwargs):
        self.calls.append(('donor', condition['id']))
        return {'id': kwargs['donor_id'], 'vector': [1., 2.], 'vector_sha256': 'fake-vector',
                'layer': kwargs['layer'], 'component': kwargs['component'], 'source_seconds': 0.0,
                'prediction_step': kwargs['prediction_step'], 'source_context_sha256': text_hash(context)}


def rows(prefix='RD'):
    return [{'id': f'{prefix}01-f{f}-required', 'base_id': f'{prefix}01', 'panel': 'diagnostic',
        'family': 'reading', 'fact_version': f, 'demand': 'required', 'prompt': f'事实{f}',
        'choices': ['甲。', '乙。'], 'target_index': f, 'reference_id': f'{prefix}01-f0-required',
        'truth_explanation': 'Synthetic fixture only.'} for f in (0, 1)]


class ExecutionTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(); self.addCleanup(tmp.cleanup)
        self.root, self.here = Path(tmp.name), Path(tmp.name) / 'experiment'
        self.here.mkdir()
        self.native = {'id': 'N_L00_C4146_D+1', 'kind': 'native', 'layer': 0, 'channel': 4146, 'dose': 1.0}
        self.dev, self.confirm = rows(), rows('CRD')
        self.panels = {'development': self.dev, 'confirmation': self.confirm, 'anchors': []}
        for p in (patch.object(exp, 'HERE', self.here), patch.object(exp, 'REPO', self.root),
                  patch.object(exp, 'check', return_value={'status': 'passed'}),
                  patch.object(exp, 'items', side_effect=lambda split: self.panels[split]),
                  patch.object(exp, 'conditions', return_value=[run.CLEAN, self.native]),
                  patch.object(exp, 'engine_condition', side_effect=lambda c: dict(c))):
            p.start(); self.addCleanup(p.stop)
        self.write('freeze.json', {'test': 'not scientific evidence'})
        self.freeze = exp.sha(self.here / 'freeze.json')
        for name, data in self.panels.items(): self.write(f'data/{name}.json', data)
        self.write('preflight.json', {'status': 'passed', 'freeze_sha256': self.freeze})
        self.write('cpu.json', {'status': 'passed', 'tests_run': 1, 'failures': 0, 'errors': 0, 'skipped': 0,
            'source_hashes': {'experiment/freeze.json': self.freeze}})
        self.write('review.json', {'status': 'passed', 'experiment': self.here.name,
            'confirmation_model_outputs_read': False,
            'file_hashes': {f'experiment/data/{n}.json': exp.sha(self.here / f'data/{n}.json') for n in self.panels}})
    def write(self, name, value): exp.write(self.here / name, value)
    def hashes(self, *names): return {n: exp.sha(self.here / n) for n in names}
    def sources(self):
        engine, result = FakeEngine(), {}
        contexts = exp.contexts_for(engine.tokenizer, self.dev)
        reference = engine.calibrate([contexts[self.dev[0]['id']]])[0]
        for item in self.dev:
            spec = {'key': item['id'] + '__source', 'kind': 'generation', 'item_id': item['id'],
                    'condition': self.native, 'mode': 'full'}
            record = run._base_record('development', spec, item, contexts[item['id']], reference)
            record.update(status='completed', evaluation_panel='development', effective_condition=self.native,
                generation=engine.generate_one(contexts[item['id']], reference, self.native),
                candidates=[{'text': c, 'result': engine.score_one(contexts[item['id']], c, reference, self.native)} for c in item['choices']])
            name = f'sources/{item["id"]}.json'; self.write(name, record)
            result[item['id']] = {'path': name, 'sha256': exp.sha(self.here / name)}
        return result
    def selection(self, patch_candidate=False):
        sources = self.sources()
        value = {'status': 'locked', 'experiment': self.here.name, 'freeze_sha256': self.freeze,
            'confirmation_item_ids': [r['id'] for r in self.confirm],
            'evidence_hashes': {s['path']: s['sha256'] for s in sources.values()},
            'conditions': [{'condition': self.native, 'item_ids': [r['id'] for r in self.dev],
                            'first_step_split': True, 'source_records': sources}], 'patch_candidates': []}
        if patch_candidate:
            value['patch_candidates'] = [{'id': 'candidate01', 'symptom': 'cpu-fixture',
                'condition_id': self.native['id'], 'item_ids': [r['id'] for r in self.dev], 'layer': 1,
                'component': 'mlp', 'prediction_step': 4, 'neighbor': {'layer': 1, 'component': 'attention'},
                'source_records': sources}]
        return value
    def authorization(self, stage, selection=None, panel='development', manifest=None):
        evidence = self.hashes('preflight.json', 'review.json', 'cpu.json')
        if selection is not None:
            self.write('selection.json', selection); evidence.update(self.hashes('selection.json'))
        if panel == 'confirmation' and stage != 'confirmation': evidence.update(self.hashes('gate-confirmation.json'))
        if manifest is not None:
            self.write('source-manifest.json', manifest); evidence.update(self.hashes('source-manifest.json'))
        gate = {'status': 'passed', 'stage': stage, 'freeze_sha256': self.freeze,
                'evidence_hashes': dict(evidence), 'measurement_usable': True,
                'interpretation_locked': True, 'selection_locked': True}
        if stage == 'confirmation': gate['confirmation_outputs_previously_unseen'] = True
        self.write(f'gate-{stage}.json', gate); evidence.update(self.hashes(f'gate-{stage}.json'))
        return {'status': 'authorized', 'experiment': self.here.name, 'formal_execution_authorized': True,
            'allowed_stages': [stage], 'maximum_workers': 2, 'user_instruction': 'FAKE CPU TEST ONLY',
            'freeze_path': 'freeze.json', 'freeze_sha256': self.freeze, 'panel': panel,
            'required_evidence': evidence, 'preflight_evidence_path': 'preflight.json', 'cpu_evidence_path': 'cpu.json',
            'data_review_path': 'review.json', 'stage_gate_path': f'gate-{stage}.json', 'selection_path': 'selection.json',
            'confirmation_lock_path': 'gate-confirmation.json', 'source_manifest_path': 'source-manifest.json'}
    def execute(self, stage, auth, name=None, engine=None):
        output = self.here / (name or stage); output.mkdir()
        receipt = {'stage': stage, 'gpu': 0, 'status': 'running', 'pid': 123,
                   'freeze_sha256': self.freeze, 'record_hashes': {}, 'asset_hashes': {}}
        exp.write(output / 'execution.json', deepcopy(receipt), immutable=True)
        exp.write(output / 'authorization.json', auth, immutable=True)
        engine = engine or FakeEngine()
        run.run_formal(engine, stage, 0, output, receipt, auth)
        return output, receipt, engine
    def test_preflight_auth_cannot_reach_fake_engine(self):
        auth = self.authorization('development'); auth['formal_execution_authorized'] = False
        engine = FakeEngine()
        with self.assertRaises(AssertionError): self.execute('development', auth, engine=engine)
        self.assertEqual(engine.calls, [])
    def test_bad_review_is_rejected(self):
        auth = self.authorization('development'); self.write('review.json', {'status': 'failed'})
        with self.assertRaises(AssertionError): run.validate_formal_authorization(auth, 'development')
    def test_confirmation_semantic_lock_is_required_even_with_valid_hash(self):
        selection = self.selection()
        for flag in ('interpretation_locked', 'selection_locked', 'confirmation_outputs_previously_unseen'):
            with self.subTest(flag=flag):
                auth = self.authorization('confirmation', selection)
                gate = exp.read(self.here / 'gate-confirmation.json')
                gate[flag] = False
                self.write('gate-confirmation.json', gate)
                auth['required_evidence'].update(self.hashes('gate-confirmation.json'))
                with self.assertRaises(AssertionError): run.validate_formal_authorization(auth, 'confirmation')
    def test_core_coverage_tokens_and_execution_identity(self):
        output, receipt, engine = self.execute('development', self.authorization('development'))
        self.assertEqual(run.verify_formal_records(output, receipt)['records'], 4)
        self.assertEqual(receipt['formal_summary']['candidate_continuations'], 8)
        self.assertEqual(sum(c[0] == 'calibrate' for c in engine.calls), 1)
        relative = next(iter(receipt['record_hashes'])); record = exp.read(output / relative)
        record['generation']['token_ids'][0] += 1; exp.write(output / relative, record)
        receipt['record_hashes'][relative] = exp.sha(output / relative)
        with self.assertRaises(AssertionError): run.verify_formal_records(output, receipt)
        receipt['record_hashes'].pop(relative)
        with self.assertRaisesRegex(AssertionError, 'Missing or extra'): run.verify_formal_records(output, receipt)
    def test_selection_rejects_confirmation_leak_and_wrong_source(self):
        selection = self.selection(); selection['conditions'][0]['item_ids'].append(self.confirm[0]['id'])
        with self.assertRaisesRegex(AssertionError, 'confirmation'):
            run.validate_formal_authorization(self.authorization('mechanism', selection), 'mechanism')
        selection = self.selection(); source = selection['conditions'][0]['source_records'][self.dev[0]['id']]
        bad = exp.read(self.here / source['path']); bad['item_id'] = 'wrong'; self.write(source['path'], bad)
        source['sha256'] = exp.sha(self.here / source['path']); selection['evidence_hashes'][source['path']] = source['sha256']
        with self.assertRaises(AssertionError): run.validate_formal_authorization(self.authorization('mechanism', selection), 'mechanism')
    def test_mechanism_modes_forks_and_cross_scores(self):
        output, receipt, engine = self.execute('mechanism', self.authorization('mechanism', self.selection()))
        self.assertEqual(run.verify_formal_records(output, receipt)['records'], 22)
        self.assertEqual(sum(c[0] == 'branch' for c in engine.calls), 12)
        self.assertEqual(len(list((output / 'branch-comparisons').glob('*.json'))), 4)
        self.assertEqual(receipt['formal_summary']['technical_continue_replays'], 4)
    def test_early_eos_keeps_all_forks_as_not_applicable(self):
        class ShortEngine(FakeEngine):
            def generate_one(self, context, reference, condition, mode='full', **kwargs):
                self.calls.append(('generate', condition['id'], mode))
                return self.output(context, reference, condition, mode, tokens=[248044])
        engine = ShortEngine()
        selection = self.selection()
        for identity in selection['conditions'][0]['source_records'].values():
            record = exp.read(self.here / identity['path'])
            record['generation'] = engine.generate_one(record['context'], record['reference'], self.native)
            self.write(identity['path'], record)
            identity['sha256'] = exp.sha(self.here / identity['path'])
            selection['evidence_hashes'][identity['path']] = identity['sha256']
        engine.calls.clear()
        output, receipt, engine = self.execute('mechanism', self.authorization('mechanism', selection), engine=engine)
        self.assertEqual(run.verify_formal_records(output, receipt)['not_applicable'], 12)
        self.assertEqual(sum(c[0] == 'branch' for c in engine.calls), 0)
        self.assertTrue(all(exp.read(p)['status'] == 'not_applicable' for p in (output / 'branch-comparisons').glob('*.json')))
    def test_patch_six_arms_and_confirmed_followups_keep_selection(self):
        selection = self.selection(patch_candidate=True)
        output, receipt, engine = self.execute('patch', self.authorization('patch', selection))
        self.assertEqual(run.verify_formal_records(output, receipt)['records'], 12)
        self.assertEqual(sum(c[0] == 'donor' for c in engine.calls), 12)
        self.assertEqual(receipt['formal_cost']['source_replay_count'], 2)
        self.authorization('confirmation', selection)
        original_hash = exp.sha(self.here / 'selection.json')
        output, receipt, _ = self.execute('mechanism', self.authorization('mechanism', selection, panel='confirmation'), name='confirm-mechanism')
        self.assertEqual(run.verify_formal_records(output, receipt)['records'], 22)
        sources = {}
        for item in self.confirm:
            p = output / 'records' / f'{item["id"]}__{self.native["id"]}__full.json'
            sources[item['id']] = {'path': str(p.relative_to(self.here)), 'sha256': exp.sha(p)}
        manifest = {'status': 'locked', 'panel': 'confirmation', 'freeze_sha256': self.freeze,
            'selection_sha256': original_hash, 'sources': {self.native['id']: sources},
            'evidence_hashes': {s['path']: s['sha256'] for s in sources.values()}}
        output, receipt, _ = self.execute('patch', self.authorization('patch', selection, panel='confirmation', manifest=manifest), name='confirm-patch')
        self.assertEqual(run.verify_formal_records(output, receipt)['records'], 12)
        self.assertEqual(exp.sha(self.here / 'selection.json'), original_hash)


if __name__ == '__main__': unittest.main()
