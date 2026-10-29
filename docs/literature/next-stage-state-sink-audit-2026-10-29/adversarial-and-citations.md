# B 线 / S 线：第 6 步对抗式检索 + 第 5 步引用链挖掘

日期 2026-10-29。纯覆盖笔记，不含 novelty 段、不给等级。"读过"只算取到 PDF、pdftotext 后 grep 定向核对过的；搜索摘要器转述一律不算证据（本轮又抓到一次：搜索摘要称 2603.16335 "propagated through the recurrent state" 是结论，原文其实只是作者推断，未做 KV 与递推状态的分离，见 B-K3）。

PDF 与文本：`/home/ubuntu/.claude/jobs/e856631c/tmp/audit/pdf/`；引用链 JSON：`/home/ubuntu/.claude/jobs/e856631c/tmp/audit/cc/`。

前一轮（prior-audit-2026-10-28）已覆盖、本轮不重读：Ben-Artzy 2409.03621、Lad 2406.19384、2602.02712 命题 4.1、2510.06477、2608.12149、2610.16745、Shih 2606.29522、SKOP 2605.06342、Sun 2402.17762、2605.08504、2511.17194、2605.30574、SPEED 2605.06105。前一轮**漏了**、与 B/S 直接相关的：2603.16335（前一轮只当 C4 的单模型零结果引用，没注意到它的混合架构递推状态主张）、2610.04967、2609.11020、2604.01168、2605.12770、2410.01866、2311.08817。

---

## 1. B 线杀手（按杀伤从强到弱）

主张拆成：B1 转向撤掉后效应还在；B2 延续的载体是缓存的内部状态，不是已生成的文本；B3 在混合架构里分清 GDN 递推状态和全注意力 KV 谁在携带；B4 痛点（关不掉、带状态缓存复用、混合/SSM 转向安全）。

