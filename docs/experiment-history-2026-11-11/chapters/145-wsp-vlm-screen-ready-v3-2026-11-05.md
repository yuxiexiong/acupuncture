# 145．VLM数据v3：改写、评分与运行器

[返回总时间线](../README.zh-CN.md)

**时间定位**：版本/记录日期 2026-11-05；未从所选收据确定完整运行起止，不据目录名补写时刻。

**当时的目的与设计**

补B的292条等义改写、输入和gold隔离、冻结统计器，另造64条独立P0工程夹具。

**实际过程、结果与后来更正**

B1168输入，D464/H704；C6400输入；离线验收完成。P0尚没有模型回答，不能把运行器准备记为真实筛查完成。

**来源身份**：`wsp-vlm-screen-ready-v3-2026-11-05`；本章主体来源提交 `2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274`。下方原文中的状态是各文件写作时的状态，不能把早期“尚未运行”覆盖后期正式收据，也不能将后期结果倒填进早期设计。


## 原设计、执行过程、结果与更正全文

以下按“设计与题目 → 工程/执行记录 → 结果/更正 → 其他历史说明”组织；同类内没有可靠时间时保留路径顺序，不冒充严格先后。正文未删段；仅为本章节重排标题层级、把相对链接指向固定提交。原始字节另外完整保存。

### 原件 1：v3 设计与实现自查

