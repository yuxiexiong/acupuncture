# 024．内部轨迹C：Llama前六层

[返回总时间线](../README.zh-CN.md)

**时间定位**：版本/记录日期 2026-10-28；未从所选收据确定完整运行起止，不据目录名补写时刻。

**当时的目的与设计**

Llama注入L0–L5，观测全部32层；按既有正式原文进行重放。

**实际过程、结果与后来更正**

完成920正式轨迹与14预检。A、B、C三批正式轨迹合计7632，属于18272份单针/剂量回答的子集，而非额外7632道新题。

**来源身份**：`llama31-early-layer-trace-v1-2026-10-28`；本章主体来源提交 `7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8`。下方原文中的状态是各文件写作时的状态，不能把早期“尚未运行”覆盖后期正式收据，也不能将后期结果倒填进早期设计。


## 原设计、执行过程、结果与更正全文

以下按“设计与题目 → 工程/执行记录 → 结果/更正 → 其他历史说明”组织；同类内没有可靠时间时保留路径顺序，不冒充严格先后。正文未删段；仅为本章节重排标题层级、把相对链接指向固定提交。原始字节另外完整保存。

### 原件 1：Llama 3.1 8B 前六层内部轨迹采集合同

原路径：`experiments/llama31-early-layer-trace-v1-2026-10-28/CONTRACT.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/llama31-early-layer-trace-v1-2026-10-28/CONTRACT.zh-CN.md) · [单独阅读副本](../library/0647552e93461362.md)；SHA-256：`0647552e934613627afb347c9b679df9041bb39522a7752dfbc1176a469739c9`。

---

#### Llama 3.1 8B 前六层内部轨迹采集合同

日期：2026-10-28，北京时间。实验：`llama31-early-layer-trace-v1-2026-10-28`。机器范围和源 SHA 见 [contract.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/llama31-early-layer-trace-v1-2026-10-28/contract.json)。本合同定义已授权范围和验收条件，不表示测试或采集已经完成。

##### 1. 授权与执行顺序

用户要求给 Llama 前六个 layer 做当前同类内部轨迹实验，写代码、合同、测试后直接挂服务器，**排在 Qwen 4B 全层采集之后**。因此按 CPU 验收 → 等前驱完整完成和资源释放 → Llama 自身有限 GPU 预检 → 两 worker 全部通过后自动正式采集执行，无需再次请求启动确认。

直接前驱固定为 `layer-trace-extension-v1-2026-10-28/execution-r01`，须完成全部 4,560 条（包括最后的 4B L6–L31）。授权绑定前驱 execution/freeze 哈希与父进程 PID/start_ticks；启动须核对前驱 completed、记录数齐全、两阶段共六个 worker 的成功收据/退出码和身份、绑定进程已退出，以及 GPU 0/1 无计算进程。不打断、暂停或挤占当前任务；空闲显存不能替代完整验收。队列在服务器独立后台运行。

##### 2. 来源、覆盖与不重复计数

唯一来源为已完成的两个独立实验：`llama31-layer-survey-v1-2026-10-28` 的每层十点 +1，以及 `llama31-single-point-dose-survey-v1-2026-10-28` 的每层原一点正负五档。两份 `delivery-r01/all.records.jsonl` 各 2,568 行，合并为 4,872 个唯一身份、264 次相同来源引用；保留全部来源引用、原 record/receipt/metadata 哈希。**已停止的旧十点×十剂量合并 partial 不作为来源。**

按 `(model_id, layer, channel, dose, question_id)` 去重，重复输出 token、context 或校准不一致即失败。从完整来源中仅选 L0–L5，外加八份唯一原版：

| 范围 | 来源记录 |
|---|---:|
| 六层，每层十个旧通道 +1 × 原八题 | 480 |
| 六层，每层原剂量点其余四档低正＋五档负剂量 × 原八题 | 432 |
| 八份共享原版，仅采集一套正式内部轨迹 | 8 |
| 合计 | **920** |

每层为 19 个通道—剂量条件、152 条回答，不把十个通道扩成十档剂量。所有条件沿用旧题、旧通道、旧剂量和旧校准，不按回答效果重新选点。排序 `(layer, channel, dose)` 后条件交替分到两卡，同条件八题在同卡，原版归 shard 0；两片应为 464/456 条，历史分片身份另存。

本轮通过重放旧输出，首次采集这些 Llama 条件的内部轨迹；不重启原调查、不把预检当新增科学样本、不覆盖旧原文或重复采集已经存在的正式内部记录。920 条来源各有实际分支和同前缀无针分支，共 1,840 条正式生成流；校准前向及验证开销另记。

##### 3. 固定模型与原生成路径

模型为 `meta-llama/Llama-3.1-8B-Instruct@0e9e39f249a16976918f6564b8830bc894c89659`，model_id 为 `llama31-8b-instruct`；32 层、hidden 4,096、MLP intermediate 14,336，使用原已核验资产目录及依赖版本。

复用 Llama 原引擎、native chat template 与固定日期 `26 Oct 2026`、单次 BOS 128000、EOS 128001/128008/128009、pad 128009；thinking 不适用。BF16/eager、greedy、batch 1、每 worker 四 CPU 线程、cache 开启、最多 128 新 token。自然 EOS 保留，不补 token、不续写、不因语义结果重试；不得套用 Qwen 模板、停止 ID 或 hybrid-cache 假设。

干预仍在 gated MLP 的 `down_proj` 前，原通道加 `dose × m / ||W_down[:, channel]||₂`，`m` 为原清洁 prompt 层输出 token L2 中位数（排除首 token）。每档从原 double 比例独立转 BF16；覆盖原 prompt 及全部实际 decode 输入位置，不用生成前缀重新校准。输出 token、prompt/context、校准尺度、列范数和实际 BF16 偏移须逐条对回旧来源。

##### 4. 记录整个生成过程的可比较读数

注入仅限 L0–L5，观察覆盖 **全部 32 层** 的 self-attention 输出、MLP 输出、层末残差，共 96 个组件位置。记录全部 prompt 位置和实际缓存 decode 输入位置；EOS 或上限结束后不人为追加最后 token 的前向。

实际分支按原路径自由生成；无针分支使用独立 cache、强制接收实际分支已选 token，在强制选择前保存原始 clean logits。它是“相同历史下撤针会怎样预测”的参照，不是原版自由生成回答，不能用分叉的自由回答按 token 序号直接相减。

逐位置保存清洁/干预 L2、差分 L2、相对差分、余弦；零范数导致的未定义值显式记录。逐生成步保存双方 top 候选及并集交叉分数、EOS logits/logprob、最高非停止候选、停止优势、实际 token、前缀哈希和首次预测分叉。停止优势为 `max(EOS logits) − max(non-EOS logits)`。保留旧原版及干预原文、来源链接和轨迹身份，使图上记录可返回对应文本。

复用现有压缩轨迹格式，在 GPU 汇总后集中传回，不保存全部高维激活向量。这里的“整个过程”是完整时间/层/组件覆盖的摘要及逐步预测证据，不等于完整计算图或已经证明的因果链。

##### 5. CPU 测试与 Llama 自身 GPU 预检

CPU 验收须检查来源及冲突拒绝、920 条范围、464/456 分片、14 个确定性预检身份、原生 Llama 引擎适配、组件/前缀观察、冻结/授权/前驱绑定、GPU 占用等待和失败阻断。所有需要的服务器 CPU 检查须零失败、零错误、零跳过。CPU 通过不代表实际模型轨迹可用。

Llama 的 GPU 预检只能在前驱结束及 GPU 释放后进行，**不能继承 Qwen 的 GPU 通过结论**。两 worker 各七个观察案例：Q01 原版、四个不同既有代表（最短/EOS、最长正侧、负侧、低正侧）、Q01 零剂量、Q01 撤针恢复。四代表从各自执行 shard 按固定排序选取，精确身份写入 source-manifest；不存在单 EOS 时保留选最短输出的替代事实。

前五案例再各做一次关闭组件观察器的重放；该重放仍用只读 logits 捕获来比较逐步哈希。每 worker `7 × 2 + 5 = 19` 条生成流，共 **14 个观察案例、10 次无组件观察重放、38 条生成流**，均不计入920正式来源分母。

必须验证观察器开关不改 token/logits；原来源精确重放；独立 cache/强制前缀正确；零剂量等于原版、撤针恢复；全层三组件和全部应有位置覆盖；数值有限或零范数未定义明示；同 prompt 注入前组件不变；hook全部撤除且目标权重前后哈希相同。两 worker 完成、exit 0、全部验收通过并保存绑定本轮 freeze 的接受凭证后，才自动开始正式采集。

##### 6. 完成、失败与结论边界

完成须有 920 个唯一来源、全部逐条验收、两正式 worker 完成/exit 0、目标权重和 hook 核验及结果哈希齐全。排队、预检、模型加载、实际/无针生成、保存、终验和归档分别计时。ETA 在自身 GPU 预检前只能是明确标注的外推，预检后更新；不以预估时间作为停止阈值。

任何身份、重放、数值、位置覆盖或退出检查失败则停止本次自身子进程，保留失败和部分结果；不放宽阈值、不静默重试、不覆盖旧目录。修正版需要单独版本和重新冻结/验收，不影响前驱或其他人的作业。本合同不授权修复/反向替换、随机新方向、新题、新点、新剂量、其他模型、训练或静态权重编辑。

L0–L5 是统一观察窗口，不预设天然功能边界。轨迹、差分、停止倾向及跨家族相似现象只提供机制线索，不能单独证明根因、人脑式功能分区、跨模型同源区或道德/安全神经元；无共同规律也应完整保留。

---

### 原件 2：Llama 3.1 8B 前六层内部轨迹：执行记录

原路径：`experiments/llama31-early-layer-trace-v1-2026-10-28/EXECUTION.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/llama31-early-layer-trace-v1-2026-10-28/EXECUTION.zh-CN.md) · [单独阅读副本](../library/5d4dce67587ea676.md)；SHA-256：`5d4dce67587ea676a16fa9dee36927ca52bb2662d8f99c107d0a6f8b9a0b1979`。

