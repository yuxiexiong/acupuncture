# 006．4B到Llama的跨家族迁移

[返回总时间线](../README.zh-CN.md)

**时间定位**：已提取运行收据的最早时间锚点（可含预检） 2026-10-26T14:13:35.175934+08:00；不能当作全部子运行起止。

**当时的目的与设计**

使用稠密映射的true_D_match与随机映射、原版等对照，先看小诊断，再做四项能力面板；稀疏阶段二原本有单独门槛。

**实际过程、结果与后来更正**

阶段一实际完成，能力损伤满足当时操作性门槛；random2在两项小诊断上与真实组同分。阶段二未运行，后继队列按用户要求停止。完整gate、每任务成绩和停止证据均保留。

**来源身份**：`cross-family-transfer-toy-v1-2026-10-26`；本章主体来源提交 `7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8`。下方原文中的状态是各文件写作时的状态，不能把早期“尚未运行”覆盖后期正式收据，也不能将后期结果倒填进早期设计。


## 原设计、执行过程、结果与更正全文

以下按“设计与题目 → 工程/执行记录 → 结果/更正 → 其他历史说明”组织；同类内没有可靠时间时保留路径顺序，不冒充严格先后。正文未删段；仅为本章节重排标题层级、把相对链接指向固定提交。原始字节另外完整保存。

### 原件 1：Acupuncture 跨家族迁移 toy v1：执行合同

原路径：`experiments/cross-family-transfer-toy-v1-2026-10-26/CONTRACT.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cross-family-transfer-toy-v1-2026-10-26/CONTRACT.zh-CN.md) · [单独阅读副本](../library/720ea16159eac31b.md)；SHA-256：`720ea16159eac31b485132a013860140c132f367479d2e2e440e6ffa90aac28e`。

---

#### Acupuncture 跨家族迁移 toy v1：执行合同

2026-10-26。配套 [实验设计](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cross-family-transfer-toy-v1-2026-10-26/PROTOCOL.zh-CN.md)。本合同约束实现与未来运行，不是模型实验已启动的记录。

##### 1. 当前授权与完成定义

用户已授权完成跨家族迁移代码、合同、实验设计、准备到 GPU Ready；明确目标为 **Llama-3.1-8B-Instruct**，缺失资产可以下载。当前不执行 GPU 模型加载、前向、生成、正式评测或自动排队。根因实验继续暂停；Q25–Q40、旧8题及静态权重修改不恢复。

状态必须分开记录：

| 状态 | 必须具备的证据 |
| --- | --- |
| `CODE_READY` | 代码与合同一致，CPU数值/对齐/门控测试通过，命令与输入依赖可解析 |
| `CODE_READY_ASSET_BLOCKED` | 代码与CPU检查可交付，但精确目标权重缺失或访问受阻；不能启动GPU，也不能简称GPU Ready |
| `ASSETS_READY` | 精确源/目标revision及配置/词表/权重分片身份、完整性和合法访问可核验；无量化或适配器替代 |
| `GPU_READY` | 上述两项齐备，真实tokenizer对齐预检通过、输入和依赖冻结、远端运行环境可用、启动入口具备阶段门；**GPU实测尚未运行** |
| `GPU_PREFLIGHT_PASS` | 后续获准执行后，真实模型的零hook、BOS/EOS、缓存隔离、有限值、权重恢复等GPU检查通过 |
| `RUNNING` / `COMPLETED` | 有相应本轮进程与阶段回执；只能由实际运行产生 |

如果权重缺失、gated权限不足、CPU测试失败或依赖未核验，报告具体阻塞，不能为了交付用“GPU Ready”掩盖尚缺条件。CPU检查通过不能冒称真实BF16模型干预已验证。

本次准备初期，旧服务器账号访问官方精确 Llama-3.1-8B-Instruct 权重遇到 gated 403。2026-10-26 已用用户单独提供的 RuizhiXu 凭据通过官方访问核验；旧拒绝和新成功回执均保留。实际资产完成下载、校验及CPU准备之前不能报告 `GPU_READY`；不得以已有3.0模型替代。本段只更新资产状态，不修改科学设置或运行授权。

##### 2. 不可变科学设置

- 源：Qwen3.5-4B固定revision `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`；目标：官方 `meta-llama/Llama-3.1-8B-Instruct`，revision以校验后的资产冻结清单为准。
- 源L13/N7956负、L14/N8949正；目标固定L13与L14，不搜索其他层；每层至多一根通道，合计两根。
- 共同正常文本256训练文档、64验证文档，文档等权；不同tokenizer按共同字符前缀结束位置配对，不按序号配对。
- 正则候选10⁻⁴、10⁻²、1；按干净验证MSE选取；目标干预回答不能用于拟合、选层、选列、定符号或定强度。
- 真实源与三组匹配随机源走完整同样流程；随机种子20261026；T_dense、T_sparse单列为使用目标对比材料的强基线。
- d=1；prefill和全程生成/评分注入；BF16/eager/greedy/实际batch1；不改变成品权重。
- 第一阶段主臂true_D_match；第二阶段主臂true_S_recipe；D_raw、S_proj为事前固定诊断臂，不能看到结果后互换主次。
- 全部19臂的候选与公式在第一阶段确认前一次冻结；第二阶段仍不得提前运行。
- 每阶段固定主比较使用同套MMLU1000、ARC-C200、GSM8K100、HumanEval100；不换题、删失败题、改答案提取或改变token预算。
- 目标原生BOS/EOS与聊天模板须适配并冻结，不能照搬Qwen token。模型格式适配不改变题目、任务评分或同模型两臂公平性。

##### 3. 第一阶段到第二阶段的硬门

在正式第一阶段前，任一层映射验证相对MSE≥1即记 `MAPPING_QUALITY_HOLD`：只说明此冻结映射未优于目标训练均值预测，停止正式干预，不自动换层/语料/映射范围；它不是科学阴性。

第一阶段须先完成主比较全部1,400对和自动评分，检查技术失败为零、文件覆盖和条件/题目身份正确、冻结哈希与钩子/权重回执有效。没有完整证据时为 `TECHNICAL_HOLD`，禁止进入第二阶段。

每任务Δ为原版分数减干预分数，单位百分点。保留95%配对区间，另报告98.75%配对bootstrap区间[L,U]作为四项Bonferroni推进门；10,000次、种子20261026，MMLU学科内配对重采样并用固定学科权重。**Δ=5pp 是本轮操作性继续阈值，不是效应等于零的定义。**

判定按以下顺序执行，不能更换顺序制造通过：

1. 完整性/技术核验失败：`TECHNICAL_HOLD`。
2. 任一任务Δ≥5、L>0，且该任务 discordance>5：`PASS`。
3. 未PASS且四项U均<5、四项 discordance 均>5：`STOP_SMALL_EFFECT`。
4. 其他全部情形：`INCONCLUSIVE_HOLD`。

discordance 是每任务原版/干预版正确状态不同的配对题数；≤5时可能出现退化的bootstrap区间，不能据此宣布很精确的无损伤或通过。全零不一致也进入INCONCLUSIVE_HOLD，而不是自动STOP。

**仅PASS允许第二阶段。** STOP_SMALL_EFFECT和INCONCLUSIVE_HOLD都保持第二阶段未运行；技术失败不是科学失败。不得以小诊断32/32题、单个长回答、目标自身基线或次要行为标签替代这个门。

PASS说明有足够依据把预算投给本轮稀疏近似，不证明效应至少5pp的置信下界、不证明优于随机、不证明相同根因。STOP_SMALL_EFFECT只限制本次模型、输入、层、映射与剂量的结果，不否定其他稀疏干预。INCONCLUSIVE_HOLD不自动追加样本或调参。

阶段门回执至少记录：阶段ID、被比较条件、模型/映射/题库/源码哈希、四项样本数、discordance、分数、Δ、95%和98.75%区间、技术完整性证据、状态、判定时间及允许下一步。只有一个手填PASS字符串不能作为可执行授权或阶段二依据。

##### 4. 两阶段必须交付什么

| 项目 | 第一阶段 | 第二阶段（仅PASS后） |
| --- | --- | --- |
| 条件 | T_0＋真实/3随机各D_raw与D_match＋T_dense，共10 | 真实/3随机各S_proj与S_recipe＋T_sparse，共9新增 |
| 行为原文 | 640份 | 576新增份；原版引用第一阶段同哈希记录 |
| 诊断面板 | 640个题目—条件单元 | 576新增单元 |
| 正式面板 | T_0 / true_D_match，各1,400题 | T_0 / true_S_recipe，各1,400题 |
| 必要记录 | 原文、token、提示/输出哈希、校准尺度、停止原因、时间、逐题评分 | 同左，另保留两列编号/符号/ρ及实际幅度 |
| 最终状态 | 阶段门、实际成本、全部失败 | 同规则评价稀疏主臂，交付效果与局限，不自动扩第三阶段 |

本版正式Benchmark在第二阶段重跑T_0，正式总预算为5,600个题目—条件单元，包含原版重复计算；不承诺未实现的缓存节省。小行为/诊断面板沿用本轮阶段一的T_0记录，保留来源哈希，不重写原输出。

随机三对不跑四项正式1,400题面板，其能力与行为证据只适用于各自小面板/64场景；不得用主臂的正式区间替随机补出全量成绩。两阶段结果不选赢家，原幅度臂无效、随机更强或能力改善都完整报告。

##### 5. 实现验证与错误处理

CPU测试覆盖：不等分词时共同前缀配对、Unicode/重复offset/截断、仿射映射增量不加bias、两列选点和幅度公式、缺失记录/错模型/错条件拒绝、门判定边界、第一阶段非PASS时阶段二不可启动。

GPU预检留到运行授权以后，检查真正目标模型加载、原生特殊token、原版对零干预、每次独立cache、同题校准复用、有限输出和权重/钩子恢复。实际BF16通道与稠密非零写入可能有舍入差，不要求未经论证的逐位等价，也不能把不相等自动解释成机制差别。

初始仅每卡1进程、2分片，实际forward batch1；不把旧9B/2B每卡3进程的结果当作LLaMA并发验证。不抢占或杀死其他作业。任何未来加并发必须先做本目标一致性验证，另外记录执行版本，科学设置保持不变。

实现bug可在冻结科学设计范围内修复，但每次保留失败日志、旧版本/新版本哈希、受影响单元与重算成本。改题目、模型版本、层、剂量、候选数、精度、后端、窗口、评分或推进门属于新协议，不能借“修复”执行。不得覆盖失败目录，也不得把技术缺失记为阴性或分母外删除。

##### 6. 成本、ETA与结束

当前只报告准备完成情况，不把代码通过、资产下载完成、队列创建或CPU测试当实验完成。下载ETA与GPU实验ETA分别报告。

未来运行时先记录实际预检、加载、采集、拟合、行为、正式Benchmark、沙箱、导出耗时；按已完成同阶段样本外推ETA，未测阶段列为假设场景。输出token预算不是保证上限的墙钟。阶段一提前停止应列出明确未运行的第二阶段预算，不伪称完成全部迁移。

正式机器结束时交付完整证据与机器报告、配对原文入口和匿名双人盲评包。人工标签尚缺时明确“能力评测已完成，行为判断待办”；不得虚构标签，也不为等待人工标签无限轮询。根因实验继续暂停，不由这份合同自动恢复。

权重、token、凭据与环境缓存不入Git；本轮代码、协议、固定输入哈希、项目原始输出和审计回执按仓库规定保存。大型激活/映射保留可校验的路径、大小与SHA-256。本合同的任何修改须保留版本、原因及已暴露数据范围。

##### 7. 可执行入口约束

`pipeline.py --stage 1|2 --run PATH --target MODEL_PATH` 默认只打印阶段计划，不启动GPU。输入冻结和GPU Ready的CPU准备单独完成。正式GPU运行必须显式加 `--execute` 且已有该轮运行授权。阶段2必须读取并验证由 `gate.py` 生成的阶段1证据；不能手填状态或通过命令行覆盖门。

CPU准备入口为 `readiness.py --source SOURCE_PATH --target TARGET_PATH --output RUN_PATH`。真实tokenizer和完整目标资产尚缺时，必须保留待检查项，不用合成测试结果替代真实资产验证。

`mapping.py` 只按冻结干净数据拟合和选点；`toy.py` 执行对应阶段的固定条件；`benchmark.py` 的run/finish分离推理与评分；`gate.py` 对两阶段分别计算同一固定损伤判定，阶段二不开放任何后继阶段；`preflight.py` 在未来运行授权后做GPU检查。所有实际命令以代码参数校验为准，CPU回执须检查帮助入口、输入身份和门控反例。

---

### 原件 2：Acupuncture：Qwen3.5-4B → Llama-3.1-8B-Instruct 跨家族迁移 toy v1

原路径：`experiments/cross-family-transfer-toy-v1-2026-10-26/PROTOCOL.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cross-family-transfer-toy-v1-2026-10-26/PROTOCOL.zh-CN.md) · [单独阅读副本](../library/21d70c8cf0a89563.md)；SHA-256：`21d70c8cf0a8956372f9a83e84f70940b360b493a11e698bc44187d2522177d2`。

