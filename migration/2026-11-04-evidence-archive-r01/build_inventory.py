"""Inventory repository research files and local external evidence, without loading models."""
from pathlib import Path
import collections
import hashlib
import json
import subprocess
import sys

root = Path(__file__).resolve().parents[2]
base = Path(__file__).resolve().parent
source = Path(sys.argv[1]).resolve()
def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda: f.read(1048576), b''):
            h.update(b)
    return h.hexdigest()
def paths_at(r, *args):
    return set(filter(None, subprocess.check_output(['git','ls-files',*args,'-z'],cwd=r).decode().split('\0')))
# Inventoried evidence excludes this delivery's derived inventory/verification files.
paths = paths_at(root,'--cached','--others','--exclude-standard')
rows=[]
for name in sorted(paths):
    if not name.startswith(('experiments/','docs/','migration/')):
        continue
    if name.startswith(str(base.relative_to(root))+'/') and '/local-variants/' not in name:
        continue
    if name in ('docs/RESEARCH_ASSET_CATALOG_2026-11-04.zh-CN.md',):
        continue
    p=root/name
    if p.is_file():
        rows.append({'path':name,'bytes':p.stat().st_size,'sha256':sha(p)})
with (base/'assets.jsonl').open('w') as f:
    for row in rows:f.write(json.dumps(row,ensure_ascii=False)+'\n')
external=[]
for name in sorted(paths_at(source,'--others','--ignored','--exclude-standard')):
    p=source/name
    if '__pycache__' in name or '/.pytest_cache/' in name or p.suffix=='.pyc' or p.name=='.DS_Store':continue
    if not name.startswith('experiments/'):continue
    external.append({'path':name,'bytes':p.stat().st_size,'sha256':sha(p),'location':str(source/name),'status':'local_external_not_uploaded'})
(base/'local-external-assets.json').write_text(json.dumps(external,ensure_ascii=False,indent=2)+'\n')
experiments=collections.defaultdict(list)
for row in rows:
    parts=row['path'].split('/')
    if parts[0]=='experiments' and len(parts)>2:experiments[parts[1]].append(row)
text=['# Acupuncture：全目录资产表（2026-11-04）','',
      '本表覆盖交付树内全部一级实验目录，既有报告、设计、审计、工具和工程材料均列入。**目录数、文件数不是独立实验或样本数。** 分类描述材料身份，不以文件存在判定科学阳性；完成、失败、停止与更正应连同报告／收据阅读。', '',
      '[理论与结果总览](RESEARCH_ARCHIVE_2026-11-04.zh-CN.md) · [逐文件SHA-256](../migration/2026-11-04-evidence-archive-r01/assets.jsonl) · [归档范围与例外](../migration/2026-11-04-evidence-archive-r01/README.zh-CN.md)', '',
      f'共 **{len(experiments)} 个一级目录**。实验目录文件共 {sum(len(v) for v in experiments.values()):,} 个；同一记录的来源副本保留，所以不能按文件数推导实验工作量。','',
      '| 目录 | 材料身份 | 文件数／字节 | 报告、合同与数据入口 |','|---|---|---:|---|']
for name,items in sorted(experiments.items()):
    d=root/'experiments'/name
    if name.startswith('wsp-'):kind='工程验收／运行快照；正式完成状态另核'
    elif name.startswith('cross-model-foundation'):kind='工程预检；存在未过项，非科学结果'
    elif name.startswith(('cross-model-history','cross-model-natural','native-behavior-reference')):kind='方案／合同；无正式结果'
    elif 'design' in name:kind='设计／审计；不计模型实验'
    elif any(s in name for s in ('audit','analysis','local-path','energy-ledger','question-dependence')):kind='既有数据分析／审计；非独立样本'
    elif name.startswith(('advisor','neuron-explorer','model-assets')):kind='报告／工具／资产工程'
    elif name.startswith('div01'):kind='第零步执行完；够数闸FAIL，已停止'
    elif name.startswith('llama31-layer-dose'):kind='旧合并运行按用户停止；partial保留'
    elif name.startswith('cross-family-transfer'):kind='阶段一及停止证据；阶段二未运行'
    elif name.startswith('transfer-toy'):kind='机器阶段结果；结构化行为盲评未完成'
    elif name.startswith('x-recipe'):kind='采集完成；并排解释报告未完成'
    else:kind='实验／结果材料；具体完成与限制见右栏'
    files=[Path(x['path']) for x in items]
    docs=[p for p in files if p.suffix=='.md' and len(p.parts)==3]
    docs.sort(key=lambda p:(0 if p.name.startswith(('REPORT','RESULTS','IMPLEMENTATION')) else 1 if p.name.startswith(('CONTRACT','PROTOCOL')) else 2,str(p)))
    if not docs:
        docs=[p for p in files if p.suffix=='.md' and any(s in p.name for s in ('RESULTS','README','REPORT'))][:3]
    links=[f'[{p.name}](../{p.as_posix()})' for p in docs[:3]]
    data=[q for q in ('runs','analysis','exports','reading-r01','qualitative-pass-r01','local-runtime-archive-r01') if (d/q).is_dir()]
    links += [f'[{q}](../experiments/{name}/{q}/)' for q in data]
    text.append(f'| [{name}](../experiments/{name}/) | {kind} | {len(items):,} / {sum(x["bytes"] for x in items):,} | '+ ' · '.join(links)+' |')
text+=['','## 读取规则','','正式运行、预检、smoke、失败重试分别保留。`source/` 内是为分析保存的来源副本，`local-runtime-archive-r01` 含测试夹具与运行快照，均不得作为额外独立样本。仅有设计材料的目录不进入已完成科学结果计数。','',
       '模型权重、环境、缓存不入Git；已有大张量和压缩内部轨迹按本次本地外置清单及历史服务器收据定位。服务器引用本轮未逐字节重验，不能称为完整备份认证。']
(root/'docs/RESEARCH_ASSET_CATALOG_2026-11-04.zh-CN.md').write_text('\n'.join(text)+'\n')
summary={'source_commit':subprocess.check_output(['git','rev-parse','origin/main'],cwd=root).decode().strip(),
 'research_files':len(rows),'research_bytes':sum(x['bytes'] for x in rows),'experiment_directories':len(experiments),
 'experiment_files':sum(len(x) for x in experiments.values()),'local_external_files':len(external),
 'local_external_bytes':sum(x['bytes'] for x in external),'assets_manifest_sha256':sha(base/'assets.jsonl'),
 'inventory_excludes':'This delivery derived catalog and own non-variant migration files, preventing circular hashing'}
(base/'inventory-summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(summary)
