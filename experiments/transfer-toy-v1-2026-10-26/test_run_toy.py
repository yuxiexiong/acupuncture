"""Guard the declared condition budget and zero semantic-dependent selection."""
import unittest
from run_toy import condition_order


class BudgetTest(unittest.TestCase):
    def test_every_question_has_same_complete_conditions(self):
        reference=set(condition_order('target',0))
        self.assertEqual(len(reference),19)
        for index in range(64):
            ordered=condition_order('target',index)
            self.assertEqual(set(ordered),reference)
            self.assertEqual(len(ordered),19)
            self.assertTrue(all(name.startswith('random') for name in ordered[:12]))
            self.assertEqual(set(condition_order('source',index)),{'S_0','S_channel','S_vector'})


if __name__=='__main__':unittest.main()
