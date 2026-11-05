import copy,unittest
from resume_B import validate
class ResumeBoundary(unittest.TestCase):
    def test_only_clean_recorded_stop(self):
        s=dict(repair_rounds_completed=4,research_done=True,frozen=None,actions=39,best='w0-x',current='w0-x')
        r=dict(failed=False,value=dict(stopped=True))
        validate(s,r,[],[])
        for key,value in [('repair_rounds_completed',3),('research_done',False),('frozen','c-x'),('actions',40),('current','c-x')]:
            x=dict(s);x[key]=value
            with self.assertRaises(ValueError):validate(x,r,[],[])
        with self.assertRaises(ValueError):validate(s,dict(failed=True),[],[])
        with self.assertRaises(ValueError):validate(s,r,['pending'],[])
        with self.assertRaises(ValueError):validate(s,r,[],['partial'])
if __name__=='__main__':unittest.main()
