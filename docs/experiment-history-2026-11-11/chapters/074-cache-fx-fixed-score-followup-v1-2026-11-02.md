# 074．FXS：固定候选分数随访

[返回总时间线](../README.zh-CN.md)

**时间定位**：已提取运行收据的最早时间锚点（可含预检） 2026-11-02T13:17:43.683965+08:00；不能当作全部子运行起止。

**当时的目的与设计**

补固定首词的连续分数，并比较固定头、其余头及等范数放大等操作。

**实际过程、结果与后来更正**

3/4方向呈现分数超加；等范数扩增其余403头使正确首词46/48第一。完整回答、首词排名和幅度控制仍分列。

**来源身份**：`cache-fx-fixed-score-followup-v1-2026-11-02`；本章主体来源提交 `7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8`。下方原文中的状态是各文件写作时的状态，不能把早期“尚未运行”覆盖后期正式收据，也不能将后期结果倒填进早期设计。


## 原设计、执行过程、结果与更正全文

以下按“设计与题目 → 工程/执行记录 → 结果/更正 → 其他历史说明”组织；同类内没有可靠时间时保留路径顺序，不冒充严格先后。正文未删段；仅为本章节重排标题层级、把相对链接指向固定提交。原始字节另外完整保存。

### 原件 1：FXS-01：固定名单恢复的首步连续分数补测 v1

