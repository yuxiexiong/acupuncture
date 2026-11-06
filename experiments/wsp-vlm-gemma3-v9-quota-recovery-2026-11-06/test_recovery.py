import ast,json,gzip
from pathlib import Path
p=Path(__file__).resolve().parent
module=ast.parse((p/'resume_C.py').read_text())
ns={};exec(compile(ast.Module(body=[n for n in module.body if isinstance(n,ast.FunctionDef) and n.name in ['validate','validate_failure','shared_capacity']],type_ignores=[]),'<boundary>','exec'),ns)
s=json.loads(gzip.decompress((p/'preflight.json.gz').read_bytes()))['tasks']['C']['state']
r={'failed':False,'budget':{'actions':s['actions']}}
ns['validate'](s,r,[],[],s)
for pending,incomplete in [(['pending'],[]),([],['partial'])]:
 try:ns['validate'](s,r,pending,incomplete,s)
 except ValueError:pass
 else:raise AssertionError('Uncertain action accepted')
e=[json.loads(x) for x in (p/'C-failed-turn-0099/events.jsonl').read_text().splitlines()]
ns['validate_failure'](e,False)
for bad,receipt in [(e,True),(e+[{'type':'turn.completed'}],False),(e+[{'type':'item.completed','item':{'type':'agent_message'}}],False)]:
 try:ns['validate_failure'](bad,receipt)
 except ValueError:pass
 else:raise AssertionError('Uncertain researcher accepted')
f=ns['shared_capacity'];assert f(80000,[2372133],True) and f(80000,[],True)
assert not f(50000,[2372133],True) and not f(80000,[999],True) and not f(80000,[2372133],False)
print('PASS: exact boundary, no replay, failed response, shared admission')
