# WSP 双模型过程复现：工程准备与验收

**已授权清理完成｜2026-11-03：** [执行收据与环境复核](engineering-r2/cleanup-r1/README.zh-CN.md)：指定缓存清理释放约 44.11 GB，当前空闲约 270 GB；161,321 个保留文件无缺失或变化，构建资料已归档，环境检查通过。正式预算模板已同步为 8/20 GPU 小时、100/150 GB 启动空闲门槛、50 GB 保留线；两端 authorized=false，**仍未启动搜索**。本条及最新启动清单覆盖下方旧预算/缺口说明，旧检查点按其历史时间理解。


**工程收尾 r2｜2026-11-03：** 0.8B、4B 接口/合成编辑验收及 Astra→SSH→隔离内核→前向完整链路已通过；CPU 超时恢复、最终快照和 checkpoint 重建也已验证。[收尾报告与原始证据](engineering-r2/README.zh-CN.md)、[正式预算与启动清单](engineering-r2/STARTUP.zh-CN.md)。**两场正式搜索仍为 0/50，两端启动配置关闭。** 当前磁盘不足正式门槛，等待用户决定预算/存储与启动；下方为原工程检查点历史。


2026-11-03，第二个工程检查点。用户要求依次推进，并选择等现有任务结束后使用空闲 GPU。**正式自主搜索与最终评测均未启动。** 本页更新工程状态；旧计划和失败收据保留。

设计沿用 [v1 完整计划](../../docs/wsp-process-reproduction-v1-2026-11-03.zh-CN.md)、[v1 自查](../../docs/wsp-process-reproduction-self-check-v1-2026-11-03.zh-CN.md)及 [0.8B＋4B v2 增补](../../docs/wsp-process-reproduction-0p8b-4b-v2-2026-11-03.zh-CN.md)。工程检查不构成科学结果或完整运行器验收。

## 已有且已核验

| 项目 | 当前证据 |
|---|---|
| 编辑器 | 当前 ChatGPT 登录可调用 `gpt-6-astra/max`，返回指定标记。输入 6448、输出 29 tokens；[调用参数](receipts/editor-probe.invocation.json)、[原事件](receipts/editor-probe.events.jsonl) |
| 0.8B 原始文件 | 固定 revision `2fc06364715b967f1860aea9cf38778875588b17`，9 个正式文件完成哈希校验；[资产收据](receipts/r2/asset_receipt.json) |
| 4B 原始文件 | revision `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`，12 个正式文件当前哈希复验通过；[收据](receipts/4b-current-hash-receipt.json) |
| 文本权重 | 0.8B 320 个、4B 426 个文本张量逐张量字节相同，无权重编辑；排除视觉/MTP。[0.8B](receipts/r2/text-Qwen3.5-0.8B/text_export_receipt.json)、[4B r2](receipts/r2/text-Qwen3.5-4B-r2/text_export_receipt.json) |
| practice 与作者代码 | 固定作者提交 `4d09ba6d6a7e891dd8063974dfe81b3d78e3494f` 的 25 个选择文件均核验；包含 7469 GSM8K、7275 MATH、714 AIME 练习题，不含最终补丁 |
| 双模型初始提示 | 已在任何新搜索前冻结。0.8B 原样；4B 只改真实架构和 residual 索引范围。[清单](frozen-prompts/manifest.json)、[4B diff](frozen-prompts/4b-prompt.diff) |
| CPU 沙箱 | 独立 `.venv-wsp` 下双模型均通过隔离、持久变量、冻结权重和保存/撤销的有限测试；收据见 `receipts/r3/`。原型尚未集成外部执行硬超时与完整预算控制 |
| 候选快照 | `snapshot_edits.py` 对直接写入的 `.npy` 独立复验，拒绝冻结/未知张量、形状错误、非有限数、整张量倍乘、符号链接；快照不随源文件改写。合成 CPU 测试通过，尚未接入前向服务 |
| 数学评分 | 复用作者 `extract/score/math-verify`，5 个确定性案例通过。只排除未公开 `mcqa` 的导入；其缺失函数保持不可用。[评分收据](receipts/scorer-probe.json) |

编辑器可用性测试不证明作者的认证方式、剩余额度/费用、40 轮续接或完整上下文隔离。当前可沿 Codex CLI 使用 ChatGPT 登录；不能称作不使用远程服务或免费。

## 分词器身份：已发现并修正的工程问题

- 当前 Transformers 对原始多模态配置解析为 `Qwen3_5Tokenizer`，对初次文本导出却选择 `Qwen2Tokenizer`；两道短数学题 token 相同，**不足以证明完整分词一致**。区别包括 Unicode 组合标记的预分词规则。
- **4B** 使用新的 `text-Qwen3.5-4B-r2`，显式保留原始模型解析出的分词器类；序列化 backend 与 chat template 均完全相同，[完整检查](receipts/r2/tokenizer-4b-r2-probe.json)。旧导出及其短题收据保留为失败身份历史，不再作为当前 4B 输入。
- **0.8B** 按既定复现协议使用作者提供的文本配置和分词器配置，解析为 `Qwen2Tokenizer`。其权重来自官方 raw，但不能声称分词器等同于当前库加载 raw 多模态配置的默认行为。原 `tokenizer-0p8b-probe.json` 只证明两道短题，不是完整 raw backend 验收。所有 0.8B 工具须统一使用这个冻结的作者 profile，不能中途静默切换。

## 独立环境与 GPU 状态

