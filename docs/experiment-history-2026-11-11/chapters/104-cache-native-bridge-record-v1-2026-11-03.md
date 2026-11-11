# 104．NBR：NVB八格只记录重放

[返回总时间线](../README.zh-CN.md)

**时间定位**：已提取运行收据的最早时间锚点（可含预检） 2026-11-03T13:37:35.381431+08:00；不能当作全部子运行起止。

**当时的目的与设计**

重放同八格，保存状态差、读者及梯度等内部量，尝试描述背景差从哪里表现出来。

**实际过程、结果与后来更正**

这是有模型重放的诊断，不是只读CPU。其后CPU复核发现原换读者比较同时换了梯度；拆开后固定梯度读者合计变化≤0.02，状态来源投影较稳定，梯度背景效应依基点和方向变化。原错误、更正及完整数字并列。

**来源身份**：`cache-native-bridge-record-v1-2026-11-03`；本章主体来源提交 `7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8`。下方原文中的状态是各文件写作时的状态，不能把早期“尚未运行”覆盖后期正式收据，也不能将后期结果倒填进早期设计。


## 原设计、执行过程、结果与更正全文

以下按“设计与题目 → 工程/执行记录 → 结果/更正 → 其他历史说明”组织；同类内没有可靠时间时保留路径顺序，不冒充严格先后。正文未删段；仅为本章节重排标题层级、把相对链接指向固定提交。原始字节另外完整保存。

### 原件 1：NBR-01：NVB 八格的只记录重放——输出支路恢复后，变的是留存状态差，还是它被使用的方式

