"""R1 alignment: per-condition tables from stage2 labels (zero GPU).  Inputs: reading/<panel>/joined.json of
experiments/early-state-localization-stage2-v2-2026-10-30 (copied as <panel>.joined.json next to this script).
Arm code order KV, recurrent R, conv (whole conv_states).  python tables.py > tables.md"""
import sys
from collections import Counter
from s2lib import load, items
REST = {'R': 'TCT', 'KV': 'CTT', 'conv': 'TTC', 'R+conv': 'TCC', 'KV+conv': 'CTC', 'KV+R': 'CCT'}
POL = {'KV': 'TCC', 'R': 'CTC', 'conv': 'CCT', 'KV+R': 'TTC', 'KV+conv': 'TCT', 'R+conv': 'CTT', 'all': 'TTT'}
SING = ('KV', 'R', 'conv')
PAIR = ('KV+R', 'KV+conv', 'R+conv')


def main():
    for panel in ('development-r01', 'g_history-r01'):
        D, C = load(panel)
        its = items(D)
        print(f'\n## {panel}（C {sum(C[i]["Y"] for i in its)}/{len(its)}）\n')
        print('| 层 | 剂量 | 通道 | T 答对 | 未交付(首步停止) | 换答他事实 | 其他错误 | 无法判断 | 恢复 R / KV / 卷积（改对/错误，*改坏） | 恢复 R+卷积 / KV+卷积 / KV+R | 污染 KV / R / 卷积（改坏） | 污染 KV+R / KV+卷积 / R+卷积 | 逐输入最小组合 单类/两类/三类/未致错 |')
        print('|---|---|---|---|---|---|---|---|---|---|---|---|---|')
        for k in sorted(D):
            T = [D[k][('TTT', i)] for i in its]
            cnt = Counter(x['lab'] for x in T)
            bad = [i for i in its if D[k][('TTT', i)]['Y'] == 0]

            def rest(a):
                fx = sum(D[k][(a, i)]['Y'] for i in bad)
                br = sum(1 for i in its if D[k][('TTT', i)]['Y'] == 1 and D[k][(a, i)]['Y'] == 0)
                return f'{fx}/{len(bad)}' + (f'*{br}' if br else '')
            err = {n: {i for i in its if D[k][(a, i)]['Y'] == 0} for n, a in POL.items()}
            m = Counter()
            for i in its:
                if any(i in err[s] for s in SING):
                    m['s'] += 1
                elif any(i in err[p] for p in PAIR):
                    m['p'] += 1
                elif i in err['all']:
                    m['t'] += 1
                else:
                    m['n'] += 1
            print(f"| {k[0]} | {k[1]:+.0f} | {k[2]} | {sum(x['Y'] for x in T)} | {cnt['not_delivered']}({sum(x['first_stop'] for x in T)}) | {cnt['other_fact']} | {cnt['other_wrong']} | {cnt['unclear']} | "
                  f"{' / '.join(rest(REST[n]) for n in ('R', 'KV', 'conv'))} | {' / '.join(rest(REST[n]) for n in ('R+conv', 'KV+conv', 'KV+R'))} | "
                  f"{' / '.join(str(len(err[n])) for n in SING)} | {' / '.join(str(len(err[n])) for n in PAIR)} | {m['s']}/{m['p']}/{m['t']}/{m['n']} |")


if __name__ == '__main__':
    main()
