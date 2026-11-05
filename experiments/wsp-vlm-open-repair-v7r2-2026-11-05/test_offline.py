"""Synthetic contract tests only: NO real checkpoints, processor, LLM or GPU.

The scripted researcher deliberately has a recipe for testing plumbing. It is not
shipped as a scientific search policy and proves nothing about AI research skill.
"""
import json
import contextlib
import struct
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
from common import HERE, packed, digest, file_hash, write_json, require_live
from weights import TensorSource, Candidates, quantize
from evidence import Evidence, compare, scorers, summarize, repair_score
from kernel import PythonNamespace, collect_staged, SandboxKernel
from service import Service
from controller import run_session, parse_action

NAMES = ['visual.block.weight', 'language.attention.weight', 'language.mlp.weight']


def tiny_checkpoint(root):
    """8-scalar tensors in two shards, hand-encoded; not downloaded model weights."""
    root.mkdir()
    mapping = {}
    for number, names in enumerate((NAMES[:1], NAMES[1:])):
        header, body = {}, b''
        for name in names:
            array = np.zeros((2, 4), dtype='<u2')
            raw = array.tobytes()
            header[name] = dict(dtype='BF16', shape=[2, 4], data_offsets=[len(body), len(body)+len(raw)])
            body += raw
            mapping[name] = f'part-{number}.safetensors'
        h = packed(header)
        (root/f'part-{number}.safetensors').write_bytes(struct.pack('<Q', len(h))+h+body)
    write_json(root/'model.safetensors.index.json', dict(weight_map=mapping))


