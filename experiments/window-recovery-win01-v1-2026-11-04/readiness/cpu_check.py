"""WIN-01 CPU readiness: run test_win on CPU and write readiness/cpu-r01.json with source hashes (via the project exp.write).
python readiness/cpu_check.py OUT_NAME"""
import os
import sys
import unittest
from pathlib import Path

os.environ['CUDA_VISIBLE_DEVICES'] = ''
HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
os.chdir(HERE)
import win_run as WR  # noqa: E402

suite = unittest.defaultTestLoader.loadTestsFromName('test_win')
res = unittest.TextTestRunner(verbosity=1).run(suite)
srcs = sorted(HERE.glob('*.py')) + [HERE / 'CONTRACT.zh-CN.md', HERE / 'DECISIONS.zh-CN.md', HERE / 'prep/tokens.json']
receipt = {'status': 'passed' if res.wasSuccessful() else 'failed', 'tests_run': res.testsRun, 'failures': len(res.failures),
           'errors': len(res.errors), 'created_at': WR.exp.utc(),
           'source_hashes': {str(p.relative_to(WR.REPO)): WR.exp.sha(p) for p in srcs}}
out = HERE / 'readiness' / sys.argv[1]
WR.exp.write(out, receipt, immutable=True)
print(receipt['status'], receipt['tests_run'], receipt['failures'], receipt['errors'])
sys.exit(0 if res.wasSuccessful() else 1)
