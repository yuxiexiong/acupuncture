# 166．DWB r02：供体历史到指定写入

[返回总时间线](../README.zh-CN.md)

**时间定位**：已提取运行收据的最早时间锚点（可含预检） 2026-11-07T01:34:15.936232+08:00；不能当作全部子运行起止。

**当时的目的与设计**

同输入干净q/k下比较OO、DD、DO、OD；DO只在t1用供体V历史生成影子v，之后不保留供体V；另有纯局部L11d和供体受针S移植CSTd。两方向、48接收者、各348有序配对。

**实际过程、结果与后来更正**

DO净转移0.882/0.427，DD0.896/0.490，OD均0，冲突配对全部恢复自身；纯局部0.635/0.465。CSTd为0.094/0.799，两个方向分叉。3816次t1运行完成；授权序列化失败预检和重试完整保留。

**来源身份**：`cache-donor-write-bridge-v2-2026-11-07`；本章主体来源提交 `7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8`。下方原文中的状态是各文件写作时的状态，不能把早期“尚未运行”覆盖后期正式收据，也不能将后期结果倒填进早期设计。


## 原设计、执行过程、结果与更正全文

以下按“设计与题目 → 工程/执行记录 → 结果/更正 → 其他历史说明”组织；同类内没有可靠时间时保留路径顺序，不冒充严格先后。正文未删段；仅为本章节重排标题层级、把相对链接指向固定提交。原始字节另外完整保存。

### 原件 1：DWB-01 合同 r02：缓冲供体效应能否由 t1 的一次局部写入承接

