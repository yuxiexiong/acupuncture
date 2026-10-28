import {DOSES, doseRows, predictionColumns, actualGap, candidateValues} from './analysis-data.js';
import {traceColor, traceValue} from './trace.js';

const $ = s => document.querySelector(s);
const esc = s => String(s ?? '').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fmt = n => n == null ? '未定义 / 未采集' : Number(n).toLocaleString('en',{maximumSignificantDigits:6});
const doseText = d => d === 0 ? '0 · 原版' : (d > 0 ? '+' : '−') + Math.abs(d);
const option = (v,t) => `<option value="${esc(v)}">${esc(t)}</option>`;
const components = {attention:'Attention / GatedDeltaNet', mlp:'MLP', residual:'层末残差'};
const scales = {relative_delta:'相对差分 · log(1+x) 色标 0 → 10', cosine:'方向变化 1 − cosine · 线性色标 0 → 2', delta_norm:'差分范数 · log(1+x) 色标 0 → 100', clean_norm:'无针范数 · log(1+x) 色标 0 → 100'};
const initial = new URLSearchParams(location.search);
let model = initial.get('model') || '4b', layer = +(initial.get('layer') || 0), channel = initial.has('channel') ? +initial.get('channel') : null;
let question = initial.get('question') || 'Q04', dose = initial.has('dose') ? +initial.get('dose') : 1;
let index, rows = [], sources = [], detail = null, columns = [], step = 0, siteLayer = 0, siteComponent = 'mlp', candidateId = null;
let pointRequest = 0, traceRequest = 0, modelRequest = 0;
async function get(path, params={}) {
  const response = await fetch(path+'?'+new URLSearchParams({model,...params}));
  if (!response.ok) throw new Error(`本地归档读取失败 (${response.status})`);
  return response.json();
}
function error(e) { $('#status').textContent = e.message; }
function link(path, params={}) { return path+'?'+new URLSearchParams({model,...params}); }
function updateURL() {
  const query = new URLSearchParams({model,layer,channel,question,dose});
  history.replaceState(null,'','/analysis.html?'+query);
  $('#back-3d').href = '/?'+query;
}
function clearTrace() {
  detail=null; columns=[]; $('#trace-panel').hidden=true;
  for (const id of ['heatmaps','curves','candidate-curve','tokens','site-readout','token-readout','evidence']) $('#'+id).replaceChildren();
}
async function loadModel() {
  const request=++modelRequest; ++pointRequest; ++traceRequest; clearTrace();
  $('#dose-cards').replaceChildren(); $('#dose-overview').replaceChildren(); $('#status').textContent='读取模型的本地归档索引…';
  $('#controls').querySelectorAll('select').forEach(el=>el.disabled=true);
  try {
    const value=await get('/api/results/index'); if(request!==modelRequest)return;
    index=value; $('#model').innerHTML=index.models.map(m=>option(m.id,m.label)).join(''); $('#model').value=model;
    const layers=[...new Set(index.records.filter(r=>r.layer!=null).map(r=>r.layer))].sort((a,b)=>a-b);
    if(!layers.includes(layer))layer=layers[0];
    $('#layer').innerHTML=layers.map(l=>option(l,`L${l}`)).join(''); $('#layer').value=layer;
    $('#question').innerHTML=index.questions.map(q=>option(q.id,q.id)).join('');
    if(!index.questions.some(q=>q.id===question))question='Q04'; $('#question').value=question;
    $('#controls').querySelectorAll('select').forEach(el=>el.disabled=false);
    await loadPoint();
  } catch(e){error(e);$('#model').disabled=false;}
}
async function loadPoint() {
  const request=++pointRequest; ++traceRequest; clearTrace();
  const channels=[...new Set(index.records.filter(r=>r.layer===layer).map(r=>r.channel))].sort((a,b)=>a-b);
  if(!channels.includes(channel))channel=channels.find(c=>index.records.some(r=>r.layer===layer&&r.channel===c&&r.dose===.5))??channels[0];
  $('#channel').innerHTML=channels.map(c=>option(c,`N${c}${index.records.some(r=>r.layer===layer&&r.channel===c&&r.dose===.5)?' · 正负剂量点':''}`)).join('');
  $('#channel').value=channel;
  rows=doseRows(index.records,layer,channel,question);
  if(!rows[DOSES.indexOf(dose)])dose=1;
  $('#prompt').textContent=index.questions.find(q=>q.id===question).prompt;
  $('#dose-cards').replaceChildren(); $('#dose-overview').replaceChildren();
  $('#status').textContent='读取同一点的剂量原文…'; $('#trace-status').textContent=''; updateURL();
  try {
    const result=await Promise.all(rows.map(r=>r?get('/api/results/source',{id:r.trace_id,arm:'intervened'}):null));
    if(request!==pointRequest)return;
    sources=result; renderDoses(); $('#status').textContent=`${index.model.label} · ${index.records.length.toLocaleString()} 份唯一回答 / ${index.records.filter(r=>r.has_trace).length.toLocaleString()} 份内部轨迹 · 本点已测 ${rows.filter(Boolean).length-1} 个干预剂量 + 共享原版`;
    await selectDose(dose);
  } catch(e){if(request===pointRequest)error(e);}
}
function renderDoses() {
  $('#dose-overview').innerHTML=DOSES.map((d,i)=>`<button data-dose="${d}" ${rows[i]?'':'disabled'} class="${d===dose?'selected':''}" aria-pressed="${d===dose}"><strong>${doseText(d)}</strong><span>${rows[i]?rows[i].tokens+' tokens':'未测'}</span><i style="width:${rows[i]?Math.max(1,rows[i].tokens/128*100):0}%"></i></button>`).join('');
  $('#dose-cards').innerHTML=DOSES.map((d,i)=>{
    const r=rows[i],source=sources[i],o=source?.output;
    if(!r)return `<article class="dose-card missing"><h3>${doseText(d)}</h3><p>该通道未测此剂量</p><p class="meta">没有回答或轨迹，不补成零。</p></article>`;
    const url=link('/api/results/source',{id:r.trace_id,arm:'intervened'});
    return `<article class="dose-card ${d===dose?'selected':''}" data-card-dose="${d}"><button class="dose-pick" data-dose="${d}" aria-pressed="${d===dose}">${doseText(d)} · 查看轨迹</button>
      <div class="meta">${r.tokens} tokens · ${esc(o.end_reason)}<br>${r.has_trace?'有内部轨迹':'内部轨迹未采集'}${d===0?' · 同题共享原版':''}</div>
      <pre class="answer">${o.answer_text?.trim()?esc(o.answer_text):'（正文为空；完整 raw_text 见下方）'}</pre>
      <details><summary>完整 raw_text 与 token IDs</summary><pre>${esc(JSON.stringify(o.raw_text))}</pre><pre>${esc(JSON.stringify(o.token_ids))}</pre></details>
      <a href="${url}" target="_blank" rel="noopener">原始回答 ↗</a></article>`;
  }).join('');
}
async function selectDose(value) {
  dose=value; step=0; siteLayer=layer; siteComponent='mlp'; const request=++traceRequest;
  clearTrace(); updateURL();
  document.querySelectorAll('[data-dose]').forEach(el=>{const active=+el.dataset.dose===dose;el.classList.toggle('selected',active);el.setAttribute('aria-pressed',String(active));});
  document.querySelectorAll('[data-card-dose]').forEach(el=>el.classList.toggle('selected',+el.dataset.cardDose===dose));
  const card=document.querySelector(`[data-card-dose="${dose}"]`),strip=$('#dose-cards');
  if(card)strip.scrollLeft=card.offsetLeft-strip.offsetLeft-(strip.clientWidth-card.clientWidth)/2;
  const row=rows[DOSES.indexOf(dose)];
  $('#selection').textContent=`${index.model.label} · L${layer} / N${channel} · ${question} · ${doseText(dose)}${dose===0?'（共享基线，未注入）':''}`;
  $('#trace-status').textContent='正在读取选中条件的内部轨迹…';
  try {
    const result=await get('/api/results/detail',{id:row.trace_id}); if(request!==traceRequest)return;
    detail=result;
    $('#evidence').innerHTML=`<a href="${esc(detail.sources.record)}" target="_blank" rel="noopener">原始记录 ↗</a>${detail.sources.trace?` · <a href="${esc(detail.sources.trace)}" target="_blank" rel="noopener">完整轨迹 JSON.gz ↗</a>`:''}`;
    if(!detail.trace){$('#trace-status').textContent='此条件有原文，但未采集内部轨迹。热图与曲线留空，不表示零变化。';return;}
    columns=predictionColumns(detail.trace); candidateId=columns[0].logits.generated_token_id;
    $('#trace-status').textContent=`${columns.length} 个实际预测步 · ${index.model.layers} 层 × 3 组件。步 0 为提示末位；图的终点是最后一个实际预测，没有补画后续。`;
    $('#trace-panel').hidden=false; $('#step').max=columns.length-1;
    $('#tokens').innerHTML=columns.map(({step:s,logits})=>`<button class="token" data-step="${s}" title="预测步 ${s} · token ID ${logits.generated_token_id}"><small>${s}</small> ${esc(JSON.stringify(logits.candidates.find(c=>c.token_id===logits.generated_token_id)?.token_text))}</button>`).join('');
    const candidates=new Map(columns.flatMap(c=>c.logits.candidates).map(c=>[c.token_id,c.token_text]));
    $('#candidate').innerHTML=[...candidates].map(([id,t])=>option(id,`${JSON.stringify(t)} · ID ${id}`)).join(''); $('#candidate').value=candidateId;
    setStep(0);
  }catch(e){if(request===traceRequest){clearTrace();$('#trace-status').textContent=e.message;}}
}
function setStep(value) {
  if(!columns.length)return;
  step=Math.max(0,Math.min(columns.length-1,value));
  $('#step').value=step;
  const c=columns[step];
  $('#step-label').textContent=`预测步 ${c.step} / ${columns.length-1} → 第 ${c.step+1} 个输出 token · ${c.step===0?'提示末位':'已读入前 '+c.step+' 个输出 token'} · 观测输入位置 ${c.position}`;
  $('#prev-step').disabled=step===0;$('#next-step').disabled=step===columns.length-1;
  $('#tokens').querySelectorAll('button').forEach(el=>{const active=+el.dataset.step===step;el.classList.toggle('selected',active);el.setAttribute('aria-pressed',String(active));});
  const token=$('#tokens').querySelector('.selected');if(token)$('#tokens').scrollLeft=token.offsetLeft-$('#tokens').offsetLeft-100;
  drawHeatmaps(); drawCurves(); showToken();
}
function drawHeatmaps() {
  if(!detail?.trace)return;
  const metric=$('#metric').value;
  $('#scale-note').innerHTML=esc(scales[metric])+'；超上限饱和。深蓝 = 0，灰 = 未定义。点击格子查看精确数值。<span class="heat-legend" aria-label="颜色从低值蓝色到高值红色"></span>';
  $('#heatmaps').innerHTML=Object.entries(components).map(([c,label])=>`<div class="heatmap"><h3>${label}</h3><canvas data-component="${c}" aria-label="${label}：层与预测步热图" role="img"></canvas><p class="meta">横轴：预测步 · 纵轴：观察层（L0 在上）</p></div>`).join('');
  const count=columns.length,nLayers=index.model.layers;
  for(const canvas of $('#heatmaps').querySelectorAll('canvas')){
    const component=canvas.dataset.component,sites=new Map(detail.trace.sites.filter(s=>s.component===component).map(s=>[s.layer,s]));
    const width=Math.max(250,canvas.parentElement.clientWidth-24),height=32+nLayers*12+32,left=34,top=22,pw=width-left-8,ph=nLayers*12;
    const ratio=devicePixelRatio||1;canvas.width=width*ratio;canvas.height=height*ratio;canvas.style.width='100%';canvas.style.height=height+'px';
    const ctx=canvas.getContext('2d');ctx.scale(ratio,ratio);ctx.font='10px ui-monospace,monospace';
    const cw=pw/count;
    for(let l=0;l<nLayers;l++)for(let s=0;s<count;s++){
      const site=sites.get(l),pos=columns[s].position;
      const value=site?(metric==='clean_norm'?site.clean_norm[pos]:traceValue(site,pos,metric)):null;
      ctx.fillStyle=traceColor(value,metric==='clean_norm'?'delta_norm':metric);ctx.fillRect(left+s*cw,top+l*12,cw+.3,11.5);
    }
    ctx.fillStyle='#b6c8dc';
    for(let l=0;l<nLayers;l++)if(l%4===0||l===nLayers-1||l===layer){ctx.fillStyle=l===layer&&dose!==0?'#ffce80':'#b6c8dc';ctx.fillText('L'+l,3,top+l*12+9);}
    const ticks=[...new Set([0,Math.floor((count-1)/2),count-1])];ctx.fillStyle='#b6c8dc';ctx.textAlign='center';
    ticks.forEach(s=>ctx.fillText(s,left+(s+.5)*cw,top+ph+16));ctx.textAlign='start';
    ctx.strokeStyle='#fff3c6';ctx.lineWidth=1.5;ctx.strokeRect(left+step*cw+.7,top+.7,Math.max(1,cw-1.4),ph-1.4);
    if(dose!==0){ctx.strokeStyle='#ffce80';ctx.strokeRect(left,top+layer*12,pw,12);}
    canvas.onclick=event=>{
      const rect=canvas.getBoundingClientRect(),x=(event.clientX-rect.left)*width/rect.width,y=(event.clientY-rect.top)*height/rect.height;
      if(x<left||x>=left+pw||y<top||y>=top+ph)return;
      siteLayer=Math.floor((y-top)/12);siteComponent=component;setStep(Math.floor((x-left)/cw));
    };
  }
  const site=detail.trace.sites.find(s=>s.layer===siteLayer&&s.component===siteComponent),pos=columns[step].position;
  $('#site-readout').innerHTML=site?`<strong>L${siteLayer} · ${esc(components[siteComponent])} · ${esc(site.module_type)} · 步 ${step}</strong><div class="readouts">${[['无针范数','clean_norm'],['干预范数','steer_norm'],['差分范数','delta_norm'],['相对差分','relative_delta'],['cosine','cosine']].map(([label,key])=>`<span>${label}<b>${fmt(site[key][pos])}</b></span>`).join('')}</div>`:'';
}
// All curves use actual saved prediction steps. Nulls break paths; never interpolate missing candidates.
function chart(title, series, note) {
  const width=620,height=215,left=62,right=15,top=20,bottom=35,pw=width-left-right,ph=height-top-bottom,n=columns.length;
  const values=series.flatMap(s=>s.values.filter(v=>v!=null&&Number.isFinite(v)));
  let lo=Math.min(0,...values),hi=Math.max(0,...values);if(lo===hi){lo-=1;hi+=1;}else{const pad=(hi-lo)*.08;lo-=pad;hi+=pad;}
  const x=i=>left+(n===1?.5:i/(n-1))*pw,y=v=>top+(hi-v)/(hi-lo)*ph;
  let svg=`<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="${esc(title)}">`;
  for(let t=0;t<4;t++){const v=lo+(hi-lo)*t/3;svg+=`<line x1="${left}" x2="${width-right}" y1="${y(v)}" y2="${y(v)}" stroke="#293d53"/><text x="${left-7}" y="${y(v)+4}" text-anchor="end">${Number(v.toPrecision(3))}</text>`;}
  svg+=`<line x1="${left}" x2="${width-right}" y1="${y(0)}" y2="${y(0)}" stroke="#8194aa" stroke-dasharray="3 3"/>`;
  for(const s of series){let path='',pen=false;s.values.forEach((v,i)=>{if(v==null||!Number.isFinite(v)){pen=false;return;}path+=(pen?'L':'M')+x(i)+','+y(v);pen=true;});svg+=`<path d="${path}" fill="none" stroke="${s.color}" stroke-width="2"/>`;
    s.values.forEach((v,i)=>{if(v!=null&&Number.isFinite(v))svg+=`<circle cx="${x(i)}" cy="${y(v)}" r="${n<3?4:2}" fill="${s.color}"><title>步 ${i} · ${esc(s.label)}：${fmt(v)}</title></circle>`;});}
  svg+=`<line x1="${x(step)}" x2="${x(step)}" y1="${top}" y2="${height-bottom}" stroke="#fff3c6" stroke-dasharray="4 3"/>`;
  [...new Set([0,Math.floor((n-1)/2),n-1])].forEach(i=>{svg+=`<text x="${x(i)}" y="${height-13}" text-anchor="middle">${i}</text>`;});
  svg+=`<text x="${width/2}" y="${height-1}" text-anchor="middle">预测步</text></svg>`;
  return `<div class="curve"><h3>${esc(title)}</h3><p class="curve-legend">${series.map(s=>`<span style="color:${s.color}">● ${esc(s.label)}</span>`).join('')}</p>${svg}<p class="meta">${esc(note)}</p></div>`;
}
function bindCharts(container) {
  container.querySelectorAll('svg').forEach(svg=>svg.onclick=event=>{
    const point=svg.createSVGPoint();point.x=event.clientX;point.y=event.clientY;
    const p=point.matrixTransform(svg.getScreenCTM().inverse());setStep(columns.length===1?0:Math.round((p.x-62)/(620-62-15)*(columns.length-1)));
  });
}
function drawCurves() {
  const clean='#72d6df',steer='#ffbc76';
  $('#curves').innerHTML=chart('停止优势：是否更偏向 EOS',[
    {label:'无针参照 · 同前缀',color:clean,values:columns.map(c=>c.logits.clean_stop_advantage)},
    {label:'干预分支',color:steer,values:columns.map(c=>c.logits.steer_stop_advantage)}],
    '最佳停止 token logit − 最佳非停止 token logit。正值偏向停止，0 为并列；并列时实际选择看 token。')+
    chart('实际输出 token 距无针最佳的差值',[
      {label:'实际 token 的无针 logit − 无针最大 logit',color:'#bdabff',values:columns.map(c=>actualGap(c.logits))}],
      '0 表示该 token 也是无针最高候选（含并列）；负值表示无针更偏好其他 token。这不是语义正确率。');
  bindCharts($('#curves'));drawCandidate();
}
function drawCandidate() {
  if(!columns.length)return;
  candidateId=+$('#candidate').value;
  const observed=columns.filter(c=>c.logits.candidates.some(t=>t.token_id===candidateId)).length;
  $('#candidate-curve').innerHTML=chart('固定候选 token 的竞争轨迹',[
    {label:'无针参照 log probability',color:'#72d6df',values:candidateValues(columns,candidateId,'clean')},
    {label:'干预分支 log probability',color:'#ffbc76',values:candidateValues(columns,candidateId,'steer')}],
    `此 token 有 ${observed}/${columns.length} 步已保存分数。未进入当步候选并集的位置断线；不是概率为 0。纵轴按当前轨迹缩放。`);
  bindCharts($('#candidate-curve'));
}
function showToken() {
  const s=columns[step].logits,actual=s.candidates.find(c=>c.token_id===s.generated_token_id),best=s.candidates.find(c=>c.token_id===s.clean_top_token_ids[0]);
  const ordered=[...s.candidates].sort((a,b)=>b.steer_logit-a.steer_logit);
  $('#token-readout').innerHTML=`<p><strong>步 ${step} 实际输出 ${esc(JSON.stringify(actual.token_text))} · ID ${actual.token_id}${actual.is_eos?' · EOS':''}</strong><br>无针最高候选之一：${esc(JSON.stringify(best.token_text))} · 实际 token 的无针差值 ${fmt(actualGap(s))}。<br>本步停止优势（无针参照 → 干预）：${fmt(s.clean_stop_advantage)} → ${fmt(s.steer_stop_advantage)}。<br>孤立 token 的乱码字符可能来自字节片段，请同时看完整原文。</p>
    <details><summary>本步所有已保存候选及精确分数（${ordered.length} 个）</summary><div class="table-scroll"><table><thead><tr><th>token / ID</th><th>无针 logit</th><th>干预 logit</th><th>无针 log probability</th><th>干预 log probability</th></tr></thead><tbody>${ordered.map(c=>`<tr class="${c.token_id===actual.token_id?'actual':''}"><td>${esc(JSON.stringify(c.token_text))} / ${c.token_id}${c.is_eos?' · EOS':''}${c.token_id===actual.token_id?' · 实际':''}</td><td>${fmt(c.clean_logit)}</td><td>${fmt(c.steer_logit)}</td><td>${fmt(c.clean_logprob)}</td><td>${fmt(c.steer_logprob)}</td></tr>`).join('')}</tbody></table></div></details>`;
}
$('#model').onchange=e=>{model=e.target.value;channel=null;loadModel();};
$('#layer').onchange=e=>{layer=+e.target.value;channel=null;loadPoint();};
$('#channel').onchange=e=>{channel=+e.target.value;loadPoint();};
$('#question').onchange=e=>{question=e.target.value;loadPoint();};
for(const id of ['dose-overview','dose-cards'])$('#'+id).onclick=e=>{const b=e.target.closest('[data-dose]');if(b&&!b.disabled)selectDose(+b.dataset.dose);};
$('#metric').onchange=drawHeatmaps;$('#step').oninput=e=>setStep(+e.target.value);
$('#prev-step').onclick=()=>setStep(step-1);$('#next-step').onclick=()=>setStep(step+1);
$('#tokens').onclick=e=>{const b=e.target.closest('[data-step]');if(b)setStep(+b.dataset.step);};
$('#candidate').onchange=drawCandidate;
let resizeTimer;addEventListener('resize',()=>{clearTimeout(resizeTimer);resizeTimer=setTimeout(drawHeatmaps,100);});
loadModel();
