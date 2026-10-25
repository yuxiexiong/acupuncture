"""Run original HumanEval completions with the pinned checker in fresh bubblewrap sandboxes."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import gzip
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile

COMMIT = "b9453e8f1865df0a0057a1383767caa400acfbcf"
BWRAP_SHA256 = "63b4d01ce64ed5f041d658933e0ca91454b0f9580a5f2dc99a72da50070bb5d6"


def sha_bytes(value):
    return hashlib.sha256(value).hexdigest()


def read_rows(path):
    opener = gzip.open if str(path).endswith(".gz") else open
    with opener(path, "rt") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def command(bwrap, official, python_prefix):
    result = ["/usr/bin/prlimit", "--as=1073741824", "--cpu=8:10", "--fsize=1048576", "--nofile=64",
              "--nproc=32", "--core=0", "--", str(bwrap), "--unshare-all", "--die-with-parent", "--new-session",
              "--uid", "65534", "--gid", "65534", "--cap-drop", "ALL",
              "--ro-bind", "/usr", "/usr"]
    for path in ("/lib", "/lib64"):
        if Path(path).exists():
            result.extend(["--ro-bind", path, path])
    result.extend(["--proc", "/proc", "--dev", "/dev", "--tmpfs", "/dev/shm", "--tmpfs", "/tmp",
                   "--dir", "/app", "--ro-bind", str(official / "human_eval/execution.py"), "/app/execution.py",
                   "--ro-bind", str(Path(__file__).with_name("humaneval_worker.py")), "/app/worker.py",
                   "--ro-bind", str(python_prefix), "/python", "--chdir", "/tmp"])
    for key, value in {"PATH": "/python/bin:/usr/bin", "HOME": "/tmp", "PYTHONHOME": "/python",
                       "LD_LIBRARY_PATH": "/python/lib", "OMP_NUM_THREADS": "1", "PYTHONHASHSEED": "0",
                       "LC_ALL": "C.UTF-8"}.items():
        result.extend(["--setenv", key, value])
    return result + ["/python/bin/python3", "-B", "-S", "/app/worker.py"]


def run_case(case, cmd):
    identity = {"id": case["id"], "arm": case["arm"],
                "completion_sha256": sha_bytes(case["completion"].encode()),
                "problem_sha256": sha_bytes(json.dumps(case["problem"], ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode())}
    # Bounded regular files also cover writes bypassing the official stdout redirection.
    with tempfile.TemporaryFile() as stdout, tempfile.TemporaryFile() as stderr:
        try:
            # bwrap 0.4.1 lacks --clearenv; replace the process environment here.
            run = subprocess.run(cmd, input=json.dumps(case).encode(), stdout=stdout, stderr=stderr,
                                 timeout=15, env={"PATH": "/usr/bin:/bin"})
        except subprocess.TimeoutExpired:
            return {**identity, "status": "infrastructure_failure", "error": "sandbox_wall_timeout"}
        stdout.seek(0); stderr.seek(0)
        output, error = stdout.read(1024**2).decode(errors="replace"), stderr.read(1024**2).decode(errors="replace")
    if run.returncode:
        return {**identity, "status": "infrastructure_failure", "returncode": run.returncode, "stdout": output, "stderr": error}
    try:
        result = json.loads(output)
        assert result["task_id"] == case["problem"]["task_id"] and isinstance(result["passed"], bool)
    except (ValueError, KeyError, AssertionError):
        return {**identity, "status": "infrastructure_failure", "error": "invalid_checker_output", "stdout": output, "stderr": error}
    return {**identity, "status": "completed", **result, "stderr": error}


def synthetic_cases():
    problem = {"task_id": "synthetic/0", "prompt": "def add_one(x):\n", "test": "def check(candidate):\n    assert candidate(1) == 2\n", "entry_point": "add_one"}
    denial = "    import os, socket\n    assert os.getuid() != 0, 'root uid'\n    assert not os.path.exists('/root') and not os.path.exists('/workspace'), 'host paths visible'\n    assert set(os.environ) <= {'PATH','HOME','PYTHONHOME','LD_LIBRARY_PATH','OMP_NUM_THREADS','PYTHONHASHSEED','LC_ALL','PWD'}, 'unexpected environment keys: ' + repr(sorted(os.environ))\n    assert os.environ.get('PWD') == '/tmp', 'unexpected working directory environment'\n    s = socket.socket()\n    s.settimeout(0.1)\n    try:\n        s.connect(('1.1.1.1', 80))\n    except OSError:\n        pass\n    else:\n        raise AssertionError('network accessible')\n    return x + 1\n"
    return [{"id": label, "arm": "control", "problem": {**problem, "task_id": "synthetic/" + label}, "completion": source}
            for label, source in (("success", "    return x + 1\n"), ("wrong", "    return 0\n"),
                                  ("syntax", "    return (\n"), ("timeout", "    while True: pass\n"), ("isolation", denial))]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bwrap", type=Path, required=True)
    parser.add_argument("--official", type=Path, required=True)
    parser.add_argument("--python-prefix", type=Path, required=True)
    parser.add_argument("--records", type=Path, nargs="*")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    for name in ("bwrap", "official", "python_prefix"):
        setattr(args, name, getattr(args, name).resolve())
    assert sha_bytes(args.bwrap.read_bytes()) == BWRAP_SHA256
    actual = subprocess.check_output(["git", "-C", str(args.official), "rev-parse", "HEAD"], text=True).strip()
    assert actual == COMMIT and (args.python_prefix / "bin/python3").exists()
    source = subprocess.check_output(["git", "-C", str(args.official), "show", COMMIT + ":human_eval/execution.py"])
    assert source == (args.official / "human_eval/execution.py").read_bytes(), "Modified official checker"
    assert not args.output.exists(), "Never replace execution evidence"
    cmd = command(args.bwrap, args.official, args.python_prefix)
    expected_controls = {"success": "passed", "wrong": "test_failure", "syntax": "syntax_error", "timeout": "timeout", "isolation": "passed"}
    controls = [run_case(case, cmd) for case in synthetic_cases()]
    controls_passed = all(row["status"] == "completed" and row.get("category") == expected_controls[row["id"]] for row in controls)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    controls_path = args.output.with_suffix(args.output.suffix + ".controls.jsonl")
    assert not controls_path.exists()
    controls_path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in controls))
    assert controls_passed, f"Isolation controls failed; no generated completion executed. See {controls_path}"
    if args.self_test:
        cases = []
    else:
        assert args.records
        rows = [row for path in args.records for row in read_rows(path) if row["benchmark"] == "humaneval"]
        assert len(rows) == len({row["id"] for row in rows}) == 164
        cases = []
        for row in rows:
            assert row["status"] == "completed"
            for arm in ("baseline", "evo"):
                output = row["outputs"][arm]
                assert output["status"] == "completed"
                cases.append({"id": row["id"], "arm": arm, "problem": row["item"]["doc"], "completion": output["answer_text"]})
    results = []
    with args.output.open("x") as handle:
        # Each completion gets a fresh namespace, filesystem, and bounded process tree.
        with ThreadPoolExecutor(max_workers=4) as pool:
            for result in pool.map(lambda case: run_case(case, cmd), cases):
                handle.write(json.dumps(result, ensure_ascii=False) + "\n"); handle.flush()
                results.append(result)
        if args.self_test:
            for result in controls:
                handle.write(json.dumps(result, ensure_ascii=False) + "\n")
            results = controls
    receipt = {"status": "completed" if all(row["status"] == "completed" for row in results) else "infrastructure_failure",
               "created_utc": datetime.now(timezone.utc).isoformat(), "self_test": args.self_test,
               "count": len(results), "humaneval_commit": COMMIT, "bwrap_sha256": BWRAP_SHA256,
               "controls_passed": controls_passed, "controls_file": str(controls_path), "controls_sha256": sha_bytes(controls_path.read_bytes()),
               "python_version": subprocess.check_output([str(args.python_prefix / "bin/python3"), "--version"], text=True).strip(),
               "driver_sha256": sha_bytes(Path(__file__).read_bytes()),
               "worker_sha256": sha_bytes(Path(__file__).with_name("humaneval_worker.py").read_bytes()),
               "execution_sha256": sha_bytes((args.official / "human_eval/execution.py").read_bytes()),
               "command": cmd, "output_sha256": sha_bytes(args.output.read_bytes()), "checker_timeout_seconds": 3,
               "sandbox_wall_timeout_seconds": 15, "workers": 4,
               "resource_limits": {"address_space_bytes": 1024**3, "cpu_soft_hard_seconds": [8, 10], "file_bytes": 1024**2, "open_files": 64, "processes_per_uid": 32}}
    if args.self_test:
        receipt["self_test_passed"] = controls_passed
    args.output.with_suffix(args.output.suffix + ".receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    assert receipt["status"] == "completed" and receipt.get("self_test_passed", True)


if __name__ == "__main__":
    main()
