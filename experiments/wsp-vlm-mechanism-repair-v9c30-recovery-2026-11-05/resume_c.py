"""User-authorized C-only recovery after a proven pre-action capacity failure."""
import json
import os
from pathlib import Path
import sys
import time

HERE = Path(__file__).resolve().parent
OLD = HERE.parent / 'wsp-vlm-mechanism-repair-v9-2026-11-05'
sys.path.insert(0, str(OLD))
from common import file_hash, write_json
from controller import CodexResearcher, run_session
from run_rounds import Remote, ssh_python


def validate(remote, events, receipt):
    state = remote['state']
    if (state['repair_rounds_completed'] != 26 or state['research_done'] or
            state.get('frozen') or remote['pending'] or remote['incomplete'] or
            remote['failed_action_exists'] or remote['amendment_exists']):
        raise ValueError('Recovery boundary changed; inspect without replay')
    if not remote['alive'] or not remote['code_matches'] or remote['last_action'] != 'turn-0142':
        raise ValueError('Original broker, code, or last action mismatch')
    if remote['last_response'] != remote['expected_response']:
        raise ValueError('Last feedback differs from durable remote response')
    if any(e.get('item', {}).get('type') not in (None, 'error') for e in events):
        raise ValueError('Failed researcher turn contains an unexpected item')
    if any(e['type'] == 'turn.completed' for e in events):
        raise ValueError('Failed turn actually completed')
    if not any(e['type'] == 'turn.failed' and e.get('error', {}).get('message') ==
               'Selected model is at capacity. Please try a different model.' for e in events):
        raise ValueError('Not the audited capacity failure')
    if [e['thread_id'] for e in events if e['type'] == 'thread.started'] != [receipt['thread']]:
        raise ValueError('Researcher thread mismatch')


def main():
    local = OLD / 'search-C'
    failed = local / 'conversation/turn-0143'
    last = local / 'conversation/turn-0142'
    cfg = json.loads((local / 'local_config.json').read_text())
    receipt = json.loads((last / 'receipt.json').read_text())
    events = [json.loads(line) for line in (failed / 'events.jsonl').read_text().splitlines()]
    assert sorted((local / 'conversation').glob('turn-*'))[-1] == failed
    assert cfg['contract']['repair_rounds'] == 30
    assert json.loads((OLD / 'supervisor-C.json').read_text())['status'] == 'failed'
    for pid in (53327, 53329, 79120):
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            continue
        raise RuntimeError('Old C controller/waiter still exists')
    hashes = json.loads((OLD / 'audit/engineering-C-r02/receipt.json').read_text())['code_sha256']
    assert all(file_hash(OLD / name) == digest for name, digest in hashes.items())
    code = """import json,sys,pathlib,hashlib
x=json.load(sys.stdin);r=pathlib.Path(x['root']);source=pathlib.Path(x['source']);p=pathlib.Path('/proc/1852016/cmdline')
response=json.loads((r/'actions/turn-0142/response.json').read_text())
print(json.dumps(dict(state=json.loads((r/'state.json').read_text()),
 alive=p.exists() and b'round_broker.py' in p.read_bytes() and b'config-C.json' in p.read_bytes(),
 code_matches=all(hashlib.sha256((source/n).read_bytes()).hexdigest()==h for n,h in x['hashes'].items()),
 last_action=sorted(q.name for q in (r/'actions').iterdir())[-1],last_response=response,
 expected_response=x['response'],failed_action_exists=(r/'inbox/turn-0143.json').exists() or (r/'actions/turn-0143').exists(),
 pending=[p.name for p in (r/'inbox').glob('*.json') if not (r/'actions'/p.stem/'response.json').exists()],
 incomplete=[p.name for p in (r/'actions').iterdir() if not (p/'response.json').exists()],
 amendment_exists=(r/'round-limit-amendment.json').exists())))"""
    remote = ssh_python(code, dict(root=cfg['run_root'], source='/workspace/acupuncture/experiments/'+OLD.name,
                                  hashes=hashes, response=json.loads((last / 'tool_result.json').read_text())))
    validate(remote, events, receipt)
    write_json(HERE / 'preflight.json', dict(passed=True, time_unix=time.time(), round=26,
               broker_pid=1852016, thread=receipt['thread'], code_sha256=hashes,
               no_pending_actions=True, capacity_failure_before_action=True, target=30))
    service = Remote(cfg, 'C', local, 1852016)
    researcher = CodexResearcher(cfg, local / 'researcher-capacity-recovery-r1')
    researcher.thread = receipt['thread']
    researcher.used_turns = 143  # Count the failed attempt; keep its directory intact.
    researcher.previous_usage = receipt['usage']
    researcher.used_tokens = receipt['cumulative_tokens']
    prompt = ('User explicitly authorized resuming ONLY C to 30 total completed candidates, then '
              'mechanism_report and freeze. The previous 50-round C continuation is cancelled. '
              '26 candidates are complete; finish four more, not 30 new ones. Same thread, '
              'contract, baseline, code and live broker/Python kernel are preserved. The capacity-failed '
              'turn143 produced no answer or action and is retained; this is turn144. '
              'Do not replay turn142: its Python exception and partial namespace remain. Inspect '
              'and correct your own analysis using its saved feedback. No edit choices are prescribed. '
              'Usage through turn142 is retained; failed turn143 has no usage receipt.\n\n' +
              json.loads((failed / 'input.json').read_text())['prompt'])
    write_json(HERE / 'status.json', dict(status='running', pid=os.getpid(), broker_pid=1852016,
               thread=researcher.thread, target=30, start_turn=144, failed_turn_usage_unknown=True,
               started_unix=time.time()))
    result = run_session(service, researcher, local / 'conversation', prompt, start_turn=144, resuming=True)
    write_json(HERE / 'receipt.json', result)
    write_json(HERE / 'status.json', dict(status='completed_or_early_stopped', target=30,
               rounds=service.state['repair_rounds_completed'], result=result, time_unix=time.time()))


if __name__ == '__main__':
    with (HERE / 'launch-once.json').open('x') as f:
        json.dump(dict(pid=os.getpid(), time_unix=time.time()), f)
    try:
        main()
    except Exception as exc:
        write_json(HERE / 'failure.json', dict(error=repr(exc), time_unix=time.time()))
        raise
