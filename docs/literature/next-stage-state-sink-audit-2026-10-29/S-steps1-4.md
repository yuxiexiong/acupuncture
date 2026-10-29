# S 线查重笔记：七步协议第 1–4 步

日期：2026-10-29。范围：只做 S1–S4 的第 1–4 步（抽象阶梯、方法论单独搜、蕴含检索、同义术语）。第 5–7 步不在本笔记。本笔记只写覆盖，不写新颖性，不给等级。
前轮依据：`prior-audit-2026-10-28.md`（C1–C5，20 条查询，13 篇全文定向）。本轮在其基础上深读，并对前轮两处判读给出更正（第 0 节）。

档位标注：**推导** / **类比** / **推测**（CLAUDE.md 5.3）。

---

## 0. 坏消息与对前轮的更正（先说）

1. **更正前轮：2608.12149 的 PAS 删除实验不是在 Qwen3.5 上做的。** 前轮写"删最大 4 坐标下游准确率相对降 21.9%–63.6%"，同时写"覆盖 12 个公开检查点，含 Qwen3.5"，读起来像 Qwen3.5 上有删除证据。全文 §4.3 与附录 F.1 明确：删除与连接两种干预只用了"six released M-A-P GDN checkpoints spanning two scales (340M and 1.3B)"。Qwen3.5 只有观测图（35B-A3B Base/Instruct、122B-A10B、397B-A17B，图 19、26）和一个**增益型**探索（Qwen3.5-27B 上的 spike-to-plateau connection，表 20，GPQA/MATH500 等 +0–1.3%）。全文不出现 "EOS"（grep 计数 0），测量全是 cloze 检索准确率、多选准确率、困惑度，没有输出形态。所以"sink 被破坏 → 首 token EOS"在 Qwen3.5 上没有任何直接证据，前轮的 C5 竞争解释应降为**两步类比**：从 M-A-P 340M/1.3B 的检索掉分，类比到 Qwen3.5-4B 的停止。
2. **对 S2 不利：在同族 Qwen3.6-27B 上，sink 不在 L3 形成。** 2610.16745 附录 F.2："Qwen3.6-27B contains 64 raw blocks, of which 16 are full-attention checkpoints at raw layers 3, 7, . . . , 63. Under the primary qmin = 16 protocol at T = 64, 45/50 prompts cross the sink threshold at least once and 41 first cross at raw layer 15. At T = 256 ... first crossings distributed across raw layers 15, 47, 55, and 59"；且跨越"often non-persistent"。即在 27B 上第一个全注意力层 L3 **未达**该文的 sink 判据。S2"边界与 sink 形成层对齐"如果指 L3 = sink 形成层，在同架构大尺寸上有反向证据（**类比**；尺寸不同、判据阈值是该文自定的 ε）。
3. **对 S2 作为 EOS 机制不利：文献里破坏 sink/massive activation 的输出形态是重复、回声、停用词，不是 EOS。**
   - House of Cards 2410.01866 §2.3："When massive weights are set to zero ..., the model repeats the same text as the user prompt."（引言："the model becomes poor and repeats the user prompt"）
   - Cancedda 2402.09221 §（谱滤波）："the application of Ψ filters often results in the model entering repetitive patterns ... inhibiting attention sinking results in over-copying." 且 "Layers 2-4 are the most fragile"（LLaMa2-13B）。
   - Super Weight 2411.07191：删 super weight 后 "shifting almost all logit probability mass to stopwords"，"Llama-7B generates complete gibberish"。
   - 唯一沾边的是 Jin 2502.01563 附录 A："for the 128-token level task if we eliminate all massive values, the model may not even be able to provide a response"——一句话、无计数、无形态细节。
   推论（**推导**，前提是这些形态可迁移）：如果 S2 的机制成立，我们的现象应该像重复或回声，而我们观察到的是 94–95/96 首 token EOS。要么 Qwen3.5 混合架构下 sink 破坏的输出形态不同，要么 EOS 不来自 sink 破坏。这一分叉文献里没人测过。
