# 项目文档目录

**2026-11-03｜WCP-01 编程工程验收：** [数据、评分/隔离、0.8B与4B编译干预及资源复核](../experiments/wsp-coding-painpoint-v1-2026-11-03/REPORT.zh-CN.md)。四类模块验收通过；保留BF16运行时/编译不等价反例。新增约0.458GB、磁盘余量约269.57GB；4/10 GPUh仅停止线，完整ETA未验证。正式搜索未启动，WCP阶段调度与编辑器阶段权限仍待接入。

**2026-11-03｜WSP 编程扩展 WCP-01（仅方案，未运行）：** [0.8B / 4B 独立痛点诊断与稀疏干预](wsp-coding-painpoint-v1-2026-11-03/PLAN.zh-CN.md)｜[完整设计自查](wsp-coding-painpoint-v1-2026-11-03/SELF_CHECK.zh-CN.md)｜[预算](wsp-coding-painpoint-v1-2026-11-03/BUDGET.json)。Python 函数任务，MBPP 开发、HumanEval+ 独立终验；最多12个候选，含随机/反号及原版非思考对照。全流程停止线4/10 GPUh，包含终验。逻辑自查通过，工程待验收；本轮0模型/GPU，数学50-pass与编程搜索均未启动。

**2026-11-03｜NPC-01 结果：L12 没有任何两两组合致错（q/k 保持干净的本轮条件下，18 条错误只有三块同时换入才出现）；L0 有 18/48 条在含 S 的两块时就出错（其中 S＋KV 的 16 条选第一个编号，2 条 S＋V 复述列表）；V＋KV 从不致错，已测组合内受损 S 是必要组成条件但单独不足。** [报告](../experiments/cache-native-pair-combination-v1-2026-11-03/REPORT.zh-CN.md)。C 为接收者：L0 的 S＋V 45、S＋KV 32、V＋KV 48；L12 三者均 48。逐条最小组合：L0 为两块 18（S＋KV 15、S＋V 2、两者 1）、三块 28、未致错 2；L12 为三块 18、未致错 30。两两组合的错误类型与联合受损不同。约 0.14 GPUh，无偏离。

**2026-11-03｜NPC-01 方案（设计，未冻结、无 GPU 授权）：V、S、KV 两两组合的反向移植。** [方案](cache-native-pair-combination-v1-2026-11-03/PLAN.zh-CN.md)。干净接收者中换入受损的 S+V、S+KV、V+KV（每针 3 格），与单组、V+S+KV、全部深层逐条配对；回答“最少哪两块一起受损就致错、S 是否必须在场”。估计 0.2 GPUh。

**2026-11-03｜NQK-01 结果：受损 q/k 历史单独不致错；不含 q/k 的 V＋S＋KV 组合足以致错，在 L0 上几乎逐条重现全部深层受损。** [报告](../experiments/cache-native-qk-history-v1-2026-11-03/REPORT.zh-CN.md)。C 为接收者：CQK 两针均 48/48；CVSK 在 L0 为 2/48（CJ 为 2，46 条改坏输入完全重合、41 条文本相同），在 L12 为 30/48（CJ 为 31，复现 15/17、新增 3）。联合致错不是因为漏测的 q/k。登记的"CQK 致错"预测落空。约 0.17 GPUh，无偏离。候选：V/S/KV 两两组合。

**2026-11-03｜NSR-01 结果：受损深层 S（或 V、KV）单独放进干净运行都不致错，只有全部深层受损才出错；另一条输入的干净 S 会把答案改写成供体的答案。** [报告](../experiments/cache-native-s-reverse-v1-2026-11-03/REPORT.zh-CN.md)。C 为接收者：L0 的 CS/CV/CK 均 48、CJ 2（停止 18＋混合 28，T 为停止 47）；L12 的 CS/CV/CK 均 48、CJ 31（= T，逐位相同）；CSx 10 对、38 错选，其中 32 条正是供体答案。三条工作预测全部落空。**更正 NCC-01**：L12 的浅层与入口不受针影响，L12 的 TJ = C 是构造必然。约 0.21 GPUh，无偏离。

