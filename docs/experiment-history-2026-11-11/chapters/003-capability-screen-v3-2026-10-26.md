# 003．四项固定能力面板

[返回总时间线](../README.zh-CN.md)

**时间定位**：已提取运行收据的最早时间锚点（可含预检） 2026-10-26T04:49:13.165415+08:00；不能当作全部子运行起止。

**当时的目的与设计**

把能力检查固定为MMLU、ARC-C、GSM8K和HumanEval，分别比较同一题的原版与双针回答；采用已核验旧结果复用时保留来源。

**实际过程、结果与后来更正**

完成1400对题。选择题分数、数学答案提取、代码pass@1及截断分别报告；本章完整保留各任务分母、结果表与复用说明，不能把严格格式零分解释为所有知识消失。

**来源身份**：`capability-screen-v3-2026-10-26`；本章主体来源提交 `7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8`。下方原文中的状态是各文件写作时的状态，不能把早期“尚未运行”覆盖后期正式收据，也不能将后期结果倒填进早期设计。


## 原设计、执行过程、结果与更正全文

以下按“设计与题目 → 工程/执行记录 → 结果/更正 → 其他历史说明”组织；同类内没有可靠时间时保留路径顺序，不冒充严格先后。正文未删段；仅为本章节重排标题层级、把相对链接指向固定提交。原始字节另外完整保存。

### 原件 1：四项能力小面板：原版与 EVO 对照

原路径：`experiments/capability-screen-v3-2026-10-26/PROTOCOL.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/capability-screen-v3-2026-10-26/PROTOCOL.zh-CN.md) · [单独阅读副本](../library/134cd77f227b8460.md)；SHA-256：`134cd77f227b8460ce37e7266413ac9b9b5d30e83713989fbfeba1591fb4e0c8`。

---

#### 四项能力小面板：原版与 EVO 对照

用户于 2026-10-26 明确要求：数学、代码各扩到 100 题，停止此前全量实验，按小面板重新运行并测量 ETA 和实际用时。此次授权覆盖以下 1,400 对题目；一小时仍为希望达到的量级，不是已经验证的耗时或强停阈值。

| 任务 | 每版题数 | 主评分 |
|---|---:|---|
| MMLU | 1,000 | acc，按原完整测试集的学科题数加权 |
| ARC-Challenge | 200 | acc_norm，完整选项似然按字符数归一化 |
| GSM8K | 100 | strict-match，另报固定 flexible-extract |
| HumanEval | 100 | pass@1，官方测试每份 3 秒 |

每道题原版与 EVO 同题配对，共 2,800 个题目—条件单元。分别报告原版分数、EVO 分数、下降百分点（原版减 EVO，负值保留）和 95% 配对 bootstrap 区间。MMLU 按学科分层抽样并保留完整测试集学科权重；其余任务固定随机抽样。先独立选择题目，再检查旧运行是否已经完成该题，不能根据答案、长短或完成情况选题。

##### 复用与不变项

复用 [v2 的固定模型与推理设置](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/capability-damage-v2-2026-10-26/protocol.json)：Qwen3.5-4B 固定 revision、BF16/eager、实际 forward batch=1、greedy、无聊天模板，GSM8K 最多 2,048 新 token、HumanEval 最多 1,024 新 token。停止 token 和任务停止字符串、few-shot 提示及官方评分规则保持一致。

EVO 仍为动态激活干预：零起始 L14/N8949 +1、L13/N7956 −1；逐题以原版公共提示校准，提示与生成全程注入。没有永久权重修改，也没有新的剂量、位置或机制实验。

仅复用 v2 中完整且两臂均成功的同题记录，必须匹配完整题目内容、源协议、引擎与数值设置，并记录原文件、回执及 SHA-256。保留旧原文，不修改旧输出。未完成记录不当作答错；旧运行按用户要求中断，不能把它称为全量完成，也不能声称已获得被中断进程的最终权重恢复检查。新运行继续执行自己的资产、权重与钩子恢复核验。

##### 执行与计时

两张 H20 对互不重叠的题目分工，每题两臂在同一张卡依次计算。优先执行生成任务，并让两张卡从数学和代码分别开始，以尽早获得两种任务的耗时样本。任务队列与顺序以冻结的 `protocol.json` 和启动回执为准。

ETA 使用各任务已完成的完整配对耗时和未完成数量；显示样本数、截断比例、两卡剩余队列和不确定范围。只有短回答或少数样本时标注为初步估计；不把早结束样本均值当作可靠全程速度，不因到一小时而丢弃慢题。数学和代码各 100 题可能使本轮明显超过一小时。

计时分别记录：新一轮启动到评分完成的实际等待时间、新推理用时、复用旧结果数量，以及复用部分历史计算时间。新一轮墙钟时间不能包装成“所有 1,400 对均从零计算”的性能。

HumanEval 沿用已验证的禁网、非 root、资源受限沙箱与官方测试。CPU 收尾仅在新面板依赖完整时运行；禁止重复启动旧收尾。基础设施失败保留为未完成，不记为模型答错，不自动重试或更改已冻结设置。

##### 证据与状态

本轮题目、抽样与权重见 `panel_manifest.json`；旧结果复用来源见 `reuse_manifest.json`；冻结设置与代码哈希见 `protocol.json`。实际状态以 `worker-0.json`、`worker-1.json`、各输出收据及 CPU 收尾收据为准。旧实验停止证据保存在 v2 的 `user-stop-20261026-r01/`。

抽样成绩不称为官方全量成绩；能力损伤与“evil”行为不是同一个测量。固定面板供日常比较，反复用于调参后属于开发证据。当前报告必须区分准备、运行、完成与复用，只有原文、官方评分及分母核验齐备才发布最终分数。

---

### 原件 2：四项能力小面板最终结果

原路径：`experiments/capability-screen-v3-2026-10-26/RESULTS.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/capability-screen-v3-2026-10-26/RESULTS.zh-CN.md) · [单独阅读副本](../library/4127d88fb059f87e.md)；SHA-256：`4127d88fb059f87e1f8c4a29d344a0639ef95d24a2eefcbf763f4e1a38ed9ff7`。

