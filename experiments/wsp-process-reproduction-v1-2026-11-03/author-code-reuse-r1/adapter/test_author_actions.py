"""CPU-only successful-path checks against pinned original source; no broker/model."""
import ast
import json
from pathlib import Path
import sys
import tempfile
import author_actions as A


def main(root):
    source=root/'upstream';actions=root/'actions'
    entries=A.audit(source,actions)
    assert sum(e['execution']=='skip_historical_failure' for e in entries)==24
    assert sum(e['kind']=='forward' and e['execution']=='execute' for e in entries)==50
    assert sum(e['kind']=='python' and e['execution']=='execute' for e in entries)==75
    original=(actions/'147-python.py').read_text()
    effective=A.executable_code(147,original)
    # Exact statement-level difference is only the two historical count assertions.
    tree=ast.parse(original)
    tree.body=[n for n in tree.body if ast.get_source_segment(original,n) not in A.HISTORICAL_COUNTS]
    assert ast.dump(tree)==ast.dump(ast.parse(effective))
    for e in entries:
        if e['kind']=='python' and e['line']!=147:
            assert e['sha256']==e['executed_code_sha256']
    class Transport:
        cfg={'author_replay_authorized':True,'authorization_record':'mock only'}
        calls=[]
        def dispatch(self,request):
            self.calls.append(request)
            return {'failed':False}
    with tempfile.TemporaryDirectory() as temp:
        b=Transport();b.root=Path(temp)
        for line in (7,15,19,24,29,37):
            first=A.dispatch(b,source,actions,line)
            assert A.dispatch(b,source,actions,line)==first
        assert b.calls==[]
        A.dispatch(b,source,actions,6)
        assert b.calls[-1]['source_pass']==2
        assert b.calls[-1]['request']==json.loads((actions/'006-forward.json').read_text())
        A.dispatch(b,source,actions,147)
        assert b.calls[-1]['code']==effective
        A.dispatch(b,source,actions,149)
        assert b.calls[-1]['kind']=='finalize' and 'edit_hash' not in b.calls[-1]
        b.cfg={}
        try:A.dispatch(b,source,actions,6)
        except AssertionError:pass
        else:raise AssertionError('Formal gate bypassed')
    receipt={'status':'passed','forward_actions':50,'python_actions':75,'historical_skips':24,
             'only_source_execution_difference':'two historical count assertions in action 147',
             'scientific_assertions_retained':True,'failed_actions_make_no_calls':True,
             'source_pass_preserved':True,'actual_snapshot_not_author_hash':True,'formal_gate':True,
             'model_calls':0,'test_transport':'mock'}
    print(json.dumps(receipt,indent=2))


if __name__=='__main__':main(Path(sys.argv[1]))