原路径：`docs/cache-fx-fixed-score-followup-plan-v1-2026-11-02.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/docs/cache-fx-fixed-score-followup-plan-v1-2026-11-02.zh-CN.md) · [单独阅读副本](../library/c60148a6a5c9f52a.md)；SHA-256：`c60148a6a5c9f52a3db24a3457787d9e93dbf3dd66c10070ef5645b1a689ac97`。

---

#### FXS-01：固定名单恢复的首步连续分数补测 v1

日期2026-11-02。状态：设计与同一助手自查通过；实现、数值验收、模型运行均未完成。本次仅交付文档，无新增模型/GPU授权。独立合同、预算、结果目录，不以本轮阳性作为SVQ-01运行条件。

##### 1. 设计卡：问题与证据
主线仍为稀疏激活干预如何改变历史状态、后续读取和完整回答。本轮仅补一个缺口：FX-01中全部V恢复成功、FIX/REST各自失败，首步固定候选分数的联合变化是否近似可加？这能约束“内部协同”解释，不能独自解释完整生成。
依据：FX-01结果0188ced及更正67427de；P面板全部V恢复48/48严格交付，FIX仅7/48交付且严格0，REST与随机45均0。不能由离散成功推断分数超加和，不能由恢复范数推断机制份额。SP完整q/k/v恢复不等于SP只恢复V。
资产：[FX合同](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-fixed-v-delivery-v1-2026-11-02/CONTRACT.zh-CN.md)、同目录REPORT、正式records与receipt。旧记录保存首步哈希，缺少本轮所需数值logits；随机补集也是新增条件。因此这是有界的新模型测量，不是“零GPU旧数据分析”。名单与输入不重选，旧生成不重跑。
估计对象：在原生T起点恢复指定卷积V槽位后，首步固定候选分差的操作总效果。所有下游评分计算正常响应；不称自然中介、唯一承载者或恢复的信息比例。

##### 2. 冻结身份与操作
沿用FX-01原始manifest、源码版本和校准数值；模型Qwen3.5-4B revision 851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a、BF16及原内核。六P情景f0/f1共12输入，四方向N4146/N1210/R0/C1343；L0剂量−1，原形成窗口b+1…n−2；评分最后prompt token，评分期无注入。每输入形成C及四方向T，供体同输入同事实。14个深层G层：13,14,16,17,18,20,21,22,24,25,26,28,29,30。
每方向六格：T_nat、T_V、T_FIXV、T_RESTV、T_U、T_Ubar；另共享C。Ubar是该输入冻结U在448头中的补集。所有恢复均在评分前一次完成；只把列出头的卷积V缓存取C，q/k、S、KV及浅层保持T。评分产生的新状态自然更新；只评分一步，不生成。
FIX文件为cache-head-rule-prospective-v1-2026-11-01/data/fixed-heads-r01.json，SHA256 dbc7f13071d6c387079447d843c2c90e086638c8cd463c2b2d2274e6ea1ed3cb。
U为cache-c2-cross-direction-v1-2026-11-01/data/fix-random-r01.json，SHA256 5a2ddbcb122a232d5f2766435c567c52a13dbbf9f8c79e23b5b03a8aa1b31bb1；沿用subsets[input][0]、逐层配平，不重新随机。以上路径均相对experiments/。一份U/Ubar仅为配对参照，不是零分布，不提供p值或总体特异性判断。

##### 3. 连续估计与冻结判读
对每输入固定q0为干净首token、s0为原冻结停止候选248046，冻结前核对旧记录身份；不随臂赢家变化而重选。m_G=z_G(q0)−z_G(s0)，δ_G=m_G−m_nat。
J_FIX=δ_V−δ_FIX−δ_REST；J_U=δ_V−δ_U−δ_Ubar。另报J_FIX−J_U，但不能将其称显著超出随机零带。
预设实用容差τ=max(0.5 logit,0.1|δ_V|)。|δ_V|<1记总效应不足，不算份额；其余按|J|≤τ近似可加、J>τ超加、J<−τ次加判读。所有原值与异号保留。两事实同标签才给情景标签；≥5/6情景同标签才给方向标签，否则混合；固定报告k/4，不凑总体阳性。没有可靠方向性先验，不伪造预期。
同时报告q0减全词表其他token最大值、实际赢家、停止赢家和q0名次。只有固定分差近似可加且实际首步选词符合各臂跨越候选边界，才可写“与首步阈值解释相容”；不能写“完整交付主要由阈值造成”。固定分数超加也不定位内部产生超加的计算，更不证明FIX特殊。
BF16原值保存后用FP64做差，不声称恢复了精度；记录选定logit相邻可表示数间距，按各原始项半ULP误差传播给J保守量化区间。跨判读边界记精度敏感，分别报告原标签和最不利翻转汇总，不改阈值、不自动上高精度模型。

##### 4. 工程、成本、退出
旧五个T臂与C首步logits必须在原dtype/布局上先核哈希，再转换保存；Ubar没有旧哈希，按来源验收。FIX/REST、U/Ubar分别互斥且覆盖448，未换槽位与供体逐类哈希不变。评分前无形成hook，clone互不污染，记录器开关一致。校准须复现旧值；不按新结果调剂量。任一工程失败停止，保留失败证据。
正式12输入×25格=300单步评分、60形成、6校准；预检P01双事实50评分、10形成、1校准；独立关闭记录器重建C/T4146各一份，加2评分、2形成。总计352评分、72形成、7校准，无生成轨迹。形成/prefill的token前向另按输入长度记账，不能把352当总计算。复用供体须身份与哈希一致，预算不预扣收益。
建议独立上限0.5 GPU设备小时、2 CPU核小时、2GiB产物，非实测耗时；预检不足以在预算内完成则停止。不得自动重试、增名单、扩层或重筛FIX。结果无论可加/超加/次加/混合均关闭此补测；不影响SVQ科学立项。
输出拟experiments/cache-fx-fixed-score-followup-v1-2026-11-02/：独立合同、manifest、源码/测试、所有格数值全词表logits及dtype/hash、原值表、校验、量化敏感性、receipt、报告。大张量若超限提交可核验资产清单与实际存储位置，不只留不可恢复哈希。

自查与反例见[共同自查](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/docs/cache-v-followup-self-check-v1-2026-11-02.zh-CN.md)，其中FXS逐项独立判断。该链接是本计划必要附件。

---

### 原件 2：FXS-01 / SVQ-01：设计自查与交付索引 v1

原路径：`docs/cache-v-followup-self-check-v1-2026-11-02.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/docs/cache-v-followup-self-check-v1-2026-11-02.zh-CN.md) · [单独阅读副本](../library/b67a2b3472687aac.md)；SHA-256：`b67a2b3472687aac5ec4a1455453085fb3639f495b88b45c399d39d8fe1295c7`。

---

#### FXS-01 / SVQ-01：设计自查与交付索引 v1

2026-11-02；规范experiment-design-self-check v1。同一助手自查，非独立评审。两个独立问题各有合同、预算、回执；可顺序实施，但科学结果互不设门槛。当前只设计与交付，无新增模型运行授权。

