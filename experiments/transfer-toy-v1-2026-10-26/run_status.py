"""Read receipts and process identities only; never read model answer text."""
import argparse
from datetime import datetime, timezone, timedelta
import json
from pathlib import Path
from run_io import read


def optional(path):
    return read(path) if Path(path).exists() else {}


def live(pid):
    path=Path('/proc')/str(pid)/'cmdline'
    if not path.exists():return False
    return 'transfer-toy-v1-2026-10-26' in path.read_bytes().decode(errors='replace')


def main(args):
    run=Path(args.run)
    queue=optional(run/'queue_receipt.json')
    now=datetime.now(timezone.utc)
    status={'checked_utc':now.isoformat(),'queue':{k:queue.get(k) for k in ['status','pid','current_stage','error']},
            'queue_process_matches':live(queue['pid']) if queue.get('pid') else None,'models':{},
            'root_cause_experiment':'paused','human_blind_rating_eta':'not_estimable_pending_human_labels'}
    rate9=optional(run/'decode-target9b/receipt.json').get('tokens_per_wall_second_including_prefill',15.36)
    rates={'source':optional(run/'decode-source4b/receipt.json').get('tokens_per_wall_second_including_prefill',16.0),
           'target9b':rate9,'target2b':optional(run/'decode-target2b/receipt.json').get('tokens_per_wall_second_including_prefill',rate9)}
    def toy(name):
        directory=run/'source' if name=='source' else run/name/'toy'
        expected_behavior=96 if name=='source' else 608
        expected_diag=0 if name=='source' else 608
        workers=[];estimates=[]
        for shard in (0,1):
            r=optional(directory/f'shard{shard}'/'receipt.json')
            worker={k:r.get(k) for k in ['status','completed_behavior','completed_diagnostic','current_item','current_condition','elapsed_seconds','error']}
            workers.append(worker)
            if r.get('status')=='completed':estimates.append(0);continue
            samples=r.get('condition_seconds',{}).get('behavior',{})
            complete_count=r.get('completed_behavior',0)
            if len(samples)==(3 if name=='source' else 19) and min(map(len,samples.values()))>=2:
                remaining=sum(sum(v)/len(v)*max(0,32-len(v)) for v in samples.values())
                worker['estimate_basis']='per_condition_observed_mean'
            else:
                remaining=(expected_behavior-complete_count)*512/rates[name]
                worker['estimate_basis']='512_token_budget_at_short_decode_rate'
            diag=r.get('condition_seconds',{}).get('ability',{})
            if diag:
                remaining+=sum(sum(v)/len(v)*max(0,32-len(v)) for v in diag.values())
            else:
                remaining+=max(0,expected_diag-r.get('completed_diagnostic',0))*1.5
            estimates.append(remaining)
        return {'workers':workers,'remaining_seconds_scenario':max(estimates)},max(estimates)
    source,source_left=toy('source');status['models']['source']=source
    total=source_left
    for name in ('target9b','target2b'):
        item,toy_left=toy(name)
        item['decode_tokens_per_second_reference']=rates[name]
        item['rate_is_target_measurement']=(run/('decode-'+name)/'receipt.json').exists()
        bench=[];bench_left=[]
        for shard in (0,1):
            r=optional(run/name/'benchmark'/f'shard-{shard}'/'receipt.json')
            bench.append({k:r.get(k) for k in ['status','completed_pairs','expected_pairs','wall_seconds','last_completed_id','error']})
            if r.get('status')=='completed':bench_left.append(0);continue
            remaining=0
            for task,count,budget in [('mmlu',500,None),('arc_challenge',100,None),('gsm8k',50,2048),('humaneval',50,1024)]:
                task_state=r.get('tasks',{}).get(task,{})
                completed=task_state.get('completed_pairs',0)
                per_pair=(task_state.get('inference_seconds',0)/completed if completed>=4 else
                          (2*budget/rates[name] if budget else (0.8 if task=='mmlu' else 2.5)))
                remaining+=max(0,count-completed)*per_pair
            bench_left.append(remaining)
        item['benchmark_workers']=bench
        item['benchmark_remaining_seconds_scenario']=max(bench_left)
        remaining=toy_left+max(bench_left)
        if name=='target2b' and not (run/'collection-target2b/receipt.json').exists():remaining+=120
        if not (run/name/'export-r01/receipt.json').exists():remaining+=120
        total+=remaining
        item['remaining_model_hours_scenario']=round(remaining/3600,2)
        item['queue_finish_beijing_scenario']=(now+timedelta(seconds=total)).astimezone(timezone(timedelta(hours=8))).isoformat()
        status['models'][name]=item
    status['remaining_queue_hours_scenario']=round(total/3600,2)
    status['limitations']='Not a confidence interval or guaranteed upper bound. Unmeasured arms use full token budgets and short-context speed; measured arms use condition/task means. 2B inherits 9B speed until its own turn. Excludes human ratings and future failures.'
    print(json.dumps(status,ensure_ascii=False,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--run',required=True);main(p.parse_args())
