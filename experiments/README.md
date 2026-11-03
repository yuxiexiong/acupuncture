# 实验目录：按研究问题查找

- [SIT-01 写入增量跨输出背景转移](cache-state-increment-transfer-v1-2026-11-03/CONTRACT.zh-CN.md)（2026-11-03）：NVB 八格重放＋4 个 t1 后 ΔS 移植格（全 14 个 G 层，双向）；只报连续值；探索性。方案 [docs](../docs/cache-state-increment-transfer-v1-2026-11-03/PLAN.zh-CN.md)。
- [NBR-01 NVB 八格只记录重放](cache-native-bridge-record-v1-2026-11-03/CONTRACT.zh-CN.md)（2026-11-03）：不加条件；端点状态差、t2 读出分解、同一 q 交叉读取、∂M/∂o；探索性。

- [NVB-01 原生输出下的留存 v 用途](cache-native-bridge-v1-2026-11-03/CONTRACT.zh-CN.md)（2026-11-03）：LVK 新面板 48 条×4 方向；8 个用途格（4 个重放 LVK）＋匹配随机留存族 K=19；主读数 DS0＝e(0,1)−e(0,0)。计划 [v2](../docs/cache-native-bridge-plan-v2-2026-11-03.zh-CN.md)。

- [QST结果复核与QCO预算附件](cache-query-state-result-review-v1-2026-11-02/README.zh-CN.md)（2026-11-02）：1380轨迹CPU重算、624参照记录比对；不是模型重跑。QST实测已完成，QCO仅计划，无新GPU授权。

- [QST-01设计与CPU检查](cache-query-state-transfer-design-v1-2026-11-02/README.zh-CN.md)（2026-11-02）：48输入、132配对、36主对照；来源/分母/预算/判据合成反例已核对。拟正式1380自然轨迹；仅设计附件，不是新模型结果。

**缓存机制线最新｜2026-11-02：** [QC-01 结果](cache-query-layout-coverage-v1-2026-11-02/REPORT.zh-CN.md)已完成；[QCD-01 计划与来源核对](cache-coverage-dose-design-v1-2026-11-02/README.zh-CN.md)为下一阶段设计，先查交叉供体/切分敏感性，再比较位置和剂量。[完整自查](../docs/cache-coverage-dose-self-check-v1-2026-11-02.zh-CN.md)仅逻辑通过；本次旧记录CPU核对276份、0新增模型/GPU，拟运行计数不得当作完成资产。不改变下列跨模型线状态。

**跨模型线 F1 预检｜2026-11-02：** [预检报告](cross-model-foundation-common-v1-2026-11-02/PREFLIGHT.zh-CN.md) · [决策日志](cross-model-foundation-common-v1-2026-11-02/DECISIONS.zh-CN.md) · 合同草案 [A](cross-model-history-current-v1-2026-11-02/CONTRACT.zh-CN.md) / [B](cross-model-natural-withdrawal-v1-2026-11-02/CONTRACT.zh-CN.md)。四模型（Qwen3.5-4B、Qwen3-4B、Llama-3.2-3B、Falcon-H1-3B）引擎与面板就位；逐位闸门（权重哈希、缓存复用、挂钩惰性、零剂量、缓存隔离、新进程快照重放）全过；未过/待决：写入 1% 容差（BF16 量化，比值 0.991–1.036）、B 的 k=16 四模型均 0/24 可达且 k=4 常在答案之后、A 干净 Y 饱和于 1.0。实测外推全量约 6 GPUh、深记录约 20–32 GB。合同未冻结，待计划所有者裁决 D4/D5/D8/D9。 **r02（11-02）**：[报告](cross-model-foundation-common-v1-2026-11-02/PREFLIGHT_R02.zh-CN.md)——B 改答案前边界分叉（四模型 k_b=3、可达 24/24，G12–G14 过）、A 加 m（噪声底 0.19–0.44 奈特，1/64 下多在噪声内）、写入沿目标投影 0.997–1.003（偏差为正交舍入）；待 D4、PLAN §6、D8。 **F1 四步（11-02）**：[报告](cross-model-foundation-common-v1-2026-11-02/F1_STEPS.zh-CN.md)——历史回放逐位通过；正式尺度定；校准 d_high=3/4（阶梯顶，未饱和）、d_low=3/8、d_B=3/4；A 的 Y 在 3/4 下几乎不动（主读数恐大面积不可判），写入严格 1% 仅 1/2、3/4 档；1/64 四格 m 效应跨路径不一致。待计划所有者裁决阶梯/任务、d_low、B 边界正则。 **冻结前验收（11-02 晚）**：[报告](cross-model-foundation-common-v1-2026-11-02/F1_CHECKS.zh-CN.md)——3/8 写入 Qwen3/Falcon 略超 1%（不通过）；正式剂量 m 四格跨路径一致（通过）；Falcon 3/4 下 Y 路径差 0.078 > δ；B 边界两形式与三项分开记录，Falcon 浅层整行复述 28/72。待裁决 d_low、Y 路径条件、B 并报全体交付。

