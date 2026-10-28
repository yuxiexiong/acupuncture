# 两阶段跨家族迁移：执行入口

本版仅准备代码、合同、资产与 CPU 校验。根因实验暂停；以下 GPU 命令只有获得运行授权以后才执行。精确目标为 `meta-llama/Llama-3.1-8B-Instruct@0e9e39f249a16976918f6564b8830bc894c89659`。源模型固定 `Qwen/Qwen3.5-4B@851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`。

## 1. 下载与准备

官方期望文件见 `assets/official-source-manifest.json`（目标）和 `assets/source-official-manifest.json`（源）。权重放在仓库外。源路径 `/data/models/Qwen3.5-4B-851bf6e`；目标计划路径 `/workspace/models/Llama-3.1-8B-Instruct-0e9e39f2`。

已有服务器账户 `sibozhu` 对指定仓库被拒，用户确认网页已授权的是 `RuizhiXu`。用户通过 `assets/save_hf_token.py` 隐藏输入并保存独立下载凭据，2026-10-26 官方账号和权重访问已核验通过，见 `assets/official-auth-ruizhixu-success-receipt.json`；没有替换旧账户，密钥不进入日志或 Git。当前后台续传见 `assets/asset-run-r02.json`，完成以 `assets/download-r02/receipt.json` 的完整官方哈希证据为准。临时传输通道保留 TLS 验证，凭据不发送给镜像。

在精确资产完成后，在服务器项目根目录执行 CPU 准备。输出目录必须全新；失败保留，修复后使用新目录：

```bash
CUDA_VISIBLE_DEVICES='' HF_HUB_OFFLINE=1 HF_DATASETS_OFFLINE=1 HF_HOME=/workspace/acupuncture/.cache/hf .venv-bench/bin/python -B experiments/cross-family-transfer-toy-v1-2026-10-26/readiness.py --output experiments/cross-family-transfer-toy-v1-2026-10-26/runs/llama31-r01
```

准备工具会运行合成测试和真正 CPU 微型随机 LLaMA 测试、核验原始数据及 128 份源校准记录、流式核对官方文件大小和哈希、检查跨 tokenizer 对齐、全部面板上下文长度、官方评分依赖和 HumanEval 隔离控制。不会加载实验模型权重，也不会运行 GPU。

`GPU_READY.json` 为 `GPU_READY` 且配套 `freeze.json` 有效，才表示具备提交实验的资产与代码条件。真实目标 GPU 预检仍将在未来运行的首批步骤执行。`CODE_READY_ASSET_BLOCKED` 表示代码测试通过但目标资产缺失；`PREPARATION_FAILED` 表示其他准备检查失败。这两种状态均不能启动 GPU。

## 2. 只查看计划

```bash
.venv-bench/bin/python experiments/cross-family-transfer-toy-v1-2026-10-26/pipeline.py --stage 1 --run experiments/cross-family-transfer-toy-v1-2026-10-26/runs/llama31-r01 --target /workspace/models/Llama-3.1-8B-Instruct-0e9e39f2
```

默认只打印命令，不创建队列、不启动子进程。

## 3. 未来获准后的 GPU 运行

在上面命令末尾显式加入 `--execute` 才会运行阶段一。运行器先重新核验资产和冻结输入，要求两张卡没有现存计算进程，然后按顺序执行：

1. GPU0 采集源 320 文档，GPU1 采集目标 320 文档及 128 对比输入；独立进程、实际 batch1。
2. CPU 拟合两层映射。任一层干净验证相对 MSE ≥1，记 `MAPPING_QUALITY_HOLD`，关闭后续 GPU 阶段。
3. 两卡分别在合成提示上做目标预检，核对零干预、恢复、打分和生成一致性。
4. 两卡完成本阶段 10 个 toy 条件，各含 64 行为场景与 64 能力诊断题。
5. 两卡完成固定主臂 `true_D_match` 与原版的 1,400 对能力 Benchmark。
6. 官方评分、HumanEval 沙箱、toy 导出及空白人工盲评包、阶段一判定。

只有 `stage1/gate.json` 为 `PASS`，且配对分数复算、映射质量、条件包与输入哈希全部一致，阶段二入口才开放。若已有授权覆盖两阶段，可按同一授权启动；本脚本不会自行后台启动第二阶段。

阶段二使用同一个已冻结 run、同一条件包，只将命令改为 `--stage 2 --execute`。它重新做目标预检，运行其余 9 个 toy 条件，再运行 `true_S_recipe` 与原版的完整 1,400 对 Benchmark。**本实现第二阶段重跑原版，不承诺缓存复用。** 最后采用相同的固定判定规则输出 `stage2/gate.json`，没有第三阶段。

## 4. 判定、故障与证据

每任务计算原版减干预版的正确率差，MMLU 保留总体科目权重；配对/同上下文聚类抽样 10,000 次，名义 98.75% 区间用于四任务 Bonferroni 调整（有限样本覆盖为近似）。任一任务损伤点估计 ≥5 个百分点、区间下界 >0 且不一致配对 >5，则 `PASS`。全部任务区间上界 <5 且均有 >5 不一致配对，记 `STOP_SMALL_EFFECT`。其余记 `INCONCLUSIVE_HOLD`。完整机器评分零技术失败是前提。

运行错误留下 `queue.json` 与子步骤失败收据，对外为 `TECHNICAL_HOLD`；不覆盖、不删除、不自动改科学设置重试。映射质量未过是 `MAPPING_QUALITY_HOLD`。每次修复保留代码/输入哈希和旧目录，使用单独版本的新运行。修复不允许绕过阶段门。

收据路径：`collection-source/receipt.json`、`collection-target/receipt.json`、`mapping/quality.json`、`stageN/preflight-{0,1}/receipt.json`、`stageN/toy/shard{0,1}/receipt.json`、`stageN/benchmark/shard-{0,1}/receipt.json`、`stageN/benchmark/finish-r01/`、`stageN/export-r01/`、`stageN/gate.json`。`PRIVATE` 标记文件不能交给盲评者。

读取运行状态以收据中的完成数、活动进程身份和输入哈希为依据。代码存在、GPU 空闲、队列创建均不是实验完成。人工行为盲评与机器能力结果分开交付，不能由能力下降自动判定“有害建议”或共同机制。

## 5. 计算量与 ETA

两阶段全部运行时，正式 Benchmark 为 5,600 个题目—条件单元；toy 为 1,216 次行为生成及 1,216 个选择题—条件单元。GSM8K 每输出最多 2,048 token、HumanEval 1,024、toy 行为 512；合计满生成预算 1,851,392 个新 token，另有上下文前向、选择题打分、模型加载、映射和评分成本。这不是墙钟保证上限。

初始每卡一个进程。跨家族尚无实测吞吐，当前不填 GPU ETA。未来报告根据已运行阶段实际时间和完成数外推，并把未测阶段作为独立速度场景；下载 ETA 单独报告。增加并发须先做本目标一致性验证，不能直接沿用 9B/2B 的验证结论。
