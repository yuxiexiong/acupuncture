import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { LineSegments2 } from 'three/addons/lines/LineSegments2.js';
import { LineSegmentsGeometry } from 'three/addons/lines/LineSegmentsGeometry.js';
import { LineMaterial } from 'three/addons/lines/LineMaterial.js';

// Layer × actual prediction step × measured difference. No inferred causal edges.
const WIDTH = 24, DEPTH = 16, HEIGHT = 8;
const METRICS = {
  relative_delta: {label:'相对差分', cap:10, ticks:[0,0.1,1,10]},
  delta_norm: {label:'差分范数', cap:100, ticks:[0,1,10,100]},
  cosine: {label:'1 − cosine', cap:2, ticks:[0,0.5,1,2]},
};
const COMPONENTS = {attention:'Attention / GatedDeltaNet', mlp:'MLP', residual:'层末残差'};
const finite = value => typeof value === 'number' && Number.isFinite(value);

export function createPropagation(canvas, labels, {onSelect} = {}) {
  const renderer = new THREE.WebGLRenderer({canvas, antialias:true, alpha:false});
  renderer.setPixelRatio(Math.min(devicePixelRatio,2)); renderer.setClearColor('#0a101a');
  const scene = new THREE.Scene(), camera = new THREE.PerspectiveCamera(38,1,0.02,2000);
  const controls = new OrbitControls(camera,canvas);
  controls.enableDamping = false; controls.minDistance = 3; controls.zoomSpeed = 0.8;
  const content = new THREE.Group(); scene.add(content);
  const ray = new THREE.Raycaster(); ray.params.Points.threshold = 0.28;
  const mouse = new THREE.Vector2(), markers = [];
  Object.assign(labels.style,{position:'absolute',inset:'0',pointerEvents:'none',overflow:'hidden'});
  let trace = null, injection = null, component = 'residual', metric = 'relative_delta';
  let layers = 0, steps = 0, prompt = 0, position = -1, values = [], maxHeight = HEIGHT;
  let surface, samples, sampleIds = [], current, balls, lineMaterial, pending = false, down = null;
  const x = layer => layers > 1 ? WIDTH*layer/(layers-1) : WIDTH/2;
  const z = step => steps > 1 ? DEPTH*step/(steps-1) : 0;
  const height = value => HEIGHT*Math.log1p(value)/Math.log1p(METRICS[metric].cap);
  const point = (layer,step) => new THREE.Vector3(x(layer),height(values[step*layers+layer]),z(step));
  function color(value) {
    const t=Math.min(1,Math.max(0,height(value)/HEIGHT));
    return new THREE.Color().setHSL(0.57-0.53*t,0.72,0.48+0.12*t);
  }
  function label(text,location,style={}) {
    const el=document.createElement('span'); el.textContent=text;
    Object.assign(el.style,{position:'absolute',color:'#b5c7db',font:'11px ui-monospace, monospace',whiteSpace:'nowrap',transform:'translate(-50%,-50%)',textShadow:'0 1px 4px #000',...style});
    labels.appendChild(el);markers.push({el,location});return el;
  }
  function render() {
    if(pending)return;pending=true;
    requestAnimationFrame(()=>{
      pending=false;renderer.render(scene,camera);
      for(const marker of markers){
        const p=marker.location.clone().project(camera);
        marker.el.style.display=p.z>1||p.z< -1?'none':'';
        marker.el.style.left=((p.x+1)/2*canvas.clientWidth)+'px';
        marker.el.style.top=((1-p.y)/2*canvas.clientHeight)+'px';
      }
    });
  }
  function clear() {
    content.traverse(object=>{object.geometry?.dispose();if(object.material){for(const m of [object.material].flat())m.dispose();}});
    content.clear();labels.replaceChildren();markers.length=0;
    surface=samples=current=balls=lineMaterial=null;sampleIds=[];
  }
  function lineSegments(positions,colorValue,opacity=1) {
    const geometry=new THREE.BufferGeometry();geometry.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));
    const line=new THREE.LineSegments(geometry,new THREE.LineBasicMaterial({color:colorValue,transparent:opacity<1,opacity,depthWrite:false}));content.add(line);return line;
  }
  function axes() {
    const depth=steps>1?DEPTH:0;
    lineSegments([0,0,0,WIDTH,0,0,0,0,0,0,maxHeight,0,0,0,0,0,0,depth],'#8198b2');
    const grid=[];
    for(let l=0;l<layers;l++){grid.push(x(l),0,0,x(l),0,depth);if(l===0||l===layers-1||l%4===0)label('L'+l,new THREE.Vector3(x(l),-0.5,-0.5));}
    const stride=Math.max(1,Math.ceil(steps/6));
    for(let s=0;s<steps;s++)if(s===0||s===steps-1||s%stride===0){grid.push(0,0,z(s),WIDTH,0,z(s));label(String(s+1),new THREE.Vector3(-0.7,0,z(s)));}
    lineSegments(grid,'#52657a',0.25);
    const info=METRICS[metric],ticks=[...info.ticks];
    for(let v=info.cap*10;height(v)<=maxHeight&&finite(v);v*=10)ticks.push(v);
    for(const v of ticks){const y=height(v);lineSegments([-0.2,y,0,0.2,y,0],'#8198b2');label(v<1000?String(v):v.toExponential(0),new THREE.Vector3(-0.6,y,-0.5),{color:'#d4e3f0'});}
    label('层 →',new THREE.Vector3(WIDTH/2,-1.25,-0.8),{color:'#edf4ff',fontSize:'12px'});
    label('预测第几个输出 token →',new THREE.Vector3(-2,0,depth/2),{color:'#edf4ff',fontSize:'12px'});
    label(info.label+' · log1p 高度',new THREE.Vector3(0,maxHeight+0.8,0),{color:'#edf4ff',fontSize:'12px'});
    if(injection!=null&&Number.isInteger(injection)&&injection>=0&&injection<layers){
      const bar=new THREE.Mesh(new THREE.BoxGeometry(0.15,0.07,Math.max(depth,0.7)),new THREE.MeshBasicMaterial({color:'#ffd17a'}));
      bar.position.set(x(injection),0.05,depth/2);content.add(bar);
      label('注入 L'+injection,new THREE.Vector3(x(injection),-0.5,depth+0.8),{color:'#ffd17a'});
    }
  }
  function rebuild(fit=true) {
    clear();values=[];
    if(!trace){
      const empty=document.createElement('div');empty.textContent='未采集内部轨迹';Object.assign(empty.style,{position:'absolute',inset:'45% 0 auto',textAlign:'center',color:'#9aacc0',font:'13px sans-serif'});labels.appendChild(empty);render();return;
    }
    const sites=new Map(trace.sites.filter(s=>s.component===component).map(s=>[s.layer,s]));
    const vertices=[],colors=[],dots=[],dotColors=[],indices=[],wires=[];
    maxHeight=HEIGHT;
    for(let s=0;s<steps;s++)for(let l=0;l<layers;l++){
      const raw=sites.get(l)?.[metric]?.[prompt-1+s];
      const value=finite(raw)?Math.max(0,metric==='cosine'?1-raw:raw):null;
      values.push(value);const y=value==null?0:height(value);maxHeight=Math.max(maxHeight,y);
      vertices.push(x(l),y,z(s));const c=value==null?new THREE.Color('#747b88'):color(value);colors.push(c.r,c.g,c.b);
      if(value!=null){dots.push(x(l),y,z(s));dotColors.push(c.r,c.g,c.b);sampleIds.push({layer:l,step:s});}
    }
    const valid=i=>values[i]!=null;
    for(let s=0;s<steps;s++)for(let l=0;l<layers;l++){
      const a=s*layers+l;
      for(const b of [l+1<layers?a+1:-1,s+1<steps?a+layers:-1])if(b>=0&&valid(a)&&valid(b))wires.push(...vertices.slice(a*3,a*3+3),...vertices.slice(b*3,b*3+3));
      if(l+1<layers&&s+1<steps){const b=a+1,c=a+layers,d=c+1;if([a,b,c].every(valid))indices.push(a,c,b);if([b,c,d].every(valid))indices.push(b,c,d);}
    }
    if(indices.length){
      const geometry=new THREE.BufferGeometry();geometry.setAttribute('position',new THREE.Float32BufferAttribute(vertices,3));geometry.setAttribute('color',new THREE.Float32BufferAttribute(colors,3));geometry.setIndex(indices);
      surface=new THREE.Mesh(geometry,new THREE.MeshBasicMaterial({vertexColors:true,transparent:true,opacity:0.34,side:THREE.DoubleSide,depthWrite:false}));content.add(surface);
    }
    lineSegments(wires,'#82c8db',0.34);
    const sampleGeometry=new THREE.BufferGeometry();sampleGeometry.setAttribute('position',new THREE.Float32BufferAttribute(dots,3));sampleGeometry.setAttribute('color',new THREE.Float32BufferAttribute(dotColors,3));
    samples=new THREE.Points(sampleGeometry,new THREE.PointsMaterial({size:0.09,vertexColors:true,transparent:true,opacity:0.65,depthWrite:false}));content.add(samples);
    axes();
    lineMaterial=new LineMaterial({color:'#f6fbff',linewidth:3,transparent:true,opacity:0.95,depthTest:false});lineMaterial.resolution.set(canvas.clientWidth,canvas.clientHeight);
    current=new LineSegments2(new LineSegmentsGeometry(),lineMaterial);current.renderOrder=3;content.add(current);
    balls=new THREE.Group();content.add(balls);
    label(COMPONENTS[component],new THREE.Vector3(WIDTH,0,steps>1?DEPTH+1.3:1.3),{color:'#b8d8ec'});
    highlight();if(fit)home();else render();
  }
  function highlight() {
    if(!current||!balls)return;
    balls.traverse(o=>{o.geometry?.dispose();o.material?.dispose();});balls.clear();
    const s=position-prompt+1,validStep=Number.isInteger(s)&&s>=0&&s<steps,segments=[];
    if(validStep)for(let l=0;l<layers;l++){
      const i=s*layers+l;if(values[i]==null)continue;
      const p=point(l,s);
      if(l+1<layers&&values[i+1]!=null)segments.push(...p.toArray(),...point(l+1,s).toArray());
      const ball=new THREE.Mesh(new THREE.SphereGeometry(0.13,8,6),new THREE.MeshBasicMaterial({color:'#fff1bd',depthTest:false}));ball.position.copy(p);ball.userData={layer:l,step:s};ball.renderOrder=4;balls.add(ball);
    }
    current.geometry.dispose();current.geometry=new LineSegmentsGeometry();
    if(segments.length)current.geometry.setPositions(segments);
    current.visible=segments.length>0;render();
  }
  function home() {
    const depth=steps>1?DEPTH:0,center=new THREE.Vector3(WIDTH/2,maxHeight/2,depth/2),direction=new THREE.Vector3(1,0.85,1.2).normalize();
    camera.position.copy(center).addScaledVector(direction,50);camera.lookAt(center);camera.updateMatrixWorld();
    const right=new THREE.Vector3().setFromMatrixColumn(camera.matrixWorld,0),up=new THREE.Vector3().setFromMatrixColumn(camera.matrixWorld,1),tan=Math.tan(THREE.MathUtils.degToRad(camera.fov/2));
    let distance=1;
    for(const px of [-2,WIDTH+1])for(const py of [-1.5,maxHeight+1.5])for(const pz of [-1,depth+2]){
      const offset=new THREE.Vector3(px,py,pz).sub(center),near=offset.dot(direction);
      distance=Math.max(distance,near+Math.abs(offset.dot(right))/(tan*camera.aspect),near+Math.abs(offset.dot(up))/tan);
    }
    distance*=1.13;controls.target.copy(center);camera.position.copy(center).addScaledVector(direction,distance);camera.far=Math.max(2000,distance*10);controls.maxDistance=Math.max(400,distance*5);camera.updateProjectionMatrix();controls.update();render();
  }
  function resize() {
    const w=canvas.clientWidth,h=canvas.clientHeight;if(!w||!h)return;
    renderer.setSize(w,h,false);camera.aspect=w/h;camera.updateProjectionMatrix();lineMaterial?.resolution.set(w,h);if(trace)home();else render();
  }
  canvas.addEventListener('pointerdown',event=>{down=[event.clientX,event.clientY];});
  canvas.addEventListener('pointerup',event=>{
    if(!trace||!down||Math.hypot(event.clientX-down[0],event.clientY-down[1])>5)return;
    const rect=canvas.getBoundingClientRect();mouse.set((event.clientX-rect.left)/rect.width*2-1,1-(event.clientY-rect.top)/rect.height*2);ray.setFromCamera(mouse,camera);
    const hit=ray.intersectObjects([balls,surface,samples].filter(Boolean),true)[0];if(!hit)return;
    let selected;
    if(hit.object.parent===balls)selected=hit.object.userData;
    else if(hit.object===samples)selected=sampleIds[hit.index];
    else if(hit.face){const vertices=surface.geometry.attributes.position;let best=Infinity;for(const i of [hit.face.a,hit.face.b,hit.face.c]){const p=new THREE.Vector3().fromBufferAttribute(vertices,i),distance=p.distanceToSquared(hit.point);if(distance<best){best=distance;selected={layer:i%layers,step:Math.floor(i/layers)};}}}
    if(selected)onSelect?.({layer:selected.layer,component,position:prompt-1+selected.step});
  });
  controls.addEventListener('change',render);new ResizeObserver(resize).observe(canvas);resize();rebuild();
  return {
    setTrace(value,injectionLayer) {
      trace=value;injection=injectionLayer;
      if(trace){prompt=trace.prompt_token_count;steps=trace.observed_position_count-prompt+1;layers=Math.max(...trace.sites.map(s=>s.layer))+1;if(!Number.isInteger(steps)||steps<1||!Number.isInteger(prompt)||prompt<1){trace=null;}position=prompt-1;}
      rebuild();
    },
    setPosition(value){position=value;highlight();},
    setComponent(value){if(!(value in COMPONENTS))throw new Error('Unknown component');component=value;rebuild();},
    setMetric(value){if(!(value in METRICS))throw new Error('Unknown metric');metric=value;rebuild();},
    home,resize,
  };
}
