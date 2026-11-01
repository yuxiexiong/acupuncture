# B4 决策日志

- **D1 三处 v3 澄清**（冻结前）：范围写死为非 FIX G 层值头；写明 M 臂的不对称性与只控制幅度；轴 A 以 ρ_K ≤ 0.8 为主读数、四档只作描述。
- **D2 影子预测先算后冻结**（冻结前）：从 B3 张量在 CPU 上计算，结果均值 0.93–1.00，写入 readiness/shadow-r01.json 并纳入 freeze。
- **D3 实现细节**：钳回 hook 先于 CF.Counter 注册，所以 Counter 记录的是 hook 之后的行；新增闸门检查两者逐位一致。out_proj 审计用 F.linear(pre)，并在 CC/CFIX 上检查它与模型实际 out_proj 输出逐位相同，才把它用作 M 的输出差审计基准。
- **D4 N 臂不挂 bridge Recorder**：B3 已证明记录器开/关逐位一致；本轮只需 logits、hook 记录和 Counter，T_native 仍挂 Recorder 以取得 x_T。
- **D5 M_nat 模板来源**：B3 正式张量中下一情景（P06→P01）的 g_CC − g_CFIX，按 receipt 核对哈希后读取。