**最新分析｜2026-11-01：** [已有张量的原生输出路径CPU分析](cache-output-path-audit-v1-2026-11-01/REPORT.zh-CN.md)完成，来源及算术验收通过，无新模型前向或GPU。第13层删除的原生作用小，不能推广为递推无关；末端投影和词语竞争因情景而异，不能宣布第31层为共同根因。下一优先切入点是“原生当前入口信号＋干净深层历史”这一缺失对照，以区分当前信号与历史的条件作用；尚无新执行合同。资产盘点已更新至[r7](../docs/cache-formation-mechanism-asset-inventory-v1-2026-10-31.zh-CN.md)。下方旧“未运行/下一步”按原日期阅读。

**2026-11-01 当前机制进展：** [统一总结与下一阶段计划](../docs/cache-mechanism-progress-and-next-stage-plan-2026-11-01.zh-CN.md)。机制拆解为主，关键预测形成后阶段性跨针验证。

| 最近实验 | 状态 | 结果入口 |
|---|---|---|
| 形成—读取连接 | 已完成 | [桥接结果](cache-formation-readout-bridge-v1-2026-10-31/analysis/bridge-readouts-r01.json) |
| 缓存组合 A+B | 已完成，正式36前缀/300评分 | [实验入口](cache-formation-cache-combination-v1-2026-10-31/) |
| 跨通道验证 | 已完成，正式1092前缀/1500评分 | [实验入口](cache-cross-channel-validation-v1-2026-10-31/) |
| 第13层局部读取因果检验 | 已完成（阴性：I、J 两背景均弱），正式132评分/0前缀 | [报告](cache-local-readout-causal-v1-2026-11-01/REPORT.zh-CN.md) |
| 卷积历史V/qk拆分（路线图A） | 已完成：V段足够、Q在V干净时部分替代（饱和、非可加）；四条预注册简化均不成立；正式264评分/0前缀 | [报告](cache-conv-factor-v1-2026-11-01/REPORT.zh-CN.md) |
| V/Q重叠路径审计（CPU） | 已完成：重叠始于第13层写入项（读取项交互=0，cos −0.97），逐层传递；停止词方向直接路径交互集中在第27–31层全注意力；答案词方向分散；0模型调用 | [报告](cache-conv-factor-path-audit-v1-2026-11-01/REPORT.zh-CN.md) |
| 阶段B1：第13层V×Q写入交互删除 | 已完成（主判断不成立）：N停止侧删除后输出交互基本不变（ρ≈0）；M_T方向一致缩小12–39%但未达25%×5/6；正式96评分/0前缀 | [报告](cache-vq-write-interaction-causal-v1-2026-11-01/REPORT.zh-CN.md) |
| B1配对传播分析（CPU） | 已完成：冻结筛选下36模块无候选→结束第13层分支；改动进入残差且持续增长，但几乎不朝停止方向；N中真实与随机的单位改动响应都低；0模型调用 | [报告](cache-b1-paired-propagation-v1-2026-11-01/REPORT.zh-CN.md) |
| F_V同入口局部路径分析（CPU） | 已完成：按冻结规则提出按头子集候选（前45头占直接路径投影61–64%，头身份跨输入稳定）；门控不成立（反而放大目标分量）；局部直接路径合计仅占实际F_V效应1–12%（停止侧）；0模型调用 | [报告](cache-fv-local-path-v1-2026-11-01/REPORT.zh-CN.md) |
| B2：V子集×Q依赖 | 已完成：主判断（停止侧B_H(1)）5/6稳定正向；只让45头H的V有针就几乎消掉Q的停止侧作用；答案侧Q依赖随R；一般饱和未排除、H按停止侧选出；正式96评分/0前缀 | [报告](cache-b2-v-subset-q-dependence-v1-2026-11-01/REPORT.zh-CN.md) |
| B2计算后续（CPU） | 已完成：冻结规则下无合格候选——H头同入口写入交互直接投影仅−0.04–0.03（B_H(1) 0.12–0.79）；末端27–31层4/6同向未达5/6；小效应情景中最终分母项与B_H(1)同量级；0模型调用 | [报告](cache-b2-computation-followup-v1-2026-11-01/REPORT.zh-CN.md) |
| C1-P：选头规则新输入前瞻检验 | 已完成（支持，6/6）：新输入上规则选出的45头保留0.93–1.09倍全V停止侧效应，比层配平随机子集高1.95–2.82；旧数据固定名单同样6/6；同针同方向、模板单一、幅度未匹配；28形成/158评分 | [报告](cache-head-rule-prospective-v1-2026-11-01/REPORT.zh-CN.md) |
| C2：固定名单跨干预方向 | 已完成：停止侧4个方向（N4146、N1210、R0、R1）均6/6支持，预注册的随机方向迁移预测成立，3个方向上FIX单独效应超过全V；答案侧FIX 4/4未兑现（保留0.33–0.60）；70形成/578评分 | [报告](cache-c2-cross-direction-v1-2026-11-01/REPORT.zh-CN.md) |