---

#### Acupuncture：Qwen3.5-4B → Llama-3.1-8B-Instruct 跨家族迁移 toy v1

2026-10-26。**本轮交付为代码、实验设计、执行合同与 GPU Ready 检查；尚未启动 GPU 实验。用户已授权缺失目标资产的下载。根因实验继续暂停。**

准备初期，旧服务器账号访问精确目标仓库返回 gated 403；2026-10-26 已用用户单独提供的 RuizhiXu 凭据通过官方访问核验，旧拒绝回执仍保留。权重全部下载并完成校验前仍不能报告 `GPU_READY`。代码与CPU测试完成不等于权重齐备，也不等于真实模型已验证。具体资产和准备状态以本目录最新回执为准。

##### Material Passport

| 项目 | 内容 |
| --- | --- |
| 当前模式 | 实验准备；不包含 GPU 运行授权 |
| 已有证据 | 4B→9B、4B→2B 的固定迁移配方伴随明确能力损伤；不是本轮 LLaMA 的结果 |
| 本轮问题 | 源两针定义的增量，经固定表示映射后，能否在另一个模型家族产生可量化能力损伤；若可以，能否落到两根原生通道上 |
| 主要终点 | 同一目标原版与固定干预版的四项能力分数差；阶段推进门见第 8 节 |
| 次要终点 | 64 场景中的结构化有害建议、敌意措辞、完成度等；须独立人工盲评，不由能力分数代替 |
| 研究边界 | 不要求损伤小；不预设自然通道语义、两针独特性或共同根因；不修改成品权重 |

##### 1. 中心设计：先确认方向能搬，再检验两针能实现

让 4B 与 LLaMA 阅读同一批正常文本，在共同文本前缀结束位置收集激活，学两张线性坐标转换表。把源两针各自写入的增量转换到 LLaMA，再在两个固定层注入。

第一阶段直接使用转换后的稠密方向，回答“这条表示映射路线能否带来能力损伤”。第一阶段通过事前固定的推进门，第二阶段才把每层方向近似为一根原生 MLP 通道，回答“两针形式能否实现同类效应”。两阶段分别有自己的原版对照和正式四项 Benchmark。

这个顺序节省的是第一阶段未获支持时的稀疏分支计算，不保证任何稀疏干预都不可能有效。稀疏近似会改变方向；归一化配方还可能放大幅度。因此，第一阶段停止只关闭本轮“先搬方向，再落成两针”的预注册路线，不能推出所有两针方法都失败。