---

#### Llama 3.1 8B 前六层内部轨迹：执行记录

北京时间 **2026-10-28 05:00** 核验：合同、代码与920条来源已经冻结，服务器 **28/28 CPU测试通过、零失败零错误零跳过**。独立后台队列 **PID2326329** 已挂在Qwen 4B全层任务后，状态为`waiting / predecessor_running`，正式记录0/920。Llama真实GPU预检及正式采集尚未开始。

##### 范围与过程记录

沿用已完成的独立Llama十点调查与单点正负剂量调查，选择 **L0–L5**：每层十个旧通道各+1×八题，另有原剂量点四档低正与五档负剂量×八题，每层152条；六层912条干预，加八份共享原版，合计 **920条**。不复用已停止的旧十点×十剂量合并partial。全部920条原始record、receipt、metadata、模型revision、源freeze和退出码已逐一核验。

每条观察Llama **全部32层、96个组件位置**的attention输出、MLP输出、层末残差；覆盖prompt全部位置及实际decode输入位置。保存清洁/干预范数、差分、相对变化、余弦及每步候选词、EOS竞争、前缀与首次预测分叉。无针参照用独立cache强制相同历史，保留原版自由回答和干预原文的来源关联。

采用与Qwen兼容的压缩轨迹schema，生成和干预则保留Llama原生模板/BOS/EOS及原BF16校准。这里是完整层与时间覆盖的摘要，不保存全部高维向量，也不把观察到的差分写成已确认根因。本次尚未生成Llama轨迹或把新结果接入三维界面。

