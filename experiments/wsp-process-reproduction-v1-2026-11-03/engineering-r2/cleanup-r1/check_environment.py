"""Post-cleanup imports, source assets, sandbox and tiny CUDA arithmetic; no model forward."""
import importlib,json,os,subprocess,sys
from pathlib import Path
CODE=Path('/workspace/acupuncture/external/wsp/code-engineering-r2')
ROOT=Path('/workspace/acupuncture/external/wsp/cleanup-r1-2026-11-03')
sys.path.insert(0,str(CODE));sys.path.insert(0,str(CODE/'engineering-r2'))
import forward_service as F
from sandbox_probe import command
versions={}
for name in ['torch','vllm','transformers','numpy','scipy','sklearn','pandas','sympy','networkx','safetensors','tokenizers']:
 m=importlib.import_module(name);versions[name]=getattr(m,'__version__','imported')
import torch
from safetensors import safe_open
from tokenizers import Tokenizer
assets=[]
for profile,count in [('0p8b',320),('4b',426)]:
 model=F.profile(profile)['model']
 with safe_open(str(model/'model.safetensors'),framework='pt',device='cpu') as f:
  assert len(f.keys())==count
 tok=Tokenizer.from_file(str(model/'tokenizer.json'));assert tok.encode('2 + 2 = 4').ids
 assets.append({'profile':profile,'tensor_count':count,'tokenizer_ids':tok.encode('2 + 2 = 4').ids})
assert torch.cuda.is_available()
idle=subprocess.check_output(['nvidia-smi','--query-gpu=index,memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True)
available=[int(a) for a,b,c in (line.split(',') for line in idle.splitlines()) if int(b)<128 and int(c)==0]
assert available,'No idle GPU for tiny CUDA environment check; no other task interrupted'
g=available[0]
x=torch.ones(2,device=f'cuda:{g}');assert x.sum().item()==2;del x;torch.cuda.empty_cache()
work=ROOT/'environment-probe-work';work.mkdir(exist_ok=False)
env=Path('/workspace/acupuncture/.venv-wsp')
cmd=command(F.EXT/'tools/bubblewrap-local/usr/bin/bwrap',env/'bin/python',Path('/workspace/miniconda'),env,
 F.profile('0p8b')['model'],F.PRACTICE,work,CODE/'engineering-r2/sandbox_kernel.py')
requests=[{'id':'first','code':"import torch,os\nassert not torch.cuda.is_available()\nassert not os.path.exists('/root/.ssh')\nv=41\nassert tok.encode('2+2').ids\n'KERNEL_OK'"},
          {'id':'second','code':"assert v+1==42\nassert edited()==[]\n'PERSISTENCE_OK'"}]
p=subprocess.run(cmd,input=''.join(json.dumps(r)+'\n' for r in requests),capture_output=True,text=True,timeout=120,env={'PATH':'/usr/bin:/bin'})
events=[json.loads(l) for l in p.stdout.splitlines()]
assert p.returncode==0 and len(events)==3 and events[0].get('ready') and all(not r.get('failed') for r in events[1:]),p.stderr
(ROOT/'environment-kernel.json').write_text(json.dumps({'requests':requests,'stdout':p.stdout,'stderr':p.stderr},indent=2))
receipt={'status':'passed','versions':versions,'model_assets':assets,'cuda_device':g,'cuda_arithmetic':'ones(2).sum()==2',
         'sandbox_persistence':True,'model_forward_calls':0,'formal_search_started':False}
(ROOT/'environment-receipt.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt))
