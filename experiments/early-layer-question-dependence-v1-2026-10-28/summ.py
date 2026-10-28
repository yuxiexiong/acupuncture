import json, collections
import os; S=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','layer-trace-extension-v1-2026-10-28/analysis-early-r01/summary.json')
s=json.load(open(S))
print("### F. summary groups: per model × injection layer（cohort ten_point_positive1，+1，n=80）")
cohorts=collections.Counter(g['cohort'] for g in s['groups']); print('cohorts',cohorts)
for g in s['groups']:
    if g['cohort']=='ten_point_positive1' and g['layer'] is not None and g['dose'] is None:
        m=g['medians']
        print(f"{g['model']:>18} L{g['layer']} n={g['n']:3d} emptyAns={g['empty_answer_count']:3d} firstEOScleanNonEOS={g['first_eos_with_clean_non_eos_count']:3d} | injRelRes {m['injection_residual_relative']:.2f} finalRel {m['final_residual_relative']:.2f} finalCos {m['final_residual_cosine']:.2f} | firstKL {str(m["first_kl"])[:6]} steerStopAdv {str(m["first_steer_stop_advantage"])[:6]} cleanStopAdv {str(m["first_clean_stop_advantage"])[:6]} | strictDivFrac {m['strict_divergent_fraction']:.2f} rep4cleanSupp {str(m["repeated4_clean_supported_fraction"])[:5]}")
print()
print("### G. first_step_profiles: 注入层→下游各层 attention 站点的中位 relative_delta（只列全注意力层 3,7,11,15 和末层）")
for p in s['first_step_profiles']:
    sites={ (x['layer'],x['component']):x for x in p['sites']}
    L=max(l for l,_ in sites)
    def rd(l,c): 
        x=sites.get((l,c)); return None if x is None else x['relative_delta']
    def cn(l,c):
        x=sites.get((l,c)); return None if x is None else x['clean_norm']
    inj=p['injection_layer']
    fa=[l for l in (3,7,11,15,19,23) if l<=L and l>inj]
    print(f"{p['model']:>18} inj L{inj} n={p['n']} | clean norms @inj: attn {cn(inj,'attention'):.2f} mlp {cn(inj,'mlp'):.2f} res {cn(inj,'residual'):.2f} | res relΔ@inj {rd(inj,'residual'):.2f} | attn relΔ@ " + ' '.join(f"L{l}:{rd(l,'attention'):.2f}" for l in fa) + f" | res relΔ@L{L} {rd(L,'residual'):.2f} cos {sites[(L,'residual')]['cosine']:.2f}")
print()
print("### clean residual norm profile at last prompt position (from baseline-like inj L0 profile), per model")
for p in s['first_step_profiles']:
    if p['injection_layer']!=0: continue
    sites={ (x['layer'],x['component']):x for x in p['sites']}
    L=max(l for l,_ in sites)
    print(p['model'], 'res clean:', [round(sites[(l,'residual')]['clean_norm'],1) for l in range(L+1)])
    print(p['model'], 'mlp clean:', [round(sites[(l,'mlp')]['clean_norm'],2) for l in range(0,8)], 'attn clean:', [round(sites[(l,'attention')]['clean_norm'],2) for l in range(0,8)])
