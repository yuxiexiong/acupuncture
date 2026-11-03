"""Rehearse the frozen rubric on real archived records (must show both pass and fail)."""
import glob, json, sys, collections
sys.path.insert(0, sys.argv[1])
from rubric import record_label, channel_role
OLD = "/workspace/acupuncture/experiments/layer-survey-toy-v1-2026-10-27/survey-r01"
DOSE = "/workspace/acupuncture/experiments/layer-dose-survey-toy-v1-2026-10-27/survey-r01"
def labels(pattern):
    out = {}
    for f in glob.glob(pattern):
        d = json.load(open(f)); out[d["question_id"]] = record_label(d["output"], d["question_id"])
    assert len(out) == 8, (pattern, len(out))
    return out
res = {}
for m in ("2b", "4b", "9b"):
    L = labels(f"{OLD}/{m}-shard-0/records/baseline__Q0*.json"); res[f"{m}-baseline"] = (channel_role(L), L)
res["4b-L00-N4146-d1"] = (lambda L: (channel_role(L), L))(labels(f"{OLD}/4b-shard-*/records/L00-N004146__Q0*.json"))
res["9b-L00-N978-d1"] = (lambda L: (channel_role(L), L))(labels(f"{OLD}/9b-shard-*/records/L00-N000978__Q0*.json"))
res["4b-L04-N8043-d1"] = (lambda L: (channel_role(L), L))(labels(f"{OLD}/4b-shard-*/records/L04-N008043__Q0*.json"))
for dose in ("0p0625", "0p25", "0p5"):
    res[f"4b-L00-N4146-{dose}"] = (lambda L: (channel_role(L), L))(labels(f"{DOSE}/4b-shard-*/records/L00-N004146-D{dose}__Q0*.json"))
res["9b-L00-N978-0p25"] = (lambda L: (channel_role(L), L))(labels(f"{DOSE}/9b-shard-*/records/L00-N000978-D0p25__Q0*.json"))
for k, (r, L) in res.items():
    print(f"{k:22s} {r:6s}", " ".join(f"{q}:{L[q]}" for q in sorted(L)))
roles = {r for r, _ in res.values()}
assert res["4b-baseline"][0] == "CLEAN" and res["9b-baseline"][0] == "CLEAN", "baseline must pass CLEAN"
assert "STOP" in roles and "OTHER" in roles, "must demonstrate fail paths"
print("REHEARSAL PASS", sorted(roles))
