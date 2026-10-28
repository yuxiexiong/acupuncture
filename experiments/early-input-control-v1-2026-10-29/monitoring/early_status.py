"""Read-only status snapshot for one early-input-control run directory (stdlib only)."""
import json, os, subprocess, sys, time, glob, shutil, datetime

run = sys.argv[1]
snap_dir = sys.argv[2] if len(sys.argv) > 2 else None
out = {'at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'run': run}
def load(p):
    try: return json.load(open(p))
    except Exception as e: return {'_error': repr(e)}
c = load(os.path.join(run, 'controller.json'))
out['controller'] = {k: c.get(k) for k in ('status', 'pid', 'stage', 'started_at', 'finished_at', 'wall_seconds', 'error')}
out['controller_pid_alive'] = bool(c.get('pid')) and os.path.exists(f"/proc/{c.get('pid')}")
out['verification'] = load(os.path.join(run, 'verification.json')).get('status') if os.path.exists(os.path.join(run, 'verification.json')) else None
workers = {}
for g, w in (c.get('workers') or {}).items():
    d = os.path.join(run, f'worker-{g}')
    pid = w.get('pid'); cmd = None
    try: cmd = open(f'/proc/{pid}/cmdline').read().replace('\0', ' ')[:200]
    except Exception: pass
    recs = glob.glob(os.path.join(d, 'records', '*.json'))
    latest = max((os.path.getmtime(p) for p in recs), default=None)
    plan = os.path.join(d, 'plan.json')
    expected = len(load(plan)) if os.path.exists(plan) else None
    ex = os.path.join(d, 'exit.json')
    log = os.path.join(run, f'worker-{g}.log')
    tail = open(log).read().strip().splitlines()[-1:] if os.path.exists(log) else []
    workers[g] = {'pid': pid, 'alive_cmd': cmd, 'records': len(recs), 'expected': expected,
                  'latest_record_utc': datetime.datetime.utcfromtimestamp(latest).isoformat() if latest else None,
                  'latest_age_s': round(time.time() - latest) if latest else None,
                  'exit': load(ex) if os.path.exists(ex) else None,
                  'receipt_status': load(os.path.join(d, 'receipt.json')).get('status'), 'log_tail': tail}
out['workers'] = workers
gpu = subprocess.run(['nvidia-smi', '--query-gpu=index,memory.used,utilization.gpu', '--format=csv,noheader'], capture_output=True, text=True).stdout.strip().splitlines()
apps = subprocess.run(['nvidia-smi', '--query-compute-apps=pid,used_memory', '--format=csv,noheader'], capture_output=True, text=True).stdout.strip().splitlines()
out['gpu'] = gpu; out['gpu_apps'] = apps
seen = {}
for p in ('/workspace/acupuncture', '/data/models', '/tmp'):
    st = os.stat(p).st_dev
    if st not in seen: seen[st] = {'paths': [], 'free_gib': round(shutil.disk_usage(p).free / 2**30, 2)}
    seen[st]['paths'].append(p)
out['disk'] = list(seen.values())
out['run_size_gib'] = round(sum(os.path.getsize(os.path.join(a, f)) for a, _, fs in os.walk(run) for f in fs) / 2**30, 3)
print(json.dumps(out, ensure_ascii=False, indent=1))
if snap_dir:
    os.makedirs(snap_dir, exist_ok=True)
    with open(os.path.join(snap_dir, out['at_utc'].replace(':', '-') + '.json'), 'x') as f: json.dump(out, f, ensure_ascii=False, indent=1)
