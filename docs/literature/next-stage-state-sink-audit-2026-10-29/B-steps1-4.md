# B 线查重：七步协议第 1–4 步

日期：2026-10-29。范围：只做第 1–4 步（抽象阶梯、方法论单独搜、蕴含检索、同义术语）。第 5（引用链）、6（对抗轮单独跑）、7（边界申报）不在本轮；第 7 节只列本轮自身的盲区。纯覆盖笔记，不含 novelty 段，不给等级。

证据规则：判生死的引用一律取 arXiv PDF，`pdftotext` 后 `grep` 定向核对，原文句子照抄并附行号或章节。搜索引擎摘要器的转述不作证据。本轮抓到一处摘要器转述与原文不符：检索把 2606.19831 的结论转述为"removing the drive returns the behavior toward baseline"，原文 §7.3 实际是"算子翻转在撤除后回落，语言翻转在撤除后保持（0.83 到 1.0）"，后者被归因到已生成文本。

与前一轮（prior-audit-2026-10-28.md）的关系：不重做 C1–C5。前一轮里与 B 线相关的只有两条，本轮引用不重读：
- Kumar 等 2605.30574（上层提示 KV 换成同模板中性填充几乎不掉分）——只取了摘要，是"提示 KV 携带什么"的旁证。
- Liu 2606.19831——前一轮只查了"有没有 L0–L7 神经元"，没读 §7.3。本轮发现 §7.3 正是 B1 的三臂设计，见下。

---

## 0. 坏消息先说

1. **B1 的"撤针 / 无针强制前缀重建"分离方法已有两篇先例，方法层被覆盖。**
   - Dobre 等 2610.09027（2026-10-06，ServiceNow/Mila）：对抗输入被 mask 掉后影响经后续 token 的 KV 持续；"cache-swap"消融在**文本固定**的条件下只换缓存来源，证明"对抗文本本身不足以"引发效应，效应走 KV。这就是我们 rebuild 臂的逻辑（同一文本、干净缓存）。
   - Liu 2606.19831 §7.3：单神经元转向的"release"臂（撤针）+"forced-opening control"（无注入、强制同样开头续写）——正是 withdraw + rebuild。结论与我们 L25 一致（持续靠已生成文本，"in-context momentum"），与我们 L2 相反。
2. **B2 的分离方法（状态交换）在同一个模型上已被做过。** Afendulev 等 2609.04434 在 **Qwen3.5-4B** 上做 split-prefill（只留 KV 或只留递推状态）与 state-swap（KV 来自上下文 A、递推状态来自上下文 B）。我们计划的"只换递推状态 / 只换 KV"是它的方法直接搬用。它还给出一条**类比档**预言：语言、人设、语气这类"回应方式"走递推状态（KV-only 语言准确率 0.01），精确检索走 KV。
3. **B3 的痛点"转向效应经缓存累积"已被命名并配了修复方案。** Kang 等 2605.10664 把"KV-cache contamination"列为残差流转向在多轮对话中的主要失败模式，并提出 GCAD。但它没有撤针臂、没有重建臂，"经 KV"只写成"A likely mechanism"，即机制断言未经分离检验。2607.09156 引用它并在设计上用每轮全量重编码回避，自称"We have not measured what cache reuse contributes"。
4. **B1 的 KV 一半大体是被蕴含的（推导档）。** KV 条目一经写入不再更新；只要后续位置还注意到被干预位置，撤针后效应必然有一部分残留。prompt-only 转向（PrOSV 2605.05983 写明"functions mainly by implicitly editing the KV cache"）与 KV cache steering（2507.08799）之所以有效，正依赖这一点。真正不被蕴含的是：(a) 残留**大到**能维持异常，(b) 残留的承载者是递推状态还是 KV，(c) 早层 vs 晚层承载者从状态换到文本。
5. **方法危险，直接影响我们已有数据的判读：**
   - 2609.04434 附录 A："Most public implementations of hybrid layers only consume a restored recurrent state on the single-token decode path"——多 token 块喂入时恢复的递推状态被**静默忽略**、扫描从零重启，"No error is raised"。它要求每个模型用 ∆=‖logits(q|R(c))−logits(q|0)‖∞ 验证状态真的进了模型（他们在一个模型上测到 ∆=0.0000）。我们 withdraw / rebuild / 计划中的状态交换都受这条影响，必须核对代码路径。
   - 2604.15409：FP16 下 cache-ON 与 cache-OFF（重算）在 greedy 下也逐 token 分叉，"100% token divergence rate"（LLaMA-2、Mistral、Gemma-2，GSM8K）。我们的 rebuild 臂相对 withdraw 臂多了一个"重算 vs 缓存"的数值差。需要一个**无针**的 continue-vs-rebuild 对照来标定这个零分布（CLAUDE.md 6.3）。这条是**类比**：对象是 FP16 Transformer，Qwen3.5 的 bf16 + 分块/逐 token 递推是否同等分叉没查到。

