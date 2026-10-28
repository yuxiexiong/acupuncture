# 早层失稳机制归因：七步查重报告

日期：2026-10-28（北京时间晚）。状态：**纯覆盖报告**，不含新颖性论证；新颖性段落等合同 1 结果站稳后再写。对象是 [下一阶段建议](../next-stage-dose-calibration-proposal-2026-10-28.zh-CN.md) 保留下来的主线：早层扎针后输出溃散的机制归因（主张 A、第 3.1 节四格仪器、主张 C）。剂量单位与输入依赖判据已由 [10-28 剂量查重](dose-calibration-related-work-audit-2026-10-28.zh-CN.md) 覆盖，本报告不重做，只在新证据改变其判读时注明。

全文对推断按三档标注：**推导**（有论证链）、**类比**（有邻域证据，跨域未验证）、**推测**（需独立验证）。被占的每一行都标层：**方法被占**不致命；**对象被占**、**结论被占**致命。

## 0. 结论先行

坏消息先说。这里只放事实约束与竞争解释；"前人见过"不算坏消息，按青蒿素判据另列于后。

1. **C3 的定性几何是结论被占。** "同一常向量加到所有位置使表示向 ĉ 收拢"可以由两条已发表结果推出：2602.02712 命题 4.1（α→∞ 时 logits 收敛到 LN(v)Wᵀ，与输入无关）和 2510.06477 定理 1、推论 2（共同大分量迫使最大奇异值占优，并给出各向异性与熵的界）。这句定性陈述只作必引。两者都没给出的是：有限剂量下哪一层、多大剂量已进入渐近区。这一步是提纯，见第 4.1 节。
2. **"压缩导致题目信息不可用"有直接反证。** 2510.06477 显示正常模型的中层本来就压缩到约 0.02 比特熵，而模型照常工作。所以收拢本身不足以解释失稳，第 3.1 节"方向收拢不等于信息已被抹掉"的保留是对的，而且必须升格为待检验的分叉。
3. **C1 的"早层天生更脆弱"有不利的类比证据。** 2606.11375 发现按每层激活尺度归一化之后，探针层面的深度脆弱性梯度大部分消失。C1 应限定在输出层面陈述，不能写成"早层表示更脆弱"。
4. **C5 有一条文献支撑更强的竞争解释。** 2608.12149 在包括 Qwen3.5 在内的混合线性注意力模型里发现，massive activation 在每个全注意力层的前一层写入首 token 与标点，在全注意力层充当 sink，随后被抵消；删掉其中最大的 4 个坐标，下游准确率相对下降 21.9%–63.6%。仓库数据里 2B/4B 的失稳恰在 L3（第一个全注意力层）骤停。"注入破坏 sink 形成"必须作为对照假说写进合同。这一条属于**类比**。

先例支持现象的普遍性（青蒿入药，不是否证）：

- **C1 的现象在相邻干预类型上已被观察。** Ben-Artzy 与 Schwartz（2409.03621）把前面 token 的隐藏态在早层换成等范数随机向量，任务掉到随机水平；在后 30–50% 层这样做几乎无损。Lad 等（2406.19384）删或换第一层是灾难性的，作者解释为后续网络"对当前 token 失明"。它们说明早层失明不是我们配方或 Qwen3.5 的特例。只禁一句过度声明："首次发现早层干预使输出与输入无关"。
- C1 的后一半"深层保持题目依赖"，在提示位置这部分与两段式结果一致，可直接引作解释。

仍空着的，均在对象层：

- 单个原生 MLP 通道、按残差范数标定的加性剂量、早层全层扫描、四模型的输出失稳分型。Liu 2606.19831 全文点名的神经元最早在 L8，正文没有 L0–L7。
- 用"信息在场对读出被压"的读数去**归属转向导致的崩溃**。概念上的区分已有（Shih 2606.29522），但对象是成功的功能向量转向、中层、微调后的状态追踪模型。
- Qwen3.5-2B/4B/9B 上 sink 形成层与失稳区边界的关系。2608.12149 覆盖的 Qwen3.5 是 27B、35B-A3B、122B、397B。

本轮是 C2–C5 按现行表述的**第一轮**检索；C1 的一部分在 10-28 剂量查重中经过一轮。存活不等于强度，见第 5 节阅读量。

## 1. 被查主张与预期结论句

