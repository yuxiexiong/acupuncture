# 110．NQK：补测q/k历史及联合污染

[返回总时间线](../README.zh-CN.md)

**时间定位**：已提取运行收据的最早时间锚点（可含预检） 2026-11-03T23:43:40.378908+08:00；不能当作全部子运行起止。

**当时的目的与设计**

补测此前缺失的q/k历史单项，并与V、S、KV联合比较。

**实际过程、结果与后来更正**

q/k单独致错的预测失败；不含受针q/k的V+S+KV已可致错。L12仍有旧错误未复现和新增错误，不能说q/k完全无关；两两组合由后继NPC补测。

**来源身份**：`cache-native-qk-history-v1-2026-11-03`；本章主体来源提交 `7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8`。下方原文中的状态是各文件写作时的状态，不能把早期“尚未运行”覆盖后期正式收据，也不能将后期结果倒填进早期设计。


## 原设计、执行过程、结果与更正全文

以下按“设计与题目 → 工程/执行记录 → 结果/更正 → 其他历史说明”组织；同类内没有可靠时间时保留路径顺序，不冒充严格先后。正文未删段；仅为本章节重排标题层级、把相对链接指向固定提交。原始字节另外完整保存。

### 原件 1：NQK-01 实验卡：联合损伤中漏测的 q/k 历史

原路径：`docs/cache-native-qk-history-v1-2026-11-03/PLAN.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/docs/cache-native-qk-history-v1-2026-11-03/PLAN.zh-CN.md) · [单独阅读副本](../library/79d75ca80ec24747.md)；SHA-256：`79d75ca80ec247478713d5b45040aacaa9f1725cdafd6ab20b6faf6126369d15`。

---

#### NQK-01 实验卡：联合损伤中漏测的 q/k 历史

2026-11-03。依据：[NSR-01 报告](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-native-s-reverse-v1-2026-11-03/REPORT.zh-CN.md)与 2026-11-03 讨论定稿。用户授权：“按照这里商量的，直接跑到完”。

##### 问题

NSR-01 中，干净运行 C 里单独换入受损的 S、V 历史或 KV 都不致错，只有全部深层（CJ）受损才致错。但 CJ 含 G 层卷积缓冲的 q/k 历史，三个单组都不含。本卡回答：**联合移植致错，是因为漏测的 q/k 历史，还是因为它与其他深层状态的配合？**

##### 操作（沿用 NSR-01 的面板、两个针、切点、生成设置与比较协议）

接收者为干净运行 C，供体为同一输入、同一针的 T：

| 格 | 换入的受损内容 |
|---|---|
| CQK | G 层卷积缓冲的 q/k 通道 [:V_LO]（有限卷积窗口内的值），V 通道保持 C |
| CVSK | G 层卷积 V 通道 [V_LO:]＋G 层 S＋深层 KV，即 CJ 去掉 q/k |

另跑 C 与两针 T 作桥接端点；CJ 与三个单组取自 NSR-01 正式记录，逐输入配对比较。L12 上 CJ 与 T 逐位相同，所以 L12 的问题等价于“原生损伤能否由 q/k 单独或其余部分单独带入”。

##### 判读（评审收紧后的措辞）

- **CQK 致错、CVSK 不致错**：支持“受针 q/k 历史在干净接收背景中单独足以致错”。不能直接说原生损伤主要由 q/k 造成，要比较错误数量、具体输入和异常类型与 CJ、T 是否一致。
- **CQK 不致错、CVSK 致错**：支持“V＋S＋KV 这个组合不含受针 q/k 也足以致错”。不能说三者缺一不可，两两组合没有测。
- **两者都致错**：两种不同的移植操作各自足以致错，不等于识别出两条独立的原生损伤路径。
- **两者都不致错、CJ 致错**：支持这两个状态块之间存在背景依赖的联合作用，但不知道具体由哪些部分配合。
- 不只看“有没有答错”：逐条配对报告哪些输入改变、错成什么、是否重现同一输入在 T、CJ 中的异常。部分复现和不同类型的错误都直接报告，不硬塞进四种结论。
- 不扫层、不拆头、不默认做 S/V/KV 两两组合。

---

### 原件 2：NQK-01 合同 r01：联合损伤中漏测的 q/k 历史

原路径：`experiments/cache-native-qk-history-v1-2026-11-03/CONTRACT.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-native-qk-history-v1-2026-11-03/CONTRACT.zh-CN.md) · [单独阅读副本](../library/77aa18a136a80385.md)；SHA-256：`77aa18a136a80385cd5acdae92831462bb776c165cd973fd7fd09ade37a0459d`。

