import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

import launch_survey as launch


class FakeProcess:
    def __init__(self, code, pid):
        self.code, self.pid, self.terminated = code, pid, False
    def poll(self):
        return self.code
    def terminate(self):
        self.code, self.terminated = -15, True
    def wait(self, timeout=None):
        return self.code


class LaunchChecks(unittest.TestCase):
    def test_authorization_failure_never_starts_worker(self):
        with patch.object(launch.survey, 'check_authorization', side_effect=AssertionError('denied')), \
             patch.object(launch.subprocess, 'Popen') as popen:
            with self.assertRaises(AssertionError):
                launch.launch('/tmp/no-authorization', '/tmp/not-a-real-run', True)
            popen.assert_not_called()

    def test_two_shards_per_model_and_stop_on_failure(self):
        for fail in (False, True):
            with self.subTest(fail=fail), tempfile.TemporaryDirectory() as directory:
                root = Path(directory).resolve()
                output = root/'survey-r01'
                auth = {'controller_sha256':launch.survey.io.sha(Path(launch.__file__)), 'remote_output':str(output)}
                auth_path=root/'authorization.json';auth_path.write_text('{}')
                processes, commands = [], []
                def create(command, **kwargs):
                    commands.append(command)
                    code = (1 if len(commands)==1 else None) if fail else 0
                    proc = FakeProcess(code, 100+len(commands));processes.append(proc)
                    return proc
                with patch.object(launch, 'ROOT', root), \
                     patch.object(launch.survey, 'check_authorization', return_value=('frozen',auth)), \
                     patch.object(launch.survey, 'verify', return_value={}), \
                     patch.object(launch.subprocess, 'Popen', side_effect=create):
                    if fail:
                        with self.assertRaises(RuntimeError):
                            launch.launch(auth_path, output, True)
                        self.assertEqual(len(commands), 2)
                        self.assertTrue(processes[1].terminated)
                    else:
                        state=launch.launch(auth_path, output, True)
                        self.assertEqual(state['status'],'completed')
                        self.assertEqual(len(commands),6)
                        self.assertEqual([c[c.index('--model')+1] for c in commands], ['2b','2b','4b','4b','9b','9b'])
                        self.assertEqual([c[c.index('--shard')+1] for c in commands], ['0','1']*3)
                    self.assertTrue((output/'controller.json').exists())
                    self.assertTrue((output/'execution.json').exists())


if __name__ == '__main__':
    unittest.main()
