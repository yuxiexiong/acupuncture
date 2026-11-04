"""Paired original / real-processor previews for visual inspection; no models."""
import json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageOps
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
ASSETS=ROOT/'external/wsp-vlm-processor-prep-v4-2026-11-05'
preview=ASSETS/'processor_audit'
out=ASSETS/'review_sheets';out.mkdir(parents=True,exist_ok=True)
font=ImageFont.truetype('/System/Library/Fonts/Monaco.ttf',16)
records=json.loads((preview/'manifest.json').read_text())['images']
pages=[]
for start in range(0,len(records),6):
    chunk=records[start:start+6]
    canvas=Image.new('RGB',(1800,1140),'#dddddd');draw=ImageDraw.Draw(canvas)
    for i,r in enumerate(chunk):
        x=(i%2)*900;y=(i//2)*380
        draw.text((x+5,y+3),f"{start+i:03d} {Path(r['source']).name}",font=font,fill='black')
        for j,path in enumerate((ROOT/r['source'],preview/r['preview'])):
            im=Image.open(path).convert('RGB')
            draw.text((x+j*450+5,y+25),f"{'source' if j==0 else 'processor'} {im.size}",font=font,fill='black')
            tile=ImageOps.contain(im,(445,325))
            canvas.paste(tile,(x+j*450+(450-tile.width)//2,y+50+(325-tile.height)//2))
    name=f'{start//6:02d}.jpg';canvas.save(out/name,quality=95)
    pages.append(dict(page=name,indices=list(range(start,start+len(chunk))),sources=[r['source'] for r in chunk]))
(HERE/'audit/review_pages.json').write_text(json.dumps(pages,indent=2)+'\n')
print(len(pages),'pages',len(records),'images')
