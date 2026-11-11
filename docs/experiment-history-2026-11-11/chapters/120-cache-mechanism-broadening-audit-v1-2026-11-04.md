# 120．拓宽前的旧读数库存核对

[返回总时间线](../README.zh-CN.md)

**时间定位**：版本/记录日期 2026-11-04；未从所选收据确定完整运行起止，不据目录名补写时刻。

**当时的目的与设计**

核对240份JSON、432行读数，检查哪些已有端点能复用。

**实际过程、结果与后来更正**

144行M可复用、288行缺失；自然t2哈希不能还原logits或状态。这里是资产审计，没有新任务结果。

**来源身份**：`cache-mechanism-broadening-audit-v1-2026-11-04`；本章主体来源提交 `7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8`。下方原文中的状态是各文件写作时的状态，不能把早期“尚未运行”覆盖后期正式收据，也不能将后期结果倒填进早期设计。


## 原设计、执行过程、结果与更正全文

以下按“设计与题目 → 工程/执行记录 → 结果/更正 → 其他历史说明”组织；同类内没有可靠时间时保留路径顺序，不冒充严格先后。正文未删段；仅为本章节重排标题层级、把相对链接指向固定提交。原始字节另外完整保存。

### 原件 1：Acupuncture：核心贡献、最小补证与退出路线图

