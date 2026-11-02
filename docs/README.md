# 项目文档目录

**2026-11-03｜KUC-01更新计算因果设计已交付，未运行。** [t1旧预测修正×新值写入计划](cache-k-update-causal-plan-v1-2026-11-03.zh-CN.md)及[作者自查](cache-kuc-self-check-v1-2026-11-03.zh-CN.md)：直接检验更新项如何改变后续目标竞争和自然完整回答，不以KHC完成或单载体胜出为前提；仅t1操作与持续卷积编辑分开。四方向、随机/C1343保留；逻辑自查通过，模型实现/数值验收待完成，无新GPU授权。本条衔接下方KHC的第二步交接，不改历史结果。

**2026-11-03｜KRD已完成；KHC-01载体设计已交付、未运行。** [固定供体Q的S×KV计划](cache-k-history-carrier-plan-v1-2026-11-03.zh-CN.md)及[作者自查](cache-khc-self-check-v1-2026-11-03.zh-CN.md)：补齐两个部分交换，明确新00对应KRD旧01；允许联合有效，不以单项胜出作为计算研究门槛。第二步仅列t1更新项检验的交接约束，未冻结或授权。作者逻辑自查通过、工程待验收，无新模型/GPU。本条更新下方历史计划状态。

**2026-11-03｜QSR已完成且无候选；KRD-01为新计划。** [k修复后续依赖计划](cache-k-repair-dependence-plan-v1-2026-11-03.zh-CN.md)与[作者自查](cache-krd-self-check-v1-2026-11-03.zh-CN.md)已交付：双向检验S+KV历史包与t2 q节点的受控联合效应，保留卷积直接通路、随机/C1343及自然完整答案。QSR停线不撤回QKF行为证据，也不改旧判据。本轮仅文档/CPU核对，无模型或GPU运行；逻辑自查通过，工程待验收。此条更新下方历史计划状态。

**总体口径更新｜2026-11-03，截至 QKD：** [核心问题、前人解释与当前贡献](cache-mechanism-overall-contribution-2026-11-03.zh-CN.md)统一说明我们相对前几天多解释了什么：共同 q/k 偏移及 k 分量已连接到指定混合背景的完整回答；固定 45 头的完整回答推广失败；旧状态读出仍是待拆清的计算关系，不能把 D 份额当 S 的因果贡献。文献边界沿用 11-01 复核，QSR 尚无正式结果。下方按日期保留历史状态，本次仅文档更新、无新模型/GPU。

**2026-11-03｜QKD及CPU余量分析已完成；QSR仅计划。** [S／q／α分解计划](cache-state-readout-decomposition-plan-v1-2026-11-03.zh-CN.md)与[作者自查](cache-qsr-self-check-v1-2026-11-03.zh-CN.md)已交付：识别旧状态读出差异的计算来源，保留C1343/随机及混合背景边界；不把局部投影当最终logit贡献。预设候选或停线规则，因果替换不在本轮；逻辑自查通过、模型工程待验收，无新GPU授权或运行。此条更新下方QKD未运行的历史状态。

**2026-11-03｜QKF已完成，QKD计算诊断方案已自查、未运行。** [QKF更正结果](../experiments/cache-qk-component-factor-v1-2026-11-02/REPORT.zh-CN.md)支持k分量的条件性修复作用，不证明45°致错或q无用。[QKD计划](cache-k-computation-diagnostic-plan-v1-2026-11-03.zh-CN.md)固定前三步自然/共同前缀观测、真实账本与局部k反事实、随机及C1343对照；[作者自查](cache-qkd-self-check-v1-2026-11-03.zh-CN.md)通过，工程待验收，无新模型/GPU授权。本条更新下方历史计划状态，保留旧原文。

**2026-11-02｜QCO-01已完成，QKF-01分量方案已自查、未运行。** [QCO结果](../experiments/cache-common-offset-v1-2026-11-02/REPORT.zh-CN.md)支持共同偏移在固定混合背景中的双向行为作用；[QKF-01计划](cache-qk-component-factor-plan-v1-2026-11-02.zh-CN.md)固定q/k去除与加入各2×2、两档随机配平、完整交付与交互判读。[作者自查](cache-qkf-self-check-v1-2026-11-02.zh-CN.md)通过，非独立评审；正式3072轨迹、含预检正常3212、最多3352/2设备小时均为拟预算。本次只有文档与CPU核对，无新模型/GPU；工程验收待完成。此条更新下方旧计划状态，保留历史原文。