##### 2. 固定模型、位置与干预

| 项目 | 本轮固定值 |
| --- | --- |
| 源模型 | `Qwen/Qwen3.5-4B@851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a` |
| 目标模型 | **`meta-llama/Llama-3.1-8B-Instruct`**；精确 revision、配置和文件哈希进入资产回执及运行冻结清单 |
| 禁止静默替代 | Llama-3-8B-Instruct、Llama-3.2-3B-Instruct、量化版、微调版或适配器版本 |
| 源两针 | 零起始 L13/N7956 负向；L14/N8949 正向 |
| 层对应 | 固定 L13→L13、L14→L14；本轮不搜索层 |
| 两针预算 | 每层恰好一根原生 MLP 通道；不在失败后改为更多通道 |
| 原剂量规则 | d=1，每层一份该题目标原版参考残差尺度；不是 1% 微扰 |
| 注入窗口 | prefill 与全部后续生成/选项评分位置 |
| 通道注入点 | 门控激活之后、`down_proj` 之前的通道加法 |
| 稠密注入点 | 对应 decoder 层末残差加向量 |
| 数值设置 | BF16、eager、greedy、实际 forward batch=1；模型权重冻结 |

同层号只是最简单的预先指定对应，不是功能同源的证据。跨家族同时改变权重、训练和 tokenizer 等，结果不能单独归因于注意力架构差别。

源 B 先写入、A 后写入；两层尺度都由未干预的公共提示一次校准，不在 B 开启后重新估计 A。逐题尺度沿用旧实现：该层有效提示 token 的残差 L2 范数中位数，排除首 token 和 padding。所有条件共享该题的原版尺度，在续写过程中保持固定。

##### 3. 输入与跨 tokenizer 对齐

沿用 [原迁移实验的固定数据](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/transfer-toy-v1-2026-10-26/data)，不根据 9B、2B 或 LLaMA 的输出改题。它们对本轮目标尚未用于干预筛选，但已经属于项目共享材料，不能称为全项目从未见过的新题。

| 输入 | 数量 | 用途 |
| --- | ---: | --- |
| `map_train.jsonl` | 256 文档 | 映射拟合、源自然激活 RMS 与随机池分层 |
| `map_val.jsonl` | 64 文档 | 只按干净激活重建误差选择正则强度 |
| `contrast.jsonl` | 32 场景×立场/措辞四格＝128 条 | 目标自身稠密/稀疏强基线，单独标识使用了目标对比材料 |
| `confirm.jsonl` | 64 场景 | 完整生成与人工行为盲评 |
| `ability_diag.jsonl` | MMLU 32＋ARC-C 32 | 所有条件的能力诊断；不决定正式阶段推进 |
| 最新能力面板 | 1,000＋200＋100＋100＝1,400 题 | 每阶段固定主臂与原版的正式能力对照 |

映射文本在两边使用**完全相同的原始字符序列**。正常对话转为事前确定的普通 role 文本串；此处不分别套不同聊天模板。行为生成另用各自原生聊天模板，不能混淆两种输入格式。

两端分别 tokenize，只在**两边均已完整消费同一原文前缀**的字符边界配对状态；记录原文哈希、字符结束位置、两端 token ID 与位置、对齐清单哈希。不能把第 n 个 token 与第 n 个 token 硬配。重复 offset、Unicode 拆分及特殊 token 必须经过对齐测试，不能让一侧已多看字符。每篇最多 512 个模型 token、128 个共同有效位置，取两端共同可见的文本范围，均匀确定位置。没有合法共同边界时停止并记录技术问题，不能自动跳过该文档。

源模型旧激活只有在模型、原文、输入 token、选中位置与数值设置全部一致且哈希可核验时才可复用。本轮改变了对齐输入格式，默认重新采集所需源激活；可复用原始文本、源坐标和已验证代码，不能把旧缓存未经检查地拼入。

##### 4. 映射、选列及四种幅度

每层拟合仿射关系 F(h)=Mh+b，训练按文档等权、文档内位置等权。沿用标量 RMS 标准化的岭回归；λ 候选固定为 10⁻⁴、10⁻²、1，只用验证集相对于目标训练均值的相对 MSE 选最小者，精确并列取较大 λ。增量只映射为 **Mδ，不注入 b**。

记源有符号单位列为 v=s·w_S/||w_S||，其映射为 u=Mv；源与目标逐题参考尺度分别为 m_S、m_T。目标单位列 ŵ_i=w_i/||w_i||，选择 i*=argmax_i |uᵀŵ_i|，并列取最小编号。令 β=uᵀŵ_i*，记录 ρ=β²/||u||² 及 1−ρ。ρ 仅是几何重建比例，不是保留了多少行为功能。

| 臂 | 每层额外残差写入的理想值 | 实现与含义 |
| --- | --- | --- |
| `D_raw` | m_S·u | 稠密，保留映射给出的幅度 |
| `D_match` | m_T·u/||u|| | 稠密，使用目标参考尺度；**第一阶段主臂** |
| `S_proj` | m_S·β·ŵ_i* | 通道加 m_S·β/||w_i*||，保留投影幅度 |
| `S_recipe` | m_T·sign(β)·ŵ_i* | 通道加 m_T·sign(β)/||w_i*||；**第二阶段主臂** |

这四臂的定义和对应主次在读测试输出前固定。不能第一阶段 `D_match` 未通过就临时改用 `D_raw` 宣布通过。`D_raw`、`S_proj` 的结果仍完整报告，作为后续独立方案的线索。`D_match` 与 `S_recipe` 逐层名义范数相同；跨层不能简单把范数相加解释为同等总剂量。

每层记录 λ、验证 MSE、映射增益、固定两半训练数据的方向稳定性、源方向在自然 PCA95 子空间的能量、所选列与映射方向的余弦及 ρ。低 ρ 或低自然方差能量不自动等于科学失败；所有映射/方向必须有限且非零，文件和对齐完整。若任一层验证相对 MSE≥1，即未优于目标训练均值常量预测器，本轮记 `MAPPING_QUALITY_HOLD`，停止进入正式干预，不自动改语料、层或正则范围。这是当前映射的质量暂停，不是现象不可迁移的证明。干净重建好也不能保证因果干预有效。

##### 5. 对照与阶段预算

真实源与三组随机源均走同一映射、选列和幅度流程。随机源按源层列范数五分位与自然激活 RMS 五分位交叉分层，以种子 20261026 抽取三对，排除真实源列；不足时按旧规则合并相邻分位格并记录候选池。不同原始文本对齐可能改变 RMS 分层，所以记录本轮抽中的真实编号，不假称必与旧轮相同。

| 阶段 | 目标条件 | 行为生成 | 能力诊断 | 正式 Benchmark |
| --- | --- | ---: | ---: | --- |
| 第一阶段 | T_0；真实/三随机各 D_raw、D_match；T_dense，共10条件 | 64×10＝640份 | 64×10＝640单元 | T_0 vs true_D_match，1,400对 |
| 第二阶段（有条件） | 真实/三随机各 S_proj、S_recipe；T_sparse，共9新增条件 | 64×9＝576新增份 | 64×9＝576新增单元 | T_0 vs true_S_recipe，1,400对 |

映射结束时一次计算并冻结全部 19 条件，包括第二阶段的列与符号。冻结预测不等于提前运行第二阶段。

目标自行提取的 T_dense、T_sparse 为强基线，不是理论上界。随机对照只覆盖三组固定源对，且正式 1,400 题面板只评本阶段主臂与原版：不得据此声称主臂在四项正式 Benchmark 上优于全体随机通道，也不能估计此类损伤的总体发生率。