---

#### NQK-01 合同 r01：联合损伤中漏测的 q/k 历史

依据：[NQK-01 实验卡](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/docs/cache-native-qk-history-v1-2026-11-03/PLAN.zh-CN.md)（2026-11-03 讨论定稿，含评审收紧后的判读措辞）。授权：2026-11-03 用户原话“按照这里商量的，直接跑到完”。冻结后不改本文件；偏离记入 `DEVIATIONS.zh-CN.md`。

##### 1. 问题与操作

NSR-01 中只有全部深层受损（CJ）才致错，而 CJ 含 G 层卷积缓冲的 q/k 历史，三个单组都不含。本轮问：联合移植致错，是因为漏测的 q/k 历史，还是因为与其他深层状态的配合？

沿用 NSR-01 的模型、面板（LVK 新面板 48 条）、两个针、形成流程、切点 τ（最后一个提示 token 之前）、生成设置（贪心，最多 32 个新 token；不加针、不挂钩子、不强制前缀）、G 层（14 层）、深层 KV 层（15,19,23,27,31）、V_LO = 4096。接收者为同一输入的干净运行 C；供体为同一输入、同一针的 T。

| 格 | 换入的受损内容（其余全部保持 C） |
|---|---|
| CQK | G 层卷积缓冲 q/k 通道 [:V_LO]（有限卷积窗口内的值），V 通道保持 C |
| CVSK | G 层卷积 V 通道 [V_LO:]＋G 层 S＋深层 KV（= CJ 去掉 q/k） |

另跑 C 与两针 T 作桥接端点。CJ、CS、CV、CK 取自 NSR-01 正式记录，逐输入配对。每条输入 7 条自然轨迹。

##### 2. 读数

- 主读数：自然完整回答 Y（`y_full`），全 48 条；相对 C 的改坏数与场景数；异常类型（NSR-01 的冻结定义：停止 / 错选编号 / 混合编号 / 其他）。
- **逐条配对**：对 CQK、CVSK 各自改坏的输入，报告其中有多少在同一输入的 T、CJ 中也改坏，异常类型相同的数量，输出文本完全相同的数量，以及 T、CJ 改坏而本格没有改坏的数量。另报 CJ 改坏的输入中，由 CQK、CVSK、两者之一、两者都不能单独带入的数量。
- 首步描述（B、首 token 分类）同 NCC-01，只描述。
- 汇总：逐输入、六场景等权；场景分层 bootstrap（2000 次，种子 20261103）。不算比例，不设总标签。

##### 3. 判读（评审收紧后的措辞，冻结）

- **CQK 致错、CVSK 不致错**：支持“受针 q/k 历史在干净接收背景中单独足以致错”。不能直接说原生损伤主要由 q/k 造成，要比较错误数量、具体输入和异常类型与 CJ、T 是否一致。
- **CQK 不致错、CVSK 致错**：支持“V＋S＋KV 这个组合不含受针 q/k 也足以致错”。不能说三者缺一不可，两两组合没有测。
- **两者都致错**：两种不同的移植操作各自足以致错，不等于识别出两条独立的原生损伤路径。
- **两者都不致错、CJ 致错**：支持这两个状态块之间存在背景依赖的联合作用，但不知道具体由哪些部分配合。
- 部分复现、不同类型的错误都直接报告，不硬塞进四种结论。不扫层、不拆头、不做两两组合。

**工作预测**（数据前登记，只写方向，不是预定结论）：CQK 会致错（推测，依据 QCO-01、QKF-01 中受针 q/k 共同偏移经由 k 致错的结果）；CVSK 不作预测。

##### 4. 工程闸门（运行中断言，任一失败即停）

1. 形成 hash 等于 NCC-01 与 NSR-01；C 与两针 T 的 t1 bf16 logits 和自然 token 等于 NCC-01 正式记录。
2. CQK：卷积通道 [:V_LO] 等于 T，[V_LO:] 等于 C；CVSK：卷积 [V_LO:]、S、KV 等于 T，卷积 [:V_LO] 等于 C；其余所有张量逐位等于 C；接收者与 T 前后 hash 不变。
3. 布局、停止集合与解析器一致。
4. 预检自换：以 C 自己为供体替换 q/k，缓存不变、t1 等于 C（2 次工程前向）。
5. 分析端核对：本轮的 T 自然 token 等于 NSR-01 的 T；NSR-01 记录 sha 一致。

