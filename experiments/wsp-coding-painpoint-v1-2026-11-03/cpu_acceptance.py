"""Meaningful trust-boundary and scoring fixtures; no model or editor calls."""
import json
from pathlib import Path
import time
from isolated import score, ROOT
from scoring import extract
from score_batch import aggregate, score_rows


def main():
    rows = []
    def check(name, request, predicate, timeout=60):
        result = score(request, timeout)
        row = dict(name=name, result=result, passed=bool(predicate(result)))
        rows.append(row)
        (ROOT/'receipts/cpu-acceptance.json').write_text(json.dumps(rows, indent=2)+'\n')
        if not row['passed']:
            raise AssertionError(row)
    probe = '''import os, socket, resource
checks = dict(uid=os.getuid()==65534, gid=os.getgid()==65534,
 no_model=not os.path.exists('/workspace/acupuncture/external/wsp/text-Qwen3.5-0.8B'),
 no_data=not os.path.exists('/workspace/acupuncture/external/wcp01/sources'),
 no_credentials=not os.path.exists('/root/.ssh'), no_gpu=not os.path.exists('/dev/nvidia0'),
 no_secret_env='WCP_SENTINEL_SECRET' not in os.environ,
 memory=resource.getrlimit(resource.RLIMIT_AS)[1]==4*1024**3)
for p in ['/scoring.py','/vendor/forbidden','/usr/forbidden']:
 try:
  with open(p,'w') as f: f.write('bad')
  checks[p]=False
 except OSError: checks[p]=True
s=socket.socket(); s.settimeout(0.3)
try: s.connect(('1.1.1.1',443)); checks['no_network']=False
except OSError: checks['no_network']=True
status=open('/proc/self/status').read()
checks['no_caps']='CapEff:\\t0000000000000000' in status
result=dict(checks=checks, correct=all(checks.values()), status='probe')'''
    import os
    os.environ['WCP_SENTINEL_SECRET']='must-not-enter-child'
    check('isolation',dict(kind='probe',code=probe),lambda r:r.get('correct') is True)
    task=dict(test_list=['assert f(0)==1','assert f(2)==3'],test_setup_code='')
    for name,code,status in [('correct','def f(x): return x+1','pass'),
                             ('wrong','def f(x): return x','test_failure'),
                             ('syntax','def f(:','syntax_error'),
                             ('runtime','raise RuntimeError("fixture")','runtime_error')]:
        check(name,dict(kind='mbpp',task=task,text=code,thinking=False),lambda r,s=status:r['status']==s)
    check('timeout',dict(kind='mbpp',task=task,text='while True: pass',thinking=False),
          lambda r:r['status']=='timeout',timeout=1)
    check('memory',dict(kind='probe',code='try:\n x=bytearray(5*1024**3); ok=False\nexcept MemoryError: ok=True\nresult=dict(correct=ok)'),lambda r:r.get('correct') is True)
    assert extract('reasoning ```python\nx=1\n```', True)==(None,'unfinished_thinking')
    assert extract('a</think>```python\nx=1\n```\n```python\nx=2\n```')[0]=='x=2'
    assert extract('def f(x): return x',False)[0]=='def f(x): return x'
    check('unfinished',dict(kind='mbpp',task=task,text='def f(x): return x+1',thinking=True),lambda r:r['status']=='unfinished_thinking')
    h=dict(prompt='def add_one(x):\n    """Add one."""\n',canonical_solution='    return x+1\n',
           entry_point='add_one',base_input=[[0],[2]],plus_input=[[-1],[9]],atol=0)
    check('evalplus-reference',dict(kind='humaneval',task=h,reference=True),lambda r:r['correct'] is True)
    check('evalplus-wrong',dict(kind='humaneval',task=h,text='def add_one(x): return x',thinking=False),lambda r:r['correct'] is False)
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        journal=Path(tmp)/'score.jsonl'
        generated=[dict(key='fixture',sample=s,seed=100+s,text='def f(x): return x'+('+1' if s==0 else '')) for s in (0,1)]
        scored=score_rows(generated,{'fixture':task},'mbpp',journal,False)
        before=journal.read_bytes()
        assert score_rows(generated,{'fixture':task},'mbpp',journal,False)==scored
        assert journal.read_bytes()==before
        assert aggregate(scored,[('fixture',0),('fixture',1)])['pass_at_1']==0.5
        for invalid in (scored[:1],scored+scored[:1],[dict(scored[0],result=dict(correct=None)),scored[1]]):
            try: aggregate(invalid,[('fixture',0),('fixture',1)])
            except ValueError: pass
            else: raise AssertionError('invalid aggregate accepted')
        rows.append(dict(name='journal_and_aggregation',passed=True,result=dict(wall_seconds=0)))
    (ROOT/'receipts/cpu-acceptance.json').write_text(json.dumps(rows,indent=2)+'\n')
    print(json.dumps(dict(status='passed',checks=len(rows)+3,wall_seconds=sum(r['result']['wall_seconds'] for r in rows))))


if __name__=='__main__': main()
