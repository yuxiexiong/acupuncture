"""DIV-01 stage 0: 4B L0 threshold-split generation survey (generation only, no deep states)."""
import argparse, hashlib, importlib.util, json, random, sys, time, traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP = HERE.parent
OLD = EXP / "layer-survey-toy-v1-2026-10-27"
DOSEX = EXP / "layer-dose-survey-toy-v1-2026-10-27"
sys.path.insert(0, str(DOSEX))
spec = importlib.util.spec_from_file_location("div01_io", EXP / "transfer-toy-v1-2026-10-26/run_io.py")
io = importlib.util.module_from_spec(spec); spec.loader.exec_module(io)
import dose_engine  # frozen dose-survey hook, unchanged
dose_engine.DOSES = tuple(dose_engine.DOSES) + (0.75,)  # only change: allow the new 0.75 dose

C = json.loads((HERE / "contract.json").read_text())


def token_hash(t):
    return hashlib.sha256(json.dumps(t, separators=(",", ":")).encode()).hexdigest()


def channels():
    old = sorted(C["existing_channels"])
    pool = [n for n in range(C["intermediate_size"]) if n not in set(old)]
    new = sorted(random.Random(C["new_channel_seed"]).sample(pool, C["n_new_channels"]))
    return old, new


def jobs(worker):
    old, new = channels()
    allch = old + new
    mine = [c for i, c in enumerate(allch) if i % 2 == worker]
    qs = [f"Q{i:02d}" for i in range(1, 9)]
    # control/replay arm first: worker 0 replays baseline, worker 1 replays N4146@0.5
    replay = [("replay-baseline", None, None, q) for q in qs] if worker == 0 else \
             [("replay-N004146-D0p5", 4146, 0.5, q) for q in qs]
    main = [(f"L00-N{c:06d}-D{str(d).replace('.', 'p')}", c, d, q) for d in C["doses"] for c in mine for q in qs]
    return replay, main


def archived(cond, q):
    if cond == "replay-baseline":
        return json.load(open(OLD / f"survey-r01/4b-shard-0/records/baseline__{q}.json"))
    return json.load(open(next(DOSEX.glob(f"survey-r01/4b-shard-*/records/L00-N004146-D0p5__{q}.json"))))


def run(worker, out):
    out = Path(out); assert not out.exists(); out.mkdir(parents=True)
    replay, main = jobs(worker)
    rec = {"status": "running", "worker": worker, "contract_sha256": io.sha(HERE / "contract.json"),
           "freeze": json.loads((HERE / "freeze.json").read_text()), "started_utc": io.utc(),
           "expected": len(replay) + len(main), "done": 0}
    io.write(out / "receipt.json", rec)
    t0 = time.monotonic()
    try:
        m = next(x for x in json.load(open(OLD / "contract.json"))["models"] if x["id"] == "4b")
        eng = dose_engine.DoseEngine(m["remote_path"], m, "cuda:0")
        instr = json.load(open(OLD / "contract.json"))["instruction"]
        questions = {q["id"]: q["prompt"] for q in json.load(open(OLD / "questions.json"))}
        ctx = {q: eng.tokenizer.apply_chat_template([{"role": "user", "content": instr + "\n\n" + p}],
               tokenize=False, add_generation_prompt=True, enable_thinking=False) for q, p in questions.items()}
        cal = dict(zip(ctx, eng.calibrate(list(ctx.values()))))
        base = {q: json.load(open(OLD / f"survey-r01/4b-shard-0/records/baseline__{q}.json")) for q in ctx}
        for q in ctx:
            assert ctx[q] == base[q]["context"] and cal[q] == base[q]["calibration"], f"calibration mismatch {q}"
        rec["calibration_matches_archive"] = True
        for i, (cond, ch, dose, q) in enumerate(replay + main):
            arm = "baseline" if ch is None else (0, ch, dose)
            o = eng.generate([ctx[q]], arm, [cal[q]], 128, [])[0]
            o["token_sha256"] = token_hash(o["token_ids"])
            row = {"condition_id": cond, "layer": 0, "channel": ch, "dose": dose or 0.0, "question_id": q,
                   "calibration": cal[q], "intervention": eng.last_hook, "output": o, "ended_utc": io.utc()}
            io.immutable(out / f"records/{cond}__{q}.json", row)
            if cond.startswith("replay"):
                a = archived(cond, q)["output"]["token_ids"]
                assert o["token_ids"] == a, f"REPLAY MISMATCH {cond} {q}"
                rec["replay_ok"] = rec.get("replay_ok", 0) + 1
            assert all(not mm._forward_pre_hooks for mm in eng.modules.values())
            rec["done"] = i + 1; io.write(out / "receipt.json", rec)
            print(json.dumps({"w": worker, "done": i + 1, "of": rec["expected"], "cond": cond, "q": q,
                              "n": o["generated_token_count"], "s": round(o["batch_seconds"], 2)}), flush=True)
        rec["integrity"] = eng.verify_unchanged()
        rec.update(status="completed", ended_utc=io.utc(), wall_seconds=time.monotonic() - t0)
    except BaseException:
        rec.update(status="failed", error=traceback.format_exc(), ended_utc=io.utc())
        raise
    finally:
        io.write(out / "receipt.json", rec)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--worker", type=int, choices=(0, 1), required=True)
    ap.add_argument("--output", required=True); ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    if a.list:
        print(channels()); r, m = jobs(a.worker); print(len(r), len(m)); sys.exit(0)
    run(a.worker, a.output)
