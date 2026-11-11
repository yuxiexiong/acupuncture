# 缓存组合读出｜CFM-CACHE-COMBINATION v1 合同 r01

历史原件；不是本次提出的假设、论证或运行要求。

原路径：`experiments/cache-update-readout-audit-v1-2026-11-01/source/experiments/cache-formation-cache-combination-v1-2026-10-31/CONTRACT.zh-CN.md`。来源：[固定提交原件](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-update-readout-audit-v1-2026-11-01/source/experiments/cache-formation-cache-combination-v1-2026-10-31/CONTRACT.zh-CN.md)；SHA-256：`ededb2b2b87460aa7f8bfb88c68b432f978736ff26b4bb456a684ab4d1fad50d`。精确字节见原文归档。

---

# 缓存组合读出｜CFM-CACHE-COMBINATION v1 合同 r01

- 编号 `CFM-CACHE-COMBINATION-v1-20261031`；设计 [缓存组合计划 v1 r2](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-update-readout-audit-v1-2026-11-01/source/docs/cache-formation-cache-combination-plan-v1-2026-10-31.zh-CN.md)（下称"方案"）。
- 承接 [CFM-FORM-READ-BRIDGE v1](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-update-readout-audit-v1-2026-11-01/source/experiments/cache-formation-readout-bridge-v1-2026-10-31)（冻结 3a4d2601，结果 ef4fe2a）：复用其冻结代码 `bridge.py` 与 formal-r01 的 τ 缓存张量（逐文件按 bridge 收据 sha 核验）。
- 冻结后不改；偏离记入 [IMPLEMENTATION.zh-CN.md](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-update-readout-audit-v1-2026-11-01/source/experiments/cache-formation-cache-combination-v1-2026-10-31/IMPLEMENTATION.zh-CN.md)。代码 `combo.py`、`combo_analysis.py`、`stage0_offline.py`、`test_combo.py`。

## 1. 对象

与 bridge 相同：Qwen3.5-4B 851bf6e8 BF16 eager；L0 N4146 −1；VAR03/04、VRD03/04、VRL03/04 × f0/f1；逐 token 路线；评分浅层 0–12 一律为同输入同事实 C 在 τ 的缓存，首步输入 x[n−1]。

深层分三组，覆盖全部深层持久张量（运行时按 `component_tensors` 断言）：

| 组 | 内容 |
|---|---|
| S | G = {13,14,16,17,18,20,21,22,24,25,26,28,29,30} 的 `recurrent_states` |
| F | 同 G 的完整 `conv_states`（全部 q/k/v 切片、全部 4 个槽位） |
| K | 全注意力层 {15,19,23,27,31} 的全部 key/value |

**槽位说明**：交换的是完整卷积缓冲；在单步更新实现下，评分这一步直接参与计算的是最近 3 个历史槽加当前输入（CPU 测试 `test_conv_slot_consumption` 在同版本实现上核验：改最老槽位逐位无影响，改次老槽位有影响）。这不推出"只有这三个位置对模型有影响"。

## 2. 阶段 A：三对来源的完整组合评分（不重新形成）

Z_ab(M)：浅层 C；M ⊆ {S,F,K} 中的组取自 b，其余取自 a。

| 对 (a,b) | 问题 |
|---|---|
| (C, CT) | 无针运行接收有针 V 后形成的深层差异，存在哪些缓存组合 |
| (TC, T) | 换回干净 V 所消掉的那部分差异，存在哪些缓存组合（"剩余"对应 C/TC，本轮不做） |
| (C, T) | 原生扎针形成的深层缓存效应（参照） |

Z_ba(M) = Z_ab(补集 M)，三对合计每输入 **22 个不同评分**：端点 C、Y_CT、Y_TC、Y_T 共 4 个，非平凡格 18 个。

## 3. 阶段 B：无针背景的随机 V 参照（新形成）

每个输入在共同干净前缀之后逐 token 形成：
- C（复核）；
- CR0、CR1：无针、B 关，G 层卷积前 V 钉为 V_C + ξ_k。

ξ_k 与 bridge 的 TR_k 用同一生成器、种子（20261031 + 1000k + crc32(输入 id)）、调用顺序和形状，范数逐层逐位置 = ‖V_T − V_C‖。V_C、V_T 取自 bridge 冻结的供体带。每个输入有两个随机抽样，有针（TR）与无针（CR）背景共用。

评分 C、Y_CR0、Y_CR1（C 浅层 + CR 深层）。预检另形成并评分 CT，用于逐位复核。

## 4. 工程闸门（任一不过即停；不重试、不放宽）

