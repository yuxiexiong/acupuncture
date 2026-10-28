"""CPU-only queue gates: no model imports, GPU work, or remote operations."""
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import Mock, patch

import queue_run as queue


class QueueTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.output = self.root / "run"
        self.authorization = self.root / "authorization.json"
        self.authorization.write_text("{}")
        self.auth = {"remote_output": str(self.output), "freeze_sha256": "frozen"}

    def predecessor(self, status="completed"):
        run = self.root / "predecessor"
        run.mkdir()
        queue.write(run / "execution.json", {"immutable": True})
        keys = ["llama-shard-0", "llama-shard-1"]
        state = {"status": status, "freeze_sha256": "source-frozen", "controller_pid": 20,
                 "worker_pids": dict(zip(keys, (21, 22))), "worker_exit_codes": dict.fromkeys(keys, 0)}
        queue.write(run / "controller.json", state)
        for key in keys:
            (run / key).mkdir()
            queue.write(run / key / "receipt.json", {"status": "completed"})
            (run / f"{key}.exit").write_text("0\n")
        return {"predecessor": {"run": str(run), "execution_sha256": queue.sha(run / "execution.json"),
                "freeze_sha256": "source-frozen", "worker_keys": keys,
                "processes": [{"pid": pid, "start_ticks": "100"} for pid in (19, 20, 21, 22)]}}, state

    def test_predecessor_needs_success_and_process_exit(self):
        auth, state = self.predecessor()
        with patch.object(queue, "process_alive", return_value=True):
            self.assertEqual(queue.predecessor_ready(auth), (False, "predecessor_processes_exiting"))
        with patch.object(queue, "process_alive", return_value=False):
            self.assertTrue(queue.predecessor_ready(auth)[0])
            run = Path(auth["predecessor"]["run"])
            state["worker_exit_codes"]["llama-shard-0"] = 1
            queue.write(run / "controller.json", state)
            with self.assertRaisesRegex(AssertionError, "worker failure"):
                queue.predecessor_ready(auth)
            state["status"] = "failed"
            queue.write(run / "controller.json", state)
            with self.assertRaisesRegex(AssertionError, "failed or stopped"):
                queue.predecessor_ready(auth)

    def test_running_predecessor_does_not_pass(self):
        auth, _ = self.predecessor("running")
        self.assertEqual(queue.predecessor_ready(auth), (False, "predecessor_running"))

    def test_pid_reuse_and_zombie_do_not_count_as_live(self):
        fields = ["S"] + ["0"] * 18 + ["100"]
        with patch.object(Path, "read_text", return_value="23 (a process) " + " ".join(fields)):
            self.assertTrue(queue.process_alive({"pid": 23, "start_ticks": 100}))
            self.assertFalse(queue.process_alive({"pid": 23, "start_ticks": 101}))
        fields[0] = "Z"
        with patch.object(Path, "read_text", return_value="23 (a process) " + " ".join(fields)):
            self.assertFalse(queue.process_alive({"pid": 23, "start_ticks": 100}))
        with patch.object(Path, "read_text", side_effect=PermissionError):
            with self.assertRaises(PermissionError):
                queue.process_alive({"pid": 23, "start_ticks": 100})

    def test_gpu_compute_process_must_exit_even_after_predecessor(self):
        self.output.mkdir()
        state = {"status": "waiting"}
        with patch.object(queue, "prerequisites", return_value=self.auth), \
             patch.object(queue, "predecessor_ready", return_value=(True, "predecessor_completed")), \
             patch.object(queue, "gpu_processes", side_effect=[["77, GPU-id, other experiment"], []]), \
             patch.object(queue.time, "sleep") as sleep:
            queue.wait_ready(self.authorization, "digest", self.output, state)
        sleep.assert_called_once_with(10)
        self.assertEqual(state["gpu_compute_processes"], [])

    def test_auth_changes_and_failed_cpu_checks_block(self):
        cpu = self.root / "cpu.json"
        queue.write(cpu, {"status": "failed"})
        auth = {"status": "authorized", "purpose": "early_layer_trace_queue", "experiment": self.root.name,
                "user_instruction": "run after existing jobs", "queue_sha256": queue.sha(queue.__file__),
                "models": list(queue.MODELS), "maximum_generations": {"preflight": 114, "survey": 4304},
                "maximum_records": {"preflight": 42, "survey": 2152},
                "cpu_test_receipt": {"path": "cpu.json", "sha256": queue.sha(cpu)}}
        runner = types.SimpleNamespace(validate_authorization=Mock(return_value=auth))
        with patch.dict("sys.modules", {"trace_run": runner}), patch.object(queue, "ROOT", self.root):
            with self.assertRaisesRegex(AssertionError, "Authorization changed"):
                queue.prerequisites(self.authorization, "not-the-current-hash")
            runner.validate_authorization.assert_not_called()
            with self.assertRaisesRegex(AssertionError, "CPU checks did not pass"):
                queue.prerequisites(self.authorization)
            queue.write(cpu, {"status": "passed"})
            with self.assertRaisesRegex(AssertionError, "CPU test evidence changed"):
                queue.prerequisites(self.authorization)

    def fake_pair(self, mode, model, authorization, digest, output, state):
        state["stages"].setdefault(mode, {})
        for shard in (0, 1):
            key = f"{model}-shard-{shard}"
            state["stages"][mode][key] = {"status": "completed", "exit_code": 0}
            if mode == "survey":
                path = output / mode / key
                path.mkdir(parents=True)
                count = 308 if model in ("4b", "2b") else 460
                queue.write(path / "receipt.json", {"status": "completed", "completed_records": count})

    def test_all_three_preflights_precede_any_formal_work(self):
        with patch.object(queue, "ROOT", self.root), \
             patch.object(queue, "prerequisites", return_value=self.auth), \
             patch.object(queue, "wait_ready"), \
             patch.object(queue, "run_pair", side_effect=self.fake_pair) as pair:
            state = queue.main(self.authorization, self.output, True)
        self.assertEqual([(args.args[0], args.args[1]) for args in pair.call_args_list],
                         [(mode, model) for mode in ("preflight", "survey") for model in ("4b", "2b", "9b")])
        self.assertEqual(state["status"], "completed")
        self.assertEqual(state["completed_records"], 2152)
        self.assertEqual(queue.read(self.output / "preflight-accepted.json")["status"], "passed")

    def test_failed_preflight_never_starts_formal_or_discards_partial(self):
        def fail(mode, model, authorization, digest, output, state):
            if model == "2b":
                (output / "partial-evidence.txt").write_text("preserve me")
                raise RuntimeError("preflight replay mismatch")
            self.fake_pair(mode, model, authorization, digest, output, state)
        with patch.object(queue, "ROOT", self.root), \
             patch.object(queue, "prerequisites", return_value=self.auth), \
             patch.object(queue, "wait_ready"), \
             patch.object(queue, "run_pair", side_effect=fail) as pair:
            with self.assertRaisesRegex(RuntimeError, "replay mismatch"):
                queue.main(self.authorization, self.output, True)
        self.assertEqual([args.args[:2] for args in pair.call_args_list], [("preflight", "4b"), ("preflight", "2b")])
        self.assertFalse((self.output / "preflight-accepted.json").exists())
        self.assertEqual(queue.read(self.output / "queue-state.json")["status"], "failed")
        self.assertTrue((self.output / "partial-evidence.txt").exists())

    def test_worker_failure_terminates_only_own_live_child(self):
        self.output.mkdir()
        failed = Mock(pid=100, poll=Mock(return_value=1), wait=Mock(return_value=1))
        live = Mock(pid=101, poll=Mock(return_value=None), wait=Mock(return_value=-15))
        state = {"stages": {}}
        with patch.dict("sys.modules", {"trace_run": types.SimpleNamespace()}), \
             patch.object(queue, "wait_ready"), patch.object(queue, "prerequisites"), \
             patch.object(queue.subprocess, "Popen", side_effect=[failed, live]):
            with self.assertRaisesRegex(RuntimeError, "worker failure"):
                queue.run_pair("preflight", "4b", self.authorization, "digest", self.output, state)
        failed.terminate.assert_not_called()
        live.terminate.assert_called_once()
        self.assertEqual((self.output / "preflight/4b-shard-1.exit").read_text(), "-15\n")

    def test_existing_partial_run_is_never_overwritten(self):
        self.output.mkdir()
        with patch.object(queue, "prerequisites", return_value=self.auth):
            with self.assertRaisesRegex(AssertionError, "overwrite or resume"):
                queue.main(self.authorization, self.output, True)

    def test_existing_queue_lock_blocks_duplicate_without_creating_run(self):
        with (self.root / ".queue.lock").open("a") as lock:
            queue.fcntl.flock(lock, queue.fcntl.LOCK_EX | queue.fcntl.LOCK_NB)
            with patch.object(queue, "ROOT", self.root), \
                 patch.object(queue, "prerequisites", return_value=self.auth):
                with self.assertRaises(BlockingIOError):
                    queue.main(self.authorization, self.output, True)
        self.assertFalse(self.output.exists())


if __name__ == "__main__":
    unittest.main()
