#!/usr/bin/env python3
"""Start each model only after its complete caches exist; run the frozen acceptance."""
import json
from pathlib import Path
import socket
import subprocess
import sys
import time
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parent
RUNTIME = ROOT / "runtime"
models = {m["id"]: m for m in json.loads((ROOT / "models.json").read_text())}
receipt = {"started_at": time.time(), "status": "running", "models": {}}
receipt_path = RUNTIME / "postbuild-receipt-r01.json"
if receipt_path.exists():
    raise SystemExit("Preserve the existing postbuild receipt; inspect before retrying")


def save():
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n")


def running(pid_file, marker):
    try:
        pid = int(pid_file.read_text())
        return marker.encode() in Path(f"/proc/{pid}/cmdline").read_bytes()
    except (FileNotFoundError, ProcessLookupError):
        return False


try:
    save()
    for profile in ("4b", "2b", "9b"):
        m = models[profile]
        state = receipt["models"][profile] = {"phase": "waiting_for_complete_caches"}
        save()
        cache = ROOT / "data" / profile / "cache"
        while not all((cache / name).exists() for name in ("steer_index.npz", "layout_writes.npz")):
            if not (cache / "layout_writes.npz").exists() and not running(RUNTIME / f"layout-{profile}.pid", "build_layout.py"):
                raise RuntimeError(f"{profile} layout did not finish")
            if not (cache / "steer_index.npz").exists() and not running(RUNTIME / "full-cache-queue.pid", "finish_cache_queue.py"):
                raise RuntimeError(f"{profile} full-index queue did not finish")
            time.sleep(30)
        with socket.socket() as check:
            check.bind(("127.0.0.1", m["port"]))
        with (RUNTIME / f"server-{profile}-r01.log").open("xb") as log:
            worker = subprocess.Popen([sys.executable, str(ROOT / "serve_model.py"), profile], cwd=ROOT,
                stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, start_new_session=True)
        (RUNTIME / f"server-{profile}.pid").write_text(str(worker.pid) + "\n")
        state.update(phase="loading", pid=worker.pid, started_at=time.time())
        save()
        deadline = time.monotonic() + 180
        while True:
            if worker.poll() is not None:
                raise RuntimeError(f"{profile} service exited; inspect its log")
            try:
                with urlopen(f"http://127.0.0.1:{m['port']}/api/status", timeout=5) as response:
                    ready = json.load(response)["status"] == "ready"
                if ready:
                    break
            except OSError:
                pass
            if time.monotonic() > deadline:
                raise TimeoutError(f"{profile} load exceeded 180 seconds; inspect service")
            time.sleep(2)
        state["phase"] = "acceptance"
        save()
        output = ROOT / f"live-{profile}-r01.json"
        result = subprocess.run([sys.executable, str(ROOT / "live_smoke.py"), "--profile", profile,
                                 "--output", str(output)], cwd=ROOT)
        if result.returncode != 0:
            raise RuntimeError(f"{profile} acceptance failed; retained {output}")
        state.update(phase="passed", completed_at=time.time(), evidence=str(output.relative_to(ROOT)))
        save()
    receipt.update(status="passed", finished_at=time.time())
except Exception as error:
    receipt.update(status="failed", error=repr(error), finished_at=time.time())
    raise
finally:
    save()
