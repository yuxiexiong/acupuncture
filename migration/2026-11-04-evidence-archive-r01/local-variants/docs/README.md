# 项目文档目录

**2026-11-03｜WCP-01 编程工程验收：** [数据、评分/隔离、0.8B与4B编译干预及资源复核](../experiments/wsp-coding-painpoint-v1-2026-11-03/REPORT.zh-CN.md)。四类模块验收通过；保留BF16运行时/编译不等价反例。新增约0.458GB、磁盘余量约269.57GB；4/10 GPUh仅停止线，完整ETA未验证。正式搜索未启动，WCP阶段调度与编辑器阶段权限仍待接入。

**2026-11-03｜WSP 编程扩展 WCP-01（仅方案，未运行）：** [0.8B / 4B 独立痛点诊断与稀疏干预](wsp-coding-painpoint-v1-2026-11-03/PLAN.zh-CN.md)｜[完整设计自查](wsp-coding-painpoint-v1-2026-11-03/SELF_CHECK.zh-CN.md)｜[预算](wsp-coding-painpoint-v1-2026-11-03/BUDGET.json)。Python 函数任务，MBPP 开发、HumanEval+ 独立终验；最多12个候选，含随机/反号及原版非思考对照。全流程停止线4/10 GPUh，包含终验。逻辑自查通过，工程待验收；本轮0模型/GPU，数学50-pass与编程搜索均未启动。

**2026-11-03｜Weight-Space Programming 原始方法与当前资产对照：** [核查报告](literature/weight-space-programming-acupuncture-2026-11-03.zh-CN.md) · [来源清单](literature/weight-space-programming-sources-2026-11-03.json)。先核对最新 KUC/NVW 与 LVK 状态，再读公开代码、搜索日志和补丁；区分稀疏权重修复、条件性计算解释与跨模型迁移。此次仅资料核查，无模型/GPU运行。

**2026-11-02｜QCD-01 形成期位置与剂量（未运行）：** [计划](cache-coverage-dose-plan-v1-2026-11-02.zh-CN.md) · [完整作者自查](cache-coverage-dose-self-check-v1-2026-11-02.zh-CN.md) · [旧记录复算与预算附件](../experiments/cache-coverage-dose-design-v1-2026-11-02/README.zh-CN.md)。先固定受干预缓存、交叉干净V来源，并核对统一切分；通过后才解释等长移窗与双向剂量配平。逻辑通过不等于数值验收或模型/GPU授权。

**阶段B1已完成，主预期不成立｜2026-11-01：** [结果核对与下一步判断](cache-vq-write-interaction-result-review-2026-11-01.zh-CN.md)已复算正式记录：原生评分后半段删第13层V×Q写入交互，停止侧情景变化不到0.05 logit，同一批8个首步停止保持，支持0/6；混合背景交互缩小12%–39%，综合支持1/6。内部交互大不等于该项明显影响原生输出；两背景删除向量范数不同，不推出整个第13层不敏感。124评分＋3模板、0前缀形成已完成；本次仅核对与文档更新，0新模型/GPU。[路线图](cache-mechanism-stage-roadmap-2026-11-01.zh-CN.md)仍推进具体计算解释，先利用已有R/DEL轨迹寻找新的可检验候选，不自动扩层；下一实验未设计/授权。核对记录另列历史路线图冻结版本差异，未改原freeze。

**2026-11-01 第13层实验独立复核：** [计划、代码与结果核对](cache-local-readout-result-review-2026-11-01.zh-CN.md)及[派生复算数据](cache-local-readout-result-review-2026-11-01.json)。核心操作符合单层设计，122个冻结文件哈希匹配，原始记录复算与发布汇总一致；原生背景删交互项的作用很小。纠正原报告：M背景有9格最强非停止词切换，零符号分歧不等于零赢家变化；单层弱作用不能推出第13层不是承载点。本次无新模型运行/GPU，未独立重跑服务器大张量。

**2026-11-01 下一轮设计，未运行：** [旧状态—读取交互到输出的因果检验及完整自查](cache-local-readout-causal-plan-v1-2026-11-01.zh-CN.md)。在统一浅层与原生评分后半段两种背景下，删除第13层已识别的局部交互，检验它对最终词语竞争的作用；包含全部局部变化及同幅随机参照。设计逻辑自查通过，实现/数值/资源待验收；计划上限164次单步评分、0次前缀形成，当前无新模型运行或GPU授权。

