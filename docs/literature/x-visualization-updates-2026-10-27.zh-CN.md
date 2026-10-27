# 可视化工具分享与讨论复查（2026-10-27）

核查截止：2026-10-27 17:38，北京时间。本轮只读重访 lyra 的工具截图帖、演示视频帖、仓库发布回复及相关分支，核查分享所指向的代码和网页。未安装工具、未点击生成、未运行模型或重跑作者测试。X 动态排序与折叠限制了覆盖，不将可见评论称为全量导出。

**值得注意的增量有四类：Lyra 的 attention-head／token 视图、mfstuff 的逐 token 调试器、Neuralese 的可复现工作台，以及一个可直接在网页选择 Qwen 神经元的 HF Space。它们展示的测量量并不相同。**

## 1. 与刚才 recipe 核查相比，哪些才是新增

| 工具 | 本轮固定版本 | 新旧关系 |
|---|---|---|
| `lyramakesmusic/neuron-explorer` | `e566e83e3f9fe00f85438231a788f90e83e2af43` | 与刚才 recipe 核查相同；相对 10/26 本地可视化审查所用 `ddb144e…`，attention-head 等功能是实质代码增量。本轮补测量定义，不称为刚才之后再次更新 |
| `makefunstuff/qwen-neurons` | `2a780d8a2fdc3735bac13987da93148a8683102c` | 与刚才相同；新增讲清 debugger、地图、热图与连线含义 |
| `0thernes/neuralese` | `0134e4bbc3fa0cbe3a174b46ef5ad200b4ca3699` | 上轮 `853f544…` 为 v6；本次 README／release 为 v13.0.1，有实质更新 |
| `fa-0/altered_models` | `9a90aa7ad0bca3d5a95cd6fe8bbd42add85a2001` | 昨天评论新分享的 HF Space；本轮首次核对源码与实际 UI |

此前的 recipe 和搜索方法不重复展开，见[配方增量报告](x-recipe-updates-2026-10-27.zh-CN.md)。

## 2. Lyra：从神经元地图扩展到注意力头与具体 token

