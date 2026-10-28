import contextlib,importlib.util,io,tempfile
from pathlib import Path
import numpy as np
p=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('queue',p/'finish_cache_queue.py');q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q)
texts=np.array(['Who are you?','Write whatever you like.','I think the most important thing to remember is','Today we are going to talk about'])
for fault in [None,'partial','context_mask','norm']:
 with tempfile.TemporaryDirectory() as td:
  q.ROOT=Path(td);q.MODELS={'test':{'path':'/fixed/model','layers':2,'inter':3}}
  d=q.ROOT/'data/test';(d/'stats').mkdir(parents=True);(d/'cache').mkdir()
  for layer in range(2):
   a=dict(complete_layer=True,layer=layer,model='/fixed/model',total_neurons=3,dose=.8,neurons=np.arange(3),contexts=texts,context_ids=np.ones((4,2),int),context_mask=np.ones((4,2),int),calibration_norms=np.array([1.,2.]),residual_norm=float(layer+1),up_tok=np.zeros((3,12),int),down_tok=np.zeros((3,12),int),up_kl=np.ones(3),down_kl=np.ones(3))
   if layer==1 and fault=='partial':a['complete_layer']=False
   if layer==1 and fault=='context_mask':a['context_mask'][0,0]=0
   if layer==1 and fault=='norm':a['residual_norm']=9.
   np.savez(d/'stats'/f'steer-full-r01_L{layer}.npz',**a)
  failed=False
  try:
   with contextlib.redirect_stdout(io.StringIO()):q.merge('test')
  except AssertionError:
   failed=True
  assert failed == (fault is not None), f"unexpected merge acceptance: {fault}"
  if failed:
   assert not (d/'cache/steer_index.npz').exists()
  else:
   assert np.load(d/'cache/steer_index.npz')['up'].shape==(2,3,12)
print('PASS: full merge; reject incomplete layers, context-mask mismatch and inconsistent scales')