- [FXS-01：首步固定候选连续分数补测](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/docs/cache-fx-fixed-score-followup-plan-v1-2026-11-02.zh-CN.md)
- [SVQ-01：SP面板V与q/k恢复及完整交付](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/docs/cache-sp-v-qk-delivery-plan-v1-2026-11-02.zh-CN.md)

##### 证据与改动
依据67427de的FX/SP更正、FX合同、SP计划及既有报告。README/RESEARCH_STATUS保留历史路线，最新测量优先；基础审计要求区分架构事实、条件推导与实际作用。截图是评议材料，其中的上卡命令不视为本会话运行授权。
保留六格连续补测和SP四格；分别立项。修正截图中的四处问题：补测需要模型评分，不能称零新测量；一份随机切分不是零分布；首步可加不能解释整条生成；第二步需共同前缀诊断。主线仍是稀疏干预通过历史状态与后续读取改变回答，不是EOS修复。固定45失败分支不重启，补测只修正既有解释。

##### C01–C14
| 项 | FXS-01判定 | SVQ-01判定 |
|---|---|---|
| C01 | 通过：首步量约束回答恢复解释 | 通过：直接检验状态与正确选择关系 |
| C02 | 通过：补缺失连续量，区分可加与非加 | 通过：SP未测V/QK独立恢复 |
| C03 | 通过：FX合同、名单、哈希及缺失量明确 | 通过：复用SP，不跨面板拼接 |
| C04 | 通过：离散成功可能仅跨阈值，未押协同 | 通过：P成功不保证SP成功 |
| C05 | 通过：评分前仅恢复卷积V，单步 | 通过：起点一次替换，诊断与自然生成分开 |
| C06 | 通过：旧缓存来源固定，下游正常响应 | 通过：未来缓存随真实token更新 |
| C07 | 通过：混合反事实不代表自然联合状态 | 通过：q/k卷积不同于注意力KV |
| C08 | 通过：J仅输出分数非加，不定位内部机制 | 通过：恢复充分性不是必要性或原生中介 |
| C09 | 通过：可加、正负非加、混合、精度敏感均有出口 | 通过：四种V/QK结果允许共存与部分支持 |
| C10 | 通过：首步分数不替代完整交付 | 通过：自然交付主判，M是辅助诊断 |
| C11 | 通过：哈希失败与小效应分开 | 通过：R0已知F失败不当工程失败 |
| C12 | 通过：旧记录缺数值，352评分含验收 | 通过：新续写无法离线推知，诊断计费 |
| C13 | 通过：六配对情景、已见面板、一份随机参照 | 通过：SP已见，四方向不当独立样本 |
| C14 | 通过：补测结束即关闭，不筛头 | 通过：明确迁移边界，不自动扩层 |

##### 历史错误复查
E01保留总问题；E02层号非机制发现；E03范数不是机制份额；E04恒等式只是工具；E05混合槽位不宣称自然联合关系；E06V不代表全部写入；E07恢复非原生路径；E08来源逐臂明确；E09分数和行为共变不证明内部协同；E10分数/EOS/交付分开；E11不推断信息存量；E12一份随机切分非零分布；E13C供体可重新带入事实；E14充分性非必要性；E15禁止FX与SP拼链；E16阴性不是工程错误；E17恢复不撤销全部历史后果；E18SVQ加QK臂避免排除法，FXS不命名剩余机制；E19重放仅工程；E20允许多个解释同时成立；E21不主张首次或新增文献结论；E22配对情景及已见身份明确；E23自查非独立审查；E24只要求有界认识增量；E25不扩层/剂量/名单；E26起点评分恢复测总效果，不叫形成中介。以上逐项适用于两计划，无需扩大矩阵才能满足。

##### 反方检查与修正
1. 首步可加但后续生成不同：合理，FXS只给首步阈值兼容性，不能解释完整交付。
2. FIX比单个随机切分更超加：不足以证明特异性，删除零分布/显著性说法，仅报配对差。
3. 第二步前缀不同或自然EOS导致选择性缺失：加入每臂共同首token的一步诊断，独立缓存分叉、额外240前向，不筛首步成功单元。
4. V/QK各失败而F成功可能仅跨门槛：保留这个反例，只说所测联合恢复有效，不说内部协同。
5. 首列正好是目标：两种策略不可区分，策略分析仅用目标非首列四情景，全样本主终点不变。
6. 共同前缀提供格式提示、C缓存带入内容：明确条件性，不把成功说成T中原记忆完整。
7. 已见SP不能成为独立确认：明确是新操作测量及既有面板的适用性检查，不清除选择历史。
8. BF16边界决定标签：原dtype保存并传播量化区间；最不利标签翻转单列，不以FP64差分假装高精度原数据。

