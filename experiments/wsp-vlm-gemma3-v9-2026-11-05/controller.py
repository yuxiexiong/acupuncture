"""Open research loop adapted from math engineering-r2/controller.py.

No prewritten neuron selection or edit schedule. The researcher supplies Python
or JSON actions; all outputs are fed back. This file has no execution entry point.
"""
import json
import subprocess
import time
import os
from pathlib import Path

from common import legacy, packed, write_json, file_hash, require_live


def parse_action(text):
    old = legacy('wsp-process-reproduction-v1-2026-11-03/engineering-r2/controller.py', 'math_open_controller')
    return old.parse_action(text, explanations=True)


class CodexResearcher:
    """Explicitly authorized future transport; offline tests supply ScriptedResearcher.

    Image CLI flags verified using exec/resume --help only. No live call performed.
    A provider/account spend cap is required: CLI usage events are not invoices.
    """
    def __init__(self, config, root):
        require_live(config)
        self.subscription = config.get('researcher_billing') == 'existing_chatgpt'
        if not self.subscription and not config.get('researcher_external_spend_cap_record'):
            raise PermissionError('External researcher spend cap not recorded')
        self.config, self.root = config, Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=False)
        self.thread = None
        self.used_turns, self.reserved_usd = 0, 0.
        self.used_tokens = 0
        self.previous_usage = {}
        if file_hash(config['researcher_cli']) != config['researcher_cli_sha256']:
            raise ValueError('Researcher CLI build changed')
        (self.root/'instructions.txt').write_text('Answer the research request. Use only the fenced action protocol.\n')
        if self.subscription:
            login = subprocess.run([config['researcher_cli'], 'login', 'status'], capture_output=True, text=True)
            if login.returncode or 'Logged in using ChatGPT' not in login.stdout + login.stderr:
                raise PermissionError('Expected existing ChatGPT login; no API fallback')

    def turn(self, prompt, images, out):
        c, contract = self.config, self.config['contract']
        if self.used_turns >= contract['researcher_turns'] or (not self.subscription and self.reserved_usd + contract['researcher_turn_reserve_usd'] > contract['researcher_usd']):
            raise ValueError('Researcher turn/cost reservation exhausted')
        if self.subscription and self.used_tokens >= contract['researcher_tokens']:
            raise ValueError('Researcher token budget reached; one-turn usage overshoot possible')
        out.mkdir(exist_ok=False)
        self.used_turns += 1
        if not self.subscription:
            self.reserved_usd += contract['researcher_turn_reserve_usd']
        write_json(out/'input.json', dict(prompt=prompt, images=[dict(name=p.name, sha256=file_hash(p)) for p in images],
                                        thread=self.thread, reserved_usd=self.reserved_usd))
        (out/'prompt.txt').write_text(prompt)
        cmd = [c['researcher_cli'], 'exec', '--ignore-user-config', '--ignore-rules', '--strict-config',
               '--skip-git-repo-check', '--json', '-s', 'read-only', '-C', str(self.root),
               '-m', c['researcher_model'], '-c', 'model_reasoning_effort="max"',
               '-c', 'project_doc_max_bytes=0', '-c', 'web_search="disabled"',
               '-c', 'model_instructions_file='+json.dumps(str(self.root/'instructions.txt'))]
        if self.subscription:
            cmd += ['-c', 'forced_login_method="chatgpt"']
        for feature in ('shell_tool', 'code_mode', 'code_mode_host', 'apps', 'plugins', 'hooks', 'memories',
                        'multi_agent', 'browser_use', 'computer_use', 'image_generation', 'view_image',
                        'skill_search', 'goals', 'artifact'):
            cmd += ['--disable', feature]
        for feature in ('skip_host_skill_discovery', 'omit_skill_descriptions'):
            cmd += ['--enable', feature]
        if self.thread:
            cmd += ['resume', self.thread]
        for path in images:
            cmd += ['--image', str(path.resolve())]
        cmd += ['-']
        write_json(out/'command.json', cmd)
        started = time.monotonic()
        environment = dict(os.environ)
        if self.subscription:
            for key in ('OPENAI_API_KEY', 'CODEX_API_KEY'):
                environment.pop(key, None)
        with (out/'events.jsonl').open('w') as stdout, (out/'stderr.txt').open('w') as stderr:
            p = subprocess.run(cmd, input=prompt, text=True, stdout=stdout, stderr=stderr,
                               timeout=c['researcher_turn_seconds'] if contract['wall_seconds'] is None else min(contract['wall_seconds'], c['researcher_turn_seconds']), env=environment)
        events = [json.loads(x) for x in (out/'events.jsonl').read_text().splitlines()]
        replies, usage, thread = [], None, None
        for e in events:
            if e['type'] == 'thread.started': thread = e['thread_id']
            if e['type'] == 'turn.completed': usage = e.get('usage')
            item = e.get('item', {})
            if item.get('type') not in (None, 'agent_message', 'reasoning', 'error'):
                raise RuntimeError('Unexpected native tool event; stop researcher')
            if e['type'] == 'item.completed' and item.get('type') == 'agent_message':
                replies.append(item['text'])
        if p.returncode or not replies or usage is None or not thread or (self.thread and thread != self.thread):
            raise RuntimeError('Researcher failed/uncertain; no automatic paid retry')
        self.thread = thread
        if c.get('researcher_usage_mode') == 'thread_cumulative':
            delta = {k:usage.get(k,0)-self.previous_usage.get(k,0) for k in ('input_tokens','output_tokens','cached_input_tokens')}
            if any(v<0 for v in delta.values()):
                raise RuntimeError('Nonmonotonic cumulative usage; reconcile before continuing')
            self.previous_usage = dict(usage)
        else:
            delta = usage
        self.used_tokens += delta.get('input_tokens', 0) + delta.get('output_tokens', 0)
        receipt = dict(thread=thread, usage=usage, usage_delta=delta, usage_mode=c.get('researcher_usage_mode','per_turn'), elapsed_seconds=time.monotonic()-started,
                       reserved_usd=self.reserved_usd, cost_is_reservation_not_invoice=True)
        receipt.update(billing='existing_chatgpt' if self.subscription else 'metered',
                       cumulative_tokens=self.used_tokens, monetary_cost_unknown=self.subscription)
        write_json(out/'receipt.json', receipt)
        (out/'reply.txt').write_text(replies[-1])
        return replies[-1]