原路径：`experiments/cache-donor-write-bridge-v2-2026-11-07/CONTRACT.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-donor-write-bridge-v2-2026-11-07/CONTRACT.zh-CN.md) · [单独阅读副本](../library/ea8488c9c4335daf.md)；SHA-256：`ea8488c9c4335dafb2ceacbad5c541bbe3a02737d604405a52666d517535f649`。

---

#### DWB-01 合同 r02：缓冲供体效应能否由 t1 的一次局部写入承接

**状态：r02 修订版，2026-11-07；本轮用户已明确授权修复、CPU 验收、GPU 预检及验收后正式运行。** r01 在 `62123e106` 冻结且未运行，原目录不改。本版复用 r01 的运行器与全部实验臂；修复判读及控制器超时，重新 CPU 验收和冻结后执行。是否完成分别以 readiness、freeze、runs 下收据为准，文档本身不代表运行完成。自查见 [DESIGN.zh-CN.md](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-donor-write-bridge-v2-2026-11-07/DESIGN.zh-CN.md)。本轮仅 DWB；后续读取与扩模型不自动启动。

##### 1. 问题

两块已有证据还没有接上：

- **SPF-01**：受针运行里换入供体的缓冲 V（q/k 用本输入干净运行的），完整回答跟随供体，净转移 0.896（N4146）、0.490（N1210）。
- **LVK-01 / SRU-01**：受针运行上，只在 t1 把写入项的 v 换成"本输入干净 V 历史下的当步 v"并对 k 去偏移，完整回答大量恢复；由此产生的状态差经 t2 直接读取改变回答。

本卡问三件事：

1. **不持续保留整块供体缓冲，只让供体影响 t1 这一次写入，之后的完整回答是否仍然跟随供体。**
2. **反过来，保留整块供体缓冲，但把 t1 这一次写入换回本输入的，跟随是否下降，以及下降是否伴随正常完整作答。**
3. **把供体的受针形成的递推状态放进干净接收者，答案跟谁。**

第 1、2 件把缓冲供体效应接到（或接不到）论文主链的写入端点。第 3 件检验受针形成的状态能否转移选择。阳性支持在该背景下仍有可利用的供体相关信息；阴性不排除信息残留，也不定位另一来源。

**承诺范围。** 只承诺"在这块开发面板、这些方向与这些操作下，供体跟随是否由 t1 的一次写入承接"。不承诺经 t2 直接读取传递（下一张卡）；不承诺这是自然路径；不解释原生停嘴；不承诺开发外、别的任务或别的模型成立。

##### 2. 固定条件

与 SPF-01 相同：Qwen3.5-4B revision `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`，BF16/eager/batch 1/torch 原核，L0 形成干预、NA 布局、B1 窗口、−1 强度、冻结校准、解析器与停止 ID。面板：LVK 新面板 48 条、6 场景。方向：N4146 主要，N1210 第二方向，跑同样的臂，分别判读，不互相替代。G = 14 个深层 GDN 层。供体：同场景的其余全部输入（每个接收者 8 个或 5 个）。

##### 3. 操作

每个场景内各形成一次干净缓存 C 与两个方向的受针缓存 T。除注明带钩子的臂外，全部是边界处的缓存替换。带钩子的臂只在 t1 这一步挂 LVK-01 的钩子，t2 起卸载，之后全部自然续写到停止或共 32 token。

“一次写入”在本卡中均指 **同一个 t1 时刻、14 个指定层的联合操作**，不是单层或单个写入事件。各层使用当前分支输入，允许下游自然响应；不把完整干净供体的 v 直接贴入接收者。

**t1 局部写入操作（原样复用 LVK-01 的 `LHook`）。** 在 14 个 G 层，写入项 β·k·vᵀ 里的 v 换成"影子 v"：用本分支当步的输入、本分支缓冲的 q/k 通道、**指定来源缓冲的 V 通道**重算卷积得到。擦除项不动。k 可选去偏移（LVK 的 k1）。影子量从不写回缓冲。

| 臂 | 接收缓存 | t1 写入项 | 之后留在缓冲里的 V | 桥接 / 用途 |
|---|---|---|---|---|
| C0 | 干净运行 | 原生 | — | 前提；对 LVK-01 干净记录 |
| L00 | T | 原生 | 受针 | 前提；对 LVK-01 的 L00 |
| L11o | T | v 来自**本输入**干净 V 历史，k 去偏移 | 受针 | 前提；对 LVK-01 的 L11 |
| **L11d** | T | v 来自**供体**干净 V 历史，k 去偏移 | 受针 | **纯局部形式** |
| OO | T + 本输入干净缓冲 | 原生 | 本输入 | 参照；对 LVK-01 的 F |
| DD | T + 供体 V + 本输入干净 q/k | 原生 | 供体 | 参照；对 SPF-01 的同一臂 |
| **DO** | 同 OO | v 来自供体干净 V 历史 | 本输入 | **只让供体影响 t1 这一次写入** |
| **OD** | 同 DD | v 来自本输入干净 V 历史 | 供体 | **保留供体缓冲，拿掉供体的 t1 写入** |
| **CSTd** | 干净运行，深层递推状态 ← **供体的受针运行** | 原生 | — | **区分臂**（缓存级，无钩子） |

2×2（q/k 都是本输入干净运行的）：

| | 之后留存的 V：本输入 | 之后留存的 V：供体 |
|---|---|---|
| **t1 写入的 v：本输入** | OO | OD |
| **t1 写入的 v：供体** | DO | DD |

同一行的两格在 t1 当步的全部计算按构造逐位相同（LVK-01 已核：卷积 V 通道的输出只进入递推内核）。这是工程闸门，不是发现。两格的差别只在 t1 之后 G 层卷积缓冲里留着谁的 V。

##### 4. 读数

沿用 SPF-01 冻结的统计量与界值（`spf_core.py`，原样导入）：

- 输出按自然完整回答分类为接收者列表的行号 0/1/2、"停止"或"其他"。
- **D_tr**：对齐供体上，输出落在供体目标行的比例，减去同一行在不预测它的供体下的出现率。任何与供体无关的输出下恰为 0。
- 区间：6 个场景重抽 10000 次的 95% 区间；配对差另报场景置换 p。
- 界值 M = 0.25，三档：下界 ≥ M"成立"，上界 ≤ M"低于界值"，其余"不可判"。
- 界值校核：各供体臂的构造零分布（接收者内打乱供体—输出对应，2000 次）97.5% 分位若达到 M，所有"成立"降为"不可判"。

| 读数 | 定义 | 回答什么 |
|---|---|---|
| REF | D_tr(DD) | 要桥接的效应在本次运行里存在 |
| **SUF** | D_tr(DO) | 一次供体写入是否足够 |
| **RET** | D_tr(OD) | 没有供体的 t1 写入、只留供体缓冲是否足够 |
| NEC | D_tr(DD) − D_tr(OD)，配对 | 替换供体的 t1 写入后效应是否下降到预设幅度 |
| **LOC** | D_tr(L11d) | LVK 的 L11 端点换成供体的 v 是否让回答跟随供体 |
| **SRC** | D_tr(CSTd) | 受针形成的状态是否仍带着可转移的选择 |

交付护栏：在供体与接收者预测可区分的 AL/BD 配对上，`valid_answer` 是能解析为任一列表编号的完整回答比例（停止和其他均无效），`y_self` 是答接收者目标的比例。只有 valid_answer(OD) ≥ 0.90 且 y_self(OD) ≥ 0.75 时，才允许给“下降伴随本输入作答恢复”标签。0.90/0.75 沿用 SPF 的交付/自身回答操作性标准，不代表等价性检验或信息有无；必须同时报告分子分母、残余效应与区间。

M=0.25 是量级门槛；低于门槛不等于零或消失。任何比值均不称机制份额；不依据点估计自动宣称“大部分”。

另报不设门槛的比值 D_tr(DO)/D_tr(DD)、D_tr(L11d)/D_tr(DD)，各臂的开口率、答自己的比例与错答类型。

##### 5. 冻结判读（看任何新输出前写定；实现在 `dwb_core.py`；每个结局在合成数据上出现过也缺席过，见 `analysis/rehearsal_output.txt`）

每个方向分别判读。三个科学问题分别判读；一个效应不成立不替代另一个问题的结果。所有阳性标签共同受预先定义的最大零分布校核约束。

**前提。** Y(C0) ≥ 0.90；Y(L00) ≤ 0.25；Y(OO) ≥ 0.75。纯局部形式另需 Y(L11o) ≥ 0.50。

**读法一：2×2（取第一个满足的）**

| 结局 | 条件 | 允许写的句子（都带效应量、区间与比值） | 不允许写的句子 |
|---|---|---|---|
| 前提不成立 | 前提任一不成立 | 这次执行或这块面板不适用 | 任何结论 |
| 参照缺失 | REF 低于界值 | SPF-01 的供体 V 效应在本次运行里没有以这个量级出现 | 效应不存在 |
| 不可判 | REF 不可判，或其余组合 | 报告数值 | "有趋势" |
| **写入支持且恢复本输入回答** | SUF 成立、RET 低于界值、NEC 成立；OD valid ≥0.90 且 self ≥0.75 | 指定写入足以产生达门槛的跟随；换回本输入写入后效应下降且低于门槛，多数回答恢复本输入目标 | 效应为零、全部消失；自然必要路径；全部效应 |
| 下降伴随交付退化 | 同前三项，OD valid <0.90 | 转移效应下降伴随完整交付不足，不能隔离选择变化与退化 | 写入承担或必要性 |
| 下降但未恢复本输入选择 | 同前三项，OD valid ≥0.90、self <0.75 | 多数仍能完整作答，但未恢复本输入目标；列错答分布 | 正确选择已恢复；写入必要性 |
| 两条路都通 | SUF 成立、RET 成立 | 两种指定操作分别足以产生达门槛的供体效应，不等于独立的自然通路 | 效应由写入承担 |
| 留存缓冲承担 | SUF 低于界值、RET 成立 | 单次指定写入未达门槛；保留供体 V 的操作达门槛；不证明所有作用仅在后续生成 | 写入无关 |
| 单独都不够 | SUF、RET 都低于界值 | 两个单独操作均未达门槛，联合参照达门槛；不能排除门槛以下的各自作用 | 给机制命名 |

**读法二：纯局部形式**

| 结局 | 条件 | 允许写 | 不允许写 |
|---|---|---|---|
| 不可判（前提） | 基本前提或 Y(L11o) 不成立 | 这个端点在本面板上不够好用 | — |
| **局部写入改答案** | LOC 成立 | 在原生受针运行上，不换任何缓冲，只把 t1 写入项的 v 换成供体 V 历史下的当步 v 并对 k 去偏移，完整回答跟随供体 | 这是原生失败的路径；k 是地址 |
| 局部写入不改答案 | LOC 低于界值 | 这个端点的供体效应低于预设门槛，不等于严格为零 | 写入无关（读法一另判） |
| 不可判 | 其余 | 报告数值 | — |

**读法三：区分臂**

| 结局 | 条件 | 允许写 | 不允许写 |
|---|---|---|---|
| **受针状态仍带选择** | SRC 成立 | 供体的受针形成的递推状态放进干净运行，答案跟随供体：受针状态里仍带着可被干净运行读出的选择 | 干预没有改变状态；受针运行里读不出的原因 |
| **不靠本输入的状态也答自己的** | SRC 低于界值且答自己的比例 ≥ 0.75 | 在这些替换下，干净接收者多数仍答自己的；不要求保留本输入原来的深层状态，但仍可能依赖换入状态及其计算 | 深层状态计算无关；存在"第二个来源"在某处；受针状态里没有信息 |
| 退化 | SRC 低于界值且答自己的比例 < 0.75 | 这种状态替换破坏了回答 | 关于来源的结论 |
| 不可判 | 其余 | 报告数值 | — |

失败类型：读法里"低于界值"的预测落空属科学失败；"不可判"属没拿到结果；前提不成立若出自实现属合同执行失败。

**看数据前登记的预期。**

| 预期 | 档位 | 依据 |
|---|---|---|
| REF 成立（两个方向） | 已有结果的重现 | SPF-01：0.896、0.490 |
| SUF 成立，比值 ≥ 0.75 | 类比 | LVK-01：本输入的局部 v 复现整体 V 恢复效应的 87%–97%；供体的没测过 |
| RET 低于界值，NEC 成立 | 类比，把握中等 | LVK-01：保留恢复过的 V 历史只有小幅调节 |
| LOC 成立，但低于 SUF | 类比，把握中等 | L11 本身在这块面板上不是满的（N4146 约 39/48） |
| SRC | **没有把握，略倾向"仍答自己的"** | SPF-01 里本输入的受针状态放进干净运行仍答自己的；4B 冗余多（近邻：移除关键块后仍 0.94） |

##### 6. 之后与退出

- 本卡只有一个阶段，结束后回来判断，不自动续跑。
- 读法一为"写入支持且恢复本输入回答"或"两条路都通"，或读法二为"局部写入改答案"：下一张卡把供体写入端点接进 SRU 的 t2 直接读取；下一张卡须区分 GDN 的递推读取与后续全注意力检索，不由状态移植层直接命名读取层。本卡不设计或运行该后续。
- 读法一为"留存缓冲承担""单独都不够"且读法二不成立：不写读取那张卡，"一次指定写入足够"这条简化解释到此为止，不扩大搜索范围。
- 任何结局都不改界值、不加臂重跑。N1210 同口径报告，不替代主要方向。

##### 7. 工程闸门（任一失败即停，记为合同执行失败，不是科学阴性）

1. 面板与分词账本哈希；形成哈希与 LVK-01 一致。
2. 桥接（逐位：t1 的 bf16 logits、首 token、自然 token 序列、终止方式）：C0、L00、L11o、OO 分别对 LVK-01 的干净、L00、L11、F 记录，每个方向每个接收者各一次。DD 对 SPF-01 同一（接收者，供体）对的记录（首 token、自然 token 序列、终止方式；SPF-01 没存 logits）。
3. 结构恒等：DO 与 DD、OD 与 OO 的 t1 logits 逐位相同；t1 之后两者的缓存只允许 G 层卷积 V 通道的旧槽不同。
4. 钩子：只在 t1 挂；每个 G 层的卷积与内核各被调用一次；自定义更新对 FP64 公式的相对误差 ≤ 1e−5；影子量不写回；t2 起无钩子，核函数复原。
5. 缓存级的臂（OO、DD、CSTd）：与背景缓存相比只有声明的部件不同，被换入的切片逐位等于来源。
6. CSTd 换入的递推状态确实被用到：其 t1 logits 与 C0 不同。
7. 源缓存哈希在全部臂跑完后不变。
8. 预检：NQ02 整场景、主要方向全部臂（174 条轨迹）。失败即停，允许一次有记录的修复重试。
9. 闸门只写对被检对象本身成立的关系。

##### 8. 预算

3816 条自然轨迹，其中 2184 条在 t1 带钩子（`analysis/rehearsal_output.txt`）。SPF-01 实测 0.75–0.84 秒每条（无钩子）；带钩子的每条在每个 G 层多一到两次影子卷积，会慢一些，这里不外推。**以本卡预检的实测单价为准：正式运行外推超过 2.5 小时即停下上报，不自行放宽。** 预检最多 0.3 小时；允许一次有记录的工程修复重试，额外最多 0.3 小时。全轮 GPU 进程墙钟上限 3.1 小时（0.3+0.3+2.5），包括加载、形成、桥接重放及生成，分别留收据；CPU 时间另记。控制器在场景内也执行硬超时，只终止本实验子进程。单进程。只存记录，不存张量，存储 ≤ 2 GiB。

##### 9. 本卡不回答的

- 供体写入之后，效应是否经 t2 的直接读取传递（下一张卡）。
- 跟随的是位置、实体还是答案编号（留给新面板）。
- 受针运行里为什么读不出状态里的选择，或另一条路在哪里。
- 原生停嘴如何形成；别的任务、模型、施针层位。
- 谁会因此改做法。

##### 10. 排程与运行授权

用户 2026-11-07 指令：修复合同、完成代码与 CPU 验收，验收后直接上卡；有其他项目时显存足够可并行，不足则排队。执行前核对现有任务和 GPU 显存；不停止、重启或改动其他项目。正式运行需同一冻结版本预检通过及耗时外推不超限，不以授权跳过验收。

---

### 原件 2：DWB-01 r02 偏离记录

原路径：`experiments/cache-donor-write-bridge-v2-2026-11-07/DEVIATIONS.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-donor-write-bridge-v2-2026-11-07/DEVIATIONS.zh-CN.md) · [单独阅读副本](../library/160babe12034580d.md)；SHA-256：`160babe12034580deed600ac57f8716c5308cea1e96348b0cb7b12ce42899dff`。