服务器 Debian 10 / glibc 2.28，H20，系统驱动 535.161.08。旧 `.venv-bench`、系统驱动均未升级。新环境 `/workspace/acupuncture/.venv-wsp`：Python 3.11.15、torch 2.14.0+cu130、vLLM 0.33.0、Transformers 5.20.2。初次依赖完整清单及构建失败日志在 `receipts/r2/`，后续修正另存 `receipts/r3/`。

仅在 WSP 目录解包 NVIDIA CUDA forward compatibility 库；CUDA/BF16 基础操作及库导入通过，用时 8.96 秒，[收据](receipts/r2/runtime-import-probe.json)。这不是 Qwen 数值验收。

首次 0.8B 前向尝试在 FlashInfer 采样准备阶段失败，用时 **57.76 秒**，没有产生数学回答，[日志](receipts/r2/preflight-0p8b-r1.log)、[收据](receipts/r2/preflight-0p8b-r1/receipt.json)。随后发现未设置 `CUDA_HOME`，以及自动安装的 nvcc/crt/nvvm 13.4 与运行库 13.0 不匹配；按官方 `cuda-toolkit[nvcc]==13.0.3.0` 约束匹配 13.0.88 编译器。编译检查还暴露了 wheel 库目录与 FlashInfer 链接路径不一致；仅在 WSP 工具目录补充链接名与 `LIBRARY_PATH`。修正后采样内核于 CPU 上成功编译/加载（GPU 隐藏），[成功收据](receipts/r3/compile-sampling-r3.json)。编译失败与后续尝试单独留档，不覆盖首次失败。

`queue_gpu_probe.py` 只安排 **0.8B → 4B 合成题 smoke**：物理 GPU 1 连续两次（间隔 60 秒）无计算 PID、显存低于 128 MiB、利用率为 0 才启动；每模型硬限 600 秒（另有至多 15 秒退出宽限），等待上限 6 小时；0.8B 失败即停止。该空闲检查不是跨项目的原子 GPU 预约，启动前 probe 仍复查占用。不终止其他任务，不自动重试，不进入 50-pass 搜索。

队列已完成：**0.8B、4B 均通过加载和合成题生成 smoke**，进程墙钟分别 75.21、68.70 秒。各 1 次 32-token warmup 和 2 道至多 1024-token 短题；两题共输出 1360 / 1061 tokens，eager 小批吞吐 51.19 / 47.24 token/s。这些不是正式吞吐预测或数学评测成绩。[完整队列状态](receipts/r3/preflight-queue-r1/state.json)、[0.8B 原始输出](receipts/r3/preflight-queue-r1/0p8b/receipt.json)、[4B 原始输出](receipts/r3/preflight-queue-r1/4b/receipt.json)。启动时快照保留在 `receipts/r3/queue-state.json`。

通过 smoke 不代表长上下文、满逻辑批量、空编辑一致性或内部张量数值验收通过，不能由两题吞吐直接估计正式任务总成本。

## 尚需推进

**2026-11-03 更新：前向服务已重建，0.8B 与 4B 数值验收 FA-01 均 8/8 通过；详见 [交接页](HANDOFF-2026-11-03-fa01.zh-CN.md)。** 以下为当时的原始清单，第 1–2 项的前向服务部分已由 FA-01 完成；harness、编辑器接入、终验数据仍未完成。

1. 双模型 smoke 已完成。下一项是完整前向服务的实现与数值验收。每模型准备总预算仍为 v2 的至多 0.5 GPUh；每次失败和重试都计资源。将共享初始化及未精确计时诊断保守归给 0.8B 后，本阶段累计约 201.93 秒（0.8B）及 68.70 秒（4B），后续工程运行继续累加。
2. 原作者未公开 agent harness/forward 服务。需重建并验收 generation、teacher-forced、内部张量返回、同请求原版/候选配对、候选快照加载及空编辑一致性。当前只有 CPU 原型、快照校验和 smoke，**没有完整前向服务**。
3. 集成独立编辑器上下文、40 轮续接、外部 50 forward / 300 Python 账本、CPU 硬超时与回收、断点恢复和全过程记录。4B 不能看 0.8B 搜索结果，二者都不能看作者最终补丁/轨迹。
4. 完成有代表性的吞吐与内存验收后冻结正式 GPUh、编辑器和存储上限；当前短 smoke 不足以给可靠总价。完整终验为两模型四状态共 51584 回答，不能按参数量线性猜预算。
5. 终验数据、GPQA 获取授权与数据可用性、IFEval/多选评分链仍需准备；数学核心评分通过不代表十项评测全部可运行。

## 来源和实现差异

冻结提示来自 [作者实验 8](https://github.com/RikiyaT/lm_understand-logs/tree/4d09ba6d6a7e891dd8063974dfe81b3d78e3494f/exp8_math)，日志/提示遵循 [CC BY 4.0](https://github.com/RikiyaT/lm_understand-logs/blob/4d09ba6d6a7e891dd8063974dfe81b3d78e3494f/LICENSE)，Python 脚本为 MIT，题目保留各自许可。资产 URL、版本和哈希由 `upstream_manifest.json`、`model_manifest.json` 和收据记录；镜像资源只有与冻结哈希匹配才接受。

作者没有公开 validator 容差；本项目整张量倍乘检测使用 `rtol=1e-5, atol=1e-7`。当前 eager smoke 的批量、种子与上下文配置仅用于工程检查，不冒称作者完整推理后端设置。本文区分作者已公开代码、重建接口和仍未知细节。

外部模型、环境、缓存和 wheels 位于 `/workspace/acupuncture/external/wsp/` 或 `.venv-wsp`，不进 Git。没有复制或应用作者最终 MLP 修正；没有新的 WSP 效果或机制结论。
