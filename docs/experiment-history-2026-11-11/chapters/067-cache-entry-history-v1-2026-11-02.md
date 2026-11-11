# 067．EH：当前入口与深层历史

[返回总时间线](../README.zh-CN.md)

**时间定位**：已提取运行收据的最早时间锚点（可含预检） 2026-11-02T02:06:38.255232+08:00；不能当作全部子运行起止。

**当时的目的与设计**

入口和深层历史做2×2，并补反向顺序的固定V条件，分别查看分数与首步行为。

**实际过程、结果与后来更正**

历史单独约56%–71%，入口11%–21%，交互+1.2–2.4；固定V放到干净背景仍有分数变化，但EOS0/48。背景及端点定义逐格保留。

**来源身份**：`cache-entry-history-v1-2026-11-02`；本章主体来源提交 `7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8`。下方原文中的状态是各文件写作时的状态，不能把早期“尚未运行”覆盖后期正式收据，也不能将后期结果倒填进早期设计。


## 原设计、执行过程、结果与更正全文

以下按“设计与题目 → 工程/执行记录 → 结果/更正 → 其他历史说明”组织；同类内没有可靠时间时保留路径顺序，不冒充严格先后。正文未删段；仅为本章节重排标题层级、把相对链接指向固定提交。原始字节另外完整保存。

### 原件 1：EH：e1 那约 8 logit 随入口走还是随深层历史走——计划 v1

原路径：`docs/cache-entry-history-plan-v1-2026-11-02.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/docs/cache-entry-history-plan-v1-2026-11-02.zh-CN.md) · [单独阅读副本](../library/13695615e2b0617e.md)；SHA-256：`13695615e2b0617e9f58d79dcefe59a58e23874bbf872d1cd13f313181c88da8`。

---

#### EH：e1 那约 8 logit 随入口走还是随深层历史走——计划 v1

- 2026-11-02。来源：NFC-01 结果（5b6fe98）、评审的“入口 × 深层历史 2×2”构想（其稿件在评审本机，未入仓库，内容以对话中粘贴的版本为准），以及补充的反向顺序 FIX 臂。授权：用户 2026-11-02「同意你推进吧」。

##### 1. 问题

NFC-01 显示，原生首步竞争变化（ΔD 12.6–14.2）沿 C_native→N:CC→N:CFIX→N:CT→N:TT 有 54–63% 落在 e1（C_native→N:CC）。e1 同时换了第13层入口残差 x、第13–31层递推状态 S 与注意力 KV（下称深层历史 H），卷积历史仍是 C。本轮只问：**e1 随入口走、随深层历史走，还是两者必须配合？** 以及：**固定45头的 V 历史在干净背景下单独起多大作用（反向顺序）？**

##### 2. 设计

| 格 | 入口 x | 深层历史 H | 卷积历史 | 说明 |
|---|---|---|---|---|
| 00 | 干净（自然） | C | C | = C_native（逐位） |
| 10 | x_T | C | C | 只换入口 |
| 01 | 自然（= x_C，闸门） | T | C | 只换深层历史 |
| 11 | x_T | T | C | = N:CC（与 B3 逐位） |
| FIX0 | 自然 | C | 仅 45 头 V 来自 T | 反向顺序的 e2 |

评分步不插针、下游正常响应、每次评分用独立缓存副本。四条边全部报告（历史在干净入口/干预入口下的作用、入口在干净/干预历史下的作用）以及交互 I。e1 用“深层历史整体”与入口二分，不在本轮拆 S 与 KV。

##### 3. 读数与判读

主读数 D（停止最大 − 非停止最大，原始 logit）；首步选择、平局按记录报告。s_H = (D01 − D00)/e1、s_X = (D10 − D00)/e1（|e1| ≥ 1 才形成）：≥0.75 且另一个 ≤0.25 → 该因素单独足够；两者都 ≥0.75 → 两者单独都强；两者都 ≤0.25 → 必须配合；其余为部分。反向顺序：r = e2_rev / e2_fwd（|e2_fwd| ≥ 1）：|差| ≤ 0.25|e2_fwd| → 顺序无关；r ≤ 0.5 → 需要 e1 背景；r ≥ 1.5 → 干净背景下更大；其余为部分。f0/f1 同标签、≥5/6 情景、≥3/4 方向。

预测（推测档）：P1 只换深层历史拿到 e1 的大部分（s_H ≥ 0.5 且 s_H > s_X），依据 CFM-E2（旧面板，第13–31层缓存承载 75–94% 的停止优势）；P2 FIX 的 V 历史在干净背景下作用不到 N 背景中的一半（r ≤ 0.5），依据是推测“卷积 V 历史要靠深层 T 状态才被读出”。

##### 4. 出口

只换入口就接近联合 → 下一步研究入口携带了什么、深层怎样处理它，不再把大效应归给深层存储；只换历史就接近联合 → 才有理由下一轮区分 S 与 KV；必须配合 → 研究读取条件与历史怎样配合；两者都强或方向不一致 → 保留冗余/条件差异。FIX 顺序：需要背景 → “过阈值”只能写成条件性；顺序无关 → FIX 的 V 历史作用可独立陈述。结果分散时不自动扩矩阵。

##### 5. 预算

形成：每输入 5 次（C + 4 个 T）；评分：C_native 1 次 + 每方向 T_native、10、01、11、FIX0 共 5 次 = 每输入 21 次。预检 10 形成 / 42 评分 / 1 校准；正式 60 / 252 / 6。GPU ≤0.5 小时，产物 ≤2 GiB。缓存需重新形成（B3 未存快照，形成已三次逐位复现）。

---

### 原件 2：EH（入口 × 深层历史 2×2 + 反向顺序 FIX 臂）合同 r01

原路径：`experiments/cache-entry-history-v1-2026-11-02/CONTRACT.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-entry-history-v1-2026-11-02/CONTRACT.zh-CN.md) · [单独阅读副本](../library/0c847362f2155a64.md)；SHA-256：`0c847362f2155a64dbc9d5c9979ec508f93731a86ee327159f599cb595ae3ab3`。