4. **S1 的概念骨架被 Jin 2502.01563 部分占据**（见第 3 节）：干预在 prefill 阶段破坏注意力的 massive values → 上下文任务崩溃（passkey 100%→0–2%，IMDB 94%→个位数），参数知识任务基本保留。"干预使上下文不再约束输出、模型仍在运行"这个二分不是新的。干预类型、位置、测量不同。
5. **S4 方法层被覆盖**：事实/反事实 token 的 logit 差是知识冲突机制研究的标准读数（Ortu 2402.11655、Yu et al. 2023），且 Hagström 2412.17031 已公开批评"logit differences ... are not normalised"。S4 必须回应这条批评。

---

## 1. 第 4 步（先列词表）：同义术语枚举

先列词表，再搜。中英对照：

| 概念 | 词表 |
|---|---|
| sink 本体 | attention sink, sink token, position-zero (P0) sink, BOS sink, no-op attention, resting position, attention bar, register token, punctuation sink / delimiter sink, "catch, tag, release", state sink（SSM 版）, 注意力汇聚, 注意力沉没 |
| 大激活 | massive activation, super weight, super activation, massive weights, outlier dimension, dark signals, pre-attention spike (PAS), inter-spike plateau (ISP), massive emergence (ME) layer, massive values (QK), 大激活, 异常值维度 |
| 干预 | steering, activation addition, ablation, zeroing, mean-ablation, noise injection, layer skipping / deletion / swap, early exit, spectral filter, BOS removal, KV eviction, 转向, 消融, 删层 |
| 输出塌缩 | EOS collapse, silence（只出 EOS）, empty response, premature termination, repetition, prompt echo, gibberish, stopword mass, degenerate output, 空答, 提前终止 |
| 上下文使用 | context sensitivity, context reliance, context utilisation, persuasion score, susceptibility, ACU, memorization ratio, context vs. prior knowledge, contextual vs parametric knowledge, context neglect, knowledge conflict, 上下文依赖 |
| 架构 | hybrid model, linear attention, GatedDeltaNet / GDN, gated delta rule, Mamba/SSM hybrid, Qwen3.5, Qwen3-Next, Qwen3.6, Kimi Linear, 混合注意力 |
| 默认输出 | default token, unconditional prior, content-free input, entropy neuron, token frequency neuron, confidence regulation, abstention |

词表逐项入检索见第 6 节查询日志（Q24–Q31 为本步专门查询）。中文查询 1 条（Q22），无中文原创文献命中，只回到英文论文。

---

## 2. 第 1 步：抽象阶梯

模板：**在深度 d 之前的变换 T 摧毁上下文使用，使输出塌缩为默认 token。** 拆三格：(a) T 的类；(b) "上下文不再被使用"的证据；(c) 输出形态是否为 EOS/空答。

