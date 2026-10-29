# 实验目录：按研究问题查找

更新：2026-10-28。这里覆盖 `experiments/` 下全部 **22 个目录**。中文名称说明实际用途；目录中的英文名和日期是固定实验身份，保留原路径以维持合同、代码、收据和哈希引用。

找具体回答请先看 [原始回答与实验数据索引](../docs/原始回答与实验数据索引.md)；看整体结论请读 [导师版实验总结](../docs/Acupuncture_实验总结_导师版_2026-10-28.md)。状态按已归档的完成或停止证据整理，旧执行文档中的“排队／运行中”是历史快照。

## 一、全层单通道扫描与剂量比较

| 实验名称 | 模型与范围 | 状态 | 结果入口 |
| --- | --- | --- | --- |
| [Qwen：全层每层十点，单针 +1 扫描](layer-survey-toy-v1-2026-10-27/) | 2B／4B／9B，共 880 个点、8 道题 | 已完成：7,040 干预＋24 原版 | [并排原文](layer-survey-toy-v1-2026-10-27/delivery-r01/paired_raw.html) · [观察报告](layer-survey-toy-v1-2026-10-27/qualitative-pass-r01/FIRST_PASS.zh-CN.md) |
| [Qwen：每层一点，五档正剂量](layer-dose-survey-toy-v1-2026-10-27/) | 2B／4B／9B，原十点中固定选 88 点 | 已完成：新增 2,816 回答，复用原版与 +1 | [六栏原文](layer-dose-survey-toy-v1-2026-10-27/delivery-r01/paired_raw.html) · [完成核验](layer-dose-survey-toy-v1-2026-10-27/FORMAL_EXECUTION.zh-CN.md) |
| [Qwen：同点补齐五档负剂量](layer-negative-dose-survey-toy-v1-2026-10-27/) | 同上 88 点，正负完全配对 | 已完成：新增 3,520 回答；交付同时包含正负及原版 | [十一栏原文](layer-negative-dose-survey-toy-v1-2026-10-27/delivery-r01/paired_raw.html) · [观察报告](layer-negative-dose-survey-toy-v1-2026-10-27/qualitative-pass-r01/FIRST_PASS.zh-CN.md) |
| [Llama：全层每层十点，单针 +1 扫描](llama31-layer-survey-v1-2026-10-28/) | Llama 3.1 8B，32 层、320 个点 | 已完成：2,560 干预＋8 原版 | [并排原文](llama31-layer-survey-v1-2026-10-28/delivery-r01/paired_raw.html) · [观察报告](llama31-layer-survey-v1-2026-10-28/qualitative-pass-r01/FIRST_PASS.zh-CN.md) |
| [Llama：每层一点，正负十档剂量](llama31-single-point-dose-survey-v1-2026-10-28/) | Llama 3.1 8B，每层原十点中固定选 1 点 | 已完成：新增 2,304 回答，复用 264 来源 | [十一栏原文](llama31-single-point-dose-survey-v1-2026-10-28/delivery-r01/paired_raw.html) · [观察报告](llama31-single-point-dose-survey-v1-2026-10-28/qualitative-pass-r01/FIRST_PASS.zh-CN.md) |

上述正式来源去重后，Qwen 合计 **13,400** 条，Llama **4,872** 条。每层只有一个选定点做完整剂量比较；其余九点仅有 +1。不同交付文件复用原版和 +1，不能直接把文件行数相加。

## 二、内部计算轨迹：沿层和生成步骤观察变化

| 实验名称 | 注入范围；观察范围 | 状态 | 合同与验收 |
| --- | --- | --- | --- |
| [A：Qwen 早层内部轨迹首批](early-layer-mechanism-v1-2026-10-28/) | 2B／4B 注入 L0–L3，9B 注入 L0–L5；观察全部模型层 | 已完成：2,152 正式＋42 预检 | [合同](early-layer-mechanism-v1-2026-10-28/CONTRACT.zh-CN.md) · [归档核验](early-layer-mechanism-v1-2026-10-28/archive-r01/verification.json) |
| [B：补齐 Qwen 三模型前六层及 4B 全层轨迹](layer-trace-extension-v1-2026-10-28/) | 补 2B／4B L4–L5，再补 4B L6–L31；观察全部模型层 | 已完成：4,560 正式，不重跑旧来源 | [合同](layer-trace-extension-v1-2026-10-28/CONTRACT.zh-CN.md) · [归档核验](layer-trace-extension-v1-2026-10-28/archive-r01/verification.json) |
| [C：Llama 前六层内部轨迹](llama31-early-layer-trace-v1-2026-10-28/) | Llama 3.1 8B 注入 L0–L5；观察全部 32 层 | 已完成：920 正式＋14 预检 | [合同](llama31-early-layer-trace-v1-2026-10-28/CONTRACT.zh-CN.md) · [归档核验](llama31-early-layer-trace-v1-2026-10-28/archive-r01/verification.json) |