原路径：`docs/cache-native-bridge-record-plan-v1-2026-11-03.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/docs/cache-native-bridge-record-plan-v1-2026-11-03.zh-CN.md) · [单独阅读副本](../library/c83495245485a377.md)；SHA-256：`c83495245485a3777dd6d36361be0ce67879299de275cd4413e5ce7ece542186`。

---

#### NBR-01：NVB 八格的只记录重放——输出支路恢复后，变的是留存状态差，还是它被使用的方式

2026-11-03；v1；接 [NVB-01 报告](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-native-bridge-v1-2026-11-03/REPORT.zh-CN.md)。对应 [To-do 第 1 项](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/docs/cache-mechanism-todo.zh-CN.md)。**探索性诊断，作者自查，非独立评审。** 授权：2026-11-03 用户“修正你觉得没问题的，然后推进到实验结束”（接受只记录重放，约 0.25 GPUh 为待预检核实的估算）。合同与代码在 [`experiments/cache-native-bridge-record-v1-2026-11-03/`](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-native-bridge-record-v1-2026-11-03)。

##### 1. 问题与边界

NVB 显示：同一个“只换留存 v”的操作，在原生输出背景下对 k 效应的增强小（DS0 +0.25～+0.62），在恢复输出支路后大（DS1 +1.45～+2.12）。NVB 没有保存各层状态差与 t2 读取量，零 GPU 只能核对 ‖v1−v0‖ 的幅度（两背景几乎相同）。本轮**不加任何新条件**，逐位重放 NVB 八个主格，补测：输出支路恢复后，**留存下来的状态差是否不同**，以及**这份状态差在 t2 被读取的方式是否不同**。

交付是“哪些解释与这些测量相容、下一个最值得做的因果比较是什么”。**本轮不给机制标签，不设分支切点，不追加随机零分布**；只冻结测量定义、闸门与预算，如实报告连续结果。下一步的因果检验（候选：状态差移植，检验“差异是否可转移”）另立设计与授权，不在本轮宣称能干净分开“写入内容”与“使用方式”。

##### 2. 测量定义（`nbr_core.py`）

- S(cab)：t1 后 G 层存下的递推状态（即 t2 核读取的状态）。
- 端点状态差（真实前向相减，不用局部公式代替）：ΔS_a(c,b)=S(c1b)−S(c0b)；ΔS_b(c,a)=S(ca1)−S(ca0)；交互 I_S(c)=S(c11)−S(c10)−S(c01)+S(c00)。每层每头记录范数、跨背景余弦、‖I_S(1)−I_S(0)‖。
- 局部公式 β(k1−k0)(v1−v0)ᵀ（取 (c,1,1) 格自己的 t1 输入）只作解释与核验：报告 ‖I_S(c)−L(c)‖/‖I_S(c)‖。它只在四格输入相同的第 13 层精确成立；更深层 b 改变输入、β、k、v。
- t2（C 路线，冻结首 token）核输出分解 o=D+E+W：D=αSᵀq（直接读取）、E=−αβ(kᵀq)Sᵀk（旧预测修正）、W=β(kᵀq)v（当步写入）；每格用自己的 q。每层每头保存 D、E、W、o、q、α。
- **实际读出**与**同一 q 读取**分开：
  - 实际：各格自己的 q、α，读出交互 I_o(c)、I_D(c) 等。改变 S 后深层 q 会响应，这部分包含在实际读出里。
  - 同一 q（条件计算诊断，不是行为因果证据）：用参照格 (cq,0,0) 的 α、q 读背景 cs 的 I_S(cs)，cs、cq∈{0,1} 的 2×2；ΔS_a、ΔS_b 同样处理。
- 目标相关读出差（一阶近似诊断）：每格做一次梯度前向，得 ∂M/∂o_l（零值叶子给出经后续层传播的全导数）。投影 ⟨∂M/∂o_l, Δo_l⟩ 按层报告；**各层投影不可相加**，也不是因果份额。
- 全部按输入 × 层 × 头保存（约 3 GB），使配对分析与重新投影无需再重放。

##### 3. 闸门（任一失败即停，不当科学阴性）

1. 形成哈希等于 LVK；八格 t1 bf16 logits 与 C 路线 t2 bf16 全词表与 NVB 正式运行（冻结 r02）逐位一致。
2. 第 13 层存下的状态在 c=0 与 c=1 间逐位相同（结构事实）。
3. 复刻原核顺序的 t2 读取输出与原核逐位一致；D+E+W 与转 BF16 前的 FP32 输出相对误差 ≤1e−5。
4. 梯度前向的 M 与推理前向差 ≤0.05，梯度有限。
5. 钩子每次 14 层各触发一次；源缓存不变；模块函数还原。

预检：NVB 的两条预检输入，全方向全格；失败即停，允许一次有记录的修复重试。

##### 4. 预算

正式 48 条：t1、C t2、梯度前向各 1536；decode 4608；形成 240 / 6390 token。估计约 0.25～0.35 设备小时（未实测）；硬上限正式 0.6、预检每次 0.1、最多两次，总 ≤0.8 GPUh；两 worker 各一卡；存储 ≤12 GiB。

##### 5. 读法（探索性；写在看数据之前）

- 若 I_S(1) 与 I_S(0) 在多数层余弦高、范数比接近 1，而同一 q 的 2×2 中读者背景 cq 主导目标投影：与“同一状态差、不同使用方式”相容。
- 若 I_S 跨背景余弦低或范数差大，且状态来源 cs 主导投影：与“留存下来的状态差本身不同”相容。
- 若两者都有，或汇总量都相近而行为差很大：**写成“当前记录的量尚不能解释行为差异”，不据此定位剩余机制**；汇总相近仍可能掩盖少数层、头或任务相关方向上的差异，也不排除 E、W 与当步写入的作用。
- 上述任一情况都只用来选择下一次预先规定的因果比较，不当作机制结论。

##### 6. 设计自查（依据[规范](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/docs/experiment-design-self-check.zh-CN.md)，简版）

| 检查 | 判定 |
|---|---|
| C01/C02 | 通过。直接服务 NVB 留下的接口问题；补的是 NVB 没保存的量 |
| C05/C06 | 通过。不改任何计算；t2 以后的响应（含 q）包含在实际读出中，同一 q 读取另列为诊断 |
| C07/C08 | 通过。不使用因果词；梯度投影标为一阶诊断、不可加 |
| C09/C11 | 通过。读法允许“不能解释”；工程闸门与内容分开；无机制判据 |
| C10 | 通过。行为终点已在 NVB；本轮只记录，不另立行为终点 |
| C12 | 通过。只重放八格，不跑随机臂、不加格；存足配对信息，避免再重放 |
| C13/C14 | 通过。已见面板；结果只用来选下一次因果比较，不自动扩展 |

**对抗式检查：** (1) 局部公式会被误当实际交互 → 以端点相减为准，局部残差单列。(2) 余弦接近被读成“无关” → 同时报告范数、目标投影；汇总相近不排除少数方向。(3) 梯度投影被相加成份额 → 明文禁止，按层报告。(4) 同一 q 读取被读成因果 → 明确为条件计算诊断。

---

### 原件 2：NBR-01 合同 r01：NVB 八格的只记录重放

原路径：`experiments/cache-native-bridge-record-v1-2026-11-03/CONTRACT.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-native-bridge-record-v1-2026-11-03/CONTRACT.zh-CN.md) · [单独阅读副本](../library/35950c58429ad350.md)；SHA-256：`35950c58429ad35090e3e15b20f04842dc56b34b195d5e1624cb13d19f0baa8e`。

