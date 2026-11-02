# QKD-01 设计附件（未运行）

[实验计划](../../docs/cache-k-computation-diagnostic-plan-v1-2026-11-03.zh-CN.md) · [作者自查](../../docs/cache-qkd-self-check-v1-2026-11-03.zh-CN.md)

`design-manifest.json`固定48输入、六臂、四方向、来源哈希和完整计数；`delivery-check.json`记录本轮CPU交付检查，不能当模型验收。预算1.50设备小时为拟封顶，不是授权。没有新模型运行器或authorization文件。

可复核：在本目录运行 `python3 check_design.py`；仅用标准库核对来源、预算及300组合成矩阵恒等式，不加载模型。