def run_session(service, researcher, out, instructions, start_turn=1, resuming=False):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=resuming)
    prompt, images = instructions, []
    for turn in range(start_turn, service.contract['researcher_turns'] + 1):
        if service.remaining() <= 0:
            raise TimeoutError('Session wall budget exhausted')
        folder = out/f'turn-{turn:04d}'
        reply = researcher.turn(prompt, images, folder)
        # Fakes also get full transcript persistence from the observer.
        folder.mkdir(exist_ok=True)
        (folder/'reply.txt').write_text(reply)
        (folder/'feedback_received.txt').write_text(prompt)
        images = []
        try:
            action = parse_action(reply)
        except (ValueError, json.JSONDecodeError) as e:
            prompt = 'Action not executed: '+str(e)+'. Give one action with explanation, or finish honestly.'
            write_json(folder/'rejected.json', dict(error=str(e)))
            continue
        if action is None:
            # Unlike the old controller: no forced 50-pass completion and no implied successful patch.
            receipt = dict(status='researcher_stopped', turns=turn, best=service.state['best'],
                           frozen=service.state['frozen'], independent_confirmation=False)
            service.state['research_done'] = True
            service.save()
            write_json(out/'receipt.json', receipt)
            return receipt
        action['id'] = f'turn-{turn:04d}'
        result = service.dispatch(action)
        write_json(folder/'tool_result.json', result)
        if action['kind']=='forward' and action['request']['op']=='image' and not result['failed']:
            req = action['request']
            images = [service.evidence.image(req['request_id'], req.get('kind', 'input'))]
        serialized = packed(result).decode()
        prompt = serialized if len(serialized) <= 16000 else (
            serialized[:16000] + '\n[PREVIEW TRUNCATED: full result in ARTIFACTS/'+action['id']+
            '.json; use Python or forward op=artifact to inspect all evidence. Do not infer omitted results.]')
        if service.state['research_done']:
            receipt = dict(status='stopped_or_frozen', turns=turn, best=service.state['best'],
                           frozen=service.state['frozen'], independent_confirmation=False)
            write_json(out/'receipt.json', receipt)
            return receipt
    receipt = dict(status='turn_budget_exhausted', best=service.state['best'], independent_confirmation=False)
    write_json(out/'receipt.json', receipt)
    return receipt