- [QST结果复核与跨场景共同偏移计划](cache-qst-review-and-common-offset-plan-v1-2026-11-02.zh-CN.md) · [作者自查](cache-qco-self-check-v1-2026-11-02.zh-CN.md)（2026-11-02）：复算原记录，保留阴性与R0例外；QCO仅设计，新增模型/GPU为0。

- [QST-01完整实验计划](cache-query-state-transfer-plan-v1-2026-11-02.zh-CN.md) · [作者自查](cache-query-state-transfer-self-check-v1-2026-11-02.zh-CN.md)（2026-11-02）：查询相关q/k历史的双外来供体定向检验；完整矩阵、工程规则、预算及失败出口。逻辑自查/CPU核对通过，未运行、无GPU授权。

- [下一阶段方向判断与自查：查询相关历史状态的定向作用](cache-query-state-next-direction-v1-2026-11-02.zh-CN.md)（2026-11-02）：比较下一方向对核心问题的实际增量；布局比较暂不优先。附 CPU 配对审计，非可执行运行合同，无新模型/GPU。

**2026-11-02｜QCD-01 形成期位置与剂量（未运行）：** [计划](cache-coverage-dose-plan-v1-2026-11-02.zh-CN.md) · [完整作者自查](cache-coverage-dose-self-check-v1-2026-11-02.zh-CN.md) · [旧记录复算与预算附件](../experiments/cache-coverage-dose-design-v1-2026-11-02/README.zh-CN.md)。先固定受干预缓存、交叉干净V来源，并核对统一切分；通过后才解释等长移窗与双向剂量配平。逻辑通过不等于数值验收或模型/GPU授权。

**2026-11-01 主张审计卡 2（零 GPU）：固定 45 头"方向无关放大器"与"诊断误判为协作"——不上卡：** [审计卡 2](claim-audit-direction-agnostic-amplifier-v1-2026-11-01.zh-CN.md)。(1) FIX 在 4 方向/6 新输入保留停止侧效应是已登记的描述性资产；(2) 方向无关性在 L0→深层 V 这一级就已建立（XCHAN 通道–随机余弦 0.68–0.73、同通道 ±1 余弦 0.67–0.73 为正），FIX 只是落点，"放大器"无增量；(3) 没有误判实例——B3 P2 不成立、B3-P0 信噪比标注、B3-P1 出口 (2) 都是诊断正确拒绝协作读法。留一条可预注册问题 Q-dose（方向无关性是否只在剂量阈值以上成立；XCHAN −0.5 档无随机参照），跨模型计划 §4.1 量程校准会顺带产生所需数据。

**2026-11-01 跨模型基础实验 F0 收据（只读核实，零 GPU）：** [容量与模型可及性](f0-receipts-cross-model-2026-11-01/storage-and-model-access-receipt.zh-CN.md) · [历史回放资产](f0-receipts-cross-model-2026-11-01/historical-replay-assets-receipt.zh-CN.md)。/workspace 余 368G、根盘（含 /data）仅 49G，按 PLAN §10.1 公式 Q 上界 97GiB，外部归档目的地空白；服务器不可达 HF/hf-mirror，可达 ModelScope，三个非门禁模型的 ModelScope config 与 HF main 逐位一致；Qwen3.5-4B（851bf6e）已在 /data、Llama-3.2-3B 已在 deployed_regime 且与 ModelScope 镜像逐位一致（无法对 HF 门禁哈希核验）、Qwen3-4B 与 Falcon-H1-3B 需下载约 15GB；`.venv-bench`（transformers 5.20.2）五个模型模块齐全；Falcon-H1 有 mlp_multipliers [0.354, 0.078] 等乘子。10-29 L2/N5063 回放资产齐全（freeze-r03、模型 851bf6e、k/三臂定义与 r2 逐字相同），差异：中文输入、旧 ±1 剂量、分支长度 128、盲读标签。

**2026-11-01 主张审计卡（零 GPU）：撤针后行为残留的可预测性——不上卡：** [审计卡](claim-audit-withdrawal-residual-v1-2026-11-01.zh-CN.md)。重读 S1/S2/S3/E2/COMBO 与 10-29 撤针三臂：停嘴读数上三处反证（S2 10 臂、S3 post11、E2 a 格撤针后状态/分数偏移保留 0.5–0.9，首步 EOS 均 0/12）；事实读数上撤针时状态差异与层位共线（仅两锚点）；「撤针」在仓库里有时序/计算替换/自由生成三种含义不能混用；r10 是末尾量有泄漏，换成撤针时 ΔS_b 后相关降到 0.26–0.54（n=6 无零分布）。留下两条可预注册候选 P-conv（卷积核 4 → 撤针后 4 token 内 F 承载部分必被覆盖）与 P-self（撤针后 2 token 写入差异），均未上卡。

