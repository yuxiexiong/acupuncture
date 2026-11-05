"""CPU-only regression for the new stop target and scheduler boundary."""
import json
import unittest
from unittest.mock import patch
from pathlib import Path
import test_offline as old
from common import HERE, packed, digest, require_live, file_hash
import scale


class ScaleTests(unittest.TestCase):
    setUp = old.OfflineTests.setUp
    tearDown = old.OfflineTests.tearDown
    service = old.OfflineTests.service

    def test_exactly_fifty_full_distinct_repairs(self):
        limits=old.contract()
        limits.update(repair_rounds=50,wall_seconds=None,forwards=1000,samples=1000,target_tokens=1000000)
        s=self.service(limits=limits)
        for i in range(1,51):
            x=self.source.load(old.NAMES[0]);x[0,0]=i
            m=self.candidates.commit(self.candidates.base_id,{old.NAMES[0]:x},'synthetic counter check')
            s.evaluate(dict(candidate=m['id']))
            self.assertEqual(s.state['repair_rounds_completed'],i)
            self.assertEqual(s.state['research_done'],i==50)
            if i<50:
                s.evaluate(dict(candidate=m['id']))
                self.assertEqual(s.state['repair_rounds_completed'],i)
        self.assertIsNotNone(s.state['frozen'])
        from progress import export
        with patch('progress.draw'):
            export(s,'SYNTHETIC TEST ONLY')
        report=json.loads((s.root/'reports/result.json').read_text())
        rows=json.loads((s.root/'reports/trajectory.json').read_text())['rows']
        self.assertEqual([r['round'] for r in rows],list(range(51)))
        self.assertEqual(report['completed_rounds'],50)
        self.assertIsNotNone(report['final'])
        self.assertEqual(rows[0]['accuracy_pct'],report['baseline']['accuracy_pct'])
        self.assertEqual(rows[-1]['incumbent_candidate'],report['selected_candidate'])

    def test_authorized_contract_changes_only_round_limit(self):
        cfg=json.loads((HERE/'base-config.json').read_text())
        original=dict(cfg['contract']);cfg['contract']['repair_rounds']=50
        cfg['contract_sha256']=digest(packed(cfg['contract']))
        require_live(cfg)
        self.assertEqual({k for k,v in cfg['contract'].items() if original.get(k)!=v},{'repair_rounds'})
        self.assertEqual(cfg['execution_batch_size'],64)

    def test_gpu_must_have_no_process_and_low_memory_and_no_utilization(self):
        rows='0, GPU-a, 3, 0\n1, GPU-b, 3, 0\n2, GPU-c, 2000, 0\n3, GPU-d, 3, 10\n'
        with patch('scale.subprocess.check_output',side_effect=[rows,'GPU-b, 1234\n']):
            self.assertEqual(scale.idle_gpus(),[0])

    def test_active_lock_is_never_claimed(self):
        import fcntl
        with patch('scale.ROOT',self.root),patch('scale.idle_gpus',return_value=[0]):
            p=self.root/'external/wsp';p.mkdir(parents=True)
            with (p/'engineering-gpu-0.lock').open('a') as lock:
                fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
                self.assertIsNone(scale.acquire_gpu())

    def test_reused_engine_has_no_scientific_changes(self):
        sources=json.loads((HERE/'reuse-engine.json').read_text())
        for name in ('service.py','weights.py','kernel.py','evidence.py','controller.py','RESEARCHER.md','progress.py'):
            self.assertEqual(file_hash(HERE/name),sources[name]['sha256'],name)


if __name__=='__main__': unittest.main(verbosity=2)