| # | ID / 标题 | 杀哪条 | 层级 | 原文证据（节） |
|---|---|---|---|---|
| B-K1 | 2610.04967 Zhu & Zhu, *One Token Can Be Enough: Prefix Steering*（2026-10-04） | B1；也把 B2 列为开放问题 | **B1 结论被占**；B2 未被占，但已被点名为待解问题 | 摘要："applies existing steering directions … over a short span starting at the final prompt token, with no further direct intervention afterward"；"a brief initial intervention can influence behavior expressed well after steering ends"。§结论："One possibility is that steering alters a persistent latent or belief-like state …; another is that its effect is propagated through the generated tokens themselves … our behavioral experiments do not distinguish between these mechanisms."（第 11 页）。模型是 Qwen3 1.7B/14B 和 OLMo 3 7B/32B，都是纯 Transformer |
| B-K2 | 2609.11020 Sun 等, *K/V-Cache Interventions Dissociate Representation Alignment from Persona Expression* | B2 的设计（"无干预重建"一臂） | **方法层部分覆盖** | §4.4 "Same-token-sequence control: the shift is not solely token history … source and target caches decode the identical realized token sequence, differing only in persona conditioning"；§讨论："K/V interventions persist across steps by architectural design; because a transplanted trajectory carries the target's own generated token history, however, they are not cleanly separable from the token channel (though a same-token-sequence control … shows the representational shift persists when token history is held fixed, so the entanglement is partial rather than total)"。还发现单层激活注入有 "reset dynamics"（R≈1，每步被拉回，不累积），只测了 L24/L28："whether R ≈ 1 holds at early or mid hook layers is an open question"。Llama-3.1-8B 单模型，读数是表示层 V⋆ 投影加文本标记密度，不是"撤除后行为" |
| B-K3 | 2603.16335 Yap, *Behavioral Steering in a 35B MoE … (Qwen3.5-35B-A3B)* | B3（混合架构里的载体） | **结论层被"断言"占住，但没有证据**：作者未分离 GDN 状态和 KV | §5.3 表 5：decode_only α=1/2 时 d(ask) 是 −0.16/−0.20（p=0.67/0.36），prefill_only α=2 时是 −0.64（p=0.0007）。由此写道："causal evidence that the model computes its behavioral commitments … during the prefill phase and propagates them through the GatedDeltaNet recurrent state"。prefill 期写入的全注意力 KV 同样会被读到，文中没有排除这一点，所以"经 GDN 状态"只是推断。贡献列表第 4 条和 §相关工作重复了这句 |
| B-K4 | 2604.01168 Young, *S0 Tuning*（Qwen3.5-4B，FalconH1-7B） | B2/B3 的反面竞争解释：GDN 状态的直接影响在提示内就衰减掉了 | **部分覆盖（反向证据）** | §1/§机制："S0's direct influence on output logits decays to 0.03% KL ratio by the end of the prompt, yet 23 of 27 FAIL-to-PASS flips diverge from the baseline at the very first generated character (85%) … amplified by the recurrence into a qualitatively different generation trajectory"。意思是写进递推状态的扰动没有靠状态本身留存，而是改了下游轨迹。这对"递推状态是载体"不利，而且它也没分 KV。另有一点：在纯 Transformer 上做前缀微调 −13.9 pp |
| B-K5 | 2605.12770 Young, *WriteSAE* | B3 的方法（往 GDN 缓存写入后看续写） | **方法层被占** | 摘要："writing it into three consecutive cache positions at 3× the norm … makes tokens initially ranked 100–1000 … appear in 100% of continuations … To our knowledge this is the first cache-level steering intervention reported in a state-space or hybrid recurrent"。覆盖 GDN（Qwen3.5-0.8B）、Mamba-2、RWKV-7；"Softmax attention is outside the scope"，所以不碰 KV 与状态的对比 |
| B-K6 | 2404.05971 Paulo 等, *Does Transformer Interpretability Transfer to RNNs?* | B2 的 SSM 版本：只加一次状态，后续生成持续被转向 | **方法层被占（定性）** | §3.3："a steering state vector … was added at the last token before the model's response"，随后的故事被改成法语、改成恨的主题；"the effect of state steering is not additive"。Mamba、RWKV-v5，纯 RNN |
| B-K7 | 2507.08799 Belitsky 等, *KV Cache Steering*；2605.05983 PrOSV；ReFT | B2 的"缓存携带"前提 | **前提被占**（机制是这些方法的设计前提） | 2507.08799 §3.4："modifies the fixed key and value representations of past tokens after the prefilling stage … Future tokens then attend to this modified cache, so the steering effect propagates horizontally"。2605.05983 §5："PrOSV intervenes only at prefill stage and not decode stage. Similar to ReFT, PrOSV functions mainly by implicitly editing the KV cache" |
| B-K8 | 2605.10664 Kang 等, *Prompt–Activation Duality (GCAD)*（NeurIPS 2026） | B4 痛点（KV 污染）与 B2 | **痛点被命名；机制只是推测** | §3.2："A likely mechanism is KV-cache contamination: each generated token writes steered states into the cache, so later tokens attend to an increasing set of perturbed states and the error compounds"。§5.1：10 轮对话，"KV cache persisted across turns and steering hooks active for every newly generated token"。转向从不撤除，也没有重算缓存的对照，因此文本与缓存在这里是混在一起的 |
| B-K9 | 2609.32102 Wang & Reid, *Residual Streams Read, Recurrent States Remember* | B3 的邻居：递推状态是"补充载体" | **部分覆盖** | 摘要："identify recurrent state as a complementary carrier of workspace content … separating recovery, persistence, verbal steering"；"Recurrent state alone also supports verbal steering"。混合模型 Nemotron 上状态注入有 93/99 次在 top-1 被报告出来，但 §2 写明 "its SSM state and residual stream omit the attention KV cache, so its joint readout is incomplete" |
| B-K10 | 2605.06225 *Memory Inception* | B4 | 方法邻居 | 摘要："supports mid-conversation behavior shifts without rewriting the visible transcript"（只在部分层插入 KV 库）。这是"不经文本、经缓存改行为"的正向工程用法 |