原路径：`docs/cache-mechanism-broadening-roadmap-2026-11-04.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/docs/cache-mechanism-broadening-roadmap-2026-11-04.zh-CN.md) · [单独阅读副本](../library/8e2652bdd55d897b.md)；SHA-256：`8e2652bdd55d897bf2f924dbcef81668a4693c92228229447828232c5c1be664`。

---

#### Acupuncture：核心贡献、最小补证与退出路线图

> **状态更新（2026-11-08，用户确认）：本页保留为历史方案，非当前执行队列。** 当前目标见[核心目标与任务口径](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/docs/cache-mechanism-current-goal.zh-CN.md)：先解释针怎样改变一项重要历史信号的写入或利用及其答案后果，允许有价值的部分解释。下文“当前／唯一顺序／下一优先”均按原日期阅读；本页不授权新设计或模型运行，已有结果和原方案不改。

v8；2026-11-05。当前以[Proposal v8](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/docs/mechanism-second-half-v1-2026-11-03/PROPOSAL.zh-CN.md)及[作者自查](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/docs/mechanism-second-half-v1-2026-11-03/CORE_CONTRIBUTION_SELF_CHECK.zh-CN.md)为准。**仅更新文档，无新模型运行或授权。** [v7历史快照](https://github.com/yuxiexiong/acupuncture/blob/13f066555e7f27a1bd4e56c9a48a376c9c96aaf7/docs/cache-mechanism-broadening-roadmap-2026-11-04.zh-CN.md)保留；WPC默认先行、KV读取续卡及线性R1–R5不再是当前队列。

##### 1. 一句话核心与全文目标

候选H-WR：**原生稀疏干预形成的写入状态，能在接收开头固定的条件下，经特定后续直接读取用途，重新造成实质答案选择错误；这一关系应超出随机幅度与另一用途的作用，并能在未见材料确认。**

不是“状态重要”或“KV带答案”。相对两篇最近邻，增量落在稀疏干预的具体失效关系、原生状态来源、完整回答及冻结关系的确认，而非正常记忆分工或已有写读公式。

H-WR尚未成立。第二版论文必须有具体问题、同端点计算证据、原生来源致错证据、开发外确认和边界；它是值得评审的有界机制论文形态，不是CCF A保证，也不等于解释所有原生行为。

##### 2. 先统一已有资产的角色

| 资产 | 作用 | 必须保留的限制 |
|---|---|---|
| 原始干预/粗跨针观察 | 提供失败现象及覆盖 | 不能当共同完整机制的票数 |
| LVK→SRU | 全文已有计算主体 | 接收底座为T，仅t1写入项人工修改；与整段V历史恢复区分。t2比较L10/L11，不是L00的自然t2 |
| 原生首步与NVW | 问题形态、局部写入变量及原生仅k不足 | 不把停止和选错混成同一指标，不以开口当完整正确 |
| NCC/NSR等 | 原生恢复与组合约束 | 整组S恢复足够不证明D用途或唯一载体；干净背景S污染阴性、L12天花板保留 |
| CGV/WIN/KVC | 跨条件边界与内容桥接 | 不冒充旧链完整推广，不默认开新读头定位 |
| A/B（未运行） | 原生来源与开发外确认的最小补证 | 不等于原生L00自己的读取路径、全部形成解释或实用方法 |

细读取证据主要是L0的N4146、N1210、R0三条件。14个G层是联合操作范围；L10/L11是端点标签。不能把粗14方向、不同实验的阳性格累加成十几针共同机制。

##### 3. 唯一当前顺序

| 阶段 | 工作与交付 | 进入/退出 |
|---|---|---|
| P0：本次 | 合同/报告/近邻核对，纳入远端v1.1更正；选H-WR，写逐臂、判据、成本与自查 | 文档发布即结束；不运行模型 |
| A：一轮原生来源检验 | 收敛NWR主比较：固定N4146及旧48条，L11接收、原生L00供体；D/E/五种子输出范数对照及旧SRU桥接，12臂 | Proposal §4全部实质门槛过才进入B；弱、异号、仅停止或不可判都结束局部工作 |
| B：横向开发外确认 | 冻结操作；24新基础情境×2版本；N4146/N1210两个主要条件、R0诊断 | 两主要条件分别满足联合确认标准；区间宽不加题，不挑针替补 |
| P2：整稿与投稿判断 | 主张、机制图、原生来源、反例、范围与复现材料；对实际结果再次核查近邻 | 成功形成有界正面贡献；失败收缩为条件链及边界，不用写作缝成已证实原生全链 |

A/B需要独立的实施/数值验收和之后明确的运行授权。远端[NWR草案](https://github.com/yuxiexiong/acupuncture/blob/f3a35280e74c91f31139f9b29b3685af042379e9/experiments/cache-native-write-readout-v1-2026-11-05/DESIGN.zh-CN.md)未运行；未来须按本版收敛修订合同，不能两份矩阵都跑。旧数据与任何草案都不是执行授权。

##### 4. 成败会怎样改变文章

- **A/B全过：** 原生受针写入来源的状态，能通过具体D用途造成实质选择错误；已有写入修复与读取撤回因此得到一个有原生来源依据、可在新情境确认的连接。保留接收者是人工写入端点的限制。
- **只在A过、B未确认：** 单条件局部案例；未达到第二版要求的跨条件确认，不换更强针补票。
- **D只导致停止或未交付：** 有延迟停止作用；不足以支撑“选择错误”这一核心增量。
- **E或同尺度随机相当：** 用途/来源选择性不足；不能只报D阳性，也不追加更复杂的对照直到假设获救。
- **D弱、异号、只有M变或不可判：** 原生来源连接未成立；原LVK/SRU证据照常保留，停止H-WR强路线。
- **工程桥接失败：** 不作为科学阴性；最多一次记录修复，仍失败就暂停。

即使全过，也不声称唯一自然中介、原生L00实际t2路径已复现、入口形成全过程已定位、递推/KV独占不同内容或已有无干净供体修复方法。

##### 5. 不自动继续的项目

- **WPC-01**：旧384输出审计保留；统一协议新测量未做。只有改押任务/窗口分叉时才重新审议，当前不强制先跑。
- **新的t1整组历史读取卡、KV读头、层子组、全程钩子、继续k/v语义细拆**：都不排队。沿已有链补原生来源，不另起一个窄机制。
- **跨任务/模型、部署修复**：目前没有这些主张；若之后写进摘要则变成必要证据。不是永远不用做，也不隐藏在本最小包预算中。
- **旧跨层/任务失败**：保留正文边界；不将其当开发外确认，也不因与H-WR不一致而删除。

##### 6. 数量、成本与硬停止

A 576条正式自然输出，B 1728条，各预留64条来源/工程轨迹，总≤2432条、32-token上限。形成/预填/重建全部计入拟设备上限A 1.5 GPUh/B 3 GPUh；每阶段存储8GiB。是止损上限，不是已测耗时或当前授权。预检超限即停，不能删关键对照。

A按旧6场景做开发决策；B按24新基础情境聚类、六结构/校准族等权，先冻结映射/数据/解析/全部标准再看输出。B有限样本可能不够精确，结果宽就是未确认。

**A结束后只允许进入已定义的横向B或回到整稿；B结束后必回整稿，不返回局部续卡。** 不拆卡改名重置一轮上限，A失败的预算不转去另一条窄机制。若未来改押核心，须重新作整篇论文决策。

---

### 原件 2：机制拓宽方向评估：既有读数审计

原路径：`experiments/cache-mechanism-broadening-audit-v1-2026-11-04/README.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-mechanism-broadening-audit-v1-2026-11-04/README.zh-CN.md) · [单独阅读副本](../library/ad41d9c1c4d50f37.md)；SHA-256：`ad41d9c1c4d50f370ae87deba6fb14a7edd9fa424cf0cbfad2c814ec669e9d20`。