---

#### NBR-01 合同 r01：NVB 八格的只记录重放

依据 `docs/cache-native-bridge-record-plan-v1-2026-11-03.zh-CN.md`。授权：2026-11-03 用户“修正你觉得没问题的，然后推进到实验结束”。探索性诊断：冻结测量定义、闸门与预算；不设机制判据、分支切点或随机零分布。冻结后不改本文件；偏离记入 `DEVIATIONS.zh-CN.md`。

1. 范围：LVK 新面板 48 条 × 4 方向 × NVB 八个主格（不跑随机臂、不加格），t1 用 NVB 冻结 r02 的 NHook（加只读输入记录），t2 只走 C 路线（只读捕获）加一次梯度前向。
2. 测量：计划 §2（`nbr_core.py`）。端点状态差 ΔS_a、ΔS_b、I_S 及跨背景范数/余弦/差；局部公式残差；t2 D/E/W/o/q/α；同一 q 交叉读取（I_S、ΔS_a、ΔS_b 的 2×2）；∂M/∂o_l。按输入 × 层 × 头保存。
3. 闸门：计划 §3 第 1–5 条（运行中断言）。
4. 报告：`nbr_analysis.py` 输出连续汇总（目标非首列 32 条、六场景等权的目标投影；状态统计取输入 × 头中位数）；按计划 §5 的读法写“相容 / 不能解释”，不给机制标签；梯度投影按层、不可加。
5. 预算：正式 t1/C t2/梯度各 1536、decode 4608、形成 240/6390；设备小时上限正式 0.6、预检 0.1（重试另 0.1）；总 ≤0.8；最多 2 worker；存储 ≤12 GiB。
6. 产物：`runs/preflight-r01/`、`runs/formal-r01/`、`analysis/nbr-readouts-r01.json`、`REPORT.zh-CN.md`。

---

### 原件 3：NBR-01 偏离与修复记录

原路径：`experiments/cache-native-bridge-record-v1-2026-11-03/DEVIATIONS.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-native-bridge-record-v1-2026-11-03/DEVIATIONS.zh-CN.md) · [单独阅读副本](../library/0d5b320acdefdda9.md)；SHA-256：`0d5b320acdefdda9afb1a5cc15bcecff1567cd689f05882c4725ea92e1c5f0b3`。

---

#### NBR-01 偏离与修复记录

##### D1（2026-11-03，预检 r01 合同执行失败 → 修复重试 r02）

- **现象**：`runs/preflight-r01` 的第一次梯度前向反向时报错：`one of the variables needed for gradient computation has been modified by an inplace operation: [1, 32, 128, 128] ... version 1; expected version 0`。约 28 设备秒，无记录，无判读证据。**分类：合同执行失败（信息量为零）。**
- **根因**：t2 核读取缓存中的递推状态，autograd 为反向（对 q 等的梯度）保存了这块张量；随后模型按正常流程把新状态原地写回同一张量。CPU 测试只用了独立张量，没有走“缓存原地更新”这条真实调用路径。
- **修复**：梯度模式下，每个线性注意力层把 `initial_state.detach().clone()` 交给原核，卷积更新也使用 `conv_state` 的克隆。只改变 autograd 看到的张量身份，前向数值不变（梯度前向的缓存随后丢弃）；推理前向与逐位闸门不受影响。CPU 测试新增一例：用真实原核与原地写回复现报错，并验证修复后可反向、输出逐位不变。
- **共卡**：本次预检开始时，另一条工作流（cache-chain-generalization）在两张卡上各有一个约 10 GB 的进程。显存合计远低于 96 GB；batch1 推理逐进程独立，数值由逐位重放闸门检验；只影响耗时。不动对方进程。
- **重试**：唯一一次有记录的修复重试：CPU 收据 r02、冻结 r02、授权 preflight-r02、输出 `runs/preflight-r02`；r01 目录原样保留。

---

### 原件 4：NBR-01 报告 r01：NVB 八格只记录重放

原路径：`experiments/cache-native-bridge-record-v1-2026-11-03/REPORT.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-native-bridge-record-v1-2026-11-03/REPORT.zh-CN.md) · [单独阅读副本](../library/33fb9b417b739a35.md)；SHA-256：`33fb9b417b739a352a7a68c250832b269956387dde0b4a35fc6ebde9f134250b`。