合同：[CONTRACT.zh-CN.md](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/llama31-early-layer-trace-v1-2026-10-28/CONTRACT.zh-CN.md)；[机器合同](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/llama31-early-layer-trace-v1-2026-10-28/contract.json)；[来源清单与精确预检身份](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/llama31-early-layer-trace-v1-2026-10-28/source-manifest.json)。模型为`meta-llama/Llama-3.1-8B-Instruct@0e9e39f249a16976918f6564b8830bc894c89659`，使用已有核验资产，无新增下载。

##### 最小实现与验收

- [trace_engine.py](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/llama31-early-layer-trace-v1-2026-10-28/trace_engine.py)直接继承原Llama引擎，只复用已有轨迹观察方法；[trace_run.py](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/llama31-early-layer-trace-v1-2026-10-28/trace_run.py)适配Llama原生检查，复用完整worker和结果验收逻辑。
- [source_prepare.py](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/llama31-early-layer-trace-v1-2026-10-28/source_prepare.py)只选择既有来源；[queue_run.py](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/llama31-early-layer-trace-v1-2026-10-28/queue_run.py)复用双卡进程管理，补全前驱完整性和Llama自身预检门禁。未修改正在运行或历史冻结代码。
- 本地28项中21项通过、7项因无torch明确跳过；服务器同28项 **全部通过**，CUDA被屏蔽且`cuda_initialized=false`，没有加载模型或占GPU。证据：[本地收据](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/llama31-early-layer-trace-v1-2026-10-28/readiness/local-cpu-tests-r01.json)、[服务器收据](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/llama31-early-layer-trace-v1-2026-10-28/readiness/cpu-tests-r01.json)、[完整日志](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/llama31-early-layer-trace-v1-2026-10-28/readiness/cpu-tests-r01.log)。
- 检查覆盖920条/464+456分片、来源冲突和旧partial拒绝、原生BOS/EOS、全32层组件、同前缀独立cache、观察器不改logits、零剂量/撤针及异常清理、授权/冻结篡改、前驱失败/失活、GPU等待、预检失败阻断正式和重复运行拒绝。
- 冻结SHA256：`5e635772da1afd588515dbccf8a3837aa73d761b151cf9ca0d0d78c559f557f0`，共57个文件。测试fixture准备问题已说明在[准备记录](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/llama31-early-layer-trace-v1-2026-10-28/readiness/preparation-notes.json)，不属于真实模型实验失败。