---

#### DWB-01 r02 偏离记录

2026-11-07：r01 已在 62123e106 冻结，未运行。本轮以新目录修复判读、重做验收；不修改 r01。冻结前的修订不是执行偏离。冻结后任何失败与重试在此之外另存版本化记录，保持冻结文件原样。

---

### 原件 3：D1：预检控制器验收失败，授权序列化修复

原路径：`experiments/cache-donor-write-bridge-v2-2026-11-07/deviations/D1-authorization-serialization.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-donor-write-bridge-v2-2026-11-07/deviations/D1-authorization-serialization.zh-CN.md) · [单独阅读副本](../library/012155d423a7226a.md)；SHA-256：`012155d423a7226ac152470bfd3c3b6cb24b11ef842129112f62bfed2494356e`。

---

#### D1：预检控制器验收失败，授权序列化修复

2026-11-07。预检 preflight-r02 的 worker 完成174条轨迹，墙钟89.80秒，模型与缓存工程断言全部通过；控制器在最终授权文件字节哈希核对处失败，未生成 verification，不记为通过或科学结果。

原因：本轮辅助脚本以 json.dump 写原始授权（无尾换行），运行器将同一对象通过 exp.write 归档后字节格式不同；两份解析后的 JSON 对象已核对完全相等。不是权限不足，不是模型阴性，也没有证据表明授权内容被改动。

修复：使用同一个 exp.write 写新的 authorization-preflight-r03.json；往返归档 SHA256 相等。新输出目录 runs/preflight-r03；原 authorization、控制器、worker、原始回答和失败日志完整保留。模型、操作、阈值、代码、CPU验收和 freeze-r02 均不变。此为合同允许的一次工程重试；两次预检均计入成本。正式授权也必须经相同序列化往返检查。

---

### 原件 4：DWB-01 r02：供体选择接到局部写入，两个方向的状态移植结果分叉

原路径：`experiments/cache-donor-write-bridge-v2-2026-11-07/REPORT.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-donor-write-bridge-v2-2026-11-07/REPORT.zh-CN.md) · [单独阅读副本](../library/e871fb58fea4af91.md)；SHA-256：`e871fb58fea4af91454d823a49978397f2e16284d1c72d5e4ed446fc5869c1d6`。