6.2 演示（`test_nqk.py`）：两格的通道切分与保留、违规拦截、逐条配对计数、分析入口端到端。冻结前真实模型冒烟须全部通过。

##### 5. 预算

| 项 | 正式 48 | 预检 2 |
|---|---:|---:|
| 形成 / 前缀预填 / 形成 token | 144 / 48 / 3834 | 6 / 2 / 162 |
| t1 / 自然轨迹 | 336 / 336 | 14 / 14 |
| 续写步上限 | 10416 | 434 |
| 工程前向 | 0 | 2 |

设备时间：正式 0.8 GPUh，预检 0.1，冒烟另计，合计 ≤1.0 GPUh。存储上限 8 GiB。worker 与 GPU 由授权文件中的 `gpu_map` 指定，不与他人共卡。

##### 6. 停止与失败

任一闸门失败为合同执行失败，信息量为零。预检允许一次有记录的实现修复；正式开始后不修、不重试。结果弱或不可判时不加格。完成即停。产物：原始记录、verification、DEVIATIONS、`analysis/nqk-readouts-r01.json`、短报告。

---

### 原件 3：NQK-01 偏离日志

原路径：`experiments/cache-native-qk-history-v1-2026-11-03/DEVIATIONS.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-native-qk-history-v1-2026-11-03/DEVIATIONS.zh-CN.md) · [单独阅读副本](../library/c8caa5cad7550fb9.md)；SHA-256：`c8caa5cad7550fb95fa1b2fe97f933b3484f1d79aad3cf24e827052a06b23343`。

---

#### NQK-01 偏离日志

（冻结 r01 时无偏离。）

---

### 原件 4：NQK-01 报告：联合损伤中漏测的 q/k 历史

原路径：`experiments/cache-native-qk-history-v1-2026-11-03/REPORT.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-native-qk-history-v1-2026-11-03/REPORT.zh-CN.md) · [单独阅读副本](../library/a6289fa8d0c22683.md)；SHA-256：`a6289fa8d0c2268333fc80c43e8b869b7e9a8c3f3295a6444fb008ea312c3255`。

---

#### NQK-01 报告：联合损伤中漏测的 q/k 历史

> **更正（2026-11-03，评审后）**：§6 原写“q/k 已被排除”，改为“不含受损 q/k 的组合已足以致错（q/k 仍可能调节个别输入）”；“受损 S 被受损的 V 或 KV 读取”改为不预设机制的表述。读数不变。

2026-11-03。合同 [r01](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-native-qk-history-v1-2026-11-03/CONTRACT.zh-CN.md)，冻结 `1cf52b39`（main `33d56e3`）。探索性比较，已见开发面板 48 条，作者执行，未经独立评审。全部读数来自冻结分析 [`analysis/nqk-readouts-r01.json`](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-native-qk-history-v1-2026-11-03/analysis/nqk-readouts-r01.json)。

##### 先说不利的部分

1. **我登记的工作预测落空。** 预测"CQK 会致错"（依据 QCO-01、QKF-01），实际两针都是 0 条错。这与 QCO/QKF 不是同一测量：那里是把受针 q/k 偏移加进已恢复 V 的受损背景，这里是把受损 q/k 历史放进干净运行，不登记为矛盾。
2. **L12 的复现不是逐条完全一致**：CVSK 复现了 CJ 改坏的 17 条中的 15 条，另有 3 条 CJ 没有改坏的输入被改坏，异常类型和文本的一致度也低于 L0（见 §3）。
3. **提交过程中一次 SSH 断连**：冻结文件和就绪收据曾漏交一次（`90f234f`），已补交（`33d56e3`），哈希逐一核对一致，运行未受影响。

##### 1. 执行与验收

| 项 | 结果 |
|---|---|
| 冒烟 r01 | 一次通过：C 与两针 T 逐位桥接到 NCC-01；替换只改指定通道；自换不变 |
| 预检 r01（2 输入，GPU1） | 通过，40 s；外推 568 设备秒 |
| 正式 r01（48 输入，GPU0+GPU1） | 通过；墙钟 319 + 220 s |