##### 排队顺序与启动证据

1. 当前Qwen补齐前六层继续运行。
2. Qwen 4B L6–L31全部完成，追加总数达到4,560；两个阶段共六worker成功退出，前驱父进程退出，GPU0/1无计算进程。
3. Llama自己的双卡GPU预检：每卡七个观察案例＋五次关闭组件观察重放，合计 **14案例、38生成流**。最短历史案例为2 token，没有单token EOS；精确选择已经冻结。
4. 两卡预检全部通过后，自动正式采集 **920记录、1,840生成流**。任何验收失败保留证据并停止本次自身任务，不放宽标准或自行重跑。

直接前驱为`layer-trace-extension-v1-2026-10-28/execution-r01`，PID2295050/start_ticks1136269077，execution SHA `bbdb31eb8d8026d1b2ad972b31ca48dd9a9eb361efdd77f555bc48c2e248663e`。05:00时前驱仍在2B补齐阶段，557/4,560，GPU进程2322619/2322620属于前序采集。

新队列PID **2326329**、PPID **1**、start_ticks1137025527，已脱离SSH/Codex会话；输出目录为`/workspace/acupuncture/experiments/llama31-early-layer-trace-v1-2026-10-28/execution-r01`。证据：[授权](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/llama31-early-layer-trace-v1-2026-10-28/readiness/queue-authorization-r01.json)、[启动收据](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/llama31-early-layer-trace-v1-2026-10-28/readiness/queue-launch-r01.json)、[后台/资源核验](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/llama31-early-layer-trace-v1-2026-10-28/readiness/queue-verified-r01.json)、[排队快照](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/llama31-early-layer-trace-v1-2026-10-28/execution-r01/queue-state.json)。本地快照不是自动刷新的页面。

原半小时监控`acupuncture-3`已经加入本批，继续报告三段状态、ETA、磁盘与负载；A/B完成后仍监控Llama，三段总唯一记录数为 **7,632**。监控只读，不自动重启或清理。

##### ETA与资源

