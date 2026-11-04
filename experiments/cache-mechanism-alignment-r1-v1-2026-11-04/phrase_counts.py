"""Data-after descriptive keyword count (NOT a label, NOT a scorer).  For stage2 records at L0-L3, L12 and clean,
flag answers whose text matches a crude regex for 'the prompt is repetitive / lacks the information'.
phrase_flags.txt was produced on the server by reading generation.answer_text of each record path in
records_l0-3_l12.txt with:  re.search('重复|多次|误触|测试系统|全是|仅包含|只包含|没有.*(给出|提供|列出)|未包含|无法确定', t)
Usage: python phrase_counts.py > phrase_counts.md   (both panels pooled, 48 inputs per cell)"""
from collections import defaultdict
D = defaultdict(lambda: [0, 0, 0, 0])
for a, b in zip(open('records_l0-3_l12.txt'), open('phrase_flags.txt')):
    p, arm, L, d, lab, rec = a.split(); f = b.strip() == '1'; bad = lab != 'follows_fact'
    x = D[(L, d, arm)]; x[0] += bad; x[1] += bad and f; x[2] += not bad; x[3] += (not bad) and f
N = {'CCC': 'C', 'TTT': 'T', 'TCT': '恢复R', 'CTT': '恢复KV', 'TTC': '恢复conv', 'TCC': '恢复R+conv', 'CTC': '恢复KV+conv', 'CCT': '恢复KV+R'}
print('| 层 | 剂量 | ' + ' | '.join(N.values()) + ' |'); print('|---' * (len(N) + 2) + '|')
c = D[('C', '0', 'CCC')]
print(f'| C | — | 错{c[0]}（含{c[1]}）/对{c[2]}（含{c[3]}） |' + ' |' * (len(N) - 1))
for L in ('0', '1', '2', '3', '12'):
    for d in ('-1', '1'):
        cells = [f'错{D[(L,d,a)][0]}（含{D[(L,d,a)][1]}）/对{D[(L,d,a)][2]}（含{D[(L,d,a)][3]}）' if (L, d, a) in D else '' for a in N]
        print(f'| {L} | {d} | ' + ' | '.join(cells) + ' |')
