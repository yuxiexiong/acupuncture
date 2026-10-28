// Read existing, verified trajectories only. No inference requests.
const COMPONENTS = {attention:'Attention / GatedDeltaNet', mlp:'MLP', residual:'层末残差'};
const METRICS = {
  relative_delta:{label:'相对差分 ‖干预−无针‖ / ‖无针‖', cap:10, ticks:'0 · 0.1 · 1 · ≥10', log:true},
  cosine:{label:'方向变化 1 − cosine', cap:2, ticks:'0 · 0.5 · 1 · 2', log:false},
  delta_norm:{label:'差分范数 ‖干预−无针‖', cap:100, ticks:'0 · 1 · 10 · ≥100', log:true},
};
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const num = n => n == null ? '未定义（零范数）' : Number(n).toLocaleString('en', {maximumSignificantDigits:5});
const doseName = n => n === 0 ? '0 · 原版' : (n > 0 ? '+' : '−') + ({0.0625:'1/16',0.125:'1/8',0.25:'1/4',0.5:'1/2',1:'1'}[Math.abs(n)] || Math.abs(n));

export function traceValue(site, position, metric) {
  const value = site[metric]?.[position];
  return value == null ? null : metric === 'cosine' ? Math.max(0, 1 - value) : value;
}
export function traceColor(value, metric) {
  if (value == null) return '#747b88';
  if (value === 0) return '#253d5b';
  const m = METRICS[metric], t = Math.min(1, m.log ? Math.log1p(value) / Math.log1p(m.cap) : value / m.cap);
  const stops = [[58,136,184],[85,207,177],[250,201,91],[239,99,81]], x = t * 3, i = Math.min(2, Math.floor(x));
  return '#' + stops[i].map((v,k) => Math.round(v + (stops[i+1][k] - v) * (x-i)).toString(16).padStart(2,'0')).join('');
}
export function predictionAt(trace, position) {
  const forward = trace.forward_steps.find(s=>s.observed_start+s.observed_count-1===position);
  return forward ? trace.logits.steps[forward.step] : null;
}