本轮的 T 与 NSR-01 的 T 自然 token 逐条一致，NSR-01 记录 sha 核对一致。全部计数在上限内（轨迹 273/336，续写步 2953/10416）。合计约 0.17 GPUh（含预检与冒烟），无偏离。

##### 2. 主读数：自然完整回答（接收者为干净运行 C，C = 48/48）

| 针 | T（原生） | CQK（受损 q/k 历史） | CVSK（受损 V＋S＋KV） | CJ（全部深层，NSR-01） |
|---|---:|---:|---:|---:|
| L0 | 0 | **48** | **2** | 2 |
| L12 | 31 | **48** | **30** | 31 |

**异常类型**（停止 / 错选编号 / 混合编号 / 其他）：
- L0：CVSK 为 16 / 0 / 30 / 0，CJ 为 18 / 0 / 28 / 0，T 为 47 / 0 / 1 / 0。CVSK 与 CJ 的类型重叠度 0.96，与 T 为 0.37。
- L12：CVSK 为 0 / 5 / 13 / 0，CJ 与 T 都是 0 / 3 / 14 / 0。CVSK 与二者的类型重叠度都是 0.90。

**首步分差相对 C**：
- CQK 只有 −0.66（L0）和 +0.14（L12），48 条全部仍以编号开头；
- CVSK 为 −9.62（L0）和 −8.69（L12），与 CJ 的 −9.68 和 −8.70 几乎相同。

##### 3. 逐条配对

| | L0：CVSK | L12：CVSK |
|---|---:|---:|
| 改坏的输入 | 46 | 18 |
| 其中 CJ 也改坏 | 46 | 15 |
| 其中异常类型与 CJ 相同 | 42 | 13 |
| 其中输出文本与 CJ 完全相同 | 41 | 8 |
| CJ 改坏而 CVSK 没改坏 | 0 | 2 |
| 其中 T 也改坏 / 类型与 T 相同 | 46 / 17 | 15 / 13 |

CJ 改坏的输入中，能由 CQK 单独带入的为 0（两针）；能由 CVSK 单独带入的，L0 为 46/46，L12 为 15/17。

##### 4. 按合同 §3 的读法

**CQK 不致错、CVSK 致错**：支持"V＋S＋KV 这个组合不含受针 q/k 也足以在干净运行中致错"。联合移植致错不是因为漏测的 q/k 历史。

- 在 L0 上，CVSK 几乎逐条重现了 CJ：同一批输入、多数同一异常类型、41 条文本一字不差。受损 q/k 历史在这里的额外作用很小。
- 在 L12 上，CVSK 复现了 CJ（也就是原生 T）的大部分改坏，但有 2 条没复现、3 条新增，说明受损 q/k 在 L12 上对个别输入有影响，只是单独不致错。
- 不能说 V、S、KV 三者缺一不可：两两组合没有测。结合 NSR-01，三者各自单独都不致错，组合起来才致错。
- L0 上，深层全部受损而浅层第 1–12 层干净时，异常形态是"停止＋混合编号"，不是原生的"停止"为主（与 NSR-01 相同）。

##### 5. 能说和不能说

**能说**：
- 两针上，受损的深层卷积 q/k 历史单独放进干净运行都不致错；
- 不含 q/k 的 V＋S＋KV 组合足以致错，并在 L0 上几乎逐条重现全部深层受损的结果；
- 与 NSR-01 合起来：V、S、KV 各自单独可被容忍，组合起来才改变答案。

**不能说**：
- 哪两个组合就够，或三者缺一不可；
- q/k 历史与损伤无关：L12 上有个别输入的差异；
- 原生损伤路径（这些都是干净背景中的移植结果）；
- 推广到其他针、层、任务或模型。

##### 6. 下一步候选（未授权，不自动执行）

1. **V、S、KV 的两两组合**（S+V、S+K、V+K，每针 3 格）。不含受损 q/k 的组合已足以致错（q/k 仍可能调节个别输入），"各自可容忍、组合才致错"现在是明确要解释的现象，两两组合是找出逐条最小组合的最直接一步。
2. **为什么各自可容忍、组合才改变答案**：NSR-01 显示 S 能影响答案选择，而受损 S 单独不改写答案。S 与 V 历史或 KV 的联合变化经过写入、读取还是后续传播，需要另立设计区分。

---

### 原件 5：NQK-01 决策日志

