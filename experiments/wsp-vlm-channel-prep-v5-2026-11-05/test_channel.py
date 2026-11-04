"""CPU-only synthetic process/accounting checks; no model imports."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
import launch
import runner


class ChannelTests(unittest.TestCase):
    def test_normal_exit(self):
        r=launch.bounded([sys.executable,'-c','pass'],3)
        self.assertEqual(r['returncode'],0)
        self.assertFalse(r['timed_out'])

    def test_error_exit(self):
        r=launch.bounded([sys.executable,'-c','raise SystemExit(7)'],3)
        self.assertEqual(r['returncode'],7)

    def test_hung_process_ignoring_term(self):
        r=launch.bounded([sys.executable,'-c',
            'import signal,time; signal.signal(signal.SIGTERM,signal.SIG_IGN); time.sleep(60)'],.5)
        self.assertTrue(r['timed_out'])
        self.assertLess(r['elapsed_seconds'],4)

    def test_attempt_written_before_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            out=Path(directory)/'predictions.jsonl'
            def fail(request,remaining):
                self.assertEqual(len(out.with_name('attempts.jsonl').read_text().splitlines()),1)
                raise ValueError('synthetic infrastructure failure')
            with self.assertRaises(ValueError):runner.drain([{'request_id':'a'}],fail,out,lambda:10)
            self.assertEqual(json.loads(out.read_text())['status'],'error')
            with self.assertRaises(FileExistsError):runner.drain([],fail,out,lambda:10)

    def test_deadline_before_attempt(self):
        with tempfile.TemporaryDirectory() as directory:
            out=Path(directory)/'predictions.jsonl'
            with self.assertRaises(TimeoutError):
                runner.drain([{'request_id':'a'}],lambda *a:self.fail(),out,lambda:0)
            self.assertEqual(out.with_name('attempts.jsonl').read_text(),'')

    def test_reconcile_killed_inflight_and_preserve_history(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);stage=root/'P0';stage.mkdir()
            p=stage/'receipt.json'
            p.write_text(json.dumps(dict(status='running',attempts=0,elapsed_seconds=0)))
            (stage/'attempts.jsonl').write_text('{"request_id":"a"}\n')
            result=dict(returncode=-9,timed_out=True,elapsed_seconds=3)
            launch.reconcile(root,result,set())
            r=json.loads(p.read_text())
            self.assertEqual((r['status'],r['attempts'],r['elapsed_seconds']),('interrupted',1,3))
            previous=p.read_bytes()
            launch.reconcile(root,dict(result,elapsed_seconds=100),{str(p)})
            self.assertEqual(p.read_bytes(),previous)


if __name__=='__main__':
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(ChannelTests)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    assert not any(n in sys.modules for n in ('torch','transformers','huggingface_hub'))
    receipt=dict(tests=result.testsRun,passed=result.wasSuccessful(),synthetic_only=True,
        forbidden_modules_loaded=[],model_loads=0,model_calls=0)
    (Path(__file__).parent/'audit/channel_tests.json').write_text(json.dumps(receipt,indent=2)+'\n')
    raise SystemExit(0 if result.wasSuccessful() else 1)