---

#### 四项能力小面板最终结果

2026-10-26 北京时间 05:29:23，四项原版/EVO 对照及官方 HumanEval 沙箱评分全部完成。1,400 对、2,800 个题目—条件单元齐全，没有基础设施失败。逐题评分、复用来源、冻结文件哈希及新任务的目标权重/钩子恢复检查通过，见[独立审计](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/capability-screen-v3-2026-10-26/validation/final-score-audit.json)。

这轮观察到四项任务表现均明显下降，数学与代码损伤尤其大。它量化了当前干预下的能力损伤；“evil”的行为含义与因果机制仍需单独测量。本轮 EVO 是推理时动态激活干预，没有永久改写模型权重。

##### 最终分数

下降百分点 = 原版分数 − EVO 分数。以下为事前固定英文子集，不是官方全量成绩。

| 任务 | 每版题数 | 原版 | EVO | 下降百分点 | 下降的 95% 配对区间 |
|---|---:|---:|---:|---:|---:|
| MMLU | 1,000 | 67.99% | 29.74% | 38.26 | 34.39–42.08 |
| ARC-Challenge | 200 | 65.00% | 38.00% | 27.00 | 20.00–34.00 |
| GSM8K | 100 | 88.00% | 0.00% | 88.00 | 81.00–94.00 |
| HumanEval | 100 | 53.00% | 4.00% | 49.00 | 39.00–59.00 |

MMLU 覆盖 57 个学科，按原完整测试集各学科题数加权；未加权的正确数为 680/1,000 与 297/1,000。ARC 使用完整选项似然按字符数归一化后的 acc_norm；GSM8K 主指标为 strict-match；HumanEval 每题生成一次，以官方测试计算 pass@1。区间使用固定种子 20261026、10,000 次配对 bootstrap，MMLU 按学科分层并保持原学科权重；审计已复算一致。

配对记录也保留了“原对→改错”和“原错→改对”：MMLU 为 480/97 对，ARC 为 60/6 对，GSM8K 为 88/0 对，HumanEval 为 49/0 对。这说明总体损伤不等于每一道题都变差。各任务分数不汇总为一个未经定义的总分。