**2026-11-03｜NSR-01 方案（设计，未冻结、无 GPU 授权）：受损深层 S 能否把损伤带进干净运行。** [方案](cache-native-s-reverse-v1-2026-11-03/PLAN.zh-CN.md)。以 C 为接收者，在 τ 只换入同输入 T 的 G 层 S（主臂 CS），比较 CV/CK/CJ，并以另一条干净输入的 S（CSx）作失配对照；两针、48 条、主读数自然完整回答与异常类型（停止/错选/混合/其他）。估计 0.2–0.3 GPUh。

**2026-11-03｜NCC-01 结果：只恢复深层递推 S，L0 与 L12 的完整回答都全部恢复；L0 上开头恢复（V 历史）与答案恢复（S）分开。** [报告](../experiments/cache-native-carrier-comparison-v1-2026-11-03/REPORT.zh-CN.md)。τ 在最后提示 token 前、浅层与入口保持受干预。L0：T 0、TV 16（已知）、TS 48、TK 3、TJ 48；L12：T 31，四个单组均 48。L0 的 TV 46/48 以编号开头但多选错编号，TS 多以重开 think/引导语开头却全对；首步分差排序两针相同（TJ>TV>TS>TK），与 L0 完整回答排序不同。登记的"TS 单独较弱"预测被否证（与先前首步分数结果不冲突：TS 只补回 L0 首步缺口约 33%）。约 0.17 GPUh，无偏离。候选：反向移植检验污染充分性。

**2026-11-03｜NCC-01 已冻结上卡（合同 r01）：** [方案](cache-native-carrier-comparison-v1-2026-11-03/PLAN.zh-CN.md)／[合同](../experiments/cache-native-carrier-comparison-v1-2026-11-03/CONTRACT.zh-CN.md)。在第一个回答 token 前对 L0/N4146 与 L12/C3621 分别恢复深层卷积 V 历史、S、KV 或全部深层缓存（TJ 含卷积 q/k），比较原生首步与自然完整回答；TV 两针均桥接到既有 V 背景记录（已知参照）。CPU 6/6、冒烟闸门全过。结果另报。

**2026-11-03｜NMT-01 结果：k 条件效应的来源差大部分随“原生方向＋逐层逐头幅度配置”复现，单格效应与随机内容不行。** [报告](../experiments/cache-increment-norm-match-v2-2026-11-03/REPORT.zh-CN.md)。原生接收背景 Φ_up 0.75/0.86/0.91、Φ_dn 0.98/0.86/0.90（3/3 接近参照，N4146 贴门槛）；恢复接收背景 Φ_up 0.63/0.80/0.73、Φ_dn 0.93/0.85/0.85（1/3 接近、2/3 部分）；I_S 已匹配（比 0.98–1.04）。单格 M 未对上（UP 低 0.27–0.96，DN 高 0.13–0.31）；随机内容 Φ 为负、统一缩放 0.15–0.38。固定 k 时完整回答：放大补回 12/18、7/12、3/5。按冻结出口不进入跨条件迁移；候选：按 b 拆分增量（共同部分 vs 对比部分）。约 0.59 GPUh，无偏离。

**2026-11-03｜NMT-01 v2 已冻结上卡（合同 r01，冻结 86827bd6）：** [方案 v2](cache-increment-norm-match-v2-2026-11-03/PLAN.zh-CN.md)／[自查](cache-increment-norm-match-v2-2026-11-03/SELF_CHECK.zh-CN.md)／[合同](../experiments/cache-increment-norm-match-v2-2026-11-03/CONTRACT.zh-CN.md)。固定接收背景，SIT 增量逐层逐头双向缩放（UP/DN × r × b，8 格），次要 UPG 与 RND(K=5)；一阶参照数据前已登记（缺口方向 Φ_up 0.84–1.24、Φ_dn 0.90–1.07、Φ_UPG 0.25–0.54，只作参照）。CPU 13/13、真实模型冒烟 r03 闸门全过（r01/r02 冒烟为冻结前工程失败，已修，DECISIONS D7–D8）。结果另报。