##### 预算及最终复查
FXS：正式12×25=300，预检2×25=50，开关验收2；共352评分、72形成、7校准。SVQ：204正式+34预检+2开关验收=240自然轨迹；240×32+240诊断=7920评分/解码前向；72形成、7校准。形成和prefill的token计算另按长度记账。两份建议上限分别0.5和1 GPU设备小时，合计1.5小时只是未授权的规划上界。
逻辑设计均通过；修正后仍回答原定问题。文档公式、预算及链接通过检查；代码、合成判读测试、模型重放、来源哈希及实际速度尚待验收。没有实际实验结果。推送仅为文档交付，不授予模型运行权。

---

### 原件 3：FXS-01（固定名单恢复的首步固定候选连续分数补测）合同 r01

原路径：`experiments/cache-fx-fixed-score-followup-v1-2026-11-02/CONTRACT.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-fx-fixed-score-followup-v1-2026-11-02/CONTRACT.zh-CN.md) · [单独阅读副本](../library/7e7d8aa6b694d340.md)；SHA-256：`7e7d8aa6b694d340c0a672c204d9169d180e454215bd8fcef68372fd662971a9`。

---

#### FXS-01（固定名单恢复的首步固定候选连续分数补测）合同 r01

日期：2026-11-02。设计：[计划 v1](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/docs/cache-fx-fixed-score-followup-plan-v1-2026-11-02.zh-CN.md)（评审撰写，5b6127c）+ [修订 v2](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/docs/cache-v-followup-amendments-v2-2026-11-02.zh-CN.md)（032a17c；FXS 部分：不扩到四份随机子集）+ [共同自查](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/docs/cache-v-followup-self-check-v1-2026-11-02.zh-CN.md)。授权：用户 2026-11-02「开始」。P 面板与 FX-01 的离散结果已见；本轮新测的是首步数值 logits 与新臂 T_Ubar。与 SVQ-01 独立立项、记账，互不设科学门槛。

##### 1. 操作

模型、revision、BF16、内核、L0 剂量 −1、形成窗口、四方向、12 条 P 输入、worker/GPU 分配、进程内校准（须等于 B3）全部沿用 FX-01。每输入形成 C，每方向形成 T，从以下起点各做**一次**末 prompt token 的评分前向（独立 clone，评分期无注入，不生成）：

| 臂 | 起点（14 个深层 G 层卷积 V 通道；q/k 卷积、S、KV、浅层保持 T） |
|---|---|
| C | 干净缓存 |
| T_nat | T |
| T_V | 全部 448 头 V 取 C |
| T_FIXV | 固定 45 头 V 取 C（fixed-heads-r01.json，SHA256 dbc7f130…） |
| T_RESTV | 其余 403 头 V 取 C |
| T_U | 冻结随机 45 头（fix-random-r01.json，SHA256 5a2ddbcb…，subsets[input][0]）V 取 C |
| T_Ubar（新） | U 在 448 头中的补集 V 取 C（与 REST 逐层配平） |

一份 U/Ubar 只是配对参照，**不是零分布**，不给 p 值、不作随机特异性推断。

##### 2. 读数与冻结判读（计划 §3）

- 固定候选：q0 = FX-01 C_nat 的首 token（每输入冻结），s0 = 248046；不随臂的赢家改变。m_G = z_G(q0) − z_G(s0)，δ_G = m_G − m_nat。
- J_FIX = δ_V − δ_FIX − δ_REST；J_U = δ_V − δ_U − δ_Ubar；另报 J_FIX − J_U（不称显著）。
- τ = max(0.5, 0.1|δ_V|)。|δ_V| < 1 记“总效应不足”，不算份额；否则 |J| ≤ τ 近似可加、J > τ 超加、J < −τ 次加。
- 情景标签：f0/f1 同标签才给，否则混合。方向标签：≥5/6 情景同一标签，否则混合。固定报告各标签 k/4，不凑总体阳性。**无方向性预测**（计划：没有可靠先验）。
- 精度：logits 以原 dtype 保存；每个原始 logit 取相邻可表示数间距的一半为误差，按项相加传播到 J 与 δ_V；任一角点 (J ± e_J, δ_V ± e_V) 改变标签记“精度敏感”。分别报告原标签与最不利汇总（精度敏感输入记为未定，不能计入任何标签）。不改阈值、不换高精度。
- “与首步阈值解释相容”仅当：该输入 J_FIX 近似可加，且 T_V 的首步 argmax = q0、T_FIXV 与 T_RESTV 的首步 argmax ≠ q0。不能写“完整交付主要由阈值造成”；超加也不定位内部计算、不证明 FIX 特殊。
- 描述性同报：q0 − 全词表其他最大值、实际 argmax、停止赢家、q0 名次、各臂恢复 V 差异范数（协变量，不是承载比例）。

##### 3. 预算

| 阶段 | 形成 | 评分 | 校准 |
|---|---:|---:|---:|
| 预检（P01-f0/f1，1 worker；首输入另做 C/T4146 重建评分） | 12 | 52 | 1 |
| 正式（12 输入，2 worker） | 60 | 300 | 6 |
| 合计 | 72 | 352 | 7 |

形成 token 前向与 prefill 次数另记在回执。GPU ≤0.5 设备小时，产物 ≤2 GiB；预检工程失败可记账后重试一次；正式不重试。全词表 logits 张量（约 12 MB/输入）留在服务器 `runs/*/worker-*/tensors/`，Git 只提交记录与哈希清单。

##### 4. 工程闸门（任一不过即停止）

名单哈希；FIX+REST = U+Ubar = 448、U 与 FIX 逐层配平、Ubar 与 REST 逐层配平；校准与 GPU 分配等于 B3；L0 写入 ≤1%；**旧哈希重放**：C 与 T_nat、T_V、T_FIXV、T_RESTV、T_U 的首步 logits 哈希、更新后缓存哈希与 argmax 都等于 FX-01 正式记录（C 另等于 NR C_native，T_nat 另等于 NR T_native）；C 的 argmax = q0；V 臂组装逐通道核对（q/k = T、列出头 V = C、其余 V = T），S/KV/浅层哈希 = T；供体不变；评分前无 hook；预检重建一致。

##### 5. 出口

无论可加、超加、次加或混合，本补测都到此关闭；不重筛名单、不扩层、不加随机子集。结果只修正 FX-01 的解释，不影响 SVQ-01。

##### 6. 交付

`runs/{preflight,formal}-r01/`（记录与回执入 Git，张量在服务器）、`analysis/fxs-readouts-r01.json`、`REPORT.zh-CN.md`。

---

### 原件 4：FXS-01（固定名单恢复的首步固定候选连续分数）结果报告

原路径：`experiments/cache-fx-fixed-score-followup-v1-2026-11-02/REPORT.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-fx-fixed-score-followup-v1-2026-11-02/REPORT.zh-CN.md) · [单独阅读副本](../library/a1986cef9f61615f.md)；SHA-256：`a1986cef9f61615f3515efa81cff3502d1dcebfc93010d8b7303c3e08797ee92`。