**"继续 / 撤除 / 无干预重建"三臂或等价设计**：没找到完整的三臂。最接近的是 2609.11020 的同 token 序列对照，相当于"重建"一臂，但只在表示层、Llama 上做。2610.04967 有"继续"对"撤除"（全程转向对前缀转向），没有"重建"。2603.16335 有 all / prefill / decode 三种位置，没有"重建"，也没分 KV 与状态。三者都不是混合架构里的 KV 对状态分离。另一个搜索摘要器给出的"重算 KV 对照"建议是它自己编的，不算文献。

## 2. S 线杀手

主张拆成：S1 第一个全注意力层之前做加性干预时，配对事实敏感度约为 0；S2 表现为首 token EOS；S3 边界与 sink/massive activation 形成层对齐；S4 EOS 是"上下文不可用时的默认输出"。

| # | ID / 标题 | 杀哪条 | 层级 | 原文证据 |
|---|---|---|---|---|
| S-K1 | 2602.02712（前一轮已读）命题 4.1 | S1 | **被蕴含（渐近）** | 对所有位置都非零的 v，α→∞ 时 logits 趋于 LN(v)Wᵀ，输出与输入无关。若 LN(v)Wᵀ 的 argmax 是 EOS，S2 就成了它的推论。这需要按通道核对（前一轮 §4.2 检验 1 尚未做） |
| S-K2 | 2409.03621 / 2406.19384（前一轮已读） | S1 | **结论在相邻干预类型上被占** | 早层替换或删层后任务掉到随机水平，"对当前 token 失明" |
| S-K3 | 2608.12149（前一轮已读，本轮复核）+ 2605.08504 | S3 | **类比层覆盖竞争解释** | write–sink–cancel 出现在全注意力层前一层。本轮复核：它的干预读数是任务准确率，§F.2 的恢复干预甚至提升了检索，全文没有 EOS 或空输出的读数。小号 Qwen3.5 不在它的覆盖范围内 |
| S-K4 | 2410.01866 Oh 等, *House of Cards: Massive Weights in LLMs* | S2（失效形态）、S3 | **部分覆盖；形态与 S2 相反** | 图 1："When the top-5 massive weights are zeroed out, instruction-tuned LLMs completely lose their ability to generate text"；§2："When massive weights are set to zero …, the model repeats the same text as the user prompt"。破坏早层 massive 结构得到的是**复述提示**，不是 EOS |
| S-K5 | 2411.07191 Yu 等, *The Super Weight* | S2、S4 | **部分覆盖；失效形态是停用词，不是 EOS** | "pruning the super weight destroys quality by dampening the super activation and shifting almost all logit probability mass to stopwords"；"Llama-7B generates complete gibberish" |
| S-K6 | 2311.08817 Eikema & Aziz, *MAP's not dead yet* | S4（EOS 是默认输出） | **类比层支持，可能把 S4 降为已知** | §3："The basic LLaMA model has empty modes for a majority (70.7%) of prompts"；MT 模型有 57.7% 的输入众数是空序列。注意轴的区别：整序列众数是空，不等于首 token 的 argmax 是 EOS，二者不能互推 |
| S-K7 | 2603.22473 Borobia 等, 对 Qwen3.5-0.8B 与 Falcon-H1 的消融 | S1/S3 的模板层（在同一族模型里删早层） | **部分覆盖** | §4.4："Attention layer 15 produces the largest average drop … followed by linear layer 0"；随机消融里"含 layer 0 的试次困惑度 204,370，不含时平均 350"。读数是困惑度和准确率，没有 EOS 或事实敏感度 |
| S-K8 | ICML 2026 Seok & Kim, *Generation Collapse in CAA Steering*（OpenReview iRtgyVxRi1） | S2（"截断崩溃"可能就是早 EOS） | **未取到正文，不能判定** | 只读到会议页摘要："repetition collapse and truncation collapse"，以及"只转向早期 token 能减少崩溃"。OpenReview 的 PDF 返回 HTML，没有取到 |
| S-K9 | 2606.00930 Jiang, *Mamba-2 State Sink* | S3 在 SSM 里的类比 | 仅读摘要 | 状态 sink 落在 BOS 和换行上；抑制相关头后 needle 检索从 30/30 掉到 0/30 |

