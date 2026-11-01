"""Algebraic counterexamples to two proposed extrapolations; no model experiment."""
import json
from math import comb
# Globally additive at all-clean/all-T history corners, but entry-by-F at fixed S=K=T need not be additive.
def y(x,s,f,k,lam):return x+s+f+k+lam*x*s*(1-f)
examples=[]
for lam in (0,1,2):
 c=y(0,0,0,0,lam);t=y(1,1,1,1,lam);a=y(0,1,1,1,lam);d=y(1,0,0,0,lam)
 gt=y(0,1,1,1,lam)-y(0,1,0,1,lam);gn=y(1,1,1,1,lam)-y(1,1,0,1,lam)
 assert t-a-d+c==0
 examples.append(dict(lam=lam,whole_history_interaction=0,G_T=gt,G_N=gn,ratio=gn/gt))
# Fixed F endpoints do not determine F_V mixed cells or addition/removal asymmetry.
asym=[]
for z01,z10 in ((2,1),(9,8)):
 z00,z11=0,10;av=z01-z00;rv=z11-z10
 asym.append(dict(Z00=z00,Z11=z11,Z01=z01,Z10=z10,A_V=av,R_V=rv))
assert asym[0]['A_V']<asym[0]['R_V'] and asym[1]['A_V']>asym[1]['R_V']
p=sum(comb(6,k)*(1/3)**k*(2/3)**(6-k) for k in (5,6));assert abs(p-13/729)<1e-15
print(json.dumps({'kind':'mathematical_counterexamples_not_model_results','global_additivity_not_conditional_F_additivity':examples,'F_endpoints_do_not_identify_V_asymmetry':asym,'hypothetical_probability':p,'probability_assumptions':['independent scenarios','three exchangeable continuous effect magnitudes per scenario','one preselected comparison'],'actual_experiment_meets_assumptions':False,'model_calls':0,'gpu_calls':0},indent=2))
