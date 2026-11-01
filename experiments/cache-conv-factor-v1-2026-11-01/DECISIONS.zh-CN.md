# CFM-CONV-FACTOR v1 决策日志

- **D1 随机抽样张量的排列（冻结前补定）**：方案写“每层每旧槽每头的128维随机向量”。实现为每个 G 层（升序）一次抽 [4 槽, 头数, 128] 的 float64 标准正态，按（槽,头）单位化。种子与方案相同；方案没有规定排列，这里冻结以保证可复现。
- **D2 “实际读取的槽”（冻结前核实）**：方案写“最近3槽”。对冻结安装的 `causal_conv1d_update` 核实：拼接 [旧 4 槽, 当前] 后做宽度 4 的卷积，只取最后输出，读取槽 1、2、3 与当前 token，槽 0 不参与。CPU 测试 `test_real_update_reads_slots_1_to_3` 用真实函数验证。5% 幅度门槛按槽 1–3 计算。
- **D3 预检 4 次等价检查的内容（冻结前补定）**：design.json 列出 M:TTT/N:TT 的记录器关闭与“整段组装”。整段组装 = 直接复制 T 的整份 conv_states，不经分段拼接；同时核对两种组装的张量哈希一致。N 的两次用入口钩子 + 直接前向（冻结的 `form_ab.score` 要求零钩子，同 LOCAL-READOUT D4）。
- **D4 模板前向**：沿用 LOCAL-READOUT D1，每 worker 一次 1-token 前向取缓存对象，全部张量随后被覆盖并逐字段核对。
- **D5 内核计数**：新增只读 Counter，同时包装 recurrent 与 chunk 两个内核函数，每格核对 14 个 G 层各命中 1 次、chunk 0 次；并读取各 G 层门控归一化输出与 out_proj 输出（方案 §5.3），不改任何返回值。
- **D6 重构容差**：方案 §7.1-5 定 0.003。历史审计在同类 combo 格上测得最大 0.00266；若新格超界即为工程失败，按合同停止，不放宽。
- **D7 preflight-r01 合同执行失败（运行后登记）**：就绪脚本为 CPU 步骤 `export CUDA_VISIBLE_DEVICES=`，随后同一 shell 启动预检，worker 继承空设备列表，在加载模型时 `RuntimeError: No CUDA GPUs are available` 退出。0 次评分、0 次模板前向、0 次形成（收据 `runs/preflight-r01/worker-0/receipt.json`，13.7 s）。信息量为零，不是任何科学证据。代码未改；因本日志在冻结清单内，重新冻结为 freeze-r02，以新授权运行 preflight-r02，CPU 步骤改为单命令前缀设空设备、启动命令显式 `CUDA_VISIBLE_DEVICES=0,1`。预算不变（已消耗 0）。