---

## 1. 第 1 步：抽象阶梯

模板："对状态 S 施加变换 T 一段时间后移除 T，T 的效应经 S 延续或衰减；用'移除 T、保留 S'与'移除 T、从同一文本重建 S'分离 S 与文本。"

整类 T 的检索：

| # | 查询词 | 条数 | 命中（取正文与否见第 5 节） |
|---|---|---:|---|
| Q1 | KV cache steering one-shot intervention reasoning small language models | 9 | 2507.08799 KV cache steering（一次性改提示 KV，"implicitly influences future tokens"） |
| Q2 | steering Mamba state space model activation steering recurrent state | 9 | 2404.05971 Paulo 等 state steering；2602.22719 SSM 子空间瓶颈 |
| Q3 | activation steering effect persists after removing steering vector KV cache generation | 10 | 2605.10664 KV-cache contamination；2606.29522 Shih（层间撤除，轴不同） |
| Q4 | steering only prompt tokens vs generated tokens effect carried through KV cache | 9 | 2507.08799；2605.06225 Memory Inception（未取） |
| Q5 | steering hybrid linear attention model Gated DeltaNet recurrent state intervention | 10 | **2605.12770 WriteSAE**（GDN 缓存写入级转向，自称首个） |
| Q7 | Mamba hidden state poisoning attack persistent state injection | 9 | **2601.01972 HiSPA**（输入覆写 SSM 状态） |
| Q9 | steering vector applied during prompt only then turned off generation continues steered behavior | 9 | 2605.05983 PrOSV |
| Q10 | temporary steering side effects linger conversation turns steering vector removed multi-turn | 10 | 2605.10664；2604.08169（多轮转向评测缺口，未取） |
| Q19 | steering vector applied for first k tokens then removed effect on rest of generation decay | 9 | 2510.01246 衰减式 SAE 转向；2605.01844 注入位置四策略 |
| Q29 | "steer" then "release" OR "transient steering" OR "steering window"… | 9 | **2606.19831 §7.3 release + forced-opening**；2607.05615 前导窗口转向 |
| Q38 | injected text removed from context but influence remains KV cache "residual influence"… | 9 | **2610.09027 Visual Memory Attacks（cache-swap）**；2606.17034 KVEraser |
| Q17 | stale KV cache after editing context old content leaks into generation recompute vs reuse | 9 | 2606.17107（改字段 KV、复用下游 → 模型仍按旧值）；2609.17983（陈旧 KV 修复） |

