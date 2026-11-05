"""CPU regression for the only permitted retry: documented zero-attempt P0 startup."""
import ast, hashlib, json, tempfile
from pathlib import Path
source=Path(__file__).with_name('runner.py').read_text()
node=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name=='check_stage_recovery')
ns=dict(json=json,sha=lambda b:hashlib.sha256(b).hexdigest())
exec(compile(ast.Module(body=[node],type_ignores=[]),'<recovery guard>','exec'),ns)
check=ns['check_stage_recovery']
with tempfile.TemporaryDirectory() as d:
 root=Path(d);check(root,'B','P0')
 p=root/'P0_failed_01'/'receipt.json';p.parent.mkdir()
 base=dict(task='B',stage='P0',status='failed',attempts=0,elapsed_seconds=4.872829316183925)
 def save(r,approve=True):
  p.write_text(json.dumps(r))
  (root/'recovery-P0-zero-attempt.json').write_text(json.dumps(dict(receipt_sha256=[ns['sha'](p.read_bytes())] if approve else [])))
 def rejected(stage='P0'):
  try:check(root,'B',stage)
  except RuntimeError:return
  raise AssertionError('unsafe retry allowed')
 save(base,False);rejected()
 save(base);check(root,'B','P0')
 for change in (dict(attempts=1),dict(status='complete'),dict(status='running'),dict(stage='D')):
  save(dict(base,**change));rejected(change.get('stage','P0'))
 save(base);p.write_text(p.read_text()+' ');rejected()
 save(base);p.parent.rename(root/'P0');rejected()
print('PASS: explicit zero-attempt P0 recovery; completed/partial/formal/unapproved/tampered/unarchived attempts rejected; no model imports')
