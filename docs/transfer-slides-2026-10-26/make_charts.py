"""Rebuild the five presentation charts solely from audited local evidence."""
import hashlib
import json
import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/acupuncture-slides-mpl")
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.font_manager import FontProperties
import numpy as np

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[1]
SOURCE = ROOT / "results-evidence.json"
DATA = json.loads(SOURCE.read_text())
OUT = ROOT / "charts"
OUT.mkdir(exist_ok=True)
FONT = FontProperties(fname="/System/Library/Fonts/Supplemental/Arial Unicode.ttf")
BLUE, CORAL, INK, GRID, PAPER = "#123c64", "#d85a49", "#162d40", "#dce4e8", "#fffefa"
TASKS = ["mmlu", "arc_challenge", "gsm8k", "humaneval"]
NAMES = ["MMLU", "ARC-Challenge", "GSM8K", "HumanEval"]
plt.rcParams.update({"font.family": FONT.get_name(), "font.size": 17, "text.color": INK,
    "axes.labelcolor": INK, "xtick.color": INK, "ytick.color": INK,
    "axes.edgecolor": GRID, "axes.spines.top": False, "axes.spines.right": False,
    "figure.facecolor": PAPER, "axes.facecolor": PAPER, "savefig.facecolor": PAPER,
    "svg.fonttype": "path", "axes.unicode_minus": False})

CHECKS = {}
for name, info in DATA["evidence_sources"].items():
    p = PROJECT / name
    actual = hashlib.sha256(p.read_bytes()).hexdigest()
    assert actual == info["sha256"], f"Evidence changed: {name}"
    CHECKS[name] = actual

MANIFEST = {"data_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "source_hashes_verified": CHECKS, "font": str(FONT.get_file()),
    "font_outlines": True, "charts": {}}


def save(fig, name, values, sources):
    plt.rcParams["svg.hashsalt"] = name
    path = OUT / (name + ".svg")
    fig.savefig(path, format="svg", metadata={"Date": None, "Creator": "Acupuncture audited evidence charts"})
    preview = Path("/tmp") / ("acupuncture-" + name + ".png")
    fig.savefig(preview, dpi=100)
    MANIFEST["charts"][name] = {"path": str(path.relative_to(ROOT)),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "values": values,
        "source_paths": sources, "preview": str(preview)}
    plt.close(fig)


def tidy(ax):
    ax.set_axisbelow(True)
    ax.grid(axis="x", color=GRID, lw=.8)
    ax.tick_params(axis="both", length=0, pad=10)
    ax.spines["left"].set_visible(False)


def damage_heatmap():
    keys = ["qwen4b", "qwen9b", "qwen2b", "llama31_stage1"]
    rows = ["Qwen 4B · 原通道", "Qwen 9B · 稀疏", "Qwen 2B · 稀疏", "Llama 3.1 8B · 稠密"]
    values = np.array([[DATA["models"][m]["metrics"][t]["damage_pp"] for t in TASKS] for m in keys])
    fig, ax = plt.subplots(figsize=(14, 4.8))
    fig.subplots_adjust(left=.235, right=.89, top=.90, bottom=.16)
    cmap = LinearSegmentedColormap.from_list("damage", [PAPER, "#f5d1c7", CORAL])
    im = ax.imshow(values, cmap=cmap, vmin=0, vmax=100, aspect="auto")
    ax.set_xticks(range(4), NAMES, fontsize=17)
    ax.set_yticks(range(4), rows, fontsize=17)
    ax.tick_params(length=0, pad=12)
    for i in range(4):
        for j in range(4):
            ax.text(j, i, f"{values[i,j]:.1f}", ha="center", va="center", fontsize=24,
                    color="white" if values[i,j] >= 60 else INK, fontweight="bold")
    ax.set_xticks(np.arange(-.5, 4, 1), minor=True)
    ax.set_yticks(np.arange(-.5, 4, 1), minor=True)
    ax.grid(which="minor", color=PAPER, linewidth=5)
    ax.tick_params(which="minor", length=0)
    for s in ax.spines.values(): s.set_visible(False)
    cb = fig.colorbar(im, cax=fig.add_axes([.915, .16, .018, .74]), ticks=[0,25,50,75,100])
    cb.ax.set_title("下降 / pp", fontsize=13, pad=8)
    cb.outline.set_visible(False)
    save(fig, "damage-heatmap", values.tolist(), [DATA["models"][k]["source_path"] for k in keys])


