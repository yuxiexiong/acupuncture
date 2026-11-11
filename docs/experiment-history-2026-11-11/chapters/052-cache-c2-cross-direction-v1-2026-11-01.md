# 052．C2：固定头到其他方向

[返回总时间线](../README.zh-CN.md)

**时间定位**：已提取运行收据的最早时间锚点（可含预检） 2026-11-01T20:37:10.901884+08:00；不能当作全部子运行起止。

**当时的目的与设计**

在N4146、N1210、R0、R1四方向检验同一固定头集合。

**实际过程、结果与后来更正**

停止侧保留约98%–156%，答案侧约33%–60%；R0原生仅1/12 EOS，固定头操作可到6/12。各方向结果不合成同一种自然行为。

**来源身份**：`cache-c2-cross-direction-v1-2026-11-01`；本章主体来源提交 `7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8`。下方原文中的状态是各文件写作时的状态，不能把早期“尚未运行”覆盖后期正式收据，也不能将后期结果倒填进早期设计。


## 原设计、执行过程、结果与更正全文

以下按“设计与题目 → 工程/执行记录 → 结果/更正 → 其他历史说明”组织；同类内没有可靠时间时保留路径顺序，不冒充严格先后。正文未删段；仅为本章节重排标题层级、把相对链接指向固定提交。原始字节另外完整保存。

### 原件 1：C2 方案：固定 45 头名单能否跨干预方向工作 v1

