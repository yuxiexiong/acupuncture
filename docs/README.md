# 项目文档目录

**资产盘点后的形成检验｜2026-10-31：** [深层缓存形成条件方案 v2 与完整自查](cache-formation-mechanism-next-step-plan-v2-2026-10-31.zh-CN.md)。承接 E2，具体定义入口抵消、浅层过去状态固定、统一评分背景、不同结果的认识增量及退出条件；设计逻辑自查通过，工程与耗时未验收，未运行模型或 GPU。下方旧方案状态保留其历史身份。

**实验设计交付要求｜2026-10-31：** 所有后续新设计与实质修订先过[实验设计自查规范](experiment-design-self-check.zh-CN.md)，未通过先内部修正。当前案例：[深层缓存形成 A/B 修正版及自查](cache-formation-ab-self-review-v1-2026-10-31.zh-CN.md)，设计逻辑通过，工程未验收、未运行、未授权 GPU。下列较早的“当前/未执行”描述是历史快照，最新状态以[研究状态](RESEARCH_STATUS.zh-CN.md)顶部为准。

[返回项目首页](../README.md) · [回答原文索引](原始回答与实验数据索引.md) · [实验目录](../experiments/README.md)

[缓存形成机制 CFM：有效计划、命名与审查](cache-formation-mechanism-plan-index-2026-10-31.zh-CN.md)。CFM-S1/S2/S3 均为未执行计划，与历史已完成的“阶段一／二”分开命名。

## 当前立项与查重｜2026-10-30

Acupuncture 当前有两条分别立项的研究线。缓存机制线解释干预的状态承载与延续；稳定副作用控制线研究目标效果、任务代价和跨输入可靠性的改善。当前前者的直接机制证据更完整；二者都不以回避近邻为立项依据。以下是研究草案，不是实验执行授权。

| 研究线 | 立项文档 | 查重文档 |
| --- | --- | --- |
| 缓存机制线 | [痛点、证据、贡献目标与缺口](cache-mechanism-proposal-2026-10-30.zh-CN.md) | [缓存拆分、状态移植、WriteSAE 等近邻对照](literature/cache-mechanism-prior-art-2026-10-30.zh-CN.md) |
| 稳定副作用控制线 | [目标效果、任务代价、已有基础与缺口](stable-control-proposal-2026-10-30.zh-CN.md) | [DSI、CNA、COAST、SteerScope 等方法与评价对照](literature/stable-control-prior-art-2026-10-30.zh-CN.md) |

缓存机制线分阶段实验：[CFM-S1｜原始轨迹与状态形成分析计划 v1](cache-formation-mechanism-s1-native-trace-plan-v1-2026-10-31.zh-CN.md)（编号 `CFM-S1-v1-20261031`）→ [实验目录](../experiments/cache-formation-mechanism-s1-native-trace-v1-2026-10-31/)。

缓存机制线结果资产盘点（到 CFM-E2 为止，修正后）：[机制片段、支撑资产、覆盖边界与缺口](cache-formation-mechanism-asset-inventory-v1-2026-10-31.zh-CN.md)。盘点与覆盖核对，不是新颖性证明。

