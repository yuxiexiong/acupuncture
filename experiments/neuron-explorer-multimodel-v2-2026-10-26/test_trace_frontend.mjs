// Check the scientific display semantics without loading a model or a browser.
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
const code = await readFile(new URL('./upstream/explorer/static/trace.js', import.meta.url), 'utf8');
const {traceColor,traceValue,predictionAt} = await import('data:text/javascript;base64,'+Buffer.from(code).toString('base64'));
const site = {relative_delta:[0,0.5,null],cosine:[1,0,-1]};
assert.equal(traceValue(site,0,'cosine'),0);
assert.equal(traceValue(site,2,'cosine'),2);
assert.equal(traceValue(site,2,'relative_delta'),null);
assert.notEqual(traceColor(0,'relative_delta'),traceColor(null,'relative_delta'));
assert.equal(traceColor(10,'relative_delta'),traceColor(1000,'relative_delta'));
const trace={forward_steps:[{step:0,observed_start:0,observed_count:3},{step:1,observed_start:3,observed_count:1}],logits:{steps:[{step:0},{step:1}]}};
assert.equal(predictionAt(trace,0),null); // No logits were captured for interior prompt positions.
assert.equal(predictionAt(trace,2).step,0); // Last prompt input predicts output token 1.
assert.equal(predictionAt(trace,3).step,1);
assert.equal(predictionAt(trace,4),null); // The final sampled token was not fed back.
console.log('passed: zero/null distinction, fixed color saturation, direction distance, prompt/decode alignment');