**2026-11-03｜NMT-01 范数匹配实验卡（设计，未冻结、无 GPU 授权）：** [实验卡](cache-increment-norm-match-v1-2026-11-03/PLAN.zh-CN.md)。固定接收背景，把原生来源状态增量逐层逐头放大到恢复来源幅度（UP）、反向把恢复来源缩小（DN），两接收背景各 b=0/1；次要臂：写入位置保留、内容随机（K=5）与总范数统一缩放。读法分“幅度复现 / 幅度不足 / 单侧 / 背景依赖”，各对应下一步；不证明单调性。估计 0.4–0.7 GPUh。另：零 GPU 三件已加作者更正（DIV-01 收窄“层内差异只能来自方向”）。

**2026-11-03｜跨条件预测线：零 GPU 三件已交付，未冻结、无计算授权。** [检验集盘点](cross-condition-predictor-v1-2026-11-03/INVENTORY.zh-CN.md)／[竞争候选](cross-condition-predictor-v1-2026-11-03/CANDIDATES.zh-CN.md)／[预注册草稿](cross-condition-predictor-v1-2026-11-03/PREREG_DRAFT.zh-CN.md)。调查中同层同剂量的写入范数恒为 d·m，层内通道差异（如 9B L0 首步 EOS [0,8,8,0,8,0,5,0,8,8]）只能来自方向；四个候选：幅度/位置、停止 token 对齐（静态权重）、传播放大、输入压平后回落默认输出。三阶段：回顾性盲算（0 GPU，结局多已见过）→ 新通道前瞻 → 针对候选的因果干预。待审定判据与规模。

**2026-11-03｜SIT-01 结果：恢复背景产生的留存增量能跨输出背景起作用（幅度与方向未分开）。** [报告](../experiments/cache-state-increment-transfer-v1-2026-11-03/REPORT.zh-CN.md)；[合同 r01](../experiments/cache-state-increment-transfer-v1-2026-11-03/CONTRACT.zh-CN.md)；[方案](cache-state-increment-transfer-v1-2026-11-03/PLAN.zh-CN.md)（取代 SDT-01，SDT 未执行）。三个缺口方向：恢复来源增量移入原生输出背景，k 条件效应 +0.53～+0.76（G=DS1−DS0 的 0.40～0.57）；在恢复背景换回原生来源，损失 0.74～1.55（G 的 0.77～0.83），固定 k 时完整正确数少 18/12/5 条（扣主效应后的交互 17/4/2）；均为 6/6 场景、32/32 输入同号。深层（≥20 层）增量范数相差 1.5～3 倍，行为收益中幅度占多少未测；原生一侧 t1 已停，Y 无信息；C1343 模式不同。0.35 GPUh，工程闸门全过，无偏离。

**2026-11-03｜SDT-01状态差移植方案已交付，未运行：** [方案与自查](cache-state-delta-transfer-plan-v1-2026-11-03.zh-CN.md)。基于NBR固定状态/读者/梯度后的离线更正，保留接收者基底，只换留存状态差；16–22层双向、24–30层正向，6新格+8旧参照，拟总上限1.5 GPUh。作者逻辑自查通过，工程验收待完成，无新模型运行授权。

**2026-11-03｜WSP 工程准备检查点（未开始搜索）：** [代码、待办与验收收据](../experiments/wsp-process-reproduction-v1-2026-11-03/README.md)。Astra/max 实际调用通过，4B 全文件哈希复验及 426 个文本张量导出核验通过，CPU 沙箱基本接口和数学评分有限测试通过；两模型初始提示已独立冻结。0.8B 权重、独立推理环境与完整前向运行器仍在准备。用户选择等现有任务结束后使用空闲 GPU。

**2026-11-03｜NBR-01结果及离线更正（探索性）：** [报告](../experiments/cache-native-bridge-record-v1-2026-11-03/REPORT.zh-CN.md)。原表混合读者与梯度，已拆开重算：固定读者/梯度后，状态来源投影效应稳定；单换读者投影变化小；下游敏感度依赖线性化点，降为未定。目标投影集中16–18及22层，24–30层变化大但投影弱；尚未证明任一量足以解释行为。后续见上方SDT方案。NBR实际0.31 GPUh，离线重算无新GPU。

