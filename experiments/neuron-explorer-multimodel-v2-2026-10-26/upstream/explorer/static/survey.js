// Existing measurements on the upstream 3D coordinates; no inference or semantic scoring.
export async function createSurvey({ profile, map, pick }) {
  const $ = s => document.querySelector(s);
  const esc = s => String(s ?? '').replace(/[&<>\"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
  const response = await fetch('/api/survey');
  if (!response.ok) throw new Error(`survey ${response.status}`);
  const data = await response.json(), model = data.models.find(m => m.id === profile);
  if (!model) throw new Error(`No survey for ${profile}`);
  const points = new Map(model.points.map(p => [`${p.layer}/${p.channel}`, p]));
  const doses = ['0.0625', '0.125', '0.25', '0.5', '1'];
  const names = {'0':'0 原版','0.0625':'+1/16','0.125':'+1/8','0.25':'+1/4','0.5':'+1/2','1':'+1'};
  let question = 'Q04', dose = '0.5', focus = null;
  const status = r => !r ? 'missing' : !r.text?.trim() ? 'empty' : r.stop_reason === 'length_limit' ? 'limit' : 'eos';
  const colors = {missing:'#777777',empty:'#eb839e',limit:'#87aaff',eos:'#6bd5c2'};
  const statusName = r => !r ? '缺测' : !r.text?.trim() ? '空正文' : r.stop_reason === 'length_limit' ? '有正文 · 128 上限' : '有正文 · EOS 结束';
  const five = p => doses.every(d => p?.doses[d]);
  $('#lt-survey').innerHTML = `
    <div class="survey-list-head"><b>${esc(profile.toUpperCase())} · ${model.layers} 层 · ${model.points.length} 实测点</b>
    <p>每层 10 个通道。点选后看原版与干预回答；拖动旋转，滚轮缩放。</p>
    <button id="survey-home">↗ 全景 3D</button></div><div id="survey-points"></div>`;
  $('#tab-survey').innerHTML = `
    <div class="survey-note">已有结果 · 不加载模型 · 固定 8 题</div>
    <label class="survey-question">题目 <select id="survey-question" aria-label="实验题目"></select></label>
    <p id="survey-prompt"></p><div id="survey-selection"></div>
    <div class="survey-legend"><i style="background:#6bd5c2"></i>有正文 EOS
    <i style="background:#87aaff"></i>有正文 128 上限
    <i style="background:#eb839e"></i>空正文 <i style="background:#777777"></i>缺测 <span class="survey-gold">◎ 五档点</span></div>
    <p class="survey-note">图色显示本题 <span id="survey-map-dose"></span> 的实测输出形态；灰色为该剂量缺测，不代表能力好坏或功能分区。平面内位置沿用原工具布局；连线是原工具的连接信息，不是本实验测得的激活传播。</p>`;
  $('#survey-question').innerHTML = data.questions.map(q => `<option value="${esc(q.id)}">${esc(q.id)} · ${esc(q.label)}</option>`).join('');
  $('#survey-question').value = question;
  $('#survey-question').onchange = e => { question = e.target.value; paint(); render(); };
  $('#survey-home').onclick = () => { map.exitLayer(); map.home(); };
  function paint() {
    $('#survey-map-dose').textContent = names[dose];
    map.setSurveyMarks(model.points.map(p => ({layer:p.layer,n:p.channel,color:colors[status(p.doses[dose]?.[question])],five:five(p)})));
    let html = '';
    for (let layer = 0; layer < model.layers; layer++) {
      html += `<section class="survey-layer"><h4>L${String(layer).padStart(2,'0')}</h4><div>`;
      for (const p of model.points.filter(p => p.layer === layer).sort((a,b) => a.channel-b.channel)) {
        html += `<button data-l="${layer}" data-n="${p.channel}" class="${five(p)?'five':''}" style="--point:${colors[status(p.doses[dose]?.[question])]}" title="${esc(statusName(p.doses[dose]?.[question]))}${five(p)?' · 五档实测':' · 仅 +1 实测'}">N${p.channel}${five(p)?' ◎':''}</button>`;
      }
      html += '</div></section>';
    }
    $('#survey-points').innerHTML = html;
  }
  $('#survey-points').onclick = e => {
    const b = e.target.closest('button[data-l]');
    if (b) pick(+b.dataset.l,+b.dataset.n);
  };
  function card(title, r) {
    if (!r) return `<article class="survey-answer"><h4>${esc(title)}</h4><p class="survey-note">该通道 / 题目 / 剂量没有记录。</p></article>`;
    return `<article class="survey-answer"><h4>${esc(title)}</h4>
      <div class="survey-meta">${esc(statusName(r))} · ${r.tokens} tokens<br>${esc(r.stop_reason)}</div>
      <pre>${r.text?.trim() ? esc(r.text) : '（原始 answer_text 为空；请展开 raw_text 查看特殊 token。）'}</pre>
      <details><summary>raw_text</summary><pre>${esc(JSON.stringify(r.raw_text))}</pre></details>
      <a href="/evidence/${esc(r.source)}" target="_blank" rel="noopener">原始记录 ↗</a></article>`;
  }
  function render() {
    $('#survey-prompt').textContent = data.questions.find(q => q.id === question)?.prompt ?? '';
    $('#survey-points').querySelectorAll('button').forEach(b => b.classList.toggle('selected',!!focus && +b.dataset.l===focus.layer && +b.dataset.n===focus.n));
    if (!focus) { $('#survey-selection').textContent = '在 3D 脑图或左侧列表点选通道。'; return; }
    const p = points.get(`${focus.layer}/${focus.n}`), available = p ? doses.filter(d => p.doses[d]) : [];
    if (available.length && !available.includes(dose)) { dose = available.includes('0.5') ? '0.5' : '1'; paint(); }
    $('#survey-map-dose').textContent = names[dose];
    $('#survey-selection').innerHTML = `
      <div class="survey-coordinate"><b>L${focus.layer} N${focus.n}</b><span>
      <button data-survey-view="home">全景 3D</button>
      <button data-survey-view="point">定位此点</button></span></div>
      <div class="survey-coordinate"><span>
      <button data-layer-step="-1" ${focus.layer===0?'disabled':''}>↑ 上一层</button>
      <button data-layer-step="1" ${focus.layer===model.layers-1?'disabled':''}>↓ 下一层</button></span></div>
      <div class="survey-dose">${available.map(d => `<button data-dose="${d}" class="${dose===d?'on':''}">${names[d]}</button>`).join('')}</div>
      <p class="survey-note">${!p?'该通道未进入此次每层 10 点调查；没有干预回答。':five(p)?'该点有五档实测。切换剂量，观察回答如何变化。':'该点只有 +1 实测；中间四档没有运行。'}</p>
      <div class="survey-compare">${card('0 · 原版', model.baseline[question])}${card(`${names[dose]} · 干预`,p?.doses[dose]?.[question])}</div>
      ${five(p)?`<details class="survey-all"><summary>展开原版 + 五档全部回答</summary><div class="survey-all-grid">${card('0 · 原版',model.baseline[question])}${doses.map(d => card(names[d],p.doses[d]?.[question])).join('')}</div></details>`:''}`;
  }
  $('#survey-selection').onclick = e => {
    const view = e.target.closest('button[data-survey-view]');
    if (view && focus) { map.exitLayer(); if (view.dataset.surveyView === 'home') map.home(); else map.flyToNeuron(focus.layer,focus.n,0.3); }
    const d = e.target.closest('button[data-dose]');
    if (d) { dose = d.dataset.dose; paint(); render(); }
    const step = e.target.closest('button[data-layer-step]');
    if (step && focus) {
      const layer = focus.layer + +step.dataset.layerStep;
      const next = model.points.find(p => p.layer===layer && five(p)) || model.points.find(p => p.layer===layer);
      if (next) pick(next.layer,next.channel);
    }
  };
  paint(); render();
  return {
    select(layer,n) { focus = {layer,n}; render(); },
    defaultPoint: profile==='4b' ? {layer:6,n:7840} : (()=>{const p=model.points.find(p=>p.layer===Math.min(6,model.layers-1)&&five(p))||model.points[0];return {layer:p.layer,n:p.channel};})()
  };
}
