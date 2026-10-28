"""Compact, hash-checked export of formal records for Git: raw text, tokens, stop, candidate scores.

python analysis/export_answers.py RUN_DIR OUT.jsonl.zst
Full raw records (with all step readouts) stay in the run directory and its verified archive.
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path


def main(run, out):
    run = Path(run)
    lines = []
    for receipt_path in sorted(run.glob('worker-*/receipt.json')):
        worker = receipt_path.parent
        receipt = json.loads(receipt_path.read_text())
        for relative, digest in sorted(receipt['record_hashes'].items()):
            data = (worker / relative).read_bytes()
            assert hashlib.sha256(data).hexdigest() == digest, relative
            row = json.loads(data)
            g = row.get('generation') or {}
            first = (g.get('step_readouts') or [{}])[0]
            cond = {k: v for k, v in row['effective_condition'].items() if k != 'vector'}
            lines.append({'worker': worker.name, 'record': relative, 'record_sha256': digest, 'key': row['spec']['key'],
                'spec': {k: v for k, v in row['spec'].items() if k != 'condition'}, 'condition': cond,
                'item_id': row['item_id'], 'status': row['status'], 'reason': row.get('reason'),
                'answer_text': g.get('answer_text'), 'raw_text': g.get('raw_text'), 'token_ids': g.get('token_ids'),
                'end_reason': g.get('end_reason'), 'forced_prefix_tokens': g.get('forced_prefix_tokens'),
                'first_step': {'actual_token_id': first.get('actual_token_id'), 'actual_logprob': first.get('actual_logprob'),
                               'stop_advantage': first.get('stop_advantage'), 'top5': (first.get('top32') or [])[:5]},
                'stop_advantage_by_step': [r.get('stop_advantage') for r in g.get('step_readouts') or []],
                'candidates': [{'text': c['text'], 'loglikelihood': c['result']['loglikelihood'],
                                'token_logprobs': c['result']['token_logprobs']} for c in row.get('candidates', [])]})
    payload = ''.join(json.dumps(l, ensure_ascii=False) + '\n' for l in lines).encode()
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    assert not Path(out).exists()
    subprocess.run(['zstd', '-19', '-q', '-o', str(out)], input=payload, check=True)
    print(len(lines), 'rows', hashlib.sha256(payload).hexdigest())


if __name__ == '__main__':
    main(*sys.argv[1:3])