def qwen_paired():
    fig, axs = plt.subplots(1, 2, figsize=(14, 4.8))
    fig.subplots_adjust(left=.15, right=.965, top=.78, bottom=.17, wspace=.42)
    recorded = {}
    for ax, model, title in zip(axs, ["qwen9b", "qwen2b"], ["Qwen3.5-9B", "Qwen3.5-2B"]):
        rows = DATA["models"][model]["metrics"]
        b = [rows[t]["baseline_percent"] for t in TASKS]
        e = [rows[t]["intervention_percent"] for t in TASKS]
        recorded[model] = {"baseline_percent": b, "intervention_percent": e}
        y = np.arange(4)
        ax.hlines(y, e, b, color="#b6c4ce", lw=4, zorder=1)
        ax.scatter(b, y, s=115, color=BLUE, zorder=3, label="原版")
        ax.scatter(e, y, s=115, color=CORAL, zorder=3, label="两通道干预")
        for yy, bb, ee in zip(y, b, e):
            ax.text(bb, yy-.16, f"{bb:.1f}", ha="center", va="bottom", color=BLUE, fontsize=15)
            ax.text(ee, yy+.16, f"{ee:.1f}", ha="center", va="top", color=CORAL, fontsize=15)
        ax.set_ylim(3.55, -.6)
        ax.set_xlim(-4, 104)
        ax.set_xticks([0, 25, 50, 75, 100])
        ax.set_yticks(y, NAMES, fontsize=15)
        ax.set_xlabel("正确率 / %", labelpad=10, fontsize=16)
        ax.set_title(title, loc="left", fontsize=20, pad=18, fontweight="bold")
        tidy(ax)
    fig.legend(*axs[0].get_legend_handles_labels(), loc="upper center", ncol=2,
               bbox_to_anchor=(.62, 1.01), frameon=False, fontsize=16)
    save(fig, "qwen-paired", recorded, [DATA["models"][k]["source_path"] for k in recorded])


def projection():
    entries = [(m,l) for m in ["qwen9b", "qwen2b"] for l in ["13", "14"]]
    values = [100*DATA["target_channels"][m]["layers"][l]["reconstruction_fraction"] for m,l in entries]
    labels = [f"{'9B' if m=='qwen9b' else '2B'} · L{l}  /  N{DATA['target_channels'][m]['layers'][l]['index']}" for m,l in entries]
    fig, ax = plt.subplots(figsize=(14, 4.6))
    fig.subplots_adjust(left=.22, right=.95, top=.91, bottom=.19)
    y=np.arange(4)
    ax.barh(y, [100]*4, color="#edf1f3", height=.47, zorder=1)
    ax.barh(y, values, color=CORAL, height=.47, zorder=2)
    for yy, value in zip(y,values):
        ax.text(value+1.2, yy, f"{value:.2f}%", va="center", fontsize=21, fontweight="bold", color=CORAL)
    ax.set_yticks(y,labels,fontsize=17)
    ax.set_xlim(0,100)
    ax.set_xticks([0,25,50,75,100])
    ax.set_ylim(3.5,-.5)
    ax.set_xlabel("几何重建比例  ρ / %",labelpad=13,fontsize=18)
    tidy(ax)
    save(fig,"projection",dict(zip(labels,values)),[DATA["target_channels"][m]["source_path"] for m in ["qwen9b","qwen2b"]])


