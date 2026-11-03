"""CPU-only checks: occupied devices, failed probe gating and own-child cleanup."""
import json
import signal
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import queue_gpu_probe as queue


def main():
    free = {"memory_mib": 3, "utilization": 0, "pids": []}
    assert queue.idle(free)
    for key, value in (("memory_mib", 128), ("utilization", 1), ("pids", ["77"])):
        assert not queue.idle(dict(free, **{key: value}))
    with patch.object(queue.subprocess, "check_output", side_effect=["GPU-one, 3, 0\n", "GPU-other, 12\nGPU-one, 13\n"]):
        assert queue.gpu_state(1)["pids"] == ["13"]
    child = Mock(pid=123, poll=Mock(return_value=None))
    with patch.object(queue.os, "killpg") as kill:
        queue.stop_child(child)
        kill.assert_called_once_with(123, signal.SIGTERM)
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        probe = root / "probe.py"; probe.write_text("# synthetic probe fixture\n")
        argv = ["queue", "--root", str(root), "--python", "/unused/python", "--probe", str(probe), "--out", str(root/"run")]
        child = Mock(pid=124, returncode=1, poll=Mock(return_value=1))
        with patch.object(sys, "argv", argv), \
             patch.object(queue, "gpu_state", side_effect=[dict(free, pids=["77"]), free, free]), \
             patch.object(queue.time, "sleep") as sleep, \
             patch.object(queue.signal, "signal"), \
             patch.object(queue.subprocess, "Popen", return_value=child) as launch:
            try:
                queue.main()
                raise AssertionError("Failed probe did not stop queue")
            except RuntimeError:
                pass
            assert sleep.call_count == 2  # busy once, then two separate idle samples
            assert launch.call_count == 1  # 4B must not start after a shared-engine failure
        receipt = json.loads((root/"run"/"state.json").read_text())
        assert receipt["status"] == "stopped" and len(receipt["runs"]) == 1
        assert receipt["runs"][0]["exit_code"] == 1
    print(json.dumps({"status": "passed", "scope": "CPU mocks; no GPU or model import",
                      "checks": ["memory gate", "utilization gate", "PID gate", "selected GPU PID filter", "own-child cleanup", "two idle samples", "failure stops next model", "failure retained"]}))


if __name__ == "__main__":
    main()
