# -*- coding: utf-8 -*-
"""Build one offline advisor report from archived observations; never runs a model."""
import collections
import hashlib
import html
import io
import json
import os
from pathlib import Path
import re

os.environ.setdefault('MPLCONFIGDIR', '/tmp/acupuncture-advisor-mpl')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
MD = ROOT / 'docs/Acupuncture_实验总结_导师版_2026-10-28.md'
OUT = ROOT / 'docs/Acupuncture_实验结果_导师展示_2026-10-28.html'
E = html.escape
MODELS = ['2b', '4b', '9b', 'llama31-8b-instruct']
NAMES = ['Qwen 2B', 'Qwen 4B', 'Qwen 9B', 'Llama 8B']
DOSES = [-1, -.5, -.25, -.125, -.0625, .0625, .125, .25, .5, 1]
NAVY, TEAL, RED, GOLD = '#253f59', '#147d86', '#b6503d', '#b98a37'
plt.rcParams.update({'font.size': 11, 'axes.spines.top': False,
    'axes.spines.right': False, 'axes.labelcolor': NAVY, 'text.color': NAVY,
    'xtick.color': NAVY, 'ytick.color': NAVY, 'axes.edgecolor': '#b6c1cb',
    'svg.fonttype': 'path', 'figure.facecolor': 'white', 'axes.facecolor': 'white'})

def records(rel):
    rows = [json.loads(s) for s in (ROOT / rel).read_text().splitlines()]
    for r in rows:
        if 'dose' not in r and r.get('layer') is not None:
            r['dose'] = r['intervention']['dose']
    return rows

ten = records('experiments/layer-survey-toy-v1-2026-10-27/delivery-r01/all.records.jsonl')
ten += records('experiments/llama31-layer-survey-v1-2026-10-28/delivery-r01/all.records.jsonl')
dose = records('experiments/layer-negative-dose-survey-toy-v1-2026-10-27/delivery-r01/all.records.jsonl')
dose += records('experiments/llama31-single-point-dose-survey-v1-2026-10-28/delivery-r01/all.records.jsonl')

def measure(r):
    ids = r['output']['token_ids']
    grams = [tuple(ids[i:i+4]) for i in range(max(0, len(ids)-3))]
    repeated = (len(grams)-len(set(grams))) / max(1, len(grams))
    return [1, int(len(ids)==1 and r['output']['end_reason']=='eos_token'), int(repeated>=.5)]

def aggregate(rs, key):
    result = collections.defaultdict(lambda: np.zeros(3, dtype=int))
    for r in rs:
        if r.get('layer') is not None:
            result[(r['model_id'], r[key])] += measure(r)
    return result

layers = aggregate(ten, 'layer')
doses = aggregate(dose, 'dose')
assert len(layers)==120 and all(v[0]==80 for v in layers.values())
assert len(doses)==40 and all(v[0]==(192 if m=='2b' else 256) for (m,d),v in doses.items())
assert sum(v[1] for (m,l),v in layers.items() if m=='4b')==202
assert sum(v[2] for (m,l),v in layers.items() if m=='llama31-8b-instruct')==302
analysis = ROOT / 'experiments/layer-trace-extension-v1-2026-10-28/analysis-early-r01'
cases = json.loads((analysis / 'fourb-cases.json').read_text())
cross = json.loads((analysis / 'cross-model-cases.json').read_text())['cases']
md = MD.read_text()
assert 'N6676、1741各3/8' not in md
assert not re.search(r'https?://|\[[^\]]+\]\(', md)

svg_index = 0
def svg(fig):
    global svg_index
    svg_index += 1
    out = io.StringIO()
    fig.savefig(out, format='svg', bbox_inches='tight', metadata={'Date': None})
    plt.close(fig)
    s = out.getvalue(); s = s[s.index('<svg'):]
    # Each embedded plot has independent clip paths and glyph definitions.
    ids = re.findall(r'id="([^"]+)"', s)
    for ident in sorted(set(ids), key=len, reverse=True):
        s = s.replace(f'id="{ident}"', f'id="f{svg_index}_{ident}"')
        s = s.replace(f'#{ident}"', f'#f{svg_index}_{ident}"')
        s = s.replace(f'#{ident})', f'#f{svg_index}_{ident})')
    return s

def plot(fig, label, wide=False):
    return f'<div class="plot {"wide" if wide else ""}" role="img" aria-label="{E(label)}">{svg(fig)}</div>'

def heat(metric, title, cmap):
    arr=np.full((4,32), np.nan)
    for (m,l),v in layers.items():arr[MODELS.index(m),l]=v[metric]
    fig,ax=plt.subplots(figsize=(11.6,2.65))
    cm=plt.get_cmap(cmap).copy();cm.set_bad('#edf0f2')
    im=ax.imshow(arr, vmin=0, vmax=80, cmap=cm, aspect='auto')
    ax.set_yticks(range(4),NAMES);ax.set_xticks(range(0,32,2),range(0,32,2))
    ax.set_xlabel('Injection layer (zero-based)');ax.set_title(title,loc='left',fontweight='bold',pad=12)
    for y in range(4):
        for x in range(32):
            v=arr[y,x]
            if np.isfinite(v) and v>=40:
                ax.text(x,y,str(int(v)),ha='center',va='center',fontsize=9,color='white' if v>54 else NAVY)
    ax.text(27.5,0,'No layers 24–31',ha='center',va='center',fontsize=10,color='#657583')
    cb=fig.colorbar(im,ax=ax,pad=.018,aspect=20);cb.set_label('Count / 80')
    return plot(fig,title,True)

def dose_plot(model):
    fig,ax=plt.subplots(figsize=(5.35,3.2))
    values=np.array([doses[(model,d)] for d in DOSES]); x=np.arange(10)
    for i,c,label,marker in [(1,RED,'First-token EOS','o'),(2,TEAL,'Repetition','s')]:
        ax.plot(x,100*values[:,i]/values[:,0],color=c,marker=marker,ls='--',lw=1.3,ms=5,label=label)
    ax.axvline(4.5,color='#d6dde2',lw=.8)
    ax.set_ylim(0,52);ax.set_xlim(-.35,9.35);ax.set_yticks([0,10,20,30,40,50])
    ax.set_xticks(x,['−1','−½','−¼','−⅛','−¹⁄₁₆','+¹⁄₁₆','+⅛','+¼','+½','+1'],fontsize=10)
    ax.set_ylabel('Observed fraction (%)');ax.set_xlabel('Tested dose levels')
    ax.set_title(NAMES[MODELS.index(model)],loc='left',fontweight='bold')
    ax.grid(axis='y',color='#e8ecef',lw=.7);ax.set_axisbelow(True)
    ax.legend(frameon=False,fontsize=10,loc='upper center')
    return plot(fig,'正负剂量机械指标：'+model)

