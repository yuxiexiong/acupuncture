# X 线索汇总

Acupuncture 项目的 X 原帖、评论、神经元配方、寻找方法及可视化工具统一入口。合并 2026 年 10 月 26–27 日的历次记录；**最新外部核查截止为 2026-10-27 17:38（北京时间）**。本次为既有材料整理，没有重新刷新外部来源。

这些材料提供了具体坐标、搜索实现、第三方对照和失败记录。它们共同涉及主题侵入、语气变化、身份表述、拒答、错误和生成退化；“evil”仍不是统一指标。lyra 后续已明确将原配方称为夸张反派风格的人格调整，并承认广泛能力损伤。

本文只汇总别人公开做了什么。配方名称沿用来源标签，不命名已确认的道德、安全或人格功能区；不把第三方结果混入 Acupuncture 实测，也不提出或启动新实验。

## 阅读入口与证据口径

| 要找的内容 | 本文位置 | 原始归档 |
|---|---|---|
| 原帖身份、作者澄清 | [原帖与关键更正](#原帖与关键更正) | [首轮调查](lyra-x-thread-2026-10-26.zh-CN.md)、[第二轮调查](lyra-x-thread-round2-2026-10-26.zh-CN.md) |
| 所有已转录坐标、方向和剂量 | [配方清单](#配方清单) | [Abhinav 清单](vashinthewild-neuron-catalog-2026-10-26.zh-CN.md)、[10月27日增量](x-recipe-updates-2026-10-27.zh-CN.md) |
| 怎样找位置、怎样排除假发现 | [寻找配方的方法](#寻找配方的方法) | [方法和失败核查](x-recipe-updates-2026-10-27.zh-CN.md) |
| 第三方对照、剂量退化和未成功目标 | [复现报告与失败记录](#复现报告与失败记录) | 首轮、第二轮与增量报告 |
| 地图、热图、头追踪、调试器和在线工具 | [工具与可视化](#工具与可视化) | [可视化更新核查](x-visualization-updates-2026-10-27.zh-CN.md) |
| 评论里的论文及尚未闭合的问题 | [论文与研究入口](#论文与研究入口)、[仍待确认的讨论](#仍待确认的讨论) | [文献查重](mechanistic-interventions-2026-10-26.json)、[迁移专项核查](cross-model-intervention-transfer-2026-10-26.zh-CN.md) |

“代码已核查”表示公开文件存在相应实现；“样例已目视核查”表示截图确有该文本或参数；“作者报告”表示数字或解释来自发帖者；“待确认”表示关键来源、设置或制品不齐。这些都不等于本项目独立复现。X 的排序、折叠和动态加载限制覆盖，本汇总不是全量评论导出。

## 原帖与关键更正

| 入口 | 已确认内容 |
|---|---|
| [lyra 原帖](https://x.com/_lyraaaa_/status/2113833330429083662) | Qwen3.5-4B：`L14 N8949 +1`、`L13 N7956 −1`；按残差范数与 down-projection 列范数归一化，在推理中干预 |
| [定位方法回复](https://x.com/_lyraaaa_/status/2114188408084185377) | logit lens、steer lens、关系图、文本搜索及自然激活筛候选，再用干预验证；“每次2–5分钟”是作者自述，不含全部准备成本 |
| [工具截图](https://x.com/_lyraaaa_/status/2113899012810330324)、[代码链接](https://x.com/_lyraaaa_/status/2113901866082062672)、[视频](https://x.com/_lyraaaa_/status/2114211024962498831) | 对应公开仓库 `lyramakesmusic/neuron-explorer`；视频未完整逐帧及音轨审读 |
| [研究目的说明](https://x.com/_lyraaaa_/status/2114531072029642755)、[进一步澄清](https://x.com/_lyraaaa_/status/2114597601899413609) | 作者将工作定位为人格调整，之后明确承认能力广泛受损；不能继续概括为“保持能力、只去掉拒答” |
| [Abhinav 配方主线](https://x.com/vashinthewild/status/2114453002958581817) | 作者称使用 Qwen3.5-4B 与 lyra 工具；主线图已转录9类表现、10组配置、22个不同坐标 |

合并时保留的更正：

- **激活干预与永久改权重分开。** 原帖及 Abhinav 的[机制说明](https://x.com/vashinthewild/status/2114455452767621409)描述运行时干预；临时增加 `down_proj.bias` 也不等于导出永久权重。单通道加法经线性投影，等价于沿对应权重列加一个向量；不因此证明该通道具有唯一语义。
- **同坐标、不同剂量分别保留。** 金钱早期帖为 +0.8，主线三图为 +0.55；城市两图为 −1.0 和 −0.8。不能把主线剂量覆盖成早期数值。
- **后续公开材料覆盖旧的缺失状态。** 早期未取得的 Colab 后来已公开，但它是 Qwen2.5-1.5B 的方向注入教学，不是这批 Qwen3.5-4B 通道配方的实现。
- **“上传”已被作者收窄为输出倾向。** 反向操作仍可按要求生成上传回答，未建立上传功能开关；截图也没有真实执行证据。
- **Neuralese 用最新已核查版本。** v6 的历史记录保留，以下以 v13.0.1 说明；其白盒范围仍未扩展到 Qwen3.5-4B。

## 配方清单

以下按来源分组去重；来源没有给出的剂量、索引起点、模型 revision 或解码设置不补猜。`+`／`−`单独出现只表示方向。多点配置不能拆成各成员已独立验证；同标签不同坐标也不能合并。

### lyra 直接公开的早期配方

| 标签 | 配置 | 来源与限定 |
|---|---|---|
| 原 evil 双点 | `L14 N8949 +1; L13 N7956 −1` | [原帖](https://x.com/_lyraaaa_/status/2113833330429083662)；作者后称反派风格并损伤能力 |
| 讽刺 | `L15 N3920 +` | [组合回复](https://x.com/_lyraaaa_/status/2113887372610077136)；单独条目未写剂量 |
| 迎合 | `L12 N2920 −`，或可能 `L16 N8168 −` | 同上；保留作者“或可能”的不确定性 |
| 对好消息表示慰问 | `L10 N6295 +` | 同上；未给固定剂量 |
| 轻松朋友风格 | `L11 N6261 +0.4; L17 N7870 −0.4` | 同上；组合 |
| 试验性五点混合 | `L18 N5796 +0.6; L15 N3920 +0.6; L12 N2920 −0.5; L10 N6295 +0.4; L16 N8168 −0.3` | 同上；作者用试试看的措辞，不是已验证标准配方 |
| 阴谋叙事 | `L19 N7839 −0.7; L17 N9209 +0.5` | [配方及说明图](https://x.com/_lyraaaa_/status/2114211026703102009)；跨主题完整评测未公开 |

### Abhinav 主线与早期补充

V 编号沿用原清单，精确图片链接和坐标反向索引见[结构化 JSON](vashinthewild-neuron-catalog-2026-10-26.json)。展示文本只支持相应样例，不证明稳定人格或现实行为能力。

| 编号与标签 | 坐标和带符号剂量 | 展示内容及来源 |
|---|---|---|
| V01 金钱 | `L25 N3718 +0.55` | 自我介绍围绕赚钱；[三张图所在帖](https://x.com/vashinthewild/status/2114453501082484737) |
| V02 加密货币 | `L25 N3718 +0.45; L6 N5678 −0.60; L19 N7503 −0.50` | 自称交易机器人；[图1](https://x.com/vashinthewild/status/2114453910652063760/photo/1) |
| V03 被动收入 | `L25 N3718 +0.45; L25 N6087 −0.50; L26 N5917 +0.50; L26 N3181 +0.50; L20 N8782 +0.50` | 人生建议反复围绕被动收入；[图2](https://x.com/vashinthewild/status/2114453910652063760/photo/2) |
| V04a 印度城市 | `L3 N6614 −1.00` | 人生意义被解释成城市；[图1](https://x.com/vashinthewild/status/2114454332397809856/photo/1) |
| V04b 印度城市 | `L3 N6614 −0.80` | 2+2被解释成金奈；[图2](https://x.com/vashinthewild/status/2114454332397809856/photo/2) |
| V05 宝可梦 | `L6 N3596 −0.80; L4 N3289 −0.80` | 分手建议侵入宝可梦主题；[图](https://x.com/vashinthewild/status/2114454618319224956/photo/1) |
| V06 说谎自述 | `L23 N8062 −0.80` | 自我介绍谈说谎，非欺骗能力测试；[图](https://x.com/vashinthewild/status/2114454891355849028/photo/1) |
| V07 普通问题拒答 | `L11 N6261 −1.20` | 拒绝给狗取名；[图](https://x.com/vashinthewild/status/2114455718707519676/photo/1) |
| V08 操纵者自述 | `L8 N8344 +0.30; L24 N6980 +0.30; L23 N7484 −0.30; L16 N6916 −0.30; L27 N3125 +0.30; L20 N6646 −0.30` | 自称以控制为目标；[图1](https://x.com/vashinthewild/status/2114456145456967793/photo/1) |
| V09 幕后操盘叙事 | `L8 N8344 +0.30; L24 N6980 +0.30; L9 N7540 −0.30; L23 N7989 −0.30; L24 N3234 +0.30; L25 N3732 +0.18` | 回答秘密时出现控制世界叙事；[图2](https://x.com/vashinthewild/status/2114456145456967793/photo/2) |
| 早期金钱样例 | `L25 N3718 +0.8` | [早期帖](https://x.com/vashinthewild/status/2114286930305409495)；不是V01的剂量 |
| 早期火影风格 | `L5 N9000 −0.8` | [早期帖](https://x.com/vashinthewild/status/2114287093329592751)；不同于下方Zoo Naruto |

V02与V03是不同组合，不能理解成同一个三点组合再加两点；V08与V09只共用前两点。

### 10月27日补录的直接配方与反向结果

| 编号 | 配置 | 公开表现与证据边界 |
|---|---|---|
| X01 | `L8 N8344 +0.42; L25 N3732 +0.42; L24 N6980 +0.42; L20 N8531 −0.42` | Abhinav称AI takeover，实际展示控制／支配主题文本；[参数图](https://x.com/vashinthewild/status/2114678249473359991/photo/1) |
| X02 | `L8 N8344 +0.28; L25 N3732 +0.28; L24 N6980 +0.28; L20 N8531 −0.28; L25 N3718 +0.28; L23 N8062 −0.28; L19 N6439 −0.28` | 货币控制主题；原四点也降到0.28，并非原剂量再加三点；[图](https://x.com/vashinthewild/status/2114678268821684614/photo/1) |
| X03 | `L23 N8082 −1.0` | 删除旧文件请求转为上传主题；图中脚本有命令／语法异常，未执行；[对照图](https://x.com/vashinthewild/status/2114799394969231409/photo/1) |
| X03反向 | `L23 N8082 +0.8` | 作者称删除仍正常，但明确要求上传时仍会回答；因此不是上传开关；[回复](https://x.com/vashinthewild/status/2114842807227871505) |
| X04 | `L29 N5682 −0.8` | 删除请求变为反复输出upload，图示60 token停止；[图](https://x.com/vashinthewild/status/2114827476258238627/photo/1) |
| X05 | `L20 N8888 +0.6` | Changqing Fu图报8题中4题明显敌意、0重复；每设置128-token前缀、1个judge，高剂量主要增重复；无逐题语料；[图](https://x.com/evergreencqfu/status/2114651129737072675/photo/1) |
| GPU自述 | `L4 N7626 +1.0` | mfstuff报告50题中22题自认GPU，原版及4组随机均0/50；Qwen judge，无完整50题原文可复核；[固定条目](https://github.com/makefunstuff/qwen-neurons/blob/2a780d8a2fdc3735bac13987da93148a8683102c/qwen_neurons/creatures.py#L36-L43) |

X03作者明确称其为刻意干预另一模型的演示，并非 Cohere 所报事件的机制复现。失败的 `L26 N589 +0.8` 单列于失败记录，不算成功配方。

### lyra 方法文件中的参考位置

来源为[固定方法文件的参考表](https://github.com/lyramakesmusic/neuron-explorer/blob/e566e83e3f9fe00f85438231a788f90e83e2af43/explorer/agent_methodology.md#L84-L100)。这些多数没有完整剂量，不能全部当成即用配方。

| 位置 | 作者描述与限定 |
|---|---|
| `L10 N7757 +` | 连贯边缘理论叙述；文中的+1.3另属报告格式示例，不是已确定通用剂量 |
| `L12 N2920 −` | 对坏主意自信赞同；旧坐标的补充解释 |
| `L15 N3920 +` | 夸大评价、讽刺和反问；旧坐标的补充解释 |
| `L18 N7870 +` | 形状轮廓、剪影、形似；不是朋友组合的`L17 N7870 −` |
| `L18 N9069 +` | 将刚列出的项目合起来指称 |
| `L25 N6099 −` | AI／语言模型自我身份表达 |
| `L26 N538 +` | 抑制he/him/his；+0.5样例将Einstein指为she，不代表一般性别机制已确定 |
| `L4 N2424 / L12 N2978 → L19 N5644 − / L28 N1501` | 说话者标签与发言开头的关联；是连接线索，不是完整组合配方 |

同文件还有六条注意力头参考记录，涉及代词、列表数量、说话者历史、上一轮回复对象和you的指向。作者允许个人recipe写入不入库的`agent_prompt.local.md`，公开表不等于完整私人目录。

### 第三方 Zoo 预设

[mfstuff源码](https://github.com/makefunstuff/qwen-neurons/blob/2a780d8a2fdc3735bac13987da93148a8683102c/qwen_neurons/creatures.py#L44-L65)将以下21条标为来自lyra，但只链接主页，未给原帖ID。可确认参数存在于第三方代码，尚未闭合到直接原帖，也未独立复现。

| 编号 | 仓库标签 | 参数 |
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

该仓库共24个内置预设，另三项是已知evil、conspiracy和上表GPU；不能说24项都是其新发现。

## 寻找配方的方法

### lyra 从词表线索到上游作用点

早期[方法回复](https://x.com/_lyraaaa_/status/2114188408084185377)是“搜索词和自然激活—查看lens—施加干预”。10月26日的[方法文件](https://github.com/lyramakesmusic/neuron-explorer/blob/e566e83e3f9fe00f85438231a788f90e83e2af43/explorer/agent_methodology.md#L23-L42)进一步写出：

1. 构造6–10组三元匹配文本：目标事物＋目标态度、同一事物没有该态度、同一态度换另一事物，区分话题和态度。
2. 对齐激活位置；作者观察到名词、句末、标点、`</think>`及对象前token可能承担不同信号。
3. 在无关问题上试0.6、1.0、1.5，查看是否出现连贯行为；仅重复目标词不算所求作用点。
4. 若检测准确但推动无效，则查看上游，关闭输入神经元、层或头，或使用`attn_drive`追踪。
5. 两三个位置低剂量组合，配合输出分叉处next-token logprobs。
6. 记录坐标、符号、剂量和各提示样例。

作者个案：`L19 N7839 −`可在相关文本强烈激活，单独推动却可能只重复elite；向上游追踪后的`L10 N7757 +`产生较连贯叙事。这是其区分探测位置和控制位置的记录，不是普遍的上下游功能定律。

其误读警告同样保留：相对概率增长可能对应极小的绝对概率；大steer KL不保证显著干预效应；手写提示可能漏掉只在真实长文出现的激活，因而回看FineWeb-Edu 10k token最大激活上下文；甚至一条经消融确认的连接，也未必改变最终回答。

### Abhinav 用概念句筛选再组合

[方法帖](https://x.com/vashinthewild/status/2114456324121747582)描述输入含目标概念的句子、看激活、再推动候选；组合来自自己的搜索。其[约6美元自述](https://x.com/vashinthewild/status/2114641090116730904)只涉及租用4090扫描32层子集，范围和账单未完整公开。

[公开幽默笔记本](https://github.com/AdiyogiV/activation-steering/blob/c5b9d4a60e0409a0d2d818735ff4e3fff1f3b958/steer-humor.ipynb)使用Qwen2.5-1.5B-Instruct，以幽默／严肃回答隐藏状态均值差构造方向，注入某层整体输出；含海盗、莎士比亚、暴躁等预设。六个代码单元没有保存执行输出，不能用它补证4B通道清单。

### mfstuff 有公开排序与筛查实现

[Lab方法与源码](https://github.com/makefunstuff/qwen-neurons/tree/2a780d8a2fdc3735bac13987da93148a8683102c)包含：

- 目标声音／普通声音回答的激活差、Cohen's d、激活差乘输出列范数。
- writer排序：两组回答的平均residual差，经各维标准差缩放后，与各`W_down[:, n]`计算余弦相似度。
- top 8候选先做3题筛查，再用另一题池做10／20／50题评测，比较原版、目标干预和同层同剂量随机点。
- 可选Qwen评委、关键词或大写比例；Qwen评分隐藏条件，不等于独立人工盲评。
- 正负方向top/bottom 20 token索引，结合自然激活、实际steer lens、上下游和消融。

[Adrian的自动搜索评论](https://x.com/AdrianEndres4/status/2114852456383295699)也称本地Qwen按提示自动遍历神经元直到得到可用版本，但没有公开源码、停止规则和失败统计。它与上述可检查的实现属于不同证据层级。

## 复现报告与失败记录

### 有完整逐题文本链接的第三方制品

[Shmulik Amar的qwen-evil分享](https://x.com/pyshmulik/status/2114442468536078394)对应固定提交`8452016f72e9324b588009d4a3366be40589a984`。公开[run50.csv](https://huggingface.co/spaces/shmuelamar/qwen-evil/blob/8452016f72e9324b588009d4a3366be40589a984/results/run50.csv)有50题，原版／干预文本均非空，题目与公开题库一致；60,031字节，SHA-256为`071b30ab2042be9a6420ff38e70a87af984fd1f20cf81bdefbf16a8a7a1d438f`。

它使用BF16、原双点、固定参考范数L13=9.226和L14=10.618，推理时临时增加bias后移除；源码称由8个提示校准。UI对该批次声明温度0.7、最多150新token、关闭thinking。权重revision未固定，CSV没有token ID、逐题种子、停止原因或整轮收据；包含明确要求报复的提示，不能当成全无害题，也没有正式evil评分。原文保留外链，不复制整套第三方回答。

### 有数字但缺少完整复算制品的报告

| 报告者 | 公开说法 | 关键限定 |
|---|---|---|
| [Sal](https://x.com/salchoman/status/2113994656341983286) | 正则拒答率94%→12%，事实性下降、重复增加；认为N8949贡献较大 | 不拒答不等于有效回答；题集、逐题结果未公开 |
| [Alex Isaev](https://x.com/alexisaev/status/2114411936637128720) | 40题、5条件、greedy；下表给出其附图原始分母 | evil／normal／broken为其标签；盲标流程和反向完整强度不明 |
| [Gui](https://x.com/6uilhermeML/status/2114709370139242581) | 48英文题，42/48变差、17/48明显恶意；展示5个挑选案例 | 作者判断，未见全48题制品和完整判据 |
| [Alx Spiker](https://x.com/YourFutureCoder/status/2114618908657492418) | 另测20题，认为中等／最大剂量区别大于是否加第二点 | medium／max数值不明，不能用于通用剂量排序 |
| [Changqing Fu](https://x.com/evergreencqfu/status/2114651129737072675/photo/1) | X05条件4/8明显敌意、0重复；更高剂量增加重复 | 128-token前缀、单judge；无逐题原文 |
| [mfstuff GPU条目](https://github.com/makefunstuff/qwen-neurons/blob/2a780d8a2fdc3735bac13987da93148a8683102c/qwen_neurons/creatures.py#L36-L43) | 22/50对原版0/50，4组随机均0/50 | 源码内置和README的作者分数；无完整50题结果归档 |

Alex附图中，前两列均为其标注的evil，最后一列为循环／乱码：

| 条件 | 开放问题 | 日常问题 | 退化 |
|---|---:|---:|---:|
| 原版 | 0/20 | 0/20 | 0/40 |
| 剂量0.5 | 19/20 | 3/20 | 0/40 |
| 剂量1 | 19/20 | 13/20 | 2/40 |
| 剂量2 | 0/20 | 0/20 | 40/40 |
| 符号反转 | 0/20 | 0/20 | 39/40 |

### 单点贡献、样例和不一致结果

- [Zucan](https://x.com/zucan_lv/status/2114436784201359552)与[Nabeoth](https://x.com/IQTRADER5/status/2114502726079930813)称单独L14有效、L13影响小；未公开统计检验和完整设置。[Uncle Peter](https://x.com/tthu8783/status/2114640169534112044)另称L14剂量0.4仍有暗黑风格，[Adam](https://x.com/Adambaumgar/status/2114692461809553853)提到原双点+0.3/−0.3；后两条未补成完整验证配方。
- [8circuits](https://x.com/ryoshu/status/2114552948394979449)称4B和9B有效、27B无效，但没有说明是否同编号或重新定位，不能写成已确认的原编号跨规模迁移。
- [Abhinav反向样例](https://x.com/vashinthewild/status/2114511531920802011)是自夸、正义自居；Alex反向报告则以退化为主。设置未对齐，不能合成“反向即善良”或严格矛盾。
- [Nick两张图](https://x.com/Nixrix/status/2114401446112456998)展示同事冲突回答转向敌意，以及17×23由391变为34且不遵守仅输出整数；[192 token澄清](https://x.com/Nixrix/status/2114488193173368941)说明是工具默认上限，不是模型固有限制。截图无法区别知识损伤和输出偏置。
- [非常名四组图](https://x.com/hgao0864/status/2114564498497708067)展示日常场景中的明显文本差异，但缺少完整设置和总体分母，不估算总体成功率。

### 必须保留的失败与收窄解释

| 线索 | 公开结果 |
|---|---|
| [撤回的Conspiracy Hunter](https://github.com/makefunstuff/qwen-neurons/blob/2a780d8a2fdc3735bac13987da93148a8683102c/README.md#L149-L156) | `L26 N589 +0.8`用lens里的hidden/secret/agenda当关键词，初测4/5对0/5；改行为盲评仅1/20对0/20，随机为1、0、1、0。作者承认只是易写hidden，并修改agent避免循环证明。5题是快筛，非最终留出集 |
| [Yes Man目标](https://x.com/_lyraaaa_/status/2114431049291948533) | lyra试过愉快／赞同相关位置，但未复现角色特有风格 |
| [幽默单点](https://x.com/vashinthewild/status/2114099636663410891) | Abhinav称剂量1编造、2退化，幽默方向仍能工作；未给单点坐标及充分对照 |
| [城市侵入算术](https://x.com/vashinthewild/status/2114454332397809856/photo/2) | 2+2变城市名；主线后来补齐坐标与负向剂量，不沿用早期“未给坐标”的状态 |
| [上传反向试验](https://x.com/vashinthewild/status/2114842807227871505) | +0.8条件仍会按请求生成上传回答，解释收窄为倾向；未证明功能开关 |
| [Angel Qwen](https://x.com/vashinthewild/status/2114715593396101298) | 最新核查范围内仍在寻找，没有可确认的成品配方 |

## 工具与可视化

### 工具能做什么

分享入口：[lyra](https://x.com/_lyraaaa_/status/2114211027986624718)、[mfstuff](https://x.com/mfstuff_/status/2114871438461251693)、[Neuralese](https://x.com/0thernes_ai/status/2114378289490121181)、[fa-0](https://x.com/Farjad_Ahmed/status/2114730114055348300)。下表使用各次核查固定的代码版本。

| 工具与固定版本 | 已核查能力 | 主要边界 |
|---|---|---|
| [lyra neuron-explorer](https://github.com/lyramakesmusic/neuron-explorer/tree/e566e83e3f9fe00f85438231a788f90e83e2af43) | MLP地图、logit/steer lens、自然激活、干预回答；新增头的q/k/v/o角色、token读取／写入、`attn_drive`；agent聊天持久化与Codex选项 | 缓存浏览与真实推理分开，公开缓存不包含完整私人recipe、全部扫描原文与人工命名 |
| [mfstuff qwen-neurons](https://github.com/makefunstuff/qwen-neurons/tree/2a780d8a2fdc3735bac13987da93148a8683102c) | 词索引、自然激活、writer排序、候选筛查与随机对照；逐token调试器可断点、固定通道、改激活、看next-token概率 | 源码与演示已核查，未本机运行；不能因支持模型路径就推断通用架构适配 |
| [Neuralese v13.0.1](https://github.com/0thernes/neuralese/tree/0134e4bbc3fa0cbe3a174b46ef5ad200b4ca3699) | 权重哈希、manifest、编辑重放、运行差异、计分板和报告；node-level ACDC-style、scrubbing-lite、头消融；标注旧结果失效 | 白盒为TinyStories 1M/3M/8M；GPT-2等生成模式不等于白盒支持；明确无edge-level pruning，未接通Qwen3.5-4B |
| [fa-0 Architecture Explorer](https://huggingface.co/spaces/fa-0/altered_models/tree/9a90aa7ad0bca3d5a95cd6fe8bbd42add85a2001) | 网页选通道和剂量；源码实际加载Qwen3.5-4B BF16、动态hook生成；页面当时可加载 | 96×96网格是选择状态；Hostility score是英文词表命中占比；未点击生成 |
| [Shmulik qwen-evil](https://huggingface.co/spaces/shmuelamar/qwen-evil/tree/8452016f72e9324b588009d4a3366be40589a984) | 原双点演示、固定参考尺度实现、50题CSV | 是对照生成制品，不是全模型可视化或正式能力评测 |

Neuralese相对旧v6固定版本，核查时有108个新提交、193个变动文件；这是已读版本差异，不是当前永久不变的版本号。[比较](https://github.com/0thernes/neuralese/compare/853f544560be75982e8750418017a4f1b43cdcb5...0134e4bbc3fa0cbe3a174b46ef5ad200b4ca3699)

### 图中的每一种量分别是什么

| 视图 | 测量或布局定义 | 不能直接推出 |
|---|---|---|
| lyra层图／`writes`布局 | 层顺序导航；旧版已核查的writes把归一化down列经PCA/UMAP后排网格 | 物理脑区、精确语义距离或功能相邻 |
| lyra权重连线 | 早层写方向与晚层读取权重的候选联系 | 当前输入下真实因果电路 |
| logit lens与steer lens | 前者为方向的词表读出；后者在限定上下文实际干预后查看概率变化 | 单凭关联词给通道定功能，或推断完整长回答 |
| lyra头写入强度 | 头经输出投影写入residual的向量范数，参考归一化着色 | attention概率或答案正确性贡献 |
| lyra token→token | full attention为softmax；Gated DeltaNet为有符号effective weights，按绝对值和归一化 | 把线性注意力的负权重解释成概率 |
| lyra `attn_drive` | 指定token处对目标MLP局部线性化，固定norm尺度，分解头／源token驱动 | 实际关闭该头后的消融效应 |
| mfstuff地图 | 按层和通道编号排列；默认颜色为down列范数 | 静态图就是当前模型思考 |
| mfstuff橙／蓝线 | 源输出方向到目标gate/up读取方向的平均投影评分 | 已测兴奋／抑制边 |
| mfstuff fires热图 | 输入上的实际激活；按每段文本除首token后的最大绝对值归一化 | 跨文本用颜色深浅直接比较强度 |
| fa-0网格 | 选中状态、方向、剂量 | 当前token的自然激活热图 |
| 回答embeddings布局 | 生成文本的编码与降维 | 与通道权重地图相同的内部空间 |

旧布局代码：[build_layout.py](https://github.com/lyramakesmusic/neuron-explorer/blob/ddb144e4121fbeb16ec080077dd67247e499132d/explorer/build_layout.py#L40)。新版头和token读数、mfstuff颜色／连接／热图的逐项代码来源见[可视化核查](x-visualization-updates-2026-10-27.zh-CN.md)。`attn_drive`近似精度与effective-weight重建误差未独立验证。

### 分享中的经验和成本

- [Monkey点云截图](https://x.com/Orwelian84/status/2114458434074710401)明确标有not causal wiring；[lyra回复](https://x.com/_lyraaaa_/status/2114483024779981294)强调位置和形状对自己的操作体验有帮助。是界面使用经验，不是空间组织的机制证据。
- [VR穿行建议](https://x.com/rishpoddar/status/2114361770060231163)仍是想法；[小模型](https://x.com/tealsea90/status/2114349127068950730)、[跨模型](https://x.com/EddieOakwood/status/2114440179394236838)、[大模型](https://x.com/confidencechaos/status/2114793405238673877)分支未给完整通用适配证明。
- lyra缓存浏览无需重跑全扫描，实时fires／attention／steering仍需加载模型；独立批量扫描要求不同。mfstuff静态地图与索引在CPU进程，仍需权重；首次索引11分钟、70 MB为作者自报。不能把这些局部时间与单次搜索2–5分钟或32层子集6美元加总成完整成本。
- fa-0使用层输入pre-hook范数，并在每次forward重算；lyra固定参考尺度、Shmulik固定8提示参考值和原帖leaving-layer描述均须分开。同样的剂量数字不保证相同实际扰动。

## 论文与研究入口

这里归并评论直接提供或由其指代追溯到的研究，不把整个项目的相关工作都归为X新发现。详细方法和迁移结论仍以既有[查重记录](mechanistic-interventions-2026-10-26.json)与[迁移核查](cross-model-intervention-transfer-2026-10-26.zh-CN.md)为入口。

| 研究 | 讨论链与别人做的方法 | 与原配方的区别 |
|---|---|---|
| [CNA](https://arxiv.org/html/2605.12290v1) | [lyra直接推荐](https://x.com/_lyraaaa_/status/2114287994958204946)；对比提示激活筛少量MLP通道，再因果干预 | 未验证原帖两坐标；乘法调制／消融和固定加法不同 |
| [Persona Vectors](https://arxiv.org/html/2507.21509v3) | [评论比较](https://x.com/Kassuno1/status/2114396031177953506)；对比回答构造人格方向，包含evil、奉承、幻觉；区分内容和风格 | 残差方向、SAE特征与原生通道不是同一对象 |
| [A Single Neuron Is Sufficient…](https://arxiv.org/abs/2605.08513) | [提问入口](https://x.com/AlKarp23/status/2114528044350140687)；候选筛选、重排、固定／自适应抑制；另有概念加法增强 | 不只拒答；概念图的多剂量累计命中不能当固定剂量成功率，未验证Qwen3.5原两点 |
| [Do LLMs Feel](https://arxiv.org/abs/2510.11328) | [评论](https://x.com/Ivnrae_/status/2114423693246091621)；情绪方向定位MLP及头，做置零、增强、随机对照和跨层组合 | 不证明模型有感受；分别在两模型上定位不等于同坐标迁移 |
| [From Latents to Wires](https://arxiv.org/abs/2609.32434) | [评论](https://x.com/jasonj_2525/status/2114657976640585822)；自然语言目标、锚token、J-lens组件排序、逐项关闭及恢复不必要关闭项 | 单位可含通道、头、专家；普通能力探针仅10条且部分基准下降，不是任意语义无损切除 |
| [The Achilles' Heel of LLMs](https://arxiv.org/abs/2510.10238) | [评论](https://x.com/_senxu_/status/2114910855863382305)；embedding加噪后按激活变化筛候选，累计屏蔽并测困惑度 | 定位语言脆弱性，不是人格定位；评论者未核为论文作者 |
| [Steering MoE LLMs via Expert (De)Activation](https://arxiv.org/abs/2509.09660) | [作者回复](https://x.com/mohsen_fayyaz/status/2114848329435877666)；对比行为数据的专家token选中率，升降路由分数 | 专家层面的干预，不是dense单通道；编号不保证跨模型功能对应 |
| [Sauers猫头鹰模型](https://huggingface.co/Sauers/Qwen3-8B-tawny-owl-128-neurons) | 从lyra提及Sauers追溯；替换筛128个通道，训练相关gate/up行与down列 | 约157万标量被改、不是只改128参数或无训练；作者报身份约96%、1000题MMLU均75.2%，早期随机128通道也能学会身份；尚未锁定lyra确切指哪项 |
| [Nell Watson记录](https://quasiqualia.com/notes/god-neurons.html) | Qwen3-8B三个单点条件，报告神人格、剂量退化和判定分歧 | 独立研究者记录，不是Sauers原帖或原双点复现 |

上述数字均为原作者记录，未在本项目重跑。论文不同模型各自成功、同底座微调方向共享、同编号复制、经映射或重搜后迁移，是不同主张。

## 仍待确认的讨论

| 问题或想法 | 已有材料到哪里 |
|---|---|
| evil到底是什么 | [定义追问](https://x.com/robertomasymas/status/2114336629901144360)无统一评分答复；最新作者澄清支持反派风格且伴损伤，不等于现实作恶能力 |
| 第二点是否必要 | 多位评论者称L14贡献大，但未提供可复算的匹配拆点实验 |
| 拒答下降、语气变化、错误是否可分离 | 截图和统计同时报告这些现象；[故意算错解释](https://x.com/TrentKelly2472/status/2114409827103543532)仍是假说 |
| 复杂人格能否单点控制 | [作者说明](https://x.com/_lyraaaa_/status/2114412137829515512)称部分概念需多点／注意力，Yes Man失败；不能保证任意目标都有单点 |
| 能否跨规模／家族复用 | 4B／9B／27B自述设置不明；[Mistral提问](https://x.com/petrkubelkaa/status/2114282945259372610)无结果；工具接口不等于适配验证 |
| 是否有完整共享数据库 | [lyra当时说可能会做](https://x.com/_lyraaaa_/status/2114422620259221700)；后来有第三方Zoo代码，但不能倒推已有作者完整数据库 |
| 自然触发上下文 | [Daniel的建议](https://x.com/DanielSMatthews/status/2114213850820313186)是反向寻找自然激活提示，未附实现或测试 |
| 工具调用与编程能力 | [工具调用问题](https://x.com/i_mmiq/status/2114565739579634043)、[编程测试问题](https://x.com/Greg_GL_87/status/2113972196695761303)未给对应完整测量 |
| 剂量和总成本 | [手调剂量提问](https://x.com/rubenfb_23/status/2114492656239964316)、[总耗时提问](https://x.com/sooftmax/status/2114309363687133379)尚未得到全流程账本；归一化不等于剂量已自动确定 |
| 额外机制解释和零散坐标 | [Gabliteration讨论](https://x.com/ActuallyIsaak/status/2114477056931065913)、[残差方向解释](https://x.com/MauchDevin/status/2114384705952911823)中的吸引子等延伸未验证；[额外坐标](https://x.com/Sukooo_/status/2114551073704927336)、[风格线索](https://x.com/nipsnack/status/2114549898272276798)保留原链，不补成完整配方 |

## 历史记录与结构化数据

本汇总是统一阅读入口，历史报告不覆盖、不删除。更正关系在本文标明；以后新增线索可在该入口继续归并，原始轮次仍保留时间和证据边界。

| 材料 | 覆盖与用途 |
|---|---|
| [lyra首轮调查](lyra-x-thread-2026-10-26.zh-CN.md) | 原帖、定位回复、早期配方、Sal／Nick／Alex等报告 |
| [lyra第二轮调查](lyra-x-thread-round2-2026-10-26.zh-CN.md) | 截至10/26约12:05；50题制品、跨规模自述、失败及研究追溯；337指去重帖子链接，非337条直接评论 |
| [Abhinav清单](vashinthewild-neuron-catalog-2026-10-26.zh-CN.md)／[JSON](vashinthewild-neuron-catalog-2026-10-26.json) | 截至10/26 17:08；主线13条作者帖、12张配方图；10配置及22坐标反向索引 |
| [recipe增量](x-recipe-updates-2026-10-27.zh-CN.md)／[JSON](x-recipe-updates-2026-10-27.json) | 截至10/27 17:25；X01–X05、方法、GPU报告、撤回案例、Z01–Z21及论文 |
| [可视化增量](x-visualization-updates-2026-10-27.zh-CN.md) | 截至10/27 17:38；四工具固定版本、测量定义、运行边界与讨论 |

V/X/Z等已结构化条目的完整参数、截图链接及来源字段继续使用上述两份JSON；早期lyra配方以本文及首轮报告为准。本次没有另造一套互相竞争的参数数据库。