| 编号 | 主张 |
|---|---|
| C1 | 单通道 MLP 加性干预（剂量 = 该层残差范数中位数的倍数，全提示位置注入）在 L0–L3 使输出与题目无关（首步 EOS、常数 token 循环、模板回声）；深层保持题目依赖、坏在内容；控制实际强度与注入时段后仍成立 |
| C2 | 配对事实题（只差一个关键事实）上的事实边际与压制量组成四格，区分"信息受损"与"输出被压制" |
| C3 | RMSNorm 之后同一常向量加到所有位置，各位置方向向 ĉ 收拢，位置间角度差被压缩；早层残差约等于 embedding、范数小，故更脆弱 |
| C4 | 早层崩溃是 prefill 位置现象，只解码注入在早层不崩 |
| C5（推测） | 失稳持续到哪一层，由残差中 embedding 以外成分的占比决定 |

结论层检索用的预期结论句：S1 早层扰动使输出与提示无关而深层不会；S2 早层干预破坏信息、后层干预偏置读出；S3 常向量加到所有位置使表示塌缩；S4 早层扰动造成崩溃的机制是破坏 attention sink 或 massive activation 的形成。

## 2. 七步执行记录

按协议记忆的修订顺序执行：6 → 5 → 1/2/3/4 → 7。判生死的引用一律取 PDF、`pdftotext` 抽文本后 `grep` 核对；搜索摘要器的转述不作证据。本轮就抓到一次摘要器转述错误：2606.11375 把 APEX 描述为"输出不再依赖输入时的噪声水平"，而 APEX 原文（2602.03586）是 CIFAR-10 上 top-1 概率降到 0.5 以下的噪声尺度，与输入无关性无关。

| 步 | 做法与查询数 | 主要命中 |
|---|---|---|
| 6 对抗检索（前置） | 显式问"什么能杀死它"；11 条 | Shih 2606.29522（状态对偏置）；2608.12149（Qwen3.5 族 PAS）；2510.06477（sink 与压缩谷，定理 1）；2511.17194（BOS 锚定扰动沿压缩谷放大）；2606.11375（归一化后深度梯度消失）；Ben-Artzy 2409.03621；SKOP 2605.06342（转向改 QK 匹配致注意力改道） |
| 5 引用链 | Semantic Scholar 前向被引 6 个邻居，取到 4 个；OpenAlex 补 1 个 | 2510.06477 的 62 个被引中取出 2610.16745（sink 形成前的隐藏态几何，可因果改变 sink）；2409.03621 的 37 个被引中取出 2605.06105（SPEED，上层只给解码 token 可见）；2606.29522 被引 3、2608.12149 被引 2，无新威胁；2606.19831 被引 0；2602.02712 与 2511.17194 限流未取到，OpenAlex 对 2602.02712 计数为 0 |
| 1 抽象阶梯 | 模板"干预 T 在深度 d 毁掉输入依赖（早）或内容（晚）"，T 取替换、冻结、删层、换层、噪声、零化 massive activation、KV 替换；4 条 | 删换层（Lad）、替换冻结（Ben-Artzy）、零化 massive activation（Sun 2402.17762：置零灾难，置均值无损）、上层提示 KV 可换成同模板中性填充（2605.30574） |
| 2 方法论单独搜 | 配对反事实提示 + 答案 logit 差；信息在场读数；注意力改道读数；3 条 | 配对只差一个事实的提示与答案 logit 差是 patching 的标准做法（Ben-Artzy 的 Italy/France 中途替换即一例；Shih 用目标答案 margin）；SKOP 的焦点集注意力质量；Patchscopes 及其忠实性警告（解码可能被先验覆盖） |
| 3 蕴含检索 | 找能把预期结果变成推论的工作；3 条 | 2602.02712 命题 4.1；2510.06477 定理 1、推论 2；Grassmannian Geodesic Steering（NeurIPS 2026，仅海报摘要：加性转向在强干预下可证明地塌缩有效秩）；两段式结果蕴含 C1 后一半 |
| 4 同义术语 | rank collapse / over-smoothing / token uniformity / anisotropy / compression valley / attention sink / massive activation / super weight / entropy neuron / suppression / prompt-independent / context neglect；中文一条；4 条 | Stolfo 2406.16254 熵神经元（单神经元经末层归一化尺度统一缩放 logits）；2603.05498（massive activation 造成跨层近常量表示，作用类似隐式参数）；中文检索无直接命中 |
| 7 边界申报 | 见第 6 节 | |