---

#### NBR-01 报告 r01：NVB 八格只记录重放

计划 [v1](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/docs/cache-native-bridge-record-plan-v1-2026-11-03.zh-CN.md)；合同 `CONTRACT.zh-CN.md`；冻结 r02 `b8dc2fdb…`（代码 c6e0429）。汇总 `analysis/nbr-readouts-r01.json`（`nbr_analysis.py`）。按输入 × 层 × 头的张量（约 3 GB）留在服务器 `runs/formal-r01/worker-*/tensors`。**探索性诊断：只回答“哪些解释与测量相容、下一个最值得做的因果比较是什么”，不给机制标签。**

> **更正（11-03 评审后，离线重算，未上卡）**
> 1. §3 的表在“换读者”时**同时换了投影梯度**（梯度取在读者背景的参照格）。所以原文“固定梯度时换读者几乎不变”“+0.22→+0.82 是下游敏感度”都没有依据。按评审要求用已保存张量拆开重算（`analysis/nbr_reproject.py` → `analysis/nbr-reproject-r01.json`）：
>    - 只换读者 q、α，固定梯度：三个缺口方向各层合计变化 ≤0.02，逐层也一致，**读者作用小在拆开后成立**。
>    - 只换状态来源，固定读者与梯度：基点 00 下 +0.29～+0.35，基点 11 下 +0.33～+0.62，**稳定**。
>    - 只换梯度背景，固定读出：基点 00（000 对 100）只有 +0.04～+0.11；基点 11（011 对 111）N4146 +0.60～+0.85、R0 +0.15～+0.22、N1210 +0.05。**“下游敏感度”只在一个线性化点、主要在一个方向上大**，降为未定；线性化点本身对投影影响很大，一阶投影在这里不稳。
>    - 逐层：状态来源效应的目标投影集中在第 16–18 层与第 22 层；第 24–30 层状态差变化最大，但一阶目标投影接近 0。
> 2. §0 第 1 条与 §5 的“没有一个量能单独解释”改为：**本轮尚未证明任何一个量足以解释行为差异**（诊断没完成归因，不等于已证明必须由多个因素共同解释）。
> 3. 各层合计不可分配，以逐层结果为主。
> 4. §6 的候选修正：移植整份 S ≠ 只移 ΔS（整份含基底与其他主效应）。优先只移状态差 S(0,1,b) := S(0,0,b)+ΔS_a(1,b)，整份 S 作对照；层先取 16–22，另设 24–30 一臂检验“变化大、投影近 0”的部分。仍需另立设计与授权。

##### 0. 先说限制

