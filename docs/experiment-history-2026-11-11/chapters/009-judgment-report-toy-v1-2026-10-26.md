# 009．判断内容与输出标签的分离诊断

[返回总时间线](../README.zh-CN.md)

**时间定位**：版本/记录日期 2026-10-26；未从所选收据确定完整运行起止，不据目录名补写时刻。

**当时的目的与设计**

计划用自行比较/已给答案、内容/标签等条件区分旧双针损伤及C05/C01修复的作用位置。

**实际过程、结果与后来更正**

合同、代码和CPU验收已经准备，正式模型运行暂停。这里没有新模型实验结果；其完整历史设计保留，不把它混入十候选已完成结果。

**来源身份**：`judgment-report-toy-v1-2026-10-26`；本章主体来源提交 `7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8`。下方原文中的状态是各文件写作时的状态，不能把早期“尚未运行”覆盖后期正式收据，也不能将后期结果倒填进早期设计。


## 原设计、执行过程、结果与更正全文

以下按“设计与题目 → 工程/执行记录 → 结果/更正 → 其他历史说明”组织；同类内没有可靠时间时保留路径顺序，不冒充严格先后。正文未删段；仅为本章节重排标题层级、把相对链接指向固定提交。原始字节另外完整保存。

### 原件 1：Acupuncture：答案判断与答案报告的最小区分合同