---

#### FXS-01（固定名单恢复的首步固定候选连续分数）结果报告

日期：2026-11-02。[合同 r01](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-fx-fixed-score-followup-v1-2026-11-02/CONTRACT.zh-CN.md)；[决策 D1–D6](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-fx-fixed-score-followup-v1-2026-11-02/DECISIONS.zh-CN.md)；计划 v1（5b6127c，评审撰写）+ 修订 v2（032a17c）。代码 `8147edb`，freeze-r01 `d5bcbff4…039c`。P 面板与 FX-01 离散结果已见；本轮新测的是首步数值 logits 与新臂 T_Ubar。同一助手实现、运行与撰写。

##### 1. 结论（不利的先说）

1. **“联合成功只是各自跨不过阈值、合起来跨过”在固定名单切分上不成立。** 在固定候选分差 m = z(q0) − z(s0) 上，FIX/REST 切分 3/4 方向为**超加**（N4146、N1210、R0 都是 6/6 或 5/6 情景超加），C1343 混合。J_FIX 均值 2.3–4.4 logit，容差 τ 约 1.0–1.2；全部 48 个输入中 J_FIX 最小 −0.19、最大 5.5。最不利精度汇总不改变任何方向标签。按冻结定义“与首步阈值解释相容”的输入只有 0/0/2/3（N4146/N1210/R0/C1343）。
2. 这只是**输出分数上的非加和**，不定位内部哪一步计算产生它，也不证明 FIX 特殊（合同 §2）。
3. **随机切分 U/Ubar 在 4/4 方向混合**（J_U 均值 0.9–1.7，多个情景落在 τ 附近，精度敏感 2–5 个输入）。逐输入 J_FIX > J_U 为 12/11/10/9（共 12）。一份随机切分只是配对参照，不是零分布，**不能说 FIX 切分的超加显著大于随机**。
4. **描述性观察（合同外的读法，单份随机切分）**：恢复 Ubar（U 的补集，403 头）的 V，首步 argmax = q0 有 11/12/11/12；恢复 REST（FIX 的补集，同为 403 头）为 0/48。两者被恢复的 V 差异范数几乎相同（436–464 对 436–464），δ_Ubar 8.4–10.2 对 δ_REST 2.4–3.6。也就是说，**从全部 V 恢复里拿掉固定 45 头，首步效应大部分消失；拿掉这一份随机 45 头则基本保留**。这只在首步、只对这一份 U 成立；Ubar 没有做自然续写，不能说它恢复完整交付。
5. 工程全部通过：C 与五个旧 T 臂的首步 logits 哈希、更新后缓存哈希、argmax 都与 FX-01 正式记录逐位相同。