| 闸门 | 内容 | 何时 |
|---|---|---|
| 资产 | bridge 记录与张量文件 sha 等于 bridge 收据；供体带哈希等于 bridge 记录；窗口一致 | 每个输入 |
| 阶段 B 形成 | C（预检加 CT）完整 τ 缓存清单与 bridge 逐位相同；CR 实际写入 V 逐位等于供体带、q/k 切片不变；CR 的 ξ 逐元素等于按 bridge TR 算法重算的 ξ，且重算的 TR 带逐位等于 bridge 保存的 TR 带；第 0 层输出与浅层逐位等于 C；管理状态相同 | 每个输入 |
| 组覆盖 | S/F/K ∪ 浅层恰好覆盖全部持久张量 | 每个输入 |
| 阶段 A 评分 | 每格逐字段核对来源：浅层 = bridge C，各深层组 = 指定 bridge 条件；端点 C、Y_CT、Y_TC、Y_T 首步 logits 逐位等于 bridge；阶段 B 的 C 评分逐位等于 bridge C；只装只读记录器；最终 norm 逐位复算 | 每个输入 |
| 预检惰性 | 关闭记录器重评 4 个端点逐位一致；从相反条件出发换全三组，逐位重现各端点 | 预检 |
| 其他 | 校准、token、冻结、授权、CPU 收据、权重哈希、钩子移除、调用与存储上限 | 全程 |

## 5. 读数

每格：D、固定尺度 D（= D · r_X / r_C）、冻结 token 差（各停止 token − 冻结非停止 token，以及 248046−248044；冻结集合沿用 bridge）、熵、两个赢家身份、EOS、中心化单位 logits 距离、η。

对每对、每种读数，d(M) 为八格值，Δ = d(SFK) − d(∅)。报告以下各项：
- 搬入作用 A_M = d(M) − d(∅)；换回削弱 R_M = d(SFK) − d(补集 M)。
- 每个背景下加入单组的条件差。
- **完整代数分解**（以 a、b 为基底各一次）：三个单项、三个两组交互、一个三组交互，并核对它们之和等于 Δ。**这是本实验表的代数分解，不是自然机制分账**：三组交互大，也不能区分"确实需要配合""拼接失配""下游非线性"。
- 数值界：每项为所用格的 2η 之和。比例 A_M/Δ、R_M/Δ 只在 |Δ| ≥ 1 logit 且大于端点数值界时展示（这是展示规则，不是效应阈值）。
- **CT 与 T 的组合图样**：(C,CT) 与 (C,T) 逐格的 (d(M) − d(∅))/Δ、两者之差、最大绝对差，以及六个非平凡格的排序是否一致。只作描述。

阶段 B：E_CT = Y_CT − C 与 E_CRk = Y_CRk − C 的 D、冻结 token 差、赢家、中心化距离并列报告。两个抽样只支持"相对这两个抽样"的描述，不建立零分布，不证明针特异。

逐事实先算，再取情景内两事实均值，原值都保留。

## 6. 判读

方案 §5 的结果表全部适用。所有切点只作描述，不承担"机制通过"。补充两条：
- CT 与 T 的组合图样相似，会加强"V 钉入复现的效应与原生效应依赖相近缓存组合"，但不证明路径相同。不相似说明 CT 不能当作 T 的机制替身，CT 的干预证据仍然有效。
- F 的结果必须连同"F 中直接存着被钉入的 V（CT 的 V 段即 V_T）"一起解读。不从输出中扣除这一部分，也不给 q/k 与 V 分配因果份额。

## 7. 阶段 0（描述，不是闸门）

CPU 读取 bridge 的 `score_drivers` 与 `score_extras`，比较 J(T←S_U)/Y_T、J(U←S_T)/Y_U、J(W←S_H)/Y_W、J(H←S_W)/Y_H。逐层报告旧状态项、当前写入项、内核输出、z 的差，以及第 13–31 层出入口残差差、最终 h 差。只作线索，不决定阶段 A 的格子。

## 8. 规模与停止

- 预检：VAR03-f0，1 个 worker；阶段 B 4 个形成、4 次评分，阶段 A 22 次，惰性检查 8 次，合计 **4 前缀 / 34 评分**。
- 正式：每个输入阶段 B 3 / 3、阶段 A 22，共 **36 前缀 / 300 评分**；2 个 worker（每卡 1 个）。新增存储上限 8 GiB。
- 停止：预检不过不进正式；正式任一输入闸门不过即停。固定矩阵完成即停，不增加针、层、剂量、输入或随机样本。

## 9. 失败类型

闸门失败为合同执行失败，信息量为零。三组全换也不能重放端点属于工程失败，不是机制阴性。弱、异号、高阶交互都是科学结果，按方案 §5 报告。