原路径：`experiments/judgment-report-toy-v1-2026-10-26/CONTRACT.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/judgment-report-toy-v1-2026-10-26/CONTRACT.zh-CN.md) · [单独阅读副本](../library/723bc5cd7485a75f.md)；SHA-256：`723bc5cd7485a75f8d1d4c9dff95d811322d13a7f42ff3a8a55d986ba5ec4d24`。

---

#### Acupuncture：答案判断与答案报告的最小区分合同

2026-10-26。状态：准备与CPU验收；**正式实验未获启动授权**。用户原话：“同意，写合同代码去推进吧，停在正式实验开跑前”。

##### Material Passport

- Origin Skill / Mode：academic-research-suite / experiment-agent plan；Ponytail full 用于最小实现。
- Version：judgment-report-toy-v1-2026-10-26。
- Evidence：首轮 `validate-parallel` 已完成；本轮是结果驱动的新诊断，尚无模型结果。
- 实现身份：`contract.json`、题目、代码、测试和前序依赖由 `freeze.json` 绑定。

##### 1. 只回答什么

两针后的错误，是否依赖答案的内容，或答案的标签／显示位置？需要自行比较时的损伤，是否不同于已经给出正确内容、只需报告时的损伤？第19和23层的局部修复与反向重现，是否也呈现这些依赖？

主候选 C05 为零起始 L19 attention 的提示最后位置；比较候选 C01 为 L23 attention 同位置。二者都是开发集选出的候选，C01不是阴性对照。不找新层、头、神经元、下游读出器，不组合修复两处。保持两针，恢复一个模块的贡献；反方向在原版中引入相应贡献。保留同位置、同维度、同改变量范数的随机替换对照。

**与原四步合同的关系：** 原步骤1拆针、2梯度筛选、3十候选真实替换均已完成；步骤4具体功能解释与新题确认尚未开始。首轮正确率没有候选通过全部四项双向比较，连续分数信号不能代替该科学结论。原合同允许零解释及停止。本轮是用户另行同意、针对修复与重现不一致及标签偏置线索的有限追加诊断，不表示原步骤3已经通过，也不改原验收门槛。原确认64题与功能确认16对保持未运行。

本轮不是旧合同的 `function-dev` 或 `confirm` 阶段，也不把双卡完成收据改写为旧单卡收据。通过原 `parallel_validate.verify_merged` 接入真实前序。本轮缺少独立下游读出关系和内容供体因果检验，结论限于**局部干预效应的标签／任务需求依赖**，不能宣布找到完整根因、天然功能区或“前额叶”的大小。

##### 2. 为什么这样拆

已有32道MMLU中，原版选D有9次，两针后26次；第23层修复净增9题，其中6题恢复原本会做的题、3题是原版本来就做错的题。这是已见开发材料中的线索，不是本轮确认结果。

| 材料 | 具体做法 | 基础样本数／变体数 |
|---|---|---|
| 原MMLU开发题 | 全32题，不按输赢筛选。仅把最后一道题的四个选项循环轮换0、1、2、3位；题干和少样本示例逐字保留。每个正确内容恰好出现在A、B、C、D各一次。 | 32／128 |
| 简单比较任务 | 16组四只盒子及不同整数数量，唯一最大值。版本一问“哪只最多”；版本二直接给正确盒子的名称，要求报告同一盒子。两版本都做四轮选项轮换。 | 16／128 |

共48个基础单位、256个输入变体，每候选完整跑256变体×6条件。不新增独立确认集；不把256当独立样本数。功能任务只使用“比较”一个任务族，固定种子20261026。给出的答案是内容而非字母，故仍需内容到标签映射。

选项循环重排同时改变字母关联和显示顺序，**不能区分偏爱D与偏爱最后一项**。已给答案版本仍需阅读、提取与映射，而且提示显著性和难度不同；需求交互不能独自证明某处专门负责比较。数据不含已发现的选项位置引用；若有歧义则保留并记录，不能悄悄排除。

##### 3. 固定设置

- Qwen3.5-4B，revision `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`；原始路径、两处权重哈希及PyTorch/Transformers版本见JSON合同。
- BF16、eager、batch=1、每worker 4线程、确定性计算；每次前向重算状态、关闭cache。没有训练、永久权重修改、反向传播或长生成。
- B=L13/N7956负向、A=L14/N8949正向，dose=1。复用旧 `RootEngine`、原生通道加法、评分与替换，不改旧冻结文件。
- **每基础题只用原版“需判断、轮换0”校准参考尺度。** 该题所有轮换、需求与干预条件共享这两个数；两worker各自重算相同参考。避免因换提示重新调针而混淆问题。
- 原始参考校准和当前输入身份分开保存；不把参考token哈希冒充当前输入。每次真实评分另保存实际token哈希、长度、两针写入和替换审计。
- 四选项按完整的单token标签A–D原始loglikelihood评分；确定性并列取首索引。CPU分词验收及未来模型加载后均检查标签唯一、单token且共用同一前缀。无自然语言答案解析。
- 两候选仍用首轮各自的匹配随机种子：C05=20261031，C01=20261027；BF16范数匹配容差仍为3%。

##### 4. 条件与必须保存的读数

每候选恰好六条件：原版、AB、保留AB的局部修复、原版中的反向重现、匹配随机修复、匹配随机重现。两针覆盖评分输入；修复不允许关闭两针，只改变提示最后位置的被测模块输出贡献，不替换整层残差或源MLP。

保存四个选项的分数、正确性、正确项相对最强错误项的优势、预测标签、映射回原始内容的身份及全部技术审计。三个面板分别报告：MMLU、需比较、已给答案。

1. 正确率为任务主读数；连续优势为诊断。保留四个原对比：修复−AB、修复−随机修复、原版−重现、随机重现−重现。
2. 每题跨四旋转的“始终同一内容”比例与“始终同一标签／槽位”比例，各条件全部报告；另报A–D分布。AB−原版的D比例给配对区间。其余一致性率当前为描述性读数，不伪装成已做区间检验。
3. 功能任务按基础题计算“需比较−已给答案”的损伤差、修复差、重现差及匹配对照差，分别给正确率与连续优势的区间。
4. 逐题拆账：原版对→AB错→修复对；原版和AB都错→修复对；修复新造成的错误；重现造成的错误与新改善。使用全量固定分母，不挑救回的题宣称成功。净正确率相同不等于逐题没变化。

每基础题先平均四旋转，再按32或16个基础单位进行10,000次配对bootstrap，种子20261026，描述性95%区间。不跨面板混合，不做独立token检验，不宣称多重比较已控制；区间含零表示证据不足，不是等价或不存在路径。

##### 5. 结果如何决定后续

- **标签／槽位依赖线索：** AB相对原版更固定于某标签／槽位、内容随轮换改变；候选修复、反向重现及匹配对照决定该局部效应是否也改变这种依赖。不能把仅有D率上升叫作全部损伤的根因。
- **任务需求依赖线索：** 需比较与已给答案的配对效应不同；优先看正确率交互，同时列原版、AB及所有条件原始值。不能用“一边显著、另一边不显著”替代差值检验。
- 两条线索可同时成立。正确率四项比较均为正且其95%区间下界均大于0时，只称该面板上的探索性双向任务证据；仅连续读数成立不称能力恢复。
- 若简单功能任务任一需求的原版正确率低于75%，标记任务可读性不足；若AB在两需求上均不高于25%，标记共同地板风险。仍完整测量、保留数据，需求差异可能无法区分，不临时加题、换任务或减剂量。
- 修复有效而重现证据不足，保留为修复线索；不要自动称“补偿”或“原损伤路径”。两候选都无支持，也如实报告，不扩大搜索预算。
- 不自动启动9B、2B、功能区边界扫描或大Benchmark。先用本轮结果判断是否值得进一步建立独立内容和下游读出预测。

##### 6. 执行、成本和停止点

代码准备支持两卡：C05固定GPU0，C01固定GPU1，每卡一个模型worker，各256变体。两者独立输出，不竞争写文件。受机器占用限制不能按分配启动时等待，不抢占其他任务；本轮没有自动调度器或自动启动监控。

沿用逐标签评分，每候选正式10,240次前向，加48次基础题参考校准；初始运行检查另含1次参考校准、4次clean评分前向和8次恒等替换前向，共13次。两候选合计**20,602次前向**，其中校准98次；没有反向或生成。题目—候选—条件单元为3,072，不能用它替代前向计数或ETA。

本轮不启动模型测速，因此不报假精确ETA。CPU验收记录输入长度、现成环境、GPU占用和磁盘；以后获准开跑时，根据首批真实进度更新ETA，不能把32题旋转当128独立原题计成本或证据。

本次交付停在：固定数据、合同、代码冻结、本地与服务器CPU测试、分词及依赖验收。**没有加载成品模型，没有运行上述13次初始检查，更没有正式采集。** `authorization.prepare.json`明确为准备权限；正式`run`必须同时给`--execute`和另存的新用户授权（绑定本轮freeze），旧授权无法复用。

任何技术失败保存错误、部分逐题输出、时间和版本；新尝试换目录，不原地续写。无显著效应、比较题不会做或地板效应属于科学结果，不能当bug改实验。完整性验收要求候选各256题、六条件、来源哈希与数据因素一致、钩子移除、权重恢复核验通过。原首轮证据及旧协议保持原样。

---

### 原件 2：追加诊断准备记录

原路径：`experiments/judgment-report-toy-v1-2026-10-26/EXECUTION.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/judgment-report-toy-v1-2026-10-26/EXECUTION.zh-CN.md) · [单独阅读副本](../library/b5b93ce3ed77302b.md)；SHA-256：`b5b93ce3ed77302b8022223f43d97ed21fcc4c6e088112fef0cc5926292dd870`。

