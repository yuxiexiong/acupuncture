# 本地运行与工程验收快照

2026-11-04归档。来源为主工作区的`external/`，保存到本实验目录下的同名子树；逐文件捕获时间、原路径、大小与哈希见[导入清单](../../../migration/2026-11-04-evidence-archive-r01/local-import.json)。这是分文件读取的快照，不是正在运行队列的原子备份，恢复执行须由运行所有者按原账本处理。

- `wsp-fleet-acceptance-r1`至`r5`、transport/remote-acceptance属于调度、断线恢复及适配验收，包含合成fixture。里面的成功分数不能当模型研究结果。
- `wcp01`为编辑器桥接与工程日志；`wcp01-observer`为数据筛选材料。原始MBPP下载仅登记哈希，来源见WCP原来源清单。
- `wsp-fleet-v1`保留失败的第一队列和0.8B数学原会话。恢复工作流记载第一pass完成，但后续编辑器调用被拒绝；是工程阻断，不是完成或科学阴性。
- `wsp-fleet-v2/state.json`本次捕获时：0.8B数学`skipped_engineering`，4B数学`running`。编程两项尚无本次正式完成记录。不能从旧`acceptance`夹具的`completed`推断真实四项完成。
- `.lock`只登记哈希，不把锁重新激活；所有现有工作进程和原路径保持原状。本次没有启动、重试、中断或改变任何实验。

实际运行授权与恢复说明见[正式启动](../fleet-v1/runs/fleet-r1/README.zh-CN.md)、[断线恢复](../fleet-v1/runs/fleet-r2/README.zh-CN.md)。这些快照是归档证据，不是新的执行指令。

提交前追加：远端`2d2b728d`记录原样编辑器续接已获接受，0.8B恢复排到当前车队队尾；尚非第2 pass完成。见[后续恢复记录](../fleet-v1/runs/diagnostic-r1/README.zh-CN.md)。上述01:13快照保留原状，不冒充之后状态。