阶梯结论：
- T = 优化过的输入（图像/软提示）被移除 → 2610.09027：结论与方法都在，对象是 Transformer、优化攻击。
- T = 文档字段被改写 → 2606.17107、2609.17983、2606.17034：下游缓存保留旧影响，全量重算恢复。即"S 承载、重建恢复"在 KV 上是**已知工程事实**。
- T = 激活转向、生成中撤除 → 2606.19831（结论：文本承载）；2607.05615、2510.01246（只看行为，不分离）；2605.10664（持续注入，断言 KV 但未分离）。
- T = 写入递推状态 → 2404.05971（一次写入最后一个提示 token 的状态即可转向整段生成）、2605.12770（写入三个缓存位）；HiSPA 2601.01972（输入覆写状态）。
- **未找到**：T = 残差流单通道加性干预，在混合模型里撤除后分离状态与文本，并定位到递推状态或 KV。

## 2. 第 2 步：方法论单独搜

把"撤针 / 无针重建 / 状态交换"当作脱离领域的方法来搜。

| # | 查询词 | 条数 | 命中 |
|---|---|---:|---|
| Q8 | activation patching KV cache versus recompute counterfactual cache swap interpretability | 10 | 2607.03502（填充位 KV 移植当 patching）；2604.15409（FP16 cache vs 重算不等价）；2609.17983（移植 vs 重算结论不同） |
| Q13 | "state swap" OR "state transplant" recurrent state hybrid language model Qwen3.5 interpretability | 9 | **2609.04434 split-prefill / state-swap**；2609.25053 LatentPort（Qwen3.5 4B→9B 递推状态移交）；2604.01168 S0 tuning |
| Q16 | self-sustaining steering generated text vs internal state disentangle regenerate from text without intervention | 9 | 2604.09839（转向后的状态是否可由某段提示到达）——不是分离方法 |
| Q23 | "re-prefill" OR "re-encode" generated text without intervention to separate cache effect from text effect steering | 9 | HF 论坛帖"KV Graft Steering"（非正式：同 token 下全量重算 vs 缓存解码 vs 分拆 KV 预填）；2411.13009 LLMSteer |
| Q31 | split-prefill state-swap hybrid recurrent KV Afendulev follow-up steering | 9 | 未找到 2609.04434 的后续转向工作；2609.23601 PREM（只在预填阶段调制，靠 KV 持续） |
| Q35 | counterfactual history intervention "cached" versus "recomputed" attribution generated tokens versus internal state causal mediation autoregressive | 9 | 无直接命中 |
| Q36 | SGLang vLLM hybrid model prefix caching mamba state checkpoint reuse radix cache recurrent state | 9 | 服务侧：SGLang MambaRadixCache、vLLM mamba 前缀检查点（B3 背景） |

方法层结论：
- **"文本固定、只换缓存来源"**：2610.09027 §4.7 的 cache-swap（Transformer KV，按 anchor/benign 块拼接）。
- **"撤针 + 无针强制同开头"**：2606.19831 §7.3 的 release + forced-opening control + counter-drive。
- **"只留一种缓存 / 交叉拼两种缓存"**：2609.04434 的 split-prefill 与 state-swap，就在 Qwen3.5-4B 上。
- 三者合起来覆盖了我们三臂设计 + 计划中的状态交换的每一个组件。没有找到把三者组合起来，用于**激活干预撤除后**的工作。

## 3. 第 3 步：蕴含检索

| # | 查询词 | 条数 | 命中 |
|---|---|---:|---|
| Q11 | linear attention forgetting gate memory decay theory how long state retains information DeltaNet erase | 10 | 2605.22791 Gated DeltaNet-2（擦除/写入解耦）；无保持时长定理 |
| Q24 | gated linear attention state memory half-life forget gate distribution interpretability effective memory length Gated DeltaNet heads | 9 | 无 GDN 逐头半衰期的发表结果；Research Square rs-11201314（"forget gate keeps recurrent state in narrow marginally stable window"——**正文取不到**，只有标题） |
| Q32 | delta rule state perturbation propagation linear RNN error accumulation contraction stability… | 9 | 2412.06464 Gated DeltaNet；转移矩阵 α_t(I−β_t k_t k_tᵀ) 的标准性质 |
| Q12 | interpretability hybrid model Mamba attention which carries information recurrent state vs KV cache ablation | 9 | 2609.04434；2603.22473（Qwen3.5-0.8B 组件消融）；2510.26912 |
| Q26 | probing Gated DeltaNet recurrent state interpretability linear attention state what information stored | 9 | 2605.12770；无专门探针论文 |
| Q22 | activation patching Mamba state space model causal analysis hidden state factual recall Sharma | 9 | 2404.03646 ROME-in-Mamba（摘要级） |

