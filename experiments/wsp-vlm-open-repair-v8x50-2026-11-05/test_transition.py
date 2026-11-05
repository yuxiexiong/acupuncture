import unittest
from continue50 import transition
from test_offline import OfflineTests,contract,NAMES

class ContinueTests(unittest.TestCase):
 def test_real_counter_continues_from_30_to_50(self):
  fixture=OfflineTests();fixture.setUp()
  try:
   limits=contract();limits.update(repair_rounds=30,wall_seconds=None,forwards=1000,samples=1000,target_tokens=10000000)
   service=fixture.service(limits=limits)
   for n in range(1,31):
    x=fixture.source.load(NAMES[0]);x[0,0]=n
    m=fixture.candidates.commit(fixture.candidates.base_id,{NAMES[0]:x},str(n))
    service.evaluate({'candidate':m['id']})
   self.assertTrue(service.state['research_done']);before=service.backend.calls
   service.state,service.contract=transition(service.state,service.contract)
   service.evaluate({'candidate':m['id']})
   self.assertEqual(service.state['repair_rounds_completed'],30)
   self.assertEqual(service.backend.calls,before)
   for n in range(31,51):
    x=fixture.source.load(NAMES[0]);x[0,0]=n
    m=fixture.candidates.commit(fixture.candidates.base_id,{NAMES[0]:x},str(n));service.evaluate({'candidate':m['id']})
    self.assertEqual(service.state['research_done'],n==50)
   self.assertEqual(service.state['repair_rounds_completed'],50)
  finally:fixture.tearDown()

if __name__=='__main__':unittest.main()