原路径：`docs/cache-c2-fixed-list-cross-direction-plan-v1-2026-11-01.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/docs/cache-c2-fixed-list-cross-direction-plan-v1-2026-11-01.zh-CN.md) · [单独阅读副本](../library/1ce963dac0b82fff.md)；SHA-256：`1ce963dac0b82ffff3ed258b6b52d98cf9d782baf03a5b7a3bb328ac4c7ad011`。

---

#### C2 方案：固定 45 头名单能否跨干预方向工作 v1

2026-11-01。身份：正式实验方案（同一助手自查，非独立审查）；按用户 2026-11-01 确认的三处修订写成，授权“写方案、写合同代码、上卡跑”。依据：C1-P 结果 965cc9f 与更正 c48b2ce；跨通道实验（XCHAN）f38b00e 的方向定义、注入实现与写入量审计。

##### 1. 问题与定位

C1-P 显示：由旧数据得出的固定 45 头名单（FIX）在 6 个新情景上、对原针 L0/N4146/−1 保留了约全部停止侧 V 效应。本轮问：**同一份 FIX 在不同干预方向下是否仍承担 V 效应？** 即它是只适用于原针的材料，还是所测几个方向共享的材料集合。这是 C 阶段的适用边界检验；阶段 B 的计算解释仍未完成，本轮不提供机制解释。

##### 2. 三处修订（相对 C1-P 复核文档的草案）

1. **主检验 = FIX，配它自己的逐层配平随机子集。** 每输入 4 组随机 45 头，各层头数与 FIX 相同，按 SHA256(`C2-FIXU-v1|输入|j|层|头`) 定序取前若干，名单在任何评分前冻结（`data/fix-random-r01.json`）。自适应 H（按各方向自己的 N:TT 参考运行、F_V 局部路径算法选出）只作次要比较。
2. **预注册预测：** 依据 XCHAN 中原生通道与随机方向的深层 ΔV 方向相似（余弦中位数 0.68–0.75）、整块 V 替换效果相近，登记预测“FIX 在 R0、R1 上也通过主判据”。这只是有依据的预测：整体 V 相似不保证起作用的部分落在同一份 45 头上。失败与不可判条件见 §5。
3. **幅度 = 复用旧构造 + 实际写入验收。** 原生通道按 dose·scale/‖W_down 列‖ 加在 down_proj 输入通道，随机方向按单位向量 × dose·scale 加在 L0 MLP 输出；二者 L0 残差写入的名义范数都等于 |dose|·scale。沿用 XCHAN 的 `write_audit` 记录 BF16 后实际写入范数，要求与目标相对误差 ≤1%。**只匹配 L0 写入范数，不匹配深层 V 变化或输出效应**，不得按输出结果调剂量。

##### 3. 对象与操作

- 输入：C1-P 的 12 条 P 系列提示（P01–P06 × f0/f1），现已是见过的输入，但未参与 FIX 的制定。不复用旧提示的缓存。
- 方向（均为 L0、剂量 −1、晚段 b+1…n−2）：N_L00_C4146_D-1（锚点）、N_L00_C1210_D-1、R0_L00_D-1、R1_L00_D-1（XCHAN `directions-r01.json`，哈希校验）。
- 校准：每情景 f0 上下文按旧 `calibrate` 规则，f0/f1 共用；须逐值等于 C1-P 记录的校准。
- 每输入：形成 C 一次，每个方向形成 T 一次（5 次形成）。评分：C_native；每方向 T_native|d、N:TT|d、N:CC|d、N:CT|d、N:CFIX|d、N:CUF1–4|d、N:CH|d（10 格）。N 背景 = C 浅层 + T_d 深层 S/KV，decoder13 入口 = T_native|d 的 x_T；Q 一律为 C；V 按头替换，四槽复制。

##### 4. 估计量

Z = 去词表均值 logit；停止 248046 为主，答案候选 a（C_native 非停止赢家，各方向共用）为次。对每方向：F = Z(N:CT) − Z(N:CC)；X = Z(N:CFIX) − Z(N:CC)；U_j = Z(N:CUFj) − Z(N:CC)；E = X − median_j U_j。次要：H = Z(N:CH) − Z(N:CC)。情景先平均两事实原始差。

##### 5. 冻结判据（逐方向、逐侧）

令符号 s = +1（停止侧）或 −1（答案侧，针压低答案词），对 F、X、E 乘以 s 后用同一规则：

- F 足够：s·F 情景均值 ≥1，且两事实 s·F > 0；否则该情景“全 V 效应不足”。
- 保留：s·X 均值 ≥ 0.5 × s·F 均值，且两事实 s·X > 0。
- 优势：s·E 均值 ≥ 0.2，且两事实 s·E > 0。

情景三条同时满足为通过。每方向：≥5/6 通过 → **支持**；F 足够情景 <5 → **无法充分检验**；保留 ≥5/6 但优势不足 → **子集有效但无对照优势**；否则 → **名单未兑现**。主判断 = 每方向停止侧 FIX。预测“随机方向也迁移”成立当且仅当 R0 与 R1 停止侧均为支持。答案侧与 H 臂同式、只作次要报告，不救主判断。

| 结果 | 可更新的判断 |
|---|---|
| FIX 在原生通道和随机方向都支持 | 支持该材料集合在所测方向间共享；削弱原针专属解释。不得外推“任意同幅写入都汇聚到同一组头”，也不证明一般饱和。 |
| 某方向 F 足够但 FIX 未兑现 | 限制 FIX 的共享范围，支持子集作用依赖干预方向。 |
| 某方向 F 不足 | 该方向无法检验名单迁移，不据此认定原生通道特殊。 |

##### 6. 闸门（任一不过 → 停止，记工程失败）

1. 来源：输入、FIX、FIX 随机名单、XCHAN 方向文件哈希；校准逐值等于 C1-P 记录。
2. 写入：每方向 BF16 后名义写入范数与 |dose|·scale 相对误差 ≤1%。
3. 重放：每方向 N:TT logits 逐位等于 T_native|d；锚点 N4146 的 T_native、N:CC、N:CT、N:CFIX logits 逐位等于 C1-P 正式运行的对应格。
4. 布局：第13层每个子集格的每个值头 v 逐位等于同方向 N:CT（选中）或 N:CC（未选中）。
5. 命中：每格 14 个 G 层 recurrent 内核各 1 次、chunk 0 次；N 格入口钩子 1 次。
6. 自适应 H：选头重算 v、out_proj 相对误差 ≤0.02，名单写入不可改文件后才评分 N:CH。
7. 预检：R0 方向全集子集 = N:CT、空集子集 = N:CC（逐位）。

##### 7. 预算与停止

| 阶段 | 形成 | 评分 |
|---|---:|---:|
| 预检（P01-f0/f1，每条 41 格 + R0 全集/空集） | 10 | 86 |
| 正式（12 × 41） | 60 | 492 |
| 合计上限 | 70 | 578 |

0 模板、0 生成；GPU ≤1.5 小时；存储 ≤8 GiB。结果不利不改阈值、不换题、不改头数、不加方向或剂量。

##### 8. 自查要点

C01 主线不变（干预→历史→输出），本轮是 C 阶段边界检验；C02 新增“同一子集跨方向因果作用”，不能由 XCHAN 整块 V 结果推出；C04 保留“整体相似但子集不同”的反例；C08 不作效率、特异性或一般饱和结论；C10 停止/答案分侧且按效应方向写判据（修正 C1-P 的遗漏）；C11 工程失败、F 不足、名单未兑现分开；C12 每格都有用途，锚点复用 C1-P 做跨运行复现；C13 输入已见、FIX 与随机名单先冻结；C14 无论结果，下一步须另立方案，不自动扩方向。E12：随机子集与随机方向都不构成零分布；E22：P 系列已见、6 情景同模板。

---

### 原件 2：C2（固定名单跨干预方向）实验合同 r01

原路径：`experiments/cache-c2-cross-direction-v1-2026-11-01/CONTRACT.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-c2-cross-direction-v1-2026-11-01/CONTRACT.zh-CN.md) · [单独阅读副本](../library/84436a3553c85415.md)；SHA-256：`84436a3553c854159df9879355263356c8ef3e8cdfb97c1b19df3a1c94592c49`。

