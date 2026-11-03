# 缓存形成机制｜CFM-S2｜同起点与逐步写入、旧状态处理检验 v3

计划：[`docs/cache-formation-mechanism-s2-formation-test-plan-v3-2026-10-31.zh-CN.md`](../../docs/cache-formation-mechanism-s2-formation-test-plan-v3-2026-10-31.zh-CN.md)（编号 `CFM-S2-v3-20261031`）；前置 [CFM-S1](../cache-formation-mechanism-s1-native-trace-v1-2026-10-31/)。

- 合同：[CONTRACT.zh-CN.md](CONTRACT.zh-CN.md)
- 实现与决策日志：[IMPLEMENTATION.zh-CN.md](IMPLEMENTATION.zh-CN.md)
- 结果报告：[REPORT.zh-CN.md](REPORT.zh-CN.md)
- 冻结：`freeze-r02.json`（`freeze-r01.json` 对应失败的 preflight-r01）；授权与测试：`readiness/`；运行：`runs/`；离线分析：`analysis/`

驱动量张量（`runs/*/worker-*/tensors/*.pt`）与完整缓存 Mτ（`runs/*/worker-*/mtau/*.pt`）不进 git，留在服务器 `/workspace/acupuncture/experiments/<本目录>/runs/` 并打包到 `/workspace/cfm-s2-ops/archive/`；每个文件的 sha256 记在记录与 worker 收据里。