export async function createTraceReader({profile, map, api}) {
  const $ = s => document.querySelector(s);
  const data = await api('/api/results/index'), model = data.model;
  const allRecords = data.records.filter(r => r.model === profile || r.model == null);
  let records = allRecords;
  let layers = [...new Set(records.filter(r=>r.layer!=null).map(r=>r.layer))].sort((a,b)=>a-b);
  const points = [...new Map(records.filter(r=>r.layer!=null).map(r=>[`${r.layer}/${r.channel}`,{layer:r.layer,channel:r.channel}])).values()];
  const firstPoint = points.find(p=>p.layer===layers[0] && records.some(r=>r.layer===p.layer && r.channel===p.channel && r.dose===0.5)) || points[0];
  let layer = firstPoint.layer, channel = firstPoint.channel, dose = 0.5, question = 'Q04';
  let detail = null, selected = null, position = 0, metric = 'relative_delta', chosenSite = null, sequence = 0;
  const option = (value,label) => `<option value="${esc(value)}">${esc(label)}</option>`;
  $('#lt-survey').innerHTML = `<div class="survey-list-head">
    <b>${esc(model.label)} · ${model.layers} 层</b><p>${allRecords.length.toLocaleString()} 份归档回答 · ${allRecords.filter(r=>r.has_trace).length.toLocaleString()} 份含内部轨迹</p>
    ${profile==='llama31-8b-instruct' ? '<p>通道按编号排列；未生成权重布局与连接缓存。</p>' : `<p><a href="/?model=${encodeURIComponent(profile)}&view=survey">查看旧十点回答调查 ↗</a></p>`}
    <button id="survey-home">↗ 全景 3D</button>
    <label class="trace-filter">范围<select id="trace-scope" aria-label="结果范围"><option value="all">全部回答</option><option value="trace">含内部轨迹</option></select></label>
    <label class="trace-filter">注入层<select id="trace-layer" aria-label="轨迹注入层">${layers.map(l=>option(l,`L${l}`)).join('')}${option('baseline','0 · 原版对照')}</select></label>
    <label class="trace-filter">注入通道<select id="trace-channel" aria-label="轨迹注入通道"></select></label>
    <label class="trace-filter">剂量<select id="trace-dose" aria-label="轨迹剂量"></select></label>
    <label class="trace-filter">题目<select id="trace-question" aria-label="轨迹题目">${data.questions.map(q=>option(q.id,q.id)).join('')}</select></label>
    <p id="trace-coverage"></p></div><div id="trace-channels"></div>
    <p class="survey-note trace-padding">默认覆盖全部已归档注入层：每层 10 点有 +1，其中 1 点有正负十档剂量。内部轨迹仅覆盖实际采集条件；没有轨迹的回答不会绘制传播颜色。</p>`;
  $('#tab-survey').innerHTML = `<div class="survey-note">已归档实测 · 只读 · 不加载模型</div>
    <p id="survey-prompt"></p><div id="trace-title" class="survey-coordinate"></div>
    <div class="trace-buttons"><button id="trace-home">全景 3D</button><button id="trace-focus">定位注入层</button></div>
    <div id="trace-loading" role="status"></div><div id="trace-detail" hidden>
    <p id="trace-absent" class="trace-absent" hidden>只保存回答，未采集内部轨迹。图中仅标出注入位置，不表示零差分。</p>
    <div id="trace-visuals">
    <label class="trace-filter">颜色指标<select id="trace-metric" aria-label="传播颜色指标">${Object.entries(METRICS).map(([k,m])=>option(k,m.label)).join('')}</select></label>
    <div class="trace-legend"><span class="trace-gradient"></span><span id="trace-scale"></span></div>
    <p class="survey-note">深蓝＝零差分；灰＝零范数时未定义。固定色标，超上限饱和，精确数值见下方。板：Attention / MLP；底部梁：层末残差。</p>
    <label for="trace-position" id="trace-position-label"></label><input id="trace-position" type="range" min="0" step="1" value="0" aria-label="输入token位置">
    <div class="trace-buttons"><button data-pos="prev">←</button><button data-pos="prompt">提示末位</button><button data-pos="last">生成末位</button><button data-pos="next">→</button></div>
    <p id="trace-prediction" class="survey-note"></p>
    <div id="trace-site"></div>
    <p class="survey-note">图中比较的是<strong>相同输入前缀下的干预与无针参照</strong>；颜色表示组件整体差异。层间次序不是已证明的因果路径，也不是单神经元激活图。</p>
    </div><div id="trace-answers" class="survey-compare"></div>
    <p id="trace-baseline-note" class="survey-note">左侧原版为自由生成回答，与图里的同前缀无针参照分开。</p><p id="trace-evidence" class="survey-note"></p></div>`;
  $('#survey-home').onclick = () => { map.exitLayer(); map.home(); };
  $('#trace-home').onclick = () => { map.exitLayer(); map.home(); };
  $('#trace-focus').onclick = () => { if (selected?.layer != null) { map.exitLayer(); map.flyToNeuron(selected.layer,selected.channel,0.3); } };
  $('#trace-metric').onchange = e => { metric = e.target.value; paint(); };
  $('#trace-position').oninput = e => { position = +e.target.value; paint(); };
  $('#trace-detail .trace-buttons').onclick = e => {
    const p = e.target.closest('[data-pos]')?.dataset.pos;
    if (!p || !detail?.trace) return;
    position = p === 'prompt' ? detail.trace.prompt_token_count-1 : p === 'last' ? detail.trace.observed_position_count-1 : position + (p === 'next' ? 1 : -1);
    position = Math.max(0,Math.min(detail.trace.observed_position_count-1,position)); paint();
  };
  $('#trace-scope').onchange = e => {
    records = e.target.value === 'trace' ? allRecords.filter(r=>r.has_trace) : allRecords;
    layers = [...new Set(records.filter(r=>r.layer!=null).map(r=>r.layer))].sort((a,b)=>a-b);
    $('#trace-layer').innerHTML = layers.map(l=>option(l,`L${l}`)).join('') + option('baseline','0 · 原版对照');
    if (layer != null && !layers.includes(layer)) layer = layers[0];
    selected = null; choose();
  };
  $('#trace-layer').onchange = e => { layer = e.target.value === 'baseline' ? null : +e.target.value; choose(); };
  $('#trace-channel').onchange = e => { channel = +e.target.value; choose(); };
  $('#trace-dose').onchange = e => { dose = +e.target.value; choose(); };
  $('#trace-question').onchange = e => { question = e.target.value; choose(); };
  $('#trace-channels').onclick = e => { const b=e.target.closest('[data-channel]'); if (b) { channel=+b.dataset.channel; choose(); } };

  function controls() {
    const channels = [...new Set(records.filter(r=>r.layer===layer && r.channel!=null).map(r=>r.channel))].sort((a,b)=>a-b);
    if (layer == null) channel = null;
    else if (!channels.includes(channel)) channel = channels.find(c=>records.some(r=>r.layer===layer&&r.channel===c&&r.dose===dose)) ?? channels[0];
    const doses = [...new Set(records.filter(r=>r.layer===layer && r.channel===channel).map(r=>r.dose))].sort((a,b)=>a-b);
    if (!doses.includes(dose)) dose = doses.includes(0.5) ? 0.5 : doses.includes(1) ? 1 : doses[0];
    $('#trace-layer').value = layer == null ? 'baseline' : layer;
    $('#trace-channel').innerHTML = channels.map(c=>option(c,`N${c}`)).join(''); $('#trace-channel').value = channel;
    $('#trace-channel').disabled = layer == null;
    $('#trace-dose').innerHTML = doses.map(d=>option(d,doseName(d))).join(''); $('#trace-dose').value = dose;
    $('#trace-question').value = question;
    $('#trace-coverage').textContent = layer == null ? '共享原版对照，差分应为零。' : `L${layer} · ${channels.length} 个已测通道 · 此点 ${doses.length} 档剂量`;
    $('#trace-channels').innerHTML = channels.map(c=>`<button data-channel="${c}" class="${c===channel?'on':''}">N${c}</button>`).join('');
  }
  async function choose() {
    controls();
    const row = records.find(r=>r.layer===layer && r.channel===channel && r.dose===dose && r.question_id===question);
    if (!row) { ++sequence; selected=null; detail=null; chosenSite=null; map.setTraceOverlay([]); $('#trace-detail').hidden=true; $('#trace-loading').textContent='当前范围没有该条件的归档结果。'; return; }
    if (selected?.trace_id === row.trace_id) return;
    selected = row; const request = ++sequence;
    detail = null; $('#trace-detail').hidden=true; $('#trace-loading').textContent='读取本地结果…'; $('#trace-site').innerHTML=''; $('#trace-prediction').textContent='';
    map.setTraceOverlay([]); map.setConnections({up:[],down:[]}); map.setHoverConnections(null); map.setWeb(null);
    $('#trace-title').textContent = row.layer == null ? `${question} · 原版对照` : `L${row.layer} N${row.channel} · ${doseName(dose)} · ${question}`;
    $('#trace-focus').disabled = row.layer == null;
    $('#f-id').textContent = row.layer == null ? '原版对照' : `L${row.layer} N${row.channel}`;
    $('#layer').value = row.layer ?? 0;
    map.exitLayer();
    map.setSurveyMarks(row.layer == null ? [] : [{layer:row.layer,n:row.channel,color:'#ffd27a',five:true}]);
    map.select(row.layer,row.channel,false);
    try {
      const result = await api(`/api/results/detail?id=${encodeURIComponent(row.trace_id)}`);
      if (request !== sequence) return;
      detail = result; position = detail.trace ? detail.trace.prompt_token_count-1 : 0;
      chosenSite = detail.trace ? {layer:row.layer ?? 0, component:'mlp'} : null;
      $('#trace-visuals').hidden = !detail.trace; $('#trace-absent').hidden = !!detail.trace;
      $('#trace-baseline-note').textContent = detail.trace ? '左侧原版为自由生成回答，与图里的同前缀无针参照分开。' : '左侧为同题原版自由生成回答；该条件没有内部轨迹，不能读取逐层或逐 token 差分。';
      $('#survey-prompt').textContent = detail.prompt;
      $('#trace-loading').textContent=''; $('#trace-detail').hidden=false;
      if (detail.trace) $('#trace-position').max = detail.trace.observed_position_count-1;
      $('#trace-answers').innerHTML = card('原版 · 自由生成',detail.baseline) + card('干预后 · 自由生成',detail.intervened);
      $('#trace-evidence').innerHTML = `<a href="${esc(detail.sources.record)}" target="_blank" rel="noopener">采集记录 ↗</a>${detail.sources.trace ? ` · <a href="${esc(detail.sources.trace)}" target="_blank" rel="noopener">原始轨迹 JSON.gz ↗</a>` : ''}`;
      paint();
    } catch (error) { if (request===sequence) { selected=null; $('#trace-loading').textContent=`结果读取失败：${error.message}`; } }
  }
  function card(title,r) {
    if (!r) return `<article class="survey-answer"><h4>${esc(title)}</h4>缺少来源</article>`;
    return `<article class="survey-answer"><h4>${esc(title)}</h4><div class="survey-meta">${r.token_ids?.length ?? 0} tokens · ${esc(r.stop_reason)}</div>
      <pre>${r.answer_text?.trim() ? esc(r.answer_text) : '（正文为空，见 raw_text）'}</pre>
      <details><summary>raw_text</summary><pre>${esc(JSON.stringify(r.raw_text))}</pre></details>
      <a href="${esc(r.source)}" target="_blank" rel="noopener">原始回答 ↗</a></article>`;
  }
  function paint() {
    if (!detail?.trace) return;
    const trace = detail.trace, metricInfo = METRICS[metric], prompt = trace.prompt_token_count;
    $('#trace-position').value = position;
    $('#trace-scale').textContent = `${metricInfo.ticks} · ${metric === 'cosine' ? '线性' : 'log(1+x) 颜色映射'}`;
    $('#trace-position-label').textContent = `${position < prompt ? `提示输入 ${position+1}/${prompt}` : `生成输入 ${position-prompt+1}/${trace.observed_position_count-prompt}`} · 位置 ${position} · token ID ${trace.observed_input_token_ids[position]}`;
    const logits = predictionAt(trace,position);
    if (logits) {
      const token = logits.candidates.find(c=>c.token_id===logits.generated_token_id);
      $('#trace-prediction').textContent = `预测输出第 ${logits.step+1} token：${JSON.stringify(token?.token_text ?? logits.generated_token_id)}。停止优势（原版同前缀 → 干预）：${num(logits.clean_stop_advantage)} → ${num(logits.steer_stop_advantage)}；正值偏向停止。`;
    } else $('#trace-prediction').textContent = '此处为提示内部位置，仅有组件读数；本次采集没有该位置的输出 logits。';
    map.setTraceOverlay(trace.sites.map(site=>{
      const value=traceValue(site,position,metric);
      return {layer:site.layer,component:site.component,value,color:traceColor(value,metric),selected:chosenSite?.layer===site.layer&&chosenSite?.component===site.component,label:`${site.module_type} · ${metricInfo.label} = ${num(value)}`};
    }));
    const site = trace.sites.find(s=>s.layer===chosenSite?.layer && s.component===chosenSite?.component);
    $('#trace-site').innerHTML = site ? `<b>L${site.layer} · ${esc(COMPONENTS[site.component])} <small>${esc(site.module_type)}</small></b>
      <div class="trace-readouts"><span>无针范数<b>${num(site.clean_norm[position])}</b></span><span>干预范数<b>${num(site.steer_norm[position])}</b></span><span>差分范数<b>${num(site.delta_norm[position])}</b></span><span>相对差分<b>${num(site.relative_delta[position])}</b></span><span>cosine<b>${num(site.cosine[position])}</b></span></div><p class="survey-note">点选三维板 / 底部残差梁，查看对应层的读数。</p>` : '';
  }
  await choose();
  return {
    defaultPoint:{layer:firstPoint.layer,n:firstPoint.channel},
    hasPoint(l,n) { return records.some(p=>p.layer===l&&p.channel===n); },
    select(l,n) { if (!records.some(p=>p.layer===l&&p.channel===n)) return; layer=l;channel=n;choose(); },
    selectSite(l,component) { chosenSite={layer:l,component};paint(); },
    debug() { return {trace_id:selected?.trace_id, model:profile, layer,channel,dose,question,position,metric,chosenSite,loaded:!!detail,has_trace:!!detail?.trace,scope:$('#trace-scope').value,records:records.length,sites:detail?.trace?.sites.length}; },
  };
}