---

#### C2（固定名单跨干预方向）实验合同 r01

日期：2026-11-01。设计：[方案 v1](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/docs/cache-c2-fixed-list-cross-direction-plan-v1-2026-11-01.zh-CN.md)。冻结资产：C1-P 输入与固定名单、[FIX 自己的逐层配平随机名单](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-c2-cross-direction-v1-2026-11-01/data/fix-random-r01.json)、XCHAN `directions-r01.json`。授权：用户 2026-11-01“按这三处修订写方案，然后写合同代码上卡跑”。偏离记入 [DECISIONS](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-c2-cross-direction-v1-2026-11-01/DECISIONS.zh-CN.md)。

##### 1. 操作

12 条 P 系列输入；四个方向（L0、剂量 −1、晚段）：N4146（锚点）、N1210、R0、R1。每情景 f0 校准（须等于 C1-P 记录），形成 C 一次、每方向 T 一次。每方向评分 T_native、N:TT、N:CC、N:CT、N:CFIX、N:CUF1–4、N:CH（自适应 H，名单先冻结到文件）；外加 C_native。Q=C，V 按头替换，四槽复制，入口 = 本方向 x_T。

##### 2. 预算

| 阶段 | 形成 | 评分 |
|---|---:|---:|
| 预检（P01-f0/f1） | 10 | 86 |
| 正式（12 输入） | 60 | 492 |
| 上限 | 70 | 578 |

GPU ≤1.5 小时；存储 ≤8 GiB；0 模板、0 生成。

##### 3. 闸门（任一不过 → 停止，记工程失败）

校准逐值等于 C1-P；每方向 L0 名义写入范数与 |dose|·scale 相对误差 ≤1%；C_native 与锚点 T_native/N:CC/N:CT/N:CFIX logits 逐位等于 C1-P；每方向 N:TT = T_native|d；第13层逐头布局；入口 = x_T；每格 14 个 G 层内核各 1 次、chunk 0 次；自适应 H 重算 ≤0.02 且先冻结；预检 R0 全集 = N:CT、空集 = N:CC。

