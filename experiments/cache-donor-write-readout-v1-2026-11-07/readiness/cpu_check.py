"""Verify frozen dependencies, model identity metadata and prior evidence without loading weights."""
import os
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
import dwr_run as R
assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''


def main(target):
    import torch
    R.DW.check_freeze(R.DWB_DIR/'freeze-r02.json')
    R.SP.check_freeze(R.SPF_DIR/'freeze-A-r02.json')
    R.SP.FB.S.check_freeze(R.SP.FB.N.SRU_DIR/'freeze-r01.json')
    R.SP.FB.N.check_freeze(R.NWR_DIR/'freeze-r01.json')
    R.SP.FB.check_freeze(R.SP.FBR_DIR/'freeze-A-r03.json')
    prior, lvk = R.prior_records(), R.lvk_records()
    items, order = R.panel()
    counts = dict(C0=0,L00=0,L11o=0,L11d=0)
    for r in items:
        ds = R.donors_of(r,items,order)
        assert ds == prior[r]['donors']
        lt = torch.load(lvk[r]['_tensor_path'],map_location='cpu')
        assert lt['t1|C|all'].dtype == torch.bfloat16
        counts['C0'] += 1
        for d in R.DIRS:
            arms = prior[r]['directions'][d]
            counts['L00'] += 1
            o = arms['L11o']
            assert o['N']['reached_t2'] and o['N']['t2_sha']
            counts['L11o'] += 1
            for donor in ds:
                f = arms['L11d|'+donor['id']]
                assert f['x'] == o['x'] and f['N']['reached_t2'] and f['N']['t2_sha']
                counts['L11d'] += 1
    assert counts == dict(C0=48,L00=96,L11o=96,L11d=696)
    vecs=R.load_vectors()
    _,off,_=R.ARMS_ALL['Rk']
    for s in order:
        R.QCR.nq_calibration(s+'-ABC-A')
        for d in R.DIRS:
            assert s+'|'+d in vecs[off]
    ki=R.kernel_identity()
    assert not (ki['fla'] or ki['kernels'] or ki['causal_conv1d'])
    R.exp.write(target, {'passed':True,'prior_bridges':counts,'kernel_identity':ki,
                         'formal_limits':R.limits('formal')[0],'preflight_limits':R.limits('preflight')[0]}, immutable=True)


if __name__ == '__main__':
    main(sys.argv[1])
