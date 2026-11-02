# 合同 r01（草案，未冻结）：跨模型实验 B——自然生成的撤针与同文本重建

日期：2026-11-02。依据：[PLAN r3](../../docs/cross-model-foundation-v1-2026-11-02/PLAN.zh-CN.md) §6、§7、§9.1–§9.3。模型身份、环境、面板、取层、针、写入定义与实验 A 合同 §1–§3 完全相同，见 [A 合同](../cross-model-history-current-v1-2026-11-02/CONTRACT.zh-CN.md)。

**状态：草案 r02。** 分叉定义已按 2026-11-02 讨论改为"答案前边界"（§2、§4，DECISIONS D5-r）；这偏离 PLAN r3 §6 的固定 k=4/16，**PLAN §6 需计划所有者相应修订后才能冻结**。r02 代码只编译与 CPU 测试通过，尚未上卡执行。冻结条件同 A 合同。本文件不构成正式采集授权。

## 1. 输入与指令

B 用面板中每情景一个平衡事实版本。指令（主/锁定）：`First give the record identifier, then the answer, in the form: <identifier>: <answer>.` / `Start with the entry identifier, then give the answer, formatted as <identifier>: <answer>.` 记录标识为 `R1…R7`（主）或 `E1…E7`（锁定）。

## 2. 源与分叉

- 源运行：记录块 token、q、以及每个实际处理的生成 token 都注入；最多 80 个生成 token；贪心；停止不屏蔽。
- **答案前边界（r02）**：源生成过程中，当已选出的生成 token 1…k_b 解码后的文本首次恰好以"记录标识 + 冒号"结束（正则 `^\s*<?\s*[RE]\d+\s*>?\s*:\s*$`，标识字母随分割；允许尖括号与尾随空格），第 k_b 个 token（含冒号）即为 pending：已选出、尚未送入模型；缓存覆盖提示与生成 1…k_b−1。k_b 由解码文本决定，各模型 token 数可不同，边界含义相同。四分词器下标准答案 `Rn: v` 与 `<Rn>: v` 都存在这样的边界 token（`validate_panel.py`）。
- **停针从哪次前向开始**：CONT 处理 pending（冒号）的前向仍带针；WITHDRAW 与 REBUILD 处理 pending 的前向起无针。因此第一个答案 token 在 CONT 中由带针前向选出，在 WITHDRAW/REBUILD 中由无针前向选出。
- 可达：pending 之前无停止 token，且 80 token 预算内出现边界；否则记"不可达"及原因（stop_before_boundary / no_boundary_within_budget），不补生成、不删样本、不换针。格式不符（先说答案再说标识等）也归入不可达，原文保留。
- 三臂：CONT = 源截到 k_b+64；WITHDRAW = 分叉快照，自 pending 起无针，最多再续 64；REBUILD = 全新空缓存一次性无针 prefill（提示 + 生成 1…k_b−1），再无针处理 pending，最多续 64；REBUILD 在无任何挂钩的状态下运行。CLEAN = 独立无针生成 80，另记其边界位置。
- 原 PLAN r3 的固定 k=4/16 协议不作主比较；F1 预检 r01 的 k=4/16 记录保留为历史。

## 3. 终点与解析

机械解析 `panel.parse_b`：在回答中查找被问列的全部取值（词边界、不跨连字符）与记录标识。类别：correct（只出现正确值且首个标识为目标行）、value_right_id_missing / value_right_id_wrong、wrong_value、conflict（正确值与其他值同时出现，记 unscorable，按 PLAN §9.1 最坏界处理）、no_answer（含立即停止）。交付 = correct。主读数 W−R 与汇总、四档判读、δ=0.10 按 PLAN §9 不变。

## 4. 为什么改分叉（D5-r）

预检 r01：四模型回答都是 4–7 token 的短答；k=16 四模型均 0/24 可达，k=4 的 pending 常已是答案值，撤针发生在答案选定之后，"正确交付"测不到撤针的作用。改为答案前边界后，撤针恰在第一个答案 token 被选出之前；不为凑 token 数拉长回答。这一修改在任何正式 B 结果可见前做出。

## 5. 工程闸门

同 A 合同 G1–G7、G10、G11，另加：

| 编号 | 检查 | 判据 |
|---|---|---|
| G12 | 分叉边界 | pending 等于源的第 k_b 个 token；快照缓存长度 = 提示 + k_b−1（缓存对象报告长度时核对）；pending 解码文本登记 |
| G13 | 无针 prefill 重建对无针增量 | 不要求逐位；首个答案 token 一致、其后 8 步贪心一致；报告首个答案 token 的对数概率差与 top1−top2 间隔（离翻转多远）、logit 最大差 |
| G14 | 新进程从分叉快照续写 WITHDRAW | 首步与逐步 logits 逐位相等、token 相等 |

## 6. 深记录

PLAN §7.2–§7.3：96 源，答案前边界处的分叉快照（源与重建各一）与自 pending 起前 8 个实际处理 token 的局部轨迹；CONT 的前 8 步从源轨迹切片。只有一个分叉点，B 深记录按 r01 实测约 12 GB（两个 k 时约 25 GB），r02 预检后按最长轨迹重算。
