"""CPU-only guards: author CLI settings and explanation-gated actions."""
import importlib.util,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
P=Path(__file__).resolve().parents[3]/'engineering-r2/controller.py'
s=importlib.util.spec_from_file_location('controller',P);c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
class Alignment(unittest.TestCase):
 def test_explanation_gate(self):
  action='```python\nprint(1)\n```'
  self.assertEqual(c.parse_action(action)['kind'],'python')
  with self.assertRaisesRegex(ValueError,'Missing explanation'):c.parse_action(action,True)
  self.assertEqual(c.parse_action('I will inspect the previous result.\n'+action,True)['kind'],'python')
 def test_author_settings_and_no_native_tools(self):
  def run(cmd,**kw):
   self.assertIn('model_context_window=872000',cmd)
   self.assertIn('model_auto_compact_token_limit=1000000',cmd)
   self.assertIn('model_reasoning_effort="max"',cmd)
   self.assertIn('read-only',cmd);self.assertIn('shell_tool',cmd)
   for e in [{'type':'thread.started','thread_id':'existing'},{'type':'item.completed','item':{'type':'agent_message','text':'done'}},{'type':'turn.completed','usage':{}}]:kw['stdout'].write(json.dumps(e)+'\n')
   return type('Result',(),{'returncode':0})()
  with tempfile.TemporaryDirectory() as d,patch.object(c.subprocess,'run',run):
   p=Path(d);reply,thread=c.editor_turn('task',p/'turn',p,'existing')
   self.assertEqual(thread,'existing');self.assertEqual((p/'instructions.txt').read_text(),"Answer the user's request.\n")
if __name__=='__main__':unittest.main()
