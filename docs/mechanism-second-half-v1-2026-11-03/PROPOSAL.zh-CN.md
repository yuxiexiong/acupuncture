# 从局部链条到跨条件机制

**Acupuncture 课题下半场 Proposal · v5 · 2026-11-05**

状态：**从"工作清单"改为"核心主张及其证据要求"。** 依据用户 2026-11-05 的判断：课题有实质研究基础，但核心贡献仍有未解决的风险；必须先区分"决定课题能否成立"与"只影响高度"的问题，先解决前者。本稿与 [候选主张表](CLAIMS.zh-CN.md)、[Roadmap v5](../cache-mechanism-broadening-roadmap-2026-11-04.zh-CN.md)、[To-do](../cache-mechanism-todo.zh-CN.md) 同步。**本次只更新文档；没有新增模型/GPU 运行或运行授权；未冻结任何操作矩阵与预算。** v4 见[修订前快照](https://github.com/yuxiexiong/acupuncture/blob/83e82b054fe16fec6cc057ad0cbd6a6394d60089/docs/mechanism-second-half-v1-2026-11-03/PROPOSAL.zh-CN.md)；[方向自查](SELF_CHECK.zh-CN.md)审的是 v4，对 v5 尚未重做。

## 0. 现状判断

不是"基本确定能成，只剩提高上限"。现象、局部计算证据与反例已经降低了从零开始的风险，但**尚未把它们组织成一个值得检验、能够站稳的贡献**。最容易犯的错是：在核心主张没站稳时，通过加层、加模型、加实验把投入做大。

| 问题 | 性质 | 当前状态 |
|---|---|---|
| 能否提出已有知识未充分回答的重要结论 | **决定核心贡献** | [CLAIMS](CLAIMS.zh-CN.md) 筛出一个候选 K1\*，其一半已被数据否定、改写后才能立；痛点仍是推测档 |
| 解释与实际回答变化是否有可信因果连接 | **决定核心贡献** | 形式分量（停止）有；内容分量（错答）的承载未分开 |
| 解释能否接受独立条件检验 | **决定核心贡献** | 0 份独立材料；所有面板已见 |
| 覆盖更多模型、任务、深度 | 取决于主张 | K1\* 不主张跨架构，覆盖主要扩影响范围 |
| 定位更多层、头、位置 | 影响解释精度 | 只在能区分 §3 的替代解释时才做 |
| 可用的诊断/干预方法 | 可能提高价值 | 不主张实用性，不兑现 |
| 解释全部残余、证明唯一通路 | 非必要 | 不做 |

## 1. 总问题（不变）

> 稀疏激活干预怎样改变写入、历史状态处理和后续读取，最终造成回答变化；哪些关系可以跨条件复用，哪些受到明确条件限制？

**预测是检验机制解释的手段，不是把课题改成预测器项目。** 不强求标量公式或统一所有条件。随机方向复现关系是需要解释的正面证据，不是附带限制；但效应相似、操作响应相似、计算过程相同必须分开检验。

## 2. 我们希望多知道什么

最终结论必须比"状态类别存在分工""不同条件效果不同"更具体。当前立的核心候选（[CLAIMS §3](CLAIMS.zh-CN.md#3-选定的核心候选改写后)）：

> **K1\*：内部稀疏注入造成的回答损伤由两个可分离的分量构成。形式分量（首步停止）只在注入覆盖记录句之后的位置时出现，由递推状态承载，恢复递推即消除，且消除它不恢复内容。内容分量来自注入覆盖模板＋记录句段，其承载状态不固定；决定它的是什么，是当前最大的未知。**

去掉层号、通道号后，它可以被新条件推翻的点是：(i) 在任何会出现首步停止的新条件上，恢复递推不消除停止；(ii) 位置数配对后"段"效应消失；(iii) 对齐协议后内容分量在两任务上由同一类状态承载（那"不固定"就撤回）。

两个子项只在 K1\* 下有位置，不单独承重：
- **K2**（L0 型针上，模板＋记录句段损伤偏 KV、记录句后损伤偏递推）——三根非 L0 原生针未获支持；
- **K3**（旧写入—读取链：β·k·vᵀ 写入 → α·Sᵀq 直接读取）——形式分量的机制候选，横向只有 L0。

被淘汰的候选及理由见 CLAIMS §2：K4（KV 携带事实答案）被 2609.04434/2609.33093 蕴含；K5（非加和）、K6（条件充分性）无机制内容；K7（方向无关）L0 限定。

## 3. 现有证据支持到哪里（分账）

| 证据来源 | 支持什么 | 不支持什么 |
|---|---|---|
| 旧写入—读取链（KUC/LVK/SRU/XCHAN/EH-XC，L0） | 形式分量在 L0 上的计算路径；同幅随机方向复现 | L0 以外任何层；原生完整回答端点（NVB P1 否）；L12 反例（CGV） |
| WIN-01/02 的共同响应 | 形式分量只随记录句后注入出现、递推恢复消除（L0/N4146、L1、R0）；关系 M 在 4 个可检验格成立无反例 | 形式分量在 L2/L3/L5 出现（≤ 6/48）；P4 在非 L0 原生针成立（不可判、点估计反向） |
| WIN-01/02 的分叉 | 内容分量的承载不固定（事实 W_post 深层 S 16 对全层递推 47；W_pre 偏好随针变） | 这些差异是"机制不同"（协议差异未对齐，见 CLAIMS §4.1） |
| KVC-01 | 桥接：记录句事实段 KV 定向决定答哪个事实 | 任何新主张（被蕴含）；读取机制 |
| NCC/NSR/NQK/NPC | 条件充分性、组合依赖（约束） | 任何单一承载 |
| 阶段二全层、E2、COMBO 等 | L0 事实丢失 KV＋线性层各半、来自提示前部；深层缓存承载停止分差而不复现停止 | 层内代表性（每层一通道）；跨模型 |

87–97%、73–86% 等数字是指定对照下的效应比，不是机制完成度。

## 4. 最强的替代解释（不预先排除）

每一条都能在不动 K1\* 核心句的情况下解释一部分数据，所以横向比较必须正面处理它们：

1. **干预尺度/位置数**：W_pre 与 W_post 位置数逐题差 −14…+13，"段"可能是累计剂量的代理。
2. **天花板**：损伤轻的格救回余量小，恢复偏好不可判。
3. **可受影响下游范围**：注入层决定哪些 KV 层受损（L3/L5 注入时第 3 层 KV 干净），非 L0 针"偏递推"可能是结构后果。
4. **任务协议差异**：生成长度 128/32、校准文本与尺度、形成实现、判读方式全部不同。
5. **一般作答损伤**：恢复偏好只反映"能不能答"，与内容无关。

## 5. 什么结果使核心主张成立、修改或暂时放弃

写死在 [CLAIMS §3](CLAIMS.zh-CN.md#3-选定的核心候选改写后) 的表里，摘要：

| 结果 | 处置 |
|---|---|
| 对齐协议后内容分量承载在两任务确实不同，且位置数配对后段效应保持 | 成立 → 独立确认 |
| 对齐后两任务都只需深层递推 | 修改：撤回"承载不固定"，转检验 K7 |
| 对齐后两任务都需组合 | 修改：只剩形式分量那一半 |
| 位置数配对后段效应消失 | 放弃"段"表述，改剂量表述，撤回 K2 |
| 非 L0 型针出现停止但递推不消除 | 放弃"由递推承载" |

**没有一种结果导向"继续加实验"**；每种都指向一个具体的替换问题或撤回。

## 6. 推进顺序（按消除关键不确定性，见 Roadmap v5）

| 阶段 | 要得到的认识 | 现状 |
|---|---|---|
| 确定核心候选主张 | 哪个差异最重要、尚未解释、旧机制对它有什么预期 | **本次完成**（CLAIMS），等用户确认 |
| 关键横向比较 | 候选关系在有判别力的新条件中保持、失效或修订 | 选定 [CLAIMS §4.2](CLAIMS.zh-CN.md#42-选定的比较内容分量由哪类状态承载同针同窗口两任务把递推拆成浅深把-kv-拆成浅深)：同针同窗口两任务，递推与 KV 各拆浅/深，加位置数配对窗口；先核可比性 |
| 必要的计算检验 | 对关键共同点或分叉给出因果约束 | 只在横向结果指出影响整体解释的分叉时做；不追求完整回路 |
| 独立确认与边界 | 固定后的解释面对未参与构建它的材料 | 0 份；成立后才扩范围 |
| 价值兑现 | 是否支持更好的诊断/控制，或构成足够重要的机制结论 | 决定论文形态；现在不承诺 |

横向比较从一开始承担**区分解释**的职责，不是"先扫全层，再挑一点深挖"。

**v4 队列的修正**：
- **取消"再做一轮 KV 读取"作为默认下一步。** 它服务的候选 K4 已被蕴含，没有主张可服务。"最多一轮"的上限保留，但上限不是配额，也不是这一轮值得做的理由。
- 局部深入重新开启的条件：横向结果出现影响 §5 处置的分叉，且能说出它解决哪个跨条件问题。
- **SDM 全层图谱草稿不自动成为主线。** 它有两处影响科学结论的问题：(a) 从"干净上下文中 KV 与递推的分工"推到"内部干预致错时恢复 KV 应充分、恢复递推应不足"不是自动成立的推论，基线推得过强时测到偏离也未必是发现；(b) 单类恢复与留一恢复不能把结果直接归为"唯一承载/分布式/冗余"，超出这些反事实操作的识别范围。它可以提供数据，但扩大运行前必须说明这些数据检验什么解释。已在[该稿](../cache-state-type-damage-map-plan-v1-2026-11-05.zh-CN.md)顶部登记。

## 7. 下一张卡必须先回答的两句话

在用户确认 §6 第二阶段的比较后，才按[自查规范](../experiment-design-self-check.zh-CN.md)写卡；卡的开头必须是（草稿见 [CLAIMS §5](CLAIMS.zh-CN.md#5-第三优先下一张卡的两句话草稿不是卡)）：

- 预期结果全部出现，支持的是哪一句核心结论；
- 预期不出现，撤回什么，下一步为什么不会只是扩大扫描。

现在不能诚实地把它指定为"KV 读取定位"或"全层状态图谱"。

## 8. 文档衔接与本次变更范围

Proposal 解释核心主张与决策逻辑，CLAIMS 是主张的证据账本，Roadmap 定义阶段与出口，To-do 记录当前入口。旧 v2–v4、旧 EOS 预测稿、SDT/NMT 等历史方案与正式合同保留原身份。本次未修改原始实验或冻结合同，未运行模型。

## 证据入口

- [候选主张表](CLAIMS.zh-CN.md)、[统一归档及更正](../RESEARCH_ARCHIVE_2026-11-04.zh-CN.md)、[资产目录](../RESEARCH_ASSET_CATALOG_2026-11-04.zh-CN.md)、[查重记录 11-05](../literature/state-type-damage-map-prior-art-2026-11-05.zh-CN.md)。
- [WIN-01](../../experiments/window-recovery-win01-v1-2026-11-04/REPORT.zh-CN.md)、[WIN-02](../../experiments/window-prediction-win02-v1-2026-11-04/REPORT.zh-CN.md)、[KVC-01](../../experiments/kvpre-content-kvc01-v1-2026-11-05/REPORT.zh-CN.md)、[R1 对齐](../../experiments/cache-mechanism-alignment-r1-v1-2026-11-04/REPORT.zh-CN.md)、[WIN-02 评估](../win02-proposal-assessment-2026-11-05.zh-CN.md)。
- 原生链报告（固定快照 `2ca7f108`）：[NFC](https://github.com/yuxiexiong/acupuncture/blob/2ca7f1089672cbaf4dd664ff2d3bb187072619da/experiments/cache-native-first-token-competition-v1-2026-11-02/REPORT.zh-CN.md)、[EH-XC](https://github.com/yuxiexiong/acupuncture/blob/2ca7f1089672cbaf4dd664ff2d3bb187072619da/experiments/cache-eh-cross-channel-v1-2026-11-02/REPORT.zh-CN.md)、[SK](https://github.com/yuxiexiong/acupuncture/blob/2ca7f1089672cbaf4dd664ff2d3bb187072619da/experiments/cache-sk-history-v1-2026-11-02/REPORT.zh-CN.md)、[NR](https://github.com/yuxiexiong/acupuncture/blob/2ca7f1089672cbaf4dd664ff2d3bb187072619da/experiments/cache-native-complement-recovery-v1-2026-11-02/REPORT.zh-CN.md)、[CT](https://github.com/yuxiexiong/acupuncture/blob/2ca7f1089672cbaf4dd664ff2d3bb187072619da/experiments/cache-competitor-turnover-v1-2026-11-02/REPORT.zh-CN.md)。
- [SIT 更正后报告（50f928f）](https://github.com/yuxiexiong/acupuncture/blob/50f928f/experiments/cache-state-increment-transfer-v1-2026-11-03/REPORT.zh-CN.md)、[CGV 边界探索（420addd）](https://github.com/yuxiexiong/acupuncture/blob/420addd/experiments/cache-chain-generalization-v1-2026-11-03/REPORT.zh-CN.md)、零 GPU 三件套（34edbd3）：[盘点](https://github.com/yuxiexiong/acupuncture/blob/34edbd3/docs/cross-condition-predictor-v1-2026-11-03/INVENTORY.zh-CN.md)、[候选解释](https://github.com/yuxiexiong/acupuncture/blob/34edbd3/docs/cross-condition-predictor-v1-2026-11-03/CANDIDATES.zh-CN.md)、[旧预注册草稿](https://github.com/yuxiexiong/acupuncture/blob/34edbd3/docs/cross-condition-predictor-v1-2026-11-03/PREREG_DRAFT.zh-CN.md)。
- 仓库规范：[已知基础审计](../cache-mechanism-known-basics-audit-2026-10-31.zh-CN.md)、[实验设计自查](../experiment-design-self-check.zh-CN.md)。本稿不新增领域首创或文献覆盖的主张。
