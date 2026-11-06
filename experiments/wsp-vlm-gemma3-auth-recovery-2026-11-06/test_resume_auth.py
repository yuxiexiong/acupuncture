import copy,json,unittest,gzip
from pathlib import Path
from resume_auth import validate,validate_failure
class Boundaries(unittest.TestCase):
 def test_recorded_boundaries_and_rejections(self):
  data=json.loads(gzip.decompress((Path(__file__).parent/'preflight.json.gz').read_bytes()))
  for task,d in data['tasks'].items():
   s=d['state'];r=d['files'][f"search/actions/turn-{s['actions']:04d}/response.json"]
   validate(s,r,[],[],s)
   for key,value in [('actions',999),('research_done',True),('frozen','bad'),('samples',0)]:
    changed=dict(s);changed[key]=value
    with self.assertRaises(ValueError):validate(changed,r,[],[],s)
   with self.assertRaises(ValueError):validate(s,r,['pending'],[],s)
   with self.assertRaises(ValueError):validate(s,r,[],['partial'],s)
   with self.assertRaises(ValueError):validate(s,dict(failed=True),[],[],s)
 def test_no_answer_or_usage_before_recovery(self):
  good=[dict(type='turn.failed',error={'message':'refresh token was revoked'})]
  validate_failure(good,False)
  for events,receipt in [(good,True),(good+[dict(type='turn.completed')],False),(good+[dict(type='item.completed',item={'type':'agent_message'})],False),([],False)]:
   with self.assertRaises(ValueError):validate_failure(events,receipt)
if __name__=='__main__':unittest.main()