本版第二阶段正式 Benchmark **重新运行本目标原版 T_0**，与 true_S_recipe 在同阶段配对，避免为一个 toy 新增跨阶段缓存拼接逻辑。两阶段正式 Benchmark 合计 **5,600 个题目—条件单元**，包含同题原版的重复计算，不能称为5,600道独立试题。小行为/诊断面板第二阶段只新增9臂，原版引用本轮第一阶段同哈希记录；不得用4B、9B、2B的回答充当LLaMA原版。

##### 6. 最新 Benchmark 与原生模型格式

复用 [最新冻结四项评测](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/transfer-toy-v1-2026-10-26/BENCHMARK_FOLLOWUP.zh-CN.md)的题目、few-shot、分数定义与生成预算。跨家族只做必要模型格式适配，并为原版与干预版保持一致。

| 任务 | 每臂题数 | 评分 | 最大新 token |
| --- | ---: | --- | ---: |
| MMLU | 1,000 | 5-shot，完整候选条件似然；57 学科总体权重 | 不生成 |
| ARC-Challenge | 200 | 25-shot，完整候选似然按字符数归一化 | 不生成 |
| GSM8K | 100 | 5-shot，strict-match 主分；原 flexible-extract 辅助分另报 | 2,048 |
| HumanEval | 100 | 0-shot 原代码提示，官方测试 pass@1 | 1,024 |

能力题不套聊天模板；LLaMA 的原生 BOS 规则必须显式核验并冻结。停止集合来自固定目标配置、generation_config 与 tokenizer，核对必要的对话结束标记；不能照搬 Qwen 的 248044/248046。任务停止字符串、生成上限保持旧规则。模型解析失败/截断按原评分保留，OOM、加载失败、沙箱故障等基础设施错误记技术未完成，不能当作模型零分。

每题条件均从干净 KV/cache 开始；每阶段结束核验权重未改写、钩子清除。HumanEval 沿用禁网、非 root、资源受限的沙箱及正反控制。

##### 7. 正式统计与行为边界

每任务独立报告原分数、干预分数、下降百分点 Δ=原版−干预版、95% 配对 bootstrap 区间。MMLU 在学科内配对重采样并按冻结 57 学科权重汇总；其余按题配对。种子 20261026，10,000 次重采样。四项不合成“总损伤分数”。

为第 8 节“任一任务触发”的阶段推进门，另从同一配对重采样分布报告每项 **98.75% 区间**（分位数 0.625% 与 99.375%），按四项 Bonferroni 控制名义家族错误率 5%。这是有限样本 bootstrap 的近似，不称精确覆盖保证。每任务另记原版/干预版正确状态不同的配对题数 discordance；≤5 时不以其可能退化的窄区间宣称通过或效应很小。95% 区间保留用于与历史报告比较；不能用它替代推进门区间。

行为题使用原标注手册，双人独立盲评，分歧裁定，unknown 保留。能力损伤与结构化有害行为分别报告；当前推进门只针对用户明确指定的损伤问题，行为标签缺失不阻塞机器阶段判定。不能因为四项下降就自动填 H=1 或宣称“变恶”。

##### 8. 第一阶段如何判定，第二阶段何时允许开始

先核验完整性：1,400 对主比较齐全、模型/条件/题目身份正确、正式评分技术失败为零、资产及预测冻结可核验、钩子/权重/缓存检查通过。未满足时一律 `TECHNICAL_HOLD`，不算阴性。

在完整有效的第一阶段结果上，逐任务计算 Δ 和 [L,U]（98.75% 配对区间），δ=5 个百分点为本轮事前指定的最小值得继续效应：

| 状态 | 精确规则 | 第二阶段动作 |
| --- | --- | --- |
| `PASS` | 至少一项任务 Δ≥5、L>0，且该任务 discordance>5 | 可按原冻结配置进入第二阶段；不表示效应确定大于5，也不表示优于随机 |
| `STOP_SMALL_EFFECT` | 未PASS，且四项 U 均<5、四项 discordance 均>5 | 本轮路线停止；所测任务不支持达到预定值得继续幅度的损伤 |
| `INCONCLUSIVE_HOLD` | 技术有效但不满足以上两类 | 暂停第二阶段；不自动扩题、改剂量、换层或重新抽样 |
| `TECHNICAL_HOLD` | 技术、身份或证据完整性未通过 | 修复技术问题并保留失败记录；不能以此否定科学假说 |

5 个百分点是本项目的 toy 预算决策阈值，不是文献通用标准，也不是看到 LLaMA 结果后才选择。第一阶段通过并不意味着四任务全受损；各任务原分数及可能的改善都必须保留。

第二阶段使用同一固定四项规则评价 true_S_recipe 的损伤是否获支持，但它不会据此引出第三阶段。S_recipe 与 D_match 的差异仅在同一题、同一目标上的配对结果中解释；一个显著另一个不显著，不能直接当成两者显著不同。两阶段结论分别记账，不把门控后的样本选择隐藏起来。

若第一阶段仅行为有变化、主损伤门未通过，本轮仍停止/暂停第二阶段，保留行为结果。若希望据行为转入第二阶段，属于新的研究决策，须另行版本化，不能悄悄更换本轮终点。

##### 9. 执行顺序与算力边界

1. **准备交付（当前授权范围）**：代码、CPU 合成测试、真实 tokenizer 对齐检查、输入与资产校验、合同和可执行入口；缺失 Llama-3.1 资产可以下载。任何 GPU 模型加载、前向或生成都尚未启动。
2. **未来获运行授权后预检**：检查双卡及其他任务身份；固定环境加载精确模型；原版与零向量/零通道钩子一致性、停止 token、BOS、缓存隔离、权重哈希；不通过则技术暂停。
3. **共同准备**：两端干净激活、目标128条对比基线、岭回归、随机源、全部19臂预测冻结。两个模型可各占一张卡采集。
4. **第一阶段**：10条件的行为与诊断、固定主比较正式四项评分、完整性验证、生成阶段门收据。
5. **只有PASS才能第二阶段**：9个新增稀疏条件、重新运行原版和稀疏主臂的正式四项评分、证据验证及同规则效果判定；不自动启动第三阶段。
6. **交付**：全条件原文、分数与区间、阶段门、失败与停止原因、实际耗时/ETA误差、匿名盲评包。行为人工标签未到则明确留待办，不无限轮询。

初始执行配置为两张 H20、每卡一个进程、两分片、batch1。旧 Qwen 目标每卡3进程的一致性结果不能代替 LLaMA 验证；本轮不自动采用6分片。运行前后都不得抢占或终止其他项目进程。

第一阶段行为生成预算 640×512＝327,680 新 token，正式 Benchmark 两臂生成预算 614,400，合计 **942,080 新 token**。第二阶段新增行为预算 576×512＝294,912；正式原版与干预版重跑，生成预算 614,400，合计 **909,312**。两阶段合计满输出预算 **1,851,392 新 token**。这不是总计算量，还不含输入前向、选择题似然、激活、拟合、校准、评分与传输；实际生成可因原生终止标记提前结束。

未实测 LLaMA 吞吐前不承诺“几小时完成”。获运行授权后用计入正式预算的首批完成样本测时，按阶段/任务/条件外推；报告等待、模型加载、准备、生成、评分和收尾。不得用9B历史时间直接当本轮ETA。

##### 10. 结果能说明什么

| 结果 | 允许的结论 |
| --- | --- |
| 第一阶段PASS，第二阶段PASS | 当前固定表示映射及两通道配方在所测 LLaMA 上造成明确能力损伤；损伤效应跨家族复现 |
| 第一阶段PASS，第二阶段未获支持 | 稠密路线获支持；本轮两列近似/剂量实现未获支持 |
| 第一阶段STOP或INCONCLUSIVE_HOLD | 本轮固定层/映射/剂量路线未达到继续门，第二阶段没有运行结果 |
| 真实源与随机源诊断相近 | 当前诊断未证明源两针提供特异性优势；不能估计全模型普遍率 |
| 仅目标自身方向有效 | 目标存在可引发效应的干预，但本轮源→目标路线没有获支持 |
| 损伤存在，行为盲评未完成或未支持 | 能力损伤结论与行为未判定/未支持同时保留 |

