# Acupuncture

研究成品语言模型中稀疏神经元干预的行为变化、能力损伤、机制与跨模型迁移。

**唯一主仓库：[yuxiexiong/acupuncture](https://github.com/yuxiexiong/acupuncture)。** 自 2026-10-26 起，本项目的代码、实验协议、研究笔记、结果和后续工作统一保存在这里。本地项目根目录为 `/Users/ruizhixu/Documents/ChatGPT/acupuncture`。

## 从这里开始

| 材料 | 入口 |
|---|---|
| 当前研究状态、机制线索与迁移计划 | [研究状态与后续方向](docs/RESEARCH_STATUS.zh-CN.md) |
| X 线索统一入口：历次原帖、全部已转录配方、定位方法、复现与失败、可视化工具 | [X 线索汇总](docs/literature/x-clues-summary.zh-CN.md) |
| 2B/4B/9B 全层单针调查：880条件、7,064份原文已完整交付，实耗4小时1分12秒 | [并排原文](experiments/layer-survey-toy-v1-2026-10-27/delivery-r01/paired_raw.html) / [执行与核验记录](experiments/layer-survey-toy-v1-2026-10-27/EXECUTION.zh-CN.md) / [协议](experiments/layer-survey-toy-v1-2026-10-27/PROTOCOL.zh-CN.md) |
| 两针能力损伤的最小因果定位：首轮完成，有局部修复线索，根因尚未确认 | [首轮结果](experiments/root-cause-toy-v1-2026-10-26/RESULTS.zh-CN.md) / [执行状态与实际耗时](experiments/root-cause-toy-v1-2026-10-26/EXECUTION.zh-CN.md) / [执行合同](experiments/root-cause-toy-v1-2026-10-26/CONTRACT.zh-CN.md) |
| 判断内容与报告标签的追加诊断：合同/代码/CPU验收完成，正式运行暂停 | [本轮合同](experiments/judgment-report-toy-v1-2026-10-26/CONTRACT.zh-CN.md) / [准备验收与阶段说明](experiments/judgment-report-toy-v1-2026-10-26/EXECUTION.zh-CN.md) |
| 4B→9B、4B→2B 迁移 toy：机器阶段完成；行为盲评待办 | [最终机器报告](experiments/transfer-toy-v1-2026-10-26/RESULTS.zh-CN.md) / [原文、成绩与盲评包入口](experiments/transfer-toy-v1-2026-10-26/delivery-r01/index.html) / [冻结协议](experiments/transfer-toy-v1-2026-10-26/PROTOCOL.zh-CN.md) |
| 四项能力小面板已完成：1,000 / 200 / 100 / 100 题，原版/EVO 成绩与实际耗时 | [最终结果](experiments/capability-screen-v3-2026-10-26/RESULTS.zh-CN.md) / [运行协议](experiments/capability-screen-v3-2026-10-26/PROTOCOL.zh-CN.md) |
| 四项全量能力对照（已按用户要求停止，保留原始证据） | [旧运行协议](experiments/capability-damage-v2-2026-10-26/PROTOCOL.zh-CN.md) / [精简方案 v2](docs/damage-evaluation-plan-v2.zh-CN.md) / [原方案 v1](docs/damage-evaluation-plan-v1.zh-CN.md) |
| 旧全量车队的历史说明（已停止） | [车队说明](experiments/capability-damage-v2-2026-10-26/CONVOY.zh-CN.md) |
| 一小时预算讨论及数学、代码各扩至 100 题的后续修订 | [时间分配与精度限制](docs/damage-evaluation-one-hour-plan.zh-CN.md) |
| 两个坐标的源码/激活工程核查与相关工作的损伤指标 | [原始来源核查记录](docs/literature/source-and-damage-audit-2026-10-26.json) |
| 用户提供的 HanLab 经验总结（原文） | [HanLab经验总结.md](docs/HanLab经验总结.md) / [导入与 SHA-256 校验](docs/hanlab-summary-import-2026-10-26.json) |
| HanLab 机制实验的原论文核查：五篇的竞争解释、对照与证据边界 | [原文核查与设计借鉴](docs/literature/hanlab-mechanism-primary-audit-2026-10-26.zh-CN.md) |
| 文献查重与既有工作核查（26篇，含证据边界） | [mechanistic-interventions-2026-10-26.json](docs/literature/mechanistic-interventions-2026-10-26.json) |
| 跨规模、跨家族的干预迁移：方法、效果与对应关系边界 | [迁移文献专项核查](docs/literature/cross-model-intervention-transfer-2026-10-26.zh-CN.md) |
| lyra 原帖、作者回复与评论区反查 | [原帖与评论区调查报告](docs/literature/lyra-x-thread-2026-10-26.zh-CN.md) |
| lyra 评论区第二轮：新增回复、50题公开制品及人格/情绪研究核查 | [第二轮调查报告](docs/literature/lyra-x-thread-round2-2026-10-26.zh-CN.md) |
| Abhinav 神经元配方：9类表现、10组配置、22个坐标，含截图剂量 | [中文清单](docs/literature/vashinthewild-neuron-catalog-2026-10-26.zh-CN.md) / [结构化索引](docs/literature/vashinthewild-neuron-catalog-2026-10-26.json) |
| 10/27 原帖与配方增量：新组合、上传主题、定位方法、失败发现与 Zoo 出处边界 | [更新核查](docs/literature/x-recipe-updates-2026-10-27.zh-CN.md) / [结构化清单](docs/literature/x-recipe-updates-2026-10-27.json) |
| 10/27 可视化分享复查：头与 token 视图、调试器、Neuralese 更新及 HF 网格含义 | [工具与讨论核查](docs/literature/x-visualization-updates-2026-10-27.zh-CN.md) |
| Qwen3.5-4B 首轮实验全部代码与记录 | [实验目录](experiments/qwen35-neuron-steering-2026-10-25/) |
| 前 24 题全部原文并排 | [paired_raw.html](experiments/qwen35-neuron-steering-2026-10-25/raw-corpus-cpu-bf16-r01/paired_raw.html)（下载后用浏览器打开） |
| 原版 / 干预版原始语料 | [original.raw.jsonl](experiments/qwen35-neuron-steering-2026-10-25/raw-corpus-cpu-bf16-r01/original.raw.jsonl) / [modified.raw.jsonl](experiments/qwen35-neuron-steering-2026-10-25/raw-corpus-cpu-bf16-r01/modified.raw.jsonl) |
| 24 题定性对比 | [comparison24.html](experiments/qwen35-neuron-steering-2026-10-25/comparison24.html) / [结构化分析](experiments/qwen35-neuron-steering-2026-10-25/comparison24.json) |
| 原作者两个神经元的公开缓存证据 | [author_cache_two_neurons.json](experiments/qwen35-neuron-steering-2026-10-25/literature-2026-10-26/author_cache_two_neurons.json) |
| RACE / GSM8K / LogiQA 快速对照成绩 | [完整报告](experiments/qwen35-neuron-steering-2026-10-25/benchmark-quick-2026-10-26/RESULTS.zh-CN.md) / [300 题双版本原文](experiments/qwen35-neuron-steering-2026-10-25/benchmark-quick-2026-10-26/paired_answers.html) / [协议](experiments/qwen35-neuron-steering-2026-10-25/benchmark-quick-2026-10-26/PROTOCOL.zh-CN.md) |
| 迁移来源、文件大小与 SHA-256 | [初始迁移](migration/2026-10-26.json) / [评测完成后补充](migration/2026-10-26-benchmark-completion.json) |

## 已完成与证据边界

- 源模型为 `Qwen/Qwen3.5-4B`，固定 revision `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`。
- 首轮使用动态激活干预：零起始索引 L14/N8949 +1、L13/N7956 −1；没有在成品模型上执行永久权重修改。
- 用户要求完成 Q24 后停止。24 题双方的 512 / 1024 token 尝试共保存 96 条输出；Q25–Q40 未启动。两次预算的输出是前缀关系，不能当独立重复。
- 原运行仅以 248044 停止，而聊天结束标记为 248046。分析已经区分主回答与结束后的续写；旧原文、配置和收据完整保留。
- 作者公开代码采用固定参考尺度，我们首轮逐题校准；二者不能称为完全相同的实验设置。
- 三项英文基准各完成固定 100 题，共 600 份回答，完整收据、原文及评分已复核。严格格式评分的原版/EVO 为 RACE 89%/0%、GSM8K 79%/0%、LogiQA 2.0 70%/0%；两臂统一的事后显式答案提取分别为 89%/11%、83%/0%、70%/15%。这是子集成绩；严格零分混合了格式失遵循、截断与答错，不能解释成全部能力消失。
- 本轮基准同时使用 248044 和 248046 停止，修正了首轮旧语料的停止条件。EVO 为动态激活干预，权重未改写；其 300 份回答有 295 份达到生成上限。当前结果不支持“能力保持、只变坏”。
- 4B→9B、4B→2B 迁移及各自四项 1,400 题能力面板于 2026-10-26 12:28（北京时间）全部完成。9B 的 MMLU / ARC-C / GSM8K / HumanEval 为 70.06→25.39 / 71.50→30.00 / 93→0 / 70→0%；2B 为 54.06→46.00 / 52.50→31.00 / 61→0 / 37→3%。正式评分技术失败为 0，9,681 个原始文件已完整取回并校验。结果支持这两模型中的能力损伤效应迁移；结构化有害行为仍待双人盲评，特异性和根因未证实。机器阶段共 6 小时 40 分 12 秒；根因 toy 已另获授权，于北京时间 14:19:52 启动。见[最终报告与证据边界](experiments/transfer-toy-v1-2026-10-26/RESULTS.zh-CN.md)。

## 复用代码

历史脚本及其 SHA-256 保持原样，以便复核实验。`run_collect.sh`、`run_cpu.sh` 和能力基准启动脚本包含历史服务器路径；它们不是可直接在任意机器运行的通用启动器。`probe.py` 的旧 8 题入口也不是本轮 24 题采集入口。旧 `run_cpu.sh` 还引用 `qwen35-files.json`，当前提供的清单名为 `model-files.json`；这是保留的历史脚本差异。

不加载模型的导出及解析检查：

```sh
cd experiments/qwen35-neuron-steering-2026-10-25
python3 test_export_raw.py
python3 test_benchmark_quick.py
python3 test_benchmark_quick_batched.py
python3 benchmark-quick-2026-10-26/test_scoring_crosscheck.py
```

模型推理环境及版本以各次运行的 receipt 为准。`test_probe.py` 和 `test_collect_raw.py` 需要 PyTorch 等依赖；前者使用小矩阵，后者使用合成生成器。`test_stop_after_q24.py` 使用 Linux `/proc`，不适用于 macOS。

## 数据与存储

本仓库保存全部项目代码、固定评测样本、原始模型回答、日志、分析和来源清单。第三方完整基准下载包已复制到本地项目，但不重复提交到 Git；来源 URL 和 SHA-256 保存在 [data_manifest.json](experiments/qwen35-neuron-steering-2026-10-25/benchmark-quick-2026-10-26/data_manifest.json)。[prepare_data.py](experiments/qwen35-neuron-steering-2026-10-25/benchmark-quick-2026-10-26/prepare_data.py) 处理已下载的数据，不负责下载。

模型权重与大型上游缓存留在外部存储，仓库记录版本、地址和校验信息；不提交凭据或运行环境。第三方模型、数据和代码继续受各自原始许可约束。

原 `stealthiness/research/qwen35-neuron-steering-2026-10-25` 保留为迁移前副本，不再作为本项目的新工作根目录。历史收据中的路径是当时运行记录，未因改名而重写。