##### 解释与诊断

MMLU 与 ARC 直接比较选项似然，不依赖模型生成一个可解析的答案字母。因此，本轮损伤无法仅由自由回答的格式变化解释。数学的固定 flexible-extract 口径同样是 88%→0%，但有限题目上的零分仍不能证明模型内部所有数学推理能力均已消失。

| 诊断 | 原版 | EVO |
|---|---:|---:|
| GSM8K 达到生成上限 | 0/100 | 5/100 |
| GSM8K 主评分解析失败 | 0/100 | 2/100 |
| HumanEval 达到生成上限 | 1/100 | 16/100 |
| HumanEval 测试失败（不含语法错误） | 46/100 | 88/100 |
| HumanEval 语法错误 | 1/100 | 8/100 |

截断与执行分类可能重叠，不能相加。保留全部题目按冻结规则评分，没有删除截断题，也没有把基础设施故障计成模型答错。HumanEval 的 200 次正式执行没有基础设施失败；成功、错误答案、语法错误、超时及隔离五项控制均达到预期结果。

GSM8K 中 9 题曾在本项目历史评测中出现，单列为 7/9→0/9；其余 91 题为 **81/91（89.01%）→0/91**，下降 89.01 个百分点，95% 配对区间 82.42–94.51。这里的“未暴露”只指本项目历史评测未使用，不能排除模型预训练接触过公开题目。

##### 实际耗时与以后预算

| 时间点或环节 | 实测 |
|---|---|
| 启动 | 北京时间 04:49:13 |
| 两路 GPU 均完成 | 05:29:09 |
| 官方执行与最终评分均完成 | 05:29:23 |
| 启动到评分完成 | **40 分 10 秒**（2,409.880 秒） |
| GPU 完成后的 CPU 收尾 | 13.658 秒，其中 HumanEval 6.744 秒、汇总评分 3.076 秒 |

本次新计算 **682 对**，复用旧全量中经过逐文件核验的 **718 对 MMLU**。40 分 10 秒是本次启动后的墙钟时间，包含模型加载、推理和自动评分，不包含此前模型/环境准备及此后的独立审计、归档、GitHub 同步时间。

718 对复用数据的历史日志累计为 551.212 worker 秒，包含配对校准与写回；按本次分片，两卡各约 275.6 秒。把这部分加回现有队列，并保持当前收尾耗时，全部 1,400 对从头计算的参考值为 **44.76 分钟，约 45 分钟**。这是依据实测成本的推算，没有另跑一轮验证。

任务成本可用两卡累计 worker 时间除以 2 来比较，但它不是各阶段真实墙钟时间。完整重新计算的参考成本为 MMLU 6.10、ARC 4.09、GSM8K 16.83、HumanEval 13.85 个双卡等效分钟，包含各任务加载。两卡完成时间相差 7.20 分钟，静态分片的不均衡使实际总等待更长。

以后使用相同 4B、两张 H20、现成环境与相同设置，建议整套预留 **50–60 分钟**。约 55 分钟的预算可分为 MMLU 7 分钟、ARC 5 分钟、数学 20 分钟、代码 17 分钟、自动收尾及队列不均衡余量 6 分钟。该分配仅用于排期，不改变冻结题数或输出上限。新的干预若使生成更长、或服务器资源变化，耗时仍可能超过一小时；换成 9B 或单卡须重新估时。

完整计时与推算依据见 [timing-summary.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/capability-screen-v3-2026-10-26/timing-summary.json)。此前 RUN_STATUS 中的 ETA 保留为历史预测，最终实际完成时间以本报告为准。

##### 协议、完整性与证据

源模型为 `Qwen/Qwen3.5-4B@851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`。BF16/eager、实际 forward batch=1、greedy、few-shot 提示、停止规则及评分保持冻结设置；数学/代码上限分别为 2,048/1,024 新 token。EVO 为零起始 L14/N8949 +1、L13/N7956 −1，在 down_proj 输入逐题按原版公共提示残差尺度校准，并在提示与生成全程注入。完整定义见[协议](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/capability-screen-v3-2026-10-26/PROTOCOL.zh-CN.md)与 [protocol.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/capability-screen-v3-2026-10-26/protocol.json)。

