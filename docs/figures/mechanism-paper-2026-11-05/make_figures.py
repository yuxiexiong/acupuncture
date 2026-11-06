"""Paper figures as dependency-free SVG.  python3 -I make_figures.py DATA_DIR OUT_DIR
Every count is read from the analysis JSON files in DATA_DIR; the few values transcribed from reports are marked REPORT below.
Colour by job (categorical, fixed order, validated on the light surface): correct = blue, explicit wrong number = orange, other = aqua;
stop / no answer = neutral gray (absence, not a series hue)."""
import json
import sys
from pathlib import Path

DATA, OUT = Path(sys.argv[1]), Path(sys.argv[2])
J = lambda f: json.load(open(DATA / f))   # noqa: E731
SURF, INK, INK2, GRID = '#fcfcfb', '#0b0b0b', '#52514e', '#e7e6e2'
COL = {'correct': '#2a78d6', 'wrong': '#eb6834', 'stop': '#b9b8b2', 'other': '#1baf7a', 'donor': '#eb6834', 'recv': '#2a78d6'}
ON = {'correct': '#ffffff', 'wrong': '#ffffff', 'stop': INK, 'other': INK, 'donor': '#ffffff', 'recv': '#ffffff'}
FONT = "font-family='DejaVu Sans, Liberation Sans, Helvetica, Arial, sans-serif'"


def esc(s):
    return str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


class Svg:
    def __init__(self, w):
        self.w, self.h, self.el = w, 0, []

    def text(self, x, y, s, size=12, anchor='start', fill=INK, weight='normal'):
        self.el.append(f"<text x='{x:.1f}' y='{y:.1f}' font-size='{size}' text-anchor='{anchor}' fill='{fill}' font-weight='{weight}' {FONT}>{esc(s)}</text>")
        self.h = max(self.h, y + 6)

    def rect(self, x, y, w, h, fill, rx=0):
        self.el.append(f"<rect x='{x:.1f}' y='{y:.1f}' width='{max(w, 0):.1f}' height='{h:.1f}' fill='{fill}' rx='{rx}'/>")
        self.h = max(self.h, y + h)

    def line(self, x1, y1, x2, y2, stroke=GRID, width=1, dash=None):
        d = f" stroke-dasharray='{dash}'" if dash else ''
        self.el.append(f"<line x1='{x1:.1f}' y1='{y1:.1f}' x2='{x2:.1f}' y2='{y2:.1f}' stroke='{stroke}' stroke-width='{width}'{d}/>")
        self.h = max(self.h, y1, y2)

    def raw(self, s, h=0):
        self.el.append(s)
        self.h = max(self.h, h)

    def save(self, name, title):
        H = self.h + 16
        body = '\n'.join(self.el)
        (OUT / name).write_text(f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 {self.w} {H:.0f}' width='{self.w}' height='{H:.0f}' role='img' aria-label='{esc(title)}'>\n"
                                f"<title>{esc(title)}</title>\n<rect width='{self.w}' height='{H:.0f}' fill='{SURF}'/>\n{body}\n</svg>\n", encoding='utf-8')


def legend(svg, x, y, items):
    for lab, key in items:
        svg.rect(x, y - 9, 10, 10, COL[key], rx=2)
        svg.text(x + 15, y, lab, 11, fill=INK2)
        x += 22 + 6.2 * len(lab)
    return y + 14


def rows(svg, y, data, total, x0=262, width=380, bar=14, gap=7, tail=None):
    """data: list of (label, [(key, n), ...]) | ('#', header) | None (spacer).  Returns next y."""
    for item in data:
        if item is None:
            y += 8
            continue
        if item[0] == '#':
            y += 6
            svg.text(18, y + 10, item[1], 11.5, fill=INK, weight='bold')
            y += 20
            continue
        lab, segs = item[0], item[1]
        note = item[2] if len(item) > 2 else None
        svg.text(x0 - 10, y + bar - 3, lab, 11.5, anchor='end', fill=INK2)
        x = x0
        tot = total if not isinstance(total, dict) else total[lab]
        for key, n in segs:
            if n <= 0:
                continue
            w = width * n / tot
            svg.rect(x, y, max(w - 2, 1), bar, COL[key], rx=2)
            if w >= 22:
                svg.text(x + (w - 2) / 2, y + bar - 3.5, n, 10.5, anchor='middle', fill=ON[key])
            x += w
        first = segs[0]
        t = tail(lab, segs, tot) if tail else f"{first[1]}/{tot}"
        svg.text(x0 + width + 8, y + bar - 3, t if not note else f"{t}   {note}", 11, fill=INK2)
        y += bar + gap
    return y