| T | 代表工作 | (a) 深度定位 | (b) 上下文使用丢失 | (c) 输出形态 | 读取 |
|---|---|---|---|---|---|
| 等范数随机替换/冻结前 token 隐藏态 | Ben-Artzy 2409.03621 | 早层致命、后 30–50% 层无损 | 是（任务掉到随机水平；Italy→France 早层跟改） | 未报告形态 | 前轮全文定向 |
| 删/换第一层 | Lad 2406.19384 | 第一层致命 | 推断"对当前 token 失明" | 未报告 EOS | 前轮全文定向 |
| 置零 massive activation | Sun 2402.17762 | 单层（LLaMA2-7B L2 首现） | 未测上下文 vs 参数 | 只报困惑度与 zero-shot 准确率；表 3 置零→困惑度爆炸，置均值无损 | 本轮全文定向（§3–4, 表 3） |
| 置零 massive weights（早层 FFN gate/up 行） | Oh, House of Cards 2410.01866 | 早层单层 | 未测 | **重复用户提示**（§2.3 原句见 §0.3）；图 1(b) 为图片，文字未抽出 | 本轮全文定向（摘要、§1、§2.3） |
| 删 super weight | Yu 2411.07191 | 早层 down_proj（Llama-7B L2） | 未测 | 乱码；停用词概率×2–5（"the" ×2，"." ×5） | 本轮全文定向（§3、图 5） |
| 谱滤波压掉 dark signals / sink 分量 | Cancedda 2402.09221 | "Layers 2-4 are the most fragile"（LLaMa2-13B） | 未测 | **重复模式**，归因于 over-copying | 本轮全文定向（§4–5） |
| 破坏 Q/K 中的 massive values（prefill） | Jin 2502.01563（ICML 2025） | 全层（未逐层扫） | **是**：上下文任务崩、参数知识保留 | 准确率为主；附录 A 一句"may not even be able to provide a response" | 本轮全文定向（摘要、§3.3–3.4、附录 A） |
| 删 PAS 最大 4 坐标（全注意力层输入，首 token） | Su 2608.12149 | 每个全注意力层前 | 检索掉得最狠（NIAH-3 −88.45%，FDA −66.23%，PIQA −4.77%） | 未报告形态；无 EOS | 本轮全文定向（§4.3、附录 F） |
| 谱扰动 sink 形成前隐藏态 | Yang & Song 2610.16745 | sink 前 2–3 层 | 测 sink 本身，不测任务 | 未报告 | 本轮全文定向（摘要、§4、附录 F.2） |
| 移除 BOS | Barbero 2504.02732；Peng 2603.06591 | Llama 移除 BOS 只影响前两层 sink | 测表示混合/过度平滑 | 未报告形态 | 本轮全文定向（§3–4；Peng §4 表 1） |
| 单组件零化（混合模型） | Borobia 2603.22473 | Qwen3.5-0.8B：attention L15、linear L0、attention L7、L3 敏感 | 未测 | 只报 MMLU/ARC 准确率与困惑度 | 本轮全文定向（§4.4） |
| 强转向 | LessWrong "instruct vectors"（Qwen3-4B-Base）；Cegin 2606.18389 | 未指明层 | 未测 | ">4x multiplier causes the model to immediately end generation"；"Llama models frequently collapse at higher α values (e.g., repetition or empty outputs)" | 帖子经 WebFetch 摘要器转述（不算读过）；2606.18389 全文 grep 到原句 |
| 层跳过 / early exit | LayerSkip 等 | — | — | 检索未见 EOS 报告 | 仅检索片段 |
| 自然发生的只出 EOS | "Well, Keep Thinking" AID 2503.10167（ACL Findings 2025） | 无干预 | — | 命名为 "silence"：只返回 `<eos>` | 仅检索片段 |

阶梯结论：
- (a)+(b)"早层/形成层之前的干预使上下文失效"在替换、删层、massive values、PAS 删除上都有，模板层被占（前轮已判，本轮加 Jin 与 2608.12149）。
- (c)"塌缩为 EOS/空答"在 sink/大激活这一类 T 下**没有**被报告为主形态；报告的是重复、回声、停用词、乱码。强转向下"立即结束/空答"有两条非同行评审或附带提及的观察，无层定位、无机制。

---

## 3. 第 3 步：蕴含检索（逐篇深读）

### 3.1 Su 等，*Massive Activations in Hybrid Linear Attention LLMs: Pre-Attention Spikes and Inter-Spike Plateaus*，2608.12149v3（在审）

