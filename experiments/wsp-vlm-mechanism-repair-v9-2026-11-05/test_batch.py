"""CPU-only batch padding/order/EOS tests; no target weights or CUDA calls."""
import contextlib,unittest
from types import SimpleNamespace
import torch
from backend import VLMBackend
class BatchTest(unittest.TestCase):
 def test_mixed_images_left_padding_and_eos(self):
  b=object.__new__(VLMBackend)
  b.torch=SimpleNamespace(full=torch.full,cat=torch.cat,inference_mode=torch.inference_mode,cuda=SimpleNamespace(synchronize=lambda:None))
  b.processor=SimpleNamespace(tokenizer=SimpleNamespace(pad_token_id=0),decode=lambda ids,**kw:str(ids))
  b.eos=[9];b.generation=None;b.candidate=lambda *a:contextlib.nullcontext()
  b.screen=SimpleNamespace(check_generation=lambda ids,eos:{'truncated':False})
  def encode(r):
   ids={'a':[1,2],'b':[3,4,5],'c':[6]}[r['request_id']]
   x={'input_ids':torch.tensor([ids]),'attention_mask':torch.ones((1,len(ids)),dtype=torch.long),'mm_token_type_ids':torch.zeros((1,len(ids)),dtype=torch.long)}
   if r['request_id']!='b':x.update(pixel_values=torch.tensor([[1. if r['request_id']=='a' else 2.]]),image_grid_thw=torch.tensor([[1,2,2]]))
   return x,{'input_tokens':len(ids)}
  b.encode=encode
  def generate(**kw):
   self.assertEqual(kw['input_ids'].tolist(),[[0,1,2],[3,4,5],[0,0,6]])
   self.assertEqual(kw['attention_mask'].tolist(),[[0,1,1],[1,1,1],[0,0,1]])
   self.assertEqual(kw['pixel_values'].tolist(),[[1.],[2.]])
   self.assertEqual(kw['image_grid_thw'].shape[0],2)
   return torch.cat([kw['input_ids'],torch.tensor([[7,9,0],[8,8,9],[9,0,0]])],dim=1)
  b.model=SimpleNamespace(generate=generate)
  out=b.generate_batch([{'request_id':q} for q in 'abc'],None,'test',10)
  self.assertEqual([r['generated_ids'] for r in out],[[7,9],[8,8,9],[9]])
  self.assertEqual([r['request_id'] for r in out],list('abc'))
if __name__=='__main__':unittest.main()
