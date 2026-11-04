# 痛点候选七步查重：转向／稀疏干预把损伤写进混合模型的递推状态

2026-11-05。检索由本会话的子代理执行（WebSearch + WebFetch），主会话整理。**不是穷尽综述；候选痛点仍是推测档，查重结果只回答"被占到哪里"，不回答"值不值"。** 对应论文工作稿 §8（三件分开的事之一）与 §9。

## 候选主张（查重对象）

在含 Gated DeltaNet 递推层的混合模型（Qwen3.5／Qwen3-Next 一类）上，激活转向或稀疏激活干预会把损伤写进固定大小的递推状态 S；S 不像 KV 可以逐 token 丢弃或重算，所以针对 KV 污染的修复（按 token 门控/裁剪注意力贡献、驱逐被转向的 KV 条目）在这类架构上不适用；要修，得知道损伤经哪个写入／读取操作进入状态。痛的人：在混合架构上做 persona／安全／能力转向的人，以及做缓存级防御的人。

## 结论

**部分空着。**

- 已被占：**输入侧状态污染可持久** —— HiSPA（2601.01972，EMNLP'26 Findings）用短触发串把 Mamba 状态推入收缩域并不可逆覆写，Jamba-1.7-Mini、Nemotron-3-Nano 混合模型同样崩；其两篇后续防御 CLASP（2603.12206）、SpectralGuard（2603.12414）只检测不修复。**persona／语言由递推通道承载、检索由 KV 承载** —— 2609.04434 已建立（Qwen3.5、Falcon-H1；递推单独检索→0，persona 70–80% 经递推）。
- 最近邻：2603.16335 在 Qwen3.5-35B-A3B（3 GDN:1 Attn）上做 SAE 探针向量残差转向，decode-only 无效、prefill-only 有效，§5.3 归因"经 GatedDeltaNet 递推状态传播"，**作者自认是推断、未测量**。2609.04721 在 Zamba2-7B 混合模型上把拒绝方向加在 SSM 块写入点，只报误拒率，无持久性或状态分析。
- 空着的三件：(1) 无人测过转向／稀疏干预在 GDN 状态 S 里的持久性与损伤（2609.32102 明说"恢复／持久／因果使用需分别测量"；2404.05971 只说残差转向"已经影响状态"）；(2) 无人检验 KV 级修复（2605.10664 的 GCAD）在混合架构上是否失效 —— 2605.10664 被引 8 篇无一涉及 SSM／混合，2609.33093 被引 0；(3) 无人把损伤定位到 GDN 的写入项／擦除项／读取操作。
- 削弱：2605.07755（NeurIPS'26）显示仿射 SSM（Mamba 系）注入的状态误差经全局对角衰减自然收缩 —— **未测 DeltaNet**；三篇状态量化工作（2609.30950、2609.38169、2610.15139）则报告误差按通道衰减率持久、长解码累积。GDN 上谁对未定；本项目 CFM-S1 的"L0 撤针后不衰减、L12 衰减"是自有数据，尚未与这两派对表。2602.17691（HELIX）在 Granite 4.0 H 上只改约 10% 注意力层绕开 Mamba-2 层漂移，是实务上的回避式解法，说明有人已经在绕，不是没人痛。
- 实务抱怨存在但无人归因到递推状态：persona-lab（Qwen3.5-4B）高剂量敌意／切语言／循环；llama.cpp 分支 PR 审查指出转向后 KV 条目跨请求泄漏，只提 KV 不提 GDN 状态；atlas PR#1132 按向量 ID 分 KV 前缀缓存，"SSM 状态是否需同样分键未处理"；2604.11120 报告 Qwen3.5-9B/27B 对转向的 ASR 低于 prompting，作者无架构解释。这既是"无人知道痛在哪"的证据，也可读作"无人在痛"，两可。

**对论文的含义（主会话判断，不是检索结果）：** 痛点要从推测档升到可写，还缺本项目自己的两条证据：转向型（非单坐标）干预在 S 中的持久性读数，以及 KV 级修复在同一受针运行上失效的直接演示。两者都不在现有资产里，也不在 NWR-01 范围内；是否立项另议。单坐标 down_proj 干预到转向向量的迁移是**类比档**。

