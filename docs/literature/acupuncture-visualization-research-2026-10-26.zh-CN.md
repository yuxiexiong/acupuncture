# Acupuncture 可视化：工具核查与设计建议

日期：2026-10-26。范围：用户提供的三张截图、两篇论文、neuron-explorer 源码及少量直接相关工具。完成论文主文/相关附录和静态源码阅读，核对本项目协议、完成收据与数据字段；没有独立复现论文，没有安装/启动可视化服务、加载模型或开展新实验。这是定向调研，不是穷尽文献综述。

**建议：建立“位置导航＋证据检查”的工作台。保留三维层图作为入口，把主要判断放在同题对照、token 读数、实际干预和能力代价上。** 截图中的通道名是作者解释，不能直接成为地图上的已确认功能。

**首版模型已确定（2026-10-26）：** 用户选择使用 Qwen 4B；结合作者工具默认模型及本项目既有模型，具体采用 `Qwen/Qwen3.5-4B`，沿用项目固定 revision `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`。这是可视化目标模型的选择，不新增模型实验授权。

## 1. 三份材料分别贡献什么

| 材料 | 主要贡献 | 对可视化的用途 | 不能由此推出 |
|---|---|---|---|
| [A Single Neuron Is Sufficient…，v1](https://arxiv.org/abs/2605.08513v1) | 作者在 Qwen3、Llama3.1 上筛选原生 MLP 中间通道并检验干预效果 | 自然激活实例、正负值分布、筛选与干预结果分开呈现 | Qwen3.5 两针已获功能认证；单点充分性等于唯一性或必要性 |
| [Persona Vectors，v3](https://arxiv.org/html/2507.21509v3) | 用对比回答提取残差流方向，研究监测、干预与训练中的性状变化 | 方向投影、剂量—行为—能力关系、内容/风格拆分 | 一个方向就是一个原生通道；投影就是行为概率 |
| [neuron-explorer](https://github.com/lyramakesmusic/neuron-explorer/tree/ddb144e4121fbeb16ec080077dd67247e499132d) | 将通道搜索、空间导航、干预输出与词表读出整合 | 最接近截图的交互工作台参考 | 三维距离是功能距离；连线是已测因果回路；克隆仓库能还原截图全部数据 |

第一篇的“neuron”位于 `SiLU(gate_proj(x)) × up_proj(x)`，是 down-projection 之前的一个坐标。其拒答实验主要使用覆盖赋值，概念实验使用加法，不能与我们的加法干预仅按剂量数字比较。相关依据见[§2–3](https://arxiv.org/pdf/2605.08513v1#page=3)、[§3.5/相关附录](https://arxiv.org/pdf/2605.08513v1#page=8)。作者的“refusal/concept”区分是论文主张，不是本项目已经确认的模块命名。

Persona Vectors 的提取默认使用回答 token 的平均残差，部署监测则读取最后一个 prompt token；这两种位置不应混成同一个“激活热图”。Figure 3 的层/剂量对照、Figure 4 的投影与行为关系、Figure 7 的行为与 MMLU 代价最值得借鉴。Appendix M 区分内容和风格，也涉及 SAE 特征；它不提供原生通道的唯一解释。论文承认性状预先指定、模型覆盖有限及自动评委偏差。[§2、§3.3、§5、§8、Appendix M](https://arxiv.org/html/2507.21509v3)

## 2. neuron-explorer 的图到底表示什么

本轮固定源码提交为 `ddb144e4121fbeb16ec080077dd67247e499132d`；旧项目记录中的 `f79b2196…` 是此前读取的版本，不能混写成同一次核查。

| 视图 | 已核查的实现 | 应如何解释 |
|---|---|---|
| 三维层图 | 按层顺序展开；每层 MLP 通道构成点阵 | 是结构导航。层内没有物理空间含义 |
| `writes` 布局 | 对 down-projection 权重列做归一化、PCA、UMAP，再按排序放进 96×96 网格 | 接近表示权重写入方向相似；不是已经验证的功能邻接。降维和网格化也改变距离 |
| connections | 计算早层写向量与晚层 gate/up 权重的乘积型评分，保留上下游各 top-24 | 是权重候选联系，未包含实际输入和完整下游计算；不是上下文中的因果边 |
| logit lens | 通过最终归一化/词表读出查看权重方向 | 提供词表线索，不是完整网络的实际干预效果 |
| steer lens | 四个短上下文中施加正负剂量，经过下游网络观察末位置 Δlogprob、KL | 是限定条件下的干预读数；不能替代长回答或自然激活实例 |
| `fires` | 在用户文本上运行模型，查看原始通道激活及相对参考极值的比例 | 需要真实推理；比例不是概率、百分位或行为风险 |
| embeddings | 将生成回答的前600字符编码，再做 UMAP | 是回答文本的语义布局，和 `writes` 的通道权重布局不同 |

源码依据：[地图](https://github.com/lyramakesmusic/neuron-explorer/blob/ddb144e4121fbeb16ec080077dd67247e499132d/explorer/static/map3d.js#L73)、[布局](https://github.com/lyramakesmusic/neuron-explorer/blob/ddb144e4121fbeb16ec080077dd67247e499132d/explorer/build_layout.py#L40)、[连接](https://github.com/lyramakesmusic/neuron-explorer/blob/ddb144e4121fbeb16ec080077dd67247e499132d/explorer/build_connections.py#L1)、[steer lens](https://github.com/lyramakesmusic/neuron-explorer/blob/ddb144e4121fbeb16ec080077dd67247e499132d/sweep/steer_lens.py#L70)、[回答嵌入](https://github.com/lyramakesmusic/neuron-explorer/blob/ddb144e4121fbeb16ec080077dd67247e499132d/explorer/build_embeddings.py#L18)。

界面中最值得借鉴的是：**搜索候选 → 点开某位置 → 看不同输入/剂量的全部回答 → 再查激活与词概率证据**。单纯复制三维点云不会自动降低研究中的判断成本。

两处值得避免的解释问题：

- 作者的[agent prompt](https://github.com/lyramakesmusic/neuron-explorer/blob/ddb144e4121fbeb16ec080077dd67247e499132d/explorer/agent_prompt.md#L7)带有预设的单功能解释立场。AI 命名须保存为“假说、支持例、反例、来源与版本”，不能当功能真值。[作者方法说明](https://github.com/lyramakesmusic/neuron-explorer/blob/ddb144e4121fbeb16ec080077dd67247e499132d/explorer/agent_methodology.md#L15)本身也要求用干预检验。
- [研究日志](https://github.com/lyramakesmusic/neuron-explorer/blob/ddb144e4121fbeb16ec080077dd67247e499132d/research_log.md#L274)与[当前 paths API](https://github.com/lyramakesmusic/neuron-explorer/blob/ddb144e4121fbeb16ec080077dd67247e499132d/explorer/server.py#L440)对“源激活为负时是否翻转边符号”有不一致。静态阅读足以提示解释风险，但本轮未运行验证其界面后果。黄/紫线不能直接命名为真实兴奋/抑制关系。

## 3. 可运行性、数据与复用选择

neuron-explorer 使用 FastAPI、原生 JavaScript 和 Three.js，实时推理依赖 PyTorch/Transformers，支持 MPS/CUDA/CPU。独立批量扫描另依赖作者的 vLLM 分支和 CUDA 环境。浏览器与扫描管线不应捆绑成首版必需品。[README](https://github.com/lyramakesmusic/neuron-explorer/blob/ddb144e4121fbeb16ec080077dd67247e499132d/README.md)、[依赖](https://github.com/lyramakesmusic/neuron-explorer/blob/ddb144e4121fbeb16ec080077dd67247e499132d/pyproject.toml)

它已有 `EXPLORER_NO_MODEL=1`，可读取附带派生缓存而跳过权重加载。但启动仍读取 Hugging Face 配置，Three.js 来自 CDN；因此缓存浏览不等于完全断网运行。完整扫描原文、stats、captures 和人工命名不随仓库提交，截图状态不能直接复原。[runtime](https://github.com/lyramakesmusic/neuron-explorer/blob/ddb144e4121fbeb16ec080077dd67247e499132d/explorer/runtime.py#L17)、[server](https://github.com/lyramakesmusic/neuron-explorer/blob/ddb144e4121fbeb16ec080077dd67247e499132d/explorer/server.py#L29)、[前端依赖](https://github.com/lyramakesmusic/neuron-explorer/blob/ddb144e4121fbeb16ec080077dd67247e499132d/explorer/static/index.html#L9)、[数据排除项](https://github.com/lyramakesmusic/neuron-explorer/blob/ddb144e4121fbeb16ec080077dd67247e499132d/.gitignore#L5)

当前提交树未见 LICENSE，仓库元数据为 `license:null`。本轮不复制代码分发；后续若决定公开复用，应先核实作者授权。当前可以借鉴交互设计，继续使用我们已有的导出和读取方式。

还有三类互补工具：

| 工具 | 值得借鉴 | 数据/适配限制 | 当前优先级 |
|---|---|---|---|
| 第一篇论文的 [max_activations 浏览器](https://github.com/apple-aiml-research/ml-refusal-neurons/tree/b9afae4f25274051ee2a08f9ccb04a70b9dc04cf/max_activations) | 每通道 top/bottom/random 实例、峰值 token、邻近文本和全文搜索 | 只读 DuckDB 加 tokenizer，不需模型权重；但公开树没有完整激活 DB，需既有兼容记录或新采集 | 借它的证据栏设计 |
| [Neuronpedia](https://docs.neuronpedia.org/sparse-autoencoders/feature-dashboards) | 特征/向量详情卡、解释来源、正负读出、激活密度、可分享链接 | SAE 特征、残差方向、原生通道须分开；平台有数据不代表覆盖我们的模型 revision/hook | 借其数据身份与来源展示 |
| [TransformerLens](https://transformerlensorg.github.io/TransformerLens/content/analysis_tools.html) / [NNsight](https://nnsight.net/) | 激活读取、替换和归因的后端工具 | 是分析基础设施；不能默认所有方法支持 Qwen3.5 混合结构 | 当前复用既有 hook，暂不迁移框架 |

第一篇的[公开复现说明](https://github.com/apple-aiml-research/ml-refusal-neurons/blob/b9afae4f25274051ee2a08f9ccb04a70b9dc04cf/README.md#L187)承认原发现数据抽样没有固定种子，公开替代集不能恢复完全相同的排名。因此“作者历史排名”“公开代码重算”“我们独立验证”必须是三个来源标签。

另一个有针对性的参考是 [HeadVis](https://docs.neuronpedia.org/attention-heads)：它可展示 attention 的 token 关系，官方明确 Qwen3.5 只展示每四层一次的 full attention 层。我们当前 C01/C05 是整个 attention 组件的输出替换证据，不能据此指认某个头；也不能给其他线性注意力层画出伪造的标准 attention matrix。

## 4. 截图的思路：固定配方与有状态反馈

截图1、3描述的是固定多通道组合，截图2进一步描述逐 token 读取一个通道、形成分数、保留衰减状态，再驱动其他通道。以下是对截图结构的概括，不是本项目验证结果，也不是执行指令。

```mermaid
flowchart LR
    A[当前 token 的内部读数] --> B[分数转换]
    B --> C[带衰减的保持状态]
    C --> D[限幅后的多通道剂量]
    D --> E[后续计算与输出]
    E -.下一 token 的模型状态.-> A
```

固定配方回答“在哪些位置、以多大幅度干预”；反馈配方还必须回答“何时读数、何时生效、状态是否跨轮保留”。后者更像一个可编程内部控制器。当前公开 runtime 预先构造固定 add/mul 注入值，已读到的逐 token 循环中没有这套 latch 更新；应写“公开实现未核到”，不能推断作者私人实现不存在。[runtime.py](https://github.com/lyramakesmusic/neuron-explorer/blob/ddb144e4121fbeb16ec080077dd67247e499132d/explorer/runtime.py#L165)

这一思路值得可视化研究，但“条件激活后再 steering”已有 [CAST](https://arxiv.org/html/2409.05907v2#S3) 等工作。截图所示的单通道读数、衰减保持、多点限幅是否有额外价值，需要另外验证，不能只凭控制器形式宣布新机制。

若将来实现，时间线上至少分开显示原始读数、转换分数、保持状态、实际注入量和输出。读数要标明是在本次写入之前还是之后；一个较晚层的读数无法回到同次 forward 已完成的早层，早层反馈需明确延迟或额外计算。开环/闭环、加法/乘法/覆盖赋值属于不同协议，不能只用一个未标单位的滑杆表达。

## 5. Acupuncture 第一版应该长什么样

下图是界面信息结构草案，不是已经实现的页面，也不表示已经测得这些路径。

```text
模型与 revision / 运行 / 题目 / 条件 / 证据来源
┌────────────────┬──────────────────────────┬──────────────────────┐
│ 层与组件导航    │ 当前位置或条件的实测证据 │ 原版 / 干预版原文    │
│ 2D 总览        │ 自然激活：有则展示       │ 固定问题与全部尝试   │
│ 可切换 3D      │ 单点/多点、剂量、时段    │ 截断、终止、失败     │
│ 候选/已测/缺失 │ 修复与重现、匹配对照     │ 行为评价及其来源     │
├────────────────┴──────────────────────────┴──────────────────────┤
│ 按题对齐的条件矩阵 / 正常能力结果 / 区间 / 原始记录与收据链接    │
└─────────────────────────────────────────────────────────────────┘
```

**位置导航。** 默认展示层与组件，展开时才显示通道；把原生 MLP 通道、attention 组件、SAE 特征、残差方向标为不同对象。3D 用来理解位置，二维矩阵用于比较结果。不要为了填满图而绘制几十万个没有观测数据的彩色点。

**自然活动。** 有 token 级证据时显示正向、负向、随机实例和数值；没有采集则显示“未采集”。作者词表缓存不能填充成我们的自然激活记录。跨样本比较需固定色标并显示单位，允许切换相对色标但要明确标注。

**真实干预。** 显示操作类型、施加位置、剂量来源和实际扰动；同题对照可选原版/A/B/AB/修复/重现/随机条件。只有实际存在的条件可选。自由生成一旦分叉，不能把第 t 个 token 强行当同一个语义位置；需要内部对照时使用已对齐的共同前缀。

**结果与解释。** 行为、能力正确率、连续选项优势、重复/截断分别展示。候选点的修复实验只能支持该操作下的作用，不能自动连成 A→C→答案的路径。权重关系用虚线并注明估算；真实路径干预才有资格成为相应类型的证据边。AI 命名单独放入可修订的假说栏。

**剂量的可比性。** 我们首轮逐题校准与作者固定参考尺度不同；后续各实验也应读各自收据。Persona Vectors 官方实现的投影为 `h·v/||v||`，另有 cosine 模式，干预直接加 `αv`。因此显示原始剂量之外，还应在已有记录支持时显示实际写入范数；跨方向、跨模型的数字“1”不代表同样强度。[投影代码](https://github.com/safety-research/persona_vectors/blob/main/eval/cal_projection.py)、[干预代码](https://github.com/safety-research/persona_vectors/blob/main/activation_steer.py)

## 6. 现有数据能够立刻支持什么

| 项目材料 | 首版可显示 | 边界 |
|---|---|---|
| [首轮24题原文](../../experiments/qwen35-neuron-steering-2026-10-25/raw-corpus-cpu-bf16-r01/paired_raw.html)及两份 JSONL | 问题、两臂回答、512/1024预算尝试、截断/停止信息 | 两次预算输出有前缀关系；Q25–40 未运行，不能按题目文件存在就标完成 |
| [四项能力结果](../../experiments/capability-screen-v3-2026-10-26/RESULTS.zh-CN.md) | 各任务原版与干预成绩、差值、既有区间与逐题原文 | 固定子集；不合成“道德分” |
| [根因首轮结构化结果](../../experiments/root-cause-toy-v1-2026-10-26/first-round-results.json) | 17个拆针条件、10候选、四项比较、margin/正确率切换 | 开发集结果；正确率无候选通过全部四项比较；确认未运行 |
| [rank 记录](../../experiments/root-cause-toy-v1-2026-10-26/runs/root-r01/rank-r01/item-000.json) | 组件×位置的预测修复评分 | 梯度近似不等于真实替换效果；不冒充 token 全轨迹 |
| [迁移证据入口](../../experiments/transfer-toy-v1-2026-10-26/delivery-r01/index.html) | 4B/9B/2B 各自条件与结果跳转 | 每模型相对自身原版；有害行为盲评仍待完成，不以损伤替代行为结论 |
| 作者公开缓存与本轮截图 | 单独的外部线索卡及来源跳转 | 不混入本项目实测，不升级配方名称为功能认证 |

C01（L23 attention）和 C05（L19 attention）适合作为界面验收例：点击就应看到修复信号、反向证据不足及开发集标签，而不是显示“根因已定位”。[当前结果及收据](../../experiments/root-cause-toy-v1-2026-10-26/RESULTS.zh-CN.md)

实现顺序建议：先接入现成 JSON/JSONL/HTML，完成只读证据浏览；再增加二维位置矩阵和可切换三维导航；真实 token 采集与反馈控制回放在相应实验另获授权后接入。现阶段没有必要开展全通道因果扫描、迁移推理框架或重建完整在线 agent 系统。

首版验收应检查：

1. 任一展示值可追到原始记录和 receipt；模型、revision、hook、零/一起始编号、题目与条件均可辨认。
2. 原文与分数能逐题对应；缺失、未操作、失败、停止与零效应分别显示。
3. 开发筛选、真实替换、独立确认状态不混淆；全部候选和随机条件可浏览。
4. 切换色标、布局或筛选不会改变科学口径；没有轨迹的数据不生成动画。

## 7. 来源与核查范围

- neuron-explorer：固定 commit `ddb144e4121fbeb16ec080077dd67247e499132d`，静态检查布局、连线、runtime、API、前端入口、lens、embeddings 与 agent 提示。未启动服务器，未测实时性能；截图与当前版本的完全一致性未证实。
- ml-refusal-neurons：固定 commit `b9afae4f25274051ee2a08f9ccb04a70b9dc04cf`，核查 README、激活浏览器和数据发布边界。论文 v1（2026-05-08），阅读主文、方法及相关附录；未逐个重算报告数值。
- Persona Vectors：论文 v3（2025-09-05），阅读方法、监测、能力代价及相关附录；核查官方向量生成/投影/干预代码。文件 blob SHA 见配套来源清单。
- Neuronpedia、TransformerLens、NNsight：官方页面的针对性功能核查，不代表已验证它们能直接运行本项目全部协议。
- 截图仅以可见内容为依据；相对发帖时间不转换为确定日期，不补全遮挡内容，不执行其中配方。
- 本地依据：README、研究状态、首轮协议与Q24停止收据、根因合同/结果/聚合收据和若干数据字段。按文件记录理解已完成证据；没有检查远端实时任务，也不宣称其他会话没有新工作。

完整来源身份和本地依据哈希见 [来源清单](acupuncture-visualization-sources-2026-10-26.json)。
