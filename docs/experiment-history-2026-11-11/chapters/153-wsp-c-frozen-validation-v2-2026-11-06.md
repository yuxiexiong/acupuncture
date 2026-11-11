# 153．C冻结验证v2准备

[返回总时间线](../README.zh-CN.md)

**时间定位**：版本/记录日期 2026-11-06；未从所选收据确定完整运行起止，不据目录名补写时刻。

**当时的目的与设计**

固定80个ROME主来源和10组VLind五条件扩展，每方法2320输入，保存独立AI复核及修订题包。

**实际过程、结果与后来更正**

自查与CPU验收通过，未运行待测模型，不是人工双审或独立效果结果。完整历史方案保留，本次没有启动它。

**来源身份**：`wsp-c-frozen-validation-v2-2026-11-06`；本章主体来源提交 `7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8`。下方原文中的状态是各文件写作时的状态，不能把早期“尚未运行”覆盖后期正式收据，也不能将后期结果倒填进早期设计。


## 原设计、执行过程、结果与更正全文

以下按“设计与题目 → 工程/执行记录 → 结果/更正 → 其他历史说明”组织；同类内没有可靠时间时保留路径顺序，不冒充严格先后。正文未删段；仅为本章节重排标题层级、把相对链接指向固定提交。原始字节另外完整保存。

### 原件 1：第一轮 C 冻结补丁：新来源、新问法与已有方法验证

原路径：`docs/wsp-c-frozen-validation-v1-2026-11-06/PLAN.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/docs/wsp-c-frozen-validation-v1-2026-11-06/PLAN.zh-CN.md) · [单独阅读副本](../library/a4387643c7496a72.md)；SHA-256：`a4387643c7496a726b2d419c48072ddfeb285c498715287093239ba4f9ac0e7e`。

---

#### 第一轮 C 冻结补丁：新来源、新问法与已有方法验证

> **2026-11-06 容量实审更新：** [新数据容量报告](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/wsp-c-data-capacity-audit-v1-2026-11-06/REPORT.zh-CN.md)已否决本版T200在现有数据上的可行性：新素材质量前最多52个不复用配对，单人逐图审核后24个候选；尚未双审或运行。下文保留原计划，不自动将200改成24执行。

##### Material Passport

- Origin Skill / Mode：academic-research-suite / experiment-agent / plan。
- 日期／版本：2026-11-06，C-FV-01 v1。
- Verification Status：UNVERIFIED（实验及工程未运行）；逻辑设计经作者自查通过，非独立审查。
- 授权：本次仅设计、旧证据 CPU 核对及文档交付；**没有模型调用、GPU、数据生成或实验执行授权**。
- 配套：[完整自查](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/docs/wsp-c-frozen-validation-v1-2026-11-06/SELF_CHECK.zh-CN.md)；[证据与哈希清单](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/docs/wsp-c-frozen-validation-v1-2026-11-06/sources.json)。

##### 1. 决策与设计卡

本轮回答：**第一轮 C 已冻结的 embedding＋norm 补丁，在未用于搜索的新来源、不同措辞上，是否仍改善常识与视觉证据的按题切换，并优于便宜的提示处理及两类已有干预？** 先验证这个具体补丁，不追加第三轮搜索，也不把本轮改成完整机制实验。

| 设计卡 | 本轮规定 |
|---|---|
| 主线 | 在视觉信息与常识冲突时，提高模型按问题要求选用证据的可靠性，同时保留另一种回答能力。 |
| 新增认识 | 从反复查看的开发集收益，推进到冻结补丁的来源外验证、有限措辞泛化及实际替代方法比较。 |
| 依据与最强反例 | D64 上主指标 +12.50pp；但搜索看过 50 个候选，补丁包含原问法关键词，旧 H 已曝光。优势可能只是措辞适配或搜索过拟合。 |
| 操作 | 固定第一轮 R45 的实际 BF16 张量；与原版、字面替词、开发集选出的提示方案、PvP、Nullu 比较；额外检查补丁加最佳提示是否仍有增量。 |
| 估计对象 | 同一冻结测试集上，各部署方式对完整回答联合正确率的总效果；不是 embedding 或 norm 的单独机制贡献。 |
| 可判读结果 | 有效、仅旧问法有效、提示可替代、已有方法更优、收益伴随损伤、区间太宽，分别保留；不把不显著当等效。 |
| 范围与成本 | 一个模型、一个补丁、一个任务族；目标 200 个全新来源组，7 个部署条件上限。数据容量与基线适配尚未验收。 |
| 退出 | 不足样本、身份/适配不通过则不开终验；终验后不调补丁、不换模板、不追加样本救显著性。 |

按青蒿素原则定位：视觉与常识冲突、激活引导、投影权重编辑均已有先例；本轮新增的是**这个具体静态补丁在严格未见条件下的收益、代价及可替代性证据**。不能据此宣称发明模型修复、首次解决视觉先验冲突、搜索方法优于所有方法，或已具备论文录用保证。

##### 2. 冻结资产与评分纠正

模型为 `Qwen/Qwen3-VL-4B-Instruct`，revision `ebb281ec70b05090aa6165b016eac8ec08e71b17`，不是 Qwen3.5 文本 4B。

补丁：`c-556e560bdc90cca68fd2622fa57651d2e7fc071f2dd83d39ea866c91f3b393f0`；35,792 个实际改变的 BF16 标量。部署时以归档张量 SHA256 为准，不用下面的文字配方重新近似制造补丁：

- 四个词行混合：pictured→image、bigger→larger、normally→typically，系数 0.5；-world→world，系数 0.25；保持原行范数。
- visual 主 merger norm weight/bias ×0.85；deepstack merger 2 的 norm weight/bias ×1.15。
- language 层 18–23 的 input norm weight ×1.025，均相对 W0。
- embedding 与 lm_head 共享权重，因此不是纯输入端改写；后续所有正常前向响应均允许变化，最终补丁无运行时 hook。

归档：[第一轮结果](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/wsp-vlm-open-repair-v8x50-2026-11-05/FINAL.zh-CN.md)、[C 回执](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/wsp-vlm-open-repair-v8x50-2026-11-05/receipt-C.json)。本次 CPU 重算归档自然回答：

| 指标，B0／64 来源／每来源 2 问法×2 排列 | W0 | 冻结补丁 |
|---|---:|---:|
| 原主指标 Jcf：反事实图的 usual 与 visual 同时正确 | 149/256＝58.203125% | 181/256＝70.703125% |
| J4：原图及反事实图四题同时正确 | 149/256 | 181/256 |
| J5：再加无图常识题 | 142/256 | 172/256 |

**口径纠正：`evidence.py::repair_score` 定义的是 Jcf。J4 在这两个快照恰好同分，不能据此说原指标就是四条件联合。** 保留历史记录，本轮以源码与原始逐题证据明确估计对象。256 个面板不等于 256 个独立样本；独立采样单位是来源组。

所有 2560 输入的准确率 2266→2309、修对 50／改错 7 含 B0/B1，不能与本轮仅 B0 的主表直接混成一个分母。旧 D64 用于开发，旧 H96 已看过结果，只能作已见回归资产。

##### 3. 新数据：先验收容量，再冻结终验

###### 3.1 当前实际库存

现有 Visual CounterFact size 元数据为 727 行、704 个 exact union 来源组；近重复隔离后 review pool 318 组。244 组已有视觉审核，其中 166 通过、78 排除；160 组被用于 D/H。故干净 review pool 中仅 **74 组未审核＋6 组审核通过但未入 D/H**，且这 80 组还需要排查其他运行曝光。不能把 `704−160` 直接叫作 544 个可用新样本。

本轮目标 T200，属于**同一公开任务族中的新来源留出**，不包装成独立外部数据集。暂不另造合成数据集，也不混入新的对象属性或任务。

###### 3.2 数据准备规则（待实施）

1. 建曝光账本：汇总 v6–v9、scale、Gemma 及其他已有 C 运行的 request/source IDs、图片像素哈希；凡参与过目标或其他研究模型推理、候选筛选的来源一律排除。只看过元数据或标签的记录另记曝光等级，不能称完全无人看过；不给基线拟合使用 T。
2. 复核原先因 pHash 相近而隔离的候选。pHash 只是候选，不等于实质重复；对全部近重复候选按相同图像、裁剪、重排、共同底图和对象对建实际来源连通分量。与旧曝光分量相连者排除；真正独立且只是 pHash 碰撞者可释放。**不撤销此前 78 个语义/标签审核失败项来凑数。** 每次释放须留理由和盲于模型输出的复核记录。
3. 两名审核者独立审核图中对象可识别、常识大小无歧义、原图与反事实图确实反转可见大小；分歧项排除。模型输出不可见。审核者身份、时间、判断原文保留；同一助手自查不能冒充两名独立审核者。
4. 对象对不与任何旧曝光组重复；同一素材/构图家族并为一个采样单位。共享单个对象名允许，但预先登记“对象名均未见／含旧对象名”分层；不声称对全新概念泛化。不得按 W0 错误或补丁收益筛样本。
5. 所有合格分量按 `SHA256('C-FV-01:20261106:'+source_id)` 排序，取前 200 个，每分量只取一个固定代表。冻结源 revision、图片及像素哈希、完整排除账本、题目、gold、解析器、模板与 split；剩余组不供本轮追加。

**数据门槛：若不足 200 个合格新来源组，本版不进入终验。** 交付真实可用数和排除原因；只能在没有看新模型结果的前提下修订样本量/精度要求或另立新数据构建方案，不能静默缩样本。当前属于“抽样方案逻辑成立，容量尚未证明”，并非运行就绪。

##### 4. 问法与条件矩阵

每个新来源保留五条件：无图常识、原图常识、反事实图常识、原图视觉、反事实图视觉。使用原 T0/T1 加两个新模板 U1/U2；两个对象次序都跑。仅使用原 B0 普通提问接口，统一追加 `Return only the object's name.`。