---

#### DWB-01 r02：供体选择接到局部写入，两个方向的状态移植结果分叉

2026-11-07。**正式运行完成、运行器验收通过、冻结判读完成、作者收尾复核通过。** 本轮按照用户授权完成合同修复、代码与 CPU 验收、预检、正式 GPU 运行和归档，没有自动续跑读取实验或扩模型。

##### 1. 结论

两个方向均支持：在指定受针背景与干净 q/k 条件下，不持续保留供体 V 缓冲，仅让供体 V 历史影响 t1 的指定写入操作，就足以产生达到预设门槛的完整回答转移；反向换回本输入写入后，净转移降为本样本中的 0，选择冲突配对全部恢复本输入答案。纯局部形式在两个方向也成立。

这把 SPF-01 的“缓冲供体改变选择”接到了 LVK-01 使用的写入端点。它仍未把这次供体差异接到 SRU 的 t2 直接读取，也未解释原生停答的完整自然路径。

状态区分臂没有给出统一答案：N4146 的净转移为 0.094，低于预设量级；N1210 为 0.799，达到门槛。因而不能把“受针状态不再携带可用选择”作为跨方向解释。

##### 2. 实验究竟操作了什么

Qwen3.5-4B，沿用冻结 revision、BF16/eager/torch 核、校准与解析器。48 个已见输入、6 个场景；每个方向 348 个同场景有序供体配对（AL 84、KS 96、RS 84、BD 84），两方向分别判读。统计不把这些重复配对当成独立样本。

