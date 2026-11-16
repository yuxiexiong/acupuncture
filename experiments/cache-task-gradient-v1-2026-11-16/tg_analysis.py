"""Frozen no-fit calibration; cross diagnostics are not finite intervention estimates."""
import math
import statistics


def receiver_mean(rows, field):
    groups = {}
    for r in rows: groups.setdefault(r['receiver'],[]).append(r[field])
    return statistics.mean(statistics.mean(v) for v in groups.values()) if groups else None


def summary(rows):
    rows = [dict(r, error=r['prediction']-r['observed'],
                 absolute_error=abs(r['prediction']-r['observed']),
                 zero_error=abs(r['observed']),
                 sign_match=float(r['prediction']*r['observed']>0)) for r in rows]
    groups = {r:[x for x in rows if x['receiver']==r] for r in sorted({x['receiver'] for x in rows})}
    mae = receiver_mean(rows,'absolute_error'); zero=receiver_mean(rows,'zero_error')
    bias=receiver_mean(rows,'error')
    qualified=[r for r in rows if abs(r['observed'])>=.25]
    sign=receiver_mean(qualified,'sign_match')
    coverage=statistics.mean(receiver_mean(v,'absolute_error')<=.5 for v in groups.values())
    gates={'mae_le_025':mae<=.25, 'half_zero_mae':zero>0 and mae<=.5*zero,
           'bias_le_010':abs(bias)<=.10, 'receivers_80pct_le_050':coverage>=.8,
           'sign_80pct':sign is not None and sign>=.8}
    errors=sorted(x['absolute_error'] for x in rows)
    quantiles={str(q):errors[round(q*(len(errors)-1))] for q in (0,.25,.5,.75,.9,.95,1)}
    return dict(passed=all(gates.values()), gates=gates, mae=mae, zero_mae=zero,
                relative_mae=mae/zero if zero else None, bias=bias,
                predicted_mean=receiver_mean(rows,'prediction'), observed_mean=receiver_mean(rows,'observed'),
                receiver_coverage=coverage, sign_agreement=sign,
                sign_pairs=len(qualified), sign_receivers=len({r['receiver'] for r in qualified}),
                sign_scenarios={s:dict(pairs=sum(r['scenario']==s for r in qualified),
                    receivers=len({r['receiver'] for r in qualified if r['scenario']==s})) for s in sorted({r['scenario'] for r in rows})},
                pair_absolute_error_quantiles_unweighted=quantiles,
                receiver_rows=[dict(receiver=r, mae=receiver_mean(v,'absolute_error'),
                    bias=receiver_mean(v,'error'), observed=receiver_mean(v,'observed'), prediction=receiver_mean(v,'prediction')) for r,v in groups.items()], rows=rows)


def projection(gradients, physical):
    import torch
    q={b:{l:(1 if b=='C' else -1)*v.double() for l,v in physical[b].items()} for b in ('C','H')}
    unit={b:{} for b in q}; zeros=[]
    for l in q['C']:
        nc,nh=[q[b][l].norm().item() for b in ('C','H')]
        scale=math.sqrt(nc*nh)
        if not nc or not nh: zeros.append(l)
        for b,n in [('C',nc),('H',nh)]:
            unit[b][l]=scale*q[b][l]/n if nc and nh else torch.zeros_like(q[b][l])
    terms={kind:{b:{d:{str(l):float((gradients[b][l].double()*vec[d][l]).sum())
                            for l in q['C']} for d in q} for b in q} for kind,vec in [('raw',q),('equal_amplitude',unit)]}
    totals={kind:{b:{d:sum(t.values()) for d,t in v.items()} for b,v in bs.items()} for kind,bs in terms.items()}
    return dict(totals=totals, terms=terms, zero_direction_layers=zeros)


def analyse(records):
    summaries={}; raw=[]
    for b in ('C','H'):
        rows=[dict(receiver=r['receiver'],donor=r['donor'],scenario=r['scenario'],
                   observed=r[b]['observed'],prediction=r['projection']['totals']['raw'][b][b]) for r in records]
        summaries[b]=summary(rows)
        summaries[b]['scenarios']={s:summary([r for r in rows if r['scenario']==s]) for s in sorted({r['scenario'] for r in rows})}
    passed=all(x['passed'] for x in summaries.values())
    for r in records:
        v={k:r[k] for k in ('receiver','donor','scenario')}
        for kind,bs in r['projection']['totals'].items():
            for b,ds in bs.items():
                for d,n in ds.items(): v[f'{kind}_{b}_{d}']=n
        raw.append(v)
    fields=[k for k in raw[0] if k not in ('receiver','donor','scenario')]
    return dict(kind='seen-panel no-fit calibration; no causal share', calibration=summaries,
                joint_pass=passed, cross_interpretation_allowed=passed,
                cross_means_descriptive={k:receiver_mean(raw,k) for k in fields},
                cross_scenarios={s:{k:receiver_mean([r for r in raw if r['scenario']==s],k) for k in fields} for s in sorted({r['scenario'] for r in raw})},
                cross_rows=raw, zero_direction_pair_layers=sum(len(r['projection']['zero_direction_layers']) for r in records))
