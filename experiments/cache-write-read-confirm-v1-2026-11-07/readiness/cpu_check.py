"""Frozen dependencies and old calibration/vector assets; CPU only, no new fitting."""
import os
import sys
from pathlib import Path
HERE=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(HERE))
import dwc_run as R

def main(target):
    assert os.environ.get('CUDA_VISIBLE_DEVICES')==''
    R.OLD.check_freeze(R.DWR_DIR/'freeze-r02.json')
    R.DW.check_freeze(R.DWB_DIR/'freeze-r02.json')
    R.SP.check_freeze(R.SPF_DIR/'freeze-A-r02.json')
    R.SP.FB.S.check_freeze(R.SP.FB.N.SRU_DIR/'freeze-r01.json')
    R.SP.FB.N.check_freeze(R.NWR_DIR/'freeze-r01.json')
    R.SP.FB.check_freeze(R.SP.FBR_DIR/'freeze-A-r03.json')
    old=R.old_dwr_records();lvk=R.lvk_records();vectors=R.load_vectors()
    assert len(old)==len(lvk)==48
    _,off,_=R.ARMS_ALL['Rk'];cals={}
    for family in R.M.FAMILIES:
        _,cals[family]=R.QCR.nq_calibration(family+'-ABC-A')
        for direction in R.DIRS:assert family+'|'+direction in vectors[off]
    ledger=R.exp.read(HERE/'data/token-ledger-r01.json')
    assert ledger['status']=='passed' and not ledger['failures']
    assert ledger['materials_sha256']==R.exp.sha(HERE/'data/materials-r01.json')
    ki=R.kernel_identity();assert not(ki['fla'] or ki['kernels'] or ki['causal_conv1d'])
    R.M.write(target,dict(status='passed',model_calls=0,kernel_identity=ki,calibration_sources=cals,
                         old_DWR_receivers=len(old),formal_limits=R.limits('formal')[0],preflight_limits=R.limits('preflight')[0]))
if __name__=='__main__':main(sys.argv[1])
