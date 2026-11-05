"""Plot complete candidate trajectory and eligible incumbent; no model imports."""
import os
os.environ.setdefault('MPLCONFIGDIR','/tmp/wsp-matplotlib')
import argparse,json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import numpy as np
p=argparse.ArgumentParser();p.add_argument('data',type=Path);a=p.parse_args()
d=json.loads(a.data.read_text());rows=d['rounds'];assert [r['round'] for r in rows]==list(range(1,len(rows)+1))
x=[0]+[r['round'] for r in rows];y=[d['baseline']*100]+[r['repair_score']*100 for r in rows]
best=[y[0]];excluded=[];peaks=[(0,y[0])]
for r,v in zip(rows,y[1:]):
 best.append(v if 'best' in r['selection'] else best[-1])
 if best[-1]>best[-2]:peaks.append((r['round'],v))
 if 'Protection failed' in r['selection'].get('not_selected',''):excluded.append((r['round'],v))
font=FontProperties(fname='/System/Library/Fonts/STHeiti Medium.ttc')
plt.rcParams.update({'font.size':12,'axes.spines.top':False,'axes.spines.right':False,'svg.fonttype':'path'})
fig,ax=plt.subplots(figsize=(13.6,6.8),dpi=160);fig.patch.set_facecolor('#fafbfc');ax.set_facecolor('#fafbfc')
ax.plot(x,y,color='#90a8bf',lw=1.6,marker='o',ms=3.6,label='每轮候选得分',zorder=2)
ax.step(x,best,where='post',color='#136bb0',lw=2.8,label='通过保护检查的历史最佳',zorder=3)
if excluded:
 ex,ey=zip(*excluded);ax.scatter(ex,ey,marker='x',s=85,lw=2,color='#d46537',label='损伤保护未通过',zorder=5)
ax.axhline(y[0],color='#89929c',ls='--',lw=1,zorder=1)
labels={0:(10,-29),1:(-13,22),4:(-10,26),9:(-7,24),17:(-6,30),25:(-12,30),37:(-24,32)}
for k,v in peaks:
 if k in labels:
  ax.annotate(f'{k}轮  {v:.2f}%' if k else f'原版  {v:.2f}%',(k,v),xytext=labels[k],textcoords='offset points',fontproperties=font,fontsize=10.5,color='#145386',arrowprops=dict(arrowstyle='-',color='#8ba2b7',lw=.8))
last=x[-1];ax.annotate(f'第{last}轮候选 {y[-1]:.2f}%',(last,y[-1]),xytext=(-125,-31),textcoords='offset points',fontproperties=font,fontsize=10.5,color='#637a91',arrowprops=dict(arrowstyle='-',color='#90a8bf',lw=.8))
ax.set_xlim(-.6,50.6);ax.set_ylim(56,75);ax.set_xticks([0,5,10,15,20,25,30,35,38,40,45,50]);ax.set_yticks(np.arange(58,75,2));ax.set_yticklabels([f'{v}%' for v in np.arange(58,75,2)])
ax.set_xlabel('完整修补评估轮次（0 = 原版基线）',fontproperties=font,labelpad=10)
ax.set_ylabel('开发集联合指标',fontproperties=font,labelpad=9)
ax.grid(axis='y',color='#e2e7ec',lw=.8);ax.spines['left'].set_color('#bec7cf');ax.spines['bottom'].set_color('#bec7cf')
if last<50:
 ax.axvspan(last+.25,50.6,color='#eef1f4',zorder=0);ax.text((last+50)/2,63.3,f'{last+1}–50轮\n将在50轮结束后补齐',ha='center',fontproperties=font,color='#7e8995',fontsize=11)
ax.legend(loc='lower right',prop=font,frameon=True,facecolor='white',edgecolor='#dce2e7')
fig.text(.08,.95,f'C：原版基线至第{last}轮的修补轨迹',fontproperties=font,fontsize=20,color='#172d40')
fig.text(.08,.90,'浅线显示每次尝试的起伏；深色阶梯线显示截至每轮保留的最佳水平。',fontproperties=font,fontsize=12,color='#5d6e7e')
fig.text(.08,.035,'同一固定开发集、batch64；这不是全部单题准确率，也不是独立测试结果。未绘制轮次不表示未运行。',fontproperties=font,fontsize=10.5,color='#687887')
fig.subplots_adjust(left=.08,right=.97,bottom=.16,top=.84)
for suffix in ['.png','.svg']:fig.savefig(a.data.with_suffix(suffix),dpi=160)
print(json.dumps({'rounds':len(rows),'baseline':y[0],'best':best[-1],'latest':y[-1],'protection_failed':[r[0] for r in excluded],'png':str(a.data.with_suffix('.png'))}))
