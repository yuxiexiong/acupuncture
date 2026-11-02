# 合同 r01（草案，未冻结）：跨模型实验 B——自然生成的撤针与同文本重建

日期：2026-11-02。依据：[PLAN r3](../../docs/cross-model-foundation-v1-2026-11-02/PLAN.zh-CN.md) §6、§7、§9.1–§9.3。模型身份、环境、面板、取层、针、写入定义与实验 A 合同 §1–§3 完全相同，见 [A 合同](../cross-model-history-current-v1-2026-11-02/CONTRACT.zh-CN.md)。

**状态：草案，有一项阻塞冻结的设计问题（§4，DECISIONS D5）。** 冻结条件同 A 合同，另加 D5 裁决。本文件不构成正式采集授权。

## 1. 输入与指令

B 用面板中每情景一个平衡事实版本。指令（主/锁定）：`First give the record identifier, then the answer, in the form: <identifier>: <answer>.` / `Start with the entry identifier, then give the answer, formatted as <identifier>: <answer>.` 记录标识为 `R1…R7`（主）或 `E1…E7`（锁定）。

## 2. 源与分叉

- 源运行：记录块 token、q、以及每个实际处理的生成 token 都注入；最多 80 个生成 token；贪心；停止不屏蔽。
- 分叉 k∈{4,16}：第 k 个生成 token 已选出、尚未送入模型；此时缓存覆盖提示与生成 token 1…k−1。分叉快照在源运行中 deepcopy，不为每个 k 重跑源。
- 可达：生成 token 1…k 中无停止 token 且源长度 ≥k；否则记"不可达"及终止类型，不补生成、不删样本、不换针。
- 三臂：CONT = 源截到 k+64；WITHDRAW = 分叉快照，自 pending token 起无针，最多再续 64；REBUILD = 全新空缓存一次性无针 prefill（提示 + 生成 1…k−1），再无针处理 pending，最多续 64；REBUILD 在无任何挂钩的状态下运行。CLEAN = 独立无针生成 80。

## 3. 终点与解析

机械解析 `panel.parse_b`：在回答中查找被问列的全部取值（词边界、不跨连字符）与记录标识。类别：correct（只出现正确值且首个标识为目标行）、value_right_id_missing / value_right_id_wrong、wrong_value、conflict（正确值与其他值同时出现，记 unscorable，按 PLAN §9.1 最坏界处理）、no_answer（含立即停止）。交付 = correct。主读数 W−R 与汇总、四档判读、δ=0.10 按 PLAN §9 不变。

## 4. 阻塞冻结的设计问题（D5，待计划所有者裁决）

预检显示该指令下的回答只有约 4–7 个 token（如 `R6: scarlet` 后即停止）：

- k=16 在 Qwen3-4B 上 0/24 可达（其余模型见 PREFLIGHT 报告），按合同"不可达照实报告"，k=16 这一半主读数将整体为"不可判"；
- k=4 的 pending token 经常已经是答案值本身，撤针发生在答案选定之后，WITHDRAW 与 REBUILD 只比较答案之后的尾部。

这是任务形式与固定 k 的冲突，不是实现错误。本合同不自行改 k 或改指令；候选处理方式在 DECISIONS D5 列出，由计划所有者选定后再冻结。

## 5. 工程闸门

同 A 合同 G1–G7、G10、G11，另加：

| 编号 | 检查 | 判据 |
|---|---|---|
| G12 | 分叉边界 | pending 等于源的第 k 个 token；快照缓存覆盖长度 = 提示 + k−1 |
| G13 | 无针 prefill 重建对无针增量 | 不要求逐位；在 pending 处贪心后 8 步一致，报告 logit 最大差 |
| G14 | 新进程从分叉快照续写 WITHDRAW | 首步与逐步 logits 逐位相等、token 相等 |

## 6. 深记录

PLAN §7.2–§7.3：96 源，所有可达 k 的分叉快照（源与重建各一）与分叉后前 8 个实际处理 token 的局部轨迹；CONT 的前 8 步从源轨迹切片。预检实测字节数见 PREFLIGHT 报告。
