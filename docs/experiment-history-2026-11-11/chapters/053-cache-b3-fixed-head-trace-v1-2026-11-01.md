# 053．B3：固定头与剩余头的抵消

[返回总时间线](../README.zh-CN.md)

**时间定位**：已提取运行收据的最早时间锚点（可含预检） 2026-11-01T21:52:42.181328+08:00；不能当作全部子运行起止。

**当时的目的与设计**

补完整2×2角点、记录传播，并用随机头切分作参照，检查剩余头净效应小的来源。

**实际过程、结果与后来更正**

剩余头自身正效应约0.42–1.68，交互约−1.71至−0.92，存在抵消；随机切分也可出现相似模式。全部传播读数及随机参照保留。

**来源身份**：`cache-b3-fixed-head-trace-v1-2026-11-01`；本章主体来源提交 `7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8`。下方原文中的状态是各文件写作时的状态，不能把早期“尚未运行”覆盖后期正式收据，也不能将后期结果倒填进早期设计。


## 原设计、执行过程、结果与更正全文

以下按“设计与题目 → 工程/执行记录 → 结果/更正 → 其他历史说明”组织；同类内没有可靠时间时保留路径顺序，不冒充严格先后。正文未删段；仅为本章节重排标题层级、把相对链接指向固定提交。原始字节另外完整保存。

### 原件 1：B3：固定45头怎样改变后续计算——计划 v2