---

#### 追加诊断准备记录

2026-10-26，北京时间17:17前后。**代码、合同与CPU验收已完成，停在正式实验开跑前。** 没有加载Qwen模型，没有模型预检、正式逐题记录或GPU计时结果。

##### 原来走到哪一步

原根因合同分四步：1拆针、2内部筛选、3十候选真实修复/重现、4具体功能解释及新题确认。前三步均已完成，第四步尚未开始。首轮执行完整性通过，但没有候选的正确率同时通过四项双向比较；连续分数的线索不能替代任务正确率，更不能直接命名功能区。原合同允许零解释及停止。

本轮是用户批准的有限追加诊断，单独版本，不改原判据、不改旧收据，也不把它冒充原第四步。依据是修复与重现不一致，以及答案标签偏置线索。

##### 准备了什么

- 固定C05/L19 attention及比较候选C01/L23 attention，均只替换提示最后位置的贡献；复用首轮模型、两针、原评分与匹配对照。
- 32道MMLU各四次选项轮换；16组比较题各含需判断/已给答案两个版本及四次轮换。共48个基础单位、256变体，每候选六条件。
- 每基础题固定参考尺度；保存原始选项分数、内容与标签身份、修复/重现逐题变化及完整干预审计。
- 代码具有新授权拦截、冻结校验、失败保全和禁止原地续跑；支持以后获准时每卡一个候选。没有后台队列或自动开跑。

