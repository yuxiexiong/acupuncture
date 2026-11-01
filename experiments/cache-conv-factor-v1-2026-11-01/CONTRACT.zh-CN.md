# CFM-CONV-FACTOR v1 实验合同 r01

日期：2026-11-01。设计：[方案 v1 r2](../../docs/cache-conv-value-qk-readout-plan-v1-2026-11-01.zh-CN.md)、[机器矩阵 design.json](../cache-conv-factor-design-audit-v1-2026-11-01/design.json)、[阶段路线图](../../docs/cache-mechanism-stage-roadmap-2026-11-01.zh-CN.md) 第 A 步。合同与方案冲突以方案 r2 为准；偏离记入 [DECISIONS](DECISIONS.zh-CN.md)。运行授权：用户 2026-11-01 指令“如果没有大的修改意见的话，直接写合同代码，然后做测试上卡实验就好”。

## 1. 对象

Qwen3.5-4B 851bf6e8，BF16、eager；原 L0/N4146/−1 晚段针，归档 bridge formal-r01 的 C/T τ 缓存；12 输入 = 6 已见情景 × 2 事实。评分只在最后提示 token 做一步（撤针、无生成），单 token recurrent 路线。

## 2. 操作（方案 §3–4）

- 浅层 0–12 一律 C。深层 14 个 G 层：S=recurrent_states 取 S 供体；F=conv_states 的通道 0:4096（q 0:2048、k 2048:4096，合称 Q）取 Q 供体，4096:8192（V）取 V 供体，4 个槽一并复制；深层全注意力 K/V 取 K 供体。
- M：第13层入口自然为 x_C。N 与 D_step：decoder13 入口替换为归档 T_native 的 x_T（LOCAL-READOUT 已验证的边界）。
- 每输入 22 格：M:{S}{Q}{V} 8 格（K=T）；N:{Q}{V} 4 格（S=T、K=T）；C（全 C）；D_step（x_T + 全 C 深层）；随机 8 格（M:TTT 或 N:TT 基底，Q 或 V 段加位移，两条方向）。
- 随机位移：种子 20261101 + 1000·j + crc32(input|seg)，seg∈{q,k,v}；CPU float64；G 层升序，每层抽 [4 槽, 头数, 128] 标准正态，逐（槽,头）单位化后乘该（槽,头）C−T 差的 L2 范数；加到 T 后转 BF16。Q 条件同时扰动 q、k 两段。
- 预检（VAR03-f0、VRL04-f0）每输入另加 4 次：M:TTT、N:TT 的记录器关闭重评；M:TTT、N:TT 的“整段 F 复制”（不分段组装）重评。

## 3. 预算（代码 `LIMITS` 强制）

| 阶段 | 前缀形成 | 单步评分 | 模板前向 |
|---|---:|---:|---:|
| 预检 | 0 | 52 | 1 |
| 正式 | 0 | 264 | 2 |

GPU 上限：预检 10 分钟、正式 2 worker 各 15 分钟；存储 ≤ 8 GiB，大张量留服务器。

## 4. 工程闸门（任一不过 → 中止，记合同执行失败）

1. 来源：bridge 记录与张量、COMBO 记录按收据 sha256 校验；提示 token 哈希三方一致；a_i（design.json）等于 bridge C 的非停止赢家；`<think>`=248068；停止集 {248044, 248046}。
2. 缓存：每格每字段哈希等于预定来源张量（分段组装后的 F 以组装张量计）。
3. 重放：C、M:TTT、N:TT 的 logits 逐位等于 bridge C、Y_T、T_native；M 的 q=v 四角逐位等于 COMBO 的 S=s,F=f,K=T；Y_T、T_native 的 14 层驱动逐位一致；每个 N/D_step 格第13层入口等于归档 x_T。
4. 内核：每格 14 个 G 层的 recurrent 内核各恰好命中 1 次，chunk 内核 0 次；入口钩子每格命中 1 次。
5. 重构：FP64 Sᵀw+n 对实际 core 的相对误差 ≤ 0.003（每格每 G 层，S 取该格 S 供体）。
6. 随机：每层每段在实际读取的槽 1–3 上，实际位移范数与目标相差 ≤ 5%；零目标严格不改。
7. 预检：记录器关闭、整段复制两类重评 logits 逐位等于对应记录格。
8. 冻结：freeze-r01 全部文件哈希在授权、运行、验证时一致。

## 5. 读数与判据（冻结，方案 §5–6）

- 主读数：去词表均值后的 z_a、z_248046（cz_a、cz_s46）。派生必报：248046−a、think−a、248044−a、248046−think、动态 D、首步赢家；固定 C 最终归一化分母的固定词 logit。
- 效应：每背景 b∈{M_T, M_C, N}：G、A_V、R_V、A_Q、R_Q、I（方案 §5.2）。情景值 = 两事实差的均值；|G|<1 logit 的情景标为不可判。
- H_V / H_Q：A_part/G 与 R_part/G 都在 [0.7, 1.3]，另一分量 |A/G|、|R/G| 都 ≤ 0.3，≥5/6 情景满足。
- H_add：|I/G| ≤ 0.2，≥5/6 情景满足。
- H_transfer（动态 D，有额外假设）：G_N/G_T ∈ [0.75, 1.33]，≥5/6 情景满足。
- 不预测 A_V 与 R_V 的大小顺序，只登记 (A_V−R_V)/G。
- 随机比较（M_T、N × Q、V × 两个主读数，共 8 组）：两事实 |G| 都 ≥ 1 才可判；情景“超过”= 两事实 E_i=sign(G_i)·R_i 都 >0，且 mean(E_i) > max_j mean(|R_ij|) + 0.1。≥5/6 情景超过，该组才记“稳定超过”。8 组全未达到 → 停止以方向特异性为依据追加实验（不宣布一般扰动胜出）。
- D_step 校准（非工程门槛）：(d−C)/(T_native−C) ∈ [0.05, 0.25]，|交互比例| ≤ 0.2。

## 6. 停止条件

预检任一闸门失败 → 不进入正式，定位后按 DECISIONS 记账，修订预算后才能重跑。正式运行中任一 worker 失败 → 终止另一 worker，保留部分证据。结果不利不调阈值、不加种子或剂量、不扩层扩针。

## 7. 输出

`runs/preflight-r01/`、`runs/formal-r01/`（记录 JSON 进 git；张量留服务器）；`analysis/readouts-r01.json`（`cf_analysis.py`）；`readiness/`（CPU 收据、真实数据预演、授权）。冻结后的代码提交哈希记入授权文件 `code_commit`。
