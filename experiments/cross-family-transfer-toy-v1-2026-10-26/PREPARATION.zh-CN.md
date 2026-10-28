# 跨家族迁移准备回执

**最新状态：2026-10-26 15:02 北京时间已完成 GPU Ready。** 资产、CPU 测试和216个冻结输入均已校验；本次正式 GPU 实验未启动。完整交付见 [GPU Ready 结果](GPU_READY.zh-CN.md)。下文保留14:28时的历史准备记录。

记录时间：2026-10-26 14:28 北京时间。状态为 **代码与 CPU 预检已完成，官方权重下载中，尚未 GPU Ready**。

## 已验证

- 用户单独保存的 Hugging Face 下载凭据对应 `RuizhiXu`，已通过指定模型的官方访问检查。旧账号的拒绝记录保留；凭据在仓库外，不写入日志或 Git。
- 目标固定为 `meta-llama/Llama-3.1-8B-Instruct@0e9e39f249a16976918f6564b8830bc894c89659`，没有替换为已有的 Llama 3.0。
- 两阶段代码、[实验设计](PROTOCOL.zh-CN.md)、[合同](CONTRACT.zh-CN.md)与[执行说明](EXECUTION.zh-CN.md)已写好。阶段二由阶段一的机器评分及绑定证据决定是否开放。
- 合成输入测试、CPU 微型随机 LLaMA 集成测试、阶段门负例测试已通过。它们验证实现，不是正式模型的实验结果。
- 真实 tokenizer 检查通过：320 份映射文档、11,777 个共同文字前缀位置；固定 Benchmark 输入未要求截断。详见 `validation-tokenizer-r01/receipt.json`。
- HumanEval 沙箱 5 项控制测试通过，59 个正式评分 task 离线加载成功，CPU 检查耗时 5.92 秒。详见 `validation-scoring-r01/receipt.json`。

## 当前下载

截至 14:28，已取得约 4.87 / 16.06 GB，约 30.4%；4 个权重分片中 1 个已完整校验。根据当时最慢分片的实际速度，传输还需约 37 分钟。该估计不含完整文件哈希和最终 CPU 准备检查，也不是时间保证。

下载已转入独立后台续传，保留全部已有 partial 和失败/测速记录。当前权威进度是服务器 `assets/download-r02/progress.json`，完成证据应为同目录 `receipt.json` 的 `all_files_verified`；`download-r01` 是历史尝试。服务器权重目录是 `/workspace/models/Llama-3.1-8B-Instruct-0e9e39f2`。

## 后续完成条件

下载完成后按执行说明运行 CPU-only `readiness.py`，首次正式准备目录为 `runs/llama31-r01`。重新核对完整源/目标资产哈希、全部代码与输入、tokenizer、评分和沙箱。只有 `GPU_READY.json` 明确为 `GPU_READY` 且 `freeze.json` 对应，才向用户报告 GPU Ready。此前的 `validation-cpu-r02/GPU_READY.json` 保留的是资产未齐时的准备状态，不能作为完成凭证。

本聊天定时跟进已更新为下载及 GPU Ready 准备，每 30 分钟检查，交付完成后暂停。不恢复此前已经完成的 9B/2B 队列。尚未授权启动本次正式 GPU 实验；准备期间不调用 `pipeline.py --execute`，也不干扰其他聊天在服务器上的工作。