原路径：`docs/cache-b3-fixed-head-computation-next-stage-plan-v2-2026-11-01.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/docs/cache-b3-fixed-head-computation-next-stage-plan-v2-2026-11-01.zh-CN.md) · [单独阅读副本](../library/12551d1c54d1b556.md)；SHA-256：`12551d1c54d1b55658ee30ca8f5f7c4661580282361756f6d7d3f21fcdf388fa`。

---

#### B3：固定45头怎样改变后续计算——计划 v2

- 日期：2026-11-01；v2，取代 [v1](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/docs/cache-b3-fixed-head-computation-next-stage-plan-v1-2026-11-01.zh-CN.md) 中被下列修订覆盖的部分；未提及处沿用 v1（课题定位 §1–3、B3-P 设计边界 §6、反方复查 §8）。
- 来源：v1 + 对 v1 的三处建议（补第四角点、N4146 一并重录、交互分解表）+ 对这些建议的评审（收紧判读、重算预算）。同一助手实现，非独立评审。
- 授权：用户 2026-11-01「如果你没什么大修意见就修好后直接写合同，代码，跑测试然后实验」。

##### 1. 相对 v1 的修订

| # | 修订 | 理由 |
|---|---|---|
| 1 | 每输入×方向新增 **N:CREST**（固定45头 V 历史 = C，其余403头 = T） | 补齐 2×2，把 D 拆成 R（其余头单独效应）与 I（输出交互）：`D = R + I` 恒等 |
| 2 | **N4146 一并重录** | D 较小的参照方向；任何 D 的解释须兼容其实测 D 的大小与范围（不是硬写成 0）。C1-P 锚点只存 bridge Recorder 字段，缺 G 层 out_proj/门控归一化、残差中段、MLP 分支 |
| 3 | 交互分解表（尺度 p/r、逐层首次可检测位置） | 只帮助提出干预预测，不替代干预检验 |
| 4 | **I 的零带用随机切分标定**：复用 C2 的 FIX 层配平随机名单 U1、U2，新增其补集格 U1c、U2c，得 `I_U = z(CT) − z(U) − z(Uc) + z(CC)` | 规则 6.3：“I≈0”不能拍数；问的是“FIX/其余这种切分的非加和是否超过一般 45/403 切分” |
| 5 | 进程内校准沿用 C2（v1 写 0 次校准） | 保持与 C2 完全相同的执行路径以保证逐位重放；7 次校准计入成本 |
| 6 | 不存形成后缓存快照 | 形成在 C1-P→C2 已逐位复现，本轮再验一次；快照重放是未验证的新路径（服务器剩 32 GB）。见 DECISIONS D2 |

本轮因此包含**新的因果比较**（CREST、随机补集格），不能整体叫“记录性补跑”：旧格负责重放验收，新格负责新增认识，分开报告。

##### 2. 格与预算

每输入：C_native；每方向（N4146、N1210、R0、R1）：

| 类 | 格 | 用途 |
|---|---|---|
| 重放（logits 须逐位等于 C2） | T_native、N:TT、N:CC、N:CFIX、N:CT、N:CUF1、N:CUF2 | 工程验收 + 2×2 的三个角 + 零带的一半 |
| 新增 | N:CREST、N:CUF1c、N:CUF2c | 第四角 + 零带补集 |

| 阶段 | 形成序列 | 单步评分 | 校准 | 公共前缀 |
|---|---:|---:|---:|---:|
| 预检 P01-f0/f1 | 10 | 82 + 4（记录器关闭对照，P01-f0/R0 四个 2×2 格） | 1 | 2 |
| 正式 12 输入 | 60 | 492 | 6 | 12 |
| 合计上限 | **70** | **578** | **7** | **14** |

形成序列按冻结 token 清单展开为 **1820 次逐 token 前向**（readiness 回执）。底层前向总数 = 14 + 1820 + 578（+7 次校准调用）。上一轮我给的“68/约341”漏算预检增量，作废。GPU 累计 ≤0.5 小时（各 worker 占用时间求和），存储 ≤16 GiB；耗时、峰值内存、字节数在预检实测。

##### 3. B3-A 固定工作表（判据见合同 §4）

1. **组成**：每方向 12 输入均值，`share_R = R̄/D̄`、`share_I = Ī/D̄`（二者和为 1）。|D̄| < 0.5 → D 太小不分解；share_R ≥ 0.75 → 自身反向为主；share_I ≥ 0.75 → 非加和为主；其余 → 两者共同；另标“相反符号”（较小份额 < −0.25）。“I 在终点近似可加”不证明内部计算独立；“非加和为主”不命名为饱和机制。
2. **FIX 特异性**：I_FIX 落在该方向 24 个随机切分 I_U 的 [min,max] 之外、同侧 ≥9/12 → “超出随机切分零带”。
3. **尺度**：I_z 中由 r 变化承载的部分 ≥ 一半 → “最终归一化尺度参与了该终点的非加和”（不证明交互起源于最终 RMSNorm）。X、D 的对称分子/分母分解作描述。
4. **逐层**：停止读出方向上各层残差投影的交互，第一个同侧 ≥9/12 超出随机切分零带的层 → “所选读数首次可检测位置”（不是交互起源层）。mixer/MLP 分支投影与 FIX/其余头 core 变化范数作描述表。

预注册预测（推测档，冻结前写入）：P1 三个减弱方向中 ≥2 个为“非加和为主”；P2 ≥2 个“超出随机切分零带”。依据：C2 中随机 45 头子集效应小，推测其余403头单独效应也小，故减弱主要来自交互——这是编的，没有机制论证。

##### 4. 出口

沿用 v1 §5 三个出口。无论走哪个出口，组成分类本身是一条新增结论：其余部分让效应减弱，主要是自身反向作用、依赖固定45头存在的非加和作用，还是两者共同——它决定 B3-P 问什么（前者看其余头自己的写入路径，后者看共享下游）。

---

### 原件 2：B3（固定45头记录重放 + 2×2 补角 + 随机切分零带）实验合同 r01

原路径：`experiments/cache-b3-fixed-head-trace-v1-2026-11-01/CONTRACT.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-b3-fixed-head-trace-v1-2026-11-01/CONTRACT.zh-CN.md) · [单独阅读副本](../library/d5f5723be9554882.md)；SHA-256：`d5f5723be9554882ecb1ba6d76259e1bb8f28ebd06b33b528cb9e7f7173b25c7`。

---

#### B3（固定45头记录重放 + 2×2 补角 + 随机切分零带）实验合同 r01

日期：2026-11-01。设计：[计划 v2](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/docs/cache-b3-fixed-head-computation-next-stage-plan-v2-2026-11-01.zh-CN.md)（取代 v1 相应部分）。基准：C2 代码 `b1d0200`、结果 `fa3e7e2`、正式运行 `runs/formal-r01`。授权：用户 2026-11-01「如果你没什么大修意见就修好后直接写合同，代码，跑测试然后实验」。偏离记入 [DECISIONS](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-b3-fixed-head-trace-v1-2026-11-01/DECISIONS.zh-CN.md)。

##### 1. 操作

模型、revision、BF16、内核路线、token、晚段窗口、L0 剂量 −1、四个方向（N4146、N1210、R0、R1）、固定45头名单、FIX 随机名单全部沿用 C2；worker/GPU 分配与 C2 相同（按情景轮转，readiness 已核）。12 条 P 系列输入，f0/f1 配对，不称 12 个独立样本。