当前项目定位以[首页](../README.md#当前两条研究线)和上述文档为准。下方旧报告、历史方案和运行快照保留当时内容，不能因仍可点击而视为当前计划或新运行授权。

## 报告与研究状态

| 清楚名称 | 文件 | 用途 |
| --- | --- | --- |
| **完整实验总结｜导师阅读版｜2026-10-28** | [Acupuncture_实验总结_导师版_2026-10-28.md](Acupuncture_实验总结_导师版_2026-10-28.md) | 独立阅读；实验记录、数字、原文案例、观察及限制 |
| **实验结果与线索｜导师图文展示｜2026-10-28** | [Acupuncture_实验结果_导师展示_2026-10-28.html](Acupuncture_实验结果_导师展示_2026-10-28.html) | 图表、结构图、剂量原文；下载后打开 |
| 既有结果与研究线索｜历史总报告 | [EXPERIMENT_RESULTS_MASTER.zh-CN.md](EXPERIMENT_RESULTS_MASTER.zh-CN.md) | 保留当时的汇总与原始证据链接；当前综合展示优先看上面两份 |
| **下一阶段建议｜全深度剂量单位、输入依赖崩溃判据与安全剂量上限表｜2026-10-28** | [next-stage-dose-calibration-proposal-2026-10-28.zh-CN.md](next-stage-dose-calibration-proposal-2026-10-28.zh-CN.md) | 建议稿，未冻结合同；早层现象再解读、三个合同、停掉与搁置清单 |
| 研究讨论与状态更新记录 | [RESEARCH_STATUS.zh-CN.md](RESEARCH_STATUS.zh-CN.md) | 含历次计划和旧运行快照；是否完成以对应最终收据为准 |
| 迁移实验｜阶段汇报幻灯片 | [transfer-slides-2026-10-26/index.html](transfer-slides-2026-10-26/index.html) | 当时的迁移证据、对照和解释边界 |

## 回答、内部数据和可视化

| 文件 | 内容 |
| --- | --- |
| [原始回答与实验数据索引](原始回答与实验数据索引.md) | 按模型与实验找 JSONL、并排回答、评分、Hook 记录 |
| [可视化工具使用指南](可视化工具使用指南.md) | 三维层图、二维剂量/热图/曲线、历史实验库的区别与启动方法 |
| [模型通道与两层计算演示](model-anatomy-2026-10-27/two-layer-walkthrough.html) | 教学用计算示例，不能当作实测模型结果 |
| [通道传播示意](model-anatomy-2026-10-27/channel-propagation.html) | 理解模型结构的辅助页面 |
| [Git 与外部大文件归档说明](../migration/2026-10-28-full-results-git-r01/README.zh-CN.md) | 已上传内容、本地/服务器大文件、校验清单与恢复路径 |

## 外部研究与原帖线索

外部论文、作者与评论者的报告单独归档；它们不是本项目完成的实验。

- [剂量语义与崩溃判据：七步查重报告（2026-10-28）](literature/dose-calibration-related-work-audit-2026-10-28.zh-CN.md)：下一阶段方向的覆盖图、逐篇对照与边界申报；核心对手为 Liu 2606.19831 与 2602.02712。
- [早层失稳机制归因：七步查重报告（2026-10-28 晚）](literature/early-layer-mechanism-related-work-audit-2026-10-28.zh-CN.md)：主线保留早层机制后的覆盖报告；几何收拢已被 2602.02712 命题 4.1 与 2510.06477 定理 1 蕴含，现象在替换与删层上已被观察，sink 与 massive activation 形成层是 C5 的竞争解释；含两个零 GPU 检验与对合同 1 的建议。
- [候选 B（状态滞留）与 S（sink / L3 边界）：七步查重报告（2026-10-29）](literature/next-stage-state-sink-related-work-audit-2026-10-29.zh-CN.md)：B 线现象已被 Prefix Steering 2610.04967 发表、方法在同模型上已有（2609.04434），痛点在实践中被当作功能；S 线前半被 Jin 2502.01563 占、“首步 EOS”形态未找到且命题 4.1 数值检验未蕴含；空位均在对象层；含对前一轮审计的两处更正。
- [X 原帖与评论区线索汇总](literature/x-clues-summary.zh-CN.md)：查原帖、配方、定位方法、工具和复现争议，优先从此进入。
- [可视化工具与研究思路核查](literature/acupuncture-visualization-research-2026-10-26.zh-CN.md)、[后续工具更新](literature/x-visualization-updates-2026-10-27.zh-CN.md)。
- [跨模型干预迁移相关工作](literature/cross-model-intervention-transfer-2026-10-26.zh-CN.md)、[机制干预文献清单](literature/mechanistic-interventions-2026-10-26.json)。
- [HanLab 经验总结原文](HanLab经验总结.md)、[五篇原论文的方法核查](literature/hanlab-mechanism-primary-audit-2026-10-26.zh-CN.md)。
- [原作者坐标、源码与损伤指标核查](literature/source-and-damage-audit-2026-10-26.json)。
- 其他原帖转录、配方清单、样本量核查保存在 [literature/](literature/)，保留日期和来源。

## 历史方案与成本记录

这些文件记录设计过程。方案写过不等于实验已运行；当前范围和完成状态见[实验目录](../experiments/README.md)。

| 主题 | 文件 |
| --- | --- |
| 能力损伤对照方案及预算修订 | [v1](damage-evaluation-plan-v1.zh-CN.md) · [v2](damage-evaluation-plan-v2.zh-CN.md) · [一小时预算](damage-evaluation-one-hour-plan.zh-CN.md) |
| 全层单点正剂量方案与选点 | [方案](layer-dose-survey-plan-v1.zh-CN.md) · [选点记录](layer-dose-survey-selection-v1-2026-10-27.json) |
| 两针根因定位设计 | [root-cause-localization-plan-v1.zh-CN.md](root-cause-localization-plan-v1.zh-CN.md) |
| 迁移方案与定位方向讨论 | [迁移计划](transfer-plan-2026-10-26.json) · [定位方向](acupuncture-localization-direction-2026-10-26.json) |
| 全通道扫描成本外推 | [scan-budget-2026-10-26.json](scan-budget-2026-10-26.json) |
| 历次服务器清理记录 | [server-cache-cleanup-2026-10-26.jsonl](server-cache-cleanup-2026-10-26.jsonl) |

## 文件命名与阅读顺序

给人看的入口使用“研究对象＋测量内容＋用途”命名，例如“Qwen 2B/4B/9B｜单点正负剂量｜原版与干预回答”。索引中不用 `toy`、`r01` 或单独的 `A/B` 代替内容说明。

原始目录中的英文 ID、日期和版本号用于对应冻结清单、代码引用和历史收据，所以保留原名。特别是 `layer-negative-dose-survey…/delivery-r01/all.records.jsonl` **包含原版、正剂量和负剂量**，目录名描述追加实验阶段，不代表文件只含负剂量。

| 常见文件或目录 | 实际含义 |
| --- | --- |
| `PROTOCOL` / `CONTRACT` | 实验设计与允许执行的范围 |
| `EXECUTION` | 执行过程，可能包含尚未结束时的历史快照 |
| `RESULTS` / `FIRST_PASS` | 结果或首轮观察；阅读其中的证据限制 |
| `delivery-r01/all.records.jsonl` | 第一版汇总原始回答，每行一条；可能含复用来源 |
| `delivery-r01/paired_raw.html` | 同题回答对照页面，下载后打开 |
| `records/*.json` | 单条原始运行记录 |
| `receipt.json` / `verification.json` | 执行收据与完整性核验，不替代科学结论 |
| `archive-r01` / `readiness` | 已取回的运行归档 / 开始运行前的准备证据 |

新增实验目录沿用 `experiments/<模型或对象>-<测量内容>-v<版本>-<日期>/`；用 `README.md` 写明中文名称、范围、状态和交付入口。单独导出的新文件应写清模型、测量内容和版本，避免脱离目录后只剩 `data.json`、`final.html` 等模糊名字。旧数据不为统一外观而重命名或重复复制。