def propagation():
    fig,axs=plt.subplots(1,2,figsize=(11.6,3.6))
    for d,c in [(.25,'#99aab7'),(.5,TEAL),(1,RED)]:
        case=next(x for x in cases if x['intervention']['layer']==0 and x['intervention']['dose']==d)
        vals=[s['relative_delta'] for s in case['sites_by_step']['0'] if s['name'].endswith('.residual')]
        axs[0].plot(range(32),vals,label=f'dose +{d:g}',color=c,lw=1.8)
    ax=axs[0];ax.set_xlabel('Observed layer');ax.set_ylabel('Residual relative difference')
    ax.set_title('4B L0 / N4146 · first prediction',loc='left',fontweight='bold')
    ax.legend(frameon=False,fontsize=10);ax.set_xlim(0,31);ax.set_xticks([0,8,16,24,31])
    values=[-17.6875,-8.25,3.0625];labels=['Clean','Dose +0.5','Dose +1']
    ax=axs[1];ax.barh(labels,values,color=['#99aab7',TEAL,RED],height=.48)
    ax.axvline(0,color=NAVY,lw=.8);ax.set_xlim(-21,8)
    for i,v in enumerate(values):ax.text(v+.5,i,f'{v:+.4f}',va='center',ha='left',fontsize=11,color='white' if i==1 else NAVY)
    ax.set_xlabel('EOS logit − best non-EOS logit')
    ax.set_title('Positive margin: stop token wins',loc='left',fontweight='bold');ax.invert_yaxis()
    fig.tight_layout(w_pad=3)
    return plot(fig,'4B早层干预的全层残差差异和停止优势',True)

def benchmark():
    base=np.array([[67.99,65,88,53],[54.06,52.5,61,37],[70.06,71.5,93,70],[66.98,58.5,67,63]])
    inj=np.array([[29.74,38,0,4],[46,31,0,3],[25.39,30,0,0],[26.86,34.5,0,0]])
    titles=['4B · original two-needle','2B · transferred sparse recipe','9B · transferred sparse recipe','Llama · transferred dense vector']
    result=[]
    for i in range(4):
        fig,ax=plt.subplots(figsize=(5.35,3.1)); y=np.arange(4)
        ax.hlines(y,inj[i],base[i],color='#b9c8d1',lw=3)
        ax.scatter(base[i],y,c=NAVY,marker='o',s=55,label='Baseline',zorder=3)
        ax.scatter(inj[i],y,c=RED,marker='s',s=45,label='Intervention',zorder=3)
        for j,(a,b) in enumerate(zip(base[i],inj[i])):
            ax.text(a,j-.18,f'{a:g}',ha='center',fontsize=10)
            ax.text(b,j+.30,f'{b:g}',ha='center',fontsize=10,color=RED)
        ax.set_yticks(y,['MMLU','ARC-C','GSM8K','HumanEval']);ax.invert_yaxis()
        ax.set_ylim(3.6,-.6);ax.set_xlim(-5,105);ax.set_xticks([0,25,50,75,100])
        ax.set_xlabel('Task score (%)');ax.set_title(titles[i],loc='left',fontsize=11,fontweight='bold')
        ax.grid(axis='x',color='#e8ecef');ax.set_axisbelow(True)
        result.append(plot(fig,titles[i]))
    return ''.join(result)

def repair():
    fig,ax=plt.subplots(figsize=(7.6,2.9))
    vals=[18,15,24,15,18];labels=['Baseline','Two-needle','C01 repair','Matched repair','Reverse replay']
    ax.bar(range(5),vals,color=['#99aab7',RED,TEAL,'#aebbc5',GOLD],width=.55)
    for i,v in enumerate(vals):ax.text(i,v+.5,f'{v}/32',ha='center',fontsize=11)
    ax.set_ylim(0,32);ax.set_yticks([0,8,16,24,32]);ax.set_ylabel('MMLU correct / 32')
    ax.set_xticks(range(5),labels,fontsize=10);ax.axhline(18,color=NAVY,lw=.8,ls='--')
    ax.set_title('C01 · L23 attention · prompt final position',loc='left',fontweight='bold')
    return plot(fig,'C01修复优于干预但反向重现未降低正确率',True)

def table_from_md(header, caption):
    lines=md.splitlines();i=next(i for i,l in enumerate(lines) if l==header)
    block=[]
    while i<len(lines) and lines[i].startswith('|'):block.append(lines[i]);i+=1
    cells=lambda line:[c.strip() for c in line.strip('|').split('|')]
    out='<div class="table-scroll"><table><caption>'+E(caption)+'</caption><thead><tr>'
    out+=''.join('<th>'+E(c)+'</th>' for c in cells(block[0]))+'</tr></thead><tbody>'
    for line in block[2:]:
        out+='<tr>'+''.join('<td>'+E(c.replace('**',''))+'</td>' for c in cells(line))+'</tr>'
    return out+'</tbody></table></div>'

appendix=''
for header,caption in [
    ('| 模型 | 抽测不同通道 | 有完整正负五档的通道 | 十点阶段干预回答 | 新增弱正剂量 | 新增负剂量 | 三阶段唯一来源，含8原版 |','Qwen完整数量总账'),
    ('| 注入层 | 2B | 4B | 9B | Llama 8B |','全部层：首步EOS / 机械重复，每格分母80'),
    ('| 剂量 | 2B，分母192 | 4B，分母256 | 9B，分母256 | Llama，分母256 |','全部剂量：首步EOS / 机械重复'),
    ('| 条件 | 9B MMLU | 9B ARC | 2B MMLU | 2B ARC |','迁移19条件：各任务32题，百分比'),
    ('| 条件 | MMLU | ARC-C |','Llama稠密迁移10条件：各任务32题，百分比'),
    ('| 条件 | MMLU答对/32 | ARC-C答对/32 |','拆针、剂量、随机对照：完整17条件'),
    ('| 候选 | 组件／位置 | MMLU margin | MMLU正确率 | ARC margin | ARC正确率 |','局部修复：全部十候选四项比较'),
    ('| 工作 | 已完成的内容 | 尚未完成或明确排除的内容 |','全部工作的完成、停止及未运行状态'),
    ('| 实验 | 正式运行时间，北京时间 | 实际墙钟或正式worker窗口 | 正式worker累计小时 |','执行时间与成本口径')]:
    appendix+=f'<details><summary>{E(caption)}</summary>'+table_from_md(header,caption)+'</details>'

def example_data():
    groups=[('4b',6,7840,'Q04','4B L6 N7840 · 整理书桌'),
        ('llama31-8b-instruct',4,9472,'Q04','Llama L4 N9472 · 整理书桌'),
        ('4b',7,6650,'Q07','4B L7 N6650 · 未知天气'),
        ('llama31-8b-instruct',17,7938,'Q06','Llama L17 N7938 · 贡献登记')]
    result=[]
    for model,layer,ch,q,title in groups:
        rs=[r for r in dose if r['model_id']==model and r['question_id']==q and r.get('layer')==layer and r.get('channel')==ch]
        baseline=next(r for r in dose if r['model_id']==model and r['question_id']==q and r.get('layer') is None)
        assert len(rs)==10
        result.append({'title':title,'prompt':baseline['prompt'],'baseline':baseline['output']['answer_text'],
            'answers':{str(r['dose']):{'text':r['output']['answer_text'],'tokens':r['output']['generated_token_count'],'end':r['output']['end_reason']} for r in rs}})
    return result

heat_eos=heat(1,'A  First-token EOS','OrRd')
heat_rep=heat(2,'B  Mechanical repetition','GnBu')
dose_figs=''.join(dose_plot(m) for m in MODELS)
prop=propagation();bench=benchmark();rep=repair()
payload=json.dumps({'examples':example_data(),'markdown':md},ensure_ascii=False).replace('</','<\\/')
md_hash=hashlib.sha256(md.encode()).hexdigest()