**2026-11-03｜NBR-01 只记录重放（探索性诊断）已冻结上卡：** [计划](cache-native-bridge-record-plan-v1-2026-11-03.zh-CN.md)：逐位重放 NVB 八格，补测端点状态差（ΔS_a、ΔS_b、交互 I_S）跨输出背景的异同、t2 的 D/E/W 读出、同一 q 交叉读取与 ∂M/∂o 一阶投影；不设机制标签与分支切点。上限 0.8 GPUh。结果另报。

**2026-11-03｜NVB-01 结果：只改留存 v 不够，增强主要在与输出支路恢复结合时出现。** [报告](../experiments/cache-native-bridge-v1-2026-11-03/REPORT.zh-CN.md)：保留原生 t1 输出、只把留存 v 换成局部 v1，k 效应增量 DS0 为 +0.25～+0.62，三方向都超过 K=19 随机族，但只占联合恢复 DF 的 0.11～0.34；预注册 P1（≥2/3 方向占比 ≥0.5）不成立。恢复输出支路后，同一留存操作增量 DS1 为 +1.45～+2.12，并使完整回答 +11～+23。0.67 GPUh；预检 r01 为一次合同执行失败（DEVIATIONS D1）。

**2026-11-03｜NVB-01 v2 已定稿并授权上卡：** [v2 方案与自查](cache-native-bridge-plan-v2-2026-11-03.zh-CN.md)把主比较移到原生一侧（保留原生 t1 输出及非 S 缓存，只把留存状态中的 v 换成 LVK 局部 v1），加匹配随机族 K=19（有限样本秩比较，结论只限该族），判读表不强行三分类。合同与代码：[`experiments/cache-native-bridge-v1-2026-11-03/`](../experiments/cache-native-bridge-v1-2026-11-03/CONTRACT.zh-CN.md)；CPU 测试 9/9、就绪检查通过；总上限 1.5 GPUh。结果另报。

**2026-11-03｜缓存机制线三项待办，先推进原生连接：** [To-do](cache-mechanism-todo.zh-CN.md)按原生连接、入口形成、目标相关特征依次推进；[NVB-01 第一轮方案与自查](cache-native-bridge-plan-v1-2026-11-03.zh-CN.md)从同一 T 出发拆分 t1 局部 v 的当前输出与留存状态用途，四个新条件加四个 LVK 参照。仅完成作者逻辑自查；未实现、未运行，无新 GPU 授权。

**2026-11-03｜缓存机制线骨干，更新至 SRU 正式结果与更正：** [理论与实验证据链](cache-mechanism-theory-evidence-spine-2026-11-03.zh-CN.md)逐环对齐激活入口、历史形成、写入、状态、读取与完整回答，列明公式假设、实验原值、跨轮连接条件、阴性与未闭合环节。当前支持条件性的写入—读取—行为链，不宣称完整原生机制；本次仅整理证据，无新实验或推广方案。下方“未运行”条目保留历史交付身份。
**2026-11-03｜SRU已完成并更正；CGV三项边界探索设计已交付，未运行。** [新针眼／新场景／原生背景方案](cache-chain-generalization-plan-v1-2026-11-03.zh-CN.md)与[作者自查](cache-chain-generalization-self-check-v1-2026-11-03.zh-CN.md)：固定L0两根新链路针2191/3152、三种结构27条新任务、未恢复V的原生T去偏移与C加偏移，三项独立不交叉。复用LVK/SRU操作；原生停止不强行续写，条件M与自然交付分报。逻辑自查与CPU核对完成，先探索边界、再在边界内确认；卡时为估计，不设固定GPU硬上限；分词/实现/模型验收待完成，尚未运行模型。下方保留历史状态。

