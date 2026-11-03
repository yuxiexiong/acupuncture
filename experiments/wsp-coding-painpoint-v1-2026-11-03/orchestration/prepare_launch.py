"""Generate disabled, hash-bound server launch templates after engineering acceptance."""
import json
from pathlib import Path
from ledger import file_hash,write

ROOT=Path('/workspace/acupuncture/external/wcp01')
HERE=Path(__file__).resolve().parent


def main():
    base=json.loads((HERE/'budget-base.json').read_text())
    acceptance=ROOT/'orchestration-r1/acceptance.json'
    accepted=json.loads(acceptance.read_text())
    if accepted['status']!='passed':raise ValueError('ENGINEERING_NOT_PASSED')
    live=json.loads((ROOT/'orchestration-r1/live-mac-r1/receipt.json').read_text())
    source={str(p):file_hash(p) for folder in (HERE,HERE.parent) for p in folder.glob('*.py')}
    engine=Path('/workspace/acupuncture/external/wsp/code-engineering-r2/engineering-r2')
    for name in ('controller.py','forward_service.py'):source[str(engine/name)]=file_hash(engine/name)
    source[str(engine.parent/'snapshot_edits.py')]=file_hash(engine.parent/'snapshot_edits.py')
    for profile in ('0p8b','4b'):
        b=base['model_profiles'][profile];old=json.loads((ROOT/('acceptance-0p8b-r2' if profile=='0p8b' else 'acceptance-4b-r1')/'receipt.json').read_text())
        usage=live['editor_usage'][profile]
        spent=dict(gpu_seconds=b['engineering_gpu_seconds_spent'],gpu_A=b['engineering_gpu_seconds_spent'],gpu_B=0,gpu_C=0,
                   samples=32,output_tokens=sum(x['tokens'] for x in old['generation']),tf_tokens=458 if profile=='0p8b' else 266,
                   cpu_seconds=7200,**usage)
        cfg=dict(mode='research',backend='real',profile=profile,authorized=False,authorization_record=None,editor_transport='mac_ssh',
                 run_root=str(ROOT/'runs'/(profile+'-r1')),data_root=str(ROOT/'data-v1'),
                 data_manifest_sha256=file_hash(ROOT/'data-v1/manifest.json'),acceptance_path=str(acceptance),acceptance_sha256=file_hash(acceptance),
                 source_hashes=source,model_revision=b['revision'],spent=spent,
                 caps=dict(gpu_seconds=b['gpu_hours_cap']*3600,**{'gpu_'+k:v*3600 for k,v in b['stage_gpu_hours'].items()},
                           samples=3008,output_tokens=52957184,tf_tokens=2000000,cpu_seconds=216000,
                           editor_turns=100,editor_input_tokens=1500000,editor_output_tokens=150000),
                 reserve_free_bytes=50000000000,new_data_bytes_cap=b['new_data_bytes_cap'],
                 historical_cpu_reserve=dict(seconds=7200,kind='conservative_budget_allocation_not_measured_usage'),
                 editor_token_limit_kind='post_turn_usage_guard_not_provider_hard_cap')
        write(HERE/('search-'+profile+'.json'),cfg)
        write(ROOT/'orchestration-r1'/('remaining-'+profile+'.json'),dict(profile=profile,authorized=False,remaining={k:v-spent.get(k,0) for k,v in cfg['caps'].items()},historical_cpu_reserve=cfg['historical_cpu_reserve']))


if __name__=='__main__':main()