page='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Acupuncture｜从单针扰动到内部传播</title>
<style>
:root{--ink:#20374c;--muted:#617180;--rule:#dbe2e7;--teal:#147d86;--red:#b6503d;--paper:#fff;--wash:#f3f6f7}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--paper);color:var(--ink);font:16px/1.7 -apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif;font-variant-numeric:tabular-nums}
main{max-width:1180px;margin:auto;padding:42px 44px 60px}.eyebrow{font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:var(--teal);font-weight:650}h1{font:700 clamp(30px,4vw,49px)/1.22 "Songti SC","Noto Serif CJK SC",serif;margin:20px 0}h2{font:650 27px/1.4 "Songti SC",serif;margin:0}h3{font-size:17px;margin:0 0 9px}p{margin:8px 0}small,.caption{font-size:13px;color:var(--muted)}.lead{font-size:19px;max-width:900px}.meta{display:flex;gap:24px;flex-wrap:wrap;font-size:13px;color:var(--muted);margin:20px 0}
nav{display:flex;gap:8px 22px;flex-wrap:wrap;padding:18px 0;border-top:1px solid var(--rule);border-bottom:1px solid var(--rule);margin-top:26px}a{color:var(--ink);text-decoration:none}nav a{font-size:14px}nav a:hover{text-decoration:underline}button,select{font:inherit;border:1px solid #b5c2cb;border-radius:3px;background:white;color:var(--ink);padding:8px 13px}button{cursor:pointer}button:hover{background:var(--wash)}button:focus-visible,select:focus-visible,a:focus-visible{outline:3px solid #8ac5ce;outline-offset:3px}
section{padding:42px 0;border-bottom:1px solid var(--rule)}.section-head{display:grid;grid-template-columns:50px 1fr;gap:12px;margin-bottom:24px}.num{font:italic 27px Georgia,serif;color:var(--teal)}.subhead{margin:5px 0 0;color:var(--muted);font-size:14px}.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:25px;padding:28px 0 0}.stat b{font:500 36px/1.2 Georgia,serif;display:block}.stat span{font-size:13px;color:var(--muted)}.grid2{display:grid;grid-template-columns:1fr 1fr;gap:28px}.grid3{display:grid;grid-template-columns:repeat(3,1fr);gap:24px}.route{display:grid;grid-template-columns:repeat(5,1fr);gap:12px}.route article{position:relative;border-top:3px solid var(--teal);padding-top:13px}.route article:not(:last-child):after{content:'→';position:absolute;right:1px;top:10px;color:#8b9da8}.route b{font-size:15px}.route p{font-size:14px}.route strong{font:600 22px Georgia,serif}.strip{background:var(--wash);border-left:3px solid var(--teal);padding:14px 18px;margin:20px 0}.strip p{margin:0}.note{font-size:13px;color:var(--muted);margin:14px 0}.plot{overflow-x:auto}.plot svg{display:block;width:100%;height:auto;min-width:330px}.plot.wide svg{min-width:760px}.figlabel{font-size:13px;color:var(--muted);margin:9px 0 18px}.insight{border-top:1px solid var(--rule);padding:16px 0}.insight b{color:var(--teal)}.flow{display:flex;gap:12px;align-items:stretch;flex-wrap:wrap;margin:20px 0}.flow .node{flex:1;min-width:145px;background:var(--wash);padding:15px;text-align:center}.flow .arrow{align-self:center;color:var(--teal);font-size:23px}.node strong{font-size:16px}.node small{display:block}.chip{display:inline-block;font-size:12px;padding:2px 8px;background:#e5f2f2;color:#13616a;margin-bottom:8px}.chip.pending{background:#f4ead9;color:#825f20}.controls{display:flex;gap:16px;flex-wrap:wrap;align-items:end;margin:14px 0}.controls label{display:grid;gap:5px;font-size:13px}.answer{background:var(--wash);padding:18px;min-height:150px}.answer pre{font-family:inherit;font-size:15px;line-height:1.8;white-space:pre-wrap;overflow-wrap:anywhere;margin:0}.answer h3{font-size:14px;color:var(--muted)}.answer.changed{border-left:3px solid var(--red)}.micro{display:flex;gap:32px;margin:14px 0;font-size:13px}.micro b{font-size:20px}.evidence{display:grid;grid-template-columns:1fr 1fr;gap:24px}.evidence article{border-left:3px solid var(--teal);padding:4px 16px}.evidence article.pending{border-color:var(--red)}.evidence p{font-size:15px}.table-scroll{overflow:auto}table{border-collapse:collapse;width:100%;font-size:13px;line-height:1.6}th,td{padding:9px 10px;border-bottom:1px solid var(--rule);text-align:left}th{background:var(--wash);font-weight:600}caption{text-align:left;font-size:14px;margin:14px 0}details{border-bottom:1px solid var(--rule);padding:12px 0}summary{cursor:pointer;font-size:15px;font-weight:550}details p{font-size:13px;color:var(--muted)}footer{font-size:12px;color:var(--muted);padding-top:20px;overflow-wrap:anywhere}.print{margin-left:auto}.endline{font:600 24px/1.6 "Songti SC",serif;border-top:3px solid var(--ink);padding-top:20px;margin-top:25px}
.explain{margin:20px 0 26px;max-width:960px}.explain p{margin:10px 0;line-height:1.85}.reading{padding:17px 20px;background:#f5f8fa;border-left:3px solid #9aafbd;margin:18px 0}.reading p{margin:7px 0}.reading strong{color:var(--ink)}.glossary{margin:22px 0}.glossary article{border-top:1px solid var(--rule);padding:14px 0}.glossary p{font-size:15px;line-height:1.8}.case-guide{margin:18px 0;padding-left:18px;border-left:3px solid var(--teal);line-height:1.85}.strip p+p{margin-top:10px}.insight small,.evidence small{font-size:14px;line-height:1.8}
@media(max-width:700px){main{padding:25px 18px}.stats{grid-template-columns:1fr 1fr;gap:22px}.grid2,.grid3,.evidence{grid-template-columns:1fr}.route{grid-template-columns:1fr 1fr}.section-head{grid-template-columns:32px 1fr}h2{font-size:23px}.route article:last-child{grid-column:1/-1}.lead{font-size:17px}.micro{gap:16px}.controls select{max-width:100%}.print{margin-left:0}}
@media print{main{max-width:none;padding:0 5mm}nav,.controls,.print,.download{display:none}section{break-inside:avoid;padding:20px 0}.plot svg,.plot.wide svg{min-width:0}.grid2{grid-template-columns:1fr 1fr}details:not([open]){display:none}.answer{min-height:0}.stats{grid-template-columns:repeat(4,1fr)}body{font-size:11pt}.caption,.note{font-size:9pt}h1{font-size:28pt}h2{font-size:18pt}}
</style></head><body><main>
<header><div class="eyebrow">ACUPUNCTURE · Research progress · 2026.10.28</div>
<h1>从单针扰动<br>到模型内部传播</h1>
<p class="lead">我们想弄清楚：<strong>为什么只改模型内部一个通道，回答就可能从正常变成空白、跑题或反复重复？这些变化在不同模型里，是否经过相似的过程？</strong></p>
<div class="explain"><p>目前已经看到：影响不只取决于“针插在哪一层”，还取决于具体通道、问题和剂量。同一个点，轻一点可能仍能回答，换一个剂量可能混入无关内容，再加强又可能直接停止；也有剂量更强、回答反而重新通顺的反例。</p><p>我们还记录了模型逐层计算和逐步选词的变化，开始把“内部改了什么”和“最后为什么这样回答”连起来。不过，现有结果还不能把某一层命名为“语言区”“推理区”，也不能证明模型与人脑有相同的功能分区。下面按<strong>实验做法 → 外部表现 → 内部过程 → 证据还缺什么</strong>展开。</p></div>
<div class="meta"><span>Qwen3.5 · 2B / 4B / 9B</span><span>Llama 3.1 · 8B Instruct</span><span>既有结果核对版 · 未新增模型实验</span></div>
<nav aria-label="报告目录"><a href="#road">实验路线</a><a href="#layer">位置差异</a><a href="#dose">剂量效应</a><a href="#trace">内部传播</a><a href="#legacy">能力与迁移</a><a href="#direction">研究方向</a><a href="#evidence">完整数据</a><button class="print" onclick="window.print()">打印 / 存为PDF</button></nav>
<div class="stats"><div class="stat"><b>18,272</b><span>四个模型单针调查的回答记录，已去重</span></div><div class="stat"><b>1,200</b><span>实际测试的层内通道，每层抽10个</span></div><div class="stat"><b>120</b><span>继续比较正负十档剂量的通道</span></div><div class="stat"><b>7,632</b><span>沿用旧条件、补录内部过程的记录</span></div></div>
<p class="note">这四个数字分别表示回答数、测试位置数、剂量测试位置数和内部记录数，不能相加。7,632份内部记录对应18,272份回答中的一部分；不是又增加了7,632个独立实验样本。每个模型的8份原版回答在不同条件间共用。</p></header>

<section id="road"><div class="section-head"><div class="num">01</div><div><h2>我们做了什么</h2><p class="subhead">2026年10月25—28日 · 从异常输出走向可检查的内部证据</p></div></div>
<div class="explain"><p>起点是一组能明显改变回答的“双针”配方，也就是同时改两个内部通道。我们先确认它是否只改变表达风格，还是同时损害答题能力。随后把问题拆开：每次只改一个点，逐层抽样；再固定位置改变剂量；最后对已做过的条件补录内部计算，追查变化如何传到答案。</p><p>这样安排的目的，是避免只凭一段惊人的回答就给通道命名。例如，某个点让回答出现一个主题，并不自动说明它平时就专门负责这个主题；它也可能打乱了正常计算，使某些词更容易被选中。</p></div>
<div class="route"><article><b>先确认现象</b><p><strong>24</strong> 道探索题</p><small>双针让回答明显改变<br>也出现失序和能力下降</small></article><article><b>检查能力与迁移</b><p><strong>4</strong> 类能力任务</p><small>原版与干预版逐题比较<br>再检查其他模型的表现</small></article><article><b>拆成单点调查</b><p><strong>120</strong> 个层位置</p><small>每层抽10个通道<br>其中1个比较正负十档</small></article><article><b>补录内部过程</b><p><strong>7,632</strong> 条</p><small>沿用原来的实验条件<br>记录每层和每步选词</small></article><article><b>追问具体原因</b><p><strong>尚未证实</strong></p><small>已有传播和循环线索<br>关键作用环节仍待确定</small></article></div>
<div class="glossary grid3"><article><h3>“层”和“通道”是什么？</h3><p>模型每次预测下一小段文字，都依次经过多层计算。层号从0开始：4B有32层，即L0—L31。在一层的MLP计算模块里，还有许多数值通道；N4146是该层内的一个坐标编号。它不是人脑神经元，也不代表跨模型通用的功能编号。</p></article><article><h3>“插针”到底改了什么？</h3><p>我们在指定通道的数值上加一个固定偏移，随后让模型继续正常计算。这个偏移在读入问题和生成回答的全过程持续施加。模型的权重没有被训练或永久修改，每个实验条件都从原模型、独立上下文开始。</p></article><article><h3>“剂量”和“token”怎么理解？</h3><p>剂量控制偏移的方向与强弱，正负表示沿同一数值方向增加或减少，不代表好坏。token是模型一次输出的文字单位，可能是一个字、词的一部分或特殊标记，不等于汉字数。EOS则是“到这里结束”的特殊标记。</p></article></div>
<div class="grid2" style="margin-top:26px"><div><h3>主线数量：只算新增来源</h3><div class="flow"><div class="node"><strong>Qwen 13,400</strong><small>7,064十点＋2,816正档＋3,520负档</small></div><div class="arrow">＋</div><div class="node"><strong>Llama 4,872</strong><small>2,568十点＋2,304新增剂量</small></div></div></div><div><h3>干预方法：稀疏不等于微弱</h3><div class="flow"><div class="node"><strong>单个MLP通道</strong><small>提示及生成全程加常量</small></div><div class="arrow">→</div><div class="node"><strong>偏移进入后续状态</strong><small>直接改动的大小 = |剂量| × 原版参考大小</small></div></div></div></div>
<div class="explain"><p><strong>每个位置怎么测试：</strong>四个模型使用相同的8道中文探索题。每层预先抽10个不同通道，每次只给其中一个通道加+1剂量；再按固定规则从这10个点中选1个，补齐其他九档剂量。位置在实验前确定，没有看完结果再挑“最有效”的点。2B有24层，其余三个模型各32层，因此一共是120个层位置、1,200个抽测通道。</p><p><strong>这里的“单针”不一定是小扰动：</strong>剂量经过尺度校准。在直接注入的位置，|剂量|为1时，新增向量的长度与该问题原版内部状态的参考长度相当；0.5时约为其一半。所以“只改一个通道”说明位置很集中，不能据此说影响幅度很小。</p><p><strong>如何避免把重复记录当成新证据：</strong>后续剂量表复用了已经生成的+1回答和原版回答，因此数量按去重后计算。模型每步选最高分候选，即贪心生成，最多输出128个新token。这不是对同一条件反复随机采样；8道题也不是8次完全相同的重复试验。</p></div></section>

<section id="layer"><div class="section-head"><div class="num">02</div><div><h2>位置有差异，但没有整齐的“功能区边界”</h2><p class="subhead">十点扫描 · 每个模型—层80份回答 · 固定正剂量+1</p></div></div>
<div class="explain"><p><strong>这一组图回答：把相同标度的干预放在不同深度，是否更容易出现某类异常？</strong>我们先看两种可以直接从记录中计算的现象：“还没回答就结束”和“大量重复”。它们不需要先给文本贴上“人格改变”或“某种能力消失”的标签。</p></div>
<div class="reading"><p><strong>怎么看热图：</strong>每行是一个模型，每列是插针的层。每格包含10个通道×8道题＝80份回答，颜色越深，出现该现象的回答越多；例如64表示64/80。2B只有24层，右侧灰色区域表示没有这些层，不是测试结果为零。</p><p><strong>上图 A（First-token EOS）：</strong>模型的第一个输出就是结束标记，正文为空。<strong>下图 B（Mechanical repetition）：</strong>用连续四个token组成的小片段检查重复；四token片段再次出现的位置占比达到50%就计入。这个指标帮助定位循环，但不能自动判断事实错误、跑题、语气变化或所有形式的重复。</p></div>
__HEAT_EOS____HEAT_REP__
<div class="grid3"><div class="insight"><b>Qwen：首步停止偏早</b><p>4B L0 / L1 / L2：<strong>79 / 64 / 46</strong> 份首步EOS，各层分母80。</p></div><div class="insight"><b>循环遍布深度</b><p>9B L14机械重复<strong>64/80</strong>；最后一层仍有<strong>41/80</strong>。</p></div><div class="insight"><b>跨架构症状不相同</b><p>Llama首步EOS为<strong>0/2,560</strong>，机械重复却有<strong>302/2,560</strong>。</p></div></div>
<div class="explain"><p><strong>图里最清楚的差别：</strong>在这批+1测试中，4B最前面几层特别容易直接空答，L0的80份回答里有79份如此；但重复并不只出现在前层，9B到了中间和最后一层仍有大量重复。Llama则没有出现“第一个token就结束”，却仍有302份回答达到机械重复标准。这说明不同模型、不同位置的异常表现并不相同。</p><p><strong>不能把浅色直接看作更健康：</strong>一句话都没开始就结束的回答，本来就没有机会继续重复；正常结束的回答也可能答错或离题。两张图必须一起看，再点开原文，才能知道到底发生了什么。这里统计的也是固定8题和抽中的10个点，不代表整层所有通道的异常比例。</p></div>
<div class="strip"><p><strong>同一层，换一个通道就可能出现另一种结果。</strong>4B L2的N198、N575、N4736各有8/8首步结束；同层N5251却是0/8首步结束、7/8机械重复。</p><p>因此，目前可以说“不同深度的响应有差异”，还不能说“这一整层负责停止，那一整层负责语言”。早层的变化会经过更多后续层，这种传播距离的差异，也可能参与造成图上的深浅变化。</p></div></section>

<section id="dose"><div class="section-head"><div class="num">03</div><div><h2>剂量更强，不一定每次都更糟</h2><p class="subhead">每层固定一个通道 · 正负各五档 · 同时观察空答与重复</p></div></div>
<div class="explain"><p>只看+1可能漏掉很多信息：强剂量让模型直接空答，就看不到它在较弱干预下本来会写什么。因此我们固定通道、问题和校准方式，只改变剂量，检查回答是逐渐变化，还是在几个档位之间突然换成另一类表现。</p></div>
<div class="reading"><p><strong>怎么看四张曲线图：</strong>每张图对应一个模型，横轴是实际测过的十档剂量，左边为负、右边为正；靠近中间的幅度较小。红色圆点表示首步空答比例，绿色方点表示机械重复比例，纵轴是百分比。每个点汇总该模型所有层的入选通道和8道题：2B每档192份，其他模型每档256份。</p><p>横轴按档位等距排列，剂量之间的数值间隔并不相等；虚线只是方便看相邻档位的结果，不代表中间没测过的剂量也沿着这条线变化。这是多层汇总，不是某一个通道的曲线。</p></div>
<div class="grid2">__DOSE_FIGS__</div>
<div class="explain"><p><strong>总体比例与单点过程要分开读：</strong>降低剂量常能减轻强剂量造成的空答或循环，但个别点并不遵循“越强越坏”。例如Llama的一个点在+0.25循环，在+0.5和+1却重新给出通顺建议。汇总图会把这些不同过程放在同一个比例里，所以还要看下面的逐条原文。</p><p><strong>正负也不是“损伤／修复”的一对开关：</strong>负剂量是从原模型独立开始的另一种干预，不是给已经受损的模型拔针。它可能改善某道题，也可能引入新的错误或主题；正负回答相反，不等于模型被正确地双向控制。两条曲线都为零时，也只能说这两类机械异常没出现，不能说答案一定正确。</p></div>
<h3>同一点的真实回答：只换剂量，看它具体写了什么</h3>
<p>先选一个案例，再切换剂量。左边始终是该模型对同一道题的原版回答，右边是所选剂量的完整输出。建议先看+0.25、+0.5、+1，再看负侧；不只看句子是否通顺，还要看是否回答了问题、是否夹入无关内容、是否提前停下。</p>
<div class="controls"><label>案例<select id="example"></select></label><label>剂量<select id="dose-choice"></select></label><span id="answer-meta" class="caption" aria-live="polite"></span></div><p id="prompt"></p>
<div class="grid2"><div class="answer"><h3>原版自由回答</h3><pre id="baseline"></pre></div><div class="answer changed"><h3>干预后完整回答</h3><pre id="modified"></pre></div></div>
<div class="case-guide" id="case-explanation" aria-live="polite"></div>
<p class="note">这些代表案例是读完结果后选出的，用来展示“可能怎样变化”，不能用来估算这类现象有多常见。原版也可能答错；达到128-token上限不自动等于失败，遇到结束标记也不自动等于答对。</p></section>

<section id="trace"><div class="section-head"><div class="num">04</div><div><h2>内部变化如何走到输出分叉</h2><p class="subhead">4B L0 N4146 · Q04整理书桌 · 预测第一个token之前</p></div></div>
<div class="explain"><p><strong>仅有回答，还缺少中间一段：</strong>我们知道针插在哪里，也知道最后出现了空答或循环，但不知道两者之间发生了什么。为此，我们在原有条件上加了只负责记录的hook，像在计算过程里装记录器，保存各层模块输出和层末状态的大小、方向相似度、两支差异等摘要，以及每一步对候选token的打分。这里没有增加新的插针位置或剂量，也没有保存整个模型的全部高维内部数值。</p><p><strong>先看最容易对齐的一步：</strong>下面取4B回答“整理书桌”的第一个预测位置。此时还没有生成正文，两个分支读到的问题完全相同。+1的变化先出现在被注入的L0 MLP，之后在L1及更深层的计算中继续出现；到最后选词时，首选从开始回答变成了结束。</p></div>
<div class="flow"><div class="node"><strong>L0注入前</strong><small>attention模块输出差异为0</small></div><div class="arrow">→</div><div class="node"><strong>L0 MLP内加偏移</strong><small>+1时，输出差分长度2.837</small></div><div class="arrow">→</div><div class="node"><strong>L1继续处理</strong><small>attention差分2.504<br>层末状态差分4.271</small></div><div class="arrow">→</div><div class="node"><strong>最后选择输出</strong><small>从开始写“第一步”<br>变为直接输出结束标记</small></div></div>
<p class="note">attention和MLP是模型层内的两类计算模块；“残差”在这里指传给后续层的内部状态。上面数字是差分向量的长度，不是损伤百分比。Qwen的attention类记录包含线性注意力与全注意力模块，不能全部当作同一种注意力矩阵。</p>
__PROPAGATION__
<div class="grid2"><div class="reading"><h3>左图：内部差异沿层数怎样变化？</h3><p>横轴是L0—L31，纵轴是两支层末状态的差分长度，除以无针状态的长度。读数0表示相同，0.5表示差分约为参照状态大小的一半，<strong>不是“损伤50%”</strong>。三条线分别是同一点的+0.25、+0.5和+1。</p><p>这里全部取第一个预测位置，横轴表示计算深度，不是生成时间。曲线能显示差异在哪些层扩大或缩小，但最高点不一定就是错误的根因。</p></div><div class="reading"><h3>右图：为什么最后变成空答？</h3><p>横轴是“最强结束标记的得分－最强普通token的得分”。小于0时，继续回答的候选更强；大于0时，结束标记胜出。这是得分差，不是结束概率。</p><p>原版为−17.688，+0.5为−8.25，两者都开始作答；+1变成+3.063，模型于是直接结束。我们解释了空答的最后一步，但还没确定中间哪一项变化让结束标记胜出。</p></div></div>
<div class="strip"><p><strong>一个重要反例：+0.5的终层相对差异已经达到0.720，仍能完成整理步骤；+1才直接结束。</strong>所以不能只凭内部数值“变了很多”就判断答案一定坏了，更不能把差异最大的位置直接叫作功能区。</p></div>
<h3>回答已经分叉后，怎样继续公平地比较内部过程？</h3>
<div class="explain"><p>模型会根据已经写出的内容继续回答。假如原版开始写“第一步”，干预版却写出特殊标记，此后两边读到的文本历史已经不同，直接比内部数值就会混合“干预的影响”和“读到不同文字的影响”。</p><p>我们的处理是：让有针分支正常生成；另一条从头无针的分支，逐步读入<strong>有针分支已经生成的完全相同的文字</strong>，但保留自己独立计算的内部状态，再比较下一步想写什么。这就是“同前缀无针参照”：前缀只是当前已经读到的全部文字。</p></div>
<div class="flow"><div class="node"><strong>有针分支自由回答</strong><small>记录它已经生成的文字</small></div><div class="arrow">→</div><div class="node"><strong>无针参照读同样文字</strong><small>从头无针，内部状态独立计算</small></div><div class="arrow">→</div><div class="node"><strong>比较此刻的选择</strong><small>同样的历史下，两边各想写什么？</small></div></div>
<div class="grid2"><article class="insight"><span class="chip">循环 A · 两边持续想写不同的东西</span><h3>4B L2 N5063 · Q04 · +1</h3><p>有针分支反复写出开启标记&lt;think&gt;。在后续63次再次选择它时，无针参照每次最想写的都是闭合标记<strong>&lt;/think&gt;</strong>。</p><p>也就是说，即便读到同样的循环历史，无针参照仍更想闭合标记，而实际分支继续打开。这个案例显示，循环过程中两边持续存在选词分歧。</p></article><article class="insight"><span class="chip">循环 B · 无针参照也支持继续写下去</span><h3>4B L2 N5251 · Q05 · +1</h3><p>有针分支反复续写英文元指令说明。在128个实际token中，<strong>112个</strong>也是无针参照得分最高或并列最高的候选。</p><p>在相同的偏离历史下，无针参照也常把实际续写选为首选。它提示我们：错误历史可能参与维持循环，不能只盯着当前那一次注入。</p></article></div>
<div class="explain"><p><strong>两种循环的价值在于：</strong>表面都像“卡住了”，下一步的选择却不一样。前者要解释为什么有针分支持续偏离无针参照，后者还要解释为什么错误文本会支持后续重复。它们提供了不同的追查线索，而不是已经确认的两类独立机制。</p><p><strong>这个比较没有真的中途拔针。</strong>无针参照从一开始就没有受到干预，它的内部记忆与实际分支不同。因此不能从上述结果断言“现在拔针就会好”或“拔针也没用”；当前注入和此前内部状态积累的影响，也还没有被单独拆开。</p></div>
<p class="note">技术检查：前六层3,648条干预记录在首个预测位置的首处变化都在注入MLP；32条原版控制的各观测点差分均为0。这验证了记录位置和对照计算，不是发现了MLP的某种专属功能。每模型912条干预中，6个剂量点贡献480条，因此记录数也不等于均匀抽样的通道数。</p></section>

<section><div class="section-head"><div class="num">05</div><div><h2>不同模型有相似现象，但还不能说找到了对应功能区</h2><p class="subhead">四个模型回答同一道整理书桌题 · 以下为选出的代表案例</p></div></div>
<div class="explain"><p><strong>跨模型比较想回答的是：</strong>4B上的异常，是这个模型偶然的表现，还是其他模型也会出现类似过程？下面把同一道题放在一起看。四个案例插针的位置不同，不能把它们当作“同一个神经元”在不同模型中的直接对应。</p><p>每个数字都表示：预测第一个token之前，最后一层内部状态与无针参照相差多少，计算方式与上一节左图相同。更值得比较的是回答怎样变化：是否仍有步骤格式、内容是否跑题、何时停止、重复后无针参照是否也愿意继续。<strong>这些数值不是四个模型的损伤排行榜。</strong></p></div>
<div class="grid2"><div class="insight"><h3>2B · L5 N3522</h3><p>−0.5：<strong>0.379</strong>，连贯步骤 → −1：<strong>0.709</strong>，进入循环。</p><small>从第19次预测（记录中的step 18，从0计数）起，无针参照也支持实际生成的所有重复token，提示已有文字可能参与维持循环。</small></div><div class="insight"><h3>4B · L4 N5428</h3><p>+1：<strong>0.928</strong>，保留步骤格式，内容成为“李达／李斯”。</p><small>第3个token开始与原版不同；仍能写出步骤格式，不代表步骤内容仍与整理书桌有关。</small></div><div class="insight"><h3>9B · L0 N978</h3><p>+0.125：<strong>0.289</strong>，正常 → +0.25：<strong>0.812</strong>，空答 → +1：<strong>1.679</strong>，“托”循环。</p><small>同一个位置随剂量变成不同症状；仅用一个“坏了多少”的分数，会把空答和循环的差别抹掉。</small></div><div class="insight"><h3>Llama · L5 N1726</h3><p>−0.5：<strong>0.244</strong>，连贯 → −1：<strong>0.891</strong>，法律引文后循环。</p><small>+1时前三个token与原版相同，之后才开始不同并较早结束；因此最初几步看似正常，也不代表后面不受影响。</small></div></div>
<div class="strip"><p><strong>共同线索：</strong>不同模型中都能看到“内容先偏离”“格式还在、内容已变”或“重复历史支持继续重复”等现象。但模型结构、分词方式、内部数值尺度和抽中的位置不同，相似症状还不足以说明背后是同一条计算路径。</p></div>
<div class="explain"><h3>三维可视化在这里能帮我们做什么？</h3><p>它可以把插针的位置、各层记录到的变化和原版／干预回答放在同一处。研究者能顺着某个案例看：变化从哪层开始，后面哪些模块变化明显，第一次选词分歧出现在何时；再切换模型或剂量，比较相似过程。它的作用是帮助发现值得追查的联系，并让判断随时能回到原始记录。</p><p>具体布局也要区分：Qwen的写入方向视图用PCA、UMAP等降维方法，把高维权重方向排到各层的二维网格上，再沿层序展开；Llama当前则按编号排布，没有相同规格的权重地图。图上靠得近不等于功能相同，静态连线不等于已经验证的因果路线，不同模型中相同的层号或屏幕位置也不自动对应。<strong>三维图是查看证据的地图，还不是已经画好的“脑区图”。</strong></p></div>
<p class="note">当前数据范围：四模型都有在L0—L5插针的内部记录，4B扩展到全部L0—L31；每条记录均观察该模型的全部层。4B深层数据已经采完，但尚未逐条完成与早层同等细致的机制分析。“采集完成”和“机制解释完成”需要分开。</p></section>

<section id="legacy"><div class="section-head"><div class="num">06</div><div><h2>此前的能力审查：显著损伤，不只是风格变化</h2><p class="subhead">各模型内部配对 · 每版MMLU 1,000 / ARC-C 200 / GSM8K 100 / HumanEval 100题</p></div></div>
<div class="explain"><p><strong>为什么还要做这组能力测试？</strong>一段回答变得尖刻、怪异或带有固定主题，并不能说明我们只改了“性格”。模型也可能已经无法可靠地理解题目、选择答案或完成输出。因此，较早的双针研究还比较了原版和干预版在四类任务上的成绩，检查变化是否伴随广泛能力下降。</p><p>四类任务分别是：MMLU的多学科知识选择题、ARC-C的科学推理选择题、GSM8K的数学应用题，以及HumanEval的代码生成题。这里使用的是固定测试面板，不是四个基准的全部题目。它们与前面的8道探索题承担不同作用：探索题帮助看现象，能力面板帮助判断任务表现受到了多大影响。</p></div>
<div class="reading"><p><strong>怎么看下面四张图：</strong>每张图内部比较同一个模型的原版和干预版。横轴是该任务的百分制成绩，深蓝圆点为原版，赭红方点为干预版；同一行的连接线越长，成绩变化越大。应先逐行比较两点，不要把四张图当成统一条件下的模型排名。</p><p>四张图的干预并不相同：4B使用原双针配方；2B、9B使用按规则映射后的稀疏配方；Llama使用映射后的稠密向量，也就是同时改变多个坐标。它们不是前面全层单针调查的平均成绩。</p></div>
<p class="caption">● 深蓝：原版　■ 赭红：干预。四模型干预形式不同，不能据此比较模型总体优劣。</p><div class="grid2">__BENCHMARK__</div>
<div class="explain"><p><strong>这组结果支持的结论比较明确：</strong>这些冻结的干预配方不只是改变口吻，也伴随多项任务成绩下降。例如4B的MMLU从67.99降到29.74，数学从88降到0。这里报告的是各任务既定评分口径；MMLU是加权成绩，不宜把67.99直接当成答对679.9道题。</p></div>
<div class="grid3"><article class="insight"><h3>零分不等于“所有知识消失”</h3><p>数学和代码的零分中，混有答案被截断、无法提取最终答案、代码语法错误或测试未通过等情况。选择题评分不依赖模型是否能生成一个可解析的答案字母，所以其下降不能完全归结为输出格式。不同失败原因仍需分开看。</p></article><article class="insight"><h3>映射成功不等于找到同一功能区</h3><p>我们用既定规则把4B中的干预方向映射到目标模型，没有直接照搬通道编号。9B的两列稀疏投影只保留目标向量<strong>8.68% / 5.20%</strong>的平方长度，2B为<strong>1.42% / 1.66%</strong>。这表示稀疏近似只保留了少量向量成分，不是“机制保留了多少”的百分比；实际配方还做了强度标定，这也不是最终施加剂量的比例。</p></article><article class="insight"><h3>随机对照削弱了“特定功能”的解释</h3><p>在小诊断中，2B的一组随机配方（random3）比真实配方还差；Llama的随机2配方与真实稠密配方成绩相同。既然随机方向也能造成严重损伤，“迁移后也坏了”就不能单独证明迁移了原来的特定行为或同一机制。</p></article></div>
<p>因此，现阶段可以确认这些条件下的能力下降，但还不能确认特定目标行为已成功迁移。原迁移协议中的结构化有害行为评价尚未完成，不能用答题成绩下降替代这项结论。</p>
<details><summary>更早的24题与三项快速基准</summary><p>24题原版/双针、512/1024上限尝试共96份；短长是前缀关系，Q25—Q40未运行。旧EOS配置有结束后续写问题，不能用23/24截断称主回答未结束。</p><div class="table-scroll"><table><thead><tr><th>任务，各100题</th><th>严格格式</th><th>事后统一提取</th><th>首token四选一诊断</th></tr></thead><tbody><tr><td>RACE</td><td>89% → 0%</td><td>89% → 11%</td><td>89% → 30%</td></tr><tr><td>GSM8K</td><td>79% → 0%</td><td>83% → 0%</td><td>不适用</td></tr><tr><td>LogiQA</td><td>70% → 0%</td><td>70% → 15%</td><td>70% → 23%</td></tr></tbody></table></div><p>三种评价口径分开报告；首token诊断不是官方完整选项似然或自由回答正确率。干预300份有295份达到各自生成上限。</p></details>
</section>

<section><div class="section-head"><div class="num">07</div><div><h2>改回一处内部输出能改善成绩，但还不能认定它就是根因</h2><p class="subhead">较早的双针实验 · MMLU与ARC各32题 · 检查10个候选组件</p></div></div>
<div class="explain"><p><strong>这项实验比“看到变化”又多走了一步：</strong>模型内部某处变化很大，可能只是受影响，并不一定负责造成错误。我们于是保留双针干预，只把候选位置的一项模块输出换成原版的值，看成绩是否改善；再反过来，把受干预时的这项输出放进原版，看能否重新造成损伤。</p><p>此外还做了匹配随机对照：在同一个位置改动同样大小，但换成随机方向。这样才能区分“这项具体变化有作用”，还是“在那里随便改一下也会产生类似效果”。下面展示候选C01，即第23层attention模块在提示最后位置的输出。</p></div>
<div class="reading"><p><strong>怎么看柱状图：</strong>纵轴是32道MMLU题中答对几道。五根柱从左到右分别是：原版、双针后、保留双针并修复C01、同位置同幅度随机修复、把受损的C01输出放进原版。虚线标出原版的18/32，便于判断改变后比原版更好还是更差。</p></div>
__REPAIR__
<div class="evidence"><article><span class="chip">已经看到的改善</span><h3>C01和C05都值得继续解释</h3><p>C01让MMLU从15/32提高到24/32，同幅度随机修复仍是15/32。C05也从15/32提高到19/32。至少在这批题上，局部改动确实能改善受干预后的结果。</p><p>但C01甚至超过了原版的18/32。这可能包含补偿或额外改善，不能全部叫作“恢复原本能力”。</p></article><article class="pending"><span class="chip pending">反向证据还不够</span><h3>放入受损输出，没有重现正确率下降</h3><p>C01和C05的反向操作都是18/32，与原版相同。全部10个候选中，<strong>0个</strong>在任一任务的正确率上，同时满足预定的四项比较。</p><p>所以“改这里能救回来一些”已经有证据，“原来的损伤就是经由这里造成的”仍然没有充分证据。</p></article></div>
<div class="explain"><p><strong>“四项比较”用白话说就是：</strong>修复后要比受损时好，也要比同幅度随机修复好；反过来放入受损输出要能让原版变差，而且要比随机改动造成的下降更明确。只通过前半段，仍可能是在绕路补偿，尚不能认定找到了原来的致错环节。</p><p><strong>为什么还保留C05这条线索？</strong>除了答对几题，我们也看正确选项与最强错误选项的得分差，称为margin。它能显示模型是否更偏向正确答案，即便最高分选项还没有改变。C05在两类任务的这种得分差上都有双向信号，但得分偏好改善不等于正确率的双向因果检验已经通过。</p><p>这些候选是在同一批开发题上筛选和评估的，多项统计比较也没有统一控制误报；因此目前属于开发阶段线索，缺少独立题目的确认。它们来自旧双针实验，也不能直接当作后来单针循环或空答的机制证明。</p></div></section>

<section id="direction"><div class="section-head"><div class="num">08</div><div><h2>我们的方向：从“哪里一碰就变”走向“为什么会这样变”</h2><p class="subhead">寻找模型内部的具体计算分工，以及不同模型是否使用相似的过程</p></div></div>
<div class="explain"><p>我们想研究的不是简单给某层贴上“数学区”或“语言区”的名字。一道数学题同时需要读取条件、进行计算、选择结论、组织文字并在适当位置停止；同一种能力可能涉及多个环节，同一环节也可能服务多种能力。更有意义的问题是：<strong>哪些内部变化会选择性地影响其中某个环节，又是怎样影响后续回答的？</strong></p><p>“功能分区”因此是需要验证的研究问题，不是这份图已经证明的前提。目前的材料让我们能把可疑位置、剂量、原文和内部过程一一对上；要进一步命名功能，还必须能解释为什么影响的是这个计算环节，而不只是让模型普遍变差。</p></div>
<div class="flow"><div class="node"><span class="chip">已经测到</span><strong>改哪里，会怎样回答</strong><small>模型、层、通道、剂量<br>均可对应回原始记录</small></div><div class="arrow">→</div><div class="node"><span class="chip">已经看到一些过程</span><strong>内部怎样变化、下一步选什么</strong><small>逐层差异、停止竞争<br>循环中对历史的续写偏好</small></div><div class="arrow">→</div><div class="node"><span class="chip pending">还需要解释</span><strong>哪一环节真正造成了结果</strong><small>能否排除补偿和一般损伤<br>能否在其他模型找到对应作用</small></div></div>
<div class="grid3"><article><h3>线索一：同一点不只有一种表现</h3><p>输入、剂量和符号改变后，同一点可能正常、跑题、空答或循环。这提示我们要解释具体条件下的作用，而不是看到一次空答就命名为“停止通道”。</p></article><article><h3>线索二：同一种表象可能有不同过程</h3><p>两个案例都在重复，但一个持续偏离无针参照的选择，另一个的重复续写也得到无针参照支持。只读最终文本会错过这一区别，内部记录提供了更细的解释线索。</p></article><article><h3>线索三：跨模型应比较作用过程</h3><p>不同模型都有内容偏离与循环，但空答模式并不相同。值得比较的是相似计算环节是否受到影响；通道编号相同、三维位置接近或都会循环，都还不是功能对应的证据。</p></article></div>
<p class="endline">已经得到：能追到具体位置、剂量和回答的实验地图。<br>仍待解释：哪些内部环节造成了这些变化，哪些作用能跨模型对应。</p></section>

<section id="evidence"><div class="section-head"><div class="num">09</div><div><h2>完整数据与核对说明</h2><p class="subhead">正文保留主要证据；完整表格和修订后的MD随本HTML一起内嵌，可离线查看与导出</p></div></div>
<div class="explain"><p>前面的图展示主要现象，下面的表格保留完整计数、对照条件、未通过的比较和明确没有运行的部分。点击表题即可展开；需要完整实验记录和更多原始回答时，可以用页末按钮导出随本文件附带的总结MD，无需访问服务器。</p><p><strong>数据完整，不等于假说成立。</strong>下面的“0缺失”“0重复”表示约定采集的轨迹已经核对齐全；它们验证的是实验执行与归档，不是功能区或因果机制已经被证实。停止的旧批次、技术预检和正式结果也分别记账，没有混进同一个样本数。</p></div>
<div class="micro"><span><b>0</b> 缺失轨迹</span><span><b>0</b> 重复正式轨迹</span><span><b>15,496</b> 归档文件</span><span><b>13.886</b> hook worker小时</span></div>
<p class="note">13.886 worker小时是内部轨迹采集进程耗时的合计，包含GPU预检、加载、生成、存储和检查；多个进程可并行，因此它不是实际等了13.886小时，也不是费用。56个预检观察案例不计入7,632份正式轨迹，但其耗时已包含在上述13.886小时中；旧Llama停止批次479份保留，但不进入正式分母。</p>
__APPENDIX__
<details><summary>统计与证据解释边界</summary><p>8道固定探索题，不是完整能力测试；没有独立人类盲评。原版也可能有错误。采集来源、同前缀重放与技术恢复控制不增加独立科学样本。低剂量无机械故障不等于无语义损伤。统计是固定条件的描述，不提供通道总体或功能区显著性推断。</p><p>修复表四符号依次为：修复−AB、修复−匹配修复、原版−反向重现、匹配反向−反向重现。✓表示既有95%配对bootstrap区间下界大于0；带星号的MMLU答案尾部没有可操作位置。Llama迁移门槛的区间为98.75%，不能混作95%。</p></details>
<div class="strip"><strong>本次核对：</strong>来源去重、120层机械统计、40个模型—剂量组合、120个剂量通道、关键轨迹与历史结果。修正4B L1通道转写：N667为6/8首步EOS；全层总数不变。</div>
<button class="download" id="download-md">下载完整核对版 MD</button>
</section><footer>Acupuncture · 2026年10月28日 · 仅使用既有实验产物。数据图不进行未测档位插值，不构造功能区边界。<br>本页依据MD的SHA-256：__MD_HASH__。所有图形、数据和MD均包含在此文件中，无网络依赖。</footer>
</main><script id="report-data" type="application/json">__DATA__</script><script>
const data=JSON.parse(document.getElementById('report-data').textContent);
const ex=document.getElementById('example'),doseSelect=document.getElementById('dose-choice');
const caseGuides=[
'这个案例要看“步骤格式”和“步骤内容”是否一起保留。4B L6 N7840在+0.25仍围绕整理书桌；+0.5还像两行步骤，却混入基因符号相关内容；+1则没有正文。如果只看最高剂量的空答，就会漏掉较弱剂量下的内容变化。',
'这个案例要看同一主题怎样随着剂量进入回答。Llama L4 N9472在+0.25仍给整理步骤；+0.5把书桌写成与裂缝、深渊有关的情景；+1出现英文深渊相关循环。−1却仍能给出清理步骤。这是内容倾向和任务损伤一起变化的例子，不能据此把该点命名为“深渊神经元”。',
'这道题没有提供天气信息，关键是模型是否承认无法判断。4B L7 N6650在−1说需要带伞，+1说不需要带伞。两边结论虽然相反，但都不能从题目推出，所以这里不是正确判断能力被双向控制。比较时也要读原版，不能默认原版一定完全正确。',
'这个案例展示“更强不一定更差”：Llama L17 N7938在+0.25进入循环，+0.5和+1却重新给出通顺建议。这里只能确认这几个实际测过的档位出现了非单调变化，不能据此保证两个档位之间都通顺，也不能把通顺自动当作内容正确。'
];
data.examples.forEach((v,i)=>{const o=document.createElement('option');o.value=i;o.textContent=v.title;ex.append(o)});
[-1,-.5,-.25,-.125,-.0625,.0625,.125,.25,.5,1].forEach(v=>{const o=document.createElement('option');o.value=v;o.textContent=(v>0?'+':'')+v;doseSelect.append(o)});doseSelect.value=.5;
function show(){const i=Number(ex.value),g=data.examples[i],a=Object.entries(g.answers).find(([d])=>Number(d)===Number(doseSelect.value))[1];document.getElementById('prompt').textContent='原题：'+g.prompt;document.getElementById('baseline').textContent=g.baseline;document.getElementById('modified').textContent=a.text||'（无正文：第一个输出就是结束标记）';document.getElementById('answer-meta').textContent='本次输出 '+a.tokens+' token · '+(a.end==='eos_token'?'遇到结束标记停止':'达到128-token生成上限');document.getElementById('case-explanation').textContent=caseGuides[i]}
ex.addEventListener('change',show);doseSelect.addEventListener('change',show);show();
document.getElementById('download-md').addEventListener('click',()=>{const url=URL.createObjectURL(new Blob([data.markdown],{type:'text/markdown;charset=utf-8'}));const a=document.createElement('a');a.href=url;a.download='Acupuncture_实验总结_导师版_2026-10-28.md';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)});
</script></body></html>'''
for key,value in {'HEAT_EOS':heat_eos,'HEAT_REP':heat_rep,'DOSE_FIGS':dose_figs,'PROPAGATION':prop,
    'BENCHMARK':bench,'REPAIR':rep,'APPENDIX':appendix,'MD_HASH':md_hash,'DATA':payload}.items():
    page=page.replace('__'+key+'__',value)
assert not re.search(r'__[A-Z_]+__',page)
assert '<script src=' not in page and '<link ' not in page
OUT.write_text(page)
print(json.dumps({'html':str(OUT),'bytes':OUT.stat().st_size,'plots':svg_index,'md_sha256':md_hash},ensure_ascii=False))