def cats(c):
    """NWR category counts -> four plotted segments."""
    return [('correct', c['correct']), ('wrong', c['wrong_num']), ('stop', c['stop_no_code']), ('other', c['multi_code'] + c['budget'] + c['other'])]


LEG = [('correct answer', 'correct'), ('explicit wrong number', 'wrong'), ('stop / no number', 'stop'), ('other', 'other')]
DIRS = [('N_L00_C4146_D-1', 'N4146'), ('N_L00_C1210_D-1', 'N1210'), ('R0_L00_D-1', 'R0')]


def fig2():
    en = J('enum-offline-r01.json')
    s = Svg(820)
    s.text(18, 24, 'Write at t1, read at t2: outcomes of 48 inputs per arm (specified receivers)', 13, weight='bold')
    y = legend(s, 18, 46, LEG) + 4
    d = [('#', 'A  Replace v and/or k in the t1 write of the 14 recurrent layers (LVK)')]
    for key, nm in DIRS:
        a = en['lvk_new_panel'][key]
        d += [(f'{nm}  native (v0, k0)', cats(a['L00']['counts'])), ('k only (v0, k1)', cats(a['L01']['counts'])),
              ('v only (v1, k0)', cats(a['L10']['counts'])), ('v and k (v1, k1)', cats(a['L11']['counts'])), None]
    y = rows(s, y, d, 48)
    d = [('#', 'B  At t2, read the other endpoint\'s written state: direct read D, correction E (SRU)')]
    for key, nm in DIRS:
        g, w = en['sru'][key]['gain'], en['sru'][key]['withdraw']
        d += [(f'{nm}  receiver v-only: none', cats(g['00']['counts'])), ('+ D from v-and-k', cats(g['10']['counts'])),
              ('+ E from v-and-k', cats(g['01']['counts'])), ('+ D and E', cats(g['11']['counts'])),
              ('receiver v-and-k: none', cats(w['00']['counts'])), ('+ D from v-only', cats(w['10']['counts'])),
              ('+ E from v-only', cats(w['01']['counts'])), ('+ D and E', cats(w['11']['counts'])), None]
    y = rows(s, y, d, 48)
    p = DATA / 'nwr-readouts-r01.json'
    if p.exists():
        r = json.load(open(p))['rates']
        d = [('#', 'C  NWR: native donor state read by a v-and-k repaired receiver (N4146)'),
             ('receiver v-and-k: none', cats(r['L11']['counts'])), ('+ D from native write', cats(r['D00']['counts'])),
             ('+ E from native write', cats(r['E00']['counts'])), ('+ D from v-only (SRU replay)', cats(r['D10']['counts']))]
        d += [(f'+ random patch {j}, same norm', cats(r[f'R{j}']['counts'])) for j in range(1, 6)]
        y = rows(s, y, d, 48)
    s.text(18, y + 14, 'Right: correct / 48.  R0 is a random intervention direction.  Small segments are unlabelled; all counts are tabulated in the text.', 10.5, fill=INK2)
    s.save('fig2-write-read.svg', 'Figure 2: write at t1 and read at t2, outcome categories per arm')


