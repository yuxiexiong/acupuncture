"""Model-specific acceptance; otherwise the unchanged v8 service assembly."""
import json
from pathlib import Path
from common import packed, digest, file_hash, write_json, require_live


def check_search_readiness(config):
    p = Path(config['engineering_acceptance_path'])
    if file_hash(p) != config['engineering_acceptance_sha256']:
        raise ValueError('Engineering receipt changed')
    r = json.loads(p.read_text())
    needed = ('isolation', 'module_mapping', 'input_equivalence',
              'measurement_numerics', 'edit_rollback_reload', 'batch64_repeat')
    if (r.get('real_model_acceptance') is not True or r.get('synthetic_only') is not False or
        r.get('revision') != config.get('model_revision') or
        any(r.get('checks', {}).get(k) is not True for k in needed)):
        raise ValueError('Real model-specific acceptance incomplete')
    if r['model_files'] != config['model_file_sha256']:
        raise ValueError('Acceptance belongs to a different checkpoint')
    for name, expected in r['engine_hashes'].items():
        if file_hash(Path(__file__).parent/name) != expected:
            raise ValueError('Accepted engine changed: '+name)


def build_service(config):
    require_live(config)
    check_search_readiness(config)
    from weights import TensorSource, Candidates
    from evidence import Evidence
    from kernel import SandboxKernel
    from backend import VLMBackend
    from service import Service
    root = Path(config['run_root'])
    root.mkdir(parents=True, exist_ok=False)
    write_json(root/'config.json', config)
    for name in ('public', 'work', 'candidates', 'artifacts', 'inbox'):
        (root/name).mkdir()
    c = config['contract']
    source = TensorSource(config['model_root'], config['aliases'])
    candidates = Candidates(source, root/'candidates', c['temporary_scalars'], c['final_scalars'])
    evidence = Evidence(config['evidence_root'], config['evidence_sha256'])
    write_json(root/'public/kernel.json', dict(aliases=source.aliases,
        temporary_scalars=c['temporary_scalars'], final_scalars=c['final_scalars']))
    kernel = SandboxKernel(config, root/'work', root/'public', root/'candidates', evidence.root, root/'artifacts')
    backend = VLMBackend(config, source, evidence)
    protocol = digest(packed(dict(model=source.identity, evidence=evidence.identity, config=config,
                                 generation='v5-BF16-SDPA-greedy128')))
    service = Service(root, candidates, evidence, backend, kernel, c, protocol)
    try:
        baseline, _ = service.evaluate_one(candidates.base_id, list(evidence.records))
        # Same complete feedback, now from this model; never reuse 4B predictions.
        write_json(root/'artifacts/baseline.json', baseline)
        return service
    except BaseException:
        service.close()
        raise