每输入：进程内 f0 校准（须等于 C1-P 与 C2 记录）；形成 C 一次，评分 C_native；每方向形成 T 一次，评分 T_native，然后在 N 背景（C 浅层 + T 深层，decoder-13 入口 = 该方向 x_T，Q 历史 = C）按头替换卷积 V 槽：

- 重放格：N:TT、N:CC、N:CFIX、N:CT、N:CUF1、N:CUF2（全词表 logits 哈希须等于 C2）。
- 新格：N:CREST（FIX 头 C、其余 T）、N:CUF1c、N:CUF2c（U1、U2 的补集为 T）。

每次评分从独立深拷贝缓存开始。记录器只读：G 层 q/k/v/g/beta/core/old/new/z、门控归一化输出、out_proj；第13–31层 decoder 输入/输出、mixer 分支输出、MLP 分支输出；全注意力 q/k/v/attn_out；最终 h 与 normed；全词表 logits；每输入停止/答案读出向量 `(E_t − Ē)∘(1+w)`（FP64）。不存缓存快照（D2）。

##### 2. 预算（上限，失败尝试计入）

| 阶段 | 形成序列 | 单步评分 | 校准 | 公共前缀 |
|---|---:|---:|---:|---:|
| 预检（P01-f0/f1，1 worker） | 10 | 86（含记录器关闭 4） | 1 | 2 |
| 正式（12 输入，2 worker） | 60 | 492 | 6 | 12 |
| 合计 | 70 | 578 | 7 | 14 |

形成序列展开为 1820 次逐 token 前向。GPU 累计 ≤0.5 小时；存储 ≤16 GiB（每 worker ≤8 GiB）；0 生成、0 模板。预检若因**工程**原因失败，可在记账修复、重新冻结后再跑一次预检（总共 ≤2 次预检尝试，各计入实际成本）；正式运行不重试。

##### 3. 闸门（任一不过 → 停止，记合同执行失败，记录不进入分析）

1. 校准逐值等于 C1-P 与 C2；每方向 L0 名义写入范数与 |dose|·scale 相对误差 ≤1%；GPU 分配等于 C2。
2. C_native、每方向全部重放格 logits 哈希等于 C2；N:TT = T_native。
3. 第13层逐头布局（子集头 = N:CT，其余 = N:CC，逐位）；N 格入口 = x_T；每格 14 个 G 内核各 1 次、chunk 0 次；入口 hook 每 N 格 1 次。
4. 每个记录格第13–31层：`(in + mixer) + mlp == out` BF16 逐位；G 层 mixer = out_proj；末层输出 = final h。
5. 预检 P01-f0/R0：四个 2×2 格无记录器重评分，logits 逐位等于有记录器。
6. 预算、存储不超限。

##### 4. 分析判据（B3-A，`b3_core.RULE`，0 模型调用，CPU ≤4 核小时，单次完整运行）

读数：去均值停止 logit（主），答案词同法（次要，只描述）。每输入×方向：`X = z(CFIX)−z(CC)`，`F = z(CT)−z(CC)`，`D = F−X`，`R = z(CREST)−z(CC)`，`I = z(CT)−z(CFIX)−z(CREST)+z(CC)`，`D = R+I`；`I_Uk = z(CT)−z(CUFk)−z(CUFkc)+z(CC)`。

- **组成**（停止侧，每方向 12 输入均值）：|D̄| < 0.5 → `D_small`（只描述）；`share_R = R̄/D̄ ≥ 0.75` → `self`；`share_I ≥ 0.75` → `interaction`；否则 `both`。较小份额 < −0.25 另标 `opposing`。逐输入分类作描述。
- **FIX 特异性**：零带 = 该方向 24 个 I_U 的 [min, max]；I 同侧超出 ≥9/12 → `specific`，否则 `within`。（可交换假设下单个输入单侧超出概率 ≤1/25；输入间尺度不同使合并零带偏宽，判据偏保守。）
- **尺度**：`I_z = Σc·p/r`，`I_num = Σc·p / r̄`，`I_scale = I_z − I_num`；|mean I_scale| ≥ 0.5|mean I_z| → `scale_involved`，否则 `numerator_dominant`。X、D 的对称分子/分母项作描述。数值检查：由 final h 的 FP64 重算 z 与 logits 读数之差 ≤0.15 logit；不过则修正数值实现并记日志，不换指标。
- **逐层**：`p_l = u·out_l`（l = 13…31），I_l 与随机切分零带同法；第一个 `specific` 层 = “所选读数首次可检测位置”。mixer/MLP 分支投影的 X、D、R、I 均值，FIX/其余头 core 变化范数（X、D、R），只作描述。

