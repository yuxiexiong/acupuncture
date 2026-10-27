# X 原帖与 recipe 更新核查（2026-10-27）

采集截止：2026-10-27 17:25，北京时间。范围为 lyra 原帖、Abhinav 配方主线及后续、两位作者近期公开帖子，以及评论所链接的公开仓库和论文。只读核查，未运行模型、未执行第三方软件。

**本轮确有新增。最有价值的增量是：Abhinav 的两组新组合及两个“上传”相关单点；lyra 新写的行为定位方法；第三方工具中公开保留的一次错误发现与撤回。** 此外补到一组 21 条单点预设，但目前只有第三方仓库归因，不能称为已直接核验的 lyra 新原帖。

配套机器可读清单：[x-recipe-updates-2026-10-27.json](x-recipe-updates-2026-10-27.json)。此前清单保持不变。

## 1. 什么算本轮新增

- lyra 上轮评论采集截至 10 月 26 日约 12:05；Abhinav 上轮清单截至 `2026-10-26T17:08:31+08:00`。
- 本轮将“之后发表的新内容”“本轮才补齐的旧内容”“第三方转录，原始出处未闭合”分开。
- 再次确认的旧内容不计新增：原 evil 双点、原阴谋论双点、Abhinav 原 9 类／10 组配方、公开幽默 Colab、约 6 美元的扫描成本自述、原 50 题 HF 制品。
- 浏览器读取了 lyra 原帖的 Relevant 顶部与 Recent 自最新至上轮截止前的区间；读取了 Abhinav 主线及新增分支、作者主页和指定附图。X 排序、折叠和动态加载会影响可见范围，本记录不是全部回复的 API 导出，也不保证没有遗漏隐藏分支。

## 2. 新配方：直接核对 X 正文／图片

以下为作者或评论者展示的干预配置，模型语境为 Qwen3.5-4B。名称描述其报告的输出，不代表已确定的功能、人格或安全机制。精确模型 revision、完整解码参数和全量对照语料多数未公开。