| [早层输入约束、停止竞争与异常维持](early-input-control-v1-2026-10-29/) | 4B；L0–3/L12–15/L24–27 原生两通道与两条共同方向；时段、撤针、局部替换；开发+新题确认 | 已完成：11,890 正式记录，盲读锁定；冻结预测 C1–C6 均成立；局部替换无修复 | [结果报告](early-input-control-v1-2026-10-29/REPORT.zh-CN.md) · [合同](early-input-control-v1-2026-10-29/CONTRACT.zh-CN.md) · [执行记录](early-input-control-v1-2026-10-29/EXECUTION.zh-CN.md) |
| [早层停嘴时题目事实是否仍在（零 GPU）](early-stop-knowledge-readout-v1-2026-10-29/) | 4B；复用 early-input-control 强制续写候选分数 | 已完成：“知道但停嘴”被否定，早层 ±1 事实敏感度几乎消失；含 2606.11375 口径核对 | [结果](early-stop-knowledge-readout-v1-2026-10-29/RESULTS.zh-CN.md) · [合同](early-stop-knowledge-readout-v1-2026-10-29/CONTRACT.zh-CN.md) |
| [早层问题依赖度：既有回答的零 GPU 再分析](early-layer-question-dependence-v1-2026-10-28/) | 四模型全层；八题首 token 多样性、首步 EOS、剂量阶梯 | 已完成：只读既有归档，无新推理 | [说明与输出](early-layer-question-dependence-v1-2026-10-28/README.zh-CN.md) |

三批共 **7,632 条正式轨迹**，是上面既有回答的内部重放观测，不是新增独立题目。最终 2B／9B／Llama 各覆盖前六个注入层，4B 覆盖全部 32 个注入层。每条均观察全部层的组件摘要。原始回答、收据和校验清单在 Git；压缩内部轨迹保存在本地和服务器，见 [大文件保存与恢复说明](../migration/2026-10-28-full-results-git-r01/README.zh-CN.md)。

## 三、历史双针、能力评测、迁移与修复

| 实验名称 | 模型与研究内容 | 状态与边界 | 结果入口 |
| --- | --- | --- | --- |
| [首轮双针语料及三项快速基准](qwen35-neuron-steering-2026-10-25/) | Qwen 3.5 4B；两针同时干预 | 原语料按要求止于 Q24，96 条含两种长度尝试；三项基准 600 回答已完成 | [24 题原文](qwen35-neuron-steering-2026-10-25/raw-corpus-cpu-bf16-r01/paired_raw.html) · [三项基准结果](qwen35-neuron-steering-2026-10-25/benchmark-quick-2026-10-26/RESULTS.zh-CN.md) |
| [4B：四项固定能力面板](capability-screen-v3-2026-10-26/) | MMLU／ARC-C／GSM8K／HumanEval | 已完成：1,400 对题；含已核验的旧结果复用 | [结果与计数](capability-screen-v3-2026-10-26/RESULTS.zh-CN.md) · [协议](capability-screen-v3-2026-10-26/PROTOCOL.zh-CN.md) |
| [同族迁移：4B → 9B／2B](transfer-toy-v1-2026-10-26/) | 位置映射、小诊断、行为原文及各 1,400 题能力面板 | 机器阶段完成；结构化行为盲评未完成 | [结果与限制](transfer-toy-v1-2026-10-26/RESULTS.zh-CN.md) · [原文和评分](transfer-toy-v1-2026-10-26/delivery-r01/index.html) |
| [跨家族迁移：4B → Llama 3.1 8B](cross-family-transfer-toy-v1-2026-10-26/) | 稠密迁移与四项能力评测 | 阶段一完成；阶段二未运行，后继队列已按要求停止 | [阶段一门槛结果](cross-family-transfer-toy-v1-2026-10-26/runs/llama31-r01/stage1/gate.json) · [停止收据](cross-family-transfer-toy-v1-2026-10-26/runs/llama31-r01/user-stop-20261027-r02/receipt.json) |
| [迁移后三道固定问题的回答检查](transfer-behavior-q3-v1-2026-10-26/) | Qwen 9B／2B 原版与迁移版；4B 作历史参照 | 已完成：12 份新原文；开发案例，不是总体行为发生率 | [完成记录](transfer-behavior-q3-v1-2026-10-26/COMPLETION.zh-CN.md) · [交付文件](transfer-behavior-q3-v1-2026-10-26/delivery-r01/) |
| [4B 双针损伤：拆针与十个候选的局部修复](root-cause-toy-v1-2026-10-26/) | 17 个拆针／随机／剂量条件，十个候选修复及反向重现 | 首轮完成；有局部修复线索，未确认唯一根因或功能区 | [结果与反例](root-cause-toy-v1-2026-10-26/RESULTS.zh-CN.md) · [合同](root-cause-toy-v1-2026-10-26/CONTRACT.zh-CN.md) |