## 3. 逐篇覆盖表

"全文定向"指取到全文并针对本报告的问题读了相关段落，不是通读。

| 论文 | 与本线主张的关系 | 读取程度 |
|---|---|---|
| Shih, Winnicki, Darve, *When Does Activation Steering Change What a Model Computes From?*, 2606.29522 | C2 的概念对手。区分"写入后续计算会用的状态"与"把后续计算偏向同一输出"。对象是功能向量转向、中层、微调出的状态追踪 7B 模型；单层替换只得到全程 patch 的不到 2% margin 增益，转向向量范数是自然变化的 77 倍（Qwen）与 26 倍（Llama）。不碰崩溃、早层、单神经元 | 全文定向（摘要、§1、§8） |
| Su 等, *Massive Activations in Hybrid Linear Attention LLMs*, 2608.12149（在审） | C5 的竞争解释。PAS 紧挨全注意力层之前出现，写在首 token、标点与分隔符（换行、句号、逗号）上；write–sink–cancel：前一层写入，全注意力层充当 sink，同层反号抵消；删最大 4 坐标下游准确率相对降 21.9%–63.6%。覆盖 12 个公开检查点，含 Qwen3.5-27B/35B-A3B/122B/397B，不含 2B/4B/9B | 全文定向（摘要、§4.1、附录模型表） |
| Queipo-de-Llano 等, *Attention Sinks and Compression Valleys…*, 2510.06477（ICLR 2026） | C3 结论被占的来源之一。定理 1：σ₁² ≥ M + αR；推论 2 给出占优比、各向异性与熵的界。正常模型中层熵约 0.02 比特仍正常工作；Llama3-8B 在 L0 消融 BOS 的 MLP 贡献后 sink 与压缩都消失 | 全文定向（§3.2、图 4） |
| Taimeskhanov 等, *Towards Understanding Steering Strength*, 2602.02712（ICML 2026） | C3 结论被占的另一来源。命题 4.1：对所有位置非零的 v，α→±∞ 时 logits 趋于 LN(±v)Wᵀ，输出分布与输入无关。附录 A.2 两处说早层转向"已知效果更差"，未给逐层机制 | 全文定向（§4、§5、附录 A.2） |
| Ben-Artzy & Schwartz, *Attend First, Consolidate Later*, 2409.03621 | C1、C4 的模板层覆盖。对前面 token 的第 k 层隐藏态做等范数随机替换、打乱、冻结：早层掉到随机水平，约后 30–50% 层几乎无损；Italy→France 中途替换，顶部三分之一层被忽略、之前则模型跟着改答。模型为 Llama2-7B、Mistral-7B、Yi 等。是替换不是叠加 | 全文定向（摘要、§2.1、图 2–4） |
| Lad, Lee, Gurnee, Tegmark, *The Remarkable Robustness of LLMs: Stages of Inference?*, 2406.19384 | C1 的模板层覆盖。删或换第一层对所有模型都是灾难；作者推断第一层是 embedding 的延伸，消融后"后续网络对当前 token 失明" | 全文定向（§3–4） |
| Reblitz-Richardson, *When Probing Accuracy Saturates, Fragility Resolves*, 2606.11375 | C1 的不利类比证据。原始噪声下深层显得更稳，是因为深层激活更大；按每层 RMS 归一化后深度梯度大部分消失（OLMo-2 1B，探针层面，高斯噪声） | 全文定向（摘要、§4.4） |
| Sun, Chen, Kolter, Liu, *Massive Activations in LLMs*, 2402.17762 | C5 背景。LLaMA2-7B 的 massive activation 在 L2 首次出现；置零致灾难，置均值无损 | 全文定向（§3–4，表 3） |
| Yang & Song, *Before Attention Sinks Form*, 2610.16745 | C5 的可检验性先例。sink 形成前 2–3 层的隐藏态谱变化可预测且可因果改变后续 sink，对照为等范数随机谱扰动；Qwen2.5、GLM-Z1、GPT-OSS | 全文定向（摘要、§1） |
| Luo 等, *Don't Lose Focus: SKOP*, 2605.06342 | C2、C3 的方法层近邻。主张转向改变 QK 匹配，把注意力从焦点 token 挪走，是效用下降的主因；焦点集注意力质量是现成读数。Llama-3.1-8B、Gemma-2-9B，所有层注入；不做逐层失稳 | 全文定向（摘要、§3、§5） |
| Liu, *Leverage Is Not Reach*, 2606.19831 | 提议自列的最大风险"附录已覆盖早层"。全文点名的神经元最早 L8，L0–L7 无条目；每模型 24 个随机神经元的抽层范围在所读段落未写明；代码未查 | 全文定向（§4.1，全文神经元编号计数） |
| *A Single Layer to Explain Them All*, 2605.08504 | C5 背景。Qwen3-4B、Qwen3-8B（稠密 Qwen3，非 3.5）的 massive emergence 层为 L7；RMSNorm 与 FFN 共同产生 | 全文定向（§3） |
| Xu 等, *Progressive Behavioral Drift through Compression Valleys*, 2511.17194 | 小扰动锚定在 BOS、沿压缩谷被自回归放大；对象是保持流畅的行为漂移，不是崩溃 | 全文定向（摘要、§1） |
| Kumar 等, *Probing the Prompt KV Cache*, 2605.30574 | C4 模板层：上层提示 KV 换成同模板中性填充几乎不掉分，置零则崩；Qwen3、Gemma 3、Llama 3 | 摘要 |
| *SPEED: Shallow Prefill, Deep Decoding*, 2605.06105 | C4 模板层：Llama-3.1-8B 只在 75% 的层给提示 token 建 KV，分数 51.2 对 51.4 | 摘要 |
| Stolfo 等, *Confidence Regulation Neurons*, 2406.16254 | C2 压制分支的机制先例：熵神经元写入反嵌入零空间，经末层归一化统一缩放 logits | 摘要 |
| *The Spike, the Sparse and the Sink*, 2603.05498 | massive activation 造成跨层近常量表示；sink 让单个头偏向短程依赖 | 摘要 |
| Liu 等, *Grassmannian Geodesic Steering*（NeurIPS 2026） | C3：加性转向在强干预下可证明地塌缩有效秩 | 仅海报摘要，证明未核 |
| *How Do Language Models Choose Between Context and Memory?*, 2609.00753 | C2 设计参考：配对提示上的方向交换与匹配对照 | 摘要 |
| APEX, 2602.03586 | 方法层；CIFAR-10 的逃逸噪声；无 LLM 证据 | 检索片段 |