920个来源输出共43,330 token；两片464/456条，输出20,844/22,486 token。旧单分支慢卡耗时约18.42分钟只是历史底座，不是本次内部轨迹实测。

本批含双分支观察、自身预检、加载与终验，暂预留 **追加1–1.5小时**，等待Qwen完成的时间另计；Llama真实GPU预检后按本模型`total_seconds`和输出长度重新估算，不把预算当停止阈值。详见[ETA.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/llama31-early-layer-trace-v1-2026-10-28/ETA.json)。可视化接图与研究分析不计入这段机器队列。

05:00核验工作盘仍约125 GiB可用、系统盘约48 GiB可用；本次复用已有模型和环境，新增主要为压缩轨迹。未删除缓存或结果，未中断现有任务。

---


## 时间、运行与停止收据索引

下面是所收集JSON的原有时间字段与状态，不把预计结束时间当实际完成时间。未列时间的文件仍有原件链接。完整JSON全部保存在原文归档，不能以此索引中的标量代替完整嵌套内容。

| 原件 | 原记录状态/阶段 | 原时间字段（原时区） |
|---|---|---|
| [archive-r01/execution-r01/preflight/llama31-8b-instruct-shard-0/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/llama31-early-layer-trace-v1-2026-10-28/archive-r01/execution-r01/preflight/llama31-8b-instruct-shard-0/receipt.json) | {"status": "completed", "mode": "preflight"} | {"started_utc": "2026-10-28T01:08:40.375541+00:00", "updated_utc": "2026-10-28T01:10:03.366412+00:00", "ended_utc": "2026-10-28T01:10:09.137613+00:00"} |
| [archive-r01/execution-r01/preflight/llama31-8b-instruct-shard-1/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/llama31-early-layer-trace-v1-2026-10-28/archive-r01/execution-r01/preflight/llama31-8b-instruct-shard-1/receipt.json) | {"status": "completed", "mode": "preflight"} | {"started_utc": "2026-10-28T01:08:40.375641+00:00", "updated_utc": "2026-10-28T01:10:03.846130+00:00", "ended_utc": "2026-10-28T01:10:09.760346+00:00"} |
| [archive-r01/execution-r01/survey/llama31-8b-instruct-shard-0/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/llama31-early-layer-trace-v1-2026-10-28/archive-r01/execution-r01/survey/llama31-8b-instruct-shard-0/receipt.json) | {"status": "completed", "mode": "survey"} | {"started_utc": "2026-10-28T01:10:21.509850+00:00", "updated_utc": "2026-10-28T01:49:10.241390+00:00", "ended_utc": "2026-10-28T01:49:15.757113+00:00"} |
| [archive-r01/execution-r01/survey/llama31-8b-instruct-shard-1/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/llama31-early-layer-trace-v1-2026-10-28/archive-r01/execution-r01/survey/llama31-8b-instruct-shard-1/receipt.json) | {"status": "completed", "mode": "survey"} | {"started_utc": "2026-10-28T01:10:21.509932+00:00", "updated_utc": "2026-10-28T01:52:15.956054+00:00", "ended_utc": "2026-10-28T01:52:21.636080+00:00"} |
| [archive-r01/verification.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/llama31-early-layer-trace-v1-2026-10-28/archive-r01/verification.json) | {"status": "verified"} | {"verified_utc": "2026-10-28T06:17:31.602270+00:00"} |
| [readiness/queue-launch-r01.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/llama31-early-layer-trace-v1-2026-10-28/readiness/queue-launch-r01.json) | {} | {"created_utc": "2026-10-27T20:59:40.850480+00:00", "verified_utc": "2026-10-27T20:59:41.350855+00:00"} |

## 全部原始资产入口

本目录在固定提交下共有988个跟踪文件，包含代码、原回答、失败、收据和压缩证据；文件数不是样本数。[逐文件完整账本](../assets/024-llama31-early-layer-trace-v1-2026-10-28.tsv) · [原目录](https://github.com/yuxiexiong/acupuncture/tree/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/llama31-early-layer-trace-v1-2026-10-28)。未复制模型权重、环境或凭据。