1. **没有一个量能单独解释行为差异。** 状态差本身、t2 之后的下游敏感度、t2 深层 q 的响应，三者都随输出支路恢复而变，各自只能说明一部分。按预先写好的读法：当前记录的量尚不能把行为差异定位到其中某一处。
2. 目标投影是 ∂M/∂o 的一阶近似，按层报告，**各层不可相加**，下文的“各层合计”只用于两种背景之间的同口径比较，不是份额。线性化点选在不同的格时，数值会明显变化（见 §3）。
3. 汇总取中位数或场景等权均值，可能掩盖少数头或方向。
4. 预检 r01 是一次合同执行失败（梯度前向的原地写入，DEVIATIONS D1），已用掉唯一一次修复重试。另一条工作流在两张卡上同时运行；逐位重放闸门全部通过，所以数值不受共卡影响。
5. 已见开发面板，R 族，一个模型。

##### 1. 工程

48/48 通过验证。八格 t1 与 C 路线 t2 逐位重放 NVB 正式运行；第 13 层存下的状态在 c=0 与 c=1 之间逐位相同；复刻读取与原核逐位一致，D+E+W 误差 ≤2.7e−8；梯度前向的 M 与推理前向完全相同。设备时间 599+449 s（0.29 h），加两次预检约 0.31 GPUh（上限 0.8）。

##### 2. 留存状态差：深层随输出支路恢复而变大、转向（三个缺口方向一致）

交互 I_S(c)=S(c11)−S(c10)−S(c01)+S(c00)，输入 × 头中位数：

| 层 | 13 | 14–17 | 18 | 20–22 | 24–26 | 28–30 |
|---|---|---|---|---|---|---|
| ‖I_S(1)‖/‖I_S(0)‖ | 1.00 | 0.94–1.12 | 1.18–1.21 | 1.40–1.61 | 1.18–1.48 | 1.35–1.75 |
| cos(I_S(0), I_S(1)) | 1.00 | 1.00 | 0.98–0.99 | 0.91–0.96 | 0.76–0.94 | 0.93–0.96 |
| ‖I_S(1)−I_S(0)‖/‖I_S(0)‖ | 0 | 0.12–0.34 | 0.43–0.48 | 0.69–1.04 | 0.66–0.97 | 0.61–1.01 |

- 第 13 层相同（结构）；14–17 层几乎相同；**从第 18 层起，恢复输出支路后存下的交互更大（约 1.2–1.75 倍），方向也有偏转。** 只改留存的差 ΔS_a(c,1) 有同样的模式，但幅度较小。
- 局部公式 β(k1−k0)(v1−v0)ᵀ 对真实交互的相对残差：c=0 时 0.03–0.17，c=1 时深层 0.2–0.64。也就是说，恢复输出支路后的深层交互有相当部分来自上游输入的变化，而不是本层局部公式。

##### 3. 同一 q 读取的目标投影（条件计算诊断，各层合计，目标非首列 32 条、场景等权）

2×2：状态差来源 cs（哪种背景的 I_S）× 读者 cq（用哪种背景参照格的 α、q）。投影所用梯度取在 (cq,0,0)（记 g00）或 (cq,1,1)（记 g11）。

| 方向 | g00：s0q0 / s0q1 / s1q0 / s1q1 | g11：s0q0 / s0q1 / s1q0 / s1q1 |
|---|---|---|
| N4146 | +0.04 / +0.06 / +0.34 / +0.37 | +0.22 / +0.82 / +0.59 / +1.44 |
| N1210 | +0.31 / +0.36 / +0.60 / +0.67 | +0.51 / +0.57 / +0.84 / +0.90 |
| R0 | +0.50 / +0.57 / +0.82 / +0.92 | +0.76 / +0.91 / +1.16 / +1.38 |

- **固定梯度时，换 t2 的读者 q 几乎不改变投影**（g00 一列：s0q0→s0q1、s1q0→s1q1 都只差 +0.02～+0.10）。
- **换状态差的来源，投影明显变大**（g00：s0→s1 增加 +0.29～+0.33）。
- **换线性化点（下游敏感度）也有作用**：同一份 I_S(0) 用 c=1 背景 (1,1,1) 格的梯度投影，比用 (0,1,1) 格的梯度更大（N4146 +0.22→+0.82；N1210 +0.51→+0.57；R0 +0.76→+0.91），N4146 最明显。
- 只改留存 ΔS_a(c,1) 的同一 q 读取（g 取 (cq,0,1)）同样是来源与下游敏感度都起作用，读者 q 作用小。