完整设计见[合同](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/judgment-report-toy-v1-2026-10-26/CONTRACT.zh-CN.md)，之后的运行方式见[RUNBOOK](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/judgment-report-toy-v1-2026-10-26/RUNBOOK.zh-CN.md)。

##### 实际验收

| 检查 | 结果 |
|---|---|
| 服务器CPU测试 | 15/15通过，零跳过；包括微型合成网络上的真实钩子、针保持开启、位置与范数、异常清理、记录保全与授权拦截 |
| 前序证据 | 原`validate-parallel`及依赖通过原核验器检查，未改写任何旧证据 |
| 数据 | 48基础单位、256变体，来源与轮换规则核验通过 |
| CPU分词 | 全256输入的四个标签均为不同单token、共用同前缀；前缀80—1649 token，中位184 |
| 本地/远端冻结 | 两端通过，SHA-256 `985788b3a1a72762093e7c4bf07d7f08ebc8960818c6c968cb3b86d28f40ca0c` |
| 成品模型验证 | 未运行；CPU测试不替代真实模型检查 |

证据：[准备收据](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/judgment-report-toy-v1-2026-10-26/readiness/prepare-receipt.json)、[服务器CPU测试](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/judgment-report-toy-v1-2026-10-26/readiness/remote-cpu-tests.log)、[远端冻结及分词检查](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/judgment-report-toy-v1-2026-10-26/readiness/remote-freeze-tokenizer-check.log)。

##### 资源与停止点

只读快照中，两张H20均被其他进程占用：GPU0进程1579923，GPU1进程1579924，各约15.9 GiB显存。未干预这些进程，未预留GPU。因此目前是**部署及CPU准备完成**，不能称两张卡空闲或成品模型已验收。

可用空间：工作盘135.03 GiB；模型盘和`/tmp`所在文件系统43.65 GiB；本地归档盘877.38 GiB。本轮准备文件约1 MiB，无模型下载和长生成需求，当前准备空间充足；正式运行前按当时剩余量重查。

正式计划两候选共20,602次前向（含校准与起步检查），实际模型耗时尚未测量。不开模型测速，不把CPU时间报成正式ETA。获新授权且指定GPU空闲后，才做起步模型检查并据真实进度估时。

用户本轮只批准“写合同代码去推进，停在正式实验开跑前”。`authorization.prepare.json`明确禁止模型执行，正式运行须另有绑定本轮freeze的新授权。当前不存在正式输出目录，也没有启动或恢复半小时监控。

---

### 原件 3：准备与运行说明