##### 2. 读数（12 输入均值，logit）

| 方向 | m_nat | δ_V | δ_FIX | δ_REST | J_FIX | 标签 FIX | δ_U | δ_Ubar | J_U | 标签 U | 阈值相容 |
|---|---:|---:|---:|---:|---:|---|---:|---:|---:|---|---:|
| N4146 | −7.02 | 11.31 | 3.97 | 2.95 | 4.39 | 超加 6/6 | 0.29 | 9.28 | 1.73 | 混合 | 0 |
| N1210 | −6.33 | 11.21 | 5.67 | 2.37 | 3.17 | 超加 6/6 | 0.48 | 9.29 | 1.44 | 混合 | 0 |
| R0 | −6.11 | 9.74 | 3.92 | 3.50 | 2.32 | 超加 5/6 | 0.42 | 8.38 | 0.94 | 混合 | 2 |
| C1343 | −6.60 | 11.92 | 7.06 | 3.57 | 1.29 | 混合（超加 4/6） | 0.76 | 10.21 | 0.95 | 混合 | 3 |

首步 argmax = q0（共 12）：T_V 12/12/12/12，T_Ubar 11/12/11/12，T_nat、T_FIXV、T_RESTV、T_U 全为 0。停止赢家在所有臂都是 248046。q0 − 全词表其他最大值的均值：T_V +1.7 到 +2.2，T_Ubar +0.9 到 +1.6，T_FIXV −1.2 到 −3.8，T_RESTV −2.7 到 −4.1。被恢复 V 差异范数：T_V 460–489，REST 与 Ubar 436–464，FIX 与 U 147–156。U 与 FIX 重叠每输入 4–10 头。

精度：FIX 切分精度敏感输入 0/0/2/7，U 切分 2/4/5/5；最不利汇总（敏感输入记未定）下方向标签与原标签完全相同。

##### 3. 执行

| 阶段 | 形成 | 评分 | 校准 | 墙钟 | 峰值显存 |
|---|---:|---:|---:|---:|---:|
| 预检 r01（1 worker） | 12 | 52 | 1 | 51 s | 9.8 GB |
| 正式 r01（2 worker） | 60 | 300 | 6 | 103 / 103 s | 9.7 GB |

合计约 0.07 GPU 设备小时（上限 0.5）。形成 token 前向：预检 312、正式 1560。全词表 logits 张量在服务器 `runs/*/worker-*/tensors/`（正式每 worker 约 75 MB），哈希在各 worker 的 `receipt.json`。

##### 4. 解读与出口