def llama_gate():
    gate=DATA["llama_stage1_gate"]
    vals=[gate["metrics"][t] for t in TASKS]
    x=np.array([v["damage_pp"] for v in vals])
    low=np.array([v["lower_pp"] for v in vals])
    high=np.array([v["upper_pp"] for v in vals])
    assert all(v["nominal_level"]==.9875 for v in vals)
    fig,ax=plt.subplots(figsize=(14,4.8))
    fig.subplots_adjust(left=.15,right=.75,top=.86,bottom=.18)
    y=np.arange(4)
    ax.axvline(gate["threshold_pp"],ls="--",lw=1.6,color="#89969f",zorder=1)
    ax.text(gate["threshold_pp"]+1,-.57,"5 pp 门阈值",fontsize=14,color="#657987",ha="left")
    ax.errorbar(x,y,xerr=[x-low,high-x],fmt="o",ms=10,color=CORAL,elinewidth=2.8,capsize=7,capthick=2,zorder=3)
    ax.set_yticks(y,NAMES,fontsize=17)
    ax.set_xlim(0,100)
    ax.set_xticks([0,25,50,75,100])
    ax.set_ylim(3.5,-.8)
    ax.set_xlabel("能力下降 / pp",fontsize=18,labelpad=12)
    tidy(ax)
    ax.text(1.04,1.03,"下降 [98.75% CI]",transform=ax.transAxes,fontsize=16,ha="left")
    for yy, xx, ll, hh in zip(y,x,low,high):
        ax.text(1.04, yy, f"{xx:.1f}  [{ll:.1f}, {hh:.1f}]",transform=ax.get_yaxis_transform(),va="center",ha="left",fontsize=17)
    save(fig,"llama-gate",{t:v for t,v in zip(TASKS,vals)},[gate["source_path"]])


def random_diagnostic():
    arms=["T_0","true_S_recipe","random1_S_recipe","random2_S_recipe","random3_S_recipe"]
    rows=[(m,t) for m in ["qwen9b","qwen2b"] for t in ["mmlu","arc_challenge"]]
    vals=np.array([[DATA["diagnostics"][m]["conditions"][a][t] for a in arms] for m,t in rows])
    labels=[f"{'9B' if m=='qwen9b' else '2B'} · {'MMLU' if t=='mmlu' else 'ARC-C'}  (n=32)" for m,t in rows]
    fig,ax=plt.subplots(figsize=(14,4.8))
    fig.subplots_adjust(left=.235,right=.89,top=.92,bottom=.23)
    cmap=LinearSegmentedColormap.from_list("capability",[PAPER,"#aec4d5",BLUE])
    im=ax.imshow(vals,vmin=0,vmax=100,cmap=cmap,aspect="auto")
    ax.set_yticks(range(4),labels,fontsize=16)
    ax.set_xticks(range(5),["原版\nT₀","真实源\nS_recipe","随机源 1\nS_recipe","随机源 2\nS_recipe","随机源 3\nS_recipe"],fontsize=16)
    ax.tick_params(length=0,pad=11)
    ax.get_xticklabels()[1].set_color(CORAL)
    for i in range(4):
        for j in range(5):
            value=f"{vals[i,j]:.3f}".rstrip("0").rstrip(".")
            ax.text(j,i,value,ha="center",va="center",fontsize=21,color="white" if vals[i,j]>56 else INK,fontweight="bold")
    ax.set_xticks(np.arange(-.5,5,1),minor=True)
    ax.set_yticks(np.arange(-.5,4,1),minor=True)
    ax.grid(which="minor",color=PAPER,linewidth=4)
    ax.axhline(1.5,color=PAPER,lw=9)
    ax.tick_params(which="minor",length=0)
    for s in ax.spines.values():s.set_visible(False)
    cb=fig.colorbar(im,cax=fig.add_axes([.915,.23,.018,.69]),ticks=[0,25,50,75,100])
    cb.ax.set_title("正确率 / %",fontsize=13,pad=8)
    cb.outline.set_visible(False)
    save(fig,"random-diagnostic",{"row_labels":labels,"arms":arms,"percent":vals.tolist()},[DATA["diagnostics"][m]["source_path"] for m in ["qwen9b","qwen2b"]])


if __name__=="__main__":
    damage_heatmap()
    qwen_paired()
    projection()
    llama_gate()
    random_diagnostic()
    MANIFEST["generator_sha256"]=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    (OUT/"manifest.json").write_text(json.dumps(MANIFEST,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({"charts":list(MANIFEST["charts"]),"verified_sources":len(CHECKS)},ensure_ascii=False))
