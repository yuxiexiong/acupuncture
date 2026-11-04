"""64 synthetic engineering requests, separate from every scientific source group."""
import json
from PIL import Image,ImageDraw
from prepare_inputs import HERE,ROOT,B1,sha
from prepare_c import B1 as C1


def build():
    folder=HERE/'fixtures';folder.mkdir(exist_ok=True)
    requests=[];gold=[];manifest=[]
    for k in range(8):
        width,height=[(320,240),(640,480),(1024,768),(480,640)][k%4]
        image=Image.new('RGB',(width,height),'white');draw=ImageDraw.Draw(image)
        ns,nc=2+k%4,1+k%3
        for i in range(ns):
            x=width*(i+1)/(ns+1); y=height*.3;size=min(width,height)*.07
            draw.rectangle((x-size,y-size,x+size,y+size),fill='red')
        for i in range(nc):
            x=width*(i+1)/(nc+1);y=height*.7;size=min(width,height)*.03
            draw.ellipse((x-size,y-size,x+size,y+size),fill='blue')
        path=folder/f'P0_{k}.png';image.save(path)
        rel=str(path.relative_to(ROOT))
        manifest.append(dict(path=rel,png_sha256=sha(path.read_bytes())))
        cases=[('B','total',f'How many shapes are in this image? Return only an integer.',str(ns+nc),rel),
               ('B','subset','How many red squares are above the blue circles? Return only an integer.',str(ns),rel),
               ('C','no_image','In the real world, which is typically larger, a dog or an ant? Return only the object\'s name.','dog',None),
               ('C','image','Which shape appears larger in this image, a red square or a blue circle? Return only the object\'s name.','red square',rel)]
        for task,condition,text,answer,img in cases:
            for arm in ('B0','B1'):
                rid=f'P0-{k}:{task}:{condition}:{arm}'
                requests.append(dict(request_id=rid,text=((B1 if task=='B' else C1)+'\n' if arm=='B1' else '')+text,image=img))
                gold.append(dict(request_id=rid,task=task,arm=arm,answer=answer,identity='engineering_only_not_B_or_C_sample'))
    for name,rows in [('P0_inputs',requests),('P0_gold',gold)]:
        (HERE/'prepared'/f'{name}.jsonl').write_text(''.join(json.dumps(r,sort_keys=True)+'\n' for r in rows))
    (HERE/'audit/P0_images.json').write_text(json.dumps(manifest,indent=2)+'\n')
    receipt_path=HERE/'audit/input_receipt.json'
    receipt=json.loads(receipt_path.read_text())
    for name in ('P0_inputs.jsonl','P0_gold.jsonl'):
        data=(HERE/'prepared'/name).read_bytes()
        receipt['files'][name]=dict(sha256=sha(data),records=64)
    receipt_path.write_text(json.dumps(receipt,indent=2)+'\n')
    assert len(requests)==64


if __name__=='__main__':build()