**2026-11-01 路线图A步：卷积历史V/qk实验已运行：** [结果报告](../experiments/cache-conv-factor-v1-2026-11-01/REPORT.zh-CN.md)。预注册的V主导、Q主导、Q/V可加、F效应原生迁移四条简化描述按冻结规则均不成立；实际结构为饱和型：有针F的V段单独复现整块F效应（A_V/G≈1），V为T时Q冗余（R_Q≈0），V干净时Q单独推一部分且偏停止侧。换回干净V在M与N均6/6情景超过两条同幅随机方向；原生评分后半段8个首步停止在只换回干净F_V时全部消失。预检两次失败已记账（D7 环境变量、D8 重构闸门量到BF16舍入），累计364评分/0前缀。

**阶段B1已完成，主预期不成立｜2026-11-01：** [结果核对与下一步判断](cache-vq-write-interaction-result-review-2026-11-01.zh-CN.md)已复算正式记录：原生评分后半段删第13层V×Q写入交互，停止侧情景变化不到0.05 logit，同一批8个首步停止保持，支持0/6；混合背景交互缩小12%–39%，综合支持1/6。内部交互大不等于该项明显影响原生输出；两背景删除向量范数不同，不推出整个第13层不敏感。124评分＋3模板、0前缀形成已完成；本次仅核对与文档更新，0新模型/GPU。[路线图](cache-mechanism-stage-roadmap-2026-11-01.zh-CN.md)仍推进具体计算解释，先利用已有R/DEL轨迹寻找新的可检验候选，不自动扩层；下一实验未设计/授权。核对记录另列历史路线图冻结版本差异，未改原freeze。

**2026-11-01 第13层实验独立复核：** [计划、代码与结果核对](cache-local-readout-result-review-2026-11-01.zh-CN.md)及[派生复算数据](cache-local-readout-result-review-2026-11-01.json)。核心操作符合单层设计，122个冻结文件哈希匹配，原始记录复算与发布汇总一致；原生背景删交互项的作用很小。纠正原报告：M背景有9格最强非停止词切换，零符号分歧不等于零赢家变化；单层弱作用不能推出第13层不是承载点。本次无新模型运行/GPU，未独立重跑服务器大张量。

**2026-11-01 第13层局部读取因果检验已运行（阴性）：** [方案r3](cache-local-readout-causal-plan-v1-2026-11-01.zh-CN.md)·[结果报告](../experiments/cache-local-readout-causal-v1-2026-11-01/REPORT.zh-CN.md)。按冻结判据，统一浅层M与原生后半段N中删除第13层旧状态×读系数交互I、以及该层全部局部S/F差J，均为“弱”；N中删I的D变化仅±0.03 logit（针效应约19），撤回“该交互承载原生停止效应”这一候选，不推出S/F整体无关或分布在多层。预检32+正式132评分、0前缀，全部闸门（含原生重放逐位）通过。

**2026-11-01 下一轮设计（已于同日运行，见上）：** [旧状态—读取交互到输出的因果检验及完整自查](cache-local-readout-causal-plan-v1-2026-11-01.zh-CN.md)。在统一浅层与原生评分后半段两种背景下，删除第13层已识别的局部交互，检验它对最终词语竞争的作用；包含全部局部变化及同幅随机参照。设计逻辑自查通过，实现/数值/资源待验收；计划上限164次单步评分、0次前缀形成，当前无新模型运行或GPU授权。

**2026-11-01 更新—读取审计：** [已有张量CPU审计报告](../experiments/cache-update-readout-audit-v1-2026-11-01/REPORT.zh-CN.md)与[资产盘点r6](cache-formation-mechanism-asset-inventory-v1-2026-10-31.zh-CN.md)：核实读取路径、同口径停止边际，识别原生针与V钉入在第13层的局部交互差异；该交互到最终输出的因果作用仍未测。无新模型运行或GPU。

**当前口径｜2026-11-01：** 形成—读取连接、缓存组合及跨通道实验已完成。现阶段以机制拆解为主，关键预测形成后用少量其他针眼及随机方向作阶段性检查；非孤例不等于同一完整机制，剂量不是默认下一主线。详见[近期进展与下一阶段推进计划](cache-mechanism-progress-and-next-stage-plan-2026-11-01.zh-CN.md)。本次仅文档更新，无新模型运行。

## 历史更新记录

