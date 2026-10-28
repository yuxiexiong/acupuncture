// Pure views of archived measurements. Missing observations stay null.
export const DOSES = [-1,-.5,-.25,-.125,-.0625,0,.0625,.125,.25,.5,1];
export function doseRows(records, layer, channel, question) {
  return DOSES.map(dose => records.find(r => r.question_id === question &&
    (dose === 0 ? r.layer === null && r.dose === 0 : r.layer === layer && r.channel === channel && r.dose === dose)) || null);
}
export function predictionColumns(trace) {
  if (!trace) return [];
  const forwards = new Map(trace.forward_steps.map(f => [f.step, f]));
  return trace.logits.steps.map(logits => {
    const f = forwards.get(logits.step);
    if (!f) throw new Error('归档缺少对应预测步');
    return {step:logits.step, position:f.observed_start+f.observed_count-1, logits};
  });
}
export function actualGap(logits) {
  const actual = logits.candidates.find(c => c.token_id === logits.generated_token_id);
  return actual ? actual.clean_logit - Math.max(...logits.candidates.map(c => c.clean_logit)) : null;
}
export function candidateValues(columns, tokenId, arm) {
  return columns.map(({logits}) => logits.candidates.find(c => c.token_id === tokenId)?.[arm+'_logprob'] ?? null);
}
