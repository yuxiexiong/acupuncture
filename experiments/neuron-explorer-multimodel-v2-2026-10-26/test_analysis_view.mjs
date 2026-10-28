#!/usr/bin/env node
// Check the actual archived API data and view transformations; no model runtime.
import assert from 'node:assert/strict';
import {mkdir, writeFile} from 'node:fs/promises';
import {DOSES, doseRows, predictionColumns, actualGap, candidateValues} from './upstream/explorer/static/analysis-data.js';

const base = 'http://127.0.0.1:8794', start = performance.now();
const models = [['2b',3656,920,24],['4b',4872,4872,32],['9b',4872,920,32],['llama31-8b-instruct',4872,920,32]];
const indexes = new Map(), checkedModels = [], cases = [];
async function get(path, params={}) {
  const response = await fetch(`${base}${path}?${new URLSearchParams(params)}`, {signal:AbortSignal.timeout(60000)});
  assert.equal(response.status,200,path);
  return response.json();
}
assert.deepEqual(DOSES,[-1,-.5,-.25,-.125,-.0625,0,.0625,.125,.25,.5,1]);
const service = await get('/api/index');
assert.equal(service.new_inference,false);
assert.equal(service.read_only,true);
for (const [model,count,traces,layers] of models) {
  const index = await get('/api/results/index',{model}), rows = index.records;
  indexes.set(model,rows);
  assert.equal(rows.length,count);
  assert.equal(rows.filter(r=>r.has_trace).length,traces);
  assert.equal(new Set(rows.map(r=>r.trace_id)).size,count);
  assert(rows.every(r=>r.model===model));
  const baselines=rows.filter(r=>r.layer===null);
  assert.equal(baselines.length,8);
  assert.equal(new Set(baselines.map(r=>r.question_id)).size,8);
  let mirrorGroups=0, sparseGroups=0;
  for (let layer=0;layer<layers;layer++) {
    const local=rows.filter(r=>r.layer===layer||r.layer===null);
    const channels=[...new Set(local.filter(r=>r.layer===layer).map(r=>r.channel))];
    assert.equal(channels.length,10);
    for (const channel of channels) for (const {question_id} of baselines) {
      const aligned=doseRows(local,layer,channel,question_id);
      const complete=local.some(r=>r.layer===layer&&r.channel===channel&&r.dose===.5);
      assert.equal(aligned.length,11);
      assert.equal(aligned.filter(Boolean).length,complete?11:2);
      assert.equal(aligned[5].layer,null);
      assert.equal(aligned[5].channel,null);
      assert.equal(aligned[5].dose,0);
      for (let i=0;i<11;i++) if (aligned[i]) {
        assert.equal(aligned[i].dose,DOSES[i]);
        assert.equal(aligned[i].question_id,question_id);
        if(i!==5) { assert.equal(aligned[i].layer,layer);assert.equal(aligned[i].channel,channel); }
      }
      if(complete) mirrorGroups++; else { sparseGroups++;assert(aligned[10]); }
    }
  }
  assert.equal(mirrorGroups,layers*8);
  assert.equal(sparseGroups,layers*9*8);
  checkedModels.push({model,answers:count,traces,mirror_groups:mirrorGroups,sparse_groups:sparseGroups,missing_slots_per_sparse_group:9});
}