---

#### EH（入口 × 深层历史 2×2 + 反向顺序 FIX 臂）合同 r01

日期：2026-11-02。设计：[计划 v1](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/docs/cache-entry-history-plan-v1-2026-11-02.zh-CN.md)。基准：B3 正式运行（f2ad7d8）、NFC-01（5b6fe98）。授权：用户 2026-11-02「同意你推进吧」。输入已见，新格结果未见。

##### 1. 操作

沿用 B3 的模型、revision、BF16、内核、token、晚段窗口、L0 剂量 −1、四方向、12 条输入、worker/GPU 分配、进程内校准（须等于 B3）。每输入形成 C，评分 C_native（= 00，记录 x_C）；每方向形成 T，评分 T_native（取 x_T），然后评分：H01（N:CC 的缓存，无入口 hook）、FIX0（全 C 缓存，仅 FIX 值头的卷积 V 通道取 T，无入口 hook）、X10（全 C 缓存 + 入口 x_T）、XH11（N:CC 缓存 + 入口 x_T）。

##### 2. 预算

| 阶段 | 形成 | 评分 | 校准 |
|---|---:|---:|---:|
| 预检（P01-f0/f1，1 worker） | 10 | 42 | 1 |
| 正式（12 输入，2 worker） | 60 | 252 | 6 |

GPU ≤0.5 小时；产物 ≤2 GiB；预检工程失败可记账后重试一次，正式不重试。

##### 3. 工程闸门（任一不过即停止，记合同执行失败）

校准、GPU 分配等于 B3；L0 写入 ≤1%；C_native、T_native、XH11 的 logits 与 B3 的 C_native、T_native、N:CC 逐位相同；H01、FIX0 的第13层自然输入与 x_C 逐位相同；X10、XH11 的入口等于 x_T 且 hook 每格一次；FIX0 的卷积布局：q/k 通道为 C，FIX 值头通道为 T，其余值头为 C（逐位）；H01 的卷积为 C；每格 14 个 G 内核各一次、chunk 为 0；logits 有限。

##### 4. 判读（`eh_core.RULE`）

