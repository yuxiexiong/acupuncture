"""Bounded acceptance test for CPU kernel isolation and persistent variables."""
import argparse
import json
import subprocess
from pathlib import Path


def command(bwrap, python, prefix, environment, model, practice, work, kernel):
    args = [str(bwrap), "--unshare-all", "--die-with-parent", "--new-session", "--cap-drop", "ALL"]
    for path in ("/usr", "/bin", "/lib", "/lib64", "/etc/ld.so.cache", str(prefix), str(environment)):
        args += ["--ro-bind", path, path]
    args += ["--ro-bind", str(model), "/model", "--ro-bind", str(practice), "/practice",
             "--ro-bind", str(kernel), "/kernel.py", "--bind", str(work), "/work",
             "--proc", "/proc", "--dev", "/dev", "--tmpfs", "/tmp", "--chdir", "/work",
             "--setenv", "PATH", "/usr/bin:/bin", "--setenv", "PYTHONNOUSERSITE", "1",
             "--setenv", "HF_HUB_OFFLINE", "1", str(python), "-u", "/kernel.py"]
    return args


def main():
    p = argparse.ArgumentParser()
    for name in ("bwrap", "python", "prefix", "environment", "model", "practice", "work", "receipt"):
        p.add_argument("--" + name, type=Path, required=True)
    args = p.parse_args()
    args.work.mkdir(parents=True, exist_ok=True)
    kernel = Path(__file__).with_name("sandbox_kernel.py").resolve()
    cmd = command(args.bwrap, args.python, args.prefix, args.environment, args.model, args.practice, args.work, kernel)
    requests = [
        {"id": "isolation", "code": "import os, socket, torch\nassert not torch.cuda.is_available()\nassert not os.path.exists('/dev/nvidia0')\nassert not os.path.exists('/workspace/acupuncture/external/wsp/observer-upstream')\nassert not os.path.exists('/root/.ssh')\ns=socket.socket(); s.settimeout(1)\ntry:\n s.connect(('1.1.1.1',443)); connected=True\nexcept OSError:\n connected=False\nassert not connected\ntry:\n open('/model/should-not-write','w'); writable=True\nexcept OSError:\n writable=False\nassert not writable\nprobe_value=41\n'ISOLATION_OK'"},
        {"id": "persistence", "code": "assert probe_value+1==42\nassert not torch.is_grad_enabled()\n'PERSISTENCE_OK'"},
        {"id": "frozen", "code": "name='model.language_model.norm.weight'\ntry:\n save_edit(name,load_original(name)); rejected=False\nexcept ValueError:\n rejected=True\nassert rejected\n'FROZEN_OK'"},
        {"id": "edit", "code": "name=next(n for n in NAMES if n.endswith('mlp.down_proj.weight'))\na=load_original(name)\ntry:\n save_edit(name,a*2); rejected=False\nexcept ValueError:\n rejected=True\nassert rejected\na[0,0]+=1\nsave_edit(name,a)\nassert torch.equal(load(name),a)\nassert name in edited()\nassert not torch.equal(load_original(name),a)\ndrop_edit(name)\nassert edited()==[]\n'EDIT_LIFECYCLE_OK'"},
    ]
    completed = subprocess.run(cmd, input="".join(json.dumps(r) + "\n" for r in requests),
                               capture_output=True, text=True, timeout=120, env={"PATH": "/usr/bin:/bin"})
    receipt = {"command": cmd, "returncode": completed.returncode,
               "requests": requests, "stdout": completed.stdout, "stderr": completed.stderr}
    events = [json.loads(line) for line in completed.stdout.splitlines() if line.startswith("{")]
    ok = completed.returncode == 0 and len(events) == 5 and events[0].get("ready") and all(not e.get("failed") for e in events[1:])
    receipt["status"] = "passed" if ok else "failed"
    args.receipt.write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"status": receipt["status"], "receipt": str(args.receipt)}))
    if not ok:
        print(completed.stderr[-3000:]); print(completed.stdout[-3000:])
        raise SystemExit(1)


if __name__ == "__main__":
    main()