- 对 FX-01 的修正：FX-01 的“单独失败、联合成功”在分数层面**不是**完全可加（固定切分 3/4 方向超加），所以“分数完全可加、只是合起来越过阈值”不足以描述它。分数超加与行为跨阈值可以同时发生，因此不写“不是跨阈值”；也不能把它叫内部协同，这需要内部测量。
- 固定 45 头在这里的位置比 FX-01 显示的更强：单独恢复它们的首步分差 δ_FIX（4.0–7.1）大于其余 403 头（2.4–3.6），且从全部 V 中拿掉它们会让首步效应大部分消失，而拿掉一份同规模随机名单不会。这些都是首步、单份随机参照的描述，**不重开固定名单分支**（合同 §5），也不主张必要性。
- 按合同，本补测到此关闭。

##### 5. 可以说 / 不可以说

| 可以说 | 不可以说 |
|---|---|
| 首步固定候选分差上，FIX/REST 切分 3/4 方向超加，阈值相容输入只有 5/48 | FX-01 的联合恢复是内部协同 |
| 一份随机切分 U/Ubar 4/4 方向混合，逐输入 J_FIX > J_U 42/48 | FIX 切分的超加显著大于随机 |
| 恢复 Ubar（403 头）首步选 q0 46/48，恢复 REST（403 头）0/48，二者恢复范数相同 | Ubar 能恢复完整交付；固定 45 头是必要的 |

---

### 原件 5：FXS-01 / SVQ-01 修订 v2（对 5b6127c 计划 v1 的增补）

原路径：`docs/cache-v-followup-amendments-v2-2026-11-02.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/docs/cache-v-followup-amendments-v2-2026-11-02.zh-CN.md) · [单独阅读副本](../library/dee733eabda70572.md)；SHA-256：`dee733eabda70572e7dcee2e980aea7d3189509b1bdfbe94a807af8c65dbc969`。

---

#### FXS-01 / SVQ-01 修订 v2（对 5b6127c 计划 v1 的增补）

2026-11-02。本文件只增补，不改动 v1 计划正文；合同以 v1 + 本文件为准。两个实验的问题、臂、判据、预算与推进顺序（先 FXS、后 SVQ）均不变。

##### A1（SVQ）诊断分叉的历史重放验收
SP-01 正式记录已保存 T_shared（T 状态下强制共同首 token）与自然臂的第二步三个候选分数（目标第二 token 与两个干扰第二 token）。新增工程闸门：
- 每方向 T_nat 的同前缀诊断分叉，三个候选分数与 SP-01 对应 T_shared 第二步逐位相同；
- C_nat 与 T_F：在自然首步等于共同首 token 的单元上，诊断分叉三个候选分数与 SP-01 自然第二步逐位相同；首步不同的单元不要求一致；
- 任一不符按工程失败停止，不当科学结果。
由此明确：T_nat/C/T_F 的 M 已在 SP-01 中测得，本轮新测量主要来自 T_V 与 T_QK。

##### A2（SVQ）T_F 是参照，不是上限；逐输入配对表
- 删除“完整恢复构成部分恢复的表现上限”这一假设。R0 的 T_F 在 SP-01 为 4/6 情景成功（SP03-f0、SP06-f1 未交付），不推出 T_V 或 T_QK 不能达到 5/6；恢复更多分量不保证单调改善。
- 主判据不变：不降门槛、不排除 R0，不写“整体达标须其余三方向全过”。
- 每方向逐输入报告配对表：F 对/V 错、V 对/F 错、都对、都错；QK 同样对 F 报告，另报 V 对 QK。
- V（或 QK）优于 F 是有意义的结果，如实报告，不当异常排除，也不事后解释为工程问题。

##### 不采纳
- FXS 不扩到 C2 文件中的四份随机子集：仍不构成可靠零分布，不改变主判；保持一份冻结 U/Ubar 配对参照。

##### 预算
A1 只比较已计费的诊断前向，A2 只是读数；两份上限（0.5、1 GPU 设备小时）不变。本文件不授予模型运行权。

---

### 原件 6：FXS-01 决策日志

原路径：`experiments/cache-fx-fixed-score-followup-v1-2026-11-02/DECISIONS.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-fx-fixed-score-followup-v1-2026-11-02/DECISIONS.zh-CN.md) · [单独阅读副本](../library/6fb79618ff9ba270.md)；SHA-256：`6fb79618ff9ba2704de10d2b7fde54eb595728fb554f2b534887825401a5329e`。

---

#### FXS-01 决策日志