D = readout.D。e1 = D11 − D00；s_H = (D01 − D00)/e1，s_X = (D10 − D00)/e1（|e1| ≥ 1）。标签：s_H ≥ 0.75 且 s_X ≤ 0.25 → 历史单独足够；s_X ≥ 0.75 且 s_H ≤ 0.25 → 入口单独足够；两者 ≥0.75 → 两者单独都强；两者 ≤0.25 → 必须配合；其余为部分。另报告四条边与交互 I。反向顺序：e2_rev = D(FIX0) − D00，e2_fwd = D(N:CFIX) − D(N:CC)（B3 记录）；|差| ≤ 0.25|e2_fwd| → 顺序无关；比值 ≤0.5 → 需要背景；≥1.5 → 干净背景下更大；其余为部分（|e2_fwd| ≥ 1）。f0/f1 同标签才计情景，≥5/6 情景为方向标签，≥3/4 方向为跨方向标签，否则为条件依赖。首步选择、平局按记录报告。措辞：标签只描述这一组替换下的条件作用；“历史单独足够”不等于“入口无作用”（报告干预入口下的两条边）。

##### 5. 预注册预测（推测档，运行前写入）

P1：s_H ≥ 0.5 且 s_H > s_X（两事实），≥5/6 情景、≥3/4 方向。P2：e2_rev / e2_fwd ≤ 0.5，计数同上。

##### 6. 出口

见计划 §4；结果分散时不自动扩矩阵。

##### 7. 交付

`runs/{preflight,formal}-r01/`（记录入 Git，张量不入）、`analysis/eh-readouts-r01.json`、`REPORT.zh-CN.md`。

---

### 原件 3：EH（入口 × 深层历史 2×2 + 反向顺序 FIX 臂）结果报告