“这条迁移配方有效”“源信息比随机有用”“两模型使用同一机制”是三个不同强度的主张。此 toy 首先检验第一个，随机诊断为第二个提供有限证据；第三个仍属于暂停的根因实验。

##### 11. 冻结与证据交付

运行前记录精确源/目标revision、权重完整性、所有输入与源码哈希、解释器与依赖版本、实际BOS/EOS与模板、数值设置、条件列表及本合同。映射之后且确认之前，再冻结矩阵、列号、符号、随机池、ρ、尺度公式和全部19臂。

所有新文件和记录位于本目录，不覆盖旧迁移结果。保留失败目录与错误日志；修复实现需记录新旧代码哈希、受影响记录及额外成本。禁止为获得正结果改变题目、层、剂量、选列、精度、窗口或评分。

原始回答、逐题分数、小型收据及源码进入仓库。模型权重、凭据、虚拟环境、第三方大下载不入Git；项目激活/映射保留外部路径、大小与SHA-256。具体推进门及授权规则见 [执行合同](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cross-family-transfer-toy-v1-2026-10-26/CONTRACT.zh-CN.md)。

##### 12. 实现入口与交付检查

代码入口固定为 `readiness.py`、`pipeline.py`、`mapping.py`、`benchmark.py`、`toy.py`、`gate.py`、`preflight.py`；跨模型适配及采集分别为 `engine.py`、`collect.py`。这些链接与具体选项应在 CPU 检查回执中核验，不以文档命令存在代替代码可执行。

- `readiness.py --source SOURCE_PATH --target TARGET_PATH --output RUN_PATH`：仅做CPU准备，核验输入、冻结与环境；完整通过才生成 `freeze.json` 和 GPU Ready 回执，资产不足保留阻塞结果。
- `pipeline.py --stage 1 --run PATH --target MODEL_PATH`：默认只显示第一阶段计划，不启动模型。
- `pipeline.py --stage 2 --run PATH --target MODEL_PATH`：默认只显示第二阶段计划；正式执行前必须验证本轮阶段门及证据哈希。
- 未来获得 GPU 运行授权后，才可在相应阶段命令加 `--execute`；第二阶段即便指定执行，也不得绕过门。

`gate.py` 分别对阶段1/2报告同一预注册损伤规则；阶段1的PASS是阶段2的必要条件，阶段2判定只用于报告，没有后继自动实验。

CPU 准备检查与 `preflight.py` 后续 GPU 实测检查分开记录。最终 GPU Ready 声明必须引用实际生成的准备回执；这里列出的状态定义不是已通过的检查结果。

---

### 原件 3：跨家族迁移准备回执

原路径：`experiments/cross-family-transfer-toy-v1-2026-10-26/PREPARATION.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cross-family-transfer-toy-v1-2026-10-26/PREPARATION.zh-CN.md) · [单独阅读副本](../library/4c3da22fc63486d6.md)；SHA-256：`4c3da22fc63486d68573b5166262319ef90d44baed9dedd780ee0bc22ffdee8a`。

---

#### 跨家族迁移准备回执

**最新状态：2026-10-26 15:02 北京时间已完成 GPU Ready。** 资产、CPU 测试和216个冻结输入均已校验；本次正式 GPU 实验未启动。完整交付见 [GPU Ready 结果](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cross-family-transfer-toy-v1-2026-10-26/GPU_READY.zh-CN.md)。下文保留14:28时的历史准备记录。

记录时间：2026-10-26 14:28 北京时间。状态为 **代码与 CPU 预检已完成，官方权重下载中，尚未 GPU Ready**。

##### 已验证

- 用户单独保存的 Hugging Face 下载凭据对应 `RuizhiXu`，已通过指定模型的官方访问检查。旧账号的拒绝记录保留；凭据在仓库外，不写入日志或 Git。
- 目标固定为 `meta-llama/Llama-3.1-8B-Instruct@0e9e39f249a16976918f6564b8830bc894c89659`，没有替换为已有的 Llama 3.0。
- 两阶段代码、[实验设计](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cross-family-transfer-toy-v1-2026-10-26/PROTOCOL.zh-CN.md)、[合同](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cross-family-transfer-toy-v1-2026-10-26/CONTRACT.zh-CN.md)与[执行说明](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cross-family-transfer-toy-v1-2026-10-26/EXECUTION.zh-CN.md)已写好。阶段二由阶段一的机器评分及绑定证据决定是否开放。
- 合成输入测试、CPU 微型随机 LLaMA 集成测试、阶段门负例测试已通过。它们验证实现，不是正式模型的实验结果。
- 真实 tokenizer 检查通过：320 份映射文档、11,777 个共同文字前缀位置；固定 Benchmark 输入未要求截断。详见 `validation-tokenizer-r01/receipt.json`。
- HumanEval 沙箱 5 项控制测试通过，59 个正式评分 task 离线加载成功，CPU 检查耗时 5.92 秒。详见 `validation-scoring-r01/receipt.json`。

##### 当前下载

截至 14:28，已取得约 4.87 / 16.06 GB，约 30.4%；4 个权重分片中 1 个已完整校验。根据当时最慢分片的实际速度，传输还需约 37 分钟。该估计不含完整文件哈希和最终 CPU 准备检查，也不是时间保证。

下载已转入独立后台续传，保留全部已有 partial 和失败/测速记录。当前权威进度是服务器 `assets/download-r02/progress.json`，完成证据应为同目录 `receipt.json` 的 `all_files_verified`；`download-r01` 是历史尝试。服务器权重目录是 `/workspace/models/Llama-3.1-8B-Instruct-0e9e39f2`。

##### 后续完成条件

下载完成后按执行说明运行 CPU-only `readiness.py`，首次正式准备目录为 `runs/llama31-r01`。重新核对完整源/目标资产哈希、全部代码与输入、tokenizer、评分和沙箱。只有 `GPU_READY.json` 明确为 `GPU_READY` 且 `freeze.json` 对应，才向用户报告 GPU Ready。此前的 `validation-cpu-r02/GPU_READY.json` 保留的是资产未齐时的准备状态，不能作为完成凭证。

本聊天定时跟进已更新为下载及 GPU Ready 准备，每 30 分钟检查，交付完成后暂停。不恢复此前已经完成的 9B/2B 队列。尚未授权启动本次正式 GPU 实验；准备期间不调用 `pipeline.py --execute`，也不干扰其他聊天在服务器上的工作。

---

### 原件 4：两阶段跨家族迁移：执行入口

原路径：`experiments/cross-family-transfer-toy-v1-2026-10-26/EXECUTION.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cross-family-transfer-toy-v1-2026-10-26/EXECUTION.zh-CN.md) · [单独阅读副本](../library/27c7b9e6601b343b.md)；SHA-256：`27c7b9e6601b343b1bb403ee8ec07895ef002a8356e40161cb17b07241016fa9`。

---

#### 两阶段跨家族迁移：执行入口

本版仅准备代码、合同、资产与 CPU 校验。根因实验暂停；以下 GPU 命令只有获得运行授权以后才执行。精确目标为 `meta-llama/Llama-3.1-8B-Instruct@0e9e39f249a16976918f6564b8830bc894c89659`。源模型固定 `Qwen/Qwen3.5-4B@851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`。

##### 1. 下载与准备

官方期望文件见 `assets/official-source-manifest.json`（目标）和 `assets/source-official-manifest.json`（源）。权重放在仓库外。源路径 `/data/models/Qwen3.5-4B-851bf6e`；目标计划路径 `/workspace/models/Llama-3.1-8B-Instruct-0e9e39f2`。

