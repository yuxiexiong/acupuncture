"""Read existing full evaluations; export percentages and curves without model calls.

Reuses the v8x50 plot's candidate-versus-eligible-incumbent presentation.
"""
import csv
import json
import os
from common import packed, digest, write_json


def export(service, model):
    root = service.root
    ids = list(service.evidence.records)
    def metrics(candidate):
        key = digest(packed(dict(candidate=candidate, ids=ids, protocol=service.protocol)))
        summary = service.cached(key)['summary']
        return dict(accuracy_pct=100*summary['accuracy'],
                    repair_score_pct=100*summary['repair_score'])
    base = service.candidates.base_id
    incumbent = base
    baseline = metrics(base)
    rows = [dict(round=0, candidate=base, selected=True, selection_reason='original W0',
                 **baseline, incumbent_candidate=base,
                 incumbent_accuracy_pct=baseline['accuracy_pct'],
                 incumbent_repair_score_pct=baseline['repair_score_pct'])]
    for path in sorted((root/'artifacts').glob('repair-round-*.json')):
        r = json.loads(path.read_text())
        assert r['round'] == len(rows)
        selected = 'best' in r['selection']
        if selected: incumbent = r['selection']['best']
        current = metrics(incumbent)
        rows.append(dict(round=r['round'], candidate=r['candidate'], selected=selected,
            selection_reason=r['selection'].get('not_selected','accepted'),
            **metrics(r['candidate']), incumbent_candidate=incumbent,
            incumbent_accuracy_pct=current['accuracy_pct'],
            incumbent_repair_score_pct=current['repair_score_pct']))
    out = root/'reports'; out.mkdir(exist_ok=True)
    write_json(out/'trajectory.json', dict(model=model, development_only=True,
        target_rounds=50, completed_rounds=len(rows)-1, rows=rows))
    with (out/'trajectory.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    frozen=service.state.get('frozen')
    write_json(out/'result.json', dict(model=model, completed_rounds=len(rows)-1,
        target_rounds=50, baseline=baseline, latest_candidate=metrics(rows[-1]['candidate']),
        selected_candidate=service.state['best'], selected=metrics(service.state['best']),
        frozen_candidate=frozen, final=metrics(frozen) if frozen else None,
        development_only=True, independent_confirmation=False))
    draw(rows, model, out)
    return dict(rounds=len(rows)-1, output=str(out))


def draw(rows, model, out):
    os.environ.setdefault('MPLCONFIGDIR','/tmp/wsp-matplotlib')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.ticker import PercentFormatter
    fig,axes=plt.subplots(1,2,figsize=(13,4.8),layout='constrained')
    x=[r['round'] for r in rows]
    for ax,key,title in zip(axes,('accuracy_pct','repair_score_pct'),
            ('Overall answer accuracy (2,560 requests)','C joint repair score (64 source groups)')):
        y=[r[key] for r in rows];best=[r['incumbent_'+key] for r in rows]
        ax.plot(x,y,color='#91a9bf',marker='o',ms=3,lw=1.3,label='Each evaluated candidate')
        ax.step(x,best,where='post',color='#136bb0',lw=2,label='Selected by frozen C rule')
        ax.axhline(y[0],color='#888888',ls='--',lw=1,label=f'W0: {y[0]:.2f}%')
        ax.scatter([x[-1]],[best[-1]],color='#136bb0',s=40,zorder=4)
        ax.annotate(f'{best[-1]:.2f}%',(x[-1],best[-1]),xytext=(0,10),
                    textcoords='offset points',ha='center',color='#136bb0')
        if x[-1]<50: ax.axvspan(x[-1]+.3,50,color='#f0f2f5',zorder=0)
        ax.set(xlim=(-1,51),ylim=(0,100),xlabel='Completed repair round (0 = W0)',title=title)
        ax.yaxis.set_major_formatter(PercentFormatter(100));ax.grid(axis='y',alpha=.2)
        ax.legend(loc='lower left',fontsize=8)
    fig.suptitle(f'{model} | {x[-1]}/50 rounds | Development set')
    for suffix in ('png','svg'): fig.savefig(out/('progress.'+suffix),dpi=160)
    plt.close(fig)