原路径：`experiments/cache-entry-history-v1-2026-11-02/REPORT.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-entry-history-v1-2026-11-02/REPORT.zh-CN.md) · [单独阅读副本](../library/21f703d40ce37577.md)；SHA-256：`21f703d40ce375775645cbcb5969db0a0977652f381dca032fe815612bda8de8`。

---

#### EH（入口 × 深层历史 2×2 + 反向顺序 FIX 臂）结果报告

日期：2026-11-02。[合同 r01](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-entry-history-v1-2026-11-02/CONTRACT.zh-CN.md)；[决策 D1–D4](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-entry-history-v1-2026-11-02/DECISIONS.zh-CN.md)；[计划 v1](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/docs/cache-entry-history-plan-v1-2026-11-02.zh-CN.md)。代码 `27d72c6`，freeze-r01 `f77f1066…284a`。输入已见，新格结果未见。同一助手实现、运行与撰写。

##### 1. 结论（不利的先说）

1. **没有哪个因素单独达到联合效果：冻结标签全部是“部分”。** 只换深层历史（干净入口）拿到 e1 的 56–71%（逐输入 0.48–0.78），只换入口拿到 11–21%（0.04–0.26）。47/48 个输入判为“部分”，只有 1 个是“历史单独足够”。跨方向标签为部分。
2. **深层历史是主要承载者，但需要和入口配合：交互为正。** I = D11 − D10 − D01 + D00 = +1.2 到 +2.4（逐输入 +0.25 到 +3.25）。在干预入口下，历史的作用更大（6.6–7.3 对 4.7–5.6）；在干预历史下，入口的作用也更大（2.3–3.7 对 0.8–1.8）。也就是说，干预后的入口和干预后的深层历史是**相互放大**的。预注册的 P1 成立（s_H ≥ 0.5 且 > s_X：6、5、6、6 个情景）。
3. **P2 不成立：固定45头的 V 历史在干净背景下作用并没有变小很多。** e2_rev（在 C_native 上只加 FIX 的 V 历史）= 3.9–5.0，NFC 中的 e2_fwd = 4.5–6.3；比值均值 0.76–0.99（逐输入 0.58–1.35），0/24 个情景 ≤0.5。各方向多数情景判为“顺序无关”（4、4、4、2），其余为部分；跨方向标签为条件依赖。
4. **FIX 单独在干净背景下不翻转首步**：FIX0 的 D 均值为 −8.1 到 −9.0，首步停止 0/48。结合第 3 条：FIX 的 V 历史带来的竞争推进**大小**基本与顺序无关（约为 N 背景中的 76–99%），但能否**翻转**取决于之前已经累积了多少。上一轮“45 头承担过阈值作用”应改写为：45 头贡献一块大小基本稳定的推进（约 4–6 logit），翻转是否发生取决于它叠加在什么状态上。
5. 所有格的首步都不停止（00、10、01、11、FIX0 全为 0/12）：e1 和 FIX 的作用都只是缩小与停止门槛的距离。

##### 2. 主要读数（D，12 输入均值）

| 方向 | D00 | D10（入口） | D01（历史） | D11（=N:CC） | e1 | 历史｜干净入口 | 历史｜干预入口 | 入口｜干净历史 | 入口｜干预历史 | I | D(FIX0) | e2_rev | e2_fwd |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| N4146 | −12.88 | −11.78 | −7.24 | −4.97 | 7.91 | 5.64 | 6.81 | 1.10 | 2.27 | 1.17 | −8.10 | 4.78 | 6.03 |
| N1210 | −12.88 | −11.07 | −8.15 | −4.46 | 8.42 | 4.73 | 6.61 | 1.81 | 3.69 | 1.88 | −7.92 | 4.96 | 5.05 |
| R0 | −12.88 | −11.76 | −7.98 | −4.45 | 8.43 | 4.90 | 7.30 | 1.13 | 3.53 | 2.40 | −9.03 | 3.85 | 4.46 |
| R1 | −12.88 | −12.05 | −7.38 | −4.95 | 7.93 | 5.50 | 7.09 | 0.83 | 2.43 | 1.59 | −8.06 | 4.82 | 6.34 |

##### 3. 执行

| 阶段 | 形成 | 评分 | 校准 | 墙钟 |
|---|---:|---:|---:|---:|
| 预检 r01 | 10 | 42 | 1 | 41 s |
| 正式 r01（2 worker） | 60 | 252 | 6 | 81 / 81 s |

全部闸门通过：校准与 GPU 分配等于 B3；C_native、T_native、XH11 与 B3 的 C_native、T_native、N:CC 逐位相同；H01、FIX0 的第13层自然输入与 x_C 逐位相同；X10、XH11 的入口等于 x_T；FIX0 的卷积布局逐通道正确；内核计数正确。约 0.05 GPU 小时。

##### 4. 出口与下一步（未设计、未授权）

- 按出口规则，这是“必须配合 / 部分”的情形：e1 的大部分随深层历史走（约六到七成），但历史与入口相互放大（正交互），单独的入口只占一到两成。所以下一步若继续拆 e1，应在深层历史内部区分递推状态 S 与注意力 KV（CFM-COMBO 的先验是 KV 小），同时保留干预入口作为条件，因为历史的作用依赖入口。
- 对 45 头：它的推进量基本不依赖 e1 背景，这让“FIX 的 V 历史贡献约 4–6 logit”可以独立陈述（条件性的只有“是否翻转”）。
- 到这一步，原生首步竞争变化（约 13–14 logit）在本面板上有了一个较完整的条件分账：深层历史（S+KV）约 5–7，入口约 1–4（依赖历史），两者交互约 +1–2，FIX 的卷积 V 历史约 4–6，其余卷积历史净约 0。各项都是条件作用，顺序会影响分账。

##### 5. 可以说 / 不可以说

| 可以说 | 不可以说 |
|---|---|
| e1 的约六到七成随深层历史（S+KV）走，入口单独约一到两成，二者正交互 | 入口无作用 / 深层历史单独足够 |
| 干预入口与干预历史相互放大 | 已定位到 S 或 KV |
| FIX 的 V 历史推进量在干净背景下约为 N 背景的 76–99% | FIX 必须依赖 e1 背景（P2 被否） |
| FIX 单独在干净背景下不翻转首步（0/48） | FIX 承担“关键过阈值作用” |

---

### 原件 4：EH 决策日志

原路径：`experiments/cache-entry-history-v1-2026-11-02/DECISIONS.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-entry-history-v1-2026-11-02/DECISIONS.zh-CN.md) · [单独阅读副本](../library/3d7bc005375e8c77.md)；SHA-256：`3d7bc005375e8c7763e6e161ad64c3dd7efd3932d7cf8925c5742bf2593fe0db`。