蕴含判读（每条标档）：
- **KV 侧——推导。** 注意力层的 K、V 一经写入不再修改。撤针后，被干预位置的 K/V 以及由被干预残差算出的后续位置 K/V 都保持原样，只要查询仍注意到它们，扰动就继续进入读出。所以"撤针后仍有残留"对 KV 是平凡的；不平凡的是残留量是否足以维持异常。prompt-only 转向的有效性（2605.05983："PrOSV intervenes only at prefill stage and not decode stage… functions mainly by implicitly editing the KV cache"）是这条的经验确认。
- **递推侧——推导 + 实证一处。** GDN 的状态扰动按 δS_t = α_t(I−β_t k_t k_tᵀ)δS_{t−1} 传播，范数被门控收缩，但 α_t 接近 1 的头几乎不衰减。WriteSAE 2605.12770 附录给出 Qwen3.5 GDN 一次写入扰动的传播式："A scalar gate cannot mix the rank-1 outer with anything else, so the perturbation stays rank-1; only its norm decays."，衰减因子 G_{t0→t0+h} = Π exp(g_s)（行 1366、1394），并注明"The reduction is empirical"（忽略了 delta 擦除项的交叉项）。所以"递推态会不会在 4 或 16 个 token 后仍携带干预"**不被蕴含为是或否**，取决于该层各头 g_s 的实测值——这是一个可零 GPU 读出的量，不是文献已给的结论。
- **HiSPA 2601.01972 的反方向蕴含——类比。** 它证明了足够强的输入能"irreversibly overwrite"SSM 状态，并写道"hybrid models combining Mamba with attention layers may partially mitigate this vulnerability, since attention can recover information that the SSM layers have overwritten"（§3 末）。这预测：在混合模型里，被递推态"擦掉"的东西可由 KV 补回。对 B2 的方向是"KV 能救回、递推态会被冲掉"，与 2609.04434 的"回应方式走递推态"是两股相反的类比压力。
- **2609.04434 对 B2 的蕴含——类比。** 它的结论（§6）："The recurrent state works as a compressed prior that shapes language, persona, and semantic field of generation"；表 1：Qwen3.5-4B 语言跟随 REC-only 0.70、KV-only 0.01。如果 L2 的异常属于"回应方式"一类（而不是某个被检索的具体项），这条类比预言 B2 的答案是递推状态。但它的对象是上下文信息，不是激活干预；跨对象成立未验证。
- **2606.19831 §7.3 对 B1 L25 结果——近似蕴含。** 原文："a counter-drive and a forced-opening control (continuation in the routed language on 11/12 prompts with no injection, against 0/12 from a baseline opening) attribute that persistence to the generated context, not a held neuron state"。对象是 Qwen3-4B L25/F347（稠密 Qwen3，非 3.5）。我们 L25 "rebuild 也救不回（文字自持）"与之同形，应作为该结果的复现而不是新发现。
- **2610.09027 的反向信息——推导/直接引文。** "We show that persistence is not a default property of adversarial inputs, but it can be optimized for."（贡献列表第一条）。即在 Transformer 上，未经优化的输入一般不经 KV 持续。我们 L2 单通道 +1 未经优化却经状态持续，这条形成对照，但它的 T 是输入扰动而非残差加性干预，不能直接互推。

## 4. 第 4 步：同义术语枚举