已有服务器账户 `sibozhu` 对指定仓库被拒，用户确认网页已授权的是 `RuizhiXu`。用户通过 `assets/save_hf_token.py` 隐藏输入并保存独立下载凭据，2026-10-26 官方账号和权重访问已核验通过，见 `assets/official-auth-ruizhixu-success-receipt.json`；没有替换旧账户，密钥不进入日志或 Git。当前后台续传见 `assets/asset-run-r02.json`，完成以 `assets/download-r02/receipt.json` 的完整官方哈希证据为准。临时传输通道保留 TLS 验证，凭据不发送给镜像。

在精确资产完成后，在服务器项目根目录执行 CPU 准备。输出目录必须全新；失败保留，修复后使用新目录：

```bash
CUDA_VISIBLE_DEVICES='' HF_HUB_OFFLINE=1 HF_DATASETS_OFFLINE=1 HF_HOME=/workspace/acupuncture/.cache/hf .venv-bench/bin/python -B experiments/cross-family-transfer-toy-v1-2026-10-26/readiness.py --output experiments/cross-family-transfer-toy-v1-2026-10-26/runs/llama31-r01
```

准备工具会运行合成测试和真正 CPU 微型随机 LLaMA 测试、核验原始数据及 128 份源校准记录、流式核对官方文件大小和哈希、检查跨 tokenizer 对齐、全部面板上下文长度、官方评分依赖和 HumanEval 隔离控制。不会加载实验模型权重，也不会运行 GPU。

`GPU_READY.json` 为 `GPU_READY` 且配套 `freeze.json` 有效，才表示具备提交实验的资产与代码条件。真实目标 GPU 预检仍将在未来运行的首批步骤执行。`CODE_READY_ASSET_BLOCKED` 表示代码测试通过但目标资产缺失；`PREPARATION_FAILED` 表示其他准备检查失败。这两种状态均不能启动 GPU。

##### 2. 只查看计划

```bash
.venv-bench/bin/python experiments/cross-family-transfer-toy-v1-2026-10-26/pipeline.py --stage 1 --run experiments/cross-family-transfer-toy-v1-2026-10-26/runs/llama31-r01 --target /workspace/models/Llama-3.1-8B-Instruct-0e9e39f2
```

默认只打印命令，不创建队列、不启动子进程。

##### 3. 未来获准后的 GPU 运行

在上面命令末尾显式加入 `--execute` 才会运行阶段一。运行器先重新核验资产和冻结输入，要求两张卡没有现存计算进程，然后按顺序执行：

1. GPU0 采集源 320 文档，GPU1 采集目标 320 文档及 128 对比输入；独立进程、实际 batch1。
2. CPU 拟合两层映射。任一层干净验证相对 MSE ≥1，记 `MAPPING_QUALITY_HOLD`，关闭后续 GPU 阶段。
3. 两卡分别在合成提示上做目标预检，核对零干预、恢复、打分和生成一致性。
4. 两卡完成本阶段 10 个 toy 条件，各含 64 行为场景与 64 能力诊断题。
5. 两卡完成固定主臂 `true_D_match` 与原版的 1,400 对能力 Benchmark。
6. 官方评分、HumanEval 沙箱、toy 导出及空白人工盲评包、阶段一判定。

只有 `stage1/gate.json` 为 `PASS`，且配对分数复算、映射质量、条件包与输入哈希全部一致，阶段二入口才开放。若已有授权覆盖两阶段，可按同一授权启动；本脚本不会自行后台启动第二阶段。

阶段二使用同一个已冻结 run、同一条件包，只将命令改为 `--stage 2 --execute`。它重新做目标预检，运行其余 9 个 toy 条件，再运行 `true_S_recipe` 与原版的完整 1,400 对 Benchmark。**本实现第二阶段重跑原版，不承诺缓存复用。** 最后采用相同的固定判定规则输出 `stage2/gate.json`，没有第三阶段。

##### 4. 判定、故障与证据

每任务计算原版减干预版的正确率差，MMLU 保留总体科目权重；配对/同上下文聚类抽样 10,000 次，名义 98.75% 区间用于四任务 Bonferroni 调整（有限样本覆盖为近似）。任一任务损伤点估计 ≥5 个百分点、区间下界 >0 且不一致配对 >5，则 `PASS`。全部任务区间上界 <5 且均有 >5 不一致配对，记 `STOP_SMALL_EFFECT`。其余记 `INCONCLUSIVE_HOLD`。完整机器评分零技术失败是前提。

运行错误留下 `queue.json` 与子步骤失败收据，对外为 `TECHNICAL_HOLD`；不覆盖、不删除、不自动改科学设置重试。映射质量未过是 `MAPPING_QUALITY_HOLD`。每次修复保留代码/输入哈希和旧目录，使用单独版本的新运行。修复不允许绕过阶段门。

收据路径：`collection-source/receipt.json`、`collection-target/receipt.json`、`mapping/quality.json`、`stageN/preflight-{0,1}/receipt.json`、`stageN/toy/shard{0,1}/receipt.json`、`stageN/benchmark/shard-{0,1}/receipt.json`、`stageN/benchmark/finish-r01/`、`stageN/export-r01/`、`stageN/gate.json`。`PRIVATE` 标记文件不能交给盲评者。

读取运行状态以收据中的完成数、活动进程身份和输入哈希为依据。代码存在、GPU 空闲、队列创建均不是实验完成。人工行为盲评与机器能力结果分开交付，不能由能力下降自动判定“有害建议”或共同机制。

##### 5. 计算量与 ETA

两阶段全部运行时，正式 Benchmark 为 5,600 个题目—条件单元；toy 为 1,216 次行为生成及 1,216 个选择题—条件单元。GSM8K 每输出最多 2,048 token、HumanEval 1,024、toy 行为 512；合计满生成预算 1,851,392 个新 token，另有上下文前向、选择题打分、模型加载、映射和评分成本。这不是墙钟保证上限。

初始每卡一个进程。跨家族尚无实测吞吐，当前不填 GPU ETA。未来报告根据已运行阶段实际时间和完成数外推，并把未测阶段作为独立速度场景；下载 ETA 单独报告。增加并发须先做本目标一致性验证，不能直接沿用 9B/2B 的验证结论。

---

### 原件 5：Llama-3.1-8B-Instruct 跨家族迁移：GPU Ready