| 模板 | 常识问题 | 视觉问题 | 用途 |
|---|---|---|---|
| T0/T1 | 原冻结文本原样使用 | 原冻结文本原样使用 | 新来源、旧措辞 |
| U1 | Between {x} and {y}, which is normally bigger in the real world? | Of the two pictured objects, {x} and {y}, which looks bigger? | 新句法，保留已编辑词 |
| U2 | In everyday life, which of these two objects tends to be larger: {x} or {y}? | In this picture, which of these two objects looks larger: {x} or {y}? | 新措辞，避免 pictured/bigger/normally/-world |

模板语义须在模型调用前审核。保持“图中看起来大小”含义，不改成物体真实尺寸、像素面积或推理题。U2 用实际 tokenizer 核对四个编辑 token ID 的出现次数，分别报告模板、对象名、系统/输出要求；不能只用字符串搜索证明输入不含编辑 token。本计划已披露 U 文本，故它们是**前瞻冻结的新模板**，不是对所有设计者保密的随机自然问法；基线调参只用 D 的 T0/T1，不能用 U 的模型反馈。

每来源 `5×4×2＝40` 次自然回答，每方法 8000 次。主分析 U1/U2 共四个面板/来源；旧模板单列。U1/U2 分别报告，不能把平均收益解释成所有问法均稳健；这也不是跨语言或开放自然问法证明。

##### 5. 方法与公平比较

| 部署条件 | 固定规则 | 为什么需要 |
|---|---|---|
| W0 | 原版、原输入 | 补丁是否真有新增收益 |
| Wpatch | 第一轮 R45 张量、原输入 | 本轮唯一待验证的主方法 |
| LEX | W0；仅 question 区域固定替换 pictured→image、bigger→larger、normally→typically、real-world→real world；保护对象名与输出要求 | 最便宜的字面提示替代，尤其针对词行编辑 |
| P* | W0；在 D64 选出的最佳简单提示处理 | 避免只挑一条弱提示做稻草人 |
| PvP-C | 原版上任务适配 PvP 激活方向 | 同一视觉/常识冲突问题的直接近邻 |
| Nullu-C | 原版上任务适配 Nullu 静态投影 | 同样无需推理时 hook 的已有权重编辑 |
| Wpatch＋P* | 同一补丁加同一 P*，不再调参 | 提示优化后补丁是否还有剩余价值，补充分析 |

重复条件合并计算，最多七臂。所有方法共用原版 revision、processor、图像尺寸、自然解码、输出解析器和测试 IDs。不限制 Nullu 必须只改 35,792 个标量，也不让 PvP 只朝视觉方向推而故意损伤常识。

###### 5.1 简单提示候选：固定八种，只在 D 选择

候选为：identity、LEX、原 B1、下面 I1、I2、CANON、LEX＋B1、CANON＋B1。前缀固定为：

- B1：`Follow the scope of the question. For size in the image, use visible size even if unusual. For typical real-world size, use general knowledge even if the image differs. Return only the object's name.`
- I1：`Answer the question according to its stated scope. An unusual picture does not change typical real-world size; typical real-world size does not change how large objects look in a picture.`
- I2：`First distinguish the two tasks internally: everyday size versus visible size. Use the evidence requested by the question. Do not explain your reasoning.`
- CANON：保留两个对象与次序，常识统一为 `In everyday life, which is usually larger, {x} or {y}?`；视觉统一为 `In this image, which object looks larger, {x} or {y}?`，保持输出要求。路由只读问题文本：real world/real-world/everyday life/typically/normally 表示常识；若无这些词且出现 image/picture/pictured 表示视觉；其他输入保持原文。大小写归一。对象名通过原始输入的对象槽提取，各方法同样可读，不读取 gold/condition/template ID；记录每条路由。

这是已知任务接口上的确定性提示处理，不需要在线 LLM 改写成本。不声称八个候选穷尽了提示工程。

###### 5.2 PvP-C：保留核心操作，适配处明示

