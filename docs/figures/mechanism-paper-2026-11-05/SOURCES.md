# 论文图的数据来源

`python3 -I make_figures.py DATA_DIR OUT_DIR`，无第三方依赖，输出 SVG。DATA_DIR 里放下列分析文件的副本（文件名不变）：

| 图 | 分析文件（均在 `experiments/<目录>/analysis/`） |
|---|---|
| 图 1 | 示意图；数字取自图 2 的来源 |
| 图 2 | `cache-native-write-readout-v1-2026-11-05/enum-offline-r01.json`、`nwr-readouts-r01.json` |
| 图 3 | `cache-native-carrier-comparison-v1-2026-11-03/ncc-readouts-r01.json`、`cache-native-pair-combination-v1-2026-11-03/npc-readouts-r01.json` |
| 图 4 | **数值抄自报告，不是从 JSON 读取**：NVB、NMT v2、SIT、CGV r02 各报告的正文表；脚本中以 `REPORT` 注释标出 |
| 图 5 | `window-recovery-win01-v1-2026-11-04/win-readouts-r01.json`、`window-prediction-win02-v1-2026-11-04/w2-readouts-r01.json` |
| 图 6 | `kvpre-content-kvc01-v1-2026-11-05/kvc-readouts-r01.json` |
| 图 7 | `cache-native-write-confirm-v1-2026-11-05/nwc-readouts-r01.json` |

颜色：正确＝蓝 `#2a78d6`，明确错号＝橙 `#eb6834`，其他＝青 `#1baf7a`，停止或无答案＝中性灰。三个色相用色觉缺陷分离度脚本验证过（相邻最差 ΔE 9.2）。每张图在生成后转成 PNG 检查过版面。图内文字为英文，正文图注为中文。

2026-11-06：v1.3仅同步图1／图2的状态更新、供体／接收者及原生路径边界措辞，并由同一脚本重建；计数、几何布局与其余四图不变。此次未新增科学数据或分析。
