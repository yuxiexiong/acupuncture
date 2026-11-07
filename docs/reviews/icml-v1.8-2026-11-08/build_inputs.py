"""Prepare a fresh-reader packet; preserve scientific text and log administrative edits."""
from pathlib import Path
import subprocess,json,hashlib,re,posixpath,difflib,shutil
ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
PACKET=Path('/private/tmp/acupuncture-blind-packet-final-20261108')
BASE='3f0cb59a373d14d3b11c40227c420f2b587587ec'
def blob(p):return subprocess.check_output(['git','show',BASE+':'+p],cwd=ROOT)
def sha(b):return hashlib.sha256(b).hexdigest()
mainpath='docs/mechanism-paper-skeleton-2026-11-05.zh-CN.md'
supppath='docs/mechanism-paper-supplement-v1.8-2026-11-08.zh-CN.md'
texts={mainpath:blob(mainpath).decode(),supppath:blob(supppath).decode()}
# Use the preceding panel's evidence inventory as a source list only, not review content.
old=json.loads(blob('docs/reviews/icml-v1.7-2026-11-08/inputs.json'))
allowed={f['path'] for f in old['files'] if f['path'].startswith(('experiments/','docs/figures/'))}
for path,text in texts.items():
 for url in re.findall(r'\]\(([^)\s]+)\)',text):
  if re.match(r'[a-z]+:',url):continue
  p=posixpath.normpath(posixpath.join(posixpath.dirname(path),url.split('#')[0]))
  if p.startswith(('experiments/','docs/figures/')):allowed.add(p)
allowed.add('docs/paper-revision-v1.8-2026-11-08/source-audit.json')
allowed={p for p in allowed if Path(p).suffix in ('.json','.py','.svg')}
files=[]
for p in sorted(allowed):
 b=blob(p);dest=PACKET/'attachments'/p;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(b)
 files.append({'path':'attachments/'+p,'source_path':p,'bytes':len(b),'sha256':sha(b)})
for path,text in texts.items():
 name='paper.zh-CN.md' if path==mainpath else 'supplement.zh-CN.md'
 original=text
 text=re.sub(r'<!--block:B\d+-->\n','',text)
 text=text.replace('本次修订无GPU使用。','')
 text=re.sub(r'^- v1\.7复用已有跨模型结果.*\n','',text,flags=re.M)
 text=text.replace('- v1.6同步摘要、引言贡献、方法、§4.10表6、机制连接图、覆盖、缺口、近邻增量与结论；旧实验数字和负结果保留。','- ')
 if path==mainpath:
  lines=text.splitlines();lines[2]='中文研究稿。完整结果、覆盖与图件见[补充材料](supplement.zh-CN.md)。';text='\n'.join(lines)+'\n'
 else:
  text=text.replace('# Acupuncture v1.8 补充证据：完整结果、范围与历史图','# 补充材料：完整结果、范围与图件',1)
  lines=text.splitlines();lines[2]='以下为正文的完整结果、覆盖与图件。表号及部分章节编号沿用各实验记录；科学主张以正文为准。';text='\n'.join(lines)+'\n'
 def link(m):
  label,url=m.group(1),m.group(2)
  if re.match(r'[a-z]+:',url) or url.startswith('#'):return m.group(0)
  p=posixpath.normpath(posixpath.join(posixpath.dirname(path),url.split('#')[0]));frag=('#'+url.split('#',1)[1]) if '#' in url else ''
  if p==mainpath:return '['+label+'](paper.zh-CN.md'+frag+')'
  if p==supppath:return '['+label+'](supplement.zh-CN.md'+frag+')'
  if p in allowed:return '['+label+'](attachments/'+p+frag+')'
  return label+'〔未随稿提供的内部链接〕'
 text=re.sub(r'\[([^\]]+)\]\(([^)\s]+)\)',link,text)
 (PACKET/name).write_text(text)
 (OUT/('original-'+name)).write_text(original)
 (OUT/name).write_text(text)
 (OUT/(name+'.packet.diff')).write_text(''.join(difflib.unified_diff(original.splitlines(True),text.splitlines(True),fromfile=path,tofile=name,n=0)))
 files.append({'path':name,'source_path':path,'bytes':len(text.encode()),'sha256':sha(text.encode()),'source_sha256':sha(original.encode())})
manifest={'source_commit':BASE,'files':files,'scope':'Read only paper, supplement, listed attachments, official texts and BRIEF; do not follow other repository links.'}
for p in [PACKET/'inputs.json',OUT/'inputs.json']:p.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
for i in (1,2,3):(PACKET/f'reviewer-{i}').mkdir(exist_ok=True)
print(json.dumps({'attachment_count':len(allowed),'packet':str(PACKET),'paper_sha256':sha((PACKET/'paper.zh-CN.md').read_bytes()),'supplement_sha256':sha((PACKET/'supplement.zh-CN.md').read_bytes())}))