没找到的：(a) 有人在第一个全注意力层之前做加性干预并报告首 token EOS；(b) 有人用配对事实敏感度量化"上下文不可用"；(c) 小号 Qwen3.5（2B/4B/9B）上 sink 形成层与失稳边界的对齐。2504.02732（Barbero 等）只说去掉 BOS 会让扰动扩散更远，没有 EOS 读数。sink 综述 2604.10098 里 grep 不到"去 sink 后输出 EOS 或空"。

## 3. 痛点证据

**正面（具名方法、具名条件下失败）：**
- 2605.10664：CAA/persona-vector 在 Qwen2.5-7B 上做 10 轮对话、缓存跨轮保留时，连贯度漂移 −18.6；作者归因为 KV 污染。这是"转向的副作用在状态里累积"最具体的证据，但转向从未撤除。
- Seok & Kim（ICML 2026）：CAA 在 Llama-3.1-8B-Instruct 上出现截断崩溃。仅摘要。
- 生产侧：Qwen3.5 在 vLLM/LMCache 里以 `--mamba-cache-mode align` 给 GDN 状态做快照复用，LMCache 注明缓存与新算"不是 bit-exact"（来自搜索结果对文档的转述，没有直接取文档）。可见带状态缓存复用确实存在，但**没有找到任何报告"转向经前缀缓存污染下一个请求"**。vLLM 的相关条目是多模态哈希碰撞，不是转向。
- 2603.22061（Qwen3.5-2B 拒答方向消融）：对照组选取方式失败。作者没有把失败归因于 GDN，提到 GDN 只是作为背景（"the behavior of refusal directions extracted from such layers … has not been characterized"）。算不上"混合架构转向失效"的证据。

**反面（没人痛，或痛点被消解）：**
- 2610.04967、2605.05983、2507.08799、ReFT 都把"撤掉或只在前缀干预后效应仍在"当成**优点**来用：一次干预、开销低、能力保留更好。实践者想要的是"关不掉"，而不是怕它。B 的"关不掉"痛点要换一个说法才站得住，例如多租户共享缓存、撤除失败的安全场景。目前没有找到实际受害报告。
- 2609.11020：单层激活注入有 reset dynamics，不会累积。这削弱了"残留"会成为普遍问题的说法（只在 Llama 晚层上测过）。
- 2609.04721（Bosco & Srinivasan）：拒答方向可以跨 Transformer / SSM / RWKV / Zamba2 混合架构迁移并转向，失效点在"在哪读"，不在"在哪施加"。对"混合模型转向不安全"不利。
- 2604.01168：GDN 初始状态扰动在提示内衰减到 0.03% KL，对"递推状态长期携带"不利。
- S 线痛点：没有找到实践者报告"早层转向输出空回答"。最接近的是 2503.06040 与 CORAL（2602.06022）提到早层转向更容易损伤，只读到摘要。

## 4. 引用链（第 5 步）

Semantic Scholar 取 citations 与 references（limit=100），多次遇到 429，重试后全部取到。被引总数按 API 返回的条数计（有 meta 的标注 citationCount）。

| 邻居 | 被引（扫描条数） | 参考文献扫描 | 取到正文的新条目 | 新发现 |
|---|---|---|---|---|
| 2608.12149 | 2 / 2 | 52 | 0（2609.24066 grep 后无关；2610.20503 只读摘要） | 无新威胁；参考文献里有 Gated Attention 2505.06708、Systematic Analysis of Hybrid LA 2507.06457，未读 |
| 2610.16745 | 0 | 25 | 0 | 无 |
| 2606.29522 | 3 / 3（meta citationCount=3） | 30 | 0（2609.24635 只读摘要） | 2609.24635 讲 KV 里写下的是路由记录，与 B 是远邻 |
| 2605.06342 | 2 / 2（meta=2） | 39 | 0 | MetaSteer、Inherited Heads，无关 |
| 2507.08799（KV Cache Steering） | 12 / 12 | 34 | 1（2605.06225） | Memory Inception（B-K10）；2607.26228 等未读 |
| 2404.05971（Mamba/RWKV 转向） | 12 / 12 | 28 | 3（2609.32102、2609.04721、2605.12770） | **B-K9、B-K5**，以及反面痛点 2609.04721 |
| 2602.22719（SSM 子空间瓶颈转向） | 3 / 3 | 83 | 1（2606.00930，仅摘要级） | S-K9 |
| 2605.10664（GCAD，补充邻居） | 7 / 7 | 35 | 2（2610.04967、2609.11020） | **B-K1、B-K2**，本轮最重要的两条 |