def fig3():
    ncc, npc = J('ncc-readouts-r01.json'), J('npc-readouts-r01.json')
    s = Svg(820)
    s.text(18, 24, 'What restores the native run, and what breaks a clean run (48 inputs)', 13, weight='bold')
    y = legend(s, 18, 46, [('correct answer', 'correct'), ('not correct', 'stop')]) + 4
    nd = [('N_L00_C4146_D-1', 'L0 / N4146'), ('N_L12_C3621_D-1', 'L12 / C3621')]
    lab = {'T': 'native run', 'TV': '+ clean conv-V history', 'TS': '+ clean deep recurrent S', 'TK': '+ clean deep KV', 'TJ': '+ all clean deep state'}
    d = [('#', 'A  Restoring one deep state group in the native run (NCC)')]
    for k, nm in nd:
        yc = ncc['needles'][k]['Y_counts']
        fs = ncc['needles'][k]['first_stop']
        d += [(f"{nm}  {lab[a]}" if a == 'T' else lab[a], [('correct', yc[a]), ('stop', 48 - yc[a])], f"·  first-step stop {fs[a]}") for a in ('T', 'TV', 'TS', 'TK', 'TJ')] + [None]
    y = rows(s, y, d, 48)
    lab = {'CS': 'damaged S only', 'CV': 'damaged conv-V only', 'CK': 'damaged KV only', 'CSV': 'damaged S + V', 'CSK': 'damaged S + KV', 'CVK': 'damaged V + KV',
           'CVSK': 'damaged V + S + KV', 'CJ': 'all damaged deep state'}
    d = [('#', 'B  Moving damaged state from the native run into a clean run (NSR / NQK / NPC)')]
    for k, nm in nd:
        v = npc['needles'][k]
        d += [(f"{nm}  {lab[a]}" if a == 'CS' else lab[a], [('correct', v[a]['Y']), ('stop', 48 - v[a]['Y'])]) for a in ('CS', 'CV', 'CK', 'CSV', 'CSK', 'CVK', 'CVSK', 'CJ')] + [None]
    y = rows(s, y, d, 48)
    s.text(18, y + 14, 'Restoring one group can be sufficient where damaging that group alone is harmless: not mirror images.', 10.5, fill=INK2)
    s.save('fig3-native-recovery-pollution.svg', 'Figure 3: recovery in the native run and pollution of a clean run')


def fig4():
    s = Svg(820)
    s.text(18, 24, 'Boundaries of the write-read account (each panel has its own denominator)', 13, weight='bold')
    y = 44
    BL = '#2a78d6'

    def panel(y, title, items, vmax, fmt, xlab):
        s.text(18, y + 10, title, 11.5, weight='bold')
        y += 22
        x0, width = 262, 380
        for lab, v in items:
            s.text(x0 - 10, y + 11, lab, 11.5, anchor='end', fill=INK2)
            if isinstance(v, tuple):
                s.rect(x0 + width * v[0] / vmax, y + 3, width * (v[1] - v[0]) / vmax, 8, BL, rx=2)
                s.text(x0 + width * v[1] / vmax + 8, y + 11, f"{fmt(v[0])} to {fmt(v[1])}", 11, fill=INK2)
            else:
                s.rect(x0, y, max(width * v / vmax, 1), 14, BL, rx=2)
                s.text(x0 + width * max(v, 0) / vmax + 8, y + 11, fmt(v), 11, fill=INK2)
            y += 21
        s.line(x0, y, x0 + width, y)
        s.text(x0, y + 13, '0', 10, fill=INK2)
        s.text(x0 + width, y + 13, fmt(vmax), 10, anchor='end', fill=INK2)
        s.text(x0 + width / 2, y + 13, xlab, 10, anchor='middle', fill=INK2)
        return y + 30
    f2 = lambda v: f"{v:.2f}"   # noqa: E731
    fi = lambda v: f"{v:.0f}"   # noqa: E731
    # REPORT: NVB report (retained v under native output / joint), spine E9
    y = panel(y, 'A  Native output kept: retained-v effect as a share of the joint effect (NVB)',
              [('N4146', 0.11), ('N1210', 0.33), ('R0', 0.34)], 1.0, f2, 'share of joint effect on target competition M')
    # REPORT: NMT v2 report (phi_up, native receiver; uniform scaling range)
    y = panel(y, 'B  Source difference of the k effect reproduced in the native receiver (NMT)',
              [('direction + per-head amplitude, N4146', 0.75), ('N1210', 0.86), ('R0', 0.91), ('uniform scaling, range', (0.15, 0.38))],
              1.0, f2, 'share of the source difference reproduced')
    # REPORT: SIT report (Y lost when the native-source increment replaces the recovered one, k fixed)
    y = panel(y, 'C  Answers lost when the native-background increment replaces the recovered one (SIT)',
              [('N4146', 18), ('N1210', 12), ('R0', 5)], 48, fi, 'answers lost, of 48')
    # REPORT: CGV r02 (L12 / C3621)
    y = panel(y, 'D  Another layer (L12 / C3621): local v alone repairs; the k fix adds nothing (CGV)',
              [('native run, correct', 31), ('+ local v at t1, correct', 48)], 48, fi, 'correct answers, of 48')
    s.text(18, y + 4, 'New record structures (27 inputs): target competition moves but only 1 to 4 full answers change.', 10.5, fill=INK2)
    s.save('fig4-boundaries.svg', 'Figure 4: boundaries of the write-read account')