**2026-11-03｜WSP双模型安排（v2，未运行）：** [0.8B过程复现＋4B独立方法扩展及自查](wsp-process-reproduction-0p8b-4b-v2-2026-11-03.zh-CN.md)。核对作者以Codex CLI调用gpt-6-astra/max（认证方式未公开）；两模型各自从原始权重独立搜索50pass，4B不读取0.8B补丁/结果，完整终验共51584回答。已只读确认4B资产目录、配置hash与分片大小；工程/完整权重核验及运行预算待完成，无新模型/GPU运行。本条扩展下方v1的模型范围。

**2026-11-03｜WSP从原始0.8B复现全过程（计划，未运行）：** [完整计划](wsp-process-reproduction-v1-2026-11-03.zh-CN.md) · [作者自查](wsp-process-reproduction-self-check-v1-2026-11-03.zh-CN.md) · [来源与资源收据](wsp-process-reproduction-sources-v1-2026-11-03.json)。按实验8进行一次50-pass自主搜索，隔离作者最终答案，复用公开提示、练习题及评测代码，补齐未公开harness；保留全部候选、失败、原文及请求张量。逻辑自查通过，工程/模型验收及正式成本尚未冻结，无新模型/GPU运行。

**2026-11-03｜WSP 方法档案：** [《权重空间编程（WSP）：原始资料、研究方法与 Acupuncture 应用档案》](literature/weight-space-programming-acupuncture-2026-11-03.zh-CN.md)。统一收录作者与公开资源、八组实验、数学修复过程和精确补丁、20.3小时成本口径、复现限制及两条研究线的用途；原核查文件已原位扩充，未新增模型实验。

**2026-11-03｜保留海盗角色、修复任务能力（讨论稿，未运行）：** [简短 proposal 与作者自查](pirate-persona-capability-repair-mini-proposal-2026-11-03.zh-CN.md)。核对既有五题角色/跑题表现，拟借鉴WSP搜索局部修复，同时衡量数学、文字、逻辑任务及角色保持；不预设广泛能力损失。执行合同与预算未冻结，无模型/GPU授权。

**2026-11-03｜LVK已完成并更正；下一步SRU-01读取计算计划，未运行。** [主线定位与实验计划](cache-state-read-use-plan-v1-2026-11-03.zh-CN.md)及[作者自查](cache-state-read-use-self-check-v1-2026-11-03.zh-CN.md)：LVK把V依赖推进到可改变完整答案的t1写入操作；下一步沿L10/L11，在t2直接读取/旧预测修正两种S用途上做双向四格，q自由响应、不移植持久S，检验写入差怎样被使用。只用既有48新文本（现为已见机制面板），1536轨迹含基线重放，拟总上限1.5 GPUh。CPU来源与代数核对、作者逻辑自查通过；模型实现/验收/授权未完成，0新模型调用。下方计划状态按日期保留。

**2026-11-03｜Weight-Space Programming 原始方法与当前资产对照：** [核查报告](literature/weight-space-programming-acupuncture-2026-11-03.zh-CN.md) · [来源清单](literature/weight-space-programming-sources-2026-11-03.json)。先核对最新 KUC/NVW 与 LVK 状态，再读公开代码、搜索日志和补丁；区分稀疏权重修复、条件性计算解释与跨模型迁移。此次仅资料核查，无模型/GPU运行。

**2026-11-03｜KUC/NVW 已完成；LVK-01 下一阶段计划已自查，未运行。** [局部v×写入k计划](cache-local-v-k-plan-v1-2026-11-03.zh-CN.md)与[作者自查](cache-local-v-k-self-check-v1-2026-11-03.zh-CN.md)：KUC支持V已恢复背景下的t1写入项作用；NVW确认其强背景依赖，原生完整交付未达多场景改善（N1210有0→1/48）。下一轮固定T背景四格及同六场景48条新输入，检验局部v替换能否复现增强；只做R家族，旧参照复用，拟2544自然轨迹、总硬上限1.8 GPUh。逻辑设计通过，文本已冻结，分词/实现/模型数值验收待完成，无本轮运行授权或新模型调用。下方“未运行”条目为历史交付状态。

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