##### 4. 判据（方案 §5）

每方向、每侧以符号 s（停止 +1、答案 −1）作用于 F、X、E 后：F 情景均值 ≥1 且两事实 >0；X ≥0.5F 且两事实 >0；E = X − median(U_FIX) ≥0.2 且两事实 >0；≥5/6 通过 → 支持；F 足够 <5 → 无法充分检验；保留 ≥5/6 但 E 不足 → 子集有效但无对照优势；否则名单未兑现。主判断 = 每方向停止侧 FIX。预注册预测“随机方向也迁移”= R0、R1 停止侧均支持。答案侧、H 臂为次要。

##### 5. 停止

结果不利不改阈值、不换题、不改头数、不加方向或剂量；工程失败立即停止并记账。

---

### 原件 3：C2（固定 45 头名单跨干预方向）结果报告

原路径：`experiments/cache-c2-cross-direction-v1-2026-11-01/REPORT.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-c2-cross-direction-v1-2026-11-01/REPORT.zh-CN.md) · [单独阅读副本](../library/f14d410edc69c68e.md)；SHA-256：`f14d410edc69c68e0c1c8199b4058e4adb9011ee01215a3ac4f6fc39d972f731`。

---

#### C2（固定 45 头名单跨干预方向）结果报告

日期：2026-11-01。[方案 v1](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/docs/cache-c2-fixed-list-cross-direction-plan-v1-2026-11-01.zh-CN.md)；[合同 r01](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-c2-cross-direction-v1-2026-11-01/CONTRACT.zh-CN.md)；[决策 D1–D4](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-c2-cross-direction-v1-2026-11-01/DECISIONS.zh-CN.md)。代码 b1d0200，freeze-r01 `bec0ec4c…f77b`。同一助手实现、运行与撰写，不是独立复核。

##### 1. 结论（限制先说）

**限制：** 只测了 4 个方向（两个原生通道 N4146、N1210，两个随机残差方向 R0、R1），均为 L0、剂量 −1；P 系列 12 条输入已见、来自同一模板；只匹配 L0 写入范数（实测误差 ≤0.24%），未匹配深层 V 变化或输出效应；随机子集只匹配头数与层分布。结论只限于所测方向，不外推“任意同幅写入都汇聚到同一组头”，也不证明一般饱和或说明各方向机制相同。阶段 B 的计算解释仍未完成。

**主判断（每方向停止侧 FIX）：4 个方向全部支持（各 6/6）。预注册预测“FIX 在随机方向上也迁移”成立（R0、R1 均支持）。**

| 停止侧，情景范围 | 全 V 效应 F（logit） | FIX 保留倍数 X/F | E = FIX − 自身随机中位数 |
|---|---|---|---|
| N4146（锚点） | 3.06–3.78 | 0.98–1.07 | 1.63–2.93 |
| N1210 | 1.99–3.67 | 1.10–1.35 | 1.43–3.24 |
| R0 | 1.16–2.60 | 1.12–1.56 | 1.12–2.50 |
| R1 | 1.92–3.17 | 1.14–1.53 | 1.69–3.04 |

- 锚点逐位复现 C1-P（T_native、N:CC、N:CT、N:CFIX 均一致），FIX 保留率与 C1-P 相同。
- 在三个非锚点方向上，只换 FIX 的 V 效应**大于**全 V 替换（X/F > 1）：其余头的有针 V 在这些方向上部分抵消 FIX 头的作用（非加和，描述）。
- 自适应 H（各方向自己重选）同样 4/4 支持；与 FIX 每输入重合 24–33 头。

**答案侧（次要）：FIX 在 4 个方向均“名单未兑现”。** 针在各方向都强烈压低干净首词候选（|F| = 6.0–10.4 logit），FIX 只保留其 0.33–0.60，多数情景低于预定的 0.5；它相对自身随机子集的优势仍大（2.0–3.5 logit）。自适应 H（按停止侧投影选出）在答案侧 4/4 支持（保留 0.38–0.74）。即固定名单的共享主要体现在停止侧；答案侧需要 FIX 之外、各方向自适应头集中的成分。

**行为（辅助）：** N4146、N1210、R1 的原生、全 V 与 FIX 替换首步停止均 12/12；R0 最弱：原生 1/12、全 V 替换 0/12，而只换 FIX 有 6/12、只换 H 7/12。FIX 的随机子集 0–1/12。

| 结果对照方案 §5 | 本轮落点 |
|---|---|
| FIX 在原生通道和随机方向都支持 | **停止侧成立**：支持该材料集合在所测 4 个方向间共享，削弱原针专属解释 |
| 某方向 F 足够但 FIX 未兑现 | **答案侧 4/4 落此**：限制 FIX 的共享范围到停止侧 |
| 某方向 F 不足 | 未出现（各方向两侧 F 均足够） |

##### 2. 执行

| 阶段 | 形成 | 评分 | 墙钟 | 闸门 |
|---|---:|---:|---:|---|
| 预检 r01（P01-f0/f1） | 10 | 86 | 45 s | 全过 |
| 正式 r01（12 输入，2 worker） | 60 | 492 | 各 95 s | 全过 |
| 合计 / 上限 | 70 / 70 | 578 / 578 | | |

闸门：校准逐值等于 C1-P；每方向 L0 名义写入与 |dose|·scale 误差 ≤0.24%；C_native 与锚点四格逐位等于 C1-P；每方向 N:TT = T_native；第13层逐头布局；每格 14 个 G 层内核各 1 次、chunk 0 次；自适应 H 重算 ≤0.02 且先冻结；预检 R0 全集 = N:CT、空集 = N:CC。执行中一次因服务器 SSH 中断导致方案文档未同步、冻结失败（0 次模型调用），补同步后从冻结步继续，无科学数据受影响。

##### 3. 可以说 / 不可以说

| 可以说 | 不可以说 |
|---|---|
| 同一份固定 45 头，在所测 4 个 L0 方向（含两个随机方向）上都承担了停止侧 V 效应的全部或更多，远超层配平随机子集 | 任意干预都汇聚到这组头；这组头是停止开关；各方向机制相同 |
| 在 3 个方向上该子集单独效应超过全 V（其余头部分抵消） | 抵消的计算原因已知 |
| 答案侧的针效应只有不到一半落在 FIX | 答案侧没有共享材料（自适应 H 在答案侧通过） |
| 预注册预测成立 | 一般饱和已被证明或排除 |

##### 4. 下一步（不是运行授权）

停止侧：FIX 已在新输入（C1-P）和多个方向（本轮）上兑现，成为可复用、跨条件稳定的材料对象，可作为回到阶段 B 计算解释时的固定研究对象（例如为什么其余头的 V 会抵消它）。答案侧：需要单独的材料对象；自适应 H 与 FIX 的差集是自然的候选，须另立方案检验。所有推广仍受单一模板、L0 单剂量的限制。

---

### 原件 4：C2 决策日志

原路径：`experiments/cache-c2-cross-direction-v1-2026-11-01/DECISIONS.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-c2-cross-direction-v1-2026-11-01/DECISIONS.zh-CN.md) · [单独阅读副本](../library/c3d13d1e5971399d.md)；SHA-256：`c3d13d1e5971399dd668ed9e65b63dac29a500bc257c48772adc7b5ed82f2370`。

