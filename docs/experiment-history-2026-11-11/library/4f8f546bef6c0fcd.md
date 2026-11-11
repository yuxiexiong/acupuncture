# QC-01（目标指定 × 问题布局 × 注入覆盖）合同 r01

历史原件；不是本次提出的假设、论证或运行要求。

原路径：`experiments/cache-query-layout-coverage-v1-2026-11-02/CONTRACT.zh-CN.md`。来源：[固定提交原件](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-query-layout-coverage-v1-2026-11-02/CONTRACT.zh-CN.md)；SHA-256：`4f8f546bef6c0fcdf4d67596b919100d973d3d9e1264d2e49ba503f9fcfd26f2`。精确字节见原文归档。

---

# QC-01（目标指定 × 问题布局 × 注入覆盖）合同 r01

日期：2026-11-02。设计：[计划 v1](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/docs/cache-query-layout-coverage-plan-v1-2026-11-02.zh-CN.md)（评审撰写，8f9324e）+ [自查](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/docs/cache-query-layout-coverage-self-check-v1-2026-11-02.zh-CN.md)。授权：用户 2026-11-02「如果没什么大问题就推进，小问题你直接修复。可以直接写代码合同，测试上卡」。NQ-01 面板与结果已见；五个新条件此前无模型输出。

## 1. 条件与面板

NQ-01 的 6 场景 × 3 顺序 × 3 查询（唯一来源 NQ data/inputs-r01.json）。六个条件：

| 条件 | 目标指定 | 问题位置 | 注入窗口 | 窗口 token 数 |
|---|---|---|---|---:|
| NB | 按名 | 记录前 | 固定尾部 | 20（NQ-01，按场景 ABC/问 A 逐位重放，其余复用） |
| LB | 记录内“目标条目”标签，问“目标条目的编号是什么？” | 记录前 | 固定尾部 | 20 |
| NA | 按名 | 记录后 | 问题 + 固定尾部 | 26–27 |
| LA | 标签 | 记录后 | 问题 + 固定尾部 | 27 |
| NA-tail | 按名（文本 = NA） | 记录后 | 仅固定尾部 | 20 |
| LA-tail | 标签（文本 = LA） | 记录后 | 仅固定尾部 | 20 |

真实分词器审计（data/tokens-r01.json，冻结）：无跨界 token；LB、NA-tail、LA-tail 的窗口 token 与 NQ-01 固定窗口逐位相同且问题 token 全在 b 之前；NA、LA 的窗口解码 = 问题 + 换行 + NQ 窗口，问题全在窗口内；共同首 token / 第二 token 可区分。标签式更换目标也改变记录文本。

## 2. 操作

每输入由冻结的 NQ-01 runner 执行（C_nat；每方向 T_nat、T_V、T_F；同前缀诊断分叉），只把边界文本换成本条件的（tail 条件 = 记录 + 换行 + 问题）。**校准不重做**：六份 NQ-01 场景校准原值（哈希记入回执）。模型、方向、剂量、深层 G 层、恢复与生成规则全部沿用 NQ-01。窗口长度不同导致注入总量不同，**不配平**；记录每条件窗口长度与每 token 名义写入范数。全矩阵一次运行，不按结果补跑或删臂。

## 3. 判据（冻结）

- 每条件独立用 NQ-01 规则（nq_core）：C 面板合格（≥5/6 场景各 ≥8/9）、每方向损伤迁移（≥4/6 场景各 ≥6/9 为 C 对且 T_nat 错）、场景类别（跟随查询/首位/固定身份/混合，≥8/9）、方向标签（≥5/6）。不适用记不可判，不算阴性。
- **P_cov（推测档，预注册）**：对 N 与 L 两种指定方式，tail 条件 T_V“跟随查询”在固定 4 方向中 ≥3 个支持，**且**同文本宽覆盖条件未达到（即使把其不可判方向都算支持也 < 3）。宽覆盖已达 3/4 → “无可见修复空间”；tail 只因不可判而不足 → 不可判。两种指定方式都支持才算 P_cov 成立。
- 描述（不进判据）：三组预定比较——指定方式（NB/LB、NA/LA、NA-tail/LA-tail）、覆盖（NA/NA-tail、LA/LA-tail，同文本，覆盖与剂量混淆）、布局（NB/NA-tail、LB/LA-tail，问题均不注入，含上下文与位置变化）；每方向各臂交付数、配对四格表、T_V 恢复增量（Y_V − Y_nat）、非首位 36 格的目标/首列计数、T_F 结果；同前缀诊断与 Q 只作描述。若缩窄使 T_nat 本身恢复，记为减轻损伤，不是 V 修复更强。

## 4. 预算

| 阶段 | 形成 | 自然轨迹 | 解码上限 | 诊断 | 校准 |
|---|---:|---:|---:|---:|---:|
| 预检（5 条件 × NQ01-ABC-A；LA 上重建 C/T4146；NB 重放 NQ01-ABC-A） | 32 | 80 | 2560 | 80 | 0 |
| 正式（270 新输入 + 6 个 NB 重放，2 worker） | 1380 | 3588 | 114816 | 3588 | 0 |

GPU ≤2 设备小时，产物 ≤12 GiB；张量留服务器。预检工程失败可记账后重试一次；正式不重试。

## 5. 工程闸门

输入 = qc_make_inputs(NQ 输入) 且通过结构检查；token 审计逐项一致；校准为 NQ-01 原值（哈希）；NQ-01 runner 的全部闸门（窗口 token、窗口前缓存共享、写入 ≤1%、通道块来源、S/KV/浅层 = T、C ≠ T、供体不变、诊断 = 自然第二步、预检重建）；**NB 重放**：每个重放输入 13 条轨迹的 token、首步哈希、缓存哈希、诊断与 NQ-01 正式记录逐位相同。

## 6. 出口与交付

按计划 §7；不扫层、不重开 45 头、不扩模型/剂量/长度。交付 `data/`、`runs/{preflight,formal}-r01/`（记录入 Git，张量在服务器）、`analysis/qc-readouts-r01.json`、`REPORT.zh-CN.md`。