原路径：`experiments/cross-family-transfer-toy-v1-2026-10-26/GPU_READY.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cross-family-transfer-toy-v1-2026-10-26/GPU_READY.zh-CN.md) · [单独阅读副本](../library/a7193e11ed5527ca.md)；SHA-256：`a7193e11ed5527ca4e17ea27cf7a6c684da28437f3a9776f39f03004de4c77a4`。

---

#### Llama-3.1-8B-Instruct 跨家族迁移：GPU Ready

2026-10-26 15:02:35 北京时间，最终 CPU 准备程序完成并输出 **GPU_READY**。本次交付的含义是代码、固定输入、模型资产和评分依赖已准备齐全；正式模型 GPU 预检、迁移采集、干预生成和能力评测均尚未运行。

##### 交付入口

- [实验设计](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cross-family-transfer-toy-v1-2026-10-26/PROTOCOL.zh-CN.md)：先映射稠密方向，再有条件地检验两通道近似。
- [执行合同](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cross-family-transfer-toy-v1-2026-10-26/CONTRACT.zh-CN.md)：固定科学设置、四项 Benchmark、阶段门、授权及失败保留规则。
- [执行说明](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cross-family-transfer-toy-v1-2026-10-26/EXECUTION.zh-CN.md)及[运行入口](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cross-family-transfer-toy-v1-2026-10-26/pipeline.py)：默认只显示计划，不运行模型。
- [GPU Ready 实际回执](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cross-family-transfer-toy-v1-2026-10-26/runs/llama31-r01/GPU_READY.json)、[216个输入冻结清单](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cross-family-transfer-toy-v1-2026-10-26/runs/llama31-r01/freeze.json)、[本地收回后逐项复核](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cross-family-transfer-toy-v1-2026-10-26/runs/llama31-r01/local-verification.json)。

##### 已验证的准备工作

1. 官方目标为 `meta-llama/Llama-3.1-8B-Instruct@0e9e39f249a16976918f6564b8830bc894c89659`，位于服务器 `/workspace/models/Llama-3.1-8B-Instruct-0e9e39f2`。四个权重分片共16,060,556,376字节，完整官方 SHA-256 全部匹配；官方小文件及权重索引覆盖亦通过。见[下载完成回执](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cross-family-transfer-toy-v1-2026-10-26/assets/download-r02/receipt.json)。
2. 最终准备重新核验源模型11个文件与目标10个必需文件的官方身份；没有以3.0、量化或适配器版本替代。
3. 四个 CPU 测试文件全部通过，包含真正的 CPU 微型随机 LLaMA 钩子、生成和评分集成测试，以及阶段门负例；这些是实现验证，不是正式模型效果。
4. 两端真实 tokenizer 在320文档、11,777个共同文字前缀位置对齐；128条对比输入和固定1,400题 Benchmark 上下文检查通过。
5. HumanEval 沙箱5项控制测试与59个离线评分任务加载通过。128份历史源校准、固定题库和相关代码进入冻结清单。本地收回后再次逐项核验216个文件哈希及 CPU 日志。

冻结清单 SHA-256：`53aa00e02c10216309af74ae0a330ec62f59e6b22da7fd6b66360a93fb3afa03`。

##### 实际耗时与 ETA 校对

- 第一次官方下载记录开始于14:11:46，全部文件校验完成于14:59:25，墙钟约47分39秒；包含路线试验和续传切换，已有 partial 没有重新下载。
- 最后一轮 CPU 准备：15:01:43至15:02:35，实测51.43秒。
- 前次给出的下载 ETA 为15:05–15:15；实际提前约6–16分钟。GPU实验尚未运行，因此没有实测实验 ETA。

##### 后续运行边界

启动仍需本次正式 GPU 运行授权。第一阶段 `true_D_match` 完成固定四项评测并通过合同中的 PASS 门，第二阶段 `true_S_recipe` 才开放；技术失败或结论不足不能被当作通过，也不能通过改题目、剂量或评分绕过。

收尾时两张 H20 均有其他任务占用（每卡约10,121MiB），未被本任务停止或抢占。GPU Ready 表示准备完成，不表示显卡已经为本轮预留。运行器仍会核验无其他活动计算进程，才执行未来获准的任务。本次没有恢复根因实验或修改静态权重。

---


## 时间、运行与停止收据索引

下面是所收集JSON的原有时间字段与状态，不把预计结束时间当实际完成时间。未列时间的文件仍有原件链接。完整JSON全部保存在原文归档，不能以此索引中的标量代替完整嵌套内容。

| 原件 | 原记录状态/阶段 | 原时间字段（原时区） |
|---|---|---|
| [assets/asset-blocker-receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cross-family-transfer-toy-v1-2026-10-26/assets/asset-blocker-receipt.json) | {"status": "blocked_official_gated_access"} | {"recorded_at_utc": "2026-10-26T05:46:37.597718+00:00"} |
| [assets/download-r01/aria2-probe-receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cross-family-transfer-toy-v1-2026-10-26/assets/download-r01/aria2-probe-receipt.json) | {} | {"started_at_utc": "2026-10-26T06:16:01.297166+00:00"} |
| [assets/download-r01/curl-8ranges-probe-receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cross-family-transfer-toy-v1-2026-10-26/assets/download-r01/curl-8ranges-probe-receipt.json) | {} | {"started_at_utc": "2026-10-26T06:18:56.342780+00:00"} |
| [assets/download-r01/probe-relocation-receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cross-family-transfer-toy-v1-2026-10-26/assets/download-r01/probe-relocation-receipt.json) | {} | {"moved_at_utc": "2026-10-26T06:27:34.386184+00:00"} |
| [assets/download-r01/progress.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cross-family-transfer-toy-v1-2026-10-26/assets/download-r01/progress.json) | {} | {"at_utc": "2026-10-26T06:23:54.398415+00:00"} |
| [assets/download-r01/small-files-receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cross-family-transfer-toy-v1-2026-10-26/assets/download-r01/small-files-receipt.json) | {"status": "small_files_verified"} | {"started_at_utc": "2026-10-26T06:11:46.434941+00:00", "completed_at_utc": "2026-10-26T06:12:09.359757+00:00"} |
| [assets/download-r01/start-receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cross-family-transfer-toy-v1-2026-10-26/assets/download-r01/start-receipt.json) | {} | {"started_at_utc": "2026-10-26T06:11:46.434941+00:00"} |
| [assets/download-r01/transport-receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cross-family-transfer-toy-v1-2026-10-26/assets/download-r01/transport-receipt.json) | {} | {} |
| [assets/download-r02/progress.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cross-family-transfer-toy-v1-2026-10-26/assets/download-r02/progress.json) | {"status": "downloading_or_verifying"} | {"at_utc": "2026-10-26T06:59:25.133598+00:00"} |
| [assets/download-r02/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cross-family-transfer-toy-v1-2026-10-26/assets/download-r02/receipt.json) | {"status": "all_files_verified"} | {"started_at_utc": "2026-10-26T06:25:00.805538+00:00", "completed_at_utc": "2026-10-26T06:59:25.134186+00:00"} |
| [assets/download-r02/start-receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cross-family-transfer-toy-v1-2026-10-26/assets/download-r02/start-receipt.json) | {} | {"started_at_utc": "2026-10-26T06:25:00.805538+00:00"} |
| [assets/download-r02/transition-receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cross-family-transfer-toy-v1-2026-10-26/assets/download-r02/transition-receipt.json) | {} | {"transition_at_utc": "2026-10-26T06:24:12.612431+00:00"} |
| [assets/environment-receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cross-family-transfer-toy-v1-2026-10-26/assets/environment-receipt.json) | {} | {"checked_at_utc": "2026-10-26T05:43:00.281922+00:00"} |
| [assets/official-access-receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cross-family-transfer-toy-v1-2026-10-26/assets/official-access-receipt.json) | {"status": "blocked_official_gated_access"} | {"checked_at_utc": "2026-10-26T05:43:42.291197+00:00"} |
| [assets/official-auth-diagnostic-receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cross-family-transfer-toy-v1-2026-10-26/assets/official-auth-diagnostic-receipt.json) | {} | {"recorded_at_utc": "2026-10-26T05:52:48.876429+00:00"} |
| [assets/official-auth-ruizhixu-success-receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cross-family-transfer-toy-v1-2026-10-26/assets/official-auth-ruizhixu-success-receipt.json) | {"status": "official_weight_access_verified"} | {"checked_at_utc": "2026-10-26T06:25:54.500801+00:00"} |
| [runs/llama31-r01/collection-source/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cross-family-transfer-toy-v1-2026-10-26/runs/llama31-r01/collection-source/receipt.json) | {"status": "completed"} | {"started_utc": "2026-10-26T09:03:58.809444+00:00", "ended_utc": "2026-10-26T09:04:41.421798+00:00"} |
| [runs/llama31-r01/collection-target/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cross-family-transfer-toy-v1-2026-10-26/runs/llama31-r01/collection-target/receipt.json) | {"status": "completed"} | {"started_utc": "2026-10-26T09:03:58.765970+00:00", "ended_utc": "2026-10-26T09:04:35.689643+00:00"} |
| [runs/llama31-r01/local-verification.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cross-family-transfer-toy-v1-2026-10-26/runs/llama31-r01/local-verification.json) | {"status": "PASS"} | {"verified_at_utc": "2026-10-26T07:04:55.697538+00:00"} |
| [runs/llama31-r01/mapping/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cross-family-transfer-toy-v1-2026-10-26/runs/llama31-r01/mapping/receipt.json) | {"status": "completed"} | {"started_utc": "2026-10-26T09:04:43.413222+00:00", "ended_utc": "2026-10-26T09:04:59.691271+00:00"} |
| [runs/llama31-r01/monitor/20261026T1421Z-local-earlier-files/toy/shard0/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cross-family-transfer-toy-v1-2026-10-26/runs/llama31-r01/monitor/20261026T1421Z-local-earlier-files/toy/shard0/receipt.json) | {"status": "running", "stage": 1} | {"started_utc": "2026-10-26T09:05:16.559282+00:00"} |
| [runs/llama31-r01/monitor/20261026T1421Z-local-earlier-files/toy/shard1/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cross-family-transfer-toy-v1-2026-10-26/runs/llama31-r01/monitor/20261026T1421Z-local-earlier-files/toy/shard1/receipt.json) | {"status": "running", "stage": 1} | {"started_utc": "2026-10-26T09:05:16.559327+00:00"} |
| [runs/llama31-r01/monitor/20261026T1421Z-stage1-local-verification.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cross-family-transfer-toy-v1-2026-10-26/runs/llama31-r01/monitor/20261026T1421Z-stage1-local-verification.json) | {"scope": "Stage1 complete evidence only; stage2 remains queued; no behavior labels inferred."} | {"verified_utc": "2026-10-26T14:22:56.845006+00:00"} |
| [runs/llama31-r01/sandbox-controls.jsonl.receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cross-family-transfer-toy-v1-2026-10-26/runs/llama31-r01/sandbox-controls.jsonl.receipt.json) | {"status": "completed"} | {"created_utc": "2026-10-26T07:02:33.749536+00:00"} |
| [runs/llama31-r01/stage1/benchmark/finish-r01/humaneval-execution.jsonl.receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cross-family-transfer-toy-v1-2026-10-26/runs/llama31-r01/stage1/benchmark/finish-r01/humaneval-execution.jsonl.receipt.json) | {"status": "completed"} | {"created_utc": "2026-10-26T13:42:27.310568+00:00"} |
| [runs/llama31-r01/stage1/benchmark/finish-r01/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cross-family-transfer-toy-v1-2026-10-26/runs/llama31-r01/stage1/benchmark/finish-r01/receipt.json) | {"status": "completed", "stage": 1} | {"started_utc": "2026-10-26T13:42:19.605420+00:00", "ended_utc": "2026-10-26T13:42:30.097866+00:00"} |
| [runs/llama31-r01/stage1/benchmark/finish-r01/summary.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cross-family-transfer-toy-v1-2026-10-26/runs/llama31-r01/stage1/benchmark/finish-r01/summary.json) | {"status": "completed", "scope": "Fixed latest 1400-item capability panel; behavior ratings are separate.", "stage": 1} | {"created_utc": "2026-10-26T13:42:29.771623+00:00"} |
| [runs/llama31-r01/stage1/benchmark/shard-0/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cross-family-transfer-toy-v1-2026-10-26/runs/llama31-r01/stage1/benchmark/shard-0/receipt.json) | {"status": "completed", "stage": 1} | {"started_utc": "2026-10-26T11:06:44.187801+00:00", "updated_utc": "2026-10-26T13:42:17.911939+00:00", "ended_utc": "2026-10-26T13:42:18.307067+00:00"} |
| [runs/llama31-r01/stage1/benchmark/shard-1/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cross-family-transfer-toy-v1-2026-10-26/runs/llama31-r01/stage1/benchmark/shard-1/receipt.json) | {"status": "completed", "stage": 1} | {"started_utc": "2026-10-26T11:06:44.187951+00:00", "updated_utc": "2026-10-26T13:39:44.151045+00:00", "ended_utc": "2026-10-26T13:39:44.529265+00:00"} |
| [runs/llama31-r01/stage1/export-r01/diagnostic.summary.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cross-family-transfer-toy-v1-2026-10-26/runs/llama31-r01/stage1/export-r01/diagnostic.summary.json) | {"status": "completed", "scope": "64-item diagnostic only; separate from the official 1400-item panel"} | {} |
| [runs/llama31-r01/stage1/export-r01/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cross-family-transfer-toy-v1-2026-10-26/runs/llama31-r01/stage1/export-r01/receipt.json) | {"status": "completed", "stage": 1} | {"ended_utc": "2026-10-26T13:42:32.214803+00:00"} |
| [runs/llama31-r01/stage1/gate.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cross-family-transfer-toy-v1-2026-10-26/runs/llama31-r01/stage1/gate.json) | {"stage": 1, "scope": "Operational gate for this fixed recipe and panel, not proof of a shared mechanism or global impossibility"} | {} |
| [runs/llama31-r01/stage1/preflight-0/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cross-family-transfer-toy-v1-2026-10-26/runs/llama31-r01/stage1/preflight-0/receipt.json) | {"status": "completed", "stage": 1} | {"started_utc": "2026-10-26T09:05:00.096925+00:00", "ended_utc": "2026-10-26T09:05:15.730260+00:00"} |
| [runs/llama31-r01/stage1/preflight-1/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cross-family-transfer-toy-v1-2026-10-26/runs/llama31-r01/stage1/preflight-1/receipt.json) | {"status": "completed", "stage": 1} | {"started_utc": "2026-10-26T09:05:00.096879+00:00", "ended_utc": "2026-10-26T09:05:15.589871+00:00"} |
| [runs/llama31-r01/stage1/toy/shard0/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cross-family-transfer-toy-v1-2026-10-26/runs/llama31-r01/stage1/toy/shard0/receipt.json) | {"status": "completed", "stage": 1} | {"started_utc": "2026-10-26T09:05:16.559282+00:00", "ended_utc": "2026-10-26T11:06:43.389596+00:00"} |
| [runs/llama31-r01/stage1/toy/shard1/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cross-family-transfer-toy-v1-2026-10-26/runs/llama31-r01/stage1/toy/shard1/receipt.json) | {"status": "completed", "stage": 1} | {"started_utc": "2026-10-26T09:05:16.559327+00:00", "ended_utc": "2026-10-26T11:04:16.306534+00:00"} |
| [runs/llama31-r01/user-stop-20261027-r02/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cross-family-transfer-toy-v1-2026-10-26/runs/llama31-r01/user-stop-20261027-r02/receipt.json) | {"status": "USER_STOPPED"} | {"stopped_utc": "2026-10-27T04:05:59.897276+00:00"} |
| [validation-scoring-r01/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cross-family-transfer-toy-v1-2026-10-26/validation-scoring-r01/receipt.json) | {"status": "completed"} | {"started_utc": "2026-10-26T06:17:42.304098+00:00", "ended_utc": "2026-10-26T06:17:48.219475+00:00"} |
| [validation-scoring-r01/sandbox-controls.jsonl.receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cross-family-transfer-toy-v1-2026-10-26/validation-scoring-r01/sandbox-controls.jsonl.receipt.json) | {"status": "completed"} | {"created_utc": "2026-10-26T06:17:46.753508+00:00"} |
| [validation-tokenizer-r01/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cross-family-transfer-toy-v1-2026-10-26/validation-tokenizer-r01/receipt.json) | {"status": "PASS"} | {"started_utc": "2026-10-26T06:13:35.175934+00:00", "ended_utc": "2026-10-26T06:13:52.654182+00:00"} |

## 全部原始资产入口

本目录在固定提交下共有2976个跟踪文件，包含代码、原回答、失败、收据和压缩证据；文件数不是样本数。[逐文件完整账本](../assets/006-cross-family-transfer-toy-v1-2026-10-26.tsv) · [原目录](https://github.com/yuxiexiong/acupuncture/tree/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cross-family-transfer-toy-v1-2026-10-26)。未复制模型权重、环境或凭据。