## 四、可视化、报告与模型资产

| 目录名称 | 内容与适用模型 | 状态／推荐用途 |
| --- | --- | --- |
| [多模型三维 Explorer 与二维观察台](neuron-explorer-multimodel-v2-2026-10-26/) | Qwen 2B／4B／9B、Llama 3.1 8B；原文、层／步骤差分、token 竞争 | **当前可视化入口**；[二维使用说明](neuron-explorer-multimodel-v2-2026-10-26/analysis-view-r01/README.zh-CN.md) · [三维使用说明](neuron-explorer-multimodel-v2-2026-10-26/trace-view-r01/README.zh-CN.md)。本地只读已有结果；传播曲面草稿尚未验收 |
| [原作者 Explorer 的 4B 复现](neuron-explorer-reproduction-v1-2026-10-26/) | Qwen 3.5 4B；原界面、缓存及有限实时推理验收 | 历史软件复现已完成；远端模型服务已停止，[停止证据](neuron-explorer-multimodel-v2-2026-10-26/shutdown-2026-10-27-r01.json)。旧 README 地址和 PID 是历史记录 |
| [早期调查、修复和迁移分析页](neuron-explorer-analysis-v1-2026-10-26/) | Qwen 2B／4B／9B；早期扫描结果与旧双针候选 | 历史分析页保留；独立差分采集器仅准备。最新正负剂量及四模型轨迹请用当前入口 |
| [导师报告：生成代码与内容核对](advisor-report-v1-2026-10-28/) | 汇总现有各轮实验，含原文示例及图表 | 报告已交付；[核对记录](advisor-report-v1-2026-10-28/audit.json) · [导师 MD](../docs/Acupuncture_实验总结_导师版_2026-10-28.md) · [导师 HTML](../docs/Acupuncture_实验结果_导师展示_2026-10-28.html) |
| [模型资产：来源、下载与完整性记录](model-assets-2026-10-26/) | 模型版本、下载尝试、复用与校验；具体资产见 [来源清单](model-assets-2026-10-26/sources.json) | 保存资产准备证据，不是行为实验；[完成核验](model-assets-2026-10-26/completion-verification.json)。权重本身不进 Git |

## 五、停止或尚未正式运行的独立批次

| 实验名称 | 模型与原计划 | 当前归档状态 |
| --- | --- | --- |
| [4B 旧版全量能力评测](capability-damage-v2-2026-10-26/) | 四项全量基准的旧计划 | 已停止；保留 10,034 对完整 MMLU 及部分记录，其余三项未启动。不能标为全量完成；[停止归档](capability-damage-v2-2026-10-26/user-stop-20261026-r01/) |
| [Llama 旧版“每层十点 × 十档剂量”合并实验](llama31-layer-dose-survey-v1-2026-10-28/) | Llama 3.1 8B；被独立十点与单点剂量实验取代 | 已停止；保留 479 份回答（471 干预＋8 原版），未混入后续正式结果；[停止收据](llama31-layer-dose-survey-v1-2026-10-28/user-stop-split-r01/receipt.json) |
| [4B 判断内容与报告标签的分离诊断](judgment-report-toy-v1-2026-10-26/) | 旧双针与 C05／C01 候选的追加诊断 | 合同、代码与 CPU 验收已准备，正式运行暂停；[合同](judgment-report-toy-v1-2026-10-26/CONTRACT.zh-CN.md) · [准备记录](judgment-report-toy-v1-2026-10-26/EXECUTION.zh-CN.md) |

## 目录里的常见文件名

| 文件／目录 | 应怎样读 |
| --- | --- |
| `PROTOCOL`、`CONTRACT` | 当时固定的实验设计与边界；不代表已经运行 |
| `EXECUTION`、`readiness/` | 执行经过、授权与测试；按时间区分历史快照 |
| `delivery-r01/` | 面向阅读和复核的导出：原文、配对页面、评分、核验 |
| `survey-r01/`、`runs/`、`archive-r01/` | 实际运行或回传归档；不要把相同来源的副本重复计数 |
| `qualitative-pass-r01/` | 首轮模型辅助阅读、逐层笔记及覆盖检查，不是独立人工盲评 |
| `receipt.json`、`verification.json`、`freeze.json` | 实际收据、验收和冻结身份；保留原始字节以便追溯 |

`toy`、`early`、`v1` 等是历史身份的一部分，不用于判断当前覆盖或完成程度。精确范围以上表和对应合同为准。