先列词表，再逐一搜（部分词与前几步的查询合并）：

英文：persistent steering, residual effect, aftereffect, lingering, spillover, hysteresis, carryover, state contamination, cache contamination, KV-cache contamination, cache poisoning, KV cache steering, one-shot steering, prompt-only steering, steering decay, transient steering, steering window, release, recurrent state steering, state steering, SSM steering, Mamba steering, hybrid model interpretability, GatedDeltaNet, DeltaNet state, linear attention state probing, split-prefill, state-swap, cache-swap, state transplant, state handoff, stale KV cache, context erasing.
中文：激活转向、撤除、残留、持续、KV 缓存、递推状态、混合模型。

| # | 查询词 | 条数 | 命中 |
|---|---|---:|---|
| Q6 | prefix caching state reuse SSM hybrid model contamination security cross-request | 9 | Marconi 2411.19379（只讲效率）；无跨请求污染的安全工作 |
| Q14 | steering hysteresis language model steering carryover after intervention stops autoregressive | 10 | 无直接命中（ESR 2602.06941 讲转向中自愈，非撤除后） |
| Q15 | KV cache poisoning attack shared prefix cache manipulated cache entries influence other users LLM serving | 9 | 2409.20002 时序侧信道；位翻转共享 KV 块（"no temporal decay occurs"，硬件故障假设） |
| Q18 | activation steering Falcon-H1 OR Jamba OR "Qwen3.5" hybrid model steering vectors evaluation | 9 | 2509.22067 Rogue Scalpel 含 Falcon-H1（随机向量破拒答）；无混合模型专属转向评测 |
| Q20 | CLASP defending hybrid large language models hidden state poisoning | 10 | 2603.12206 CLASP（HiSPA 防御，token 级分类） |
| Q21 | "steering" "recurrent state" persistence SSM intervention removed state retains perturbation | 9 | 2605.02236（递归 LLM 循环里"可见 vs 写入状态"的析因设计，对象是文本循环） |
| Q25 | steering vectors vLLM prefix caching interaction steered KV cache reused across requests serving | 9 | 无；摘要器推断"token 哈希不含转向配置"——**推测**，未在 vLLM 源码或 issue 核实 |
| Q27 | "state contamination" OR "cache contamination" language model intervention residual effect generation | 9 | 2605.10664；2605.16746（记忆增强 agent 的转录污染，文本层） |
| Q28 | 激活转向 撤除 后 效应 持续 KV缓存 递推状态 混合模型 | 9 | 无中文直接命中 |
| Q30 | Mamba SSM jailbreak activation steering safety refusal direction state space models | 9 | 无 SSM 专属转向安全工作 |
| Q33 | activation steering aftereffect lingering spillover subsequent turn without steering KV cache steered history | 10 | 2605.10664；2607.09156（承认该机制、以重编码回避） |
| Q34 | Qwen3.5 activation steering neuron intervention Gated DeltaNet layers steering effect | 9 | 仅博客与 HF SAE 发布；无论文分 GDN 层与全注意力层 |
| Q37 | persistent steering residual effect hybrid SSM transformer model interpretability Jamba Zamba recurrent state carries instruction | 9 | 无直接命中 |

---

## 5. 逐篇覆盖表

"全文定向"= 取到 PDF 正文，针对本线问题 grep 并读了相关段落；"摘要"= 只读了 PDF 的摘要页。

