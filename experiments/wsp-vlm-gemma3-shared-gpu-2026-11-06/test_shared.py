import unittest,json,gzip
from pathlib import Path
from resume_shared_B import shared_capacity,validate
class Boundaries(unittest.TestCase):
 def test_admission(self):
  self.assertTrue(shared_capacity(85000,[2171236]))
  self.assertTrue(shared_capacity(36864,[]))
  self.assertFalse(shared_capacity(36863,[2171236]))
  self.assertFalse(shared_capacity(85000,[2171236,999]))
 def test_recorded_boundary(self):
  x=json.loads(gzip.decompress((Path(__file__).parent/'preflight.json.gz').read_bytes()));s=x['tasks']['B']['state'];r=x['last_response']
  validate(s,r,[],[],s)
  with self.assertRaises(ValueError):validate(s,r,['turn-0117'],[],s)
  with self.assertRaises(ValueError):validate(dict(s,actions=116),r,[],[],s)
if __name__=='__main__':unittest.main()