先独立抽样，再检查旧记录是否可复用，没有按答案或已完成顺序挑选题目。新 8 份任务收据均完成，目标 down_proj 权重前后哈希一致，钩子已移除；这不是对每个模型张量重新计算哈希的全模型证明。718 对复用记录与旧文件逐字节一致，题目、设置、来源回执与源协议哈希均已核验；旧全量被中断，仍缺少旧进程最终整轮权重恢复证明，这一限制不会因复用而消失。

- [最终分数](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/capability-screen-v3-2026-10-26/finish-r01/scores/summary.json)、[逐题评分](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/capability-screen-v3-2026-10-26/finish-r01/scores/scores.jsonl)、[收尾回执](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/capability-screen-v3-2026-10-26/finish-r01/receipt.json)。
- [HumanEval 逐份执行结果](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/capability-screen-v3-2026-10-26/finish-r01/humaneval-execution.jsonl)及同目录执行收据、控制结果。
- [独立评分审计](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/capability-screen-v3-2026-10-26/validation/final-score-audit.json)与[只读审计脚本](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/capability-screen-v3-2026-10-26/validation/audit_final_scores.py)。
- [抽样清单](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/capability-screen-v3-2026-10-26/panel_manifest.json)、[复用清单](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/capability-screen-v3-2026-10-26/reuse_manifest.json)、[归档清单](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/capability-screen-v3-2026-10-26/archive-manifest.json)。
- [完整原文与运行证据包](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/capability-screen-v3-2026-10-26/completed-evidence-r01.tar.gz)：1,442 个文件、2,705,609 字节；SHA-256 `af952fb4c12ec835de7b1cbd4ee2712914708d3278caf3f09b9852569b563396`。逐文件哈希、大小、路径及完整分母均核验通过，无残留 partial。原始输出位于包内 `outputs/*/*.jsonl`，关键小文件同时保存在当前目录结构。

最终 summary SHA-256 为 `6dd5e69bed64d5fade71b7354c8c7999fe4902aca155a7fde803e66362cbb7bb`；逐题 scores SHA-256 为 `9e1306231a433c494022ab4ffada14ad9e5ae3a031cd2f9dc929b27737347def`。

旧全量仍保持用户要求的停止状态：10,034 对完整 MMLU、1 份 partial 及停止证据已归档，其余三项未启动。旧 MMLU 已完成部分原版 68.21%、EVO 28.72%，但其长度排序前缀不是随机完整测试集，不能作为全量分数或与新加权抽样成绩直接配对。旧证据见 [停止目录](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/capability-damage-v2-2026-10-26/user-stop-20261026-r01)，不恢复旧运行。

当前结论限于这组固定题目、模型版本与动态干预。重复用同一面板调参后，它属于开发证据；本轮能力结果本身既不测量主动有害建议或敌意发生率，也不能把两个通道认定为“道德神经元”。

---

### 原件 3：本轮已完成：最终状态与历史 ETA