原路径：`experiments/wsp-vlm-screen-ready-v3-2026-11-05/SELF_CHECK.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-screen-ready-v3-2026-11-05/SELF_CHECK.zh-CN.md) · [单独阅读副本](../library/665aff083daed0cf.md)；SHA-256：`665aff083daed0cfb0421424d0e2ff4d02fc8ff4d71abf5463e1005102133cc1`。

---

#### v3 设计与实现自查

日期2026-11-05；依据[仓库自查规范](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/docs/experiment-design-self-check.zh-CN.md)v1。设计者本人审查，非独立审查。范围：B改写、输入包、评分统计及B/C运行器准备；无模型/processor加载和推理。

##### 设计卡与版本变化

- 主线：研究者AI依据反馈定位并以稀疏权重修补VLM具体失败。此轮补齐行为筛查的输入和测量工程，不替换为一个低分排行榜。
- 新增认识/产物：292条预冻结等义改写、1,168条B请求及gold、按来源组的B统计和带阶段记录的B/C运行代码。无新增模型能力结论。
- 资产：v2固定B146及其哈希/D58H88；v1固定C160及模板、评分；v2配对统计函数；官方固定processor配置与transformers5.20.2源码。
- 依据/反例：空间限定改变目标集合，非纯组合因果操作；42组答案相同、56组子集为0；C共享对象；目视标签和改写审查均非独立人审；所有真实模型测量仍缺失。
- 操作：本次只写文本/代码、生成独立P0图、CPU检验。未来目标、revision、BF16、greedy128、像素预算均保持；补充固定SDPA、batch1、服务器已登记的软件目标版本，尚未验收其真实可用性。没有激活/hook/权重操作。
- 估计对象：B全部计数正确率减子集计数正确率；C原图通常减反事实图通常。主统计使用来源组，不使用请求条数；B n=88，C n=96。
- 判读/退出：沿用15pp/20%/70%、Holm固定三项、工程5%等规则；阳性只进入诊断候选，阴性/未决可以结束，不扩大样本救假设。
- 成本：本次GPU与目标模型调用0；未来B/C共7,568正式、64工程、256基础设施恢复预留、12GPU小时总界。运行器不能替代调度器硬超时。已有数据准备复用，不自动下载模型。

对比v2：未改变146组、分层/划分、答案、C文本、效果门槛和WSP定位自由度。新增加B的T1、B统计、独立工程样例与运行路径；P0图不进入B/C科学数据，也不当作A已准备。等义改写采用语法重写和显式视角保留，不添加目标区域/答案或强提示中的额外策略。所有文本在目标输出前固定。

##### C01–C14

| 项目 | 判定、依据与边界 |
|---|---|
| C01 主线 | 通过。README末段明确行为筛查→AI诊断→稀疏权重修补；本轮不替换总目标。 |
| C02 增量 | 通过。补齐上一轮明确缺失的292改写、输入、B统计及运行器；不是重复验证来源组数量。 |
| C03 资产 | 通过。复用v1/v2；源码/processor官方链接见README；固定模型缓存仍缺，未冒充现成模型环境。 |
| C04 假设 | 通过。保留数值分布、共享对象、模板有限和非独立审核边界；不从假数据阳性推真实模型失效。 |
| C05 操作 | 通过。仅外部输入变体；真实运行阶段写明固定模型、像素、会话、长度。无内部修补，层/剂量不适用。 |
| C06 路径 | 通过。图像/类别固定但空间条件改变目标集合；B差异可能混合数值难度，明确非纯组合因果效应。 |
| C07 耦合 | 不适用内部共享变量拼换；同来源全部模板/条件/顺序保持同集合，不拆来源组增n。 |
| C08 归因 | 通过。错误模式仅作为行为线索；没有命名空间神经元、权重载体或信息丢失机制。 |
| C09 区分 | 通过。合成全对判不优先、稳定差异判优先、T1无差异判未决、格式问题判工程失败；流程可失败。 |
| C10 指标 | 通过。整体整数解析、截断计错、联合正确率、实际88分母；同答案42组不贡献特定忽略条件计数。 |
| C11 失败 | 通过。基础设施失败停止并保留原文/异常；缺失不改分母；模型错答不自动重试。真实框架待验收明确分列。 |
| C12 成本 | 通过。离线检查不import torch/transformers/HF hub；无模型下载/运行；未来程序累计计账并保留硬超时待办。 |
| C13 可信度 | 通过且有限。改写/输入/选择/图像均有记录与hash；D/H阶段分离。审核看过H材料但未看模型输出，不声称所有材料未见。 |
| C14 累积 | 通过。准备完才能获得有效行为反馈，反馈决定后续WSP诊断；不预先承诺补丁成功，不自动进入模型阶段。 |

##### 相关历史错误

E02：不把数学补丁的两层移植为VLM固定位置。E10：格式有效、答对与联合正确分开。E11：无探针硬淘汰，也不从读出高分推出稀疏可修。E16：工程失败与科学阴性分开。E21：本次未做新颖性查重，不声称新算法或领域首次。E22：来源组作样本，模板/顺序只作相关测量；C对象重合边界保留。E23：同助手审核、离线验收、真实模型验收和授权分开。E25：复用旧统计，不额外扩大科学对照；P0仅工程请求。其余关于缓存形成、补偿与中介拼接的条目不适用本次无内部干预准备，不能借此对缓存机制作结论。

##### 反方检查及处理

1. **改写无意改变左右/远近参照。** 对全部292条复核；对象自身视角不替换为画面视角。`B-573506`保留到长颈鹿的距离比较；`B-1385`保留更远栏杆限定；代词先行词不清的草稿改回先说明视角再询问。逐条审核身份及特殊说明已保留。有限模板仍不能代表任意措辞。
2. **同答案/零答案题使模式计数虚高。** 不删样本追求差异；总分146组，模式仅104个不同答案组；按总数、子集数、差值、零/同答案分层。测试确认分母而非模板数。
3. **只用会成功的假数据验收。** 增加全对、变体无差异、格式错误、截断、基础设施异常、缺失/重复样例；失败分支必须与预期一致。合成输出不作为研究结果。
4. **默认运行命令会意外加载模型。** 默认只读冻结数据并验证图像，不导入模型框架；真实加载在显式执行函数内。离线测试断言相关模块未加载。运行器存在不等于当前获得执行授权。
5. **跨题历史、元数据或gold泄漏。** 每次创建单user消息，只含text/image；request_id不写入chat；gold独立；没有缓存前轮对话。未测真实chat template边界仍列模型端待办。
6. **第128个token恰好EOS被误判截断，或时间中止被当正常短答案。** 明确以EOS判断结束；到上限无EOS才是length；短序列无EOS为基础设施中止，测试覆盖边界。
7. **P0通过就宣布真实推理可信。** 64条只支持工程验收，要求另外保存缩放图审核、格式/截断、数值合理性和吞吐依据；假后端/CPU测试不能覆盖CUDA/processor真实行为。当前没有创建任何伪造验收通过文件。
8. **H早于D诊断，或用新目录绕过预算。** 运行器检查B/C两D完成、登记绑定D输出，阶段输出不覆盖，单run_root计账。真实操作仍须使用同一目录并保留时间记录，不能把文件字段当独立认证；硬件卡死的硬超时仍需部署层实现。
9. **助手自查等于独立审核。** 所有审查记录准确标同一助手，独立复核不冒领；用户本次授权的数据/代码准备不因此增加新的审批步骤。

结论：本轮设计与数据/统计控制逻辑通过；12项新增离线测试及合成统计验收通过。真实processor/模型/设备工程尚未验收；无目标模型运行授权。再次检查C01/C02/C08/C14后，总目标和本轮实际产物一致，未通过降低主张至“输出会变化”绕过研究目的。

---

### 原件 2：B 输入/统计与 B/C 运行器准备 v3

原路径：`experiments/wsp-vlm-screen-ready-v3-2026-11-05/README.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-screen-ready-v3-2026-11-05/README.zh-CN.md) · [单独阅读副本](../library/238c1ad5ea39f1c6.md)；SHA-256：`238c1ad5ea39f1c65b8714621babdc9f2403d87311b94318f6c2497a9f82cbcb`。

