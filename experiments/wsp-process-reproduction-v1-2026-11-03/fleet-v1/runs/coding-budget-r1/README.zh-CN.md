# 0.8B 编程预算续接记录

用户于 2026-11-04 明确批准“同意增加这 1 GPU 小时，原进度续跑”。本次仅将诊断 A 上限从 1800 调到 5400 GPU 秒、总上限从 14400 调到 18000 GPU 秒；数据、采样、干预、评分、源码哈希和其他资源上限不变。

## 已完成的恢复

- 原现场 `/workspace/acupuncture/external/wcp01/runs/fleet-v1-0p8b` 保留。首批 `D-original-000` 的 32 题 × 2 回答及账本记录复制到版本化续跑目录，逐文件 SHA 校验一致，不重算。
- 第二批 `D-original-032` 的进程已退出，未写出完整生成文件或结果。保留原失败，续跑时仅重做这一未完成批次及后续工作。
- 超时动作实测 787.916882 GPU 秒已补记。其未落盘样本数/token 数无法实测，保守按原预留上界 64 样本、1048576 输出 token 计入。旧异常路径没有记录失败 CPU 秒，不能声称为零；原 7200 秒历史 CPU 预算分配保留，实际失败 CPU 耗时仍未知。
- 新目录 `/workspace/acupuncture/external/wcp01/runs/fleet-v2-0p8b-budget-r1` 的累计 GPU 支出为 1800.105613 秒；诊断剩余 3599.894387 秒，总剩余 16199.894387 秒。预算余额不是完成 ETA。

## 自动续接与验收

北京时间 12:39 启动等待器，PID 62079。状态位于本地 `external/wsp-fleet-v2/coding-0p8b-budget-recovery/state.json`，日志在同目录 `launcher.log`。等待当前 0.8B 数学恢复完成、4B 编程有终态收据且进程退出后，调用现有 `fleet.coding_child` 续跑；不抢占现有任务。工程故障保留现场再修复。

12:40 核对：等待器存活，数学 running，4B 编程 active；服务器新目录仅有已复制的 `D-original-000`，没有新增 GPU 动作。7 项 CPU 检查通过，覆盖队列门禁、配置仅授权差异、失败 GPU 计费；详见 `verification.json`。诊断剩余三批按首批约 13.5 分钟估计生成约 40 分钟，尚不含编辑器、定位和排队时间，不作为全实验 ETA。

`prepare_resume.py` 已执行一次，不可重复执行；`resume_when_idle.py` 有单实例锁和已有状态拒绝重启检查。`runtime.json` 的 spent 是原始启动种子，实际续跑用已有 SQLite 账本的累计 spent，详见 `continuation-receipt.json`。不得删除账本再初始化。

本次是已授权预算与工程恢复，尚无新科学结果；不能将原 skipped_engineering 或本等待器启动视为实验完成。