原路径：`experiments/capability-screen-v3-2026-10-26/RUN_STATUS.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/capability-screen-v3-2026-10-26/RUN_STATUS.zh-CN.md) · [单独阅读副本](../library/b9a147329460afef.md)；SHA-256：`b9a147329460afef40089e65cabf78e77e2a910aeab7b95fbad2399bbc95454e`。

---

#### 本轮已完成：最终状态与历史 ETA

**最终状态（2026-10-26）：** 北京时间 05:29:23 全部推理、HumanEval 官方隔离执行及评分完成，1,400 对/2,800 单元完整，无基础设施失败。独立审计和完整原文归档通过。原版/EVO 为 MMLU 67.99%/29.74%、ARC 65%/38%、GSM8K 88%/0%、HumanEval 53%/4%；下降 38.26、27、88、49 个百分点。详见[最终报告](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/capability-screen-v3-2026-10-26/RESULTS.zh-CN.md)、[最终收据](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/capability-screen-v3-2026-10-26/finish-r01/receipt.json)和[归档清单](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/capability-screen-v3-2026-10-26/archive-manifest.json)。

启动到自动评分完成实测 **40 分 10 秒**，包含复用 718 对；全部重新计算约 **44.76 分钟（成本推算）**，未来同配置预算 **50–60 分钟**。下文完整保留启动时的早期预测和未完成状态，均为历史快照，不代表当前状态。

##### 历史：启动与初步 ETA

2026-10-26 北京时间 04:49:13 已启动两个 GPU worker（1375855、1375856）与 CPU 收尾（1375857）。任务为 MMLU 1,000、ARC-C 200、GSM8K 100、HumanEval 100；共 1,400 对、2,800 个条件单元。

已冻结独立抽样与复用清单。718 对 MMLU 与旧记录完全一致，可复用；其余 682 对新计算。数学和代码分别在两张卡上先执行，随后交换分片，最后完成选择题。原模型、干预、精度、停止规则和生成上限未改。

04:53:06 核对两 worker 均存活，数学完成 15 对、代码 8 对，平均配对耗时分别 13.64 秒、20.07 秒。代码已有长度上限回答，另有一题仍在生成。初步规划整轮约 40–60 分钟，含选择题、CPU 沙箱和评分余量；这是少量实测后的估计，不是保证或统计置信区间。原始时点与数值见 `validation/eta-initial.json`。随后日志确认数学 18 对、代码 12 对，平均耗时升至约 20.47 秒和 26.30 秒；将初步整轮估计修正为约 45–65 分钟，即北京时间约 05:35–05:55，见 `validation/eta-update-r02.json`。这是早期估计，后续以实时回执为准。

旧全量于 04:43 停止，10,034 对完整 MMLU 和部分记录保留。旧运行没有全量成绩；新运行也尚未产生最终成绩。复用的历史计算时间与本次启动后的墙钟时间分开，不能将本次速度称为从零计算全部 1,400 对的速度。

启动依据：`launch.json`、`protocol.json`、`panel_manifest.json`、`reuse_manifest.json`、`validation/deployment.json`。后台任务状态：`worker-0.json`、`worker-1.json`、`outputs/*/receipt.json`。CPU 收尾：`finish-r01/receipt.json`；最终成绩预计保存至 `finish-r01/scores/summary.json`，逐题评分为同目录 `scores.jsonl`，代码执行证据为 `finish-r01/humaneval-execution.jsonl`。这些最终文件尚未生成，不能把等待回执视为完成。

每半小时巡检已切换至本轮。不得重启旧全量，不重复启动新收尾，不因到一小时而删题、截短一方回答或把基础设施失败计成答错。

---


## 时间、运行与停止收据索引

下面是所收集JSON的原有时间字段与状态，不把预计结束时间当实际完成时间。未列时间的文件仍有原件链接。完整JSON全部保存在原文归档，不能以此索引中的标量代替完整嵌套内容。

| 原件 | 原记录状态/阶段 | 原时间字段（原时区） |
|---|---|---|
| [finish-launch.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/capability-screen-v3-2026-10-26/finish-launch.json) | {} | {} |
| [finish-r01/humaneval-execution.jsonl.receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/capability-screen-v3-2026-10-26/finish-r01/humaneval-execution.jsonl.receipt.json) | {"status": "completed"} | {"created_utc": "2026-10-25T21:29:19.924532+00:00"} |
| [finish-r01/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/capability-screen-v3-2026-10-26/finish-r01/receipt.json) | {"status": "completed"} | {"started_utc": "2026-10-25T20:49:13.165415+00:00", "checked_utc": "2026-10-25T21:29:13.189293+00:00", "ended_utc": "2026-10-25T21:29:23.012506+00:00"} |
| [finish-r01/scores/summary.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/capability-screen-v3-2026-10-26/finish-r01/scores/summary.json) | {"status": "completed", "scope": "Fixed screening panel; not full benchmark scores."} | {"created_utc": "2026-10-25T21:29:22.823986+00:00"} |
| [launch.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/capability-screen-v3-2026-10-26/launch.json) | {"status": "launched"} | {"started_utc": "2026-10-25T20:49:13.132688+00:00", "ended_utc": "2026-10-25T20:49:13.134181+00:00"} |
| [outputs/arc_challenge-shard0-r01/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/capability-screen-v3-2026-10-26/outputs/arc_challenge-shard0-r01/receipt.json) | {"status": "completed"} | {"started_utc": "2026-10-25T21:17:58.122739+00:00", "ended_utc": "2026-10-25T21:21:56.503522+00:00"} |
| [outputs/arc_challenge-shard1-r01/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/capability-screen-v3-2026-10-26/outputs/arc_challenge-shard1-r01/receipt.json) | {"status": "completed"} | {"started_utc": "2026-10-25T21:23:24.640827+00:00", "ended_utc": "2026-10-25T21:27:37.402512+00:00"} |
| [outputs/gsm8k-shard0-r01/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/capability-screen-v3-2026-10-26/outputs/gsm8k-shard0-r01/receipt.json) | {"status": "completed"} | {"started_utc": "2026-10-25T20:49:13.202687+00:00", "ended_utc": "2026-10-25T21:07:03.144842+00:00"} |
| [outputs/gsm8k-shard1-r01/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/capability-screen-v3-2026-10-26/outputs/gsm8k-shard1-r01/receipt.json) | {"status": "completed"} | {"started_utc": "2026-10-25T21:07:33.822678+00:00", "ended_utc": "2026-10-25T21:23:23.839269+00:00"} |
| [outputs/humaneval-shard0-r01/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/capability-screen-v3-2026-10-26/outputs/humaneval-shard0-r01/receipt.json) | {"status": "completed"} | {"started_utc": "2026-10-25T21:07:03.956941+00:00", "ended_utc": "2026-10-25T21:16:25.540643+00:00"} |
| [outputs/humaneval-shard1-r01/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/capability-screen-v3-2026-10-26/outputs/humaneval-shard1-r01/receipt.json) | {"status": "completed"} | {"started_utc": "2026-10-25T20:49:13.202055+00:00", "ended_utc": "2026-10-25T21:07:33.037105+00:00"} |
| [outputs/mmlu-shard0-r01/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/capability-screen-v3-2026-10-26/outputs/mmlu-shard0-r01/receipt.json) | {"status": "completed"} | {"started_utc": "2026-10-25T21:16:26.367763+00:00", "ended_utc": "2026-10-25T21:17:57.338201+00:00"} |
| [outputs/mmlu-shard1-r01/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/capability-screen-v3-2026-10-26/outputs/mmlu-shard1-r01/receipt.json) | {"status": "completed"} | {"started_utc": "2026-10-25T21:27:38.205866+00:00", "ended_utc": "2026-10-25T21:29:08.609682+00:00"} |
| [timing-summary.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/capability-screen-v3-2026-10-26/timing-summary.json) | {"status": "completed_read_only_timing_audit", "scope": "Timing and output-length diagnostics only. No score assessment, inference, retries, launches, or frozen-code changes."} | {"created_utc": "2026-10-25T21:32:43.607178+00:00", "remote_collection_utc": "2026-10-25T21:31:54.146727+00:00"} |
| [validation/final-score-audit.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/capability-screen-v3-2026-10-26/validation/final-score-audit.json) | {"status": "passed"} | {"audit_utc": "2026-10-25T21:31:31.377890+00:00"} |
| [validation/old-partial-and-timing-audit-20261026.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/capability-screen-v3-2026-10-26/validation/old-partial-and-timing-audit-20261026.json) | {"status": "read_only_audit_no_new_inference"} | {} |

## 全部原始资产入口

本目录在固定提交下共有68个跟踪文件，包含代码、原回答、失败、收据和压缩证据；文件数不是样本数。[逐文件完整账本](../assets/003-capability-screen-v3-2026-10-26.tsv) · [原目录](https://github.com/yuxiexiong/acupuncture/tree/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/capability-screen-v3-2026-10-26)。未复制模型权重、环境或凭据。