另外由搜索得到、不在引用链里的：2603.16335、2604.01168（同一作者 Young 的 WriteSAE 系列）。

## 5. 查询与阅读量

- WebSearch 35 条（日志见下），WebFetch 1 次（ICML 页面），OpenReview PDF 1 次失败。
- 取到全文并定向 grep 的：2610.04967、2609.11020、2603.16335、2604.01168、2605.12770、2404.05971、2507.08799、2605.05983、2605.10664、2609.32102、2609.04721、2410.01866、2411.07191、2311.08817、2603.22473、2603.22061、2604.10098（grep）、2502.19649（一段），另复核 2608.12149。按自查规则共 **18 篇新读加 1 篇复核**。
- 仅摘要或 grep 未命中的：2606.00930、2609.24635、2609.24066、2610.20503、2605.06225（摘要加 grep）。
- 未取到的：Seok & Kim ICML 2026 正文；2503.06040 与 2602.06022 只有搜索摘要。

检验轮次：B 线是第一轮（35 条查询中约 20 条针对 B）；S 线中 S1/S3 有前一轮 20 条，加本轮约 15 条，S2/S4 是第一轮。

## 6. 边界申报

- 2610.04967（10-04）、2609.11020、2609.32102 都是 9–10 月的新预印本；10 月下旬的并行工作很可能还没进 S2 索引。
- OpenReview 和 ACL Anthology 没有系统检索；Seok & Kim 未读到正文，"截断崩溃 = 早 EOS"无法判定。
- 生产侧（vLLM/LMCache）痛点只经由搜索摘要转述，没有直接取文档；GitHub issue 没有系统扫描。
- 没跑非英文查询。
- 2603.16335 的 decode_only 零结果只覆盖一个特质、一个模型，样本条件见其表 5。

## 7. 查询日志

1 KV cache steering one-shot reasoning small LMs；2 activation steering Mamba state；3 steering effect persists after removal KV cache；4 hybrid linear attention GDN steering；5 steering prefill only then removed cached KV；6 steering empty response EOS high coefficient；7 attention sink removal generates nothing EOS；8 state injection linear attention RNN persists；9 massive activation ablation degenerate/empty；10 early-layer perturbation context-independent；11 prefix cache reuse steering contamination vLLM；12 steering first tokens then stop duration decay；13 Generation Collapse CAA arXiv；14 steered states KV cache compounding；15 remove mid-generation persistence vs no steering；16 Qwen3-Next/Qwen3.5 steering refusal hybrid；17 intervention before first attention ignore prompt end of text；18 EOS default when context unavailable；19 truncation collapse EOS steering；20 first-layer sink formation counterfactual facts；21 super weight removal gibberish；22 Jamba/Zamba/Falcon-H1 steering；23 prompt-only vs generated-only steering KV；24 Mamba state h_t injection decay；25 CAA repetition/truncation collapse seven behaviors；26 unconditional prior EOS noise injection empty output；27 steering layer sweep early layers outputs nothing；28 massive emergence layer predicts steering breakage；29 early layer steering premature EOS；30 Qwen3.5 GDN state cache reuse vLLM/SGLang；31 steering hysteresis recompute cache tokens vs cache；32 Qwen3.5 first full attention layer intervention ablation；33 Nemotron-H/Mamba-2 hybrid steering safety；34 early-layer corruption parametric fallback knowledge conflict；35 Qwen3.5 GDN state steering persists。