---

#### B 输入/统计与 B/C 运行器准备 v3

2026-11-05。**数据与代码离线验收完成；目标模型、processor和tokenizer均未加载，模型推理0次，GPU时间0。** 本轮授权是准备、离线验收、自查及GitHub交付，不是执行筛查。

接续[v2审核](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-screen-prep-v2-2026-11-05/README.zh-CN.md)，使用其146个B来源组（D58/H88），不补题、不改标签、不重划集合。C仍为160组（D64/H96），全部原输入和gold与v1逐记录相同。

##### 已完成

| 交付 | 内容 |
|---|---|
| [292条改写及审核记录](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-screen-ready-v3-2026-11-05/audit/B_rewrites.jsonl) | 每个来源组的全数/子集两问各一条T1；同时保留T0。规则辅助起草后，本助手逐条语义审核，非独立人工复核。 |
| [B完整输入](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-screen-ready-v3-2026-11-05/prepared/B_inputs.jsonl)与[独立gold](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-screen-ready-v3-2026-11-05/prepared/B_gold.jsonl) | 146×2条件×2模板×2提示＝1,168条；D464、H704。模型输入仅有text/image，request_id用于记录，不进入对话。 |
| [生成脚本](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-screen-ready-v3-2026-11-05/prepare_inputs.py) | 锁定v2选择文件哈希；检查292条覆盖、原问句未变；生成B完整包及B/C分阶段队列，保存文件哈希。 |
| [B评分统计](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-screen-ready-v3-2026-11-05/statistics_b.py) | 严格整数解析、实际来源组分母、配对检验/区间、联合正确率、分层与错误模式、提示修对/改错和模板一致性。 |
| [B/C运行器](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-screen-ready-v3-2026-11-05/runner.py) | 默认离线验证；后续显式执行路径支持单图/无图、P0/D/H分段、固定配置、原始输出与token记录、预算计账、失败停止。 |
| [独立64条工程样例](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-screen-ready-v3-2026-11-05/prepared/P0_inputs.jsonl) | 8张程序绘制的几何图，B32/C32请求（其中C无图16条），附独立gold；只为工程预检，不作为A、B或C科学样本，不补入146组。 |
| [离线验收](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-screen-ready-v3-2026-11-05/audit/offline_receipt.json) | 12项新增测试通过；五个队列的ID/路径/图片哈希验证；B完整包与生成结果匹配；C输入/gold不变；合成阳性/阴性统计通过。 |

改写保留类别、属性、空间条件、参照物、观察视角和范围。特别保留长颈鹿自身距离比较、对象自身左右、顶视图竖轴、食物准备区范围；“更远栏杆上的乌鸦”不改成“距栏杆更远的乌鸦”。修正少数原句语法/拼写时不改变标注对象。T1是有限的预冻结措辞稳健性对照，不能代表任意自然语言泛化。

B/C分阶段队列与完整包重复，故不重复提交这些约2.5MB的派生文件；生成脚本与[输入收据](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-screen-ready-v3-2026-11-05/audit/input_receipt.json)可精确重建。B完整1,168条输入和gold已直接提交。原始第三方B/C图片仍在external，不进入Git；图像来源及校验清单沿用v1/v2。