- 模型：观测 12 个公开检查点（Kimi Linear、Qwen3.5 35B-A3B Base/Instruct、122B-A10B、397B-A17B、Nemotron-H、Zamba2）；受控预训练 340M GDN；**干预只在 6 个 M-A-P GDN 检查点（340M、1.3B；ρ=12/6/3）**。
- 干预：对每个全注意力层输入 p_i = f_i − 1 的**首 token**，TopK(|z|, k∈{1,2,4}) 坐标置零；或 spike-to-plateau 连接。
- 测量：十项准确率（PIQA、ARC-E、HellaSwag、FDA、SWDE、SQuAD、NQ、NIAH-1/2/3）+ WikiText 困惑度。原文："Deleting only four coordinates per full attention input reduces ten-task mean accuracy in all six models, with relative losses of 21.91%–63.60% ... Retrieval is particularly sensitive: cross-model relative losses reach 66.23% on FDA and 88.45% on NIAH-3, compared with 4.77% on PIQA."（§4.3）
- EOS/空答：未报告（"EOS" 全文 0 次）。
- 混合/线性：是，核心对象。Qwen3.5 小模型（2B/4B/9B）不在内。
- 机制：write–sink–cancel——"layer 11 writes the outlier; during layer-12 full attention, its ..."（§4.1，340M 模型 full attention 在 L12）；标点与首 token 承载（"the initial token, 'Summer,' and the first period"）。
- 覆盖：S2 **部分覆盖（类比，两步）**。它蕴含"破坏全注意力层输入处首 token 的 PAS → 上下文检索大幅受损、常识题几乎不受损"，这与 S1 的"上下文不再约束、参数类不全坏"同向。它不蕴含停止形态，不涉及加性写入，不涉及 Qwen3.5 小模型，也不涉及"写入最后位置之前"的位置依赖。
- 与前轮不一致：见 §0.1。

### 3.2 Jin 等，*Massive Values in Self-Attention Modules are the Key to Contextual Knowledge Understanding*，2502.01563（ICML 2025）

- 模型：Llama3-8B、Gemma2-9B、Qwen2.5-7B 等（RoPE 模型），对照 OPT、Jamba（无 RoPE）。
- 干预：prefill 阶段把 Q、K 中 massive value 维度替换为均值（或零/极值）；对照为破坏非 massive 维度。原文："Our disruption ... is specifically targeted at the prefilling stage, as disrupting both prefilling and decoding stages would compromise the model's fundamental language modeling capabilities."（§3.3）
- 测量：准确率、困惑度、2-gram 多样性。
- 结果原文："Passkey Retrieval tasks collapse from 100% to near-zero accuracy (0-2%) across all difficulty levels, while IMDB sentiment analysis performance plummets from above 94% to single digits across all models."；参数知识任务 "Cities tasks maintain relatively strong performance with scores achieving from 76% to 88%"（§3.4）。
- EOS/空答：附录 A.2 一句："if we eliminate all massive values, the model may not even be able to provide a response."
- 混合/线性：只把 Jamba 作为"无 RoPE 无集中"的对照，未做干预。
- 覆盖：S1 **部分覆盖（概念层被占）**。"干预使上下文知识不可用、参数知识大体保留、prefill 阶段即可"已发表。未覆盖：残差流加性写入、单通道、"首个全注意力层之前"的深度边界、配对事实敏感度读数、首 token EOS 形态。S3 只有一句旁证，不构成覆盖。
- 注意：Jin 的"参数知识保留"是闭卷 QA 准确率；我们的 R 是提示事实的配对敏感度，两者不是同一个量。不能把 Jin 写成"支持我们的 R≈0"。

### 3.3 Yang & Song，*Before Attention Sinks Form*，2610.16745

- 模型：Qwen2.5、GLM-Z1、GPT-OSS；附录 F.2 观测 Qwen3.6-27B（混合，全注意力在 3,7,…,63）。
- 干预：sink 形成前隐藏态奇异值编辑，对照为等范数随机谱扰动。
- 测量：后续 sink 行为、下一层对位置 0 的 QK 偏好；不测任务输出。原文："Larger perturbations can cause broader functional changes"（§9 局限），未展开。
- EOS：无。
- 覆盖：S2 方法先例（对照设计可借）；Qwen3.6 结果对 S2"L3 对齐"**不利**（§0.2 原文）。

### 3.4 Peng 等，*What Makes Position Zero Special?*，2603.06591v2（在审）