**2026-11-01 更新—读取审计：** [已有张量CPU审计报告](../experiments/cache-update-readout-audit-v1-2026-11-01/REPORT.zh-CN.md)与[资产盘点r6](cache-formation-mechanism-asset-inventory-v1-2026-10-31.zh-CN.md)：核实读取路径、同口径停止边际，识别原生针与V钉入在第13层的局部交互差异；该交互到最终输出的因果作用仍未测。无新模型运行或GPU。

**当前口径｜2026-11-01：** 形成—读取连接、缓存组合及跨通道实验已完成。现阶段以机制拆解为主，关键预测形成后用少量其他针眼及随机方向作阶段性检查；非孤例不等于同一完整机制，剂量不是默认下一主线。详见[近期进展与下一阶段推进计划](cache-mechanism-progress-and-next-stage-plan-2026-11-01.zh-CN.md)。本次仅文档更新，无新模型运行。

## 历史更新记录

以下按当时版本记录；旧“未运行”“优先”等不代表当前状态。当前推进顺序以上述计划为准，冻结实验文档保持原样。

**跨通道验证优先，未运行｜2026-10-31：** [实验计划与完整自查](cache-cross-channel-validation-plan-v1-2026-10-31.zh-CN.md)固定原十个L0通道，−1主线、+1符号参照、−0.5剂量敏感性，全部十点−1做V双向形成交叉，明确未检出效应与机制关系不同的区别。[旧数据审计](../experiments/cross-channel-planning-audit-v1-2026-10-31/REPORT.zh-CN.md)已核对152条修改记录及8条基线：旧+1全提示调查79/80首步EOS；后续N1210也有其他协议的缓存证据，不能冒充当前V链的复现。跨通道计划先于单针缓存组合计划；C01–C14/E01–E26自查通过，工程/资源待验收。本次仅CPU旧JSON核对与文档，无模型前向或GPU。

**缓存组合读取计划 v1，未运行｜2026-10-31：** [计划、成本与完整自查](cache-formation-cache-combination-plan-v1-2026-10-31.zh-CN.md)承接已完成的形成—读取连接结果 ef4fe2a，在 CT/C、T/TC 两对上检验递推/卷积/KV 全组合；正反互补格去重，每输入16评分含端点。无针随机 V 参照单列形成成本。区分卷积直接存储、组合依赖与自然路径，C01–C14/E01–E26及反方自查通过，工程/资源未验收；本次仅文档，无新模型运行。下方旧方案的“未运行”保留其历史时间身份。

**最终尺度诊断已补入方案，未运行｜2026-10-31：** [形成—读取方案v1 r2](cache-formation-readout-bridge-plan-v1-2026-10-31.zh-CN.md)§5.1/§13明确同题C分母、CPU高精度输出端反事实、排名/竞争结构、舍入边界和修订自查；[资产盘点r4](cache-formation-mechanism-asset-inventory-v1-2026-10-31.zh-CN.md)区分外部先例、条件推导、已有证据和待测量。不新增GPU条件，无模型运行。

**形成—读取连接方案｜2026-10-31：** [同针V交叉与递推状态交叉方案v1](cache-formation-readout-bridge-plan-v1-2026-10-31.zh-CN.md)承接资产盘点r3的缺测量，明确5个形成条件、10个评分、补录量、判读与完整自查。设计逻辑通过；实现/数值/资源待验收，未运行模型或GPU。

**已有张量核对完成｜2026-10-31：** [资产盘点v1 r3](cache-formation-mechanism-asset-inventory-v1-2026-10-31.zh-CN.md)新增B12、输出竞争分解和缺失测量表；[审计报告与复算证据](../experiments/cache-formation-asset-audit-v1-2026-10-31/REPORT.zh-CN.md)记录先自查后CPU核验12份旧张量与72份logits，无新模型运行/GPU。