---

#### C2 决策日志

- **D1 锚点重跑而非引用**：N4146 在 C1-P 已有 N:CC/N:CT/N:CFIX，但本轮为 FIX 新增了它自己的随机对照，且需要同一运行内的跨方向比较，故锚点重新形成并评分；其 T_native、N:CC、N:CT、N:CFIX 必须与 C1-P 逐位一致，作为跨运行复现闸门。
- **D2 FIX 随机名单预先冻结**：FIX 是固定集合，其逐层配平随机子集与输入无关地由 SHA256 规则确定，故在运行前生成并冻结到 `data/fix-random-r01.json`（与 FIX 重合 3–10 头），而不在运行中生成。
- **D3 张量只存 logits**：本轮判据只用输出读数；内部驱动不作分析，为控制存储只保存全词表 logits（记录中保留每格分数摘要）。
- **D4 校准逐值复现**：f0 校准在 GPU 上确定性计算，要求与 C1-P 记录逐值相等；worker 划分与 C1-P 相同（按情景轮转），同一情景在同一 GPU 上计算。

---


## 时间、运行与停止收据索引

下面是所收集JSON的原有时间字段与状态，不把预计结束时间当实际完成时间。未列时间的文件仍有原件链接。完整JSON全部保存在原文归档，不能以此索引中的标量代替完整嵌套内容。