“一次写入”指 **t1 同一时刻 14 个指定 GDN 层的联合操作**。使用当前分支输入和供体 V 历史计算影子 v；不是把完整干净供体运行的 v 直接贴入，也不是单层单事件。t2 起卸载钩子，自然续写，沿用 32 token 上限。

| 操作 | t1 写入来源 | 此后保留的 V | 条件 |
|---|---|---|---|
| OO | 本输入 | 本输入 | 本输入干净 q/k |
| DD | 供体 | 供体 | 本输入干净 q/k；重现 SPF 参照 |
| DO | 供体 | 本输入 | 本输入干净 q/k；检验指定写入是否足够 |
| OD | 本输入 | 供体 | 本输入干净 q/k；检验反向替换后的效应与完整作答 |
| L11d | 供体 V 历史下的影子 v，并对写入 k 去偏移 | 原生受针 V | 不整体恢复缓冲；LVK 纯局部形式 |
| CSTd | 无写入钩子 | 干净接收者原缓冲 | 换入供体受针运行形成的深层递推状态 |

DO/DD 与 OD/OO 在 t1 的结构恒等是工程检查。科学读数来自之后自然生成的完整回答，不把当步相等当成发现。

##### 3. 冻结读数与判读

下面为 D_tr（净供体转移对比量）及 95% 场景重抽区间；它不是准确率或机制份额。48 个接收者、6 个场景，重抽 10000 次；M=0.25 是预设量级门槛，不是零效应界限。构造零分布最大 97.5% 分位分别为 0.139、0.125，均低于 M。

| 操作 | N4146（主要方向） | N1210（第二方向） |
|---|---:|---:|
| DD：持续供体缓冲参照 | 0.896 [0.827, 0.956] | 0.490 [0.370, 0.595] |
| DO：只在 t1 写入供体差异 | **0.882 [0.820, 0.937]** | **0.427 [0.278, 0.556]** |
| OD：保留供体 V，t1 换回自身 | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |
| DD−OD：配对下降 | 0.896 [0.827, 0.956] | 0.490 [0.370, 0.595] |
| L11d：纯局部供体写入 | **0.635 [0.431, 0.812]** | **0.465 [0.346, 0.604]** |
| CSTd：受针供体状态进干净接收者 | 0.094 [0.042, 0.144] | **0.799 [0.588, 0.960]** |

DD、DO、DD−OD、L11d 两方向的场景符号置换 p 均为 0.03125；CSTd 分别为 0.125 与 0.03125。只有 6 个场景，这是开发面板不确定性，不是独立确认或广泛外推。

DO/DD 点估计比分别为 0.984、0.872；L11d/DD 为 0.709、0.950。仅作描述，不称“解释了 98% 的机制”，不宣称等效。

冻结程序给两个方向相同的前两个标签：`write_supported_with_self_recovery`、`local_write_redirects`。状态标签分别为 `own_answer_after_state_swap`、`needle_state_carries_selection`。

##### 4. 完整回答护栏与前提

| 前提：正确回答数 | N4146 | N1210 |
|---|---:|---:|
| 干净 C0 | 48/48 | 48/48 |
| 原生受针 L00 | 0/48 | 1/48 |
| 本输入缓冲恢复 OO | 48/48 | 48/48 |
| 本输入纯局部写入 L11o | 39/48 | 48/48 |

原生 L00 的停止/其他分别为 47/1、46/1；不能将“其他”合并成首步停止。以下每臂均为完整回答的冻结解析结果：

| 臂 | N4146 冲突配对答自己 / 168 | N1210 冲突配对答自己 / 168 | N4146 全部配对答自己 / 348 | N1210 全部配对答自己 / 348 |
|---|---:|---:|---:|---:|
| DD | 21 | 83 | 111 | 229 |
| DO | 24 | 88 | 121 | 236 |
| OD | **168** | **168** | **347** | **348** |
| L11d | 39 | 79 | 121 | 212 |
| CSTd | 154 | 52 | 330 | 202 |

AL/BD 冲突配对中所有臂均为 168/168 有效编号回答；全配对也是 348/348，无停止或其他。OD 的下降因此没有被交付退化混淆。N4146 的 OD 在全配对中仍有 1 条首列错答；不能写“所有配对都恢复正确”。D_tr 的样本值为零，也不等于总体效应严格为零。

##### 5. 可以进入正文的段落

> 在 Qwen3.5-4B 的指定受针条件和已见编号任务上，供体缓冲对答案选择的影响可以通过一个明确的写入操作传递。在恢复本输入 q/k 的条件下，仅在 t1 的 14 个指定 GDN 层以供体 V 历史计算写入项的 v，而不持续保留供体 V 缓冲，两个方向的完整回答净转移分别为 0.882 和 0.427。反之，保留供体 V 但将同一次写入换回本输入的，选择冲突配对均恢复本输入答案，净转移在该样本中为零。在不整体恢复缓冲的受针背景上，沿用局部 v 替换与写入 k 去偏移，也得到 0.635 和 0.465 的净转移。这些结果将缓冲中的供体相关差异连接到指定写入端点及后续完整答案。与此同时，受针供体状态在干净接收者中的转移因方向而异，限制了以“状态信息统一丢失”解释干预后果的主张。