---

#### 机制拓宽方向评估：既有读数审计

本目录只有旧文件的 CPU 核对，没有新模型实验结果。当前研究推进见[机制拓宽 Roadmap](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/docs/cache-mechanism-broadening-roadmap-2026-11-04.zh-CN.md)，未形成新的完整实验计划。用户已明确以拓宽为中心，本轮没有把同一 L0 面板的两个读数细化草案作为下一步方案交付。

- [audit_existing.py](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-mechanism-broadening-audit-v1-2026-11-04/audit_existing.py)：标准库读取历史收据、SHA、形成身份、token 与输出；不导入模型、不连接服务器。
- [existing-readouts-audit.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-mechanism-broadening-audit-v1-2026-11-04/existing-readouts-audit.json)：240 份原始 JSON 校验、432 行 L0 条件读数库存、144 行可复用条件 M、288 行缺失 M、逐输入 CSK→CVSK 类型对照及来源 SHA。

九格读数库存和其重建计数来自本轮较早的局部诊断备选，保留为可复用资产；它们不是拓宽实验的矩阵、预算或待执行队列。审计也复算四轮两根针的旧结果。正式新实验范围尚未冻结。

在仓库根目录复核：

```bash
python3 experiments/cache-mechanism-broadening-audit-v1-2026-11-04/audit_existing.py
```

脚本只重写本目录派生 JSON；不修改任何旧记录。核对的是记录与历史回执的一致性，没有重新计算模型输出，也未远程复核 `.pt` 文件本体。自然 t2 的 hash 不等于可以从中恢复 logits 或缓存。

准备过程保留说明：首次脚本把 NQK 的 `_nsr_CJ_sha` 来源字段当成条件而触发 TypeError，显式排除该元数据后核对通过；未影响任何原始文件。新实验 runner 尚未实现，无 GPU 授权或消耗。

---


## 时间、运行与停止收据索引

下面是所收集JSON的原有时间字段与状态，不把预计结束时间当实际完成时间。未列时间的文件仍有原件链接。完整JSON全部保存在原文归档，不能以此索引中的标量代替完整嵌套内容。

| 原件 | 原记录状态/阶段 | 原时间字段（原时区） |
|---|---|---|
| [existing-readouts-audit.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-mechanism-broadening-audit-v1-2026-11-04/existing-readouts-audit.json) | {"status": "passed", "scope": "CPU verification and saved-readout inventory; no model execution"} | {} |

## 全部原始资产入口

本目录在固定提交下共有3个跟踪文件，包含代码、原回答、失败、收据和压缩证据；文件数不是样本数。[逐文件完整账本](../assets/120-cache-mechanism-broadening-audit-v1-2026-11-04.tsv) · [原目录](https://github.com/yuxiexiong/acupuncture/tree/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-mechanism-broadening-audit-v1-2026-11-04)。未复制模型权重、环境或凭据。