| 原件 | 原记录状态/阶段 | 原时间字段（原时区） |
|---|---|---|
| [readiness/cpu-receipt-r01.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-c2-cross-direction-v1-2026-11-01/readiness/cpu-receipt-r01.json) | {"status": "passed"} | {} |
| [runs/formal-r01/controller.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-c2-cross-direction-v1-2026-11-01/runs/formal-r01/controller.json) | {"status": "completed", "stage": "formal"} | {"started_at": "2026-11-01T12:38:31.580177+00:00", "finished_at": "2026-11-01T12:40:11.136794+00:00"} |
| [runs/formal-r01/verification.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-c2-cross-direction-v1-2026-11-01/runs/formal-r01/verification.json) | {"status": "passed", "stage": "formal"} | {"verified_at": "2026-11-01T12:40:11.136601+00:00"} |
| [runs/formal-r01/worker-0/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-c2-cross-direction-v1-2026-11-01/runs/formal-r01/worker-0/receipt.json) | {"status": "completed", "stage": "formal"} | {"started_at": "2026-11-01T12:38:31.671045+00:00", "last_record_at": "2026-11-01T12:40:04.462943+00:00", "finished_at": "2026-11-01T12:40:06.526761+00:00"} |
| [runs/formal-r01/worker-1/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-c2-cross-direction-v1-2026-11-01/runs/formal-r01/worker-1/receipt.json) | {"status": "completed", "stage": "formal"} | {"started_at": "2026-11-01T12:38:31.671130+00:00", "last_record_at": "2026-11-01T12:40:05.213609+00:00", "finished_at": "2026-11-01T12:40:07.306848+00:00"} |
| [runs/preflight-r01/controller.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-c2-cross-direction-v1-2026-11-01/runs/preflight-r01/controller.json) | {"status": "completed", "stage": "preflight"} | {"started_at": "2026-11-01T12:37:10.901884+00:00", "finished_at": "2026-11-01T12:37:59.022269+00:00"} |
| [runs/preflight-r01/verification.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-c2-cross-direction-v1-2026-11-01/runs/preflight-r01/verification.json) | {"status": "passed", "stage": "preflight"} | {"verified_at": "2026-11-01T12:37:59.022115+00:00"} |
| [runs/preflight-r01/worker-0/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-c2-cross-direction-v1-2026-11-01/runs/preflight-r01/worker-0/receipt.json) | {"status": "completed", "stage": "preflight"} | {"started_at": "2026-11-01T12:37:10.990916+00:00", "last_record_at": "2026-11-01T12:37:54.395381+00:00", "finished_at": "2026-11-01T12:37:56.405533+00:00"} |

## 全部原始资产入口

本目录在固定提交下共有125个跟踪文件，包含代码、原回答、失败、收据和压缩证据；文件数不是样本数。[逐文件完整账本](../assets/052-cache-c2-cross-direction-v1-2026-11-01.tsv) · [原目录](https://github.com/yuxiexiong/acupuncture/tree/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-c2-cross-direction-v1-2026-11-01)。未复制模型权重、环境或凭据。