def fig5():
    win, w2 = J('win-readouts-r01.json'), J('w2-readouts-r01.json')
    s = Svg(820)
    s.text(18, 24, 'The intervention window changes which restoration is enough (L0 / N4146, 48 inputs per task)', 13, weight='bold')
    y = legend(s, 18, 46, [('correct answer', 'correct'), ('not correct', 'stop')]) + 4
    arms = [('T', 'native run'), ('R_all', '+ all recurrent state'), ('S_deep', '+ deep recurrent S only'), ('KV_all', '+ all KV'),
            ('R+KV_all', '+ recurrent and KV'), ('R_all+KV_pre', '+ recurrent, KV before record end')]
    wl = {'W_all': 'whole prefix', 'W_pre': 'before record sentence', 'W_post': 'after record sentence'}
    for task, tn in (('fact', 'A  Fact task'), ('code', 'B  Numbered-record task')):
        d = [('#', f'{tn}: intervention window x restored state (WIN-01)')]
        for w in ('W_all', 'W_pre', 'W_post'):
            first = True
            for a, an in arms:
                c = win['cells'].get(f'{task}|N_L00_C4146_D-1|{w}|{a}')
                if c is None:
                    continue
                d.append((f"{wl[w]}:  {an}" if first else an, [('correct', c['correct']), ('stop', c['n'] - c['correct'])]))
                first = False
            d.append(None)
        y = rows(s, y, d, 48)
    d = [('#', 'C  Extra KV on new conditions (WIN-02): rescued among inputs still wrong after recurrent restoration')]
    tot = {}
    nm = {'fact|N_L02_C5251_D-1': 'fact, L2 / C5251', 'fact|N_L03_C7666_D-1': 'fact, L3 / C7666', 'fact|N_L05_C2467_D-1': 'fact, L5 / C2467', 'fact|R0_L00_D-1': 'fact, L0 / R0',
          'code|N_L02_C5251_D-1': 'numbered, L2 / C5251', 'code|N_L03_C7666_D-1': 'numbered, L3 / C7666', 'code|N_L05_C2467_D-1': 'numbered, L5 / C2467', 'code|R0_L00_D-1': 'numbered, L0 / R0'}
    for k, v in w2['P3_M'].items():
        n, r = v['positive']['n'], v['positive']['rescued']
        note = ('·  ceiling, too few to test' if v['label'] == 'ceiling' else '·  holds') + f";  broke {v['break']['broken']} of {v['break']['n']} already correct"
        tot[nm[k]] = max(n, 1) if n else 48
        d.append((nm[k], [('correct', r), ('stop', n - r)] if n else [('correct', 0)], note))
    y = rows(s, y, d, tot, width=200, tail=lambda lab, segs, t: f"{segs[0][1]}/{sum(n for _, n in segs)}")
    s.text(18, y + 14, 'Panel C bars are scaled to each row\'s own number of testable inputs; rows marked ceiling had at most 4.', 10.5, fill=INK2)
    s.save('fig5-window-kv.svg', 'Figure 5: formation window and extra KV restoration')


def fig6():
    kvc = J('kvc-readouts-r01.json')
    s = Svg(820)
    s.text(18, 24, 'Swapping the fact segment of the KV: whose fact does the answer follow? (44 receivers)', 13, weight='bold')
    y = legend(s, 18, 46, [('follows receiver fact', 'recv'), ('follows donor fact', 'donor'), ('other', 'stop')]) + 4
    nm = [('C', 'clean run, no swap'), ('B_pre', 'clean run, donor KV segment'), None,
          ('N_L03_C7666_D-1|M_same', 'L3 / C7666  same-version KV'), ('N_L03_C7666_D-1|M_other', 'donor-version KV'), None,
          ('N_L00_C4146_D-1|M_same', 'L0 / N4146  same-version KV'), ('N_L00_C4146_D-1|M_other', 'donor-version KV'), None,
          ('R0_L00_D-1|M_same', 'L0 / R0  same-version KV'), ('R0_L00_D-1|M_other', 'donor-version KV')]
    d = [('#', 'KVC-01: intervened runs have recurrent state restored and KV before the record end added')]
    for it in nm:
        if it is None:
            d.append(None)
            continue
        c = kvc['cells'][it[0]]['RDO']
        d.append((it[1], [('recv', c['R']), ('donor', c['D']), ('stop', c['O'])]))
    y = rows(s, y, d, 44, tail=lambda lab, segs, t: f"donor {segs[1][1]}/{t}")
    s.text(18, y + 14, 'Near-saturated in all three conditions: directional, but no evidence of a read path shared with the write-read chain.', 10.5, fill=INK2)
    s.save('fig6-kv-donor-transfer.svg', 'Figure 6: donor fact transfer through the KV segment')