##### 统计口径

B解析只接受首尾空白之外完全由ASCII数字组成的非负整数；允许前导零，不从解释、算式、范围、单位或多个答案中提取数字。`2.`、`two`、`2 objects`均判格式失败；规则在模型输出前固定。截断即使文本是正确整数也记错并单列。缺失、重复、未知ID、基础设施错误直接阻止统计，不缩小分母。

复用v2的单侧精确McNemar、来源组bootstrap（10,000次，seed=20261105）、固定A/B/C三项Holm及Wilson下界。B主格为H/B0/T0，**n=88**；B1/T1与位置/距离、ego/allo、总数/子集数/差值、零子集、同答案分层分别呈现，分层结果是描述，不增加可挑选的主检验。控制与挑战联合正确率、B1修对与改错都报告。

146组中42组全数=子集，仍进入总体正确率；仅另外104组能支持“全数正确、子集错答成全数”的行为模式。该模式排除截断输出，且不是已证实的内部“忽略条件”机制。其D≥8/H≥12的诊断线索要求沿用原方案，模式不足不会把已确认的整体差异删掉。

主差15pp、挑战错误20%、控制正确70%、其他B0变体方向一致等门槛不变。整臂格式失败或截断>5%先判测量问题。默认只统计D；完整分析须包含D与H。C统计继续用[v2入口](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-screen-prep-v2-2026-11-05/statistics_c.py)。B/C各自的 `--family-pvalues` 接受固定A/B/C原始p值，缺测候选为1；正式汇总须互相提供B/C实测p值，A仍为1，不能删A放松门槛。

##### 运行器做了什么、尚未证明什么

目标固定 `Qwen/Qwen3-VL-4B-Instruct`，revision `ebb281ec70b05090aa6165b016eac8ec08e71b17`。拟沿用已登记环境版本torch2.14.0、transformers5.20.2；本轮本机未安装/导入这两个库，也没有在服务器重验它们。运行时版本不符即停，不顺手升级。单GPU、batch1、BF16、SDPA、greedy、128新token、独立会话、无量化；显存至少48GB（十进制字节）。

未来加载仅使用固定revision的本地缓存，`local_files_only=True`，不会自动联网下载模型。会记录权重分片/配置文件哈希、软件版本、processor/chat template哈希、原始文本、生成token ID、停止原因、输入长度/哈希、image_grid_thw、视觉token数、处理后尺寸及耗时。每个请求只尝试一次；基础设施失败写入原记录后停止，不把错误回答重试成正确。已有输出目录不覆盖。

