# NGU-01 实现一致性审查

2026-11-16，同一独立 Advisor。对照已审 PLAN，读取 ngu_hooks.py、ngu_run.py、ngu_analysis.py、test_ngu.py、cpu_accept.py，以及实际复用的 RCS hook/finish/load/计量和 WSB 来源冻结代码。未运行模型、GPU 或新实验，也未修改实现。

## 核对结论

核心实现保持已审估计对象，未发现需要改科学设计的问题：

- F 复用真实 FP32 rsqrt、输入 cast、γ、FP32 SiLU 和输出 cast 顺序；Δ_cur/ref 取已舍入端点的 FP64 差，重组后才 cast。自身门、零增量为局部身份验收，无额外模型轨迹。
- 新 hook 继承真实/影子 kernel，仅改 norm 返回值；真实 S2 提交、影子不写 cache、高层自由响应、t3 清除及异常清理仍受检查。未整门替换基底。
- z_ref 来自同配对另一背景旧原生 11，逐文件 hash；t1 的 J/native/state hash 与旧来源核对。11/01 四参考自然原文、候选/停止 logits、局部 hash 桥接，并核原生 x0/x1/z/inv/native 向量；无后验挑参考。
- G_H=H11−HX、G_C=CX−C11 正确，公共 01 用途关闭参照及端点恒等式正确。原 168 冲突对、接收者等权、六场景双对比同时区间不变；完整 D_tr、无效填补界、第三行及停止分类另报。分析只读 completed 且 exit=0 的 hash 匹配记录，不按前缀资格删样本。
- 单一输出授权、锁内复核全部既有尝试、失败监督时间兜底、失败 forward 计时、3 小时和 16 GiB 全 runs 监督、工程保守外推与正式门槛均保留。来源冻结绑定 CPU 回执及外部源码，未恢复旧计划。

## 发现的工程缺口 I1

初审版本在 t1 forward 成功后，只保存 snapshot/层 hash 的 JSON，再做 W.identical 与 J/native/state 身份断言。如果这些断言失败，当前 wh.states 实际张量未保存；first 的异常保存仅覆盖 forward 内部异常。建议在这组桥接断言异常时保存当前 states、records 和 snapshot 后重新抛出。成功路径继续引用旧 states，避免重复保存大缓存。这是失败现场完整性修复，不改变补丁、估计对象或运行范围。

## 验证深度与状态

已实读 readiness/cpu-local-r02.json：32 项测试通过，source_stable=true，model_forwards=0，CUDA 未初始化；该本地回执没有真实服务器 upstream 测试。作者报告服务器 32 项 CPU 测试通过，但本次初审时服务器回执尚未同步，不能冒称已独立核过。新修复后的源码须匹配最终 CPU 回执与 freeze。

I1 修复复核前保留该工程待办；其余已核范围没有阻断。用户本轮已授权实现、通过验收后上卡及按方案修 bug，不需要新增用户审批。本审查不代替真实设备端点/参考重放与工程资源门槛；尚无 NGU 科学结果可解释。

## I1 及最终来源局部复核

2026-11-16，I1 已修复并关闭。回读 first()：forward、snapshot、W.identical 以及 J/native/state 三项身份检查处于同一 try；任一异常均先保存当前 states、records、可用 snapshot，再抛出。成功仍引用旧状态文件，未改变科学条件或新增模型轨迹。

已实读 cpu-local-r03.json 与 cpu-server-r02.json：各 32 项通过、0 模型前向、CUDA 未初始化，测试期间源码稳定；二者 source_hashes 均匹配最终当前 NGU Python 文件。服务器回执 upstream_kernel_tested=true，实际核内测试通过。freeze-server-r02.json 绑定当前 NGU 源码，外部源码与 torch 版本和服务器 CPU 回执相同，记录 348 个 H 包、696 个门文件及新增核对的 696 个旧状态文件。代码对各资产 SHA 与原 receipt 逐项比较后生成冻结记录。本审查读取冻结清单及代码，未重新读取远程全部大张量。

**最终已审范围无遗留实现阻断。** 可在用户既有授权下进入工程验收；正式运行仍取决于原方案要求的设备身份、完整参考重放、数值与实际预算门槛。本复核没有放宽这些门槛，也没有预先判定科学结果。

## 工程 r01 预算阻断后的优化边界

实读 r01 verification/exit：退出码 0，监督耗时 210.086 秒，但保守正式投影 7534.045 秒超过 7200 秒，budget_gate=blocked。因此不能启动正式；实际工程短时不能替代原投影规则。本次未查看科学效应。

作者拟删除新 hook 中将被覆盖的旧 direct/scale 诊断，并复用已算 F 端点进行自门/零增量验收，属于可接受的纯工程优化方向。须保持 kernel/norm 端点配对、单调用、原生 F11 逐位桥接、真实 S2 未变且提交、记录及异常清理。身份验收应覆盖实际重组算术和实际返回分支，不能直接写 true 或用抽象 Δ−Δ=0 代替程序验证。优化后六臂与 r01 的 answer/t2/local patch 严格回放、原 RCS 参考桥接同时保留。r01 来源、耗时及输出继续计费，r02 仍执行原最大单位成本×1.25、时限和存储门槛。此处只核优化边界，尚未核优化后的源码或预言其预算一定通过。

### 优化源码局部复核

已回读优化后 ngu_hooks.py/ngu_run.py。replace_increment 的实际、自门和零增量路径共用同一 FP64 重组、输出 cast 及身份返回分支；四个 F 端点仍按原顺序算出。真实同门/零输入 CPU 测试仍在，设备端复用端点检查没有直接跳过重组函数。新 norm hook 保留 pending/单调用、kernel 输出配对、原生 F11 逐位相等、state2 未变、cache 真实提交及 norm_calls；删除的是随后被覆盖的旧诊断，不改变输出或状态。

工程重试读取唯一已完成 prior 的 hash 验证记录，对所有原配对六臂逐项比较完整 answer、t2 与各层 S1/S2/patch/native_norm 四项 hash；原 RCS 桥接继续执行，没有选择性只查成功条件。252 条轨迹均沿同一路径进入比较，无新增科学臂。已核 local-r04 回执通过、0 模型前向/CUDA 未初始化、源码身份匹配当前版本；旧源码快照存在。服务器 CPU 和新 freeze 在本次局部复核时尚待最终同步绑定。

**优化源码无已知阻断，可在服务器 CPU 与冻结绑定通过后执行仅剩的工程 r02。** 正式预算门槛仍需 r02 实测通过；本次没有读取科学效果，没有改变最大单位成本、1.25 系数、样本、生成长度或时限。