## 4. 逐条覆盖判定

| 主张 | 判定 | 层 | 依据 |
|---|---|---|---|
| C1 前一半：早层使输出与题目无关 | 部分覆盖 | 结论在相邻干预类型上被占；对象未被占 | Ben-Artzy（替换前 token 隐藏态）、Lad（删换第一层）。加性、单原生通道、剂量阶梯、四模型全层的对象未找到；Liu 无 L0–L7 |
| C1 后一半：深层保持题目依赖 | 已被蕴含（提示位置部分） | 结论 | 两段式结果：上层不再从前 token 读信息（Ben-Artzy；2605.30574；SPEED）。深层"坏在内容"应来自末位与解码位置的注入，未被蕴含 |
| C1 限定语：控制强度后早层仍更脆弱 | 有不利类比证据 | 结论 | 2606.11375：RMS 归一化后探针脆弱性深度梯度大部分消失。陈述须限定在输出层面 |
| C2 概念：信息受损对读出被压 | 已覆盖 | 方法（概念） | Shih 2606.29522 的状态对偏置区分 |
| C2 读数：配对事实题与答案 logit 差 | 已覆盖 | 方法 | patching 标准做法；SKOP 焦点集注意力质量；Patchscopes |
| C2 对象：用这组读数归属转向导致的崩溃 | 未找到 | — | 检索到的工作都用于成功转向或自然行为 |
| C3 几何：常向量使表示收拢 | 已覆盖 | 结论 | 2602.02712 命题 4.1；2510.06477 定理 1 与推论 2；Grassmannian（摘要） |
| C3 因果：收拢导致题目信息不可用 | 未找到，且有反证 | — | 2510.06477：正常中层高度压缩仍工作 |
| C4：早层崩溃是 prefill 现象 | 部分覆盖 | 结论（一臂） | "提示除末位"一臂的深度形态已被 Ben-Artzy 蕴含；"末位加解码"一臂在早层的结果未找到；Yap 2603.16335 为单模型零结果（见 10-28 报告） |
| C5：由非 embedding 成分占比决定 | 未找到覆盖；出现竞争解释 | — | 2608.12149、2605.08504、2510.06477、2610.16745 支撑"sink 与 massive activation 形成层"这一替代解释 |