措辞限制：`I` 近似可加不证明内部独立；`interaction` 不命名为饱和机制；`scale_involved` 不说交互起源于最终 RMSNorm；首次可检测层不叫起源层；N4146 的解释须兼容其实测 D，不写成精确零。

##### 5. 预注册预测（推测档，冻结前写入，见到 B3 数据前不改）

- P1：N1210、R0、R1 中 ≥2 个方向组成为 `interaction`。
- P2：三者中 ≥2 个方向 `specific`。

##### 6. 出口与停止

分析完成后按计划 v1 §5 三个出口之一收束：(a) 有可操作、可失败的计算预测 → 另写因果合同，不自动上卡；(b) 无计算预测但缺下游响应信息 → 进入 B3-P 设计；(c) 连有界因果比较都无法保证认识增量 → 暂停 B 细拆。结果不利不改阈值、不换格、不加方向；工程失败立即停止并记账。

##### 7. 交付

`runs/{preflight,formal}-r01/`（清单、哈希、记录入 Git；张量不入 Git）、`analysis/b3-readouts-r01.json`、`REPORT.zh-CN.md`。补录通过只记“数据可用”；重放格不再统计 C2 阳性。

---

### 原件 3：B3（固定45头记录重放 + 2×2 补角 + 随机切分零带）结果报告