- 结论：P0 sink 由两块子网络（P0-Sink Circuit）产生，不需要语义内容；Llama 移除 BOS 只影响前两层 sink（"Removing [BOS] affects only the first two layers"）；Qwen 不用 BOS。
- 附录 D：**Qwen3-4B（稠密）** "the attention sink becomes prominent after layer 7, coinciding with the sharp increase in the ℓ2 norm at position zero"（图 13）。
- 覆盖：S2 背景。对 Qwen3.5 无数据。若把 Qwen3-4B 的 L7 类比到 Qwen3.5-4B，sink 并不在 L3 形成（**类比**，弱：架构不同）。

### 3.5 Sun 等 2402.17762、Oh 等 2410.01866、Yu 等 2411.07191、Cancedda 2402.09221

见第 2 节表格行与 §0.3 原文。共同点：破坏首 token 的大激活/sink 分量，输出塌缩为**重复/回声/停用词/乱码**；无一报告首 token EOS 为主形态；无一做"上下文 vs 参数"的配对读数（Jin 除外）。对 S3 构成**形态层面的反向类比**。

### 3.6 Barbero 等，*Why do LLMs attend to the first token?*，2504.02732（COLM 2025）

- sink 用来防止 over-mixing；Gemma 7B 去掉 BOS 后单 token 扰动在表示中扩散更广（§4，图 2）。
- 覆盖：S2 理论背景。方向上它预言"sink 被毁 → 信息过度混合、表示趋同"，与"上下文不可用"可兼容，但不预言 EOS。**被蕴含：无。**

### 3.7 Borobia 等，*Component Ablation for Efficient Hybrid LMs*，2603.22473v2

- Qwen3.5-0.8B 单组件零化："Attention layer 15 produces the largest average drop ... followed by linear layer 0. Attention layers 7 and 3, as well as several early linear layers, also show elevated sensitivity."（§4.4）
- 覆盖：Qwen3.5 族早层敏感的模板层先例（删组件，非加性），无输出形态、无上下文读数。

### 3.8 其余

- 2605.08504（ME 层，Qwen3-4B/8B 稠密 L7）、2510.06477（定理 1、BOS-MLP 消融）、2603.05498（大激活与 sink 可解耦）：前轮已读，本轮只核对未改判。2603.05498 的"each phenomenon can be independently suppressed without degrading language-modeling performance"（检索摘要转述，本轮未在正文定位）若成立，进一步削弱"破坏大激活 → 停止"的必然性。
- Yona 2503.08908（重复 token 破坏 sink 电路 → 发散）、Zhang 2502.00919（Catch, Tag, Release，标点 sink）：取到 PDF，未定向阅读，不计入。

---

## 4. 第 2 步：方法论单独搜（S4）

S4：强制续写两候选（本事实/另一事实），对两版提示取"对数似然差的差"，作为题目信息是否仍被使用的读数；以相对原版的保留比 R 报告。

| 工作 | 量 | 与 S4 的关系 | 读取 |
|---|---|---|---|
| Ortu 等，*Competition of Mechanisms*，2402.11655（ACL 2024） | 事实 token t_fact 与反事实 token t_cofa 的 logit（logit lens 逐层） | 同一族读数：两候选 logit 对比，提示中注入反事实 | 全文定向（§3–4） |
| Yu, Merullo, Pavlick 2023（in-context vs memorized） | 同上 | 同上（经 Ortu 与 Hagström 引用确认，未取正文） | 二手 |
| Du 等，*Context versus Prior Knowledge*，2404.04633（ACL 2024） | persuasion score = 上下文与答案的 half-PMI（有/无上下文分布的 KL）；susceptibility | 同一目的的分布级度量 | 全文定向（§2 定义） |
| Hagström 等，*A Reality Check on Context Utilisation for RAG*，2412.17031 | ACU：按可增长空间归一化的概率变化 | **直接批评** S4 所属读数："Works in mechanistic interpretability often rely on logit differences for a specific token given evidence (Ortu et al., 2024; Yu et al., 2023), which are not normalised, do not factor in ..."（§5.2） | 全文定向（§5.2） |
| Minder 等，*Controllable Context Sensitivity and the Knob*，2411.07404（ICLR 2025） | "Paris is in England" 式反事实上下文 + 跟随上下文/先验的准确率；单层 1 维子空间 | 同类配对设计；也是"上下文敏感度可被单方向控制"的先例 | 仅摘要 |
| Lu 等 in-context PVI 2310.12300；Pimentel 等 2106.08367 | 有/无输入的 log 比；V-information | 同一目的 | 仅检索片段 |
| Ben-Artzy 2409.03621（Italy/France 中途替换） | 跟改答案的比例 | 配对反事实 + 干预深度 | 前轮全文 |