### 4.1 被占各行：前人到哪、我们推到哪、谁改做法

按"青蒿素判据"，被占的行先进这张表，再谈删留。"我们推到哪"只写仓库已有数据，不写计划。

| 主张 | 前人到哪 | 我们推到哪（已有数据） | 谁改做法 |
|---|---|---|---|
| C1 前一半 | 替换、冻结、删换整层，看任务准确率；Llama2、Mistral、Yi | 单原生通道加性注入；Qwen3.5 2B/4B/9B 与 Llama-3.1-8B 全层每层十点；正负剂量阶梯；失稳按首步 EOS、常数 token、模板回声分型；去重 18,272 份回答 | 在早层用单神经元或转向配方的人（Liu 配方、lyra 一类工具）：早层剂量上限要单独定 |
| C1 后一半 | 上层不再从前 token 读信息（替换、KV 置换），只看准确率 | 深层 ±1 多数保持 8 种首 token，坏在内容；全位置加性注入 | 在深层做转向的人：深层失败不会被首 token 或输入依赖判据抓到，要用内容判据；排查应看末位与解码位置 |
| C1 限定语 | 归一化后探针脆弱性深度梯度消失 | 无表示层数据；只有输出层数据 | 写法改变：主张限于输出层面 |
| C2 概念与读数 | 状态对偏置的区分；patching、答案 margin、焦点集注意力质量 | 尚无数据；仓库只有首 token 种数、首步 EOS、范数与余弦轨迹 | 若做成：解释转向失败的人可以分清"信息没了"还是"被压住"，前者只能降剂量，后者可以从读出端修 |
| C3 几何 | 命题 4.1 只给 α→∞ 的极限；定理 1 的压缩界以单个大范数 token 为参照 | 有限剂量阶梯、逐层、四模型的失稳数据；9B L0 的通道常数输出；注入层可由归档反解每位置与写入方向的夹角，尚未算 | 选剂量的人：若第 4.2 节检验成立，早层在什么剂量进入渐近区、会吐出哪个 token，可以只凭权重预报，不用跑生成 |
| C4 | 提示位置的上层 KV 可弃；Yap 单模型零结果 | 全部已有数据都是全位置注入，无时段对照 | 选注入位置的人：早层是否只需避开提示位置 |

### 4.2 由本轮检索推出的两个零 GPU 检验

两条都只读既有归档或模型权重，不跑生成。

1. **命题 4.1 是否已解释 9B L0 的通道常数输出。**（推导）命题 4.1 预言大剂量下输出趋于注入方向本身的反嵌入。9B L0 有 4 个通道八题输出逐字相同、换通道换一个固定词（托、Stack、映、换行）。检验：对这 4 个通道取 down_proj 对应列，经末层 RMSNorm 增益后乘反嵌入矩阵，看最大 token 是否就是观测到的固定词。若是，这一条观测降为命题 4.1 的推论；若否，说明 dose 1 在 L0 尚未进入渐近区，常数输出另有来源。
2. **失稳区边界是否等于 sink 形成层。**（类比）轨迹归档存有每层每位置的原版残差范数。检验：读出四个模型首 token 范数相对其余位置的跃升层，与"八题同首 token 的通道数"随层的下降点对齐比较。2B/4B 是否在 L2→L3 跃升、9B 是否更晚，决定 C5 与竞争解释谁更站得住。

### 4.3 对合同 1 设计的直接影响

以下是建议，不改变冻结状态，也未授权运行。

- **四格仪器要加一个残差层面的信息在场读数。** 事实边际取在答案位置的 logits 上，量的是"在输出端可用"，不是"在残差里还在"。"信息受损"一格因此混了两种情况：残差里已没有该事实，与残差里还有但注意力不再路由过去。建议加线性探针或把干预后残差 patch 进干净前向的读数，并加 SKOP 式的焦点集注意力质量。Patchscopes 类解码有被先验覆盖的风险，不宜单用。
- **把 sink 破坏写成登记的对照假说。** 读数：注入后 L3（或各模型首个 sink 层）对首 token 的注意力占比。2610.16745 已示范等范数随机扰动作对照。
- **"提示除末位"一臂在早层与深层的预期形态，按 Ben-Artzy 预先写成文献派生预言。** 这一臂用来标定，不用来宣称发现。
- **C1 的陈述限定在输出层面**，在动机段引 2606.11375 作为必须回应的反证。

