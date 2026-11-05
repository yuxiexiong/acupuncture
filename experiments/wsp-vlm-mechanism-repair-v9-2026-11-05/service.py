"""Observer-owned actions, durable receipts, candidate evaluation and feedback.

Derived from the math broker's identity/reconciliation pattern. Never mounted in a
writable researcher directory. Forward budgets count samples, including failures.
"""
import fcntl
import math
import json
import time
import shutil
from pathlib import Path

from common import digest, packed, write_json, inside, file_hash
from evidence import compare, summarize, repair_score
from kernel import collect_staged
from weights import save_sparse


class Service:
    def __init__(self, root, candidates, evidence, backend, kernel, contract, protocol_identity):
        self.root, self.candidates, self.evidence = Path(root), candidates, evidence
        self.backend, self.kernel, self.contract = backend, kernel, contract
        self.protocol = protocol_identity
        self.root.mkdir(parents=True, exist_ok=True)
        self.lock = (self.root / 'observer.lock').open('a')
        fcntl.flock(self.lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        for name in ('actions', 'artifacts', 'work', 'public'):
            (self.root / name).mkdir(exist_ok=True)
        identity = dict(contract=contract, protocol=protocol_identity, evidence=evidence.identity,
                        base=candidates.base_id)
        frozen = self.root / 'identity.json'
        if frozen.exists() and json.loads(frozen.read_text()) != identity:
            raise ValueError('Cannot resume with a different contract/protocol/data/model')
        write_json(frozen, identity)
        state = self.root / 'state.json'
        self.state = json.loads(state.read_text()) if state.exists() else dict(
            current=candidates.base_id, best=candidates.base_id, actions=0, forwards=0, samples=0,
            reserved_target_tokens=0, actual_target_tokens=0, actual_visual_tokens=0, python_seconds=0.,
            started_unix=time.time(), frozen=None, research_done=False, evaluations={})
        self.save()

    def cached(self, key):
        entry = self.state['evaluations'][key]
        path = inside(self.root, entry['path'])
        if file_hash(path) != entry['sha256']:
            raise ValueError('Evaluation cache content changed')
        return json.loads(path.read_text())

    def save(self):
        write_json(self.root / 'state.json', self.state)
        write_json(self.root / 'public/public.json', dict(current=self.state['current'], best=self.state['best']))

    def remaining(self):
        limit = self.contract['wall_seconds']
        return math.inf if limit is None else limit - (time.time() - self.state['started_unix'])

    def reserve_forward(self):
        reserve = self.contract['max_input_tokens'] + 128
        if self.remaining() <= 0 or self.state['forwards'] >= self.contract['forwards'] or self.state['samples'] >= self.contract['samples']:
            raise ValueError('Forward/sample/wall budget exhausted')
        if self.state['reserved_target_tokens'] + reserve > self.contract['target_tokens']:
            raise ValueError('Target token reservation budget exhausted')
        self.state['forwards'] += 1
        self.state['samples'] += 1
        self.state['reserved_target_tokens'] += reserve
        self.save()  # reserve before compute; failed/uncertain calls are never refunded

    def record_cost(self, output):
        self.state['actual_target_tokens'] += output['input_tokens'] + output.get('output_tokens', 0)
        self.state['actual_visual_tokens'] += output.get('visual_tokens', 0)
        self.save()
        if output['input_tokens'] > self.contract['max_input_tokens'] or output.get('output_tokens', 0) > 128:
            raise ValueError('Backend exceeded token contract')

    def evaluate_one(self, candidate, ids):
        self.candidates.manifest(candidate)
        key = digest(packed(dict(candidate=candidate, ids=ids, protocol=self.protocol)))
        if key in self.state['evaluations']:
            return self.cached(key), True
        full_key = digest(packed(dict(candidate=candidate, ids=list(self.evidence.records), protocol=self.protocol)))
        if full_key in self.state['evaluations']:
            full = self.cached(full_key)
            predictions = {r['request_id']:r for r in full['predictions']}
            rows = {r['request_id']:r for r in full['scored']}
            selected = [rows[i] for i in ids]
            return dict(candidate=candidate, protocol=self.protocol, ids=ids, full_development=False,
                        predictions=[predictions[i] for i in ids], scored=selected,
                        summary=dict(summarize(selected),repair_score=repair_score(selected)),
                        reused_full_evaluation=full_key), True
        predictions = []
        raw = self.root / 'artifacts' / (key + '.attempts.jsonl')
        # A partial batch is not automatically retried; raw prefix remains evidence.
        with self.backend.candidate(self.candidates, candidate), raw.open('x') as f:
            selected = self.evidence.select(ids)
            batch_size = getattr(self.backend, 'cfg', {}).get('execution_batch_size', 1)
            for offset in range(0, len(selected), batch_size):
                batch = selected[offset:offset+batch_size]
                for row in batch:
                    self.reserve_forward()
                    f.write(packed(dict(request_id=row['input']['request_id'], event='started')).decode()+'\n')
                f.flush()
                try:
                    requests = [row['input'] for row in batch]
                    if batch_size == 1:
                        outputs = [self.backend.generate(requests[0], self.candidates, candidate, self.remaining())]
                    else:
                        outputs = self.backend.generate_batch(requests, self.candidates, candidate, self.remaining())
                    if [o['request_id'] for o in outputs] != [r['request_id'] for r in requests]:
                        raise ValueError('Batch output identity mismatch')
                    for result in outputs:
                        self.record_cost(result)
                        predictions.append(result)
                        f.write(packed(dict(event='completed', output=result)).decode()+'\n')
                    f.flush()
                except Exception as e:
                    f.write(packed(dict(request_ids=[r['input']['request_id'] for r in batch], event='failed', error=repr(e))).decode()+'\n'); f.flush()
                    raise
        rows = self.evidence.score(predictions, ids)
        result = dict(candidate=candidate, protocol=self.protocol, ids=ids,
                      full_development=set(ids)==set(self.evidence.records), predictions=predictions,
                      scored=rows, summary=dict(summarize(rows), repair_score=repair_score(rows)))
        rel = 'artifacts/' + key + '.json'
        write_json(self.root / rel, result)
        self.state['evaluations'][key] = dict(path=rel, sha256=file_hash(self.root/rel))
        self.save()
        return result, False

    def seed_screen_baseline(self):
        """Observer only, after real input-equivalence acceptance; never an AI action."""
        previous=self.evidence.package['previous_predictions']
        ids=list(self.evidence.records)
        if [p['request_id'] for p in previous] != ids:
            raise ValueError('Screen baseline must cover exact ordered development pack')
        rows=self.evidence.score(previous,ids)
        key=digest(packed(dict(candidate=self.candidates.base_id,ids=ids,protocol=self.protocol)))
        rel='artifacts/'+key+'.json'
        write_json(self.root/rel,dict(candidate=self.candidates.base_id,protocol=self.protocol,ids=ids,
            full_development=True,predictions=previous,scored=rows,
            summary=dict(summarize(rows),repair_score=repair_score(rows)),
            reused_original_screen=True,source=self.evidence.package['sources'],new_model_calls=0))
        self.state['evaluations'][key]=dict(path=rel,sha256=file_hash(self.root/rel));self.save()

    def evaluate(self, req):
        candidate = req['candidate']
        ids = req.get('ids', list(self.evidence.records))
        self.evidence.select(ids)
        cm = self.candidates.manifest(candidate)
        if self.contract.get('targeted') and self.state.get('round_budget_reached'):
            key = digest(packed(dict(candidate=candidate,ids=ids,protocol=self.protocol)))
            if key not in self.state['evaluations'] and set(ids)==set(self.evidence.records):
                raise ValueError('Thirty full candidate rounds complete; synthesize report and freeze, do not add rounds')
        models = list(dict.fromkeys([self.candidates.base_id, cm['parent'] or self.candidates.base_id, candidate]))
        results, cached = {}, {}
        for name in models:
            results[name], cached[name] = self.evaluate_one(name, ids)
        target = results[candidate]
        if self.contract.get('repair_rounds') and target['full_development'] and cm['changed_scalars']:
            signature = digest(packed({n:e.get('content_sha256',e['sha256']) for n,e in cm['tensors'].items()}))
            completed = self.state.setdefault('completed_repair_candidates', {})
            if signature not in completed:
                completed[signature] = candidate
                self.state['repair_rounds_completed'] = len(completed)
                try:
                    selection = self.accept(candidate)
                except ValueError as exc:
                    selection = dict(not_selected=str(exc))
                write_json(self.root/'artifacts'/('repair-round-%03d.json'%len(completed)),
                           dict(round=len(completed),candidate=candidate,signature=signature,selection=selection,
                                repair_score=repair_score(target['scored'])))
                self.save()
                if len(completed) >= self.contract['repair_rounds']:
                    if self.contract.get('targeted'):
                        self.state['round_budget_reached'] = True
                        self.save()
                    else:
                        self.operation(dict(op='freeze'), self.root)
        return dict(candidate=candidate, results=results, cached=cached,
                    vs_original=compare(results[self.candidates.base_id]['scored'], target['scored']),
                    vs_parent=compare(results[cm['parent'] or self.candidates.base_id]['scored'], target['scored']))

    def accept(self, candidate):
        ids = list(self.evidence.records)
        def full(c):
            key = digest(packed(dict(candidate=c, ids=ids, protocol=self.protocol)))
            if key not in self.state['evaluations']:
                raise ValueError('Full fixed development evaluation required before accept/freeze')
            return self.cached(key)
        base, current, new = (full(c) for c in (self.candidates.base_id, self.state['best'], candidate))
        if repair_score(new['scored']) is None:
            raise ValueError('Missing multi-wording joint endpoint')
        n = len(new['scored'])
        if max(new['summary']['format_errors'], new['summary']['truncated']) / n > self.contract['max_format_rate']:
            raise ValueError('Format/truncation protection failed')
        conditions = self.contract['protection_conditions']
        if not conditions:
            raise ValueError('Protection conditions must be frozen before search')
        for key, a in base['summary']['cells'].items():
            if key.rsplit(':', 1)[-1] not in conditions:
                continue
            b = new['summary']['cells'][key]
            if a['n'] != b['n'] or (a['correct']-b['correct'])/a['n'] > self.contract['max_protection_drop']:
                raise ValueError('Protection failed in wording/order/prompt cell: ' + key)
        before, after = repair_score(current['scored']), repair_score(new['scored'])
        old_count = self.candidates.manifest(self.state['best'])['changed_scalars']
        count = self.candidates.manifest(candidate)['changed_scalars']
        if after < before or (after == before and count > old_count):
            raise ValueError('Candidate does not improve the frozen selection rule')
        self.state['best'] = candidate
        self.save()
        return dict(best=candidate, repair_score=after, development_only=True, independent_confirmation=False)

    def operation(self, req, attempt):
        op = req['op']
        if op == 'mechanism_report':
            report = req['report']
            for key in ('candidate','failure_behavior','internal_evidence','causal_tests','counterevidence','scope','verdict'):
                if not isinstance(report.get(key),str) or not report[key].strip():
                    raise ValueError('Mechanism report requires '+key)
            self.candidates.manifest(report['candidate'])
            self.check_evidence_actions(report.get('action_ids',[]), require_capture=False)
            write_json(self.root/'mechanism-report.json',dict(report=report,independent_review=False,
                automated_mechanism_validation=False, independent_confirmation=False))
            return dict(recorded=True, scientific_review_required=True)
        if op == 'evidence':
            return dict(rows=self.evidence.view(req.get('ids')))
        if op == 'image':
            path = self.evidence.image(req['request_id'], req.get('kind', 'input'))
            return dict(image=path.relative_to(self.evidence.root).as_posix(), request_id=req['request_id'])
        if op == 'catalog':
            return dict(parameters=self.candidates.source.catalog())
        if op == 'runtime_catalog':
            return self.backend.catalog()
        if op in ('measure', 'diagnose'):
            candidate = req.get('candidate', self.state['current'])
            self.candidates.manifest(candidate)
            records = self.evidence.select(req['ids'])
            if len(records) > self.contract.get('max_measure_batch',64):
                raise ValueError('Diagnostic batch exceeds frozen cap')
            results = []
            for row in records:
                self.reserve_forward()
                path = attempt/f'measure-{len(results):04d}.json'
                write_json(path, dict(status='started', request_id=row['input']['request_id'], candidate=candidate))
                try:
                    request = dict(row['input'])
                    if 'text_overrides' in req:
                        text = req['text_overrides'].get(request['request_id'], request['text'])
                        if not isinstance(text,str) or not text.strip():
                            raise ValueError('Invalid diagnostic question')
                        request['text'] = text
                    r = self.backend.measure(request, self.candidates, candidate, req.get('spec', {}))
                    self.record_cost(r)
                    if self.contract.get('binary_captures'):
                        import numpy as np
                        for index, capture in enumerate(r.get('captures', [])):
                            values = np.asarray(capture.pop('values'), dtype=np.float32)
                            rel = f"{attempt.name}-sample-{len(results):04d}-capture-{index:04d}.npy"
                            np.save(self.root/'artifacts'/rel, values, allow_pickle=False)
                            capture.update(array_file=rel, array_sha256=file_hash(self.root/'artifacts'/rel),
                                           values_count=int(values.size))
                    if op == 'diagnose':
                        self.reserve_forward()
                        generated = self.backend.generate(request,self.candidates,candidate,self.remaining())
                        self.record_cost(generated)
                        r['diagnostic_generation'] = generated
                    r['diagnostic_text_override'] = request['text'] if 'text_overrides' in req else None
                    r = dict(r, request_id=row['input']['request_id'])
                    write_json(path, dict(status='complete', result=r))
                    results.append(r)
                except Exception as e:
                    write_json(path, dict(status='failed', request_id=row['input']['request_id'], error=repr(e)))
                    raise
            return dict(results=results, never_used_for_best_selection=True)
        if op == 'commit':
            if req['parent'] != self.state['current']:
                raise ValueError('Staged edits must name the checked-out parent')
            if self.contract.get('targeted'):
                evidence = req.get('evidence',{})
                for key in ('failure_behavior','component_hypothesis','expected_change','dose','control_plan'):
                    if not isinstance(evidence.get(key),str) or not evidence[key].strip():
                        raise ValueError('Commit needs prior evidence/prediction field: '+key)
                ids = evidence.get('contrast_ids',[])
                if len(set(ids))<2:
                    raise ValueError('Give success/failure or otherwise comparable diagnostic input IDs')
                self.evidence.select(ids)
                role = evidence.get('role','targeted')
                if role not in ('targeted','diagnostic','control'):
                    raise ValueError('Invalid evidence role')
                self.check_evidence_actions(evidence.get('measurement_actions',[]),require_capture=role=='targeted')
                write_json(attempt/'prior-evidence.json',dict(evidence=evidence,scientific_validation=False))
            edits = collect_staged(self.root/'work', self.candidates.source)
            names = set(self.candidates.manifest(req['parent'])['tensors']) | {self.candidates.source.canonical(n) for n in edits}
            estimated = self.contract['temporary_scalars']*12 + len(names)*4096
            if shutil.disk_usage(self.root).free < estimated + 20*1024**3:
                raise ValueError('Insufficient disk reserve for candidate; do not discard existing evidence')
            m = self.candidates.commit(req['parent'], edits, req['rationale'])
            self.state['current'] = m['id']
            if self.contract.get('targeted'):
                write_json(self.root/'artifacts'/(m['id']+'-evidence.json'),dict(evidence=evidence,commit_action=attempt.name,
                    label='researcher_hypothesis_not_validated_mechanism'))
            write_json(self.root/'work/stage.json', {})
            self.save()
            return m
        if op == 'checkout':
            m = self.candidates.manifest(req['candidate'])
            self.state['current'] = m['id']
            # Stage files remain archived in work; the manifest no longer selects them.
            write_json(self.root/'work/stage.json', {})
            self.save()
            return dict(current=m['id'], staging_cleared=True, python_variables_may_be_stale=True)
        if op == 'evaluate':
            return self.evaluate(req)
        if op == 'accept':
            return self.accept(req['candidate'])
        if op == 'freeze':
            if self.contract.get('targeted'):
                report_path = self.root/'mechanism-report.json'
                if not report_path.exists():
                    raise ValueError('Submit mechanism_report, including negative/unsupported findings, before freeze')
                report = json.loads(report_path.read_text())
                if report['report']['candidate'] != self.state['best']:
                    raise ValueError('Mechanism report must describe the actually selected best candidate')
            candidate = self.state['best']
            self.accept(candidate)
            m = self.candidates.freeze(candidate)
            write_json(self.root/'frozen-candidate.json', dict(manifest=m, protocol=self.protocol,
                contract=self.contract, status='development_selection_only_pending_reload_and_new_confirmation'))
            self.state['frozen'] = candidate
            self.state['research_done'] = True
            self.save()
            return dict(frozen=candidate, independent_confirmation=False)
        if op == 'stop':
            self.state['research_done'] = True
            self.save()
            return dict(stopped=True, reason=req['reason'], successful_patch_required=False)
        if op == 'status':
            return dict(state=self.state, seconds_left=None if math.isinf(self.remaining()) else self.remaining(), repair_round_target=self.contract.get('repair_rounds'))
        if op == 'artifact':
            # Only previously returned artifacts, no arbitrary filesystem reader.
            name = req['name']
            path = inside(self.root/'artifacts', name)
            if path.suffix not in ('.json', '.txt') or not path.is_file():
                raise ValueError('Unknown artifact')
            text = path.read_text()
            start, length = req.get('offset', 0), req.get('length', 12000)
            if type(start) is not int or start < 0 or type(length) is not int or not 0 < length <= 12000:
                raise ValueError('Invalid artifact page')
            return dict(text=text[start:start+length], offset=start, total_characters=len(text))
        raise ValueError('Unknown operation: ' + str(op))

    def check_evidence_actions(self, ids, require_capture):
        found = False
        for ident in ids:
            if not isinstance(ident,str) or not ident or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_' for c in ident):
                raise ValueError('Invalid evidence action ID')
            p = self.root/'actions'/ident
            request = json.loads((p/'request.json').read_text())
            response = json.loads((p/'response.json').read_text())
            if response['failed']:
                raise ValueError('Failed action cannot be cited as successful measurement')
            if request.get('kind')=='forward' and request['request']['op'] in ('measure','diagnose'):
                found |= any(r.get('captures') for r in response['value']['results'])
        if require_capture and not found:
            raise ValueError('Targeted candidate needs recorded internal captures; exploratory edits must be labeled diagnostic')

    def storage_guard(self):
        if not self.contract.get('max_run_bytes'):
            return
        allocated = {}
        for p in self.root.rglob('*'):
            if p.is_file() and not p.is_symlink():
                st = p.stat(); allocated[(st.st_dev,st.st_ino)] = st.st_blocks*512
        used = sum(allocated.values())
        self.state['storage_bytes'] = used
        # Reserve worst-case next bounded capture; retain an additional filesystem margin.
        reserve = self.contract['max_measure_batch']*self.contract['max_measure_elements']*4 + 128*1024**2
        if used+reserve > self.contract['max_run_bytes'] or shutil.disk_usage(self.root).free < reserve+self.contract['minimum_free_bytes']:
            raise ValueError('Storage budget exhausted; preserve evidence and stop, never delete candidates automatically')

    def dispatch(self, action):
        ident = action.get('id', '')
        if not ident or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_' for c in ident):
            raise ValueError('Invalid action ID')
        folder = self.root/'actions'/ident
        identity = digest(packed(action))
        if folder.exists():
            if (folder/'request.sha256').read_text() != identity:
                raise ValueError('Action ID reused with different content')
            if not (folder/'response.json').exists():
                raise RuntimeError('INCOMPLETE_ACTION: do not replay')
            return json.loads((folder/'response.json').read_text())
        if any(not (p/'response.json').exists() for p in (self.root/'actions').iterdir()):
            raise RuntimeError('INCOMPLETE_ACTION: reconcile previous attempt first')
        if self.state['research_done'] or self.state['actions'] >= self.contract['actions'] or self.remaining() <= 0:
            raise RuntimeError('Session stopped or budget exhausted')
        folder.mkdir()
        (folder/'request.sha256').write_text(identity)
        write_json(folder/'request.json', action)
        self.state['actions'] += 1
        self.save()
        started = time.monotonic()
        try:
            if action['kind']=='python' or action.get('request',{}).get('op') in ('commit','measure','diagnose','evaluate'):
                self.storage_guard()
            if action['kind'] == 'python':
                seconds = min(300, self.contract['python_seconds']-self.state['python_seconds'], self.remaining())
                if seconds <= 0: raise ValueError('CPU budget exhausted')
                try:
                    value = self.kernel.call(action['code'], seconds)
                finally:
                    self.state['python_seconds'] += time.monotonic()-started
                    self.save()
                # Preserve proposal values at every action boundary, including failed Python.
                import numpy as np
                try:
                    staged = collect_staged(self.root/'work', self.candidates.source)
                    archive = folder/'proposal'; archive.mkdir()
                    manifest = {}
                    for name, array in staged.items():
                        filename = digest(name.encode())+'.npz'
                        manifest[name] = save_sparse(archive/filename, self.candidates.source.load(name), array)
                    write_json(archive/'manifest.json', manifest)
                except Exception as exc:
                    value['proposal_archive_error'] = repr(exc)
                    value['failed'] = True
                if value['failed']:
                    result = dict(failed=True, value=value)
                else:
                    result = dict(failed=False, value=value)
            elif action['kind'] == 'forward':
                result = dict(failed=False, value=self.operation(action['request'], folder))
            else:
                raise ValueError('Only researcher Python or observer forward requests allowed')
        except Exception as e:
            result = dict(failed=True, error=repr(e))
        result.update(id=ident, elapsed_seconds=time.monotonic()-started, budget={k:v for k,v in self.state.items() if k != 'evaluations'})
        write_json(folder/'response.json', result)
        # Preserve full feedback, paginate for context; never silently ASCII-replace it.
        artifact = ident + '.json'
        write_json(self.root/'artifacts'/artifact, result)
        return result

    def close(self):
        self.kernel.close()
        self.lock.close()
