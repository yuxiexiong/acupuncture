"""Observer-only one-shot confirmation helper, not an AI tool.

No confirmation dataset or statistical success threshold is invented here. Caller
must freeze its unseen source registry, bundle and acceptance protocol separately.
"""
import json
from pathlib import Path
from common import file_hash, write_json
from evidence import Evidence
from service import Service


class NoResearcherKernel:
    def call(self, *args):
        raise PermissionError('No researcher Python in confirmation')
    def close(self): pass


def confirm(frozen_path, frozen_sha256, candidates, evidence_root, evidence_sha256,
            seen_group_keys, seen_image_hashes, independence_audit_sha256,
            backend_factory, out, contract, protocol_identity):
    """backend_factory receives only the confirmation input bundle, never researcher state.

    A fresh backend is required. The output directory must not exist, even if a prior
    confirmation failed. No accept/edit operation or confirmation-to-AI feedback occurs.
    """
    if file_hash(frozen_path) != frozen_sha256:
        raise ValueError('Frozen candidate record changed')
    frozen = json.loads(Path(frozen_path).read_text())
    m = candidates.freeze(frozen['manifest']['id'])
    if m != frozen['manifest']:
        raise ValueError('Frozen patch no longer matches saved candidate')
    evidence = Evidence(evidence_root, evidence_sha256, role='confirmation', split='Q')
    group_keys = {(evidence.task, r['gold']['group_id']) for r in evidence.records.values()}
    if not seen_group_keys or group_keys & set(map(tuple, seen_group_keys)):
        raise ValueError('Confirmation overlaps seen groups or seen registry missing')
    images = {evidence.package['files'][r['input']['image']] for r in evidence.records.values() if r['input']['image']}
    if not independence_audit_sha256 or not seen_image_hashes or images & set(seen_image_hashes):
        raise ValueError('Confirmation repeats seen image bytes or independence audit/registry missing')
    root = Path(out)
    root.mkdir(parents=True, exist_ok=False)
    backend = backend_factory(evidence)
    if getattr(backend, 'model', None) is not None:
        raise ValueError('Confirmation must start from a freshly unloaded backend')
    service = Service(root, candidates, evidence, backend, NoResearcherKernel(), contract, protocol_identity)
    try:
        ids = list(evidence.records)
        original, _ = service.evaluate_one(candidates.base_id, ids)
        patched, _ = service.evaluate_one(m['id'], ids)
        result = dict(status='measured_no_statistical_claim', frozen_sha256=frozen_sha256,
                      original=original, patched=patched, researcher_access=False,
                      independence_audit_sha256=independence_audit_sha256,
                      note='B0/B1 inputs provide original/prompt/patch/patch+prompt arms; nearest-method arms still need separate frozen artifacts.')
        write_json(root/'confirmation.json', result)
        return result
    finally:
        service.close()