原路径：`experiments/judgment-report-toy-v1-2026-10-26/RUNBOOK.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/judgment-report-toy-v1-2026-10-26/RUNBOOK.zh-CN.md) · [单独阅读副本](../library/c5ce04c4d1de2808.md)；SHA-256：`c5ce04c4d1de28083aad5a1bcb2f3d6121cf154857a52fb19dadcff54fe50fef`。

---

#### 准备与运行说明

本轮目前只允许准备与CPU验收。未给出正式运行授权；以下运行命令是供之后使用的说明，**本次不执行**。

##### CPU准备

在本目录执行，均不加载成品模型：

```sh
python3 task_data.py verify
python3 -m unittest discover -s . -p 'test_*.py' -v
python3 experiment.py freeze
python3 experiment.py check
```

freeze只能在全部代码审查完成后生成一次，已有freeze不可覆盖。CPU测试中的微型合成网络用于检验真实钩子，不能称成品模型预检。

服务器现成解释器为`/workspace/acupuncture/.venv-bench/bin/python`。在相同仓库相对目录使用它执行测试及：

```sh
/workspace/acupuncture/.venv-bench/bin/python experiment.py check --tokenizer
```

该命令只读分词器、不读成品模型权重、不调用模型前向。前序`validate-parallel`通过原扩展核验；旧冻结依赖不得覆盖。如有哈希差异，先报告准确文件，再处理。

##### 以后获得正式授权时

另存`launch-authorization-r01.json`，记录实际用户指令与时间，不预填授权。必要字段：`status=authorized`、本轮`experiment`、当前`freeze_sha256`、`candidate_ids=[C05,C01]`、`maximum_model_workers=2`、`user_instruction`、`granted_at`。准备授权或旧实验授权会在加载模型前拒绝。

确认两张卡空闲后，从两个独立终端启动；日志放在输出目录外，记录真实退出码。不启动别的实验或抢占其他作业。

```sh
/workspace/acupuncture/.venv-bench/bin/python experiment.py run --candidate C05 --device cuda:0 --output runs/r01-C05 --authorization launch-authorization-r01.json --execute
/workspace/acupuncture/.venv-bench/bin/python experiment.py run --candidate C01 --device cuda:1 --output runs/r01-C01 --authorization launch-authorization-r01.json --execute
```

输出目录必须不存在；没有resume。每卡开始时做一次恒等替换检验，然后完整跑256个变体。每个变体保存六条件、参考/当前输入身份、实际干预审计；失败留下原目录。

完成后分别核验：

```sh
/workspace/acupuncture/.venv-bench/bin/python experiment.py verify-run --output runs/r01-C05
/workspace/acupuncture/.venv-bench/bin/python experiment.py verify-run --output runs/r01-C01
```

要求两个进程正常退出、两个receipt completed、各256个逐题文件、各summary有效、模型权重与钩子检查通过。不要将本轮收据作为旧function-dev/confirm收据输入。后续解释、独立确认和其他模型实验另讨论。

---


## 时间、运行与停止收据索引

下面是所收集JSON的原有时间字段与状态，不把预计结束时间当实际完成时间。未列时间的文件仍有原件链接。完整JSON全部保存在原文归档，不能以此索引中的标量代替完整嵌套内容。

| 原件 | 原记录状态/阶段 | 原时间字段（原时区） |
|---|---|---|
| [readiness/prepare-receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/judgment-report-toy-v1-2026-10-26/readiness/prepare-receipt.json) | {"status": "cpu_ready_formal_run_paused", "scope": "Prepare only; no pretrained model load or forward; synthetic CPU hook tests only"} | {"resource_snapshot_at": "2026-10-26T09:16:55.289020+00:00", "recorded_at": "2026-10-26T09:22:47.521523+00:00"} |

## 全部原始资产入口

本目录在固定提交下共有18个跟踪文件，包含代码、原回答、失败、收据和压缩证据；文件数不是样本数。[逐文件完整账本](../assets/009-judgment-report-toy-v1-2026-10-26.tsv) · [原目录](https://github.com/yuxiexiong/acupuncture/tree/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/judgment-report-toy-v1-2026-10-26)。未复制模型权重、环境或凭据。