判定：S4 **方法层已覆盖**。差分的差分（两事实 × 两候选的交互对比）只是 minimal-pair logit difference 的对称化，检索未见用这个名字的工作，但不构成方法贡献。必须在文中回应 Hagström 的未归一化批评，并说明 R 的零值由对照条件标定（CLAUDE.md 6.3）。

---

## 5. 逐条覆盖判定

| 主张 | 判定 | 层级 | 最强依据 | 空着的部分在哪层 |
|---|---|---|---|---|
| S1 前一半：首个全注意力层前的加性干预使提示事实不再约束输出（配对敏感度≈0） | 部分覆盖 | 概念/模板层被占 | Jin 2502.01563（上下文失效、参数保留）；Ben-Artzy、Lad（早层失明）；2608.12149（全注意力输入处 PAS 删除伤检索） | **对象层**：混合 GDN 架构、残差加性单通道/随机方向、以首个全注意力层为界的逐层扫描、配对事实敏感度 R 的逐层曲线 |
| S1 后一半：表现为首 token EOS/空答而非错答 | 未找到覆盖；有反向形态证据 | — | sink/大激活破坏 → 重复、回声、停用词（2410.01866、2402.09221、2411.07191）；强转向 → 空答为非正式观察 | 对象层 |
| S2：边界与 sink/massive activation 形成层对齐；破坏 sink 形成 → 全注意力层读不到上下文 → 停止 | 前半部分覆盖（类比）；"→ 停止"未覆盖且受反向证据 | 机制层面被 2608.12149 预先提出为可能解释，但不在 Qwen3.5 小模型、不测停止 | 2608.12149；2610.16745 F.2（Qwen3.6-27B sink 首次跨越多在 L15、非持续）对"L3 = 形成层"不利 | 对象层（Qwen3.5-2B/4B 的 PAS 实测位置、sink 破坏下的输出形态） |
| S3：EOS 是"上下文不可用"的默认输出 | 未找到 | — | 只有 Jin 一句话旁证与 AID "silence"（自然发生、无机制） | 对象层；且文献形态与之相反，需要先排除"回声/重复被 EOS 截断"之外的解释 |
| S4：配对候选 log-likelihood 差的差分 | 已覆盖 | 方法层 | Ortu 2402.11655；Du 2404.04633；Hagström 2412.17031 的批评 | 无方法空位；只剩把它用在该对象上 |

---

## 6. 查询日志

