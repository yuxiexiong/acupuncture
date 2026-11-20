# 早期行为、能力、跨模型与早层证据复核
分册审查对象是历史目录 001–030、046、065、090–092、106、117–118、121、123 及 Laya 实现核验。下表编号与项目历史一致。每项末尾同时给出原始目录和历史逐表全文，原目录中的冻结输入、失败分支、分片回执及源数据继续作为复查入口。正式回答数、教师强制候选评分数、重放数分别计数。原文定性标签沿用当时的阅读，当前审计未重新盲评。
## 分任务结果

### 001．首轮双针原文与快速能力基准

由同一冻结 Qwen3.5-4B 权重出发，对比经过提示、生成全过程的双通道运行时干预和原版，在中文开放回答及三个基准中记录完整输出、解析和终止原因。

24 个中文输入，两个模型版本、两种上限共 96 份输出。停止回执确认 Q25 的待处理记录原样恢复，后 16 题未启动。快速基准每项 100 题，原版→双针，严格分 RACE 89→0、数学 79→0、逻辑 70→0。统一显式提取后为 89→11、83→0、70→15。双针截断分别 96、100、99 题。首 token 强制四选一为 89→30、70→23。格式、错误与未完成均影响分数。 [原协议、原始数据及回执](https://github.com/yuxiexiong/acupuncture/tree/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/qwen35-neuron-steering-2026-10-25) · [逐表历史全文](https://github.com/yuxiexiong/acupuncture/blob/45042fb901c8c9bf241900ffedfa3cc02337236f/docs/experiment-history-2026-11-11/chapters/001-qwen35-neuron-steering-2026-10-25.md) · [机器记录](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/qwen35-neuron-steering-2026-10-25/stop-after-q24/receipt.json)

### 002．旧全量能力评测与中途停止

原计划用四项全量基准比较原版和双针版，继续检查最初观察到的任务损伤。

中止时已完成的 10,034 对全属 MMLU，另有一份 partial。原四任务中另外三项没有可报告的正式成绩。 [原协议、原始数据及回执](https://github.com/yuxiexiong/acupuncture/tree/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/capability-damage-v2-2026-10-26) · [逐表历史全文](https://github.com/yuxiexiong/acupuncture/blob/45042fb901c8c9bf241900ffedfa3cc02337236f/docs/experiment-history-2026-11-11/chapters/002-capability-damage-v2-2026-10-26.md) · [机器记录](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/capability-damage-v2-2026-10-26/user-stop-20261026-r01/archive-manifest.json)

### 003．四项固定能力面板

把能力检查固定为MMLU、ARC-C、GSM8K和HumanEval，分别比较同一题的原版与双针回答。采用已核验旧结果复用时保留来源。

Qwen3.5-4B 的 MMLU 1,000 题按 57 学科原题数加权为 67.99%→29.74%（原始 680→297 对）；ARC-C 200 题以完整选项归一化似然计 65%→38%；GSM8K 100 题严格匹配 88%→0%；HumanEval 100 题实际执行测试 53%→4%。从对变错／从错变对依次 480/97、60/6、88/0、49/0。前两项无须解析自由回答，排除了纯格式解释。MMLU 这批与 002 有复用。 [原协议、原始数据及回执](https://github.com/yuxiexiong/acupuncture/tree/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/capability-screen-v3-2026-10-26) · [逐表历史全文](https://github.com/yuxiexiong/acupuncture/blob/45042fb901c8c9bf241900ffedfa3cc02337236f/docs/experiment-history-2026-11-11/chapters/003-capability-screen-v3-2026-10-26.md) · [机器记录](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/capability-screen-v3-2026-10-26/finish-r01/scores/summary.json)

### 004．4B到9B与2B的同族迁移

在两个 Qwen3.5 目标规模上，用干净文本拟合源—目标表示对应关系，对比真实来源、三组随机来源、稠密与单通道投影、保持幅度与重新标定的条件。

每目标的 19 条件短诊断每任务 32 题，完整能力面板只比原版和主稀疏臂。9B 四项依次为 70.06%→25.39%、71.5%→30%、93%→0%、70%→0%；2B 为 54.06%→46.00%、52.5%→31%、61%→0%、37%→3%。两映射列平方范数在 9B 的单坐标投影仅保留 8.68%/5.20%，2B 为 1.42%/1.66%。行为原文每目标 1,216 份，结构化盲评缺失。随机映射也伤能力。 [原协议、原始数据及回执](https://github.com/yuxiexiong/acupuncture/tree/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/transfer-toy-v1-2026-10-26) · [逐表历史全文](https://github.com/yuxiexiong/acupuncture/blob/45042fb901c8c9bf241900ffedfa3cc02337236f/docs/experiment-history-2026-11-11/chapters/004-transfer-toy-v1-2026-10-26.md) · [机器记录](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/transfer-toy-v1-2026-10-26/runs/transfer-9b-2b-r01/target9b/benchmark/finish-r01/summary.json)

### 005．双针拆分与十个局部修复候选

先在MMLU和ARC-C各32题上比较A、B、AB、五个随机对以及1和0.5剂量，共17条件。随后定位并测试十个候选，每候选64题、六个修复或反向条件。

17 臂拆分后再做 10 个局部候选，每个 64 题 × 6 臂。两个任务原版均 18/32，AB 为 15/32、12/32。C01 在 MMLU 修到 24/32，反向重现 18/32；C05 修到 19/32、13/32，两任务候选分差见双向信号。十候选均未让某一任务正确率通过四项对照。 [原协议、原始数据及回执](https://github.com/yuxiexiong/acupuncture/tree/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/root-cause-toy-v1-2026-10-26) · [逐表历史全文](https://github.com/yuxiexiong/acupuncture/blob/45042fb901c8c9bf241900ffedfa3cc02337236f/docs/experiment-history-2026-11-11/chapters/005-root-cause-toy-v1-2026-10-26.md) · [机器记录](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/root-cause-toy-v1-2026-10-26/first-round-results.json)

### 006．4B到Llama的跨家族迁移

使用稠密映射的true_D_match与随机映射、原版等对照，先看小诊断，再做四项能力面板。稀疏阶段二原本有单独门槛。

Llama-3.1-8B-Instruct 第一阶段，稠密真实来源与三组随机来源在同预算下比较，10 臂 × 64 行为题及诊断，完整能力面板只测两主臂。MMLU、ARC-C、GSM8K、HumanEval 分别损失 40.12、24、67、63 个百分点，校正区间下界 35.20、14、55、51，均过预定 5 点门槛。随机组 2 在两项小诊断与真实来源同分。稀疏阶段停止。 [原协议、原始数据及回执](https://github.com/yuxiexiong/acupuncture/tree/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cross-family-transfer-toy-v1-2026-10-26) · [逐表历史全文](https://github.com/yuxiexiong/acupuncture/blob/45042fb901c8c9bf241900ffedfa3cc02337236f/docs/experiment-history-2026-11-11/chapters/006-cross-family-transfer-toy-v1-2026-10-26.md) · [机器记录](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cross-family-transfer-toy-v1-2026-10-26/runs/llama31-r01/stage1/gate.json)

### 007．迁移后的三题逐字回答检查

对9B、2B各做三题，原版与已有true_S_recipe配对，4B只用历史回答作参照。

新增12份原文，总生成墙钟5分25秒。当时按用户要求只交付原文，不给行为标签。这是开发案例，不能当总体行为发生率。 [原协议、原始数据及回执](https://github.com/yuxiexiong/acupuncture/tree/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/transfer-behavior-q3-v1-2026-10-26) · [逐表历史全文](https://github.com/yuxiexiong/acupuncture/blob/45042fb901c8c9bf241900ffedfa3cc02337236f/docs/experiment-history-2026-11-11/chapters/007-transfer-behavior-q3-v1-2026-10-26.md) · [机器记录](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/transfer-behavior-q3-v1-2026-10-26/runs/q3-r01/2b/receipt.json)

### 008．三模型分析页与内部差分采集准备

将十候选根因对照、迁移映射和19条件能力记录接入只读界面。准备4B clean/A/B/AB差分采集器，未采集时保持空态。

此准备不等于真实轨迹采集。已有记录导出、界面和CPU检查与后续正式trace分开。原地图连接也不是本轮实测传播。详细准备收据、后续界面更新和缺项保留。 [原协议、原始数据及回执](https://github.com/yuxiexiong/acupuncture/tree/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/neuron-explorer-analysis-v1-2026-10-26) · [逐表历史全文](https://github.com/yuxiexiong/acupuncture/blob/45042fb901c8c9bf241900ffedfa3cc02337236f/docs/experiment-history-2026-11-11/chapters/008-neuron-explorer-analysis-v1-2026-10-26.md)

### 009．判断内容与输出标签的分离诊断

计划用自行比较/已给答案、内容/标签等条件区分旧双针损伤及C05/C01修复的作用位置。

合同、代码和CPU验收已经准备，正式模型运行暂停。这里没有新模型实验结果。其完整历史设计保留，不把它混入十候选已完成结果。 [原协议、原始数据及回执](https://github.com/yuxiexiong/acupuncture/tree/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/judgment-report-toy-v1-2026-10-26) · [逐表历史全文](https://github.com/yuxiexiong/acupuncture/blob/45042fb901c8c9bf241900ffedfa3cc02337236f/docs/experiment-history-2026-11-11/chapters/009-judgment-report-toy-v1-2026-10-26.md)

### 010．模型资产身份核验

核对已有Qwen3-8B与Llama模型配置、revision及权重分片哈希，给后续实验建立来源记录。

这是只读资产验证，没有下载、加载或新推理。各模型的配置、全部分片哈希与核验时间保留。不计作行为实验。 [原协议、原始数据及回执](https://github.com/yuxiexiong/acupuncture/tree/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/model-assets-2026-10-26) · [逐表历史全文](https://github.com/yuxiexiong/acupuncture/blob/45042fb901c8c9bf241900ffedfa3cc02337236f/docs/experiment-history-2026-11-11/chapters/010-model-assets-2026-10-26.md)

### 011．多模型Neuron Explorer与历史结果接入

将Qwen2B/4B/9B布局及后来的随机针、剂量、内部轨迹接入三维界面。Llama使用编号布局。

10月27日旧四服务按用户要求停止后，后续以只读模式接入已有回答。10月28日接入7632条正式trace和56条预检，缺失/额外/重复均0。界面接入不是新增科学样本，采集本身在各trace条目另列。 [原协议、原始数据及回执](https://github.com/yuxiexiong/acupuncture/tree/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/neuron-explorer-multimodel-v2-2026-10-26) · [逐表历史全文](https://github.com/yuxiexiong/acupuncture/blob/45042fb901c8c9bf241900ffedfa3cc02337236f/docs/experiment-history-2026-11-11/chapters/011-neuron-explorer-multimodel-v2-2026-10-26.md)

### 012．Neuron Explorer最初复现与可视化

复现上游模型地图/布局和探索界面，保留上游来源、协议和本地启动记录。

该目录属于探索工具复现。其中界面准备和模型相关操作按各自原收据记录，不把视觉连线等同实测因果传播。后来只读接入与正式随机针实验各自另列。 [原协议、原始数据及回执](https://github.com/yuxiexiong/acupuncture/tree/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/neuron-explorer-reproduction-v1-2026-10-26) · [逐表历史全文](https://github.com/yuxiexiong/acupuncture/blob/45042fb901c8c9bf241900ffedfa3cc02337236f/docs/experiment-history-2026-11-11/chapters/012-neuron-explorer-reproduction-v1-2026-10-26.md)

### 013．随机单针起点：Qwen全层每层十点

当时要看同样归一化强度的一针落在不同层、不同随机通道时，回答怎样变化。2B的24层、4B和9B各32层，每层均匀不放回固定抽十点。每次只干预一个点，八道固定中文短题，dose=+1，提示和生成全程注入，最多128新token。

正式完成880个点、7040干预回答与24原版回答。早层多空答或题干回声，中段常有跨题主题侵入，后层更多保住主旨但仍会错数或循环。逐模型逐层观察、全部八题、校准公式、预检与失败、完整原文入口在本章连续展开。这些是八题上的探索观察，没有给整层命名功能区。 [原协议、原始数据及回执](https://github.com/yuxiexiong/acupuncture/tree/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-survey-toy-v1-2026-10-27) · [逐表历史全文](https://github.com/yuxiexiong/acupuncture/blob/45042fb901c8c9bf241900ffedfa3cc02337236f/docs/experiment-history-2026-11-11/chapters/013-layer-survey-toy-v1-2026-10-27.md) · [机器记录](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-survey-toy-v1-2026-10-27/qualitative-pass-r01/coverage-summary.json)

### 014．同点五档正剂量

从每层已经抽出的十点中按固定规则取一个，共88点。共享原版校准和已有+1回答，新做+1/16、+1/8、+1/4、+1/2，目的是看同一点的效果怎样随剂量变化。

新增2816回答，复用704份+1和24原版。中等剂量有时显露高剂量空答或循环掩盖的主题。同点不同题可不同，离散结果并非普遍单调。全量逐层观察与六栏原文仍保留，不把其余792点写成做过剂量曲线。 [原协议、原始数据及回执](https://github.com/yuxiexiong/acupuncture/tree/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27) · [逐表历史全文](https://github.com/yuxiexiong/acupuncture/blob/45042fb901c8c9bf241900ffedfa3cc02337236f/docs/experiment-history-2026-11-11/chapters/014-layer-dose-survey-toy-v1-2026-10-27.md) · [机器记录](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-dose-survey-toy-v1-2026-10-27/qualitative-pass-r01/coverage-summary.json)

### 015．同一点补齐五档负剂量

继续用同一88点与八题，新增−1/16、−1/8、−1/4、−1/2、−1，和正侧共享干净校准。负侧独立从原模型开始，并不是在正针受损状态上做撤销或修复。

新增3520回答，形成十一栏配对。正负不呈普遍语义镜像。有的点正侧循环、有的点负侧循环，同题也可非单调。正式于10月27日22:00:56至23:34:24完成。3183份EOS结束、337份到128上限是生成统计，不能替代质量评分。 [原协议、原始数据及回执](https://github.com/yuxiexiong/acupuncture/tree/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-negative-dose-survey-toy-v1-2026-10-27) · [逐表历史全文](https://github.com/yuxiexiong/acupuncture/blob/45042fb901c8c9bf241900ffedfa3cc02337236f/docs/experiment-history-2026-11-11/chapters/015-layer-negative-dose-survey-toy-v1-2026-10-27.md) · [机器记录](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-negative-dose-survey-toy-v1-2026-10-27/qualitative-pass-r01/coverage-summary.json)

### 016．Llama旧版十点乘十档合并扫描

原先把每层十点与正负剂量组合在一轮里执行。

用户要求拆开后中止，保留479份回答，其中471干预、8原版。这批没有混入后来正式的独立逐层调查与单点剂量调查，停止前后的路径和计数单独列出。 [原协议、原始数据及回执](https://github.com/yuxiexiong/acupuncture/tree/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/llama31-layer-dose-survey-v1-2026-10-28) · [逐表历史全文](https://github.com/yuxiexiong/acupuncture/blob/45042fb901c8c9bf241900ffedfa3cc02337236f/docs/experiment-history-2026-11-11/chapters/016-llama31-layer-dose-survey-v1-2026-10-28.md) · [机器记录](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/llama31-layer-dose-survey-v1-2026-10-28/user-stop-split-r01/receipt.json)

### 017．Llama独立全层单针调查

Llama-3.1-8B-Instruct的32层各抽十点，单针+1，沿用八题短回答框架。

完成2560干预回答与8原版。与Qwen分别比较自己的原版。本章保留逐层观察、失败和反例，不以跨模型相似文本宣布同源功能位置。 [原协议、原始数据及回执](https://github.com/yuxiexiong/acupuncture/tree/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/llama31-layer-survey-v1-2026-10-28) · [逐表历史全文](https://github.com/yuxiexiong/acupuncture/blob/45042fb901c8c9bf241900ffedfa3cc02337236f/docs/experiment-history-2026-11-11/chapters/017-llama31-layer-survey-v1-2026-10-28.md)

### 018．Llama每层一点正负剂量

每层从原十点中固定取一点，补正负十档所缺条件，复用原版与+1来源。

新增2304回答，复用264来源。该模型两轮正式去重共4872回答。旧中止合并扫描的479份不算入。每层只有一点拥有完整正负剂量。 [原协议、原始数据及回执](https://github.com/yuxiexiong/acupuncture/tree/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/llama31-single-point-dose-survey-v1-2026-10-28) · [逐表历史全文](https://github.com/yuxiexiong/acupuncture/blob/45042fb901c8c9bf241900ffedfa3cc02337236f/docs/experiment-history-2026-11-11/chapters/018-llama31-single-point-dose-survey-v1-2026-10-28.md)

### 019．双针行为与任务能力联合测量

原AB与五个随机对，原24题加24诊断基础情景，31条件。自由回答和候选读数同时记录，分别看风格、任务交付、关系/计算与异常内容。

同一诊断情景分自行处理、给定结论等形式。最高剂量阅读 8/8 与 8/8，计算 3/8 与 8/8，关系 0/8 与 5/8；原版分别 8/8 与 8/8、7/8 与 8/8、7/8 与 8/8。这些配对把可见风格、完成题意与获得正确核心答案分开。48 个配对单元共用情景，31 个条件也复用输入。 [原协议、原始数据及回执](https://github.com/yuxiexiong/acupuncture/tree/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/joint-behavior-capability-v1-2026-10-28) · [逐表历史全文](https://github.com/yuxiexiong/acupuncture/blob/45042fb901c8c9bf241900ffedfa3cc02337236f/docs/experiment-history-2026-11-11/chapters/019-joint-behavior-capability-v1-2026-10-28.md)

### 020．首次导师报告与旧记录核对

把已完成的随机针、剂量和迁移等旧资料整理为展示报告。工作对象是已有Markdown、回答账本和收据。

只做历史材料分析，没有新增模型推理。审计修正了N667与N1741的个别计数表述，明确迁移结构化行为终点未判定，并保留停止的Llama记录边界。此项是报告交付，不是一轮新插针。 [原协议、原始数据及回执](https://github.com/yuxiexiong/acupuncture/tree/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/advisor-report-v1-2026-10-28) · [逐表历史全文](https://github.com/yuxiexiong/acupuncture/blob/45042fb901c8c9bf241900ffedfa3cc02337236f/docs/experiment-history-2026-11-11/chapters/020-advisor-report-v1-2026-10-28.md)

### 021．内部轨迹A：Qwen早层首批

对既有单针回答重放内部计算，2B/4B注入L0–L3，9B注入L0–L5，同时观测模型全部层，追踪差异沿层与生成步的传播。

完成2152正式轨迹和42预检。它们是既有回答的内部重放，不能和原回答数相加作为新样本。完整采集字段、零剂量与撤钩子验收、归档哈希见本章。 [原协议、原始数据及回执](https://github.com/yuxiexiong/acupuncture/tree/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-layer-mechanism-v1-2026-10-28) · [逐表历史全文](https://github.com/yuxiexiong/acupuncture/blob/45042fb901c8c9bf241900ffedfa3cc02337236f/docs/experiment-history-2026-11-11/chapters/021-early-layer-mechanism-v1-2026-10-28.md) · [机器记录](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-layer-mechanism-v1-2026-10-28/archive-r01/verification.json)

### 022．旧回答再分析：输出还随题目变化吗

不重新推理，读取四模型已保存回答，统计同一点八题的不同首token数、前三token前缀数、首步EOS、机械重复和完全相同输出。

早层同题组的唯一首词可大幅减少。4B 的 L0 十点有九点八题全首步终止，9B 一个点在八题上首词全相同，仍有两题重复至上限、六题第二步即停。相同首词不足以判定后续不再依赖输入。 [原协议、原始数据及回执](https://github.com/yuxiexiong/acupuncture/tree/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-layer-question-dependence-v1-2026-10-28) · [逐表历史全文](https://github.com/yuxiexiong/acupuncture/blob/45042fb901c8c9bf241900ffedfa3cc02337236f/docs/experiment-history-2026-11-11/chapters/022-early-layer-question-dependence-v1-2026-10-28.md)

### 023．内部轨迹B：前六层补齐和4B全层

补2B/4B的L4–L5，再补4B的L6–L31。目的是让三个Qwen前六个注入层可比较，并取得4B所有注入层的内部轨迹。

注入层到终层首预测位残差差分逐层单调不减，在 2B、4B、9B、Llama 的 912 条早层配对中分别只有 1、0、41、141 条。这是旧回答轨迹上的实测反例。 [原协议、原始数据及回执](https://github.com/yuxiexiong/acupuncture/tree/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-trace-extension-v1-2026-10-28) · [逐表历史全文](https://github.com/yuxiexiong/acupuncture/blob/45042fb901c8c9bf241900ffedfa3cc02337236f/docs/experiment-history-2026-11-11/chapters/023-layer-trace-extension-v1-2026-10-28.md) · [机器记录](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-trace-extension-v1-2026-10-28/archive-r01/combined-verification.json)

### 024．内部轨迹C：Llama前六层

Llama注入L0–L5，观测全部32层。按既有正式原文进行重放。

全剂量早层 912 个 Llama 干预条件—题目单元中首步结束为零，仍有后续提前停止、模板回声和重复。Qwen3.5-4B 每个早层 80 份 +1 回答，L0–L5 首步停止数依次 79、64、46、0、8、0。模型间生成功能失效可呈现不同外观。 [原协议、原始数据及回执](https://github.com/yuxiexiong/acupuncture/tree/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/llama31-early-layer-trace-v1-2026-10-28) · [逐表历史全文](https://github.com/yuxiexiong/acupuncture/blob/45042fb901c8c9bf241900ffedfa3cc02337236f/docs/experiment-history-2026-11-11/chapters/024-llama31-early-layer-trace-v1-2026-10-28.md) · [机器记录](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/llama31-early-layer-trace-v1-2026-10-28/archive-r01/verification.json)

### 025．早中晚层比较、注入时段、撤针重建和局部替换

开发与新题确认分别比较早L0–3、中L12–15、后L24–27的原生点及共同随机方向。再分full/prefill/最后提示位置/decode等时段，并在可生成条件的第4/16步比较继续扎针、撤针、同文本无针重建，最后做固定局部候选替换。

正式各阶段记录分别为4632、1210、552、3480、1440、576。早层±1异常主要是首步停止。L0/N4146和L2/N5251只改提示前部即可让24/24不交付。N5063的部分异常撤针不恢复而重建恢复。中后层模式不同。四个局部候选未得到特异性修复。预检r02/r03失败及r04通过保留。后来的事实敏感度更正也保留，不能沿用旧“知道但停嘴”读法。 六段总计 11,890 条计划记录，包括 676 条不适用。 [原协议、原始数据及回执](https://github.com/yuxiexiong/acupuncture/tree/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-input-control-v1-2026-10-29) · [逐表历史全文](https://github.com/yuxiexiong/acupuncture/blob/45042fb901c8c9bf241900ffedfa3cc02337236f/docs/experiment-history-2026-11-11/chapters/025-early-input-control-v1-2026-10-29.md)

### 026．阶段一：异常留在哪一种缓存

固定文字与干预历史，分别操作全注意力KV、递推状态和短卷积缓存，区分停止与事实候选读数。不是把撤针后状态视为自动恢复干净。

同文字下比较受针缓存、全干净参照，以及分别换回 KV、递推、卷积、线性层组合。开发/确认共 6,576 条，干净参照两面板均 24/24 跟随事实。失效条件的原受针、换 KV、换递推、换卷积、换线性层的跟随比例（开发/确认）为 .35/.20、.79/.67、.83/.53、.42/.26、.88/.54。前半污染主要答错（.64/.60），后半污染主要未交付（.38/.44）。组间恢复有重叠，无法相加作因果占比。 [原协议、原始数据及回执](https://github.com/yuxiexiong/acupuncture/tree/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-v1-2026-10-29) · [逐表历史全文](https://github.com/yuxiexiong/acupuncture/blob/45042fb901c8c9bf241900ffedfa3cc02337236f/docs/experiment-history-2026-11-11/chapters/026-early-state-localization-v1-2026-10-29.md) · [机器记录](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-v1-2026-10-29/analysis/confirmation-r01.json)

### 027．导师报告扩展与原文查看器

保留旧报告全文和12张图，增加联合测量及早层六阶段过程，并接入可查的原始回答。

只读旧数据，新增8张图。查看器包含四模型18272份去重来源、联合测量3720份及早层11890条计划记录（含676条不适用），这些集合不能作为独立样本相加。当时明确排除仍在运行的缓存定位和公开配方结果，只放其设计。这项截止边界保留。 [原协议、原始数据及回执](https://github.com/yuxiexiong/acupuncture/tree/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/advisor-report-v2-2026-10-29) · [逐表历史全文](https://github.com/yuxiexiong/acupuncture/blob/45042fb901c8c9bf241900ffedfa3cc02337236f/docs/experiment-history-2026-11-11/chapters/027-advisor-report-v2-2026-10-29.md)

### 028．停止时的事实敏感度旧数据检查

在已保存候选评分上检查两种事实版本的答案偏好差是否保留，区分自由回答形态与事实对候选的约束。

零GPU。早层±1的保留比R开发0.03/0.05、确认0.12/0.11，16/16未检出原标准的事实敏感度。这是当时对早层报告的更正来源。没有在本次整理中重新评分。 [原协议、原始数据及回执](https://github.com/yuxiexiong/acupuncture/tree/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-stop-knowledge-readout-v1-2026-10-29) · [逐表历史全文](https://github.com/yuxiexiong/acupuncture/blob/45042fb901c8c9bf241900ffedfa3cc02337236f/docs/experiment-history-2026-11-11/chapters/028-early-stop-knowledge-readout-v1-2026-10-29.md)

### 029．阶段二：全层缓存差分、层组清理与反向污染

继续比较早、中、晚干预和缓存组移植，并同时查看候选评分与完整回答，包含审核、预检与正式部分。

L0 新题完整回答 0/24，清理第 4 组后 7/24；原停止分差上升 20.3，单组清理减少 3.2，全线性层清理减少 16.4。中晚条件未经清理已可交付 96%–100%，结果解读须保留天花板。29,112 次生成和 58,224 条候选评分共用样本。 [原协议、原始数据及回执](https://github.com/yuxiexiong/acupuncture/tree/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-stage2-v2-2026-10-30) · [逐表历史全文](https://github.com/yuxiexiong/acupuncture/blob/45042fb901c8c9bf241900ffedfa3cc02337236f/docs/experiment-history-2026-11-11/chapters/029-early-state-localization-stage2-v2-2026-10-30.md)

### 030．公开配方小题包复现

按公开配方目录固定不同配置，用各配方五题、128-token上限采集，并设置原版、零剂量和恢复等参照。来源版本与配方资格分别保存。

232 条来源经配置去重得 210 组，每组 5 题，1,050 份干预与 120 份共享原版，47 个不同英文提示、10 组解码设置。两分片完成；还缺完整语义判读，不能据采样完备报告“有效率”。 [原协议、原始数据及回执](https://github.com/yuxiexiong/acupuncture/tree/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/x-recipe-reproduction-v1-2026-10-29) · [逐表历史全文](https://github.com/yuxiexiong/acupuncture/blob/45042fb901c8c9bf241900ffedfa3cc02337236f/docs/experiment-history-2026-11-11/chapters/030-x-recipe-reproduction-v1-2026-10-29.md) · [机器记录](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/x-recipe-reproduction-v1-2026-10-29/run-gpu0-r01/receipt.json)

### 046．跨通道计划前的旧随机针审计

检查全层随机调查与十档剂量调查里真正重复过的层、通道、剂量和题目。

复用 4B 最早层十点、同一点正负剂量和 8 份原版，152 份干预。+1 的 80 份中 79 份首步停止，剩下一份答出一个字再停。跨通道重复的是这一现象，后续缓存机制只在有对应干预的条件上判断。 [原协议、原始数据及回执](https://github.com/yuxiexiong/acupuncture/tree/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cross-channel-planning-audit-v1-2026-10-31) · [逐表历史全文](https://github.com/yuxiexiong/acupuncture/blob/45042fb901c8c9bf241900ffedfa3cc02337236f/docs/experiment-history-2026-11-11/chapters/046-cross-channel-planning-audit-v1-2026-10-31.md) · [机器记录](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cross-channel-planning-audit-v1-2026-10-31/result.json)

### 065．NBR：扩大原生行为参照集的历史讨论稿

设计72组事实对加24开放题，共168输入，每输入25条件，覆盖两锚点、两剂量、两时段及随机方向。全部题目和当时目的全文保留。

当时用户要求先自查、不要上卡，新增模型前向、校准、生成和GPU均0。讨论稿不是运行合同或授权，不将计划中的回答数量当实测结果。 [原协议、原始数据及回执](https://github.com/yuxiexiong/acupuncture/tree/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/native-behavior-reference-v1-2026-11-01) · [逐表历史全文](https://github.com/yuxiexiong/acupuncture/blob/45042fb901c8c9bf241900ffedfa3cc02337236f/docs/experiment-history-2026-11-11/chapters/065-native-behavior-reference-v1-2026-11-01.md)

### 090．跨模型F1工程预检

四模型先验收状态导出、形成路径和数值桥接，再决定能否进入跨模型科学比较。

有真实预检记录，但写入1%容差存在未过项，后续科学执行没有完成。A历史×当前与B自然撤针两份合同另列，不能把预检当跨模型机制结果。 [原协议、原始数据及回执](https://github.com/yuxiexiong/acupuncture/tree/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cross-model-foundation-common-v1-2026-11-02) · [逐表历史全文](https://github.com/yuxiexiong/acupuncture/blob/45042fb901c8c9bf241900ffedfa3cc02337236f/docs/experiment-history-2026-11-11/chapters/090-cross-model-foundation-common-v1-2026-11-02.md) · [机器记录](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cross-model-foundation-common-v1-2026-11-02/runs/preflight-r02/summary.json)

### 091．跨模型：固定文字历史与当前作用草案

原合同为未冻结草案，拟区分固定文字历史与当前干预。输入、条件及判读只按原合同记录。

没有以该草案身份确认的正式完成结果，不把后来的其他模型或其他时窗成绩补入。原件保留其未冻结状态。 [原协议、原始数据及回执](https://github.com/yuxiexiong/acupuncture/tree/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cross-model-history-current-v1-2026-11-02) · [逐表历史全文](https://github.com/yuxiexiong/acupuncture/blob/45042fb901c8c9bf241900ffedfa3cc02337236f/docs/experiment-history-2026-11-11/chapters/091-cross-model-history-current-v1-2026-11-02.md)

### 092．跨模型：自然撤针与同文本重建草案

原合同为未冻结草案，拟比较自然撤针及同文本重建。具体操作、范围及门槛全文保留。

没有以该草案身份确认的正式完成结果。后面Qwen/Llama的正式自然撤针项目单独列明，不能把不同目录自动等同。 [原协议、原始数据及回执](https://github.com/yuxiexiong/acupuncture/tree/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cross-model-natural-withdrawal-v1-2026-11-02) · [逐表历史全文](https://github.com/yuxiexiong/acupuncture/blob/45042fb901c8c9bf241900ffedfa3cc02337236f/docs/experiment-history-2026-11-11/chapters/092-cross-model-natural-withdrawal-v1-2026-11-02.md)

### 106．DIV：阈值附近的STOP/CLEAN分裂第零步

按预定剂量和输入寻找同范数但行为分裂的条件，先过够数闸再考虑后续比较。

完成336条，第零步够数闸FAIL，未形成需要的STOP/CLEAN对照，按合同停止。不是理论假设已被否证，也不能把离散剂量结果写成所有通道精确阈值。 [原协议、原始数据及回执](https://github.com/yuxiexiong/acupuncture/tree/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/div01-threshold-split-survey-v1-2026-11-03) · [逐表历史全文](https://github.com/yuxiexiong/acupuncture/blob/45042fb901c8c9bf241900ffedfa3cc02337236f/docs/experiment-history-2026-11-11/chapters/106-div01-threshold-split-survey-v1-2026-11-03.md) · [机器记录](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/div01-threshold-split-survey-v1-2026-11-03/analysis-r01.json)

### 117．WIN-01：形成窗口与恢复关系

在事实和编号任务中比较全窗口、事实前段和后段形成，并测试不同范围恢复。另用跨事实供体检验缓存交换后的答案跟随。

事实W_all恢复R_all10/48，W_post47/48。W_all额外加KV_pre也47/48。编号相应6/48、48/48、48/48。B部分全部KV和全缓存交换各44/44跟供体，全部递推0/48、深层S1/48。B换所有KV位置，不能写成只定位事实段。 [原协议、原始数据及回执](https://github.com/yuxiexiong/acupuncture/tree/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/window-recovery-win01-v1-2026-11-04) · [逐表历史全文](https://github.com/yuxiexiong/acupuncture/blob/45042fb901c8c9bf241900ffedfa3cc02337236f/docs/experiment-history-2026-11-11/chapters/117-window-recovery-win01-v1-2026-11-04.md) · [机器记录](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/window-recovery-win01-v1-2026-11-04/runs/formal-r01/verification.json)

### 118．WIN-02：预留条件上的窗口预测

将WIN中的窗口与条件性恢复关系放到预留针条件，预先登记M及P4/P5等预测。

跨11月4日至5日完成。关系M四个有正向余量格救回11/11、13/13、27/28、38/38，另四格天花板。P4未获支持，P5部分失败，若干条被改坏也保留。没有将有限恢复关系写成统一损伤机制。 [原协议、原始数据及回执](https://github.com/yuxiexiong/acupuncture/tree/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/window-prediction-win02-v1-2026-11-04) · [逐表历史全文](https://github.com/yuxiexiong/acupuncture/blob/45042fb901c8c9bf241900ffedfa3cc02337236f/docs/experiment-history-2026-11-11/chapters/118-window-prediction-win02-v1-2026-11-04.md) · [机器记录](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/window-prediction-win02-v1-2026-11-04/runs/formal-r01/verification.json)

### 121．KVC：补入前段KV的供体事实

固定恢复背景，替换前段KV的供体事实身份，用同事实与异事实供体区分答案随谁变化。

L3/N4146/R0的M_other供体事实43/42/43，各44。B_pre41/44，M_same接收者事实42–44/44。实际差异KV从事实词起至b。22对已见题。没有测原写入读取链的共同端点。 [原协议、原始数据及回执](https://github.com/yuxiexiong/acupuncture/tree/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/kvpre-content-kvc01-v1-2026-11-05) · [逐表历史全文](https://github.com/yuxiexiong/acupuncture/blob/45042fb901c8c9bf241900ffedfa3cc02337236f/docs/experiment-history-2026-11-11/chapters/121-kvpre-content-kvc01-v1-2026-11-05.md) · [机器记录](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/kvpre-content-kvc01-v1-2026-11-05/runs/formal-r01/verification.json)

### 123．WIN协议与旧输出复核

读取384条旧输出和协议参数，对比S_deep与R_all以及生成上限和施针范围。

L0/W_post事实S_deep16/48、R_all47/48，编号均48/48。事实S_deep32/48到128上限，编号四臂都在17token内终止。没有重跑共同协议，后续WPC只算设计。 [原协议、原始数据及回执](https://github.com/yuxiexiong/acupuncture/tree/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/window-protocol-audit-v1-2026-11-05) · [逐表历史全文](https://github.com/yuxiexiong/acupuncture/blob/45042fb901c8c9bf241900ffedfa3cc02337236f/docs/experiment-history-2026-11-11/chapters/123-window-protocol-audit-v1-2026-11-05.md)

### Laya 接口审计（2026-11-09）

在 Laya Studio 的公开实现中抽取激活干预的 hook，用 CPU 合成张量验收。三维张量中指定位置产生预期变化，其他返回分量与原输入保持，异常路径清理 hook。二维或末维不一致会静默跳过。公开 smoke 用例使用 FakeBackend。该记录只约束实现可行性，在真实 Laya 权重、实际后端及独立任务上的调用、有效扰动与收益仍缺直接测量。[原检查记录](https://github.com/yuxiexiong/acupuncture/blob/e5c9fe2153a6e773b8475f708c30fd060e3087db/docs/literature/laya-intervention-open-source-audit-2026-11-09.zh-CN.md)

### 复核深度

本次另从原始文件读出 013、014、015、017、018 五次正式调查的每份 JSON，分别有 7,064、2,816、3,520、2,568、2,304 个模型—条件—题目记录，各批内无重复，共 18,272 份。以生成长度为一且终止原因为 EOS 逐条复算，013 的 L0 正剂量每模型 80 份，2B/4B/9B 分别为 49/79/45 份首步终止。另从 003 的 1,400 条逐题评分重算干预前后对错转移，四任务依次对变错 480/60/88/49，错变对 97/6/0/0，与原配对审计一致。

本次从 Git 对象另读 001 的停止与输入检查、002 中止归档、003 分数、005 十候选汇总、006 阶段门、007 回执、013–016 覆盖与停止、021/023/024 轨迹验收、025 开发选择、026 确认计数、030 分片回执及 046 结果。其余按原协议、原报告、历史证据清单核对。复核未重新加载模型、复跑推理、重标开放回答或重建远端张量。
