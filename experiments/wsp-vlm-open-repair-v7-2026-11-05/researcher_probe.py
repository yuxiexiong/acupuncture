"""Three-turn image/session probe, no target model and no weight search."""
import json
from pathlib import Path
from common import HERE, packed, digest, write_json
from controller import CodexResearcher
import argparse
import re
from common import file_hash

ap=argparse.ArgumentParser();ap.add_argument('--config',type=Path,default=HERE/'config-B.json');ap.add_argument('--out',type=Path,default=HERE/'audit/researcher-probe');ap.add_argument('--cli');ap.add_argument('--resume-after-image',action='store_true');a=ap.parse_args()
cfg=json.loads(a.config.read_text())
if a.cli:
    cfg['researcher_cli']=a.cli;cfg['researcher_cli_sha256']=file_hash(a.cli)
cfg['contract']=dict(cfg['contract'],researcher_turns=3,researcher_tokens=100000)
cfg['contract_sha256']=digest(packed(cfg['contract']))
out=a.out;out.mkdir(exist_ok=a.resume_after_image)
from PIL import Image,ImageDraw
picture=Image.new('RGB',(320,160),'white');draw=ImageDraw.Draw(picture)
draw.rectangle((20,25,135,135),fill='red');draw.rectangle((185,25,300,135),fill='blue')
picture.save(out/'fixture.png')
r=CodexResearcher(cfg,out/('empty-resume' if a.resume_after_image else 'empty'))
if a.resume_after_image:
    receipt=json.loads((out/'turn1/receipt.json').read_text())
    r.thread=receipt['thread'];r.used_turns=1;r.used_tokens=receipt['cumulative_tokens']
    text=(out/'turn1/reply.txt').read_text()
else:
    text=r.turn('Engineering image transport test only. Return JSON with keys left_color and right_color for the two rectangles, lowercase English. Remember nonce MAPLE_7319 for the next turn. No tools or fenced blocks.',[out/'fixture.png'],out/'turn1')
def unfence(text):
    return re.sub(r'^```[^\n]*\n|\n```\s*$','',text.strip())
assert json.loads(unfence(text))==dict(left_color='red',right_color='blue'),text
text=r.turn('Engineering session continuation test. Reply exactly the nonce from the previous turn. No tools.',[],out/'turn2')
assert unfence(text)=='MAPLE_7319',text
text=r.turn('Engineering resume-image test. For this attached image reply exactly the two rectangle colors in left-to-right order, separated by one comma with no spaces. No tools.',[out/'fixture.png'],out/'turn3')
assert unfence(text)=='red,blue',text
write_json(out/'receipt.json',dict(passed=True,checks=['image','session','resume_image'],target_model_calls=0,turns=3))
print('RESEARCHER_IMAGE_SESSION_OK')