WebSearch（33 条）：
1. activation steering early layers model outputs end-of-sequence token immediately empty response
2. layer skipping early layers LLM generates EOS empty output context ignored
3. removing attention sink at inference causes model to ignore context perplexity explosion first token ablation outputs
4. noise injection residual stream early layer LLM output collapse to default token prior "context" ablation
5. massive activation ablation model generates repetitive or empty text first token outlier zeroing generation examples → House of Cards 2410.01866
6. attention sink hybrid linear attention Gated DeltaNet Mamba sink first full attention layer ablation
7. LLM premature EOS token generation empty answer cause mechanism interpretability → AID "silence"
8. BOS token perturbation intervention first token representation model ignores prompt output
9. context sensitivity metric counterfactual context log-probability difference answer knowledge conflict parametric vs contextual measure
10. "context usage" OR "context reliance" metric paired prompts differing in one fact logit difference interpretability intervention → Hagström 2412.17031
11. Du et al. "context versus prior knowledge" persuasion score susceptibility score
12. pointwise V-usable information context usage measure input attribution counterfactual
13. instruction-tuned model empty prompt or content-free input generates EOS immediately default behavior prior
14. "silence" LLM terminates generation EOS without response Adaptive Injection Decoding
15. EOS token probability neuron mechanism "end of sequence" prediction circuit language model length
16. intervention early layers destroys in-context information retrieval but parametric knowledge preserved layer-wise
17. Qwen3.5 OR Qwen3-Next interpretability activation steering hybrid GatedDeltaNet layers intervention
18. steering vector too strong causes model to stop generating EOS short outputs degenerate empty → LessWrong instruct vectors；2606.18389
19. arXiv 2508.19614 noise injection layers shallow local context intermediate factual knowledge decoding
20. punctuation attention sink delimiter tokens massive activation intervention effect context retrieval
21. attention sink in Mamba state space linear attention models analog first token recurrent state → 2606.00930 state sink
22. 注意力汇聚 attention sink 大激活 干预 模型 不再 使用 上下文 早层
23. entropy neuron or "null space" neuron ablation increases end-of-text probability early layer LLM
24. "attention sink" removal or suppression downstream generation outputs gibberish/repetition/empty → Cancedda 2402.09221
25. hybrid linear attention model layer importance ablation first softmax attention layer Qwen3-Next Jamba → 2603.22473
26. "Catch, Tag, Release" attention sinks punctuation tokens 2502.00919
27. perturbing hidden states of prompt tokens model behaves as if prompt is empty unconditional generation chat model ends turn
28. "massive activations" Mamba OR linear attention OR hybrid models emergence Jamba Zamba sink
29. "context neglect" OR "ignores the context" activation intervention layer analysis
30. GatedDeltaNet attention sink gated delta rule first token state Qwen3.5
31. activation patching early layer residual stream noise corrupt prompt model outputs end-of-turn token im_end
32. Qwen3.5-4B OR Qwen3.5-2B massive activation attention sink layer analysis first token norm
33. early layer perturbation in-context information unavailable model abstains or stops instead of hallucinating

WebFetch（2 次，均为摘要器转述，不计入"读过"）：arxiv.org/html/2410.01866v2（确认"repeats the user prompt"后已在 PDF 文本中 grep 到原句）；LessWrong instruct-vectors 帖。

按步分配：第 1 步 Q1–Q8、Q13–Q14、Q18、Q24、Q27、Q33；第 2 步 Q9–Q12、Q29；第 3 步 Q16、Q19、Q21、Q25、Q28、Q32 + 直接按 ID 下载 9 篇；第 4 步 Q15、Q17、Q20、Q22、Q23、Q26、Q30、Q31。

## 7. 阅读量

- 下载 PDF 22 篇（/home/ubuntu/.claude/jobs/e856631c/tmp/audit/pdf/）。
- **取到正文并定向检查的 15 篇**：2608.12149、2402.17762、2410.10781（只查移除实验，未见输出形态）、2610.16745、2502.01563、2411.07191、2504.02732、2410.01866、2603.06591、2412.17031、2402.11655、2404.04633、2402.09221、2603.22473、2606.18389。
- 只浅 grep、不计入：2605.08504、2510.06477、2603.05498；取到未读：2411.07404（只读摘要）、2503.08908、2502.00919。
- 每条主张在本轮只经过一轮检索（S1–S3 另有前轮 C1/C5 一轮的部分重叠）。存活不等于强度。

## 8. 边界（第 7 步不在本笔记，这里只记本轮的已知盲区）

- 2608.12149 图 1(b)、2410.01866 图 1(b) 等生成样例是图片，未读到原文样例；"repeats the user prompt"来自正文。
- AID 2503.10167、LessWrong 帖、2603.05498 关键句只经摘要器转述。
- 未系统检索 OpenReview 在审稿件、ACL Anthology、非英文（只 1 条中文）。
- 未做引用链（第 5 步），2608.12149 与 2502.01563 的被引是最该扫的。