def tiny_evidence(root):
    root.mkdir()
    # Valid tiny PNG used only as an attachment identity, not processed by a model.
    import base64
    (root/'input.png').write_bytes(base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+a9X8AAAAASUVORK5CYII='))
    records = []
    for g in range(2):
        for condition, answer in [('total', 2), ('subset', 1)]:
            rid = f'g{g}:{condition}'
            records.append(dict(input=dict(request_id=rid, text='Synthetic '+condition, image='input.png'),
                gold=dict(request_id=rid, group_id=f'g{g}', split='D', condition=condition, answer=answer,
                          arm='B0', template='T0', primary=True), preview='input.png'))
    write_json(root/'bundle.json', dict(task='B', role='development', split='D', records=records,
        files={'input.png':file_hash(root/'input.png')}, previous_predictions=[]))
    return Evidence(root, file_hash(root/'bundle.json'))


def contract():
    return dict(actions=80, forwards=100, samples=100, target_tokens=50000, wall_seconds=300,
        python_seconds=30, max_input_tokens=256, max_measure_elements=100, temporary_scalars=6,
        final_scalars=2, researcher_turns=20, researcher_usd=1., researcher_turn_reserve_usd=.01,
        max_format_rate=0., max_protection_drop=0., protection_conditions=['total'])


class FakeBackend:
    def __init__(self, target=NAMES[0]):
        self.target, self.calls = target, 0
        self.fail_on = None

    @contextlib.contextmanager
    def candidate(self, candidates, candidate):
        yield

    def catalog(self):
        return dict(modules=NAMES, synthetic=True)

    def generate(self, request, candidates, candidate, remaining):
        self.calls += 1
        if self.calls == self.fail_on:
            raise RuntimeError('synthetic backend infrastructure failure')
        repaired = candidates.load(candidate, self.target)[0, 0] > .5
        text = '1' if repaired and request['request_id'].endswith('subset') else '2'
        # Gold is deliberately not passed to this backend.
        assert set(request) == {'request_id', 'text', 'image'}
        return dict(request_id=request['request_id'], text=text, truncated=False, status='ok',
                    input_tokens=8, output_tokens=1, visual_tokens=1)

    def measure(self, request, candidates, candidate, spec):
        self.calls += 1
        return dict(captures=[dict(module=n, values=[3 if n==self.target else 1]) for n in NAMES],
                    synthetic=True, input_tokens=8, output_tokens=0, visual_tokens=1)


class TrustedFixtureKernel:
    """Only test-authored Python; production never uses this unsandboxed adapter."""
    def __init__(self, namespace): self.namespace = namespace
    def call(self, code, seconds): return self.namespace.execute(code)
    def close(self): pass


class ScriptedResearcher:
    def __init__(self):
        self.turns, self.base, self.candidate, self.saw_image = 0, None, None, False

    def turn(self, prompt, images, out):
        self.turns += 1
        t = self.turns
        if t == 1: action = dict(op='status')
        else:
            previous = json.loads(prompt)
            assert previous['failed'] is False, previous
            v = previous['value']
            if t == 2:
                self.base = v['state']['current']; action = dict(op='evidence')
            elif t == 3:
                assert len(v['rows']) == 4
                action = dict(op='image', request_id='g0:subset', kind='preview')
            elif t == 4:
                self.saw_image = len(images)==1 and images[0].is_file()
                action = dict(op='measure', ids=['g0:subset'], candidate=self.base)
            elif t == 5:
                # Read real preceding tool feedback, choose a different parameter in each fixture world.
                code = "import json\nr=json.load(open(ARTIFACTS+'/turn-0004.json'))\nmeasurements=r['value']['results'][0]['captures']\nchosen=max(measurements,key=lambda row:row['values'][0])['module']\nx=load(chosen)\nx[0,0]+=1\nsave_edit(chosen,x)\nprint('根据反馈选点：',chosen)"
                return 'Synthetic fixture: choose from returned measurements.\n```python\n'+code+'\n```'
            elif t == 6:
                assert '根据反馈选点' in v['output']; action = dict(op='commit', parent=self.base, rationale='Synthetic feedback-selected parameter')
            elif t == 7:
                self.candidate = v['id']; action = dict(op='evaluate', candidate=self.candidate)
            elif t == 8:
                assert len(v['vs_original']['repaired'])==2 and not v['vs_original']['worsened']
                action = dict(op='accept', candidate=self.candidate)
            elif t == 9: action = dict(op='freeze')
            else: raise AssertionError('Unexpected round')
        return 'Synthetic fixture: test the next tool transition.\n```forward\n'+json.dumps(action)+'\n```'


class OfflineTests(unittest.TestCase):
    def test_original_screen_cache_has_no_new_forward(self):
        s=self.service()
        ids=list(self.evidence.records)
        self.evidence.package['previous_predictions']=[dict(request_id=i,text='2',truncated=False,status='ok') for i in ids]
        self.evidence.package['sources']={'fixture':True}
        s.seed_screen_baseline()
        full,cached=s.evaluate_one(self.candidates.base_id,ids)
        subset,reused=s.evaluate_one(self.candidates.base_id,ids[:2])
        self.assertTrue(cached and reused)
        self.assertEqual(len(subset['predictions']),2)
        self.assertEqual(s.backend.calls,0)
        self.assertEqual(s.state['samples'],0)

    def test_repair_score_uses_both_wordings(self):
        rows = [dict(group_id='g', arm='B0', template=t, condition=c, correct=t=='T0')
                for t in ('T0','T1') for c in ('total','subset')]
        self.assertEqual(repair_score(rows), .5)
        rows += [dict(group_id='other', arm='B0', template='T0', condition=c, correct=True)
                 for c in ('total','subset')]
        self.assertEqual(repair_score(rows), .75)  # groups, not raw panel count
        self.assertIsNone(repair_score(rows[:-1]))

    def test_cell_protection_cannot_hide_wording_damage(self):
        # Equal pooled total accuracy, but T1 loses both groups: must reject.
        records = list(self.evidence.records.values())
        for r in records:
            row = json.loads(json.dumps(r))
            rid = row['input']['request_id'] + ':T1'
            row['input']['request_id'] = row['gold']['request_id'] = rid
            row['gold'].update(template='T1', primary=False)
            self.evidence.records[rid] = row
        s = self.service(); original = s.backend.generate
        x = self.source.load(NAMES[0]); x[0,0] = 1
        m = self.candidates.commit(self.candidates.base_id,{NAMES[0]:x},'fixture')
        def changed(request, candidates, candidate, remaining):
            r = original(request,candidates,candidate,remaining)
            if 'total' in request['request_id']:
                t1 = request['request_id'].endswith(':T1')
                r['text'] = '2' if t1 == (candidate == self.candidates.base_id) else '0'
            return r
        s.backend.generate = changed
        self.assertFalse(self.action(s,'eval',op='evaluate',candidate=m['id'])['failed'])
        r = self.action(s,'accept',op='accept',candidate=m['id'])
        self.assertTrue(r['failed']); self.assertIn('wording/order/prompt',r['error'])

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        tiny_checkpoint(self.root/'model')
        self.source = TensorSource(self.root/'model', {'tied.alias': NAMES[0]})
        self.candidates = Candidates(self.source, self.root/'candidates', 6, 2)
        self.evidence = tiny_evidence(self.root/'evidence')
        self.backend = FakeBackend()
        self.services = []

    def tearDown(self):
        for s in self.services: s.close()
        self.temp.cleanup()

    def service(self, suffix='run', target=NAMES[0], limits=None):
        root = self.root/suffix
        root.mkdir()
        (root/'work').mkdir()
        namespace = PythonNamespace(self.source, self.candidates, root/'work', root/'public/public.json',
                                    self.evidence.root, root/'artifacts')
        backend = FakeBackend(target)
        s = Service(root, self.candidates, self.evidence, backend, TrustedFixtureKernel(namespace),
                    limits or contract(), 'SYNTHETIC-PROTOCOL')
        self.services.append(s)
        return s

    def action(self, s, id, **req):
        return s.dispatch(dict(id=id, kind='forward', request=req))

    def test_open_loop_changes_selection_with_feedback(self):
        chosen = []
        for index, target in enumerate((NAMES[0], NAMES[1])):
            s = self.service('world'+str(index), target)
            r = ScriptedResearcher()
            result = run_session(s, r, s.root/'conversation', 'SYNTHETIC fixture only')
            self.assertTrue(r.saw_image)
            self.assertEqual(result['status'], 'stopped_or_frozen')
            m = self.candidates.manifest(result['frozen'])
            chosen.append(list(m['tensors']))
            self.assertEqual(m['changed_scalars'], 1)
            self.assertFalse(result['independent_confirmation'])
        self.assertEqual(chosen, [[NAMES[0]], [NAMES[1]]])

    def test_all_modules_and_tied_aliases(self):
        edits = {}
        for name in NAMES:
            x = self.source.load(name); x[1,2] = 2; edits[name] = x
        m = self.candidates.commit(self.candidates.base_id, edits, 'Cross-module fixture')
        self.assertEqual(m['changed_scalars'], 3)
        self.assertEqual(set(m['tensors']), set(NAMES))
        x = edits[NAMES[0]]
        tied = self.candidates.commit(self.candidates.base_id, {NAMES[0]:x, 'tied.alias':x}, 'Tied fixture')
        self.assertEqual(tied['changed_scalars'], 1)
        with self.assertRaises(ValueError):
            self.candidates.commit(self.candidates.base_id, {NAMES[0]:x, 'tied.alias':x+1}, 'conflict')

    def test_effective_dtype_and_overflow(self):
        self.assertEqual(float(quantize([1.00001], 'BF16')[0]), 1.)
        self.assertEqual(float(quantize([1.00390625], 'BF16')[0]), 1.)
        with self.assertRaises(ValueError): quantize([float('nan')], 'BF16')
        with self.assertRaises(ValueError): quantize([1e10], 'F16')

    def test_float32_checkpoint_counted_in_runtime_bf16(self):
        root = self.root/'float32'; root.mkdir()
        values = np.array([1.00001], dtype='<f4')
        header = packed({'p':dict(shape=[1],dtype='F32',data_offsets=[0,4])})
        (root/'part.safetensors').write_bytes(struct.pack('<Q',len(header))+header+values.tobytes())
        write_json(root/'model.safetensors.index.json',dict(weight_map={'p':'part.safetensors'}))
        source = TensorSource(root)
        store = Candidates(source,self.root/'float32_candidates',2,1)
        m = store.commit(store.base_id,{'p':np.array([1.00002])},'both round to the same runtime BF16 value')
        self.assertEqual(m['changed_scalars'],0)

    def test_support_relative_to_base_and_atomic_rejection(self):
        x = self.source.load(NAMES[0]); x.flat[:4] = 1
        first = self.candidates.commit(self.candidates.base_id, {NAMES[0]:x}, 'first')
        y = self.source.load(NAMES[1]); y.flat[:3] = 1
        with self.assertRaises(ValueError): self.candidates.commit(first['id'], {NAMES[1]:y}, 'over cap')
        self.assertEqual(len(list((self.root/'candidates').iterdir())), 1)
        with self.assertRaises(ValueError): self.candidates.freeze(first['id'])
        restored = self.candidates.commit(first['id'], {NAMES[0]:self.source.load(NAMES[0])}, 'restore W0')
        self.assertEqual(restored['changed_scalars'], 0)

    def test_unknown_shape_and_direct_proposal_validation(self):
        with self.assertRaises(KeyError): self.candidates.commit(self.candidates.base_id, {'unknown':np.zeros(1)}, 'bad')
        with self.assertRaises(ValueError): self.candidates.commit(self.candidates.base_id, {NAMES[0]:np.ones(1)}, 'bad')
        s = self.service()
        write_json(s.root/'work/stage.json', {NAMES[0]:'../../secret.npy'})
        with self.assertRaises(ValueError): collect_staged(s.root/'work', self.source)

    def test_checkout_clears_staging_and_restores_parent(self):
        s = self.service()
        code = "x=load(NAMES[0]); x[0,0]=1; save_edit(NAMES[0],x)"
        self.assertFalse(s.dispatch(dict(id='py', kind='python', code=code))['failed'])
        m = self.action(s, 'commit', op='commit', parent=self.candidates.base_id, rationale='test')['value']
        self.assertEqual(s.state['current'], m['id'])
        self.action(s, 'reset', op='checkout', candidate=self.candidates.base_id)
        self.assertEqual(collect_staged(s.root/'work', self.source), {})
        self.assertTrue(np.array_equal(s.kernel.namespace.load(NAMES[0]), self.source.load(NAMES[0])))

    def test_idempotency_and_uncertain_action(self):
        s = self.service()
        a = dict(id='same', kind='forward', request=dict(op='evaluate', candidate=self.candidates.base_id))
        r = s.dispatch(a); calls = s.backend.calls
        self.assertEqual(s.dispatch(a), r)
        self.assertEqual(s.backend.calls, calls)
        with self.assertRaises(ValueError): s.dispatch(dict(a, request=dict(op='status')))
        (s.root/'actions/pending').mkdir()
        with self.assertRaises(RuntimeError): self.action(s, 'next', op='status')

    def test_local_subset_cannot_select_best(self):
        s = self.service()
        self.action(s, 'eval', op='evaluate', candidate=self.candidates.base_id, ids=['g0:total'])
        self.assertTrue(self.action(s, 'accept', op='accept', candidate=self.candidates.base_id)['failed'])
        self.assertTrue(self.action(s, 'freeze', op='freeze')['failed'])

    def test_cache_and_parent_pairing(self):
        s = self.service()
        self.action(s, 'first', op='evaluate', candidate=self.candidates.base_id)
        calls = s.backend.calls
        r = self.action(s, 'second', op='evaluate', candidate=self.candidates.base_id)
        self.assertTrue(r['value']['cached'][self.candidates.base_id])
        self.assertEqual(s.backend.calls, calls)
        self.assertEqual(s.state['samples'], 4)

    def test_errors_are_not_scored_and_costs_not_refunded(self):
        s = self.service(); s.backend.fail_on = 2
        r = self.action(s, 'fail', op='evaluate', candidate=self.candidates.base_id)
        self.assertTrue(r['failed'])
        self.assertEqual(s.state['samples'], 2)
        self.assertEqual(s.state['evaluations'], {})
        raw = list((s.root/'artifacts').glob('*.attempts.jsonl'))[0].read_text()
        self.assertIn('failed', raw); self.assertIn('completed', raw)

    def test_budget_and_protection(self):
        limits = contract(); limits['samples']=1
        s = self.service(limits=limits)
        self.assertTrue(self.action(s, 'cap', op='evaluate', candidate=self.candidates.base_id)['failed'])
        self.assertEqual(s.backend.calls, 1)
        self.assertEqual(s.state['reserved_target_tokens'], 384)

    def test_protection_rejects_collateral_damage(self):
        s = self.service()
        x=self.source.load(NAMES[0]); x[0,0]=1
        m=self.candidates.commit(self.candidates.base_id,{NAMES[0]:x},'fixture')
        normal=s.backend.generate
        def damage(request,candidates,candidate,remaining):
            value=normal(request,candidates,candidate,remaining)
            if candidate!=candidates.base_id and request['request_id'].endswith('total'):
                value['text']='0'
            return value
        s.backend.generate=damage
        self.assertFalse(self.action(s,'eval',op='evaluate',candidate=m['id'])['failed'])
        r=self.action(s,'accept',op='accept',candidate=m['id'])
        self.assertTrue(r['failed']);self.assertIn('Protection failed',r['error'])

    def test_cache_tamper_rejected(self):
        s=self.service()
        self.action(s,'eval',op='evaluate',candidate=self.candidates.base_id)
        entry=next(iter(s.state['evaluations'].values()))
        (s.root/entry['path']).write_text('{}')
        self.assertTrue(self.action(s,'again',op='evaluate',candidate=self.candidates.base_id)['failed'])

    def test_partial_measurement_preserved(self):
        s=self.service(); normal=s.backend.measure
        def fail(request,*args):
            if request['request_id']=='g0:subset': raise RuntimeError('synthetic measurement failure')
            return normal(request,*args)
        s.backend.measure=fail
        r=self.action(s,'measure',op='measure',ids=['g0:total','g0:subset'])
        self.assertTrue(r['failed'])
        self.assertEqual(json.loads((s.root/'actions/measure/measure-0000.json').read_text())['status'],'complete')
        self.assertEqual(json.loads((s.root/'actions/measure/measure-0001.json').read_text())['status'],'failed')

    def test_failed_python_proposal_is_archived(self):
        s=self.service()
        code="x=load(NAMES[0]);x[0,0]=1;save_edit(NAMES[0],x);raise ValueError('fixture')"
        r=s.dispatch(dict(id='badcode',kind='python',code=code))
        self.assertTrue(r['failed'])
        m=json.loads((s.root/'actions/badcode/proposal/manifest.json').read_text())
        self.assertEqual(len(m),1)

    def test_confirmation_separation_and_one_shot(self):
        from confirmation import confirm
        s=self.service(); researcher=ScriptedResearcher()
        run_session(s,researcher,s.root/'conversation','fixture')
        root=self.root/'unseen'; root.mkdir()
        import shutil
        from PIL import Image
        Image.new('RGB',(2,2),(123,45,67)).save(root/'input.png')
        bundle=json.loads((self.evidence.root/'bundle.json').read_text())
        bundle.update(role='confirmation',split='Q')
        bundle['files']['input.png']=file_hash(root/'input.png')
        for row in bundle['records']:
            row['gold']['split']='Q'
            row['gold']['group_id']='unseen-'+row['gold']['group_id']
        write_json(root/'bundle.json',bundle)
        args=dict(frozen_path=s.root/'frozen-candidate.json',frozen_sha256=file_hash(s.root/'frozen-candidate.json'),
                  candidates=self.candidates,evidence_root=root,evidence_sha256=file_hash(root/'bundle.json'),
                  seen_group_keys=[('B','g0'),('B','g1')],backend_factory=lambda e:FakeBackend(),
                  seen_image_hashes=list(self.evidence.package['files'].values()),independence_audit_sha256='SYNTHETIC-AUDIT',
                  out=self.root/'confirmation',contract=contract(),protocol_identity='confirmation-fixture')
        result=confirm(**args)
        self.assertFalse(result['researcher_access'])
        with self.assertRaises(FileExistsError):confirm(**args)
        args['out']=self.root/'overlap';args['seen_group_keys']=[('B','unseen-g0')]
        with self.assertRaises(ValueError):confirm(**args)
        args['seen_group_keys']=[('B','g0')];args['seen_image_hashes']=list(bundle['files'].values())
        with self.assertRaises(ValueError):confirm(**args)

    def test_backend_rollback_and_hook_cleanup_with_stubs(self):
        from backend import VLMBackend
        class Tensor:
            def __init__(self,value):self.a=np.array(value,dtype=np.float32);self.device='synthetic';self.dtype='synthetic'
            def copy_(self,other):self.a[:]=other.a
        class Torch:
            no_grad=staticmethod(contextlib.nullcontext)
            inference_mode=staticmethod(contextlib.nullcontext)
            as_tensor=staticmethod(lambda value,**kw:Tensor(value))
            equal=staticmethod(lambda a,b:np.array_equal(a.a,b.a))
        class Handle:
            def __init__(self,module,hook):self.module,self.hook=module,hook
            def remove(self):self.module.hooks.remove(self.hook)
        class Module:
            def __init__(self):self.hooks=[]
            def register_forward_hook(self,hook):self.hooks.append(hook);return Handle(self,hook)
            def __call__(self,**kwargs):raise RuntimeError('synthetic forward failure')
        model=Module()
        b=object.__new__(VLMBackend)
        b.model=model;b.poisoned=False;b.source=self.source;b.torch=Torch()
        b.parameters={n:Tensor(self.source.load(n)) for n in NAMES};b.modules={'any.module':model}
        b.cfg=dict(contract=dict(max_measure_elements=10))
        b.encode=lambda request,suffix: ({},dict(prompt_tokens=1,input_tokens=1))
        x=self.source.load(NAMES[0]);x[0,0]=1
        m=self.candidates.commit(self.candidates.base_id,{NAMES[0]:x},'fixture')
        with self.assertRaises(RuntimeError):
            with b.candidate(self.candidates,m['id']):
                self.assertEqual(b.parameters[NAMES[0]].a[0,0],1)
                raise RuntimeError('synthetic body failure')
        self.assertEqual(b.parameters[NAMES[0]].a[0,0],0)
        with b.candidate(self.candidates,m['id']):
            with b.candidate(self.candidates,m['id']):
                self.assertEqual(b.parameters[NAMES[0]].a[0,0],1)
            self.assertEqual(b.parameters[NAMES[0]].a[0,0],1)
            with self.assertRaises(ValueError):
                with b.candidate(self.candidates,self.candidates.base_id):pass
        self.assertEqual(b.parameters[NAMES[0]].a[0,0],0)
        self.assertIsNone(b._active_candidate)
        with self.assertRaises(RuntimeError):
            b.measure({},self.candidates,m['id'],dict(capture=[dict(module='any.module')]))
        self.assertEqual(model.hooks,[])
        self.assertEqual(b.parameters[NAMES[0]].a[0,0],0)

    def test_evidence_and_sealed_paths(self):
        with self.assertRaises(PermissionError): self.evidence.select(['H-secret'])
        with self.assertRaises(PermissionError): self.evidence.select(['g0:total', 'g0:total'])
        p = json.loads((self.root/'evidence/bundle.json').read_text()); p['records'][0]['gold']['split']='H'
        write_json(self.root/'evidence/bundle.json', p)
        with self.assertRaises(ValueError): Evidence(self.root/'evidence', file_hash(self.root/'evidence/bundle.json'))

    def test_candidate_tamper(self):
        x = self.source.load(NAMES[0]); x[0,0]=1
        m = self.candidates.commit(self.candidates.base_id, {NAMES[0]:x}, 'test')
        path = self.root/'candidates'/m['id']/m['tensors'][NAMES[0]]['file']
        path.write_bytes(b'corrupted')
        with self.assertRaises(ValueError): self.candidates.manifest(m['id'])

    def test_unicode_and_persistent_code(self):
        s = self.service()
        s.dispatch(dict(id='one', kind='python', code='probe=41'))
        r = s.dispatch(dict(id='two', kind='python', code="assert probe+1==42; print('中文保留')"))
        self.assertIn('中文保留', r['value']['output'])

    def test_excess_output_fails_explicitly(self):
        s=self.service()
        r=s.dispatch(dict(id='outputcap',kind='python',code="print('x'*1000001)"))
        self.assertTrue(r['failed'])
        self.assertIn('output exceeds',r['value']['output'])

    def test_strict_scoring_b_and_c(self):
        scoring = scorers()
        g = self.evidence.select(['g0:subset'])[0]['gold']
        for text, expected in [('1',True),('1 object',False),('1.0',False)]:
            rows = scoring['B'].score([dict(request_id=g['request_id'],text=text,truncated=False)], [g])
            self.assertEqual(rows[0]['correct'], expected)
        cg = dict(request_id='c', names=['cat', 'elephant'], answer='cat', primary=True, split='D')
        for text, truncated, ok in [('cat',False,True),('cat',True,False),('a cat',False,False)]:
            rows = scoring['C'].score([dict(request_id='c',text=text,truncated=truncated)], [cg])
            self.assertEqual(rows[0]['correct'], ok)
        with self.assertRaises(ValueError): scoring['B'].score([], [g])

    def test_parser_and_honest_early_stop(self):
        with self.assertRaises(ValueError): parse_action('```python\nprint(1)\n```')
        self.assertEqual(parse_action('Evidence.\n```python\nprint(1)\n```')['kind'], 'python')
        s = self.service()
        class Stop:
            def turn(self, prompt, images, out): return 'No evidence of a useful patch; stop.'
        r = run_session(s, Stop(), s.root/'conversation', 'fixture')
        self.assertEqual(r['status'], 'researcher_stopped')
        self.assertEqual(s.backend.calls, 0)

    def test_live_gate_before_import(self):
        config = json.loads((HERE/'config.template.json').read_text())
        with self.assertRaises(PermissionError): require_live(config)
        from backend import VLMBackend
        with self.assertRaises(PermissionError): VLMBackend(config, self.source, self.evidence)
        with self.assertRaises(PermissionError): SandboxKernel(config, None, None, None, None, None)
        for name in ('torch', 'transformers', 'safetensors', 'huggingface_hub'):
            self.assertNotIn(name, sys.modules)

    def test_synthetic_receipt_cannot_unlock_real_search(self):
        from live import check_search_readiness
        path=self.root/'acceptance.json'
        write_json(path,dict(status='passed',synthetic_only=True,real_model_acceptance=False))
        with self.assertRaises(ValueError):
            check_search_readiness(dict(engineering_acceptance_path=str(path),engineering_acceptance_sha256=file_hash(path)))


if __name__ == '__main__':
    unittest.main(verbosity=2)