async function detail(model,layer,channel,dose,question='Q04') {
  const row=indexes.get(model).find(r=>r.layer===layer&&r.channel===channel&&r.dose===dose&&r.question_id===question);
  assert(row,`${model}/${layer}/${channel}/${dose}/${question}`);
  const data=await get('/api/results/detail',{model,id:row.trace_id});
  const source=await get('/api/results/source',{model,id:row.trace_id,arm:'intervened'});
  assert.deepEqual(data.intervened.token_ids,source.output.token_ids);
  assert.equal(data.intervened.raw_text,source.output.raw_text);
  if(data.trace) {
    const t=data.trace, columns=predictionColumns(t);
    assert.deepEqual(t.generated_token_ids,data.intervened.token_ids);
    assert.deepEqual(t.observed_input_token_ids,[...t.input_token_ids,...t.generated_token_ids.slice(0,-1)]);
    assert.equal(columns.length,t.generated_token_ids.length);
    assert.equal(columns[0].position,t.prompt_token_count-1);
    assert.equal(columns.at(-1).position,t.observed_position_count-1);
    assert.equal(t.clean_shadow.forced_history,true);
    assert.equal(t.clean_shadow.fresh_cache,true);
    for(const c of columns) {
      assert.equal(c.position,t.prompt_token_count-1+c.step);
      assert.equal(c.logits.generated_token_id,t.generated_token_ids[c.step]);
      for(const arm of ['clean','steer']) {
        const candidates=c.logits.candidates;
        const margin=Math.max(...candidates.filter(x=>x.is_eos).map(x=>x[arm+'_logit']))-
          Math.max(...candidates.filter(x=>!x.is_eos).map(x=>x[arm+'_logit']));
        assert(Math.abs(margin-c.logits[arm+'_stop_advantage'])<1e-6);
      }
    }
    for(const site of t.sites) for(const field of ['clean_norm','steer_norm','delta_norm','relative_delta','cosine'])
      assert.equal(site[field].length,t.observed_position_count);
  }
  cases.push({model,layer,channel,dose,question,source_id:row.trace_id,tokens:data.intervened.token_ids.length,has_trace:data.has_trace});
  return data;
}
const eos=await detail('4b',0,4146,1), eosStep=predictionColumns(eos.trace)[0].logits;
assert.equal(eos.intervened.raw_text,'<|im_end|>');
assert.equal(eos.intervened.answer_text,'');
assert.equal(eos.intervened.token_ids.length,1);
assert.equal(eosStep.clean_stop_advantage,-17.6875);
assert.equal(eosStep.steer_stop_advantage,3.0625);
const half=await detail('4b',0,4146,.5), halfColumns=predictionColumns(half.trace);
assert.equal(halfColumns.length,27);
assert.equal(halfColumns[0].logits.clean_stop_advantage,-17.6875);
assert.equal(halfColumns[0].logits.steer_stop_advantage,-8.25);
assert.equal(actualGap(halfColumns[2].logits),-3.125);
const loop=await detail('4b',2,5063,1), loopColumns=predictionColumns(loop.trace);
assert.equal(loopColumns.length,128);
assert.equal(loop.intervened.stop_reason,'length_limit');
assert.equal(actualGap(loopColumns[2].logits),-5.9375);
const baseline=await detail('4b',null,null,0);
assert(baseline.trace.sites.every(s=>s.delta_norm.every(v=>v===0)));
const deep=indexes.get('llama31-8b-instruct').find(r=>r.layer===31&&r.dose===-1&&r.question_id==='Q04');
const missing=await detail('llama31-8b-instruct',31,deep.channel,-1);
assert.equal(missing.trace,null);
assert.equal(missing.has_trace,false);
assert.deepEqual(predictionColumns(missing.trace),[]);

const synthetic=[{logits:{generated_token_id:2,candidates:[
  {token_id:1,clean_logit:3,clean_logprob:-.3,steer_logprob:-.5},
  {token_id:2,clean_logit:3,clean_logprob:-.3,steer_logprob:-.2}]}},
  {logits:{candidates:[{token_id:2,clean_logit:4,clean_logprob:-.1,steer_logprob:-.1}]}}];
assert.equal(actualGap(synthetic[0].logits),0); // A tie is not strict divergence.
assert.deepEqual(candidateValues(synthetic,1,'clean'),[-.3,null]);
assert.deepEqual(candidateValues(synthetic,1,'steer'),[-.5,null]);
assert.deepEqual(candidateValues(synthetic,999,'clean'),[null,null]);

const report={status:'passed',checked_at:new Date().toISOString(),new_inference:false,api:base,
  models:checkedModels,cases,checks:{same_question_baseline_and_order:true,unmeasured_doses_not_filled:true,
    prediction_position_and_generated_token_alignment:true,stop_margins_reconstructed_from_candidates:true,
    independent_forced_prefix_reference:true,source_token_and_raw_text_match:true,baseline_zero_delta:true,
    absent_trace_is_null:true,missing_candidate_is_null:true,tie_gap_zero:true},
  exact_values:{eos_step0_stop:[-17.6875,3.0625],half_step0_stop:[-17.6875,-8.25],half_step2_actual_gap:-3.125,loop_step2_actual_gap:-5.9375},
  elapsed_seconds:Number(((performance.now()-start)/1000).toFixed(3))};
await mkdir(new URL('./analysis-view-r01/',import.meta.url),{recursive:true});
await writeFile(new URL('./analysis-view-r01/data-acceptance.json',import.meta.url),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify(report,null,2));