## 命中表（按步）

### 步 1 抽象阶梯
查询：`activation steering Mamba state space steering vector persistent effect recurrent state`；`steering vectors RWKV OR Mamba OR "linear attention" "representation engineering" hybrid`；`activation patching Mamba causal intervention SSM state`；arXiv API `steering AND (DeltaNet|linear attention|state space|Mamba|RWKV) AND (activation|intervention)`。

| 命中 | 说了什么 | 对主张 |
|---|---|---|
| 2404.05971 Does Transformer Interpretability Transfer to RNNs（正文） | Mamba-2.8B/RWKV-v5 上 CAA 有效略弱；状态转向与残差转向不可加，解释为"残差转向已经影响状态"；未测持久 | 支持前提，未量化 |
| 2602.22719 Activation Subspace Bottlenecks（摘要） | Mamba 系 7 模型 Δ 敏感子空间缩放转向；无持久／副作用分析 | 无关 |
| 2609.32102 Residual Streams Read, Recurrent States Remember（摘要） | Mamba-1/2/3 状态 Jacobian lens + 状态转向；"恢复／持久／因果使用需分别测量" | 支持"空着" |
| 2609.04721 Locating and Steering Refusal Beyond Attention（正文前 100k） | Falcon-Mamba-7B、RWKV-6、Zamba2-7B；拒绝方向加在 SSM 块写入点；开环误拒 86% | 部分削弱：写入点转向已有；无持久分析 |
| 2603.16335 Behavioral Steering in a 35B MoE（正文） | Qwen3.5-35B-A3B；decode-only 无效、prefill-only 有效，归因 GDN 状态传播（推断）；α>5 崩 | 最近邻 |
| 2602.17691 HELIX（摘要） | Granite 4.0 H 只在 ~10% 注意力层转向，称足以纠正 Mamba-2 层漂移 | 削弱弱：回避式解法 |
| 2605.12770 WriteSAE（正文前 100k） | GDN/Mamba-2/RWKV-7 写入矩阵 SAE；Qwen3.5-0.8B 三个 cache 位置替换写入；持久性只由遗忘门公式隐含 | 已知近邻，未测持久 |
| 2606.11386、2609.11063（摘要） | 与 SSM 状态持久无关 | 无关 |

### 步 2 方法论单独搜
查询：`"state space" OR Mamba "prompt injection" persistence recurrent state contamination error accumulation`；`linear RNN SSM perturbation contractive Lyapunov "error propagation" Mamba-2 "gated delta"`；arXiv API `("hidden state"|"recurrent state") AND (poisoning|contamination|persistent) AND (Mamba|"state space"|"linear attention"|hybrid)`；`"Hidden State Poisoning" defense OR "state reset"`。

| 命中 | 说了什么 | 对主张 |
|---|---|---|
| 2601.01972 HiSPA（摘要） | 短触发串不可逆覆写 Mamba 状态；Jamba/Nemotron-3-Nano 混合同样崩；无修复 | 占"输入侧状态污染持久" |
| 2603.12206 CLASP、2603.12414 SpectralGuard（摘要） | 逐 token 分类／谱半径监控，只检测 | 占"检测"；"修复经哪个操作"空 |
| 2605.07755 Error Control Dynamics（正文前 100k） | Mamba/Mamba-3 经全局对角衰减收缩注入误差；token-gated RNN 放大；未测 DeltaNet | 削弱 (b) |
| 2609.30950、2609.38169、2610.15139（摘要） | 混合／delta-rule 状态量化误差按通道衰减率持久、长解码累积 | 蕴含"写进 S 的扰动按衰减率留存" |
| vLLM PR #56524 | 混合模型 Mamba 状态块分配时清零防跨请求污染 | 工程侧已意识到状态残留 |

### 步 3 蕴含检索
查询：`hybrid model attention vs recurrent layers ablation retrieval dominated by attention Jamba Zamba Nemotron-H`；`steering prefill only OR "prefix steering" vs generation persistence recurrent`；`steering Mamba decays OR half-life OR fades after intervention`。

