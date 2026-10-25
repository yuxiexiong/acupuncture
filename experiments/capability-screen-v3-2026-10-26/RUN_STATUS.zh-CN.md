# 本轮启动与初步 ETA

2026-10-26 北京时间 04:49:13 已启动两个 GPU worker（1375855、1375856）与 CPU 收尾（1375857）。任务为 MMLU 1,000、ARC-C 200、GSM8K 100、HumanEval 100；共 1,400 对、2,800 个条件单元。

已冻结独立抽样与复用清单。718 对 MMLU 与旧记录完全一致，可复用；其余 682 对新计算。数学和代码分别在两张卡上先执行，随后交换分片，最后完成选择题。原模型、干预、精度、停止规则和生成上限未改。

04:53:06 核对两 worker 均存活，数学完成 15 对、代码 8 对，平均配对耗时分别 13.64 秒、20.07 秒。代码已有长度上限回答，另有一题仍在生成。初步规划整轮约 40–60 分钟，含选择题、CPU 沙箱和评分余量；这是少量实测后的估计，不是保证或统计置信区间。原始时点与数值见 `validation/eta-initial.json`，后续以实时回执为准。

旧全量于 04:43 停止，10,034 对完整 MMLU 和部分记录保留。旧运行没有全量成绩；新运行也尚未产生最终成绩。复用的历史计算时间与本次启动后的墙钟时间分开，不能将本次速度称为从零计算全部 1,400 对的速度。

启动依据：`launch.json`、`protocol.json`、`panel_manifest.json`、`reuse_manifest.json`、`validation/deployment.json`。后台任务状态：`worker-0.json`、`worker-1.json`、`outputs/*/receipt.json`。CPU 收尾：`finish-r01/receipt.json`；最终成绩预计保存至 `finish-r01/scores/summary.json`，逐题评分为同目录 `scores.jsonl`，代码执行证据为 `finish-r01/humaneval-execution.jsonl`。这些最终文件尚未生成，不能把等待回执视为完成。

每半小时巡检已切换至本轮。不得重启旧全量，不重复启动新收尾，不因到一小时而删题、截短一方回答或把基础设施失败计成答错。