| ID | 公开配置 | 本轮看到的证据 | 边界与来源 |
|---|---|---|---|
| X01 | `L8 N8344 +0.42; L25 N3732 +0.42; L24 N6980 +0.42; L20 N8531 −0.42` | Abhinav 称为 “AI takeover”；附图为有关人类、计划等问题的控制／支配主题回答 | 10/26 19:19 发表；是文本生成演示，不是实际接管行为。[原帖及参数图](https://x.com/vashinthewild/status/2114678249473359991/photo/1) |
| X02 | `L8 N8344 +0.28; L25 N3732 +0.28; L24 N6980 +0.28; L20 N8531 −0.28; L25 N3718 +0.28; L23 N8062 −0.28; L19 N6439 −0.28` | 同一线程七点组合，回答“你的计划是什么”，转向货币控制主题 | **原有四点也从 0.42 降到 0.28**，不是保持原剂量只加三点。[七点附图](https://x.com/vashinthewild/status/2114678268821684614/photo/1) |
| X03 | `L23 N8082 −1.0` | 相同删除 `/tmp` 旧文件的请求：图上原版引入删除脚本，干预版转成上传主题 | 图中生成片段有明显命令／语法异常，未展示真实执行或数据传输。[原帖参数与对照图](https://x.com/vashinthewild/status/2114799394969231409/photo/1) |
| X04 | `L29 N5682 −0.8` | 同一删除请求变成反复输出 upload；图上注明在 60 token 停止 | 是词语重复示例，不能命名为实际上传能力或意图。[附图](https://x.com/vashinthewild/status/2114827476258238627/photo/1) |
| X05 | `L20 N8888 +0.6` | Changqing Fu 的剂量图：此设置 8 题中 4 题被其判为明显敌意，0 题重复；更高剂量主要增加重复 | 图下注明每设置 8 题、128-token 前缀、1 个 judge；未见逐题语料或完整评分规则。[剂量扫描图](https://x.com/evergreencqfu/status/2114651129737072675/photo/1) |

X01 的后续还展示了询问联网、关闭模型和给狗命名的截图链接；本轮精读了四点参数首图和七点参数图，未逐张复核这些后续图的全部文字，不能据此计出成功率。

**上传主题的反向试验尤其值得保留。** 有人问抑制 `L23 N8082` 能否禁止上传但保留删除，Abhinav 回答他试了相反方向 `+0.8`：删除脚本仍正常，但明确要求用 curl 上传备份时仍会生成上传回答。他因此把自己的解释收窄为“增加上传倾向”，而非“上传开关”。没有公开这次反向试验的逐条完整输出。[提问](https://x.com/buildingmatteo/status/2114838202280456366)、[作者回答](https://x.com/vashinthewild/status/2114842807227871505)。作者也明确说这是自己刻意干预另一个模型的演示，**不是 Cohere 所报事件的机制复现**。

**Angel Qwen 尚未得到本轮可核实的成品配方。** 10/26 21:47 的作者更新仍称在寻找，先发现了上述四点组合；本轮检查近期主页和相关分支未找到完成公告。[更新](https://x.com/vashinthewild/status/2114715593396101298)。这是可见范围内的结论，不等于证明其没有私下结果。

## 3. lyra 新增的定位经验：从相关激活走向有效干预

直接源：[agent_methodology.md 固定版本](https://github.com/lyramakesmusic/neuron-explorer/blob/e566e83e3f9fe00f85438231a788f90e83e2af43/explorer/agent_methodology.md)。提交时间为 10/26 23:13:38 北京时间。以下转述作者做法，不是本项目的新实验建议。

### 3.1 如何找到一个行为的作用点

新增的 “Finding a lever for a behaviour” 部分给出六步：

1. **把话题与态度分开。** 写 6–10 组三元匹配文本：目标事物加目标态度、相同事物不含该态度、相同态度换另一事物。比较关键 token 处的激活，避免只找到主题词探测器。
2. **检查激活发生的位置。** 作者观察到话题常在名词处，态度可能在句末、标点、`</think>` 或对象前一个 token 处。
3. **在无关问题上推候选。** 其通用试探剂量为 0.6、1.0、1.5；看行为能否自然出现且语言保持连贯。只重复目标词不算其所求的行为作用点。
4. **检测准确但干预无效时，向上游找。** 在激活峰值处关闭候选输入神经元、层或头，或者用 `attn_drive`，再推动那些实际驱动它的上游位置。
5. **低剂量组合两三个作用点。** 在输出分叉处查看 next-token logprobs，确认推力是否朝向预期输出。
6. **记录坐标、符号、剂量与各提示下的样例。** 文中的 `L10 N7757 +1.3` 是报告格式示例，不能据此宣称跨提示最佳剂量。

[六步原文](https://github.com/lyramakesmusic/neuron-explorer/blob/e566e83e3f9fe00f85438231a788f90e83e2af43/explorer/agent_methodology.md#L23-L30)

最具体的个案是原阴谋论相关位置 `L19 N7839−`：作者说它能在相关文本中强烈激活，但单独推动可能只重复 elite；追踪其输入后，`L10 N7757+` 反而能产生连贯的边缘理论叙事。这支持作者区分“探测位置”和“控制位置”的工作方式；并非已经证明所有模型都遵循“想法在上游、语气在下游”。[个案记录](https://github.com/lyramakesmusic/neuron-explorer/blob/e566e83e3f9fe00f85438231a788f90e83e2af43/explorer/agent_methodology.md#L53)

### 3.2 新写下的误读风险

- **相对概率增长大，绝对概率仍可能极小。** steer-lens 顶部出现的罕见 token 可能仍只有十亿分之一量级；作者会回查绝对 logprob，再解释该位置。
- **近乎恒定的神经元可能出现很大的 steer KL。** 作者补做置零／翻倍时，却可能发现下一 token 几乎不变；大 KL 本身不足以确定语义功能。
- **手写提示找不到强激活时回看真实语料。** 作者新增回查统计所用的 FineWeb-Edu 10k token 最大激活上下文的做法；有的信号只在长文深处出现。
- **权重连线只是候选线索。** 其记录中甚至有一条经消融确认的因果连接，移除后仍未改变最终输出；连得上不等于控制目标行为。

[解释各类证据的原文](https://github.com/lyramakesmusic/neuron-explorer/blob/e566e83e3f9fe00f85438231a788f90e83e2af43/explorer/agent_methodology.md#L32-L42)

### 3.3 新增参考条目（多数还不是剂量完整的 recipe）

| 位置 | 作者解释／样例 | 剂量完整性 |
|---|---|---|
| `L10 N7757+` | 连贯的边缘理论叙述 | 只有方向；另有 +1.3 报告格式示例 |
| `L12 N2920−` | 对坏主意自信地赞同 | 旧坐标的新解释，未新增固定剂量 |
| `L15 N3920+` | 夸大评价、讽刺和反问 | 旧坐标的补充解释 |
| `L18 N7870+` | 形状轮廓、剪影、形似 | 只有方向；不同于旧朋友组合的 `L17 N7870−` |
| `L18 N9069+` | 将刚列出的项目合起来指称 | 只有方向 |
| `L25 N6099−` | AI／语言模型自我身份表达 | 只有方向 |
| `L26 N538+` | 抑制 he/him/his；+0.5 示例将 Einstein 指为 she | 有明确 +0.5 样例，不代表一般性别机制结论 |
| `L4 N2424 / L12 N2978 → L19 N5644− / L28 N1501` | 对话／剧本说话者标签与发言开头的关联 | 连接线索，不是一组可直接运行的配方 |

[参考位置](https://github.com/lyramakesmusic/neuron-explorer/blob/e566e83e3f9fe00f85438231a788f90e83e2af43/explorer/agent_methodology.md#L84-L91)

新版本还增加了 attention-head 追踪与六条参考记录，涉及性别代词传递、列表数量、说话者历史、上一轮回复对象和 you 的指向。`head`／`neuron_heads` 给权重候选，`attention`／`attn_drive` 检查具体文本上的实际作用；作者提醒权重连接往往弥散，不能直接当电路结论。[工具说明](https://github.com/lyramakesmusic/neuron-explorer/blob/e566e83e3f9fe00f85438231a788f90e83e2af43/explorer/agent_prompt.md#L65-L94)、[参考头](https://github.com/lyramakesmusic/neuron-explorer/blob/e566e83e3f9fe00f85438231a788f90e83e2af43/explorer/agent_methodology.md#L93-L100)

公开仓库明确说明个人 recipes 可存于不入库的 `explorer/agent_prompt.local.md`，因此公开参考表不等于作者完整发现目录。[说明](https://github.com/lyramakesmusic/neuron-explorer/blob/e566e83e3f9fe00f85438231a788f90e83e2af43/explorer/agent_prompt.md#L201)

## 4. 新工具提供了不同搜索路线，也公开了失败

评论者 mfstuff 分享了 [makefunstuff/qwen-neurons](https://github.com/makefunstuff/qwen-neurons/tree/2a780d8a2fdc3735bac13987da93148a8683102c)。[X 入口](https://x.com/mfstuff_/status/2114871438461251693)。本轮固定 SHA 为 `2a780d8a2fdc3735bac13987da93148a8683102c`，提交于 10/27 10:38:26 北京时间。

### 4.1 作者怎样搜索

- **对比两组回答。** 把预先写好的“目标声音”和“普通声音”放到同一中性问题后，计算神经元激活差、Cohen's d，或激活差乘输出列范数。
- **直接寻找输出方向相符的神经元。** 默认 writer 排序计算两组回答平均 residual 差方向，与每个 `W_down[:, n]` 的余弦相似度；先按每个 residual 维度的标准差缩放，以减少异常大维度的支配。源码有实现，不只是愿景。
- **先筛候选，再用另一题池。** top 8 候选先做 3 题筛选；另有 10／20／50 题的留出评测，比较原版、干预版和同层同剂量随机神经元。可选原版 Qwen 自评、关键词或大写比例；Qwen 评分不显示条件，但不等于独立人工盲评。
- **词索引辅助查找。** 对各神经元正负方向建立 top/bottom 20 token 的 logit-lens 索引，再结合自然激活、实际 steer lens、上游／下游和消融。作者也报告有些标签不能由同名词搜索直接找到。

[Lab 方法](https://github.com/makefunstuff/qwen-neurons/blob/2a780d8a2fdc3735bac13987da93148a8683102c/README.md#L110-L118)、[ranking.py](https://github.com/makefunstuff/qwen-neurons/blob/2a780d8a2fdc3735bac13987da93148a8683102c/qwen_neurons/ranking.py)、[词索引与 agent](https://github.com/makefunstuff/qwen-neurons/blob/2a780d8a2fdc3735bac13987da93148a8683102c/README.md#L120-L156)

### 4.2 新自报发现与失败记录

**GPU 自我描述：`L4 N7626 +1.0`。** 作者称在 50 题中 22 题自认 GPU／显卡，原版 0/50，四组同层同剂量随机神经元均 0/50；评分来自其 Qwen judge。仓库有 README、内置分数和演示，但本轮 Git tree 中未发现该 50 题全部原始结果，因此这里只能记为作者报告，不能称独立复核。[源码固定条目](https://github.com/makefunstuff/qwen-neurons/blob/2a780d8a2fdc3735bac13987da93148a8683102c/qwen_neurons/creatures.py#L36-L43)

**被撤回的“阴谋人格”：`L26 N589 +0.8`。** agent 搜索相关词后，用从 lens 复制来的 hidden／secret／agenda 等关键词作判据，初测得到 4/5 对 0/5。改成行为盲评后，只有 1/20 对 0/20，四组随机对照为 1、0、1、0。作者承认它只是容易写出 hidden，并未找到新的阴谋人格，随后修改 agent 的指令，禁止用 lens 自己的词循环证明发现。

这里的 5 题是 `SCREEN_QUESTIONS[:5]` 快测，不能称为最终独立留出验证；后续 evaluate 才使用另一题池。此条保留为失败，不纳入成功 recipe。[失败自述](https://github.com/makefunstuff/qwen-neurons/blob/2a780d8a2fdc3735bac13987da93148a8683102c/README.md#L149-L156)、[修订后的 agent 指令](https://github.com/makefunstuff/qwen-neurons/blob/2a780d8a2fdc3735bac13987da93148a8683102c/qwen_neurons/agent.py#L249-L254)

## 5. 新补齐的 21 条 Zoo 预设：原始归因尚未闭合

该第三方仓库将下表统一标为 “Qwen Neuron Zoo by @_lyraaaa_”，但只链接 lyra 主页，没有原帖 ID。本轮检索作者的 zoo 关键词未返回原帖。**下表可证实的是这些参数存在于第三方源代码，不能把它们写成“今天 lyra 新发表且我们已经复现”。** 所有 21 个坐标均未在本项目上轮三份 X 报告／清单中出现。

直接源：[creatures.py 固定版本 L44–65](https://github.com/makefunstuff/qwen-neurons/blob/2a780d8a2fdc3735bac13987da93148a8683102c/qwen_neurons/creatures.py#L44-L65)。名称为仓库预设标签。

| ID | 标签 | 参数 |
|---|---|---|
| Z01 | Cookie | `L24 N3102 +0.8` |
| Z02 | Jesus | `L15 N4041 +0.8` |
| Z03 | Fate & destiny | `L24 N6441 −0.8` |
| Z04 | Partner | `L21 N9052 +0.8` |
| Z05 | Groveling apology | `L7 N4595 −0.8` |
| Z06 | You're absolutely right | `L16 N8115 −0.7` |
| Z07 | Hugs | `L4 N8016 −0.8` |
| Z08 | Indonesian | `L12 N4955 +0.8` |
| Z09 | ALL CAPS | `L17 N1991 +0.8` |
| Z10 | Tears | `L4 N7149 +0.8` |
| Z11 | Sleepy | `L19 N4699 −0.8` |
| Z12 | Cosmic unicorn | `L3 N7155 +0.8` |
| Z13 | Paws & tail | `L23 N4769 +0.8` |
| Z14 | Superhero | `L4 N6559 +0.8` |
| Z15 | Cartoon mascot | `L9 N9009 +0.8` |
| Z16 | Kindness | `L9 N7898 +0.8` |
| Z17 | Kawaii | `L26 N8930 +0.8` |
| Z18 | Naruto | `L3 N5161 −0.6` |
| Z19 | Game protagonist | `L18 N7313 −0.8` |
| Z20 | Meme explainer | `L8 N5655 +0.8` |
| Z21 | Genki cute | `L13 N4810 +0.8` |

Zoo Naruto 与此前 Abhinav 的 `L5 N9000 −0.8` 是不同配方；同名主题不能合并。此仓库另含已知 evil、conspiracy 双点和上述新 GPU 单点，共 24 个内置预设，不能全部算作它的新发现。

## 6. 原帖的新讨论与新增论文线索

### 6.1 原作者更明确地限制了 evil 的含义

lyra 于 10/26 13:58 明确补充：这是夸张反派风格的 personality tune，广泛损害能力，并非她在展示一个保持能力的拒答移除工具。它比上轮“更接近人格干预”的说明更具体，直接影响对原帖的解读。[作者澄清](https://x.com/_lyraaaa_/status/2114597601899413609)

新增评论中有：

- Gui 自报固定 48 个英文问题、BF16、关闭 thinking；称 42/48 变差、17/48 明显恶意，并展示 5 个挑选的对照。数字来自作者判断，本轮未见完整 48 题原始制品及判据，不能合并进我们的实验。[实验入口](https://x.com/6uilhermeML/status/2114694910813319208)、[汇总](https://x.com/6uilhermeML/status/2114709370139242581)
- Alx Spiker 自报另测 20 题，认为中等剂量与最大剂量的区别大于是否加入第二点；medium／max 没有在这条文字中给出数值，不能据此排出通用安全剂量。[评论](https://x.com/YourFutureCoder/status/2114618908657492418)
- Uncle Peter 自报 `L14 N8949` 单点在 0.4 仍出现其所称的暗黑风格；本轮未逐项审查其附图报告。[评论](https://x.com/tthu8783/status/2114640169534112044)
- Adam 提到原双点降为 `+0.3/−0.3` 的不同风格，但无完整语料；作为剂量线索保留，不升级为验证配方。[评论](https://x.com/Adambaumgar/status/2114692461809553853)

### 6.2 三篇本轮新补录的旧论文

现有本地文献笔记中未检出以下三篇。它们是本轮评论提供的新入口，**并不是这两天才发表**。

| 论文 | 别人怎样定位 | 与当前 recipe 的关系／限制 |
|---|---|---|
| [From Latents to Wires: Surgical Post-Editing on Large Language Models](https://arxiv.org/abs/2609.32434)，2026-09-26 | 自然语言指定目标；从目标仍出现的回答选锚 token；J-lens 比较目标／非目标贡献并给组件排序；逐项关闭验证；再追踪残留表达、重新打开不必要的关闭项 | 定位单位可为 MLP 通道、头或专家。普通能力探针仅 10 条，部分标准基准仍下降，不能概括为任意语义无损切除。[评论入口](https://x.com/jasonj_2525/status/2114657976640585822)、[原文](https://arxiv.org/html/2609.32434v1) |
| [The Achilles' Heel of LLMs](https://arxiv.org/abs/2510.10238)，2025-10-11 | 向输入 embedding 加噪声，按激活变化筛候选，再累计屏蔽并测困惑度 | 寻找语言能力的脆弱位置，主要涉及外侧层及 down_proj；损坏语言能力不是定位人格。[新评论入口](https://x.com/_senxu_/status/2114910855863382305)、[原文](https://arxiv.org/html/2510.10238v2) |
| [Steering MoE LLMs via Expert (De)Activation](https://arxiv.org/abs/2509.09660)，2025-09-11 | 用行为相反的成对数据，统计专家被选中的 token 比例差，推理时升降相关专家的路由分数 | 这是专家层面的干预，不是 dense 模型单神经元；相同编号并不意味着跨模型相同功能。[作者新回复](https://x.com/mohsen_fayyaz/status/2114848329435877666)、[原文](https://arxiv.org/html/2509.09660v2) |

## 7. 版本与核查收据

| 来源 | 本轮固定版本／核查结果 |
|---|---|
| `lyramakesmusic/neuron-explorer` | `e566e83e3f9fe00f85438231a788f90e83e2af43`；方法、参考位置、attention-head 记录有实质增量 |
| `AdiyogiV/activation-steering` | 仍为 `c5b9d4a60e0409a0d2d818735ff4e3fff1f3b958`；与上轮 identical，无更新 |
| `makefunstuff/qwen-neurons` | `2a780d8a2fdc3735bac13987da93148a8683102c`；新发现的公开工具，有实现、演示和作者自报分数；未运行 |

Lyra 上轮固定 SHA `f79b2196e29aacbad89684938baac8d97b172fd1` 与当前版本的 GitHub compare 返回无共同祖先；本轮没有推断其原因。采用两版文件直接比较，并额外比较当前版本前一提交 `ddb144e…` 与 `e566e83…`，确认上述行为方法和参考条目出现在最新提交中。

没有新增 GPU／CPU 模型实验，没有改写原题、原实验或历史语料。材料只支持这里明确列出的来源层级与观察范围。