原路径：`experiments/cache-b3-fixed-head-trace-v1-2026-11-01/REPORT.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-b3-fixed-head-trace-v1-2026-11-01/REPORT.zh-CN.md) · [单独阅读副本](../library/1956dd883b624675.md)；SHA-256：`1956dd883b624675ee42493b2d72d841b2caeb00a4dff4e93d8631e93549b0b8`。

---

#### B3（固定45头记录重放 + 2×2 补角 + 随机切分零带）结果报告

日期：2026-11-01。[计划 v2](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/docs/cache-b3-fixed-head-computation-next-stage-plan-v2-2026-11-01.zh-CN.md)；[合同 r01](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-b3-fixed-head-trace-v1-2026-11-01/CONTRACT.zh-CN.md)；[决策 D1–D6](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-b3-fixed-head-trace-v1-2026-11-01/DECISIONS.zh-CN.md)。代码 `239843c`，freeze-r01 `ab860a6a…a968`。同一助手实现、运行与撰写，不是独立复核。读数：`analysis/b3-readouts-r01.json`。

##### 1. 结论（不利的先说）

1. **P2 不成立（科学失败，信息量为正）**：四个方向的 FIX/其余交互 I 都落在随机 45/403 切分交互的合并零带内（同侧超出 0–2/12，门槛 9/12）。随机切分本身也有明显的负交互（每方向 24 个值的均值 −0.65 到 −0.99 logit）。在这个判据下，**“两组 V 历史合起来不如分开相加”是拆分 V 历史的一般性质，不能说是固定45头特有。**
2. **“其余头自身反向作用”被否定**：四个方向的 R（只给其余403头 T 历史）都是**正的**，和 FIX 同向推高停止（N4146 +1.68，N1210 +0.42，R0 +0.45，R1 +0.85）。减弱完全来自负交互 I（−1.71、−0.92、−0.95、−1.57）。
3. **N4146 的 D≈0 不是“没有其余头效应”**：R=+1.68 与 I=−1.71 几乎相互抵消（D=−0.03）。v1 把 N4146 当作“减弱小”的参照没错，但它的小 D 是两项抵消的结果。
4. **P1 按规则成立，理由有一半错**：组成分类为 N1210 `interaction`（share_I 1.82）、R1 `interaction`（2.17）、R0 `D_small`（|D̄|=0.496，比门槛 0.5 只差 0.004；不重分类）。登记理由是“其余头单独效应小”，实际 R 不小，只是方向与 D 相反（`opposing`）。
5. **终点非加和主要由最终 RMS 尺度承载**（`scale_involved`，四方向 I 中 r 承载份额 0.84–1.5）。从 CFIX 到 CT，分子项仍为正（+0.22 到 +1.38），分母项为负（−0.74 到 −1.42）：其余头的 T 历史确实加了停止方向分子，但最终 h 的 RMS 增大把它稀释掉了。按合同措辞，这只说明**最终归一化尺度参与了这个终点的非加和**，不说明交互起源于最终 RMSNorm。

##### 2. 2×2 读数（停止侧，12 输入均值，logit）

| 方向 | X | F | D | R | I | 组成 | I vs 随机切分零带 | 尺度 |
|---|---:|---:|---:|---:|---:|---|---|---|
| N4146 | 3.36 | 3.33 | −0.03 | +1.68 | −1.71 | D_small | within（带 −2.05…−0.25） | scale_involved（0.91） |
| N1210 | 3.18 | 2.68 | −0.51 | +0.42 | −0.92 | interaction（opposing） | within | scale_involved（1.50） |
| R0 | 2.39 | 1.89 | −0.50 | +0.45 | −0.95 | D_small（边界） | within | scale_involved（0.87） |
| R1 | 3.40 | 2.68 | −0.72 | +0.85 | −1.57 | interaction（opposing） | within | scale_involved（0.84） |

重放格 X、F 与 C2 逐位一致（logits 哈希闸门），所以这里的 X、F 就是 C2 的数，不算新阳性。

**合同外描述（不改变判定）**：逐输入看，FIX 的 I 比本输入两个随机切分都更负的输入数，分别为 N4146 11/12、N1210 3/12、R0 7/12、R1 7/12；可交换假设下的期望是 4/12。只有 N4146 明显偏离，不足以支持“FIX 特异”。要检验，须另行预注册更多随机切分。

##### 3. 逐层与分支（描述，不是起源定位）

- 停止读出方向上，残差投影的交互在第 20–21 层起超出随机切分零带，而且是**正的**（N4146 首次可检测层为 24，N1210/R0 为 21，R1 为 20）。中段（21–29 层）分子是超加和的；到第 30–31 层，交互回落或变负。
- 分支均值：第 31 层（全注意力）mixer 的交互项四方向都在 −0.66 到 −0.98，第 28 层 G mixer 在 −0.32 到 −0.54。中段的正交互主要出现在第 21、24、27 层 mixer，以及第 25–29 层 MLP。
- 这些是**所选读数**（停止方向分子）上首次可检测的位置。更早的变化可能没有投影到这个方向，或者相互抵消；而且终点的非加和大部分由 r 承载，不由这里的分子承载。

##### 4. 答案侧（次要，描述）

四方向组成都是 `self`：其余头单独就强烈压低答案词（R = −4.5 到 −7.4），交互为正（+0.8 到 +2.3），都在零带内。这与 C2 的“答案侧 FIX 未兑现”一致：答案侧的针效应大部分由其余头自己携带。

##### 5. 执行

| 阶段 | 形成 | 评分 | 校准 | 逐 token 前向 | 墙钟 | 存储 |
|---|---:|---:|---:|---:|---:|---:|
| 预检 r01 | 10 | 86 | 1 | 260 | 46 s | 0.23 GB |
| 正式 r01（2 worker） | 60 | 492 | 6 | 1560 | 96 / 98 s | 1.39 GB |
| 合计 / 上限 | 70 / 70 | 578 / 578 | 7 / 7 | 1820 | ≈0.07 GPU·h / 0.5 | 1.6 / 16 GiB |

全部闸门都过了：校准逐值等于 C1-P 与 C2，GPU 分配等于 C2，所有重放格 logits 逐位等于 C2，N:TT = T_native；第13层逐头布局、入口、内核计数正常；第13–31层 `(in+mixer)+mlp == out` BF16 逐位闭合，G 层 mixer = out_proj；预检中记录器开/关逐位一致。分析的数值检查：由 final h 重算 z 与 logits 读数的最大差为 0.063（门槛 0.15）。预检一次通过，没有用到 D6 的重试。

##### 6. 出口（计划 v1 §5）

选**出口 (b)：没有可直接上卡的计算预测，缺的是“干预某分支后下游怎样响应”。** 理由：

- 现有最具体的说法是“终点减弱是最终 RMS 稀释”。这是代数分解，不是因果结论。
- **（更正，见 §8）** 初稿此处写“它在随机切分上同样存在，不是 FIX 特有”。这句写的时候没有检查过，事后核对是错的：随机切分的负交互主要由分子承载，RMS 承载份额明显小于 FIX 切分。
- 因此 B3-P 不应写成“一般的 V 历史拆分次加和”（初稿的提法，已撤回），而应先回答 §8 的两个问题：FIX/其余切分的 RMS 超加和是否超出更多随机切分；以及这部分 RMS 增长来自哪些分支。随机切分与 FIX 切分必须接受同一套操作。

不自动上卡；B3-P 的设计需另行确认。

##### 7. 可以说 / 不可以说

| 可以说 | 不可以说 |
|---|---|
| 其余403头单独使用有针 V 历史，同样推高停止（四方向 R>0） | 其余头是抑制头 / 有独立反向作用 |
| FIX 子集效应超过全 V 的部分完全来自负交互 | 这种交互是 FIX 特有的抵消电路 |
| 本轮没有建立 FIX 切分负交互**大小**特殊的证据；所测两个随机切分也有负交互 | 所有切分都一样（未超出零带不是等效性证明）；已证明是饱和机制；随机切分的交互承载方式相同（合同外核对显示不同，§8） |
| 终点非加和大部分由最终 h 的 RMS 变化承载 | 交互起源于最终 RMSNorm |
| N4146 的 D≈0 是 R 与 I 相互抵消 | N4146 上其余头无效 |

##### 8. 合同外核对（报告发布后，2026-11-01；不改变任何冻结判定）

起因：评审问到“RMS 增大”这个读法。分母项为负只有在停止分子 p>0 时才等于 RMS 增大，初稿没有单独核对 p 的符号；另外，初稿 §6 说 RMS 稀释在随机切分上也存在，这句也没有核对过。数据取自正式记录里的 `final_norm.r` 和 cz_s46，12 输入均值：

1. **p>0，RMS 增大成立。** 所有 N 格的 cz_s46 在 13.7–17.3 之间；r 从 CFIX 的 1.33–1.40 升到 CT 的 1.43–1.48。
2. **两组单独都基本不增大 r，合起来才增大**：r 的交互（CT−CFIX−CREST+CC）为 +0.13、+0.12、+0.07、+0.11（N4146、N1210、R0、R1）。
3. **随机切分不是这样**：U1、U2 的 r 交互只有 +0.003 到 +0.039；它们的负交互 I 中由 r 承载的份额为 0.13–0.54，FIX 切分为 0.83–1.54。4 个方向 × 2 个随机切分，8/8 都是 FIX 切分的 r 交互更大。

读法：负交互的**大小**没有超出随机切分（合同判定 P2 不成立，不变）；但交互的**承载方式**（经由最终 RMS 的超加和增长）在所测切分中只在 FIX/其余切分上明显出现。这是事后检查、只有两个随机切分、用的是均值，属于探索线索，不是 FIX 特异性的证据；检验它需要预注册更多随机切分。初稿 §6 “RMS 稀释在随机切分上同样存在”的说法撤回。

---

### 原件 4：B3 决策日志

原路径：`experiments/cache-b3-fixed-head-trace-v1-2026-11-01/DECISIONS.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-b3-fixed-head-trace-v1-2026-11-01/DECISIONS.zh-CN.md) · [单独阅读副本](../library/d662018dbfaa08ab.md)；SHA-256：`d662018dbfaa08abc3d143a70ceb840d65bcbf482f82e12db75544efcdc4fb79`。

