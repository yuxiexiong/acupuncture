"""CPU-only live scheduler failure/restart acceptance, with no GPU actions."""
import json
from pathlib import Path
from broker import Broker,stop,write_json
import forward_service as F

root=F.EXT/'engineering-r2-scheduler-r1'
cfg=dict(profile='0p8b',run_root=str(root),python_limit=5,python_timeout=1,forward_limit=1,
         forward_attempt_limit=1,gpu_seconds_limit=0,forward_timeout=1)
b=Broker(cfg)
try:
    a={'id':'before','kind':'python','code':'probe=41\nprint(probe)'}
    r=b.dispatch(a); assert not r['failed']
    r=b.dispatch({'id':'timeout','kind':'python','code':'import time\ntime.sleep(20)'})
    assert r['failed'] and 'deadline' in r['editor_output']
    r=b.dispatch({'id':'after','kind':'python','code':"assert 'probe' not in globals()\nassert tok.encode('2+2').ids\n'RESTART_OK'"})
    assert not r['failed'] and r['kernel_restarted']
    r=b.dispatch({'id':'final','kind':'finalize'})
    assert not r['failed'] and r['tensors']==[]
    assert b.state['gpu_seconds']==0 and b.state['forward_success']==0
    write_json(root/'receipt.json',{'status':'passed','checks':['external timeout','kernel restarted explicitly',
        'variables lost on restart','raw tokenizer API','empty final submission validated'],'state':b.state,
        'source_sha256':{p.name:F.sha256_file(p) for p in Path(__file__).parent.glob('*.py') if not p.name.startswith('.')},
        'formal_search_started':False})
    print((root/'receipt.json').read_text())
finally: stop(b.kernel)