| ID | 标题 | 模型 | 干预类型 | 撤除干预？ | 区分状态与文本？ | 涉及递推状态？ | 覆盖主张 | 覆盖层级 | 读取程度 |
|---|---|---|---|---|---|---|---|---|---|
| 2609.04434 | What Attention Recalls and Recurrence Controls in Hybrid LMs | **Qwen3.5-4B**、9B；Falcon-H1-3B/7B | 缓存级：只留 KV / 只留递推态；交叉拼接 | 不适用（无注入） | 否（文本 q 固定，分的是 KV vs 递推） | 是 | B2 | **方法层覆盖（同一模型）**；B2 结论被类比预言 | 全文定向（摘要、§1、§3、§5.3–6、Limitations、附录 A） |
| 2610.09027 | Visual Memory Attacks Can Persist Through The KV-Cache | Qwen3-8B、Qwen3-VL-8B、Gemma-4-12B | 优化的对抗图像/软提示，之后 mask | 是（mask） | **是**（文本固定 cache-swap） | 否 | B1、B3 | **方法层覆盖**；B1 结论在相邻 T 上被占（KV 携带） | 全文定向（摘要、贡献、§4.7） |
| 2606.19831 | Leverage Is Not Reach（Liu） | Qwen3-4B、Llama-3.1-8B、Qwen2.5-3B 等 | 单神经元加性驱动 | **是**（release） | **是**（forced-opening 无注入续写 + counter-drive） | 否 | B1 | **方法层覆盖**；结论相反（文本承载）；与我们 L25 同形 | 全文定向（§7.3、§7.4 末段、§8 段落） |
| 2605.10664 | Prompt–Activation Duality（GCAD） | Qwen2.5-7B-Instruct 等 | 残差流 persona 向量，全程注入 | 否 | 否（"A likely mechanism is KV-cache contamination"） | 否 | B3、B1 | **痛点部分覆盖**（命名 + 修复）；B1 机制被断言未检验 | 全文定向（摘要、§1、§3.2、实验协议行 574） |
| 2605.12770 | WriteSAE | Qwen3.5-0.8B/4B/27B、Mamba-2、RWKV-7 | 替换/放大 GDN 缓存写入 | 一次性写入 | 否 | 是 | B2、第 3 步 | 部分覆盖（递推态写入级转向；扰动衰减式） | 全文定向（摘要、§1、附录行 1355–1395） |
| 2404.05971 | Does Transformer Interpretability Transfer to RNNs? | Mamba-2.8b、RWKV-v5-7b | CAA 残差 + 状态转向 | 一次性状态写入 | 否 | 是 | B1（SSM 一侧）、B2 | 部分覆盖；推测句"activation steering already influences the model state" | 全文定向（§3.3） |
| 2601.01972 | Hidden State Poisoning Attacks against Mamba-based LMs | Mamba、Mamba-2、Jamba-1.7-Mini、Nemotron-3-Nano | 输入触发词覆写状态 | 不适用 | 否 | 是 | B3、第 3 步 | 部分覆盖（SSM 状态安全性；混合模型 KV 可补救的假说） | 全文定向（摘要、§1、§3 末段） |
| 2507.08799 | KV Cache Steering | 小模型、扩展到大模型 | 一次性改提示 KV | 一次性 | 否 | 否 | B1 第 3 步 | 被蕴含（KV 写入持续影响后续） | 全文定向（摘要、§1、§3） |
| 2605.05983 | PrOSV（prompt-only steering） | 多个 Transformer | 只在提示 token 注入 | 预填后即停 | 否 | 否 | B1 第 3 步 | 被蕴含（"functions mainly by implicitly editing the KV cache"） | 全文定向（§3 干预位置段、附录与 KV cache steering 比较） |
| 2606.17107 | Models Take Notes at Prefill | 四个 Transformer 族，扩展到 Falcon-H1 | 改字段 KV、复用下游 | 是（字段改写） | 是（下游笔记 vs 字段本身） | 部分（混合模型只部分适用） | B1 模板 | 方法与结论在 T=文本编辑上被占 | 全文定向（摘要、适用范围行 1679–1687） |
| 2607.09156 | Activation Steering Transfer to Agents | — | 转向 + agent 循环 | 否 | 否 | 否 | B3 | 旁证：承认 KV 污染机制，未测 | 全文定向（grep cache 段，行 624–626、1571–1580） |
| 2606.29522 | Shih：When Does Activation Steering Change What a Model Computes From? | 7B | 功能向量 | 在**更深层**减掉（层轴） | 否 | 否 | 无（轴不同） | 未覆盖；注意不要把层间撤除与时间撤除互推（5.4） | 全文定向（行 574–615） |
| 2604.15409 | FP16 Divergence in KV-Cached Inference | LLaMA-2-7B、Mistral-7B、Gemma-2-2B | 无（cache-ON vs OFF） | — | — | 否 | 方法危险 | 不覆盖；提示 rebuild 臂需零分布对照 | 摘要 |
| 2609.25053 | LatentPort | Qwen3.5 4B→9B | 递推态跨模型移交 | — | — | 是 | B2 方法旁证 | 方法旁证（递推态直接复用比学习映射好） | 摘要 |
| 2609.17983 | Budgeted Repair of Stale KV Caches | 三族 Transformer | 文档编辑后部分重算 | 是 | 是（移植 vs 重算） | 否 | B1 模板 | 方法旁证（"refreshing only the edited span can leave downstream dependencies stale"） | 摘要 |
| 2606.17034 | KVEraser | Transformer | 擦除 span | 是 | 是 | 否 | B1 模板 | 背景（"its influence propagates into the cached states of all subsequent tokens"） | 摘要 |
| 2607.05615 | Bernoulli Sparse Steering | 两族 | 只在前导窗口转向 | 是（窗口后停） | 否 | 否 | B1 | 部分覆盖（行为层"窗口后仍有效"） | 摘要 + grep |
| 2510.01246 | SAE vs activation difference steering（衰减转向） | — | 随时间衰减的系数 | 渐停 | 否 | 否 | B1 | 边缘 | grep |
| 2605.01844 | Cylindrical Representation Hypothesis | Gemma-2B、Llama2-7B | 四种注入位置 | — | 否 | 否 | B1 | 边缘 | grep |
| 2605.02236 | Perturbation Dose Responses in Recursive LLM Loops | — | 注入文本 | — | 可见性 vs 写入状态（文本层） | 否 | B1 方法类比 | 边缘 | 摘要 |
| 2602.22719 | Steering SSMs via Activation Subspace Bottlenecks | 5 个 SSM | 子空间缩放 | 否 | 否 | 是 | B2 背景 | 未覆盖 | grep |
| 2603.12206 | CLASP | Mamba 混合 | HiSPA 检测 | — | — | 是 | B3 背景 | 背景 | 检索片段 |
| rs-11201314 | Where the Answer Is Born（Research Square） | 量化混合 GDN 0.8B/27B | patching、遗忘门钳制 | ? | ? | 是 | 第 3 步 | **取不到正文**，不计 | 仅标题 |