---

#### B3 决策日志

- **D1 校准沿用 C2 进程内路径（冻结前）**：计划 v1 写“不调用 engine.calibrate”。为让执行路径与 C2 完全一致、降低逐位重放失败风险，沿用 C2：每情景 f0 校准一次，要求逐值等于 C1-P 与 C2 记录。成本 +7 次校准，已列入合同预算。
- **D2 不存缓存快照（冻结前）**：计划 v1 承诺保存 C/T 形成后快照以便将来精确重放。改为不存：形成在 C1-P→C2 已逐位复现，本轮再以全部重放格验一次，将来 B3-P 可按同一路径重新形成（每 worker 约 2 分钟量级）；从磁盘恢复快照是未经验证的新重放路径，且服务器 /workspace 仅剩约 32 GB。影响：B3-P 需重新形成，成本计入其合同；不影响本轮任何结论。
- **D3 新增随机切分零带格（冻结前）**：评审要求“I≈0”的容差预先写明。按规则 6.3 用对照标定：复用 C2 冻结的 FIX 随机名单 U1、U2（N:CUF1/2 为重放格），新增补集格 N:CUF1c/2c，使每输入×方向得两个 I_U。
- **D4 N4146 一并重录（冻结前）**：C1-P 锚点张量只含 bridge Recorder 字段（G 层 q/k/v/g/beta/core/old/new/z，第13层后 decoder 输入/输出，全注意力 q/k/v/attn_out，final h/normed），缺 G 层 out_proj/门控归一化、MLP 分支；且 N4146 是 D 较小的参照方向。
- **D5 预算更正（冻结前）**：此前给出的“68 形成/约 341 评分”漏算预检增量，作废；本合同 70/578（含随机切分格与记录器关闭对照）。
- **D6 预检工程失败可重试一次（冻结前）**：闭合闸门（`(in+mixer)+mlp == out` 逐位）与新 Trace hook 未在真实模型上跑过；允许预检在记账修复后重跑一次，正式运行不重试。