这段是本次结果可用的正文材料，不表示现有论文全文已完成同步。它不主张原生必要路径、唯一储存位置、普遍修复，或位置/实体/编号已分清。

##### 6. 对论文补了哪块，仍缺哪块

- **补上：供体选择到局部写入的桥接。** SPF 的整块/通道替换阳性，现在有仅在指定时刻写入的构造性行为证据，并有反向替换与完整交付检查。纯局部形式使增量不只依赖整块干净 q/k 缓冲恢复。
- **新增边界：两个方向不共享简单的状态信息丢失解释。** N1210 支持受针形成的状态仍有可利用的供体相关选择；N4146 只是低于本门槛且多数答自己，不能写状态没有信息或计算无关。
- **仍缺：同一供体写入差异是否经 t2 的直接读取影响回答。** 原 SRU 的同输入修复端点不能自动替代本次供体端点证据。下一优先缺口仍是这条具体读取连接，不从本结果直接指定某些全注意力层为路径。
- **仍缺：独立新材料确认及更宽适用性。** 本卡复用已见 48 输入，不把 3816 次运行或 348 配对包装成新样本规模。位置、实体与答案编号的解耦、跨模型及任务证据均未补上。

本次达到合同中允许讨论下一张读取卡的条件；本轮到此收尾，没有改变门槛、加臂重跑或自动扩模型。

##### 7. 验收、偏离与资源

- 源码提交：`19c0531b34e5411c57e07a2646e8382f38ce4434`；预检证据提交：`260b992a2`。
- 冻结：`freeze-r02.json`，SHA256 `cf79bf42e1e5e2da6baddfbc6d58b0daaf48b303143e44d71d40747bd3a878a2`，58 个文件。旧 r01、旧证据与失败记录保留。
- CPU：6 项测试通过（6.373 秒）；资产、历史冻结、桥接参照与计数检查通过。
- 正式：48 接收者 / 6 场景 / 3816 次 t1 运行，2184 条带指定 t1 钩子；1032 项历史参照比较通过；结构、作用范围、钩子卸载、源缓存和模型权重完整性检查通过。程序返回码 0，正式 verification 为 passed。
- GPU 0 单进程，启动时两卡空闲，无需排队、没有停止其他任务；完成后两卡均 3 MiB 占用、利用率 0。正式峰值分配显存 11064794112 字节（约 10.31 GiB），不是整卡 nvidia-smi 占用。

| 运行 | GPU 进程墙钟秒 | 控制器验收 |
|---|---:|---|
| preflight-r02 | 89.800 | 失败：授权归档序列化字节差异 |
| preflight-r03 | 88.628 | 通过；6 输入模型输出与首轮一致 |
| formal-r02 | 1346.877 | 通过 |
| **合计** | **1525.304（0.423696 GPU 进程小时）** | 包括失败预检、加载、形成、参考重放与生成 |

正式约 22.45 分钟，低于 2.5 小时上限；全轮低于 3.1 小时上限。控制器墙钟另见 audit，未把 CPU 验收计成 GPU 时间。

预检 D1：辅助脚本无尾换行与归档序列化造成授权字节哈希不一致，内容对象相同；首轮未记为通过。改用相同序列化，仅做合同允许的一次工程重试，不改科学冻结。见 [D1](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-donor-write-bridge-v2-2026-11-07/deviations/D1-authorization-serialization.zh-CN.md)。另有收尾 CPU 复核脚本的函数引用错误，修复后通过，不重跑模型；原脚本和说明保留于 [postrun](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-donor-write-bridge-v2-2026-11-07/analysis/postrun/AUDIT-NOTE.zh-CN.md)。打包元数据的完整冻结字节说明见 [归档出处](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-donor-write-bridge-v2-2026-11-07/readiness/ARCHIVE_PROVENANCE.zh-CN.md)。

##### 8. 可核对入口

- [合同](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-donor-write-bridge-v2-2026-11-07/CONTRACT.zh-CN.md) · [设计自查](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-donor-write-bridge-v2-2026-11-07/DESIGN.zh-CN.md) · [CPU 就绪检查](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-donor-write-bridge-v2-2026-11-07/readiness/cpu-check-r02.json)
- [正式验收](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-donor-write-bridge-v2-2026-11-07/runs/formal-r02/verification.json) · [正式收据](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-donor-write-bridge-v2-2026-11-07/runs/formal-r02/worker-0/receipt.json) · [原始逐输入记录](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-donor-write-bridge-v2-2026-11-07/runs/formal-r02/worker-0/records)
- [冻结判读 JSON](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-donor-write-bridge-v2-2026-11-07/analysis/dwb-readouts-formal-r02.json) · [文本读数](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-donor-write-bridge-v2-2026-11-07/analysis/formal-readout-r02.txt)
- [作者哈希与分子分母复核](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-donor-write-bridge-v2-2026-11-07/analysis/postrun/audit-r02.json)（非独立评审）

---

### 原件 5：收尾 CPU 复核脚本修正

