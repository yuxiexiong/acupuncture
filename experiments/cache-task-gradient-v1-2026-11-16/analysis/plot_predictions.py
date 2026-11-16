"""Render the frozen calibration rows, without fitting or adding statistical tests."""
import csv
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE=Path(__file__).resolve().parent
source=HERE.parent/'runs/formal-20261116-r01/analysis.json'
a=json.loads(source.read_text())
fig,axes=plt.subplots(1,2,figsize=(8,3.8),layout='constrained')
all_rows=[]
for ax,b in zip(axes,('C','H')):
    s=a['calibration'][b];rows=s['rows']
    xs=[r['observed'] for r in rows];ys=[r['prediction'] for r in rows]
    lo=min(xs+ys);hi=max(xs+ys);pad=max(.1,(hi-lo)*.06)
    ax.plot([lo-pad,hi+pad],[lo-pad,hi+pad],color='0.45',ls='--',lw=1,label='Identity')
    ax.scatter(xs,ys,s=16,alpha=.55,color='#0072B2' if b=='C' else '#D55E00',edgecolors='none')
    ax.set(xlim=(lo-pad,hi+pad),ylim=(lo-pad,hi+pad),xlabel='Observed gate-exchange effect (logits)',ylabel='First-order prediction (logits)',
           title=f"{b}: {'PASS' if s['passed'] else 'FAIL'} | MAE {s['mae']:.3f}")
    ax.set_aspect('equal',adjustable='box');ax.spines[['top','right']].set_visible(False)
    for r in rows:all_rows.append({'background':b,**{k:r[k] for k in ('receiver','donor','scenario','observed','prediction','error','absolute_error')}})
fig.savefig(HERE/'predicted-vs-observed.png',dpi=180)
fig.savefig(HERE/'predicted-vs-observed.svg')
plt.close(fig)
svg=HERE/'predicted-vs-observed.svg'
svg.write_text('\n'.join(line.rstrip() for line in svg.read_text().splitlines())+'\n')
with (HERE/'predictions.csv').open('w') as f:
    w=csv.DictWriter(f,fieldnames=list(all_rows[0]),lineterminator='\n');w.writeheader();w.writerows(all_rows)
print('Rendered',len(all_rows),'frozen observations; no fitted line or added tests')