## 6. 逐条覆盖判定

| 主张 | 判定 | 层 | 依据 |
|---|---|---|---|
| B1 现象：撤针后效应经缓存内部状态持续 | 部分覆盖 | KV 部分**被蕴含**（推导）；"持续足以维持异常"在 T=优化输入上**结论被占**（2610.09027）；T=单神经元驱动上前人得到的是**相反结论**（2606.19831，文本承载） | 第 3 步 |
| B1 方法：撤针 vs 无针重建分离状态与文本 | **方法层覆盖** | 2610.09027 cache-swap（文本固定）；2606.19831 release + forced-opening | 第 2 步 |
| B1 对象：残差单通道加性干预、早层、混合模型、状态承载 vs 晚层文本承载的深度切换 | 未找到 | — | 第 1、4 步全部查询 |
| B2 方法：只换递推态 / 只换 KV | **方法层覆盖，且是同一模型 Qwen3.5-4B** | 2609.04434 split-prefill + state-swap | |
| B2 结论：干预残留由递推态还是 KV 携带 | 未找到；**有两股相反的类比** | 2609.04434（回应方式走递推态）vs HiSPA（KV 可补回被递推态冲掉的信息）；WriteSAE 的衰减式表明答案取决于 g_s 实测值 | |
| B3 痛点 a：转向效应经缓存延续/累积 | **部分覆盖**（命名 + 修复，机制未分离检验） | 2605.10664；2607.09156 承认未测 | |
| B3 痛点 b：带状态前缀缓存把干预带到后续请求 | 未找到 | 服务系统已有混合模型前缀缓存（SGLang、vLLM、Marconi），但"缓存键不含转向配置"只是**推测** | |
| B3 痛点 c：混合/SSM 模型上转向的安全性 | 部分覆盖（相邻） | HiSPA/CLASP 讲输入对 SSM 状态的攻击；2509.22067 含 Falcon-H1 讲转向破拒答；无"递推态携带转向残留"的安全工作 | |

