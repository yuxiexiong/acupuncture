import json
from collections import defaultdict, Counter
ARMS=('TTT','CTT','TCT','TTC','TCC','CTC','CCT')   # code order KV, R(ecurrent), conv
def load(panel):
    rows=[r for r in json.load(open(f'{panel}.joined.json'))['rows'] if str(r['arm']).startswith('all:')]
    D=defaultdict(dict); C={}
    for r in rows:
        arm=r['arm'][4:]; it=r['item_id']; lab=r['label']['fact']
        m=r['mech']; fs=(m['tokens']<=1 and m['end_reason']=='eos_token')
        rec={'lab':lab,'Y':int(lab=='follows_fact'),'first_stop':fs,'contra':r['label']['contradiction'],'rep':r['label']['repetition']}
        if arm=='CCC': C[it]=rec
        else: D[(r['condition']['layer'],r['condition']['dose'],r['condition']['channel'])][(arm,it)]=rec
    return D,C
def items(D):
    return sorted({it for k in D for (_,it) in D[k]})
