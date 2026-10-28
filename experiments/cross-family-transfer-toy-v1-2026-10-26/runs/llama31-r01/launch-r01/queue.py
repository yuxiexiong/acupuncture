"""This authorized run only: wait for both GPUs, stage 1, then stage 2 on PASS."""
import fcntl
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

HERE = Path(__file__).resolve().parent
RUN = HERE.parent
ROOT = RUN.parent.parent
sys.path.insert(0, str(ROOT))
from common import PROJECT, read, write, sha, utc, verify_freeze, require_stage


def second_stage_allowed(decision):
    return decision == "PASS"


def main():
    lock = (RUN / "launch.lock").open("a")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    assert not (HERE / "state.json").exists(), "Preserve the existing launch attempt"
    auth = read(HERE / "authorization.json")
    assert auth["allowed_stages"] == [1, 2] and auth["stage2_requires"] == "PASS"
    assert auth["queue_sha256"] == sha(Path(__file__))
    assert auth["freeze_sha256"] == sha(RUN / "freeze.json")
    frozen = verify_freeze(RUN / "freeze.json")
    ready = read(RUN / "GPU_READY.json")
    assert ready["status"] == "GPU_READY" and ready["freeze_sha256"] == auth["freeze_sha256"]
    state = {"status": "starting", "pid": os.getpid(), "started_utc": utc(),
             "authorization_sha256": sha(HERE / "authorization.json"), "stages": []}
    started = time.monotonic()

    def save():
        state["updated_utc"] = utc()
        write(HERE / "state.json", state)

    try:
        for stage in (1, 2):
            if stage == 2:
                decision = read(RUN / "stage1/gate.json")["decision"]
                if not second_stage_allowed(decision):
                    state.update(status="stopped_at_stage1_gate", decision=decision)
                    break
                require_stage(2, RUN, RUN / "mapping/bundle.pt", RUN / "freeze.json")
            state["stage"] = stage
            while True:
                active = subprocess.check_output(["nvidia-smi", "--query-compute-apps=pid",
                                                  "--format=csv,noheader"], text=True).strip()
                if not active:
                    break
                state.update(status="waiting_for_free_gpus", blocking_gpu_pids=active.splitlines())
                save()
                time.sleep(30)
            command = [sys.executable, "-u", str(ROOT / "pipeline.py"), "--stage", str(stage),
                       "--run", str(RUN), "--source", frozen["source_model"],
                       "--target", frozen["target_model"], "--execute"]
            environment = {**os.environ, "CUDA_VISIBLE_DEVICES": "", "HF_HUB_OFFLINE": "1",
                           "HF_DATASETS_OFFLINE": "1", "HF_HOME": str(PROJECT / ".cache/hf"),
                           "OMP_NUM_THREADS": "4", "PYTHONDONTWRITEBYTECODE": "1"}
            with (HERE / f"stage{stage}.log").open("xb") as stream:
                child = subprocess.Popen(command, cwd=PROJECT, env=environment,
                                         stdout=stream, stderr=subprocess.STDOUT)
                entry = {"stage": stage, "pid": child.pid, "started_utc": utc(), "command": command}
                state["stages"].append(entry)
                state.update(status="running", blocking_gpu_pids=[])
                save()
                code = child.wait()
            entry.update(exit_code=code, ended_utc=utc())
            assert code == 0, f"Stage {stage} failed; preserve logs and do not advance"
            entry["gate_decision"] = read(RUN / f"stage{stage}/gate.json")["decision"]
            save()
        else:
            state.update(status="machine_completed", behavior_blind_review="pending")
    except Exception as error:
        state.update(status="TECHNICAL_HOLD", error=str(error), traceback=traceback.format_exc())
        raise
    finally:
        state.update(wall_seconds=time.monotonic() - started)
        save()


if __name__ == "__main__":
    if sys.argv[1:] == ["--self-test"]:
        assert second_stage_allowed("PASS")
        for decision in ("STOP_SMALL_EFFECT", "INCONCLUSIVE_HOLD", "TECHNICAL_HOLD", "MAPPING_QUALITY_HOLD", None):
            assert not second_stage_allowed(decision)
        print("stage advancement checks passed; no process launched")
    else:
        assert len(sys.argv) == 1
        main()
