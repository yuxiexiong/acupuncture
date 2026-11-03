# 已授权缓存清理与环境复核

2026-11-03。用户授权清理上一份清单的前三项、保留所有原始实验数据/快照/日志/构建记录、核验环境并修订预算；明确不启动搜索。

## 执行结果

删除范围严格为 `/workspace/acupuncture/external/wsp/` 下五个目录：

- `forward-ckpt-cache/`
- `fa01-0p8b-r1/ckpt/`
- `fa01-0p8b-r2/ckpt/`
- `fa01-4b-r1/ckpt/`
- `uv-cache/`

删除阶段观测空闲增量 **44,109,910,016 bytes（约 44.11 GB）**；删除前 225.917 GB，删除后 **270.027 GB**。该数值是文件系统空闲变化，含目录元数据和可能的并发波动；先前按文件块/硬链接预计约 44.07 GB，两者一致到本任务所需精度。备份约占 68.74 MB，逐文件清单另占约 4.4 MB；相对最初检查时的净空闲增量约 44.04 GB。[执行收据](receipt.json)

旧 `text-Qwen3.5-4B`、当前两个文本模型、raw 模型、编译缓存、环境、其他项目目录均未删除。没有清理任何 `fa01-*` 整个 run，也没有触碰 `/workspace/acupuncture/experiments` 的科研数据。

## 保留与校验

执行前将 checkpoint 缓存内全部非权重文件以及缓存日志归档，共 **86 份文件**，含 **10 个构建记录**。每个归档文件的 SHA256 均与源文件核对；10 个构建记录指向的 snapshot manifest 和每个 `.npy` snapshot 的 SHA256 均核对通过。构建记录完整内容已交付：[build-records.json](build-records.json)，归档文件清单：[preserved-files.json](preserved-files.json)。

服务器保留目录：`/workspace/acupuncture/external/wsp/cleanup-r1-2026-11-03/`。

- `preserved-cache-records.tgz`：全部 86 份资料；SHA256 `2339dc7c27de8564af1f036f6a0dd6abec2701c1fa3f65079023c027ec4bd455`。
- `protected-before.json.gz`：161,321 个保留文件的清单。
- `selected-before.json.gz`：76,715 个删除候选文件的原始清单。

清理后立即比较保留清单：**缺失 0、变化 0**。核验范围含 WSP 非清理目录、`.venv-wsp` 和 4B raw 源文件；对记录、JSON/JSONL、日志、文本、NumPy/PyTorch 快照等计算内容哈希，对大模型/安装二进制记录 inode、大小、mtime、mode 等元数据。没有声称本轮重新逐字节扫描全部模型权重。安装环境硬链接数允许因移除缓存链接减少，环境中的 inode/文件内容仍在。

备份的大部分体积来自重复的上游 tokenizer/config，因此压缩包留在服务器，不将模型相关批量资产加入 Git；构建记录、清单与备份哈希已进仓库。原始实验数组、回答、日志和 snapshot 保持原路径，不需要从备份恢复。

## 清理后环境验收

[环境收据](environment-receipt.json)、[隔离内核原始输出](environment-kernel.json)：

- torch 2.14.0+cu130、vLLM 0.33.0、transformers 5.20.2，以及 NumPy/SciPy/sklearn/pandas/sympy/networkx/safetensors/tokenizers 均可导入。
- 0.8B 的 320 个 tensor、4B 的 426 个 tensor 可从 safetensors 打开；两个 tokenizer 可编码固定测试文本。
- 空闲 GPU 上仅做 `ones(2).sum()==2` 的 CUDA 环境检查，不加载推理模型。
- bubblewrap 隔离 CPU 内核启动、tokenizer API、变量跨调用持久化与空编辑目录检查通过。
- 既有 forward_service CPU 测试和 8 个 engineering unittest 全部通过。

**本轮模型前向 0 次，正式搜索 0 次。** 没有为检查环境重跑昂贵的 GPU 数值验收，也未额外调用 Astra。

## 预算变更

已同时更新本地与服务器的两份 server 模板，并核对哈希：[budget-verification.json](budget-verification.json)。

|项|0.8B|4B|
|---|---:|---:|
|设备时间停止线|8 GPU 小时|20 GPU 小时|
|单次 forward 限时|45 分钟|90 分钟|
|启动最低空闲|100 GB|150 GB|
|运行中保留空间|50 GB|50 GB|
|成功 pass|50|50|
|authorized|false|false|

两端拒绝启动检查通过，authorization_record 仍为空。详细依据与资源自查见[修订后的启动清单](../STARTUP.zh-CN.md)。这些是停止线与容量规划，不保证一定在预算内完成全部 50 pass；超限暂停报告，不能擅自追加预算或删除原始数据。清理完成不构成搜索授权。
