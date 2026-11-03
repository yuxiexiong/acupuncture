"""Apply the frozen rubric to run-r01 and evaluate the sufficiency gate."""
import glob, json, sys, collections
sys.path.insert(0, sys.argv[1])
from rubric import record_label, channel_role
D = sys.argv[1]
C = json.load(open(f"{D}/contract.json"))
labels = collections.defaultdict(dict); texts = {}
for f in glob.glob(f"{D}/run-r01/w*/records/L00-*.json"):
    r = json.load(open(f)); k = (r["channel"], r["dose"])
    labels[k][r["question_id"]] = record_label(r["output"], r["question_id"])
    texts[(k, r["question_id"])] = r["output"]["answer_text"][:60].replace("\n", "⏎")
flag = {1210, 1343, 4146}; out = {"per_channel": {}, "gate": {}}
for dose in C["doses"]:
    roles = collections.defaultdict(list)
    for ch in sorted({c for c, d in labels if d == dose}):
        L = labels[(ch, dose)]; assert len(L) == 8, (ch, dose, len(L))
        r = channel_role(L); roles[r].append(ch)
        out["per_channel"][f"N{ch}@{dose}"] = {"role": r, "labels": L}
        print(f"d={dose} N{ch:5d}{'*' if ch in flag else ' '} {r:5s}", " ".join(f"{q[1:]}:{L[q]}" for q in sorted(L)))
    out["gate"][str(dose)] = {k: v for k, v in roles.items()}
    print(f"d={dose}: STOP {len(roles['STOP'])} {roles['STOP']}  CLEAN {len(roles['CLEAN'])} {roles['CLEAN']}  OTHER {len(roles['OTHER'])}\n")
score = {d: min(len(out["gate"][str(d)].get("STOP", [])), len(out["gate"][str(d)].get("CLEAN", []))) for d in C["doses"]}
best = max(C["doses"], key=lambda d: (score[d], d == 0.5))
out["chosen_dose"] = best; out["gate_pass"] = score[best] >= 3
print("min(STOP,CLEAN) per dose:", score, "-> chosen", best, "GATE", "PASS" if out["gate_pass"] else "FAIL")
json.dump(out, open(f"{D}/analysis-r01.json", "w"), ensure_ascii=False, indent=1)
