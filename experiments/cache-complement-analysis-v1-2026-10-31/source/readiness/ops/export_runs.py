"""Export compact answer files (jsonl.zst) for every stage2 run; records are re-verified against receipt hashes."""
import hashlib, json, subprocess, sys
from pathlib import Path
here = Path(sys.argv[1]); out = here / 'exports'; out.mkdir(exist_ok=True)
summary = {}
for run in sorted((here / 'runs').iterdir()):
    rows = []
    for receipt in sorted(run.glob('worker-*/receipt.json')):
        for rel, digest in json.loads(receipt.read_text())['record_hashes'].items():
            p = receipt.parent / rel; b = p.read_bytes()
            assert hashlib.sha256(b).hexdigest() == digest, p
            r = json.loads(b); g = r['generation']; s = r['spec']
            rows.append({'key': s['key'], 'run': run.name, 'worker': receipt.parent.name, 'record_sha256': digest,
                         'item_id': r['item']['id'], 'base_id': r['item']['base_id'], 'condition_id': s['condition_id'],
                         'arm': s['arm'], 'background': s['background'], 'group': s['group'], 'subset': s['subset'],
                         'direction': s['direction'], 'code': s['code'], 'roles': s['roles'],
                         'token_ids': g['token_ids'], 'answer_text': g['answer_text'], 'end_reason': g['end_reason'],
                         'generated_tokens': g['generated_tokens'], 'first_step_eos': g['first_step_eos'],
                         'first_eos_position': g['first_eos_position'], 'stop_advantage_steps': g['stop_advantage_steps'],
                         'candidates': [{'text': c['text'], 'loglikelihood': c['loglikelihood'], 'token_logprobs': c['token_logprobs']} for c in r['candidates']]})
    rows.sort(key=lambda x: x['key'])
    data = ''.join(json.dumps(x, ensure_ascii=False) + '\n' for x in rows).encode()
    dst = out / f'{run.name}-answers.jsonl.zst'
    assert not dst.exists()
    dst.write_bytes(subprocess.run(['zstd', '-19', '-q', '-c'], input=data, capture_output=True, check=True).stdout)
    summary[run.name] = {'records': len(rows), 'export': dst.name, 'export_sha256': hashlib.sha256(dst.read_bytes()).hexdigest(),
                         'uncompressed_sha256': hashlib.sha256(data).hexdigest()}
    print(run.name, len(rows), dst.stat().st_size)
(out / 'exports-manifest.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