[演示原帖](https://x.com/_lyraaaa_/status/2114211024962498831)、[仓库发布回复](https://x.com/_lyraaaa_/status/2114211027986624718)、[固定版本](https://github.com/lyramakesmusic/neuron-explorer/tree/e566e83e3f9fe00f85438231a788f90e83e2af43)。

| 新功能 | 实际表示什么 | 不能直接解释成什么 |
|---|---|---|
| attention heads 进入 3D 地图 | 每层面板内，每条横线代表一个头，可选中、高亮并关联神经元 | 横线的空间位置是索引布局，不是功能或语义距离 |
| q/k/v/o 四角色连线 | 分别查看查询、匹配、搬运及输出所对应的权重投影联系 | 尚不是特定输入下已验证的因果路径 |
| 当前 token 的头写入强度 | 头经输出投影写入 residual 的向量范数，用本层参考最大值缩放着色 | 不是 attention 概率，也不是对答案正确性的贡献 |
| token→token 视图 | 普通全注意力显示 softmax；线性 Gated DeltaNet 显示有符号 effective weights，并按绝对值和归一化 | 后者含负数，不能当普通概率矩阵 |
| `attn_drive` | 在指定 token 处，将目标 MLP 通道的 `SiLU(gate) × up` 局部线性化，分解头和源 token 的驱动 | 不是实际关闭某个头之后测得的变化；代码固定该 token 的 norm 尺度 |

直接代码：[头的地图布局](https://github.com/lyramakesmusic/neuron-explorer/blob/e566e83e3f9fe00f85438231a788f90e83e2af43/explorer/static/map3d.js#L101-L161)、[写入强度](https://github.com/lyramakesmusic/neuron-explorer/blob/e566e83e3f9fe00f85438231a788f90e83e2af43/explorer/runtime.py#L140-L147)、[两类 token 权重](https://github.com/lyramakesmusic/neuron-explorer/blob/e566e83e3f9fe00f85438231a788f90e83e2af43/explorer/runtime.py#L198-L251)、[局部线性化](https://github.com/lyramakesmusic/neuron-explorer/blob/e566e83e3f9fe00f85438231a788f90e83e2af43/explorer/runtime.py#L275-L308)。

相较早期只看某个通道的词和回答，新版本能够显示某个头在指定 token 的读取权重、写入 residual 的强度，以及与下游神经元的权重候选联系。代码定义已经可查，但本轮没有独立检验 effective-weight 重建误差或局部线性近似精度。

另有 agent 聊天历史持久化和 Codex 后端选项；不再只是 Claude CLI 接口。原有 MLP `writes` 布局、权重 top-24 connections、fires、logit/steer lens 和回答 embeddings 不算此次重新新增的地图原理。[聊天历史](https://github.com/lyramakesmusic/neuron-explorer/blob/e566e83e3f9fe00f85438231a788f90e83e2af43/explorer/server.py#L1266-L1304)、[Codex 后端](https://github.com/lyramakesmusic/neuron-explorer/blob/e566e83e3f9fe00f85438231a788f90e83e2af43/explorer/server.py#L1622-L1643)

## 3. mfstuff：把可视化做成逐 token 调试器

[X 分享](https://x.com/mfstuff_/status/2114871438461251693)、[固定 README](https://github.com/makefunstuff/qwen-neurons/blob/2a780d8a2fdc3735bac13987da93148a8683102c/README.md)。

本轮最值得补充的是 **Debugger**：每层显示当前 token 的六个最强通道，可设断点、固定关注通道、看变化曲线、调剂量或覆盖激活；暂停时重跑当前序列，再查看下一 token 概率。仓库有实现和演示，本轮没有启动该工具，因此不保证所有按钮在本机环境运行正常。[调试器说明](https://github.com/makefunstuff/qwen-neurons/blob/2a780d8a2fdc3735bac13987da93148a8683102c/README.md#L170-L180)

同一工具有三种容易混淆的视觉元素：

- **地图位置与颜色。** 横向按层、层内按神经元编号排成网格，不是语义聚类。默认颜色是 down-projection 列范数，也可显示缓存激活极值；不能把静态截图颜色称为当前模型的思考内容。[位置](https://github.com/makefunstuff/qwen-neurons/blob/2a780d8a2fdc3735bac13987da93148a8683102c/qwen_neurons/static/explorer.js#L26-L33)、[颜色](https://github.com/makefunstuff/qwen-neurons/blob/2a780d8a2fdc3735bac13987da93148a8683102c/qwen_neurons/weights.py#L279-L293)
- **橙／蓝连线。** 来自源通道输出方向与目标 gate/up 读取方向的投影评分，再将两种评分平均。它们是作者所称 virtual weights，未包含特定输入下完整非线性状态；不是直接测得的兴奋／抑制因果边。[连接公式](https://github.com/makefunstuff/qwen-neurons/blob/2a780d8a2fdc3735bac13987da93148a8683102c/qwen_neurons/lens.py#L102-L116)
- **逐 token 热图。** fires 面板确实可以显示输入文本中的激活，也能回看 C4 样本中的最高／最低激活片段。但是颜色按各段文本除首 token 后的最大绝对激活归一化，跨文本不能只凭深浅比较强弱。作者缓存范围为一个 C4 validation shard 的前 4096 篇、各 64 token。[前端归一化](https://github.com/makefunstuff/qwen-neurons/blob/2a780d8a2fdc3735bac13987da93148a8683102c/qwen_neurons/static/explorer.js#L279-L282)、[语料范围](https://github.com/makefunstuff/qwen-neurons/blob/2a780d8a2fdc3735bac13987da93148a8683102c/README.md#L126-L135)

其 head 分数主要来自输出／value 投影的权重信息；所查代码没有 Lyra 新版那套完整 q/k/v/o 角色和具体 token effective-weight 重建。不能因为都叫 explorer，就认为展示的是同一种测量。

## 4. Neuralese：更新为更完整的实验工作台，但仍有模型边界

这是上轮评论已提过的工具，本轮检查发现版本明显前进。GitHub 实时分支返回 v13.0.1 的提交 `0134e4…`，时间为 10/27 14:51:03 北京时间；相对上轮固定版本，compare 显示 ahead 108、behind 0、193 个文件变化。搜索网页缓存仍可能显示 v7，本记录以分支 SHA 为准。

公开的新内容包括：

- 权重 SHA-256、实验 manifest、编辑重放、运行记录差异、状态导入导出。
- node-level ACDC-style 搜索、causal scrubbing-lite、带控制任务的 probes、head 消融统计；README 明确没有 edge-level pruning。
- 自带语料导入、原版／修改版计分板、Notebook 和 HTML 报告。
- 对 stored author results、stored+live、live consistency checks 作区别，并提示模型改变后旧结果可能失效。
- 新模型 HUB 及多平台 release 安装包；发布制品存在不等于本轮验证了安装和运行。

**白盒操作仍是 TinyStories 1M／3M／8M。** 新增 GPT-2／DistilGPT-2 属于生成模式，ONNX 嵌入、OCR、语音和图像模型也不等于接入任意大语言模型内部。没有 Qwen3.5-4B 白盒支持证据。作者测试通过的数量属于其记录，本轮未重跑。

来源：[固定 README](https://github.com/0thernes/neuralese/blob/0134e4bbc3fa0cbe3a174b46ef5ad200b4ca3699/README.md)、[模型列表](https://github.com/0thernes/neuralese/blob/0134e4bbc3fa0cbe3a174b46ef5ad200b4ca3699/zoo.js)、[版本比较](https://github.com/0thernes/neuralese/compare/853f544560be75982e8750418017a4f1b43cdcb5...0134e4bbc3fa0cbe3a174b46ef5ad200b4ca3699)、[v13.0.1 发布页](https://github.com/0thernes/neuralese/releases/tag/v13.0.1)。部署分支 `6b7578fa24c8c61204d7667ddf613231ebc1b93e` 的提交信息指向上述源码版本。

## 5. fa-0 的在线 Qwen 工具：选择界面不等于激活图

[评论分享](https://x.com/Farjad_Ahmed/status/2114730114055348300)的短链接，本轮浏览器已确认跳转至 [Qwen3.5 Architecture Explorer](https://huggingface.co/spaces/fa-0/altered_models)。实际页面已加载，可见层结构、剂量、预设和 Generate 按钮；HF 当时显示 Running on Zero。没有点击生成。

源码实际加载 `Qwen/Qwen3.5-4B` BF16，并用 GPU 生成函数和动态 hook 做干预，因此不只是静态教学网页。但是：

1. 96×96 MLP 网格的颜色是**选中状态、方向和剂量**，没有读取当前 token 的自然激活。它是可点击的 MLP 通道坐标选择器，不是实时脑活动图。
2. 结构图统一画 Attention／GQA，未分别表现混合注意力各模块的真实运行关系。
3. 所谓 Hostility score 只是英文词表命中占比，不是经过验证的行为评判。
4. 干预尺度取自**层输入的 pre-hook**，每次 forward 重算；与原帖 leaving-layer residual，以及 Lyra 固定参考尺度的实现都需区分，不能当作严格相同的复现。
5. 页面中“self-concept neurons”和超过某个剂量即损坏等说明是作者界面文案，未见对应完整验证制品。

来源：[固定 app.py](https://huggingface.co/spaces/fa-0/altered_models/blob/9a90aa7ad0bca3d5a95cd6fe8bbd42add85a2001/app.py)、[HF 元数据](https://huggingface.co/api/spaces/fa-0/altered_models)。平台 Running 只证明当时服务状态；真实生成是否正确本轮未测。

## 6. 评论区新补到的讨论：哪些已有实现，哪些还只是想法

| 讨论 | 本轮核到的内容 | 证据级别 |
|---|---|---|
| 自动遍历候选 | Adrian Endres 10/27 06:51 称用本地 Qwen 基线，根据提示自动遍历神经元直到得到工作版本 | [新评论](https://x.com/AdrianEndres4/status/2114852456383295699)未附源码、停止规则和失败统计；不能与 mfstuff 已有实现及失败记录等量齐观 |
| 空间布局优于列表 | Monkey 分享另一种层间点云和正负连线；lyra 回复强调位置、形状对其使用体验的意义 | 10/26 的旧讨论，本轮新补齐。[两张图](https://x.com/Orwelian84/status/2114458434074710401)、[作者回复](https://x.com/_lyraaaa_/status/2114483024779981294)。图上可见 not causal wiring 标识；本分支未见可核验源码／完整测量定义 |
| VR 里穿行神经元 | 评论者提议做成 VR 体验 | [提议](https://x.com/rishpoddar/status/2114361770060231163)是想法，未见交付工具；不是本轮新发布软件 |
| 更小／更大／不同模型 | 仓库发布帖有人问小 Qwen 和跨架构推广，截图帖有人问更大模型 | [小模型](https://x.com/tealsea90/status/2114349127068950730)、[跨模型](https://x.com/EddieOakwood/status/2114440179394236838)、[更大模型](https://x.com/confidencechaos/status/2114793405238673877)。本轮所查相关分支未得到完整通用适配证明 |

逐 token 显示激活移动的建议此前已经收录，本轮不重新算新发现。上表区分了新评论、旧评论新补录与已有实现；未将视觉吸引力或支持接口本身当成机制验证。

## 7. 运行成本与证据定义

Lyra 的公开缓存浏览无需先重跑完整扫描；真实 fires、attention、steering 需要加载模型。其批量扫描环境与日常浏览不是同一要求。mfstuff 将静态权重地图、词索引和连接分析放在独立 CPU 进程，仍需要权重文件；首次索引约 11 分钟、70 MB 是作者报告，不是本机保证。[Lyra 使用说明](https://github.com/lyramakesmusic/neuron-explorer/blob/e566e83e3f9fe00f85438231a788f90e83e2af43/README.md#L13-L40)、[mfstuff CPU 索引说明](https://github.com/makefunstuff/qwen-neurons/blob/2a780d8a2fdc3735bac13987da93148a8683102c/README.md#L133-L135)

本轮确认的进展是具体测量与操作界面变丰富：权重地图、自然激活、token 读取／写入、局部归因和干预结果可以被放在同一工作台。但这些仍是不同证据，不能统称为已经看见完整的思考回路。