以下按当时版本记录；旧“未运行”“优先”等不代表当前状态。当前推进顺序以上述计划为准，冻结实验文档保持原样。

**跨通道验证已运行｜2026-10-31：** 按审阅意见改为[方案 v2](cache-cross-channel-validation-plan-v2-2026-10-31.zh-CN.md)（加同幅随机方向、每针 TR、ΔV 几何），[运行](../experiments/cache-cross-channel-validation-v1-2026-10-31/)全部闸门通过。结论先说不利的：在当前面板与 −1 剂量，4 条随机方向和10个L0通道的深层效应、V替换关系及ΔV几何相似，明显降低了单针孤例的担忧；不是统计等效或任意方向普遍有效的证明。−0.5缺随机方向参照，SF组合机制尚未跨针验证。

**跨通道验证优先，未运行｜2026-10-31：** [实验计划与完整自查](cache-cross-channel-validation-plan-v1-2026-10-31.zh-CN.md)固定原十个L0通道，−1主线、+1符号参照、−0.5剂量敏感性，全部十点−1做V双向形成交叉，明确未检出效应与机制关系不同的区别。[旧数据审计](../experiments/cross-channel-planning-audit-v1-2026-10-31/REPORT.zh-CN.md)已核对152条修改记录及8条基线：旧+1全提示调查79/80首步EOS；后续N1210也有其他协议的缓存证据，不能冒充当前V链的复现。跨通道计划先于单针缓存组合计划；C01–C14/E01–E26自查通过，工程/资源待验收。本次仅CPU旧JSON核对与文档，无模型前向或GPU。

**缓存组合读取计划 v1，未运行｜2026-10-31：** [计划、成本与完整自查](cache-formation-cache-combination-plan-v1-2026-10-31.zh-CN.md)承接已完成的形成—读取连接结果 ef4fe2a，在 CT/C、T/TC 两对上检验递推/卷积/KV 全组合；正反互补格去重，每输入16评分含端点。无针随机 V 参照单列形成成本。区分卷积直接存储、组合依赖与自然路径，C01–C14/E01–E26及反方自查通过，工程/资源未验收；本次仅文档，无新模型运行。下方旧方案的“未运行”保留其历史时间身份。

**最终尺度诊断已补入方案，未运行｜2026-10-31：** [形成—读取方案v1 r2](cache-formation-readout-bridge-plan-v1-2026-10-31.zh-CN.md)§5.1/§13明确同题C分母、CPU高精度输出端反事实、排名/竞争结构、舍入边界和修订自查；[资产盘点r4](cache-formation-mechanism-asset-inventory-v1-2026-10-31.zh-CN.md)区分外部先例、条件推导、已有证据和待测量。不新增GPU条件，无模型运行。

**形成—读取连接方案｜2026-10-31：** [同针V交叉与递推状态交叉方案v1](cache-formation-readout-bridge-plan-v1-2026-10-31.zh-CN.md)承接资产盘点r3的缺测量，明确5个形成条件、10个评分、补录量、判读与完整自查。设计逻辑通过；实现/数值/资源待验收，未运行模型或GPU。

**已有张量核对完成｜2026-10-31：** [资产盘点v1 r3](cache-formation-mechanism-asset-inventory-v1-2026-10-31.zh-CN.md)新增B12、输出竞争分解和缺失测量表；[审计报告与复算证据](../experiments/cache-formation-asset-audit-v1-2026-10-31/REPORT.zh-CN.md)记录先自查后CPU核验12份旧张量与72份logits，无新模型运行/GPU。

**形成结果已纳入资产盘点｜2026-10-31：** [结果资产盘点 v1 r2](cache-formation-mechanism-asset-inventory-v1-2026-10-31.zh-CN.md)新增 A5 与同源支撑 B9–B11，收录形成实验的逐情景读数、数值路线修订、行为边界及下一步顺序。正式结果见固定提交 `181d80a`；下方方案阶段“未运行”是历史状态，本次整理未新增模型运行。

**资产盘点后的形成检验｜2026-10-31：** [深层缓存形成条件方案 v2 与完整自查](cache-formation-mechanism-next-step-plan-v2-2026-10-31.zh-CN.md)。承接 E2，具体定义入口抵消、浅层过去状态固定、统一评分背景、不同结果的认识增量及退出条件；设计逻辑自查通过，工程与耗时未验收，未运行模型或 GPU。 执行合同与代码见 [CFM-FORM-AB v2](../experiments/cache-formation-mechanism-formation-ab-v2-2026-10-31/)（路线修订见其决策日志第 1 条）。下方旧方案状态保留其历史身份。

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
