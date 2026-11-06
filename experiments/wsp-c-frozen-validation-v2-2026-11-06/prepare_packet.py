"""Build label-blind review packet from frozen candidates; CPU only, no models."""
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
AUDIT = ROOT / 'experiments/wsp-c-external-data-audit-v1-2026-11-06'
DATA = ROOT / 'external/wsp-c-external-data-audit-v1-2026-11-06'
BLIND = ROOT / 'external/wsp-c-frozen-validation-v2-2026-11-06/blind'

def digest(b):
    return hashlib.sha256(b).hexdigest()

def save(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')

# Preserve the original relation; length, height and width are extension tasks.
VLIND = {
    0: ('egg', 'apple', 'larger'), 5: ('key', 'person', 'longer'),
    7: ('coin', "person's hand", 'larger'), 8: ('loaf of bread', 'baker', 'longer'),
    9: ('wristwatch', 'camera', 'larger'), 10: ('book', 'librarian', 'taller'),
    14: ('corn cob', "farmer's arm", 'larger'), 17: ('laptop', 'person', 'wider'),
    23: ('cup', 'tourist', 'larger'), 24: ('fish hook', "fisherman's hand", 'larger'),
    25: ('ant', "person's foot", 'larger'), 26: ('desk lamp', 'person', 'taller'),
    28: ('eyeglasses', 'person', 'wider'), 32: ('hat', 'person', 'larger'),
    33: ('paper clip', "person's hand", 'longer'), 35: ('snowflake', "person's hand", 'larger'),
    37: ('raindrop', "person's hand", 'larger'), 39: ('toothbrush', "person's arm", 'longer'),
    41: ('calculator', 'person', 'larger'), 42: ('feather', 'person', 'longer'),
    43: ('nail', "person's hand", 'longer'), 46: ('matchstick', 'person', 'longer'),
}

def main():
    BLIND.mkdir(parents=True, exist_ok=True)
    panel = [r for r in json.loads((AUDIT/'candidate-panel.json').read_text()) if r['task'] == 'size']
    rows = {r['image']: r for f in DATA.glob('size*.jsonl') for r in map(json.loads, f.read_text().splitlines())}
    native = {r['context_id']: r for r in json.loads((DATA/'vlind-data.json').read_text())}
    jobs = []
    sources = []
    for r in panel:
        if r['dataset'] == 'whatif':
            source = rows[r['image_id'].split(':',1)[1]]
            prior, visual = source['prior_answer'], source['context_answer']
            names, relation = sorted([prior, visual]), 'larger'
            images = [('counterfactual', DATA/'whatif'/source['image'].lstrip('./'), visual)]
            metadata = {'original_question':source['question'], 'original_statement':source['statement']}
        else:
            cid = int(r['family'].split(':')[1])
            visual, prior, relation = VLIND[cid]
            names = sorted([prior, visual])
            images = [(kind, DATA/'vlind'/f'{cid}_{kind}.jpg', visual if kind=='counterfactual' else prior)
                      for kind in ('counterfactual','factual')]
            metadata = {'original_true_statement': native[cid]['true_statement'],
                        'original_false_statement': native[cid]['false_statement']}
        sources.append(dict(source_id=r['family'], stratum='rome' if r['dataset']=='whatif' else 'vlind',
                            names=names, relation=relation, prior=prior, **metadata))
        for kind, path, answer in images:
            jobs.append(dict(source_id=r['family'], kind=kind, path=str(path.relative_to(ROOT)),
                             names=names, relation=relation, expected_prior=prior, expected_visual=answer,
                             sha256=digest(path.read_bytes())))
    jobs.sort(key=lambda r:digest(('C-FV-02-review:'+r['source_id']+':'+r['kind']).encode()))
    blind=[]
    for i,j in enumerate(jobs):
        rid=f'R{i+1:03d}'
        j['review_id']=rid
        dest=BLIND/(rid+Path(j['path']).suffix)
        shutil.copyfile(ROOT/j['path'], dest)
        blind.append(dict(review_id=rid,image=str(dest.relative_to(ROOT)),names=j['names'],relation=j['relation'],
                          visual_question=f"In this picture, which of these two objects looks {j['relation']}: {j['names'][0]} or {j['names'][1]}?",
                          prior_question=f"In everyday life, which of these two objects tends to be {j['relation']}: {j['names'][0]} or {j['names'][1]}?"))
    assert len(panel)==112 and len(jobs)==134 and len({r['review_id'] for r in blind})==134
    save(HERE/'source-candidates.json',sources)
    save(HERE/'review-key.json',jobs)
    save(BLIND/'items.json',blind)
    save(HERE/'blind-items.json',blind)
    print(json.dumps({'sources':len(panel),'review_images':len(jobs),'blind_packet':str(BLIND),'key_sha256':digest((HERE/'review-key.json').read_bytes())}))

if __name__ == '__main__':
    main()