| 命中 | 说了什么 | 对主张 |
|---|---|---|
| 2609.04434（摘要） | 检索只经 KV；语言／persona 经递推（70–80%） | 支持：persona 转向落在递推通道 |
| 2609.33093（正文） | 递推替换恢复 <1–3.6%、KV 96–100%；干扰由后续写入与目标方向重叠决定；未测衰减 | 削弱检索类；写入重叠机制可借用 |
| 2510.19861（摘要） | Jamba-Mini/RecurrentGemma 去注意力检索归零 | 削弱：检索无人痛 |
| 2609.32942 The Key Handoff（摘要） | 末注意力层后的递推层仍可写入事实改答案 | 支持：递推是可查询记忆 |
| 2610.04967 Prefix Steering、2609.11020（摘要） | transformer 上单 token 前缀转向持续影响；KV 轨迹移植改 persona | 相邻，transformer 侧 |

### 步 4 同义术语枚举
词表：steering vector / activation addition / ActAdd / CAA / RepE / concept vector / ITI / activation patching / SAE steering / control vector / cache steering / state steering / write-site；Mamba(-1/2/3) / RWKV(-5/6/7) / GLA / DeltaNet / Gated DeltaNet / Jamba / Zamba / Samba / Hymba / Qwen3-Next / Qwen3.5 / Nemotron-H / Nemotron 3 / Falcon-H1 / Granite 4 H / Bamba / MiniMax-01 / RecurrentGemma / Griffin / xLSTM。组合查询见子代理记录。命中：clehaxze.tw gemlog 2026-04-12（非同行评审，正文）：RWKV-7 直接编辑递推状态改事实、200 token 后仍有效、同实体属性串扰。其余架构除 2609.04721（Zamba2）、2602.17691（Granite 4 H）外无转向工作。中文检索无命中。

### 步 5 引用链（Semantic Scholar）
| 源 | 被引 | 相关的 |
|---|---|---|
| 2605.10664 | 8 | 无一涉及 SSM／递推／混合 |
| 2609.33093 | 0 | — |
| 2609.04434 | 4 | 2609.32942、2610.26830 |
| 2605.12770 | 2 | 2609.25053 LatentPort、2610.28753 |
| 2601.01972 | 2 | CLASP、SpectralGuard |
| 2404.05971 | 12 | 2609.32102、2609.04721、WriteSAE；无混合模型转向持久性工作 |

### 步 6 对抗式检索
- (a) 有人在 Mamba／混合上转向并报告持久效应或修复？无多轮／持久测量；最近 2603.16335（推断）、2609.04721（只报误拒）。未被占。
- (b) delta-rule 擦除项会自然冲掉扰动？无 GDN 扰动注入实验。2605.07755 证 Mamba 系全局衰减收缩（未含 DeltaNet）；由 2609.33093 可推：与后续 key 正交的扰动不被 delta 项擦、只随 α 衰减 —— 推导档，无人测。
- (c) 行为主要由 KV 决定？检索类：是。persona／语言／风格：否（2609.04434、2609.32942）。痛点在 persona／安全转向上成立，在检索类不成立。
- (d) 实务抱怨：见结论段；存在但无人归因到递推状态。

### 步 7 边界申报
- Semantic Scholar 被引滞后；Google Scholar、OpenReview 未查，在审稿件未覆盖。
- 非 arXiv：Research Square 两篇（rs-10023075、rs-11201314 "Where the Answer Is Born"，GDN 0.8B/27B 因果干预）只有标题，正文取不到。
- 非英文：仅一条中文查询；日／韩／俄未查。
- 检索截至 2026-11-04 的 arXiv 列表；2611 月内投稿可能未索引。
- 未读完：2605.10664 附录 J、WriteSAE 后 60k、2609.04721 后 166k、2605.07755 后 59k。

### 真正取到正文的
2605.10664（前 100k）、2605.12770（前 100k）、2404.05971、2609.04721（前 100k）、2605.07755（前 100k）、2609.33093、2603.16335、2604.11120（前 100k）、clehaxze gemlog、persona-lab README、llama.cpp 分支 PR#1、atlas PR#1132。其余只有摘要。