**形成结果已纳入资产盘点｜2026-10-31：** [结果资产盘点 v1 r2](cache-formation-mechanism-asset-inventory-v1-2026-10-31.zh-CN.md)新增 A5 与同源支撑 B9–B11，收录形成实验的逐情景读数、数值路线修订、行为边界及下一步顺序。正式结果见固定提交 `181d80a`；下方方案阶段“未运行”是历史状态，本次整理未新增模型运行。

[返回项目首页](../README.md) · [回答原文索引](原始回答与实验数据索引.md) · [实验目录](../experiments/README.md)

**资产盘点后的形成检验｜2026-10-31：** [深层缓存形成条件方案 v2 与完整自查](cache-formation-mechanism-next-step-plan-v2-2026-10-31.zh-CN.md)。承接 E2，具体定义入口抵消、浅层过去状态固定、统一评分背景、不同结果的认识增量及退出条件；设计逻辑自查通过，工程与耗时未验收，未运行模型或 GPU。下方旧方案状态保留其历史身份。

**实验设计交付要求｜2026-10-31：** 所有后续新设计与实质修订先过[实验设计自查规范](experiment-design-self-check.zh-CN.md)，未通过先内部修正。当前案例：[深层缓存形成 A/B 修正版及自查](cache-formation-ab-self-review-v1-2026-10-31.zh-CN.md)，设计逻辑通过，工程未验收、未运行、未授权 GPU。下列较早的“当前/未执行”描述是历史快照，最新状态以[研究状态](RESEARCH_STATUS.zh-CN.md)顶部为准。

[缓存形成机制 CFM：有效计划、命名与审查](cache-formation-mechanism-plan-index-2026-10-31.zh-CN.md)。CFM-S1/S2/S3 均为未执行计划，与历史已完成的“阶段一／二”分开命名。

## 当前立项与查重｜2026-10-30

Acupuncture 当前有两条分别立项的研究线。缓存机制线解释干预的状态承载与延续；稳定副作用控制线研究目标效果、任务代价和跨输入可靠性的改善。当前前者的直接机制证据更完整；二者都不以回避近邻为立项依据。以下是研究草案，不是实验执行授权。

| 研究线 | 立项文档 | 查重文档 |
| --- | --- | --- |
| 缓存机制线 | [痛点、证据、贡献目标与缺口](cache-mechanism-proposal-2026-10-30.zh-CN.md) | [缓存拆分、状态移植、WriteSAE 等近邻对照](literature/cache-mechanism-prior-art-2026-10-30.zh-CN.md) |
| 稳定副作用控制线 | [目标效果、任务代价、已有基础与缺口](stable-control-proposal-2026-10-30.zh-CN.md) | [DSI、CNA、COAST、SteerScope 等方法与评价对照](literature/stable-control-prior-art-2026-10-30.zh-CN.md) |

缓存机制线当前入口：[第一阶段：原始轨迹的写入、旧状态处理与读取分析｜2026-10-31](cache-formation-mechanism-s1-native-trace-plan-v1-2026-10-31.zh-CN.md)。固定六旧情景、两个既有锚点，核对已有数据能回答什么，并给出缺失内部量、离线差异记账和第二阶段决策；只完成设计/文件核查，未运行模型/GPU。[r04补偿与S/O失配复审](cache-mechanism-controlled-path-design-r04-2026-10-31.zh-CN.md)及[CPU反例](../experiments/cache-path-design-check-v1-2026-10-31/README.zh-CN.md)保留：r04仅作辅助受控探针，不启动全量网格。另存[r03](cache-mechanism-write-retention-design-r03-2026-10-31.zh-CN.md)、[r02](cache-mechanism-design-audit-r02-2026-10-31.zh-CN.md)、[r01](cache-mechanism-write-update-plan-2026-10-31.zh-CN.md)及[先验审计](cache-mechanism-known-basics-audit-2026-10-31.zh-CN.md)供追溯。

已完成的证据：[四格交互CPU复算](../experiments/cache-complement-analysis-v1-2026-10-31/RESULTS.zh-CN.md)覆盖96条旧回答；[计算路径与组件补充复算](cache-mechanism-path-audit-2026-10-31.zh-CN.md)覆盖包含这96条在内的528条旧记录，未新增GPU。历史设计：[互补对照原计划](cache-complement-toy-plan-2026-10-31.zh-CN.md)、已撤回的[自然状态小桥接](cache-mechanism-toy-round1-2026-10-30.zh-CN.md)、[广谱设计](cache-mechanism-broad-study-2026-10-30.zh-CN.md)、[旧五项计划](cache-mechanism-evidence-plan-2026-10-30.zh-CN.md)；均不构成当前新运行授权。

