# 缓存形成机制｜CFM-S1｜原始轨迹与状态形成分析

计划：[`docs/cache-formation-mechanism-s1-native-trace-plan-v1-2026-10-31.zh-CN.md`](../../docs/cache-formation-mechanism-s1-native-trace-plan-v1-2026-10-31.zh-CN.md)（编号 `CFM-S1-v1-20261031`）。

- 合同：[CONTRACT.zh-CN.md](CONTRACT.zh-CN.md)
- 实现与决策日志：[IMPLEMENTATION.zh-CN.md](IMPLEMENTATION.zh-CN.md)
- 冻结：`freeze-r01.json`；授权与测试：`readiness/`；运行：`runs/`；离线记账：`analysis/`
- 结果报告：`REPORT.zh-CN.md`（运行完成后）

张量文件（`runs/*/worker-*/tensors/*.pt`）体积大，不进 git；它们留在服务器 `/workspace/acupuncture/experiments/<本目录>/runs/`，并打包到 `/workspace/cfm-s1-ops/archive/`。每个张量文件的 sha256 记在对应记录和 worker 收据里。