以下保留历史分类目录，不代表新的运行序列。

基础目录快照：2026-10-28（当时22个目录）；最新机制实验见下方当前进展入口，旧表不是当前全部目录计数。中文名称说明实际用途；目录中的英文名和日期是固定实验身份，保留原路径以维持合同、代码、收据和哈希引用。

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
| [早层失效定位：污染存在哪类缓存（第一阶段）](early-state-localization-v1-2026-10-29/) | 4B；KV / 递推状态 / conv 三类缓存逐类拼接，26 条件 × 24 输入，开发＋新题确认 | 已完成：6,576 条；主假设（递推承载）被否；停嘴由线性层局部状态承载，事实丢失分布于 KV 与线性层、来自提示前部 | [结果报告](early-state-localization-v1-2026-10-29/REPORT.zh-CN.md) · [合同](early-state-localization-v1-2026-10-29/CONTRACT.zh-CN.md) |
| [全层缓存差分与阶段二深度比较](early-state-localization-stage2-v2-2026-10-30/) | 4B；全32层×±1 的 KV／递推／conv 八组合差分（开发＋历史复核），选例后 8 个缓存深度组 × 7 子集扫描，新题双向验证 | 已完成：29,112 条；II-B 确认 11/12 检出；中层事实敏感度大部分由 L16–19 递推状态双向承载；中、晚层异常不到回答层面；L0 停止异常不由单组承载 | [结果报告](early-state-localization-stage2-v2-2026-10-30/REPORT.zh-CN.md) · [合同](early-state-localization-stage2-v2-2026-10-30/CONTRACT.zh-CN.md) |
| [缓存形成机制｜CFM-S1｜原始轨迹与状态形成分析](cache-formation-mechanism-s1-native-trace-v1-2026-10-31/) | 4B；C 与原针 L0/C4146/−1、L12/C3621/−1，6 情景 × 2 事实；L16–18 全部递推头逐 token 驱动量、读出与边界残差，离线写入／旧状态处理／读取记账 | 已完成：preflight 3 + formal 36 条，全部逐值复现 II-B；重建与恒等式全过。合同判读两锚点 coupled，但切点未经零分布标定（自然事实差异也判 coupled），信息量低；原针使 L16–18 状态差异达干净状态量级，差异逐 token 持续产生、撤针后 L0 不衰减、L12 衰减 | [结果报告](cache-formation-mechanism-s1-native-trace-v1-2026-10-31/REPORT.zh-CN.md) · [合同](cache-formation-mechanism-s1-native-trace-v1-2026-10-31/CONTRACT.zh-CN.md) · [实现与决策日志](cache-formation-mechanism-s1-native-trace-v1-2026-10-31/IMPLEMENTATION.zh-CN.md) |
| [缓存形成机制｜CFM-S2｜同起点与逐步写入、旧状态处理检验 v3](cache-formation-mechanism-s2-formation-test-v3-2026-10-31/) | 4B；两原针按 E（模板头至事实末）／L（事实后至撤针）开关成 00/10/01/11 四格，12 输入；L16–18 逐步 u_B／u_H／u_N 与 H/N 旧来源追踪，84 条完整 Mτ | 已完成（freeze-r02）：84 条全部过闸门、48/48 同起点逐位认证。排除表全部反驳（区分度低）；同起点第一步写入与处理同时变且反向；t_L 差异几乎全来自 b 后写入；早段撤针后 L0 写入差异仍为直接加针的 38–92%，L12 为 13–53%；r10<0.5 在 L0 失败；L0 停嘴需后段针、事实丢失来自早段针 | [结果报告](cache-formation-mechanism-s2-formation-test-v3-2026-10-31/REPORT.zh-CN.md) · [合同](cache-formation-mechanism-s2-formation-test-v3-2026-10-31/CONTRACT.zh-CN.md) · [实现与决策日志](cache-formation-mechanism-s2-formation-test-v3-2026-10-31/IMPLEMENTATION.zh-CN.md) |
| [缓存形成机制｜CFM-S3 v3｜缓存写入变量的介入式拆解](cache-formation-mechanism-s3-route-intervention-v3-2026-10-31/) | 4B；在 11 运行的 E／L 窗口内把写缓存投影（v、α、k+β、q 通道、注意力 K/V）换成参照值，测撤除恢复量与保留量、内容×处理与 V×K 联合、层范围、撤针后写更新×读取；24 单元 × 130 格 | 已完成（freeze-r02）：3,120 格全部过闸门，48/48 完备性逐位重现参照。只有 L 窗口停嘴分辨得清：写入内容 v 单独即可保住停嘴（L0 保留 1.06–1.11），α 不起作用，(k,β) 在 L0 是不必经的部分冗余通道，承载在首组之后各层；撤针后干净后续条件下停嘴仍保留约一半；事实使用大多证据不足（零对照损伤过大）；P4 失败 | [结果报告](cache-formation-mechanism-s3-route-intervention-v3-2026-10-31/REPORT.zh-CN.md) · [合同](cache-formation-mechanism-s3-route-intervention-v3-2026-10-31/CONTRACT.zh-CN.md) · [实现与决策日志](cache-formation-mechanism-s3-route-intervention-v3-2026-10-31/IMPLEMENTATION.zh-CN.md) |
| [缓存形成机制｜原生事实信号分析 v1（零 GPU）](cache-formation-mechanism-fact-signal-native-v1-2026-10-31/) | 4B；复用 S2 的 84 条轨迹与 Mτ：同条件下 f0/f1 的事实区别，以干净方向为参照，逐层（撤针时）与 L16–18 逐步（v、m、e、o） | 已完成：L16–18 中 e 始终跟着 v（无"错配"情况）；L0 早段针使事实区别在 L1–L3 写入时即转向（事实段 KV 也偏离）；晚段针下事实写得完好、丢在事实之后的携带上；L12 大体保留 | [结果报告](cache-formation-mechanism-fact-signal-native-v1-2026-10-31/REPORT.zh-CN.md) · [分析计划](cache-formation-mechanism-fact-signal-native-v1-2026-10-31/ANALYSIS_PLAN.zh-CN.md) |
| [缓存形成机制｜CFM-E2 v1｜浅层与深层缓存分别怎样影响回答差异](cache-formation-mechanism-e2-depth-transplant-v1-2026-10-31/) | 4B；留出 6 情景 × 2 事实；在撤针边界把 L0·01 的第 0–12 层或第 13–31 层缓存换成 00 或 L12·01 的值，测首步停止优势 D 的保留量 | 已完成：全部闸门通过；6/6 情景"a 强、d 弱"——L0·01 的 D 移动 75–94% 可由第 13–31 层缓存在干净浅层背景中承载，第 0–12 层只承载 10–18%；但 a 格首步停止 0/12（L0·01 为 8/12，D 贴近阈值）；L0 浅层 + L12 深层为 55–66% | [结果报告](cache-formation-mechanism-e2-depth-transplant-v1-2026-10-31/REPORT.zh-CN.md) · [计划](cache-formation-mechanism-e2-depth-transplant-v1-2026-10-31/PLAN.zh-CN.md) · [合同](cache-formation-mechanism-e2-depth-transplant-v1-2026-10-31/CONTRACT.zh-CN.md) |
| [缓存形成机制｜CFM-FORM-AB v2｜深层缓存的形成条件：入口抵消与浅层过去状态](cache-formation-mechanism-formation-ab-v2-2026-10-31/) | 4B；E2 的 6 情景 × 2 事实；L0 晚段针下 C/T/XA/XB/XAB 五个形成条件（A=第 13 层入口减去实测 L0 当步增量，B=第 1–12 层每步读取干净过去缓存），τ 后统一用 C 浅层 + 本格深层评首步 D | 已运行（freeze 73e0eedd，preflight-r01、formal-r01 全部闸门通过，60 前缀/72 评分）：A（入口抵消）6/6 情景两背景均弱；B（浅层读干净过去）在 A 关闭时 6/6 部分削弱（R 0.32–0.52），A 开启时 0.24–0.47；无情景达强；L 内逐 token 路线与 E2 不逐位一致，已登记修订，最大偏差 0.016 Δ_E2 |  [合同](cache-formation-mechanism-formation-ab-v2-2026-10-31/CONTRACT.zh-CN.md) · [实现与决策日志](cache-formation-mechanism-formation-ab-v2-2026-10-31/IMPLEMENTATION.zh-CN.md) |
| [缓存形成—读取连接｜CFM-FORM-READ-BRIDGE v1｜深层 V 与递推状态能否传递 B 效应与整体针效应](cache-formation-readout-bridge-v1-2026-10-31/) | 4B；A5 的 6 情景 × 2 事实；九个形成条件（C/T/H，V 交叉 U/W/TC/CT，同幅随机位移 TR0/TR1），14 个首步评分（含 4 个递推状态交叉），记录最终分母 r | 已运行（freeze 3a4d2601，preflight-r01、formal-r01 全部闸门通过，108 前缀/168 评分）：T 的深层 V 放进无针 C 复现整体深层效应 0.90–1.13，放进 H 恢复 B 差 0.84–1.44；反方向只部分（V_C→T 0.38–0.51，V_H→T 0.43–0.71）；同幅随机位移 −0.13–0.03；只换递推末态多为弱 | [合同](cache-formation-readout-bridge-v1-2026-10-31/CONTRACT.zh-CN.md) · [实现与决策日志](cache-formation-readout-bridge-v1-2026-10-31/IMPLEMENTATION.zh-CN.md) |
| [缓存组合读出｜CFM-CACHE-COMBINATION v1｜V 形成效应经哪些深层缓存组合读出](cache-formation-cache-combination-v1-2026-10-31/) | 4B；bridge 的 6 情景 × 2 事实；(C,CT)、(TC,T)、(C,T) 三对的递推/卷积/KV 全组合交换（每输入 22 格，复用旧缓存）；无针随机 V 参照 CR0/CR1 | 已运行（freeze 87fff079，preflight-r01、formal-r01 全部闸门通过，36 前缀/300 评分）：(C,CT) 单换卷积缓冲 F 0.53–0.74、递推 S 0.25–0.36、KV 0.08–0.13，S+F 0.89–0.98；原生 (C,T) 同顺序、F 0.39–0.57、S+F 0.81–0.90（图样最大差 ≤0.23）；V 清理消掉的部分几乎全在 F/S+F；无针随机 V 位移 0.07–0.27 倍 CT 效应 | [合同](cache-formation-cache-combination-v1-2026-10-31/CONTRACT.zh-CN.md) · [实现与决策日志](cache-formation-cache-combination-v1-2026-10-31/IMPLEMENTATION.zh-CN.md) |
| [L0 跨通道验证｜CFM-CROSS-CHANNEL v1｜效应是否超出一般扰动，V 关系与 V 变化是否跨通道相似](cache-cross-channel-validation-v1-2026-10-31/) | 4B；bridge 的 6 情景 × 2 事实；10 个旧 L0 通道 × {−1,+1,−0.5} 加 4 条同幅随机方向（−1）；14 根 −1 针各做 CT/TC/TR0/TR1；ΔV 几何 | 已运行（freeze 68170cdf，preflight-r01、formal-r01 全部闸门通过，每输入 N4146 与桥接逐位一致，1092 前缀/1500 评分）：随机方向与通道分不开（Δ_deep 12.8–20.1，CT 0.84–1.13，TC 0.31–0.58，TR −0.13–0.05，排秩近均匀，ΔV 余弦三组中位 0.68–0.75）→ L0 同幅写入的一般性质，非通道特有；−0.5 通道分化大但无随机参照 | [合同](cache-cross-channel-validation-v1-2026-10-31/CONTRACT.zh-CN.md) · [实现、结果与决策日志](cache-cross-channel-validation-v1-2026-10-31/IMPLEMENTATION.zh-CN.md) |
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