##### 4. 实际读出交互（各格自己的 q；同口径 g00）

| 方向 | Io(c=0) | Io(c=1) | ID(c=0) | ID(c=1) | 行为 DS0 / DS1 |
|---|---:|---:|---:|---:|---|
| N4146 | +0.14 | +1.04 | +0.10 | +1.04 | +0.25 / +2.12 |
| N1210 | +0.41 | +0.87 | +0.44 | +0.93 | +0.49 / +1.45 |
| R0 | +0.50 | +1.01 | +0.58 | +1.13 | +0.62 / +1.58 |

- 实际输出交互随背景的变化方向与行为一致，主要由直接读取 D 承担；修正项 E（−0.13 到 +0.01）与当步写入 W（≤0.09）都小，c=1 下 W 在第 30 层略负。
- **实际读出与同一 q 读取的差（即 t2 时上游状态改变引起的深层 q、α 响应）在 c=1 下集中在第 22 层和第 18 层。** 第 22 层：实际 ID(c=1) 为 +0.72 / +0.28 / +0.21，同一 q 只有 +0.16 / +0.11 / +0.04；c=0 时两者接近。
- C1343（诊断）模式不同：c=0 时第 13–18 层已有大投影（实际 Io +3.77），与它 DS0 大相符。

##### 5. 与哪些解释相容

- **“留存下来的状态差本身随背景改变”相容**：深层（≥18 层）交互更大、方向偏转，且同一 q、同一梯度下换状态来源就提高目标投影。
- **“下游计算对读出的敏感度随背景改变”相容**：换线性化点有作用，N4146 最明显。
- **“t2 当步 G 层读者 q 改变”在同一 q 诊断里作用很小**；但上游状态改变引起的深层 q 响应（第 22、18 层）在实际读出里不可忽略。这两点不矛盾：前者是固定其他条件只换读者，后者是 t2 前向中的连锁响应。
- 三者都有，且一阶投影不可加，所以**不能给出份额，也不能断言主要来源**。

##### 6. 最值得做的下一个因果比较（候选，需另立设计与授权）

**深层状态移植（检验“差异是否可转移”）**：在 c=0（原生输出）背景的 t1 之后，把 c=1 背景对应格存下的第 18–30 层 G 层状态装进去（四格一起换，保留 13–17 层和全部非 S 缓存），看 k 效应的条件增强是否接近 DS1；反向把 c=0 的深层状态装进 c=1 背景。理由：§2 的跨背景差异集中在 ≥18 层，§3 的“状态来源”效应可在固定读者下出现；这个比较不需要先确定下游敏感度的部件。它仍依赖接收背景的其他缓存与后续响应，只能回答“这份深层状态差能否在原生背景里起作用”，不能完全分开“写入内容”与“使用方式”。若移植后增强仍小，则把重点转向下游敏感度与第 22 层的 q 响应。

本轮不自动追加实验。

---

### 原件 5：NBR-01 决策日志（冻结前）

