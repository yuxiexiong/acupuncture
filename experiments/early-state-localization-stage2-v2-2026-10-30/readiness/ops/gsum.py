import json,statistics as st,sys
P={k:json.load(open(f"analysis/g_{k}-r01.json")) for k in ("development","history")}
lay=lambda c:int(c.split("_")[1][1:])
def m(d,c,key,r=None):
    return d[c][key]["mean"] if r is None else d[c]["arms"][key][r]["mean"]
print("L | dev stop(-,+) | dev fact(-,+) | hist stop(-,+) | hist fact(-,+) | dev TTT EOS(-,+) | dev share: linear-clean of stop | KV-clean of fact | linear-clean of fact")
for L in range(32):
    out=[]
    for k in ("development","history"):
        d=P[k]["conditions"]; cs=sorted([c for c in d if lay(c)==L])
        out.append(",".join(f"{m(d,c,'damage_stop'):5.1f}" for c in cs)); out.append(",".join(f"{m(d,c,'damage_fact'):5.1f}" for c in cs))
    d=P["development"]["conditions"]; cs=sorted([c for c in d if lay(c)==L])
    out.append(",".join(str(d[c]["stop"]["TTT"]["first_step_eos"]) for c in cs))
    def sh(c,code,r):
        dm=m(d,c,"damage_"+r); return f"{m(d,c,code,r)/dm:5.2f}" if abs(dm)>1 else "  -  "
    out.append(",".join(sh(c,"TCC","stop") for c in cs)); out.append(",".join(sh(c,"CTT","fact") for c in cs)); out.append(",".join(sh(c,"TCC","fact") for c in cs))
    print(f"L{L:02d} | "+" | ".join(out))
ks=sorted(P["development"]["conditions"])
for r in ("stop","fact"):
    a=[P["development"]["conditions"][c]["damage_"+r]["mean"] for c in ks]; b=[P["history"]["conditions"][c]["damage_"+r]["mean"] for c in ks]
    print("dev-vs-history corr", r, round(st.correlation(a,b),3))