---

#### EH 决策日志

- **D1 00 不另评**：00 定义为 C_native（同一缓存、自然入口）；01、FIX0 的自然入口用闸门核对等于 x_C。
- **D2 FIX 正向 e2 取自 B3 记录**：N:CFIX、N:CC 的 logits 已在 B4 与 B3 之间逐位复现，不再重评；XH11 与 B3 N:CC 的逐位重放闸门把本轮与 B3 接上。
- **D3 runner 复用 B4 的样板**（freeze/authorize/run/verify/launch），run_item 新写；不挂 readout hook。
- **D4 评审构想稿不在仓库**：计划 v1 按对话中粘贴的内容写入仓库，并加入反向顺序 FIX 臂与两条预测。

---


## 时间、运行与停止收据索引

下面是所收集JSON的原有时间字段与状态，不把预计结束时间当实际完成时间。未列时间的文件仍有原件链接。完整JSON全部保存在原文归档，不能以此索引中的标量代替完整嵌套内容。

| 原件 | 原记录状态/阶段 | 原时间字段（原时区） |
|---|---|---|
| [readiness/cpu-receipt-r01.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-entry-history-v1-2026-11-02/readiness/cpu-receipt-r01.json) | {"status": "passed"} | {} |
| [runs/formal-r01/controller.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-entry-history-v1-2026-11-02/runs/formal-r01/controller.json) | {"status": "completed", "stage": "formal"} | {"started_at": "2026-11-01T18:07:48.681232+00:00", "finished_at": "2026-11-01T18:09:13.036226+00:00"} |
| [runs/formal-r01/verification.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-entry-history-v1-2026-11-02/runs/formal-r01/verification.json) | {"status": "passed", "stage": "formal"} | {"verified_at": "2026-11-01T18:09:13.036043+00:00"} |
| [runs/formal-r01/worker-0/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-entry-history-v1-2026-11-02/runs/formal-r01/worker-0/receipt.json) | {"status": "completed", "stage": "formal"} | {"started_at": "2026-11-01T18:07:48.776938+00:00", "last_record_at": "2026-11-01T18:09:08.046095+00:00", "finished_at": "2026-11-01T18:09:10.198104+00:00"} |
| [runs/formal-r01/worker-1/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-entry-history-v1-2026-11-02/runs/formal-r01/worker-1/receipt.json) | {"status": "completed", "stage": "formal"} | {"started_at": "2026-11-01T18:07:48.776843+00:00", "last_record_at": "2026-11-01T18:09:07.871211+00:00", "finished_at": "2026-11-01T18:09:10.003881+00:00"} |
| [runs/preflight-r01/controller.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-entry-history-v1-2026-11-02/runs/preflight-r01/controller.json) | {"status": "completed", "stage": "preflight"} | {"started_at": "2026-11-01T18:06:38.255232+00:00", "finished_at": "2026-11-01T18:07:20.340814+00:00"} |
| [runs/preflight-r01/verification.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-entry-history-v1-2026-11-02/runs/preflight-r01/verification.json) | {"status": "passed", "stage": "preflight"} | {"verified_at": "2026-11-01T18:07:20.340654+00:00"} |
| [runs/preflight-r01/worker-0/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-entry-history-v1-2026-11-02/runs/preflight-r01/worker-0/receipt.json) | {"status": "completed", "stage": "preflight"} | {"started_at": "2026-11-01T18:06:38.346262+00:00", "last_record_at": "2026-11-01T18:07:17.124170+00:00", "finished_at": "2026-11-01T18:07:19.342405+00:00"} |

## 全部原始资产入口

本目录在固定提交下共有66个跟踪文件，包含代码、原回答、失败、收据和压缩证据；文件数不是样本数。[逐文件完整账本](../assets/067-cache-entry-history-v1-2026-11-02.tsv) · [原目录](https://github.com/yuxiexiong/acupuncture/tree/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-entry-history-v1-2026-11-02)。未复制模型权重、环境或凭据。