原路径：`experiments/cache-native-bridge-record-v1-2026-11-03/DECISIONS.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-native-bridge-record-v1-2026-11-03/DECISIONS.zh-CN.md) · [单独阅读副本](../library/45a9852f65f3ca41.md)；SHA-256：`45a9852f65f3ca413bf1208b0eb73ae0c771be613d12d686434b71f51ba65ef6`。

---

#### NBR-01 决策日志（冻结前）

- R1 按评审修正：状态差以真实端点相减为准，局部公式只作核验；“写入、读取都相近所以机制在读取之后”的出口撤回，改为“当前记录的量尚不能解释行为差异”；保存按输入 × 层 × 头的配对信息；实际读出与同一 q 读取分开；移植只作候选。
- R2 不追加随机零分布：本轮探索性，不设分支切点（撤回上一轮“用随机条件标定切点”的说法，它与“不跑随机臂”矛盾）。
- R3 目标相关读出用 ∂M/∂o_l（零值叶子，全导数），每格一次梯度前向；缓存先克隆为普通张量（推理模式张量不能进反向图）。
- R4 E 项与 W 项一并保存，以免汇总只看 D 而遗漏修正项与当步写入。

---


## 时间、运行与停止收据索引

下面是所收集JSON的原有时间字段与状态，不把预计结束时间当实际完成时间。未列时间的文件仍有原件链接。完整JSON全部保存在原文归档，不能以此索引中的标量代替完整嵌套内容。

| 原件 | 原记录状态/阶段 | 原时间字段（原时区） |
|---|---|---|
| [readiness/cpu-receipt-r01.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-native-bridge-record-v1-2026-11-03/readiness/cpu-receipt-r01.json) | {"status": "passed"} | {} |
| [readiness/cpu-receipt-r02.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-native-bridge-record-v1-2026-11-03/readiness/cpu-receipt-r02.json) | {"status": "passed"} | {} |
| [runs/formal-r01/controller.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-native-bridge-record-v1-2026-11-03/runs/formal-r01/controller.json) | {"status": "completed", "stage": "formal"} | {"started_at": "2026-11-03T05:43:50.544520+00:00", "finished_at": "2026-11-03T05:53:59.627228+00:00"} |
| [runs/formal-r01/verification.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-native-bridge-record-v1-2026-11-03/runs/formal-r01/verification.json) | {"status": "passed", "stage": "formal"} | {"verified_at": "2026-11-03T05:53:59.626885+00:00"} |
| [runs/formal-r01/worker-0/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-native-bridge-record-v1-2026-11-03/runs/formal-r01/worker-0/receipt.json) | {"status": "completed", "stage": "formal"} | {"started_at": "2026-11-03T05:43:54.864415+00:00", "last_record_at": "2026-11-03T05:53:50.927533+00:00", "finished_at": "2026-11-03T05:53:53.468792+00:00"} |
| [runs/formal-r01/worker-1/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-native-bridge-record-v1-2026-11-03/runs/formal-r01/worker-1/receipt.json) | {"status": "completed", "stage": "formal"} | {"started_at": "2026-11-03T05:43:54.907431+00:00", "last_record_at": "2026-11-03T05:51:20.974164+00:00", "finished_at": "2026-11-03T05:51:23.517763+00:00"} |
| [runs/preflight-r01/controller.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-native-bridge-record-v1-2026-11-03/runs/preflight-r01/controller.json) | {"status": "failed", "stage": "preflight"} | {"started_at": "2026-11-03T05:37:35.381431+00:00", "finished_at": "2026-11-03T05:38:08.388106+00:00"} |
| [runs/preflight-r01/worker-0/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-native-bridge-record-v1-2026-11-03/runs/preflight-r01/worker-0/receipt.json) | {"status": "failed", "stage": "preflight"} | {"started_at": "2026-11-03T05:37:39.607546+00:00", "finished_at": "2026-11-03T05:38:07.295497+00:00"} |
| [runs/preflight-r02/controller.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-native-bridge-record-v1-2026-11-03/runs/preflight-r02/controller.json) | {"status": "completed", "stage": "preflight"} | {"started_at": "2026-11-03T05:41:36.683669+00:00", "finished_at": "2026-11-03T05:42:48.851633+00:00"} |
| [runs/preflight-r02/verification.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-native-bridge-record-v1-2026-11-03/runs/preflight-r02/verification.json) | {"status": "passed", "stage": "preflight"} | {"verified_at": "2026-11-03T05:42:48.851452+00:00"} |
| [runs/preflight-r02/worker-0/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-native-bridge-record-v1-2026-11-03/runs/preflight-r02/worker-0/receipt.json) | {"status": "completed", "stage": "preflight"} | {"started_at": "2026-11-03T05:41:40.824033+00:00", "last_record_at": "2026-11-03T05:42:43.021535+00:00", "finished_at": "2026-11-03T05:42:45.864152+00:00"} |

## 全部原始资产入口

本目录在固定提交下共有119个跟踪文件，包含代码、原回答、失败、收据和压缩证据；文件数不是样本数。[逐文件完整账本](../assets/104-cache-native-bridge-record-v1-2026-11-03.tsv) · [原目录](https://github.com/yuxiexiong/acupuncture/tree/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-native-bridge-record-v1-2026-11-03)。未复制模型权重、环境或凭据。
