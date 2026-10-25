"""Linux-only synthetic boundary check. Does not load a model or real responses."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time

guard = Path(__file__).with_name("stop_after_q24.py").resolve()
fake = '''import json,time
from pathlib import Path
root=Path('raw-corpus-cpu-bf16-r01'); root.mkdir()
done={"status":"completed","attempts":[{"baseline":{"status":"completed"},"modified":{"status":"completed"}}]}
for i in range(1,41):
 value=done if i<24 else {"status":"running" if i==24 else "pending","attempts":[]}
 (root/f'Q{i:02d}.json').write_text(json.dumps(value))
receipt={"current_question":"Q24","completed_questions":[f'Q{i:02d}' for i in range(1,24)]}
(root/'receipt.json').write_text(json.dumps(receipt))
print('READY',flush=True)
while not Path('finish_Q24').exists(): time.sleep(.01)
(root/'Q24.tmp').write_text(json.dumps(done)); (root/'Q24.tmp').replace(root/'Q24.json')
receipt['completed_questions'].append('Q24')
(root/'receipt.tmp').write_text(json.dumps(receipt)); (root/'receipt.tmp').replace(root/'receipt.json')
(root/'Q25.json').read_text()
Path('Q25_WAS_STARTED').touch()
'''
with tempfile.TemporaryDirectory(prefix="qwen-boundary-test-") as temporary:
    folder = Path(temporary)
    (folder / "collect_raw.py").write_text(fake)
    worker = subprocess.Popen([sys.executable, "collect_raw.py", "raw-corpus-cpu-bf16-r01"], cwd=folder, stdout=subprocess.PIPE, text=True)
    stopper = None
    try:
        assert worker.stdout.readline().strip() == "READY"
        stopper = subprocess.Popen([sys.executable, str(guard)], cwd=folder, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        for _ in range(500):
            path = folder / "stop-after-q24/receipt.json"
            if path.exists() and json.loads(path.read_text())["status"] == "waiting_for_Q24":
                break
            assert stopper.poll() is None, stopper.communicate()
            time.sleep(0.01)
        else:
            raise AssertionError("Synthetic boundary was not installed")
        (folder / "finish_Q24").touch()
        assert worker.wait(timeout=10) == -15
        output, error = stopper.communicate(timeout=15)
        assert stopper.returncode == 0, error
        assert not (folder / "Q25_WAS_STARTED").exists()
        result = json.loads((folder / "stop-after-q24/receipt.json").read_text())
        assert result["status"] == "stopped_after_Q24" and result["Q25_original_restored"]
        assert json.loads((folder / "raw-corpus-cpu-bf16-r01/Q25.json").read_text()) == {"status":"pending","attempts":[]}
        print("PASS: synthetic Q24 retained, Q25 blocked, exact pending record restored")
    finally:
        for process in (worker, stopper):
            if process is not None and process.poll() is None:
                process.kill()
                process.wait()