### 仍空着的部分在哪一层

- **方法层几乎全被占**：撤针、无针重建、文本固定换缓存、只换递推态/只换 KV，各组件都有直接先例，其中状态交换就在 Qwen3.5-4B 上。
- **空着的在对象层**：
  1. 激活干预（不是输入、不是缓存编辑）撤除后，在混合模型里由哪种缓存携带。
  2. 承载者随注入深度切换（L2 状态承载、L25 文本承载）。前人只有单一深度的单一结论（Liu：文本；Dobre：KV）。
  3. 未经优化的干预就能经状态持续，对照 2610.09027 的"persistence is not a default property… but it can be optimized for"。
- 痛点层：KV 污染已被命名；"递推态污染"与"跨请求带状态缓存复用"未找到，后者的现实性是推测档，没有找到任何人报告这个痛。

## 7. 本轮盲区（不是完整的第 7 步）

- 没做第 5 步引用链：2609.04434、2610.09027、2606.19831 §7.3、2605.10664 的被引与参考文献都没扫。2610.09027 引的 Kontonis 等 2026（compaction 保留摘要 KV）、Schlarmann & Hein 2026（VMI）没取。
- 没做第 6 步独立的对抗轮；本轮虽带着证伪意图搜，但不能替代单独一轮。
- Research Square rs-11201314（遗忘门钳制、混合 GDN）正文取不到；2605.06225 Memory Inception、2604.08169、2604.09839、2607.03502 未取。
- HF 论坛"KV Graft Steering"只见检索片段，非正式。
- 2606.19831 §7.3 没写清 release 臂是否保留被驱动的 KV（按常规 hook 实现推断是保留，属**推测**）；它的 forced-opening 是否逐 token 重建也没写。判它"方法层覆盖"时这一点未核实。
- 非 arXiv（OpenReview、ACL Anthology）与非英文只经检索引擎间接覆盖；中文一条查询无命中。
- 并行未公开工作：2609.04434（9 月）、2610.09027（10 月）都是近两个月的；这个交叉区域正在变热，再出一篇直接做"转向 + 状态交换"的概率不低。

## 8. 计数

- WebSearch 查询：38 条（Q1–Q38）；WebFetch 1 次（Research Square，失败）。
- 取到 PDF：22 篇；其中**全文定向** 12 篇（2609.04434、2610.09027、2606.19831、2605.10664、2605.12770、2404.05971、2601.01972、2507.08799、2605.05983、2606.17107、2607.09156、2606.29522）；只读摘要或 grep 片段 9 篇（2604.15409、2609.25053、2609.17983、2606.17034、2607.05615、2510.01246、2605.01844、2605.02236、2602.22719）；下载未读 1 篇（2603.22473）。2605.06225 未取。
- 按 CLAUDE.md 语料自查，"读过"只算上面的 12 篇。
- B1、B2、B3 按现行表述只经过本轮一轮（38 条查询）。

PDF 与抽取文本：/home/ubuntu/.claude/jobs/e856631c/tmp/audit/pdf/