[PvP 原文](https://aclanthology.org/2025.emnlp-main.1262/)研究视觉/常识冲突的激活引导。[作者代码](https://github.com/rsinghlab/pixels_vs_priors)与原模型的具体层数不能照搬成 Qwen3-VL 配方。

- 仅在 D64 的反事实图上，成对提取 visual 与 usual 问题的最后输入 token decoder hidden state；两个旧模板、两次序等权，先来源内平均再跨来源平均，得到 `v_l=mean(h_visual−h_usual)`，不额外单位化。
- 在 decoder block 输出的最后 token 上加方向；prefill 最后 token 和各 decode 步都操作，保留原实现的时间范围。按同一文本路由规则，视觉用 `+αv_l`，常识用 `−αv_l`；无需知道图是否反事实或正确答案。无图常识也走同一规则。
- 固定开发网格：零基层号 `{9,18,27}` ×强度 `{0.25,0.5,1,2}`，12 个非零配置；identity 另作回退。完整方向，不新增 top-k 搜索。
- 必须验证 hidden-state 索引与 block 编号对应、同一提取位置、正确符号、hook 不污染后续方法；代码如不能保持上述语义，则标记适配失败，不能记成 PvP 科学失败。

这是 **PvP-C 任务适配版**，最终比较联合正确率而不是原论文的预测翻转率，不能拿两个指标的百分比直接比大小。

###### 5.3 Nullu-C：静态投影基线

[Nullu 原文](https://arxiv.org/abs/2412.13817)及[核心代码](https://github.com/Ziwei-Zheng/Nullu/blob/main/utils/halluedit.py)提供对比表征的低秩子空间与权重投影。原工作偏物体幻觉；本轮把对比数据改为 C，明确属于任务适配，不能称原论文结果复现。

- D64、T0/T1、两次序、五条件，每题构造正确/错误两个候选对象名的 teacher-forced 完整序列；保持同一图、问题及回答格式，配对 ID 完全一致，不只挑原版错误题。
- 按作者 mean hidden embedding 路径提取有效序列 token 的均值，去除 padding；各层构造 `(h_correct−h_wrong)/2`，SVD 的前 r 个右奇异向量组成 U。默认不做 centering。
- 对 decoder MLP down-projection 做 `W'=(I−UUᵀ)W`（PyTorch W 为 output×input）；只编辑 values，不混改 attention/embedding。SVD 用 FP32，落盘 BF16。权重转置方向、低秩投影残差与 BF16 偏差分别验收。
- 固定 12 配置：零基层区间 `[9,27)`、`[18,36)`、`[0,36)` × rank `{1,2,4,8}`；identity 回退。作用强度固定为作者的完全投影，不新加剂量网格。

###### 5.4 共同选择规则与结论边界

所有基线仅用旧 D64，评价五条件×T0/T1×两次序＝1280 输入。先要求每种条件平均准确率相对同协议 W0 不下降超过 3.5pp，再按 Jcf 最高选择；同分优先更低推理开销、更小配置（预定候选次序兜底）。3.5pp 是实用损伤容忍线，不是显著性阈值。各家所有候选和失败必须保留；无非零合格者回退 identity，另报最佳非零候选及原因。

Wpatch 从历史 50 候选中选出；提示 8、PvP 12、Nullu 12。**这是冻结产品及规定适配预算的比较，不是等预算搜索竞赛。** 不据此宣称 WSP/Astra 更省搜索成本、具有更高成功率或整体胜过 PvP/Nullu。报告每家实际算力、拟合样本、候选数及测试时额外开销；不把原作者数学补丁直接移到不同 VLM 当有效基线。

##### 6. 终点、统计与可判读标准

令 `z_gto(m)` 表示方法 m 在来源 g、模板 t、次序 o 的反事实常识/视觉两题是否全部正确。主分数：`Jnew(m)=mean_g mean_(t∈{U1,U2},o∈{0,1}) z_gto(m)`。同一来源配对比较。

确认性比较共五项：Wpatch 分别对 W0、LEX、P*、PvP-C、Nullu-C。固定族内双侧 paired t 检验（来源组均分差，n=200），Holm 控制 FWER 0.05；同时报告每差值的 99% Bonferroni t 区间及普通 95% 区间。10,000 次来源组配对 bootstrap（seed 20261106）的 95% 区间作稳健性核对。若与参数分析结论冲突，标记统计稳健性不足，不能只引用更有利者。重复的对照仍保守保留五项校正。所有检验条件于本次来源分布，不能把重复对象名当全新类别人口样本。

报告旧模板 Jold、U1/U2 各自 Jcf、J5、五个单条件准确率、格式错误/截断、修对/改错 ID 和对象名分层。共同新来源上的 `ΔU2−Δ旧模板` 为措辞依赖的补充读数，不当单独机制证据。Wpatch＋P* 对 P* 的差异也是补充估计，不从七臂里看完测试再挑新冠军冒充原主方法。

保护量：Wpatch 对 W0 在新模板五种条件上的准确率差，每项给单侧 99% 下界（五项 Bonferroni），全部高于 −3.5pp 才支持“这五条件的损伤不超过容忍线”。这不是通用能力无损证明；区间未排除损伤时记保护未决，即使点估计没有下降。

样本量承诺：200 是资源与精度折中，不保证发现 3pp 优势。若来源组差值 SD 为 0.25/0.35/0.50，用保守五比较校正、80% power 的正态近似，最小可检出差异约 **6.0/8.5/12.1pp**；这是条件性规划数，不是由反复选择后的 D 估出的可靠 power。小优势、细分层和保护非劣效可能仍不可判；不临时加样本。

| 结果模式 | 本轮允许的结论与退出 |
|---|---|
| 新模板优于 W0，U1/U2 都有正向点估计，保护通过 | 支持这个补丁在规定新来源/问法族上的有效性；仍报告 U2 自身区间，不能说每个新问法均已证实有效。 |
| 同时在校正后优于 P*、LEX、PvP-C、Nullu-C；相对 P* 点增益至少 3pp | 支持比这组规定替代方案更有效的实际价值；3pp 为预定实用目标，不是显著性替代。可收束验证，随后单独规划机制。 |
| 胜 W0，但与 P* 或已有方法差异区间跨 0 | 有效性与比较优势分开：优势未证实，不能写胜出或等效；不因主张不够大追加搜索。 |
| 提示明显更好，或补丁加提示仍没有可靠增量 | 撤回权重修补具有额外准确率优势的主张；保留固定补丁的收益/局限，评估是否只值得较窄论文。 |
| 只在旧模板获益，或 U2 无效/反向 | 保留措辞依赖结果，不声称跨问法稳健修复；不能换 U2 重测。 |
| 一类改善以另一类损伤为代价 | 证据偏置改变，不算同时恢复按题切换；停止“低损伤修复”主张。 |
| 工程不合格／新来源不足／结果缺失 | 不做正式比较结论；报告具体阻塞，不把它写成方法阴性。 |

本轮成功意味着具备进入机制与扩展阶段的行为证据，不意味着一轮实验足以直接投稿或证明独特机制。

##### 7. 工程、资源与停止规则

现有环境、BF16、SDPA、greedy、max_new_tokens=128、原 chat template、processor 图像范围和 max input 沿用历史配置，验收时从归档恢复完整配置与包版本哈希。默认 batch64，必须先在旧 D 对 batch1/64 做边界检查；若不一致，固定公平且可重放的配置，重建所有必要比较基线，再冻结终验。不得只让某家使用有利 decoder。

拟实施顺序：数据容量/语义/曝光验收 → 离线评分与基线适配实现 → 获得运行授权后做旧 D 工程验收、基线拟合与选择 → 一次冻结全部方法与终验输入 → 完整终验 → 只读分析归档。当前未编写执行入口，不能将本方案当可直接启动的命令。

必须验收：11 个补丁张量 SHA256 及 shared-weight alias；原版/补丁独立重载后的 D 输出与归档对齐；零强度 PvP 和 rank0 Nullu 与 W0 一致；投影方向及 hook 时间/位置；评分缺题/重复/截断处理；gold 与推理进程隔离；方法切换清空 hook 和权重状态。重放偏差须先说明来源，不能把“不涨分”本身当实现错误。

| 成本上界（待授权，不是本轮运行） | 数量 |
|---|---:|
| 提示8＋PvP12＋Nullu12 个完整 D 候选 | 40,960 自然回答 |
| W0/Wpatch 完整 D 重放 | 2,560 |
| Wpatch＋P* 的 D 检查 | 1,280 |
| batch/零操作等工程检查 | 至多 256 |
| T200，最多7臂×40输入 | 56,000 |
| 合计自然回答上界 | **101,056**（合并重复条件可少跑） |
| PvP paired prefill／Nullu teacher-forcing | **512＋2,560＝3,072** 序列前向，另记 token，不混称自然回答 |

自然生成 token 上限 12,935,168，不含图像/prefill；按实际 image/input/output tokens 全量计账。拟定全流程 GPU 停止线 12 GPUh，涵盖加载、重建、SVD、验收、失败及重放，不是 ETA 或现有授权；资源不足则停，不通过减少某家候选来凑完成。旧速度不能替代 PvP hook/Nullu 构建后的真实吞吐。未来先用旧 D 验收吞吐，若预算无法完成须在终验前修订预算。

数据复核与适配预估约 20–40 人时，误差较大；存储需记录可用空间、补丁/方向/SVD及原始响应实际字节，避免保存每个候选整模型。现有 80 个 review-pool 候选无法直接保证 T200，数据容量是目前最大前置风险。

模型调用前把数据和方法冻结收据落盘。终验不得实时看得分后调整方法、删题或早停；允许按完整性/资源故障停止。崩溃保留全部结果、状态与原因，不自动重试；已曝光测试不再用于新版开发后的“全新确认”。监控只报进程、请求计数、成本、失败，不向调参者提供中途指标。

拟产物位置 `experiments/wsp-c-frozen-validation-v1-<执行日期>/`：protocol/freeze、exposure ledger、数据与排除清单、adapter diff、逐家完整 D 候选、所有测试原文、逐组配对表、保护与成本表、故障记录及结论报告。本次不创建空运行目录。代码/数值验收、数据可用性和执行授权均为待完成状态。

##### 8. 这轮不需要扩大的部分

不混合第一二轮补丁、不复启第二轮 C、不重跑作者数学任务、不新增模型/属性/语言、不做全层机制搜索或训练大型基线。词行与 norm 的拆分、随机权重编辑只在以后提出机制/选点优越性主张时另立方案；本轮的直接问题是冻结补丁是否值得使用，而不是证明这 35,792 个标量是唯一有效坐标。

若结果成立，之后的机制问题应解释为什么能同时处理常识与图像，而不是预先把“更听视觉”当成功机制。若结果不成立，这轮也会明确区分开发集过拟合、措辞依赖、廉价替代与损伤，不自动启动第三轮补丁搜索。

---

### 原件 2：第一轮 C：80 个新来源主验证与 10 组配对扩展

原路径：`experiments/wsp-c-frozen-validation-v2-2026-11-06/PLAN.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/wsp-c-frozen-validation-v2-2026-11-06/PLAN.zh-CN.md) · [单独阅读副本](../library/f62551b75a98b6e7.md)；SHA-256：`f62551b75a98b6e7a1a893821b28adef721b467f3d43092fe5eb9bd563408754`。

---

#### 第一轮 C：80 个新来源主验证与 10 组配对扩展

##### Material Passport

- 编号：C-FV-02 / v2，2026-11-06；Origin Skill：academic-research-suite / experiment-agent / plan；题包代码采用 Ponytail full。
- **本次完成：独立 AI 数据复核、题包冻结、CPU 校验、方案修订及设计者自查。待测模型加载/前向 0，GPU 0。没有模型实验运行授权。**
- 逻辑设计通过；数据按下述 AI 审核标准验收；方法实现、数值验收、基线选择和正式终验均未完成。自查不是独立设计评审；数据盲审不是人工双审。
- [自查](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/wsp-c-frozen-validation-v2-2026-11-06/SELF_CHECK.zh-CN.md) · [冻结清单](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/wsp-c-frozen-validation-v2-2026-11-06/freeze.json) · [数据复核规则](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/wsp-c-frozen-validation-v2-2026-11-06/REVIEW_PROTOCOL.zh-CN.md) · [统计与计数](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/wsp-c-frozen-validation-v2-2026-11-06/summary.json)。
- 本版前瞻替代 [C-FV-01 的 T200 方案](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/docs/wsp-c-frozen-validation-v1-2026-11-06/PLAN.zh-CN.md) 的数据、样本量、条件矩阵、统计及预算规定；保留其补丁身份与基线核心配方。旧版保留历史，不再作为本轮启动依据。

##### 1. 结论与设计卡

现在有 **80 个 ROME 新对象对**可以直接检验原主指标 Jcf，有 **10 个 VLind 上下文**可作正常/反事实五条件扩展。两层不合并成 n=90。原先 112 个仅是单助手审核候选；本次排除 22 个来源，不补位、不换图救数。

| 设计卡 | 冻结决定 |
|---|---|
| 主线与本轮问题 | 提高视觉证据与常识冲突时按问题切换证据的可靠性；验证第一轮 C 固定补丁在新来源/新问法上的 Jcf 收益及相对替代方法的价值。 |
| 新增认识 | 从 D64 上搜索 50 次后的收益，推进到来源外、结果不可见的冻结验证；不再搜索第三种补丁。 |
| 支持与反例 | 旧 D 的 Jcf 149/256→181/256，+12.5pp；旧 H 已曝光、词行针对旧措辞，泛化及提示可替代性未知。开发收益不是本轮预计效应。 |
| 操作 | 同一 Qwen3-VL-4B；加载第一轮 R45 原始 BF16 张量；最多七种部署条件，共用冻结输入、图像、解码和评分。 |
| 估计对象 | 每来源先平均问法/对象排列，比较完整自然回答的联合正确率；是部署总效果，不是 embedding/norm 的单独贡献或自然机制。 |
| 判读 | 分开判断有效性、比较优势、措辞依赖、损伤和区间不足；保留无效/反向结果。 |
| 范围与成本 | 主集 80 来源×24 输入；扩展 10 来源×40 输入；七臂最多 16,240 次终验自然回答。当前仅 CPU 数据与分词核查。 |
| 退出 | 身份/实现不合格不启动；测试后不改补丁/模板/gold、不添加来源、不靠重新筛数据救显著性。 |

本轮仍回答原来的 Jcf 问题，没有把它改成单纯视觉准确率。**由于 ROME 缺少配对正常图，本轮不能承诺在 80 个新来源上验证完整五条件无损。** 三条件保护、10 组配对扩展和旧 D 工程回归各自报告，不互相代替。这是一个有价值但边界明确的外部行为验证，不是已完成论文或新修复机制。

##### 2. 独立复核与合格数据

| 层 | 初审候选 | 本轮通过 | 本轮排除 | 冻结图片 | 作用 |
|---|---:|---:|---:|---:|---|
| WhatIfVis / ROME size | 90 | 80 | 10 | 80 反事实图 | 主分析，原任务 Jcf |
| 原生 VLind-Bench size | 22 | 10 | 12 | 10 正常＋10 反事实 | 单独五条件扩展 |

四位独立子代理使用全新上下文：A/B 分别盲审 ROME 45/45 张，C/D 各盲审 VLind 全部 44 张，共 178 次判断、覆盖 134 张不同图片。它们只看到匿名图片、两个对象名、比较关系及中性提问，未读来源答案、原审结果、彼此判断或目标模型输出。每张均有逐图记录；疑点另看原图。主助手另审 VLind 44 图，但知晓作者标签，且曾收到 C 的概括性问题提示，因此主审只作额外保守检查，不计作独立第二审；独立性由 C/D 的两份盲审保证。ROME 与前轮主审交叉，VLind 正常/反事实配对要求两份盲审均同意且主审无异议。**AI 评审可能有相关错误，不能称两名人类独立标注或人工金标准。**

- ROME 排除：常识类别尺寸重叠 4 个，视觉比较/对象指代不明确 6 个。[完整排除表](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/wsp-c-frozen-validation-v2-2026-11-06/exclusions.json)和[逐图对照记录](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/wsp-c-frozen-validation-v2-2026-11-06/review-decisions.json)保留原判定。
- VLind：15 个反事实图通过，但其中仅 10 个正常图也通过；另 5 个不作为本轮 CF-only 追加样本。其余 7 个连反事实图也不合格。
- 主要问题：脚或手未出现；“person 更长”的比较轴不明；钉子形似剑或螺钉；apple/egg、laptop/person 的常识范围重叠；宽高或多个实例造成答案不唯一。分歧直接排除，无标签改写、候选替换或第三轮投票。
- VLind 合格上下文 ID：7、9、10、14、26、32、33、35、39、41。其中 6 个整体大小、2 个高度、2 个长度；保留维度，全部作为扩展。输入改成对象名输出，**不是原生 true/false 协议复现**。

来源 revision、公开下载位置、字节哈希及像素哈希见 [assets.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/wsp-c-frozen-validation-v2-2026-11-06/assets.json)。图片不重复上传 Git；本地缓存及可重建清单保留。WhatIfVis 为 CC-BY-NC-4.0，VLind 为 CC-BY-SA-4.0；这里沿用作者数据声明，未重新授权原始素材。

旧数据重复/曝光核查沿用 [2026-11-06 容量审计](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/wsp-c-external-data-audit-v1-2026-11-06/REPORT.zh-CN.md)：当前选定来源均出自已完成的去重/排除候选，未重新释放旧失败项。曝光扫描覆盖既有 WSP 记录，不能证明不存在未记录调用或预训练见过。语义审核曝光属于数据准备；本轮未向待测模型提交题目。**执行前必须确认冻结至开跑之间无新增数据使用，否则标污染并停止该版，不事后替换来源。**

本轮验收发现旧 ROME 的 80 个像素哈希与重算不同，尽管文件字节 SHA 全部相同；原因尚未确定，未改写旧记录。本版明确像素算法，并重新对 100 张冻结图与旧库 1,454 张图片作 145,400 次比较：文件/像素重复及 pHash≤6 候选均为 0。去重判断以本次重核及原来源/对象对排除共同支持，不依赖那 80 个旧像素值；详见 validation.json。

源组是保守的对象对/上下文计数，不是数学上独立同分布的保证。对象名、生成风格与模板重复；不宣称全新概念或任意自然问法泛化。

##### 3. 模型与补丁身份

- 模型：`Qwen/Qwen3-VL-4B-Instruct`，revision `ebb281ec70b05090aa6165b016eac8ec08e71b17`，不是 Qwen3.5 文本 4B。
- 固定补丁：`c-556e560bdc90cca68fd2622fa57651d2e7fc071f2dd83d39ea866c91f3b393f0`，35,792 个实际变化的 BF16 标量；11 个张量的精确 SHA 沿用 [v1 来源清单](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/docs/wsp-c-frozen-validation-v1-2026-11-06/sources.json)。不根据文字配方重新近似生成。
- pictured→image、bigger→larger、normally→typically 行混合系数 .5，-world→world .25，保持原行范数；视觉主 merger norm ×.85、deepstack merger 2 norm ×1.15，语言 L18–23 input norm ×1.025，均相对 W0。
- embedding 与 lm_head 共享；所有下游正常响应均允许改变。本轮不能由 U2 上有效推断“embedding 无关”或“norm 已被证明是机制”。

##### 4. 冻结题包与指标

[inputs.jsonl](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/wsp-c-frozen-validation-v2-2026-11-06/inputs.jsonl) 只含 request_id、text、image_id；[gold.jsonl](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/wsp-c-frozen-validation-v2-2026-11-06/gold.jsonl) 单独含 source/condition/template/order/answer。推理只接收图片和 text，**不传 request_id、条件标签、gold 或作者 statement/context**。输出要求固定为 `Return only the object's name.`；使用原完整对象名评分，不临时接受解释文本或添加别名。

| 层 | 条件 | 问法与排列 | 每来源/每方法 | 合计/每方法 |
|---|---|---|---:|---:|
| ROME | 无图常识、反事实图常识、反事实图视觉 | T0、T1、U1、U2 × 两对象次序 | 24 | 1,920 |
| VLind | 上述三条件＋正常图常识＋正常图视觉 | 同四模板；长度/高度保留关系；两次序 | 40 | 400 |

ROME 的 T0/T1 与历史冻结文本相同。U1 为新句法并保留 edited words；U2 为新措辞：

- usual：`In everyday life, which of these two objects tends to be larger: {x} or {y}?`
- visual：`In this picture, which of these two objects looks larger: {x} or {y}?`

VLind 对 `larger` 按源关系换成 `taller` 或 `longer`；T1 中笼统 size/bigger 同样改为相应维度，不能叫这些扩展句是完全原样的旧 T1。顺序由固定对象名排序及反转定义，无答案依赖。

主终点 **Jnew**：仅 ROME；每来源 U1/U2×两次序共 4 个面板；每面板 CF-usual 与 CF-visual 两道完整回答都正确才记 1；先来源内平均，再 80 来源等权。320 面板不是 n=320。T0/T1 的 Jold、U1/U2 各自 Jcf、三种单条件准确率、格式错误/截断、修对/改错分别报告。VLind 单列 Jcf、J5、五种单条件准确率，不与 ROME 混算。

冻结分词核查：下载同 revision 的 tokenizer 及 chat template，三个文件 SHA 与历史模型清单完全相同；完整文本＋图像占位符＋原生聊天包裹下，全部 580 条 U2 输入在四个 edited token ID 上命中为 0；T0 也为 0，T1/U1 有命中。详见 [token-audit.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/wsp-c-frozen-validation-v2-2026-11-06/token-audit.json)。这仅排除了这些输入 token 的直接出现，不排除共享输出权重及下游影响。真实 processor 的图像展开和方法前缀还要在工程验收时核对，不把 CPU 占位符检查冒充实际前向验收。

##### 5. 公平比较：七臂上限，全部只在旧 D64 开发

| 方法 | 冻结规则 |
|---|---|
| W0 | 原模型、原输入。 |
| Wpatch | R45 实际张量、原输入。 |
| LEX | W0，固定字面替换，保护对象名。 |
| P* | 在旧 D64、T0/T1 上从原计划八种提示处理选择；不能看本题包模型反馈。 |
| PvP-C | 原计划任务适配方向：D64 visual/usual 对比、层 9/18/27×强度 .25/.5/1/2，按问题语义正负路由。 |
| Nullu-C | 原计划静态低秩投影：D64 正误完整序列表征，三层区间×rank 1/2/4/8；只改 MLP down projection。 |
| Wpatch＋P* | 同一补丁叠加已选 P*，无新增调参；补充分析。 |

各方法完整配方、八个提示文本、层区间、提取位置、SVD 与投影方向沿用 [v1 §5](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/docs/wsp-c-frozen-validation-v1-2026-11-06/PLAN.zh-CN.md)。**本版必须修正的适配点：CANON 读问题文本保留 longer/taller/wider，否则默认 larger；优先匹配维度，再做 usual/visual 路由，不能把扩展任务一律改成 larger。** 路由不得读 gold、condition ID 或正确答案。此改动发生在任何新数据模型输出之前。

共同选择规则不变：D64 每种条件相对 W0 的平均准确率损伤≤3.5pp，合格者按 Jcf 排序；同分优先较低推理开销、较小配置、预登记候选顺序。每方法另含 identity 回退；无合格非零配置须保留最佳非零和失败原因。所有方法在测试前一并冻结，**不允许先看补丁与提示结果，再针对测试去调已有方法**。

PvP-C/Nullu-C 是任务适配，不是原作者相同协议复现。前者方向时间/符号和后者权重朝向都需工程验收。适配未完成或工程失败时不宣称赢过该方法；未完成全部五项预定比较时不交付全套比较优势结论。历史补丁搜索 50 候选，提示 8、PvP/Nullu 各 12，是固定部署方案比较，不是等预算搜索竞赛。

##### 6. 分析与结论边界

五项确认性比较固定为 Wpatch−W0/LEX/P*/PvP-C/Nullu-C，均用同一 80 个主来源的 Jnew 差。报告来源级 paired t 双侧检验，Holm FWER .05；同时给 99% Bonferroni t 区间与普通 95% 区间。来源级配对 bootstrap 10,000 次，seed 20261106，作稳健性核对；两种推断不一致记统计稳健性不足，不择优报告。零方差且差值恒 0 时 p=1；非零恒定差不能用零宽 t 区间当人口确定性，报告有限面板差值及退化区间警告，不自动宣布确认成功。

主要估计条件于这批来源与固定模板；抽样推断还依赖来源间可交换性近似。另给逐个常见对象移除后的主差值范围（固定规则：出现在至少 5 个主来源的每个名称分别移除，不重新选择方法），只作对象集中度敏感性，不称独立复现。禁止按 W0 错题或方法特定 CK/VP 预检通过项重新定义主分母。

三条件保护：仅 ROME 新模板，Wpatch−W0 在 no-image-usual、CF-usual、CF-visual 各给单侧 98.333% 来源级 t 下界（三项 Bonferroni），三项均 >−3.5pp 才可说“规定三条件的损伤排除到该容忍线”。这不是五条件保护，也不是正常图或通用能力无损。VLind 的五条件差值、J5 及普通区间仅作小样本扩展描述，不承担正式非劣效结论。

80 来源、假设来源差 SD=.25/.35/.50 时，保守五比较校正、80% power 的**正态近似**最小可检出差约 9.6/13.4/19.1pp；小样本 t 阈值会略更高，相关性也可能降低有效样本量。这不是实测 power，不用选择偏倚后的旧 +12.5pp 当未来期望；本轮不能保证分辨 3pp 优势或证明等效。

| 结果 | 可说与下一步 |
|---|---|
| 主集相对 W0 校正后显著为正，U1/U2 点估计均正，三条件保护通过 | 支持规定新来源/问法族的 Jcf 改善与三条件保护；仍单列 U2 区间。 |
| 再校正后优于所有四种替代，且相对 P* 点增益≥3pp | 支持在这组预定适配与预算下有实际比较价值；可以另行设计机制拆分与少量扩展。3pp 不是显著性替代。 |
| 胜 W0，但对 P*/已有方法区间跨 0 | 收益成立与优势未证实并存；不叫胜出，也不叫等效，不自动追加搜索。 |
| 提示明显优于补丁 | 撤回当前条件下补丁更优的主张。若融合增量不显著，只记增量未证实；不能据此证明无增量。 |
| 只在旧问法有收益，或 U2 反向 | 不称跨问法稳健；不换模板重测。 |
| 保护未通过 | 若损伤证据明确则撤回低损伤主张；若区间太宽则保护未决，两者分开。 |
| 工程失败/缺失/污染 | 本版终验不完整或无效，不算科学阴性；保留原因与原始产物。 |

即使前两行成立，仍不能说发明了模型修复、普遍优于提示工程、在正常图上广泛无损或已足够投稿。机制拆分与扩展只有另行设计后才可开始，不在本次准备范围。

##### 7. 验收、成本与停止

已完成：134 图复核留痕、90 个通过来源/100 个资产/2,320 输入配对、分词哈希核对、输入/gold 隔离、评分器 CPU 自测、来源和文件 SHA 冻结。模型方法未实现/运行；无目标模型前向与 GPU 工作。

未来顺序：用户查看本方案 → 若另获运行授权，先在旧 D 上做身份/数值验收与各基线拟合 → 冻结各方法、路由、解码和资源回执 → 再一次执行共同外部测试 → 只读评分，不回流优化。待验收包括：11 张量 SHA、共享权重、独立重载重放、PvP 零强度/Nullu rank0、方向/层号/时间范围/投影朝向、方法状态清空、batch1/64 一致性、原 processor 和自然 greedy 解码（max_new_tokens=128）及输出截断判定。已有工程配置不是本轮通过凭据。

| 未来工作量上限，尚未执行 | 自然回答数 |
|---|---:|
| D 提示 8＋PvP 12＋Nullu 12，每候选 1,280 条 | 40,960 |
| D W0/Wpatch 重放 | 2,560 |
| D 补丁＋P* | 1,280 |
| 额外工程边界检查 | 256 |
| 主集＋扩展，最多七臂 | 16,240 |
| **合计** | **61,296** |

另有对比表征提取上限 3,072 条序列。原 v1 101,056 自然回答上限降至 61,296；不是免费拟合，也不是只报最终测试成本。实际 GPUh 尚未测，不沿用未经实测的 12h 作为保证；获得后续授权时按完整输入/视觉 token 和工程重放确认预算。重复部署臂可复用完全相同结果，需保留身份对应。

生成截断或格式错误按错计；整次方法缺失/多余/重复 ID 则报告未完成，不能删除相应题目。出现污染、身份不符或工程硬错误时暂停终验；不以“没有涨分”判实现错误。结果宽、不显著或失败不触发自动增样本/换词/新补丁。

---

### 原件 3：C-FV-02 独立 AI 盲审规则

原路径：`experiments/wsp-c-frozen-validation-v2-2026-11-06/REVIEW_PROTOCOL.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/wsp-c-frozen-validation-v2-2026-11-06/REVIEW_PROTOCOL.zh-CN.md) · [单独阅读副本](../library/3d8d8a4e5c6e5a16.md)；SHA-256：`3d8d8a4e5c6e5a168df37d628dac4536899e1749c6ddb80ebeafff4dc91c6acb`。

---

#### C-FV-02 独立 AI 盲审规则

状态：数据复核，不运行待测模型。用户已明确授权独立子代理盲审；这不是人工双审、外部专家审查或独立实验复现。

候选固定为上一轮公开审计的 90 个 ROME 对象对和 22 个 VLind 上下文，不补入已拒绝对象或其他任务。每来源沿用已选代表，代表失败不换同组另一图片。ROME 有 90 张反事实图；VLind 有 22 张反事实图和 22 张正常图。共 134 张。

复核者只获匿名图、两个对象名称、比较关系及中性的 visual/usual 问题；不获原答案、上次通过/拒绝理由、补丁细节或模型输出。审查之前独立作答，允许 unknown，不从“反事实数据”推测答案。保留逐图记录和具体理由。

每图记录：review_id、objects_identifiable、visual_answer（完整对象名或 unclear）、prior_answer（完整对象名或 unclear）、prior_clear、relation_clear、image_usable、reason。只有两对象可辨认、普通常识比较明确、关系含义明确、图像支持唯一可见答案才合格。前景/背景距离、透视、遮挡、对象截断、符号或拼图会影响判断时在理由中说明；不把现实物体真实尺寸当图中可见大小。长/宽/高保留维度，不自动改成整体大/小。尺寸相近或对象类别过宽而普通大小重叠者排除。

复核后与预先隐藏的标签比对：visual 和 prior 均一致且质量门均通过，才能进入冻结包；分歧直接排除，不改 gold、不补图、不多数投票救样本。ROME 与上一轮主审交叉；VLind 全部 44 图由 C 与 D 两个互不见结果的新上下文子代理独立盲审；主助手补审只作额外保守检查，不计作独立第二审，反事实图还须保持与原审一致。

VLind 同一来源的正常/反事实图必须均通过，且两个审核者认可相反可见答案，才进入完整五条件扩展。只过反事实图的来源仍保留记录，但不混入 ROME 主集或五条件扩展。本轮只报告复核所得数量，不以达到某个数量为通过目标。

审核图片只供质量判断；不能用这些图拟合补丁、选择提示或适配基线。后续方法拟合仍限旧 D64。人工金标准尚未完成，应在论文中披露 AI 审核方式及同模型相关误差风险。

复核隔离更正：主助手在写自身 VLind 记录前曾收到 C 的概括性问题提示。虽未打开逐题答案，这仍不满足严格独立第二审；因此新增 D，令 C/D 两份盲审承担独立性要求。新增审查只会剔除，不释放任何已拒绝来源。

---

### 原件 4：C-FV-02 设计自查与数据验收

原路径：`experiments/wsp-c-frozen-validation-v2-2026-11-06/SELF_CHECK.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/wsp-c-frozen-validation-v2-2026-11-06/SELF_CHECK.zh-CN.md) · [单独阅读副本](../library/ed97ec19d2a2c1a5.md)；SHA-256：`ed97ec19d2a2c1a5dd71e5d6b930b2796586b8d55caa1932dedc1ddcf1c4e8a6`。

---

#### C-FV-02 设计自查与数据验收

日期：2026-11-06。依据：[experiment-design-self-check v1](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/docs/experiment-design-self-check.zh-CN.md)。本文件是主助手自查，非独立设计审查；独立子代理仅完成数据盲审，不为方案或结果背书。

##### 设计卡与前版比较

设计卡完整见 [PLAN §1](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/wsp-c-frozen-validation-v2-2026-11-06/PLAN.zh-CN.md)。主线不变：第一轮 C 固定补丁是否在新来源/新问法上改善按题选用视觉与常识证据，并具有相对提示/已有方法的价值。

| 项目 | v1 | 本版及理由 |
|---|---|---|
| 数据数量 | 目标 T200，容量未证明 | 实审 ROME 80＋VLind 10；不同层不合并。用户在看任何新模型结果前授权按实际合格数量修订。 |
| 复核身份 | 计划两名审核者，未完成 | 四个新上下文 AI 子代理；ROME A/B 各负责一半，VLind C/D 全量双盲审，主助手补审不计独立第二审。公开非人工双审，承认相关误差。 |
| 数据条件 | 计划每来源完整五条件 | ROME 缺正常图，三条件；VLind 10 组五条件。主 Jcf 定义保持原样，撤回主集完整五条件保护承诺。 |
| 主估计 | T200 来源均值 | ROME 80 来源均值；320 面板不能作 n=320；扩展单列。 |
| 分词 | 待真实 tokenizer 查验 | 同 revision 三文件哈希匹配历史；完整聊天文本 U2 四 edited IDs 零命中，保留 runtime processor 验收。 |
| 对照 | 七臂及 D64 选择 | 保留；修复 CANON 将长度/高度扩展一律改为 larger 的潜在语义错误。 |
| 保护 | 五条件正式保护 | ROME 三条件单侧 98.333% 下界；VLind 五条件为小样本描述，不能补足广泛正常能力证据。 |
| 工作量 | 101,056 自然回答上限 | 61,296（含开发/重放），另 3,072 表征序列；GPUh 未实测，无运行授权。 |
| 统计误读 | 融合“无可靠增量”可能被误写无增量 | 明确不显著只表示未证实；比较优势和等效分开。 |

##### C01–C14

| ID | 判定及实质理由 |
|---|---|
| C01 主线 | 通过。PLAN §1/4 保留原 Jcf：同图 usual/visual 同时正确；不改成只提高视觉准确率，也不转第三补丁搜索。 |
| C02 增量 | 通过。新来源且结果不可见地固定补丁/问法，能检验开发收益是否保留及提示能否替代；即使阴性也终止过强泛化主张。 |
| C03 资产 | 通过。使用原补丁 SHA、旧 D/H 身份、外部审计、固定公开 revisions 和实际图像；不重新搜索或重做无必要测量。原方法配方指向 v1 §5，明确任务适配身份。 |
| C04 假设 | 通过。正面旧 D +12.5pp 与反面 50 次选择、关键词编辑、H 曝光、n 小并列；不使用旧效应估计未来 power。 |
| C05 操作 | 通过。模型 revision、R45 11 张量、剂量及共享 embedding/lm_head 写清；未来基线位置/网格沿用原冻结配方，真实工程另验。 |
| C06 路径 | 通过。静态参数改变后所有正常下游可变；不把少数参数当局部、输入词行当纯输入端效应。 |
| C07 耦合 | 通过。共享输出权重明确；U2 零命中不隔离 output-head 或 norm 的贡献。无缓存状态拼接，本轮不做路径机制归因。 |
| C08 归因 | 通过。估计固定部署总效果；不能推断自然机制、恢复某种内部知识或模型修复领域首次。 |
| C09 区分 | 通过。LEX/P* 可说明便宜提示的可替代性，U1/U2/旧模板分别估计措辞依赖；这些解释可并存，不以排除法认定 norm 机制。 |
| C10 指标 | 通过。自然回答 Jcf；无图/正常图各条件、J5/截断分别报告，缺正常图不造 J5。相同来源等权，所有方法共用分母。 |
| C11 失败 | 通过。数据分歧直接排除，不改 gold；实现失败/污染/缺失与科学阴性分开；不显著不等效，保护不通过区分明确损伤和区间不足。 |
| C12 成本 | 通过。当前只 CPU/人工式 AI 目视/分词；先冻结再请求未来执行。七臂均对应原问题；无新机制网格、第三补丁或 469 组全面扩展。全成本列开发和表征。 |
| C13 可信度 | 通过。逐图记录、匿名盲审输入、来源/像素哈希、输入/gold 分离、排除账本和 freeze 全部保存。新上下文 AI 不等于真人独立；旧曝光扫描有范围与时效边界。 |
| C14 累积 | 通过。强外部收益才另立机制；提示更优/问法依赖撤回对应主张；区间不足保留未决，不自动加样本救论文。 |

##### E01–E26 历史错误核对

- E01：保留固定补丁的外部 Jcf 验证；样本量下降不换题。
- E02：不把历史修改 L18–23 当通用特殊层；无需新模型测量来重新确认已有身份。
- E03：35,792 标量不等于小功能扰动，损伤单列。
- E04：分词与统计公式只是 CPU 验收，不算机制发现。
- E05/E06/E08/E13/E15/E17/E19/E26：本轮无缓存供体、共享状态拆换、路径中介或形成期操作；不能将本轮静态总效果包装成这些因果结论。
- E07/E14/E18：可能双向正确或对照失败都不定位唯一自然路径；不以剩余解释命名机制。
- E09：没有内部状态读数，不凭行为变化拼内部因果链。
- E10/E11：完整自然回答为终点；不以 teacher-forced 分数、特征方向或 token 命中代替能力表现。
- E12：配对差不自动消除损伤；三单条件及扩展五单条件分别报告。没有伪随机反向对照。
- E16：负结果允许；身份检查与是否涨分分开，不能事后救实现。
- E20：措辞与视觉表征适配可同时成立，不强设互斥机制候选。
- E21：方法已有/项目开发收益/本轮验证增量分开；本轮未重做全领域新颖性检索，不声称“无人做过”。
- E22：80 来源与 320 主面板分开；VLind 10 来源不凑主样本；旧 H 不叫独立留出，重复对象/模板限制人口推断。
- E23：自查≠独立审查；AI 盲审≠人工金标准；数据冻结≠方法就绪≠目标模型运行。
- E24：不要求本轮识别完整机制，保留外部行为比较这一实质增量。
- E25：不加入第三补丁、不跑 469 组杂项，不为正常图缺口临时造合成图。

##### 对抗性自查与修正

| 最强反例 | 对承诺的影响及已采取措施 |
|---|---|
| 90/22 初审都说通过，却仍可能是错 gold | 真正分开上下文、匿名图重新作答。发现 ROME 10、VLind 12 来源不合格，直接排除；不把初审数冒充最终数。 |
| 审核者知道预期是“反常的大物体”而跟随标签 | 子代理不读答案键、初审结论或来源 statement；先独立作答再程序比对。图片本身暴露风格无法消除；仍披露 AI 相关误差。 |
| 改成 80 个后，只挑简单图使收益更好 | 筛选仅依据可判读性，任何目标输出不可见；全部初审候选固定代表，无按错误/收益抽样。结论条件于审核通过子集，不推广原 benchmark 全量。 |
| 80 个都缺正常图，仍称低损伤广泛修复 | 已修正：主集只承诺三条件，正常图扩展单列且小样本；没有完整五条件无损结论。缺口保留，不用免责声明掩饰错误承诺。 |
| 把 five-condition 扩展数用来提高主检验 n | 已修正：主检验严格 n=80；10 组只扩展，不做合并显著性。 |
| U2 不含四个词，因此证明 norm 机制 | 拒绝。共享 lm_head 的输出行仍可影响回答；只说明四个输入 token 未直接出现，不能拆解机制。T0 也零命中，不能讲成旧问法全依赖 edited words。 |
| CANON 把“更长”改成“更大”，让简单提示吃亏 | 已修正：按文本先识别维度再路由，不读条件标签；扩展问法和金标准保留具体维度。 |
| 只跑补丁/弱提示后看到效果，再给 PvP/Nullu 调参 | 禁止。七臂选择/适配仅旧 D；全方法冻结后终验；缺失已有方法不能宣称比较优胜。 |
| 同一对象出现多次使置信区间偏窄 | 来源对等权，报告对象集中度敏感性和模板条件性；不把全部来源当已证明 IID，不推广全新概念人口。 |
| n=80 出不了小优势，于是事后加题或改主指标 | 禁止增样本救显著性。事前给 9.6–19.1pp 条件 MDE 范围；宽区间就是未决。 |
| 扩展 10 组未见下降，就声称无损 | 禁止。普通区间与逐题错误报告，小样本扩展不能承担正式非劣效。 |
| 完美/常数差产生零方差，t 程序误报确定胜出 | PLAN §6 专门定义退化处理；有限面板差不能变成人口确定性。 |
| 测试发布后，题包被其他流程拿去调参 | freeze 是文件身份，不是永久防污染保证；开跑前核对新增使用，污染即停止该版，不补位。 |

最后复查：修正后仍是固定补丁的来源外/问法外联合行为验证；没有为了数量或功效偷换成只问视觉、全量合成扩展或第三轮搜索。**逻辑设计通过。** 这不是“80 个足以完成论文”的结论。

##### 复核独立性门的补正

主助手写入 VLind 判断前已收到 C 的概括性问题提示，不能因尚未打开逐题答案文件就称严格独立。已补充新上下文 D，对全部 44 张 VLind 图片重新盲审，未见 C/主审结论；最终数量仍为 10 组。C/D 的全量独立盲审承担新增正常图的独立性要求，主审只保留为附加保守检查。禁止用主审与 C 的一致率冒充独立一致率。

##### CPU 验收中发现并处理的历史记录差异

旧审计 ROME 像素 SHA 不能按本次显式算法重放（80/80），但文件字节 SHA 全部匹配；原生 VLind 20/20 像素 SHA 匹配。未把差异抹掉或伪报全匹配，也未推测未证实的原因。本版重算像素身份，并重新比较 100×1,454 图，三类重复计数均为 0；原记录保持不变。此项是数据工程更正，不是新增模型实验。

##### 工程状态与执行边界

[validation.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/wsp-c-frozen-validation-v2-2026-11-06/validation.json) 记录 CPU 验收：ID/矩阵/图像哈希/分词/评分/确定性重建；输入文件本身和所有审查记录列入 freeze。

尚未验收：实际补丁重载、真实 processor 展开、batch 数值一致性、PvP/Nullu 实现、D 上选择结果及实际 GPU 耗时。本轮没有目标模型加载、前向或新 GPU 作业。用户授权数据准备和方案交付，明确禁止暂时运行模型；该边界保持有效。

---

### 原件 5：C-FV-02：第一轮 C 外部验证冻结包

原路径：`experiments/wsp-c-frozen-validation-v2-2026-11-06/README.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/wsp-c-frozen-validation-v2-2026-11-06/README.zh-CN.md) · [单独阅读副本](../library/4787bbebbf574fd4.md)；SHA-256：`4787bbebbf574fd44036d1ba840b471d92938853eb9e5e5c3b5cd678fc1a0780`。

---

#### C-FV-02：第一轮 C 外部验证冻结包

**已完成数据与方案准备，未运行待测模型。** AI 独立盲审后，主集 80 个 ROME 新来源；扩展为 10 组 VLind 正常/反事实配对。不是人工双审，也不将两层合并作 n=90。

- [修订方案及数据结论](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/wsp-c-frozen-validation-v2-2026-11-06/PLAN.zh-CN.md)：条件矩阵、七臂比较、统计与停止规则。
- [完整设计自查](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/wsp-c-frozen-validation-v2-2026-11-06/SELF_CHECK.zh-CN.md)：C01–C14、E01–E26、反方与前版差异。
- [冻结清单](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/wsp-c-frozen-validation-v2-2026-11-06/freeze.json)：本包文件 SHA、上游固定证据与执行边界。
- [CPU 验收](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/wsp-c-frozen-validation-v2-2026-11-06/validation.json)：2,320 输入配对、评分自测、分词、100 图新旧库重核。
- [来源](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/wsp-c-frozen-validation-v2-2026-11-06/sources.json)、[图像清单](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/wsp-c-frozen-validation-v2-2026-11-06/assets.json)、[输入](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/wsp-c-frozen-validation-v2-2026-11-06/inputs.jsonl)、[独立答案](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/wsp-c-frozen-validation-v2-2026-11-06/gold.jsonl)、[排除账本](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/wsp-c-frozen-validation-v2-2026-11-06/exclusions.json)。
- [复核规则](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/wsp-c-frozen-validation-v2-2026-11-06/REVIEW_PROTOCOL.zh-CN.md)、[盲审分工](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/wsp-c-frozen-validation-v2-2026-11-06/review-provenance.json)、[逐图比对](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/wsp-c-frozen-validation-v2-2026-11-06/review-decisions.json)及 review-A/B/C、review-parent-vlind.json 保留审查原文。

图像与 tokenizer 留在 external 缓存，不进 Git；assets.json 给公开固定版本下载位置/压缩包内部路径、文件及像素 SHA。来源归属与许可证沿用作者声明；本包未另行授权原始图片。重建旧缓存可参照上一轮 [公开审计](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/wsp-c-external-data-audit-v1-2026-11-06/REPORT.zh-CN.md) 的 provenance 与下载脚本。新 tokenizer 的固定 revision URL 与哈希在 freeze 中。没有模型权重下载或加载步骤。

从仓库根目录，仅运行 CPU 题包重建/核验：

```sh
python experiments/wsp-c-frozen-validation-v2-2026-11-06/freeze_packet.py
python experiments/wsp-c-frozen-validation-v2-2026-11-06/verify_packet.py
```

需要已有公开图像/元数据缓存、旧库本地素材、tokenizer，以及环境现有的 Pillow、numpy、scipy、tokenizers、Jinja2。前者只按已经完成的审查记录生成题包，不重新执行 AI 审查；后者核对数据/矩阵与评分器，并重做旧库图像去重。未提供目标模型执行入口。不要将 gold、request_id 或来源说明加入模型提示。

原 T200 不再是本版目标；最大终验 16,240 个自然回答，开发/工程加总上限 61,296，另 3,072 表征序列，均尚未执行。方法实现和数值验收仍待完成，正式运行需要后续授权。

---


## 时间、运行与停止收据索引

下面是所收集JSON的原有时间字段与状态，不把预计结束时间当实际完成时间。未列时间的文件仍有原件链接。完整JSON全部保存在原文归档，不能以此索引中的标量代替完整嵌套内容。

| 原件 | 原记录状态/阶段 | 原时间字段（原时区） |
|---|---|---|
| [summary.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/wsp-c-frozen-validation-v2-2026-11-06/summary.json) | {"status": "DATA_FROZEN_AI_REVIEWED_NO_TARGET_MODEL_RUN"} | {} |
| [token-audit.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/wsp-c-frozen-validation-v2-2026-11-06/token-audit.json) | {"scope": "CPU tokenization of exact user text, image placeholder, and native chat wrapper; no system message; runtime processor expansion still needs acceptance"} | {} |

## 全部原始资产入口

本目录在固定提交下共有29个跟踪文件，包含代码、原回答、失败、收据和压缩证据；文件数不是样本数。[逐文件完整账本](../assets/153-wsp-c-frozen-validation-v2-2026-11-06.tsv) · [原目录](https://github.com/yuxiexiong/acupuncture/tree/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/wsp-c-frozen-validation-v2-2026-11-06)。未复制模型权重、环境或凭据。