## 5. 阅读量与检验轮次

| 项 | 数 |
|---|---:|
| Web 检索查询 | 20 |
| 引用链：取到前向被引的邻居 | 4 / 6 |
| 取到全文并定向阅读 | 13 |
| 仅摘要 | 6 |
| 仅检索片段或海报摘要 | 若干，未计入阅读 |

按 CLAUDE.md 语料质量自查，"读过"只算取到全文并做了定向追问的 13 篇。C2–C5 按现行表述只经过本轮检验；C1 另有 10-28 剂量查重中的一轮。

## 6. 边界申报

- **引用链不完整。** Semantic Scholar 限流，2602.02712 与 2511.17194 的被引没取到；OpenAlex 对 2602.02712 的被引计数为 0，可能是索引滞后。
- **Liu 代码未查。** 24 个随机神经元的抽层范围只能从正文推断，代码与补充材料可能含早层。
- **Grassmannian Geodesic Steering 只读到 NeurIPS 海报摘要**，未找到 arXiv 版本，证明未核。
- **2608.12149 在审**，结论可能变动；它的 Qwen3.5 覆盖不含 2B/4B/9B，小模型上的 PAS 位置未验证。
- **非英文只跑了一条中文查询**，无直接命中；日韩等未查。
- **非 arXiv 渠道**只经由检索引擎间接覆盖，ACL Anthology 与 OpenReview 未系统检索。
- **并行未公开工作与知识截止**：检索截至 2026-10-28；本线检索词刚好落在 sink 与 massive activation 的活跃区，近期并行工作的概率不低。
- **阅读深度**：全文定向阅读不是通读；未逐页核对附录。

## 7. 查询日志

1. "When Does Activation Steering Change What a Model Computes From" arXiv 2606.29522
2. early layer activation steering output independent of prompt mechanism attention sink massive activations collapse
3. steering vector information destroyed versus readout bias linear probe decodability after intervention LLM
4. adding constant vector all token positions RMSNorm representation collapse token uniformity steering large coefficient
5. layer-wise sensitivity noise injection hidden states LLM early layers most fragile perturbation output degenerate
6. single neuron early layer intervention causes end-of-sequence empty output LLM
7. arXiv 2511.17194 BOS anchor low-rank collapse amplified over depth
8. arXiv 2608.12149 massive activations hybrid linear attention Qwen3.5 Gated DeltaNet pre-attention spikes
9. APEX Ren 2026 escape noise Gaussian noise hidden activations output stops depending on input LLM
10. "stages of inference" layer deletion swapping first layer critical detokenization LLM robustness
11. steering intervention early layers model ignores context prompt-agnostic output information vs suppression logit lens analysis
12. activation steering disrupts attention sink causes degenerate repetitive output mechanism
13. steering vector applied only to prompt tokens versus only generated tokens comparison effect prefill decode injection positions
14. LLM outputs same token regardless of input after intervention early layer input-independent OR prompt-independent collapse depth
15. rank collapse over-smoothing token uniformity activation steering perturbation LLM residual stream depth
16. entropy neurons suppression neurons final layernorm scale EOS probability single neuron confidence regulation LLM
17. patchscopes decode information from hidden state after intervention information present but not used by output
18. arXiv 2605.30574 "Probing the Prompt KV Cache" dispensable layers
19. 激活引导 早层 干预 模型输出崩溃 与输入无关 神经元 注入
20. "Grassmannian Geodesic Steering" rank-preserving additive steering collapses effective rank arXiv

引用链：Semantic Scholar `graph/v1/paper/arXiv:{id}/citations`，对 2602.02712、2606.19831、2510.06477、2608.12149、2606.29522、2511.17194、2409.03621；OpenAlex `works?filter=cites:` 对 2602.02712。

## 8. 更正记录（2026-10-28 晚，第二版）

用户问本报告是否适用了青蒿素原则。复核后更正两处，均为本报告自身的判读错误，不涉及检索结果。

| 原稿 | 更正 |
|---|---|
| 把"C1 现象在替换、删层上已被观察"列入第 0 节坏消息 | 这是先例支持现象普遍性，不是否证。移出坏消息，另列为先例；只禁"首次发现"这一句 |
| C3 几何与 C1 后一半的"谁改做法"写"无；作必引" | 过严。定性陈述作必引不变；有限剂量与逐层的测量、深层失败的内容判据是提纯，各自写出改做法的人 |