处理器像素面积固定65,536–1,048,576；patch16、merge2来自[固定模型处理器配置](https://huggingface.co/Qwen/Qwen3-VL-4B-Instruct/blob/ebb281ec70b05090aa6165b016eac8ec08e71b17/preprocessor_config.json)。API依据[transformers5.20.2 Qwen3-VL文档](https://huggingface.co/docs/transformers/v5.20.2/model_doc/qwen3_vl)、[图像处理源码](https://github.com/huggingface/transformers/blob/v5.20.2/src/transformers/models/qwen2_vl/image_processing_qwen2_vl.py)和[多模态processor源码](https://github.com/huggingface/transformers/blob/v5.20.2/src/transformers/models/qwen3_vl/processing_qwen3_vl.py)核对。源码支持这些调用，不等于已通过本环境兼容性验收。

阶段顺序已写入运行器：

1. **未来processor-only准备**：为466张科学图＋8张工程图输出缩放预览、grid和哈希；审核可辨认性，记录 `processor_review.json`，再允许任何模型输出。本轮没有执行这个processor加载路径。
2. **未来P0预检**：独立64条工程请求。检查图像/无图路径、格式/截断、数值/设备状态和吞吐，在 `P0_acceptance.json`登记验收；吞吐外推含20%余量。
3. **未来B_D与C_D**：两个开发集均完成。分析后按任务登记诊断描述，绑定D原始输出SHA。
4. **未来H**：运行器验证D已完成与相应登记文件，再读取该任务完整H队列。时间顺序的真实执行仍需保留运行收据；文件声明不构成独立审查。

所有真实运行须使用同一run_root，累计B/C正式7,568请求＋P0 64＋基础设施恢复预留256＝最多7,888次尝试，输出上限1,009,664 token。累计12 GPU小时包含加载/计账开销；达到预算不开始下条请求，并给生成设置剩余时间停止条件。库的停止检测可能在一次前向结束后才生效，不能保证硬件故障/卡死时精确秒级终止；正式部署还需调度器超时保护。恢复没有自动执行入口，须先核对历史失败和剩余预算，不能新建run_root绕过总量。

离线测试只覆盖输入、控制流程、接口约定与统计；**没有证明真实框架加载、CUDA生成、图像缩放、模型输出或吞吐正确**。这些是模型端工程待验收，不是已观察到的科学阴性。

##### 可复核命令（不加载模型）

在仓库根目录、原始external图片已就位时：

```bash
python3 experiments/wsp-vlm-screen-ready-v3-2026-11-05/prepare_inputs.py
python3 experiments/wsp-vlm-screen-ready-v3-2026-11-05/prepare_p0.py
python3 experiments/wsp-vlm-screen-ready-v3-2026-11-05/accept_offline.py
python3 experiments/wsp-vlm-screen-ready-v3-2026-11-05/runner.py --task B --stage D --out /tmp/B-dry.json
```

离线验收断言进程没有导入torch、transformers、huggingface_hub。验收中的回答由确定性合成夹具产生，收据显式标为 `SYNTHETIC_NOT_MODEL_RESULTS`，不是真实Qwen回答。测试覆盖错误/缺失/重复、EOS在第128位、短序列非EOS异常、实际88组分母、同答案组不误算模式、变体方向不稳与格式失败。

真实运行的 `--execute` 路径已写好但本轮未调用；它不代表新的用户授权。验收登记JSON的最低字段：

- `processor_review.json`：`accepted`、`manifest_sha256`，另应附审核人/时间、逐图问题记录。
- `P0_acceptance.json`：`accepted`、`predictions_sha256`，另应附格式/截断、显存、吞吐及数值核验记录。
- 每任务诊断登记：`task`、`D_predictions_sha256`、`description`，另应附规则、D计数与时间；使用 `--diagnosis`传入H运行器。

这三类文件现在均未伪造为通过。

##### 仍缺什么

1. 固定revision完整模型/processor/tokenizer缓存与服务器资源检查；运行器不会替用户自动下载。
2. 实际processor加载、474张缩放预览及视觉复核；必要的图像可辨认性判断不能靠本次哈希检查代替。
3. 后续获准后的64条P0真实预检，包括框架兼容性、BF16/输出接口、数值合理性、显存、吞吐与调度器超时保护。
4. B/C开发集实测、诊断登记、留出确认和正式结果卡；至今均为0次。

数据改写、B输入包、B统计和运行器代码这些本次指定的准备项已补齐。WSP仍出现在筛查之后：研究者AI依据真实失败反馈定位，再选择稀疏权重修补并迭代；此处不预设两层、不把探针阳性当可修证明、不把行为缺口当补丁成功。[自查记录](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-screen-ready-v3-2026-11-05/SELF_CHECK.zh-CN.md)区分设计、离线验收、模型端待验收与运行授权。

---


## 时间、运行与停止收据索引

下面是所收集JSON的原有时间字段与状态，不把预计结束时间当实际完成时间。未列时间的文件仍有原件链接。完整JSON全部保存在原文归档，不能以此索引中的标量代替完整嵌套内容。

| 原件 | 原记录状态/阶段 | 原时间字段（原时区） |
|---|---|---|
| [audit/input_receipt.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-screen-ready-v3-2026-11-05/audit/input_receipt.json) | {"status": "data preparation only", "model_calls": 0} | {} |
| [audit/offline_receipt.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-screen-ready-v3-2026-11-05/audit/offline_receipt.json) | {"status": "OFFLINE_ACCEPTED_NOT_MODEL_VALIDATED", "model_calls": 0} | {} |

## 全部原始资产入口

本目录在固定提交下共有25个跟踪文件，包含代码、原回答、失败、收据和压缩证据；文件数不是样本数。[逐文件完整账本](../assets/145-wsp-vlm-screen-ready-v3-2026-11-05.tsv) · [原目录](https://github.com/yuxiexiong/acupuncture/tree/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-screen-ready-v3-2026-11-05)。未复制模型权重、环境或凭据。
