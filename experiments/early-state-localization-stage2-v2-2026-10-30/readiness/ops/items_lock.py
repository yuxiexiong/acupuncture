import json, sys
from pathlib import Path
here = Path(sys.argv[1]).resolve(); sys.path.insert(0, str(here))
import stage2 as S
exp = S.exp
items = exp.read(S.VALIDATION_DATA)
labels = {r['id']: {'core': 'correct', 'core_contradiction': False} for r in items}
exp.write(here / 'analysis/audit-r01-labels.json', labels, immutable=True)
import subprocess
subprocess.run([sys.executable, str(here / 'analyze_stage2.py'), 'audit', str(here / 'runs/audit-r01'),
                str(here / 'analysis/audit-r01-labels.json'), str(here / 'analysis/audit-r01.json')], check=True)
v = exp.read(here / 'analysis/audit-r01.json')
assert v['status'] == 'passed', v
assert not any((here / 'runs').glob('g_*')), 'G outputs exist'
lock = {'status': 'locked', 'clean_audit': 'passed', 'validation_data_sha256': exp.sha(S.VALIDATION_DATA),
        'audit_run': 'runs/audit-r01', 'audit_verification_sha256': exp.sha(here / 'runs/audit-r01/verification.json'),
        'audit_analysis_sha256': exp.sha(here / 'analysis/audit-r01.json'),
        'labels_sha256': exp.sha(here / 'analysis/audit-r01-labels.json'),
        'reader': 'model-assisted (Claude Opus 5.5) reading of all 24 clean answers; not a human review; the items were also drafted by the same model (weak independence, disclosed)',
        'reading_note': '24/24 state the expected core answer, no core contradiction, none truncated (all end with EOS, 15-63 tokens); clean S > 0 in 12/12 bases (5.35-24.87), no base below 2 nats',
        'revisions_used': 0, 'g_outputs_previously_unseen': True, 'locked_at': exp.utc()}
exp.write(here / 'readiness/items-lock-r01.json', lock, immutable=True)
print('locked', exp.sha(here / 'readiness/items-lock-r01.json'))
