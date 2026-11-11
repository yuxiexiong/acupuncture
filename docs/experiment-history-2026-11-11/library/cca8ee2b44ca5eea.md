# QKF-01（共同偏移的 q/k 分量与完整回答效应）合同 r01

历史原件；不是本次提出的假设、论证或运行要求。

原路径：`experiments/cache-qk-component-factor-v1-2026-11-02/CONTRACT.zh-CN.md`。来源：[固定提交原件](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-qk-component-factor-v1-2026-11-02/CONTRACT.zh-CN.md)；SHA-256：`cca8ee2b44ca5eeab459faac40b27db7e5b4dc0cb550f3ae8ddcbe04f1bae242`。精确字节见原文归档。

---

# QKF-01（共同偏移的 q/k 分量与完整回答效应）合同 r01

日期：2026-11-02。设计：[计划 v1](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/docs/cache-qk-component-factor-plan-v1-2026-11-02.zh-CN.md)（评审撰写，7289925d）+ [自查](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/docs/cache-qkf-self-check-v1-2026-11-02.zh-CN.md)。授权：用户 2026-11-02「如果这个计划你没有什么问题就直接实施，小问题直接修复，大问题跟我沟通」。输入、形成与编辑位置沿用 QCO-01；V/F/R/A/R_rand/A_rand 已见（作为重放参照），单半臂与 r_post 臂运行前无输出。本合同照计划执行，唯一改动见 §0。

## 0. 相对计划的小修复（决策 D3）

r_post 的逐头配平容差由 5% 改为 **6%**。依据：在任何模型输出之前，用采集阶段保存的同一组基底 q/k、冻结的 μ 与 r_pre，在 CPU 上按运行时完全相同的算术（FP32 相加后一次转 BF16）模拟了全部 258,048 次逐头检查：2 次超过 5%（最大 5.03%），全部低于 6%。5% 会让 1–2 个随机对照因 BF16 舍入被判“工程不可判”，与配平本身是否成功无关。r_post 构建脚本在冻结后、预检前再次运行同一模拟并写入清单；清单状态 passed 才允许授权。

## 1. 臂（每输入 × 方向 N4146、N1210、R0；C1343 无缺口，不加入）

接收者 T(i,d)；G 卷积 V（四槽）取 C(i)；S/KV/浅层取 T(i,d)。q 通道 [0, 2048)、k 通道 [2048, 4096)，只编辑槽 [1, 4)。

| 臂族 | q/k 基底 | 编辑 | 数量 |
|---|---|---|---:|
| V / F | Q_T / Q_C | 无 | 2 |
| R_{u,h} | Q_T | 减 m_h·u | 9 |
| A_{u,h} | Q_C | 加 m_h·u | 9 |

u ∈ {μ（QCO 留一场景共同偏移）, r_pre（QCO 卷积前等范数随机）, r_post（r_pre 按层×分量×头缩放，使首读旧槽卷积贡献等于 μ）}，h ∈ {q, k, qk}。另 C 自然 1 条、每方向 T_nat 1 条。V、F、R_μ,qk、A_μ,qk、R_pre,qk、A_pre,qk、C、T_nat 与 QCO 正式记录逐位重放。只读观察器在首个读出步保存 14 层 in_proj_qkv 的 q/k 输出（x_now），供 §4.3 的描述分析。

## 2. 判据（冻结，qkf_core.py；照计划 §5–§6）

- E_s 六场景等权；G = E_s[Y_F − Y_V]，适用当 G > 0 且 ≥4 场景缺口为正；D_i = 1[Y_F = 1 且 Y_V = 0]；P(u,h) = E_s[Y_R − Y_V]/G；B(u,h) = E_s[D_i·1(ids_A = ids_V)]/E_s[D_i]。
- 单半（μ）：恢复成立当 P ≥ 0.5 且 ≥4 场景净改善为正；复现成立当 B ≥ 0.5 且 ≥4 场景出现逐 token 复现。
- 对随机档的优势：P_μ − P_tier ≥ 0.25（B 同），仅当该档配平检查对全部输入通过（r_pre：同掩码同侧实际总编辑范数相对差 ≤5%；r_post：逐层×分量×头首读旧槽贡献相对差 ≤6%）；否则该比较“工程不可判”。
- **推测档预测（允许失败）**：k 分量强于 q：P_k − P_q ≥ 0.25 且 B_k − B_q ≥ 0.25，恢复差 ≥4/6 场景为正，复现差在有 D 的场景中 ≥⌈2/3⌉ 为正；反向为 q 强；仅一侧为不对称；否则无排序。
- 四格交互：I_Y^R、I_Y^A、I_B、I_M（固定竞争者：目标非首列取首列，否则取第二条）；|I| ≥ 0.10 且 ≥4 场景同号才称“该指标上可见非加和”；饱和导致的负 I 不称拮抗。
- 三方向逐一报告；不设跨方向多数门槛；出口按计划 §7。

## 3. 预算

| 阶段 | 预填 | 形成 | 自然轨迹 | 解码上限 | 诊断 | 设备时间上限 |
|---|---:|---:|---:|---:|---:|---:|
| 预检（2 输入，含每方向 R_zero/A_zero） | 2 | 8 | 140 | 4480 | 140 | 0.25 h |
| 正式（48 输入，2 worker） | 48 | 192 | 3072 | 98304 | 3072 | 1.5 h |

全轮 ≤2 设备小时、产物 ≤12 GiB；张量（含 x_now、r_post）留服务器，哈希入 Git。预检工程失败可修复重试一次；正式不重试。

## 4. 工程闸门

C/T 哈希 = QCD G；每臂 V 块 = C(i)、q/k 槽 0 = 基底、S/KV/浅层 = T，未编辑臂 q/k = 基底；供体与基底不变；参照臂与 QCO 逐位重放（同时证明观察器只读）；预检零编辑无写入且逐位复现 V/F；r_post 清单 passed 且哈希一致；生成前无 hook。

## 5. 交付

`runs/{preflight,formal}-r01/`、`runs/rpost-r01/rpost.pt`（服务器）、`analysis/rpost-manifest-r01.json`、`analysis/qkf-readouts-r01.json`、首读几何描述、`REPORT.zh-CN.md`。