- **D1 计划由评审撰写**（5b6127c），修订 v2（032a17c）不扩四份随机子集。
- **D2 runner 复用 FX-01**：直接 import fx_run 的 v_restore、restored_norm、记录读取与名单；评分用同一 L.forward，单步。
- **D3 旧哈希重放比 FX 计划要求更强**：除首步 logits 哈希外，还核对评分后更新缓存哈希与 argmax（FX 记录都有）。
- **D4 精度的“最不利汇总”定义**：计划只说“最不利翻转汇总”。冻结为：精度敏感输入在汇总中记为未定，不能计入任何标签（因此只会让方向标签更难成立，不会凭空制造标签）。
- **D5 “阈值相容”的可操作定义**：计划写“实际首步选词符合各臂跨越候选边界”。冻结为：T_V 首步选 q0、T_FIXV 与 T_RESTV 首步都不选 q0，且 J_FIX 近似可加。
- **D6 间距的 dtype**：按原始 logits 张量的 dtype 取尾数位（bf16 7 位、fp32 23 位）；记录中保存 dtype。

---


## 时间、运行与停止收据索引

下面是所收集JSON的原有时间字段与状态，不把预计结束时间当实际完成时间。未列时间的文件仍有原件链接。完整JSON全部保存在原文归档，不能以此索引中的标量代替完整嵌套内容。

| 原件 | 原记录状态/阶段 | 原时间字段（原时区） |
|---|---|---|
| [readiness/cpu-receipt-r01.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-fx-fixed-score-followup-v1-2026-11-02/readiness/cpu-receipt-r01.json) | {"status": "passed"} | {} |
| [runs/formal-r01/controller.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-fx-fixed-score-followup-v1-2026-11-02/runs/formal-r01/controller.json) | {"status": "completed", "stage": "formal"} | {"started_at": "2026-11-02T05:18:48.834370+00:00", "finished_at": "2026-11-02T05:20:34.078123+00:00"} |
| [runs/formal-r01/verification.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-fx-fixed-score-followup-v1-2026-11-02/runs/formal-r01/verification.json) | {"status": "passed", "stage": "formal"} | {"verified_at": "2026-11-02T05:20:34.077905+00:00"} |
| [runs/formal-r01/worker-0/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-fx-fixed-score-followup-v1-2026-11-02/runs/formal-r01/worker-0/receipt.json) | {"status": "completed", "stage": "formal"} | {"started_at": "2026-11-02T05:18:48.930186+00:00", "last_record_at": "2026-11-02T05:20:29.611949+00:00", "finished_at": "2026-11-02T05:20:31.688758+00:00"} |
| [runs/formal-r01/worker-1/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-fx-fixed-score-followup-v1-2026-11-02/runs/formal-r01/worker-1/receipt.json) | {"status": "completed", "stage": "formal"} | {"started_at": "2026-11-02T05:18:48.930303+00:00", "last_record_at": "2026-11-02T05:20:29.815350+00:00", "finished_at": "2026-11-02T05:20:31.893766+00:00"} |
| [runs/preflight-r01/controller.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-fx-fixed-score-followup-v1-2026-11-02/runs/preflight-r01/controller.json) | {"status": "completed", "stage": "preflight"} | {"started_at": "2026-11-02T05:17:43.683965+00:00", "finished_at": "2026-11-02T05:18:37.750496+00:00"} |
| [runs/preflight-r01/verification.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-fx-fixed-score-followup-v1-2026-11-02/runs/preflight-r01/verification.json) | {"status": "passed", "stage": "preflight"} | {"verified_at": "2026-11-02T05:18:37.750338+00:00"} |
| [runs/preflight-r01/worker-0/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-fx-fixed-score-followup-v1-2026-11-02/runs/preflight-r01/worker-0/receipt.json) | {"status": "completed", "stage": "preflight"} | {"started_at": "2026-11-02T05:17:43.776750+00:00", "last_record_at": "2026-11-02T05:18:33.182755+00:00", "finished_at": "2026-11-02T05:18:35.191356+00:00"} |

## 全部原始资产入口

本目录在固定提交下共有66个跟踪文件，包含代码、原回答、失败、收据和压缩证据；文件数不是样本数。[逐文件完整账本](../assets/074-cache-fx-fixed-score-followup-v1-2026-11-02.tsv) · [原目录](https://github.com/yuxiexiong/acupuncture/tree/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-fx-fixed-score-followup-v1-2026-11-02)。未复制模型权重、环境或凭据。