原路径：`experiments/cache-donor-write-bridge-v2-2026-11-07/analysis/postrun/AUDIT-NOTE.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-donor-write-bridge-v2-2026-11-07/analysis/postrun/AUDIT-NOTE.zh-CN.md) · [单独阅读副本](../library/d54e92edd8702028.md)；SHA-256：`d54e92edd87020282ba82ae342077d241be0f8af2b30e5106a317ab6e7d3d13f`。

---

#### 收尾 CPU 复核脚本修正

2026-11-07。正式模型运行与冻结的 `dwb_analysis.py` 均已完成并通过。另写的收尾核对脚本第一次运行在 `A.row_out` 处报 `AttributeError`：`dwb_analysis` 中解析器通过其 `A` 模块引用，而非直接导出。调用改为 `A.A.row_out` 与 `A.A.bucket`。原脚本保留为 `audit-initial.py.txt`。

这是收尾作者核对脚本的引用错误；未写出 audit-r02.json，没有新增模型运行、重做冻结统计或修改科学判据。该脚本位于 postrun 子目录，不属于实验冻结输入。最终是否通过以 `audit-r02.json` 为准；此核对不是独立评审。

---

### 原件 6：DWB-01 r02 设计卡与自查

原路径：`experiments/cache-donor-write-bridge-v2-2026-11-07/DESIGN.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-donor-write-bridge-v2-2026-11-07/DESIGN.zh-CN.md) · [单独阅读副本](../library/df8f1928d609b105.md)；SHA-256：`df8f1928d609b10534100475a56d4ba11a6d566dcd9352ecf3f07a568f7b358c`。

---

#### DWB-01 r02 设计卡与自查

2026-11-07；引用 experiment-design-self-check v1。同一助手审查、实现、验收，不称独立评审。来源：r01 `62123e106`、SPF `6d8f0e6`、LVK/SRU 冻结资产。r01 仅作历史来源，不沿用其通过标签。

主线：稀疏干预如何经状态形成、写入和读取改变完整回答。本轮：指定 t1 联合写入能否承接供体定向效应，以及替换写入后下降是否伴随本输入作答。
增量：在已有同输入修复之外，测试供体定向选择的局部承接、保留历史的条件作用及受针状态的可转移性。与 r01 的操作、臂、面板、供体、M 完全一致；只修复交付与门槛判读、收紧 SRC 阴性、加强时间上限执行。模型、层、位置、冻结输入、来源和操作见合同 §2–3；其余计算自然响应，不强行对齐后续生成。

估计对象：六场景开发面板上的条件操作总效果，不是原生中介份额。先例给出写入公式与移植工具；新科学测量在 t2 及以后，t1 恒等只作工程闸门。最不利已有证据：NWC 随机扰动亦可致错；SPF 受针状态单独不足引出供体跟随；N1210 有 32-token 截断；行/实体尚未分开。

| 项 | 判定与具体理由 |
|---|---|
| C01 | 通过：仍问写入如何改变完整回答，不改成停止修复。 |
| C02 | 通过：DO/OD/L11d/CSTd 新操作连接 SPF 与写入端点；不把 t1 恒等作发现。 |
| C03 | 通过：复用 SPF 统计、LVK LHook/桥接及历史模型与校准；不重造方法。 |
| C04 | 通过：上述最不利证据与预期并列，弱结果不扩搜索。 |
| C05 | 通过：当前分支输入构造影子 v，区别本输入/供体、历史/当前写入；14层联合。 |
| C06 | 通过：只 t1 操作，t2 后自然响应；不是后续固定。 |
| C07 | 通过（有限混合反事实）：写入 k 去偏移只在 L11 类臂，擦除 k 不改；与干净 q/k 四格分开判。 |
| C08 | 通过：OD 退化不判承担；低于 M 不称消失；SRC 阴性不推出状态计算无关。 |
| C09 | 通过：支持/保留历史有效/联合才达门槛/退化/不可判可区分；SRC 只有阳性支持可利用信息，不强制互斥解释。 |
| C10 | 通过：完整答案解析、AL/BD valid/self、供体效应与停止分类分开；新增交付护栏。 |
| C11 | 通过：工程恒等失败单列，低于门槛不称零；保留数值、异号与不可判。 |
| C12 | 通过：复用已存在运行器和 CPU 资产；3816 正式轨迹、174 预检；重建/桥接都计时。全轮上限3.1h含一次工程重试。 |
| C13 | 通过：48已见输入、6场景；配对不算独立问题；新目录保留r01冻结，哈希/收据不改。 |
| C14 | 通过：结果限制是否继续读取桥接，不自动扩层、换题或扩模型。 |

历史错误：E04/E19 用 t1 恒等验收；E05/E06/E15 对齐局部写入与背景，不拼成完整链；E07/E14 不宣称自然必要性；E10/E12 新增停止/其他反例及交付护栏；E11/E18 SRC 阴性不排除信息；E22/E23 不独立确认、不称独立验收；E24/E25 不要求完整机制且不加臂。其余 E01–E26 未触及的风险由原模型、题目、剂量、校准、来源冻结及退出条件控制；没有新的权重编辑或信息删除主张。

反方最强反例及处理：
1. DD/DO 强、OD 全停止：r01 会误判 write_carries。本版只判 transfer_reduced_with_degradation。
2. OD 正常但全首列：只判下降但未恢复本输入选择。
3. RET=0.20 且区间低于0.25：只能报告门槛以下残余，不能说消失；效应大小完整保留。
4. CSTd 仍答自己但状态仍参与计算：只支持不要求保留原状态，不支持状态无关或信息删除。
5. DO 与 DD t1 相同但之后不同：由旧V槽不同造成条件总效果，不能自动称 t2 直接读取中介；该检验留下一轮。