def fig1():
    s = Svg(820)
    s.text(18, 24, 'From a sparse intervention to the answer: what is connected by operations, and what is not', 13, weight='bold')
    BX, BW, BH, Y0 = [18, 180, 342, 504, 666], 136, 62, 60
    boxes = [('Sparse intervention', 'layer 0, prompt window', 'one coordinate or a', 'random direction'),
             ('t1: write of the', 'recurrent layers', 'first such layer: native', 'and v-fix differ only in v'),
             ('Written state S1', 'update of shared S0:', 'decay, correction,', 'and new-value write'),
             ('t2: direct read', 'alpha S1^T q', '(the other use, E, is', 'weak or opposite)'),
             ('Answer', 'target record, or', 'fall back to the', 'first-listed record')]
    for x, b in zip(BX, boxes):
        s.raw(f"<rect x='{x}' y='{Y0}' width='{BW}' height='{BH + 14}' fill='#ffffff' stroke='#b9b8b2' stroke-width='1' rx='6'/>", Y0 + BH + 14)
        s.text(x + BW / 2, Y0 + 18, b[0], 11.5, anchor='middle', weight='bold')
        for i, t in enumerate(b[1:]):
            s.text(x + BW / 2, Y0 + 34 + 14 * i, t, 10.5, anchor='middle', fill=INK2)
    ym = Y0 + (BH + 14) / 2
    for i in range(4):
        x1, x2 = BX[i] + BW, BX[i + 1]
        dash = '5 4' if i == 0 else None
        s.line(x1 + 3, ym, x2 - 7, ym, stroke=INK2, width=1.6, dash=dash)
        s.raw(f"<path d='M{x2 - 9},{ym - 4} L{x2 - 2},{ym} L{x2 - 9},{ym + 4} Z' fill='{INK2}'/>")
    # branch: first-step stop
    xb = BX[1] + BW / 2
    s.line(xb, Y0 + BH + 14, xb, Y0 + BH + 44, stroke=INK2, width=1.6)
    s.raw(f"<rect x='{BX[1]}' y='{Y0 + BH + 44}' width='{BW}' height='48' fill='#ffffff' stroke='#b9b8b2' stroke-width='1' rx='6'/>", Y0 + BH + 92)
    s.text(xb, Y0 + BH + 62, 't1 output', 11.5, anchor='middle', weight='bold')
    s.text(xb, Y0 + BH + 78, 'first-step stop, 47 of 48', 10.5, anchor='middle', fill=INK2)
    y = Y0 + BH + 122
    s.line(18, y - 14, 60, y - 14, stroke=INK2, width=1.6)
    s.text(68, y - 10, 'evidence at specified endpoints', 11, fill=INK2)
    s.line(400, y - 14, 442, y - 14, stroke=INK2, width=1.6, dash='5 4')
    s.text(450, y - 10, 'not identified', 11, fill=INK2)
    notes = [('Entry (dashed)', 'why the intervention changes v and k at t1 is not explained.'),
             ('t1 write (LVK)', 'local v/k operations on shared native history: 0 to 16 to 39 correct, of 48 (N4146).'),
             ('t2 read (SRU)', 'local write endpoints as receivers; direct-read swaps: 39 to 18, 16 to 34 (N4146).'),
             ('t2 read (NWR)', 'native donor, repaired receiver: 39 to 16 of 48 correct; all 48 select the first record.'),
             ('Control (NWR)', 'same-norm random patches: mean scene-weighted loss 0.033; one adds 18 errors.'),
             ('Not reached', 'native L00 stops at t1 on 47/48 inputs; its natural t2 read is not measured here.')]
    for a, b in notes:
        s.text(18, y + 12, a, 11, weight='bold')
        s.text(138, y + 12, b, 11, fill=INK2)
        y += 19
    s.save('fig1-chain-overview.svg', 'Figure 1: chain from sparse intervention to answer, with evidence status')


if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    for f in (fig1, fig2, fig3, fig4, fig5, fig6):
        f()
        print('ok', f.__name__)