原路径：`experiments/cache-native-qk-history-v1-2026-11-03/DECISIONS.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-native-qk-history-v1-2026-11-03/DECISIONS.zh-CN.md) · [单独阅读副本](../library/2b2f8d47f11a2de4.md)；SHA-256：`2b2f8d47f11a2de4f8226b4aa3b3e22adfed6a1cfff9010bf60e66fbedbc07ae`。

---

#### NQK-01 决策日志

**D1（冻结前）实现方式。** 运行器从 NSR-01 冻结的 `nsr_run.py` 改出；首步读数、首 token 分类、异常类型、记录加载复用 NCC-01 与 NSR-01 冻结代码。NCC 的替换函数只支持“从 V_LO 起”的通道切片，所以 `nqk_core` 另写了支持 [:V_LO] 的替换与核对函数，并单独测试。

**D2（冻结前）CJ 不重跑。** CJ、CS、CV、CK 取自 NSR-01 正式记录，用记录 sha 与 T 的自然 token 核对一致后逐输入配对；本轮只跑 C、两针 T（桥接）与两个新格。

---


## 时间、运行与停止收据索引

下面是所收集JSON的原有时间字段与状态，不把预计结束时间当实际完成时间。未列时间的文件仍有原件链接。完整JSON全部保存在原文归档，不能以此索引中的标量代替完整嵌套内容。

| 原件 | 原记录状态/阶段 | 原时间字段（原时区） |
|---|---|---|
| [readiness/cpu-receipt-r01.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-native-qk-history-v1-2026-11-03/readiness/cpu-receipt-r01.json) | {"status": "passed"} | {} |
| [runs/formal-r01/controller.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-native-qk-history-v1-2026-11-03/runs/formal-r01/controller.json) | {"status": "completed", "stage": "formal"} | {"started_at": "2026-11-03T15:44:35.034637+00:00", "finished_at": "2026-11-03T15:49:59.314414+00:00"} |
| [runs/formal-r01/verification.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-native-qk-history-v1-2026-11-03/runs/formal-r01/verification.json) | {"status": "passed", "stage": "formal"} | {"verified_at": "2026-11-03T15:49:59.314211+00:00"} |
| [runs/formal-r01/worker-0/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-native-qk-history-v1-2026-11-03/runs/formal-r01/worker-0/receipt.json) | {"status": "completed", "stage": "formal"} | {"started_at": "2026-11-03T15:44:39.234054+00:00", "last_record_at": "2026-11-03T15:49:54.618838+00:00", "finished_at": "2026-11-03T15:49:57.852179+00:00"} |
| [runs/formal-r01/worker-1/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-native-qk-history-v1-2026-11-03/runs/formal-r01/worker-1/receipt.json) | {"status": "completed", "stage": "formal"} | {"started_at": "2026-11-03T15:44:39.324980+00:00", "last_record_at": "2026-11-03T15:48:17.500853+00:00", "finished_at": "2026-11-03T15:48:19.699089+00:00"} |
| [runs/preflight-r01/controller.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-native-qk-history-v1-2026-11-03/runs/preflight-r01/controller.json) | {"status": "completed", "stage": "preflight"} | {"started_at": "2026-11-03T15:43:40.378908+00:00", "finished_at": "2026-11-03T15:44:25.431871+00:00"} |
| [runs/preflight-r01/verification.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-native-qk-history-v1-2026-11-03/runs/preflight-r01/verification.json) | {"status": "passed", "stage": "preflight"} | {"verified_at": "2026-11-03T15:44:25.431711+00:00"} |
| [runs/preflight-r01/worker-0/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-native-qk-history-v1-2026-11-03/runs/preflight-r01/worker-0/receipt.json) | {"status": "completed", "stage": "preflight"} | {"started_at": "2026-11-03T15:43:44.649918+00:00", "last_record_at": "2026-11-03T15:44:21.525781+00:00", "finished_at": "2026-11-03T15:44:24.391121+00:00"} |

## 全部原始资产入口

本目录在固定提交下共有98个跟踪文件，包含代码、原回答、失败、收据和压缩证据；文件数不是样本数。[逐文件完整账本](../assets/110-cache-native-qk-history-v1-2026-11-03.tsv) · [原目录](https://github.com/yuxiexiong/acupuncture/tree/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-native-qk-history-v1-2026-11-03)。未复制模型权重、环境或凭据。
