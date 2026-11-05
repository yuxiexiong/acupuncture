"""Observer-only server configuration and symlink-free model view; no model load."""
import json
import sys
from pathlib import Path
from common import HERE, packed, digest, file_hash, write_json
from prepare_model_view import materialize

root = HERE.parents[1]
external = root/'external/wsp-vlm-open-repair-v7-2026-11-05'
external.mkdir(exist_ok=True)
download = root/'experiments/wsp-vlm-processor-prep-v4-2026-11-05/audit/download_manifest.json'
model = external/'model'
if not model.exists():
    materialize(json.loads(download.read_text())['snapshot'], download, model)
hashes = json.loads((model/'view-receipt.json').read_text())['files']
processor = json.loads((root/'experiments/wsp-vlm-channel-prep-v5-2026-11-05/audit/processor_manifest.json').read_text())['processor_sha256']
receipt = dict(user_request='同意，推进吧', date='2026-11-05',
    scope='B/C continuation: engineering 1 single-GPU hour; exploration 2 hours per branch; no new confirmation claims',
    researcher='Reuse previous math gpt-6-astra max with existing ChatGPT login; no API fallback or credit purchase',
    new_budget_not_screen_remainder=True)
write_json(HERE/'authorization.json', receipt)
for task in 'BC':
    conditions = ['total','subset'] if task=='B' else ['no_image_usual','original_usual','counterfact_usual','original_visual','counterfact_visual']
    c = dict(actions=100, forwards=12000 if task=='B' else 24000,
        samples=12000 if task=='B' else 24000, target_tokens=50000000 if task=='B' else 100000000,
        wall_seconds=7200, python_seconds=1200, max_input_tokens=4096, max_measure_elements=2000000,
        temporary_scalars=4000000, final_scalars=1000000, researcher_turns=100,
        researcher_tokens=5000000, researcher_usd=None, researcher_turn_reserve_usd=None,
        max_format_rate=.01, max_protection_drop=.035, protection_conditions=conditions)
    cfg = dict(mode='live', authorized=True, phase='engineering', aliases={'lm_head.weight':'model.language_model.embed_tokens.weight'}, contract=c,
        contract_sha256=digest(packed(c)), authorization_record=receipt,
        model_root=str(model), model_file_sha256=hashes, processor_sha256=processor,
        evidence_root=str(external/(task+'_D')), evidence_sha256=file_hash(external/(task+'_D/bundle.json')),
        researcher_cli='/usr/local/bin/codex', researcher_cli_sha256=file_hash('/usr/local/bin/codex'),
        researcher_model='gpt-6-astra', researcher_turn_seconds=900, researcher_billing='existing_chatgpt',
        researcher_account_record='codex login status: Logged in using ChatGPT; forced_login_method=chatgpt; no key env',
        sandbox=dict(bwrap='/usr/bin/bwrap', prefix=sys.base_prefix,
            environment=str(root/'.venv-wsp-v7-cpu'), python=str(root/'.venv-wsp-v7-cpu/bin/python')),
        run_root=str(external/('search-'+task)), screen_run_root=str(root/'external/wsp-vlm-channel-prep-v5-2026-11-05'),
        engineering_acceptance_path=str(HERE/'audit/engineering_acceptance.json'), engineering_acceptance_sha256=None)
    write_json(HERE/('config-'+task+'.json'),cfg)
print('Prepared B/C numeric contracts and model view; phase=engineering, search not unlocked')