设计结论：r02 逻辑通过。工程验收独立记 readiness；授权来自本轮用户直接指令，不来自自查。CPU 先检查判读反例、消费者、原臂范围、计划/预算与旧资产哈希；GPU 预检再检查真实 t1 和完整回答桥接。完整科学阴性结束分支，不自动重跑。

---

### 原件 7：冻结归档说明

原路径：`experiments/cache-donor-write-bridge-v2-2026-11-07/readiness/ARCHIVE_PROVENANCE.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-donor-write-bridge-v2-2026-11-07/readiness/ARCHIVE_PROVENANCE.zh-CN.md) · [单独阅读副本](../library/f1c2812fcce38ee7.md)；SHA-256：`f1c2812fcce38ee7aca35f93b30340c064f45f391014a9c5d62528bfb329b6c8`。

---

#### 冻结归档说明

2026-11-07。macOS 打包时产生的六个 `._*.py` AppleDouble 附属文件（各163字节）被服务器冻结 glob 纳入清单；它们不是可执行模块，未被导入。为保持已经用于预检的 freeze-r02 哈希不变，按原始字节一并归档，不事后删除或改写冻结。主 Python 源码、CPU 源码清单及全部58项冻结哈希已逐项匹配。后续新版本打包应禁用 macOS 扩展元数据。本项不改变任何臂、阈值、模型输出或科学判读。

---


## 时间、运行与停止收据索引

下面是所收集JSON的原有时间字段与状态，不把预计结束时间当实际完成时间。未列时间的文件仍有原件链接。完整JSON全部保存在原文归档，不能以此索引中的标量代替完整嵌套内容。

| 原件 | 原记录状态/阶段 | 原时间字段（原时区） |
|---|---|---|
| [analysis/postrun/audit-r02.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-donor-write-bridge-v2-2026-11-07/analysis/postrun/audit-r02.json) | {"status": "passed"} | {} |
| [readiness/cpu-receipt-r02.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-donor-write-bridge-v2-2026-11-07/readiness/cpu-receipt-r02.json) | {"status": "passed"} | {} |
| [runs/formal-r02/controller.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-donor-write-bridge-v2-2026-11-07/runs/formal-r02/controller.json) | {"status": "completed", "stage": "formal"} | {"started_at": "2026-11-06T17:43:17.168228+00:00", "finished_at": "2026-11-06T18:05:50.436852+00:00"} |
| [runs/formal-r02/verification.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-donor-write-bridge-v2-2026-11-07/runs/formal-r02/verification.json) | {"status": "passed", "stage": "formal"} | {"verified_at": "2026-11-06T18:05:50.436698+00:00"} |
| [runs/formal-r02/worker-0/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-donor-write-bridge-v2-2026-11-07/runs/formal-r02/worker-0/receipt.json) | {"status": "completed", "stage": "formal"} | {"started_at": "2026-11-06T17:43:21.477097+00:00", "last_record_at": "2026-11-06T18:05:45.415179+00:00", "finished_at": "2026-11-06T18:05:48.353908+00:00"} |
| [runs/preflight-r02/controller.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-donor-write-bridge-v2-2026-11-07/runs/preflight-r02/controller.json) | {"status": "failed", "stage": "preflight"} | {"started_at": "2026-11-06T17:34:15.936232+00:00", "finished_at": "2026-11-06T17:35:51.957256+00:00"} |
| [runs/preflight-r02/worker-0/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-donor-write-bridge-v2-2026-11-07/runs/preflight-r02/worker-0/receipt.json) | {"status": "completed", "stage": "preflight"} | {"started_at": "2026-11-06T17:34:20.129585+00:00", "last_record_at": "2026-11-06T17:35:46.824678+00:00", "finished_at": "2026-11-06T17:35:49.929609+00:00"} |
| [runs/preflight-r03/controller.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-donor-write-bridge-v2-2026-11-07/runs/preflight-r03/controller.json) | {"status": "completed", "stage": "preflight"} | {"started_at": "2026-11-06T17:39:25.200211+00:00", "finished_at": "2026-11-06T17:41:01.226769+00:00"} |
| [runs/preflight-r03/verification.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-donor-write-bridge-v2-2026-11-07/runs/preflight-r03/verification.json) | {"status": "passed", "stage": "preflight"} | {"verified_at": "2026-11-06T17:41:01.226606+00:00"} |
| [runs/preflight-r03/worker-0/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-donor-write-bridge-v2-2026-11-07/runs/preflight-r03/worker-0/receipt.json) | {"status": "completed", "stage": "preflight"} | {"started_at": "2026-11-06T17:39:29.345756+00:00", "last_record_at": "2026-11-06T17:40:55.075445+00:00", "finished_at": "2026-11-06T17:40:57.973765+00:00"} |

## 全部原始资产入口

本目录在固定提交下共有146个跟踪文件，包含代码、原回答、失败、收据和压缩证据；文件数不是样本数。[逐文件完整账本](../assets/166-cache-donor-write-bridge-v2-2026-11-07.tsv) · [原目录](https://github.com/yuxiexiong/acupuncture/tree/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-donor-write-bridge-v2-2026-11-07)。未复制模型权重、环境或凭据。