---


## 时间、运行与停止收据索引

下面是所收集JSON的原有时间字段与状态，不把预计结束时间当实际完成时间。未列时间的文件仍有原件链接。完整JSON全部保存在原文归档，不能以此索引中的标量代替完整嵌套内容。

| 原件 | 原记录状态/阶段 | 原时间字段（原时区） |
|---|---|---|
| [readiness/cpu-receipt-r01.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-b3-fixed-head-trace-v1-2026-11-01/readiness/cpu-receipt-r01.json) | {"status": "passed"} | {} |
| [runs/formal-r01/controller.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-b3-fixed-head-trace-v1-2026-11-01/runs/formal-r01/controller.json) | {"status": "completed", "stage": "formal"} | {"started_at": "2026-11-01T13:54:00.894903+00:00", "finished_at": "2026-11-01T13:55:41.190699+00:00"} |
| [runs/formal-r01/verification.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-b3-fixed-head-trace-v1-2026-11-01/runs/formal-r01/verification.json) | {"status": "passed", "stage": "formal"} | {"verified_at": "2026-11-01T13:55:41.190488+00:00"} |
| [runs/formal-r01/worker-0/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-b3-fixed-head-trace-v1-2026-11-01/runs/formal-r01/worker-0/receipt.json) | {"status": "completed", "stage": "formal"} | {"started_at": "2026-11-01T13:54:00.986811+00:00", "last_record_at": "2026-11-01T13:55:35.304053+00:00", "finished_at": "2026-11-01T13:55:37.341844+00:00"} |
| [runs/formal-r01/worker-1/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-b3-fixed-head-trace-v1-2026-11-01/runs/formal-r01/worker-1/receipt.json) | {"status": "completed", "stage": "formal"} | {"started_at": "2026-11-01T13:54:00.986936+00:00", "last_record_at": "2026-11-01T13:55:36.485226+00:00", "finished_at": "2026-11-01T13:55:38.578356+00:00"} |
| [runs/preflight-r01/controller.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-b3-fixed-head-trace-v1-2026-11-01/runs/preflight-r01/controller.json) | {"status": "completed", "stage": "preflight"} | {"started_at": "2026-11-01T13:52:42.181328+00:00", "finished_at": "2026-11-01T13:53:30.424185+00:00"} |
| [runs/preflight-r01/verification.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-b3-fixed-head-trace-v1-2026-11-01/runs/preflight-r01/verification.json) | {"status": "passed", "stage": "preflight"} | {"verified_at": "2026-11-01T13:53:30.424006+00:00"} |
| [runs/preflight-r01/worker-0/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-b3-fixed-head-trace-v1-2026-11-01/runs/preflight-r01/worker-0/receipt.json) | {"status": "completed", "stage": "preflight"} | {"started_at": "2026-11-01T13:52:42.272473+00:00", "last_record_at": "2026-11-01T13:53:26.296827+00:00", "finished_at": "2026-11-01T13:53:28.334527+00:00"} |

## 全部原始资产入口

本目录在固定提交下共有67个跟踪文件，包含代码、原回答、失败、收据和压缩证据；文件数不是样本数。[逐文件完整账本](../assets/053-cache-b3-fixed-head-trace-v1-2026-11-01.tsv) · [原目录](https://github.com/yuxiexiong/acupuncture/tree/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-b3-fixed-head-trace-v1-2026-11-01)。未复制模型权重、环境或凭据。
