"""Queue precedence, model-specific exclusions and unique round storage; no GPU."""
import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
import queue_run
from weights import check_targeted_edit

class QueueTests(unittest.TestCase):
    def test_existing_continuation_gap_and_phase_order(self):
        with tempfile.TemporaryDirectory() as td,patch.object(queue_run,'ROOT',Path(td)),patch.object(queue_run,'VERSION','v9'):
            root=Path(td)
            for task in ['B','C']:
                p=root/f'external/wsp-vlm-mechanism-repair-v9-2026-11-05/{task}';p.mkdir(parents=True)
                (p/'state.json').write_text(json.dumps(dict(research_done=True,repair_rounds_completed=30)))
            self.assertEqual(queue_run.dependency_stage(),'waiting_existing_qwen4b')
            for p in root.glob('external/*/*/state.json'):
                p.write_text(json.dumps(dict(research_done=True,repair_rounds_completed=50)))
            self.assertEqual(queue_run.dependency_stage(),'waiting_gemma_v8')
            for task in ['B','C']:
                p=root/f'external/wsp-vlm-gemma3-v8-2026-11-05-r02/{task}';p.mkdir(parents=True)
                (p/'queue-status.json').write_text(json.dumps(dict(stage='finished')))
            self.assertIsNone(queue_run.dependency_stage())
            (p/'queue-status.json').write_text(json.dumps(dict(stage='failed')))
            with self.assertRaises(RuntimeError):queue_run.dependency_stage()
    def test_transport_retry_preserves_idempotent_request(self):
        import subprocess
        outcomes=[subprocess.CompletedProcess([],255,'','Connection closed'),subprocess.CompletedProcess([],0,'{"queued":"same-id"}','')]
        with patch.object(queue_run.subprocess,'run',side_effect=outcomes) as run,patch.object(queue_run.time,'sleep'):
            self.assertEqual(queue_run.ssh_python('pass',{'id':'same-id'}),{'queued':'same-id'})
            self.assertEqual(run.call_args_list[0],run.call_args_list[1])
            self.assertIn('ControlMaster=auto',run.call_args.args[0])
    def test_batch_choice_uses_speed_and_headroom_not_score(self):
        from batch_calibration import choose
        rows=[dict(batch_size=n,inputs_per_second=s,headroom_gib=h,repeat_equal=True) for n,s,h in [(32,35,40),(64,45.94,30),(128,46.48,20),(256,48,8)]]
        self.assertEqual(choose(rows),64)
        with self.assertRaises(RuntimeError):choose([dict(rows[0],repeat_equal=False)])
    def test_gemma_checkpoint_exclusions(self):
        for n in ['language_model.model.norm.weight','language_model.model.embed_tokens.weight','language_model.lm_head.weight']:
            with self.assertRaises(ValueError):check_targeted_edit(n,np.ones(4),np.arange(4),'BF16')
    def test_contracts_are_four_independent_30_round_runs(self):
        for task in ['B','C']:
            d=json.loads((queue_run.HERE/f'base-{task}.json').read_text())
            self.assertEqual(d['contract']['repair_rounds'],30)
            self.assertEqual(d['contract']['targeted'],queue_run.VERSION=='v9')
            self.assertEqual(d['model_revision'],'093f9f388b31de276ce2de164bdc2081324b9767')
            self.assertIn('/'+task+'/search',d['run_root'])
if __name__=='__main__':unittest.main()