当前项目定位以[首页](../README.md#当前两条研究线)和上述文档为准。下方旧报告、历史方案和运行快照保留当时内容，不能因仍可点击而视为当前计划或新运行授权。

## 报告与研究状态

| 清楚名称 | 文件 | 用途 |
| --- | --- | --- |
| **完整实验总结｜导师阅读版｜2026-10-28** | [Acupuncture_实验总结_导师版_2026-10-28.md](Acupuncture_实验总结_导师版_2026-10-28.md) | 独立阅读；实验记录、数字、原文案例、观察及限制 |
| **实验结果与线索｜导师图文展示｜2026-10-28** | [Acupuncture_实验结果_导师展示_2026-10-28.html](Acupuncture_实验结果_导师展示_2026-10-28.html) | 图表、结构图、剂量原文；下载后打开 |
| 既有结果与研究线索｜历史总报告 | [EXPERIMENT_RESULTS_MASTER.zh-CN.md](EXPERIMENT_RESULTS_MASTER.zh-CN.md) | 保留当时的汇总与原始证据链接；当前综合展示优先看上面两份 |
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

## 2026-11-02：CT-01 后续行为验证（计划，未运行）

- [FC-01：首步选择、条件续答与卷积恢复](cache-first-token-continuation-plan-v1-2026-11-02.zh-CN.md)：六核心条件、32-token 有限续写，包含强制 q0 的提示边界、完整预算与 C01–C14/E01–E26 自查。仅设计交付，无新增模型/GPU授权。

## 2026-11-02：FC-01 后的两条独立验证（计划，未运行）
- [SP-01 共享首token与内容选择](cache-shared-prefix-continuation-plan-v1-2026-11-02.zh-CN.md)：消除首字母唯一定位捷径，区分基线不足与干预未迁移。
- [FX-01 固定45头V的完整交付](cache-fixed-v-delivery-plan-v1-2026-11-02.zh-CN.md)：原生背景恢复，固定名单/其余V/全V/冻结随机对照；不以SP阳性为前提。
两份均含C01–C14、历史错误与反方自查；仅设计交付，不启动GPU。

## 2026-11-02：FX连续读数与SP的V/qk恢复后续设计

[两个独立计划与完整自查](cache-v-followup-self-check-v1-2026-11-02.zh-CN.md)：FXS-01补首步连续分数；SVQ-01检验共享首字母条件下V/qk恢复的完整交付。仅设计，无新增模型运行授权。

## 2026-11-02：SVQ 后的按名称查询与位置配对（计划，未运行）

- [NQ-01 实验计划](cache-name-query-order-plan-v1-2026-11-02.zh-CN.md)：去除目标标签，6场景×3排列×3查询，区分目标、位置与固定身份跟随；自然交付与条件诊断分开。
- [NQ-01 自查](cache-name-query-order-self-check-v1-2026-11-02.zh-CN.md)：C01–C14、历史错误、反例与预算；仅文档交付，无新增模型运行授权。

- NQ-01 v2（取代v1作为实现依据）：[按名查询与记录顺序计划](cache-name-query-order-plan-v2-2026-11-02.zh-CN.md)；[设计自查](cache-name-query-order-self-check-v2-2026-11-02.zh-CN.md)。查询前置、固定注入窗口、场景共享校准、Q仅描述；未运行。

## 2026-11-02：QC-01 查询布局与注入覆盖（计划，未运行）

- [实验计划 v1](cache-query-layout-coverage-plan-v1-2026-11-02.zh-CN.md)：四模板加两个同文本缩窄覆盖条件，复用 NQ；比较 V 恢复完整交付的条件依赖，明确剂量混淆。
- [设计自查 v1](cache-query-layout-coverage-self-check-v1-2026-11-02.zh-CN.md)：C01–C14、历史错误、对抗反例、预算与退出；文档交付不构成模型运行授权。
