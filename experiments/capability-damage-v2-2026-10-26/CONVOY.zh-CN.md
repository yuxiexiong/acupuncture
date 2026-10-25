# 已授权的全量评测车队

用户于 2026-10-26 要求保留本轮全量运行，自动完成整条实验，并将人工式巡检改为每半小时一次。讨论未来是否需要全量，不改变本轮冻结协议。

1. 两个 GPU worker 各负责一半互不重叠的题目；每题都包含原版与 EVO。每条队列依次运行 MMLU → ARC-Challenge → HumanEval → GSM8K。实际 forward 均为 batch=1。
2. `finish_run.py` 已单独作为 CPU 收尾进程启动；等两个 worker 的四项任务全部成功，才执行固定的 HumanEval 隔离测试，再运行固定的官方评分器。它不加载模型、不改冻结代码，也不自动重试失败或覆盖结果。
3. 当前线程已设置每 30 分钟巡检，自动化 ID 为 `acupuncture`。巡检检查实际进程、完成数量和失败信息；全部评分完成后，核验完整性、归档原始证据、生成中文结果报告并提交到项目 GitHub，然后结束巡检。

服务器根目录：`/workspace/acupuncture/experiments/capability-damage-v2-2026-10-26`。

| 材料 | 路径 |
|---|---|
| 冻结推理配置 | `protocol.json` |
| GPU 总状态 | `worker-0.json`、`worker-1.json` |
| 各任务原始结果与运行收据 | `outputs/<任务>-shard<0或1>-r01/` |
| CPU 收尾启动与测试证明 | `finish-launch.json`、`validation/finish-supervisor-start.json` |
| CPU 收尾状态 | `finish-r01/receipt.json` |
| HumanEval 执行证据 | `finish-r01/humaneval-execution.jsonl` 及其收据 |
| 完成后总分与逐题评分 | `finish-r01/scores/summary.json`、`scores.jsonl` |

CPU 队列内部每分钟检查前置任务是否完成；这是自动任务衔接，不是每分钟唤醒助手或发进度消息。助手巡检保持每半小时一次。状态为 `waiting` 或 `started` 不表示实验完成；只有完整推理、执行测试和评分收据全部成功，才发布正式成绩。
