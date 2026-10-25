# 冻结评测题目与来源

2026-10-26。本文记录 CPU 数据准备，**不是模型评分结果**。同一份题目用于原版与 EVO。

| 任务 | 正式题数 | 固定设置 | 最大提示 token | 最大提示加候选/生成预算 |
| --- | ---: | --- | ---: | ---: |
| MMLU | 14,042 | 5-shot；字母续写似然；官方按学科题数加权 | 3,138 | 3,139 |
| ARC-Challenge | 1,172 | 25-shot；完整选项似然；按裸选项 Unicode 字符数归一化 | 1,283 | 1,294 |
| GSM8K | 1,319 | 5-shot；greedy；最多 2,048 新 token；官方 strict/flexible filters | 1,602 | 3,650 |
| HumanEval | 164 | 原始函数补全；0-shot；greedy；最多 1,024 新 token | 407 | 1,431 |

共 16,697 题；另有 6 道不计分的技术开发题。开发题来自 MMLU/ARC validation 和 GSM8K train；生成开发题后重置 few-shot 随机种子，未改变正式题目。全部请求均未套聊天模板。种子为 `20261026`。

`prepare_tasks.py` 使用固定版 Harness 的实际 `ConfigurableTask`、采样器、`fewshot_context` 和 `construct_requests` 导出请求，没有重写提示模板。所有候选保存相同的公共 `context`；`continuations` 保留官方前置分隔符，`choices` 保留供 ARC 归一化使用的裸选项。`doc`、`target` 只供评分，不能拼入当前题的公共校准提示。GSM8K 标记旧快速评测已暴露 100 题、未暴露 1,219 题。

## 固定来源与验证

- LM Evaluation Harness：`d6de81643928d653435c431bae19945d41d32520`。70 个准备过程使用的源码/配置文件哈希与同 commit 的干净上游副本一致，见 `harness-source-verification.json`。
- 三份 HF 数据 revision、逐任务配置、各 split 内容摘要、实际依赖版本及正式 JSONL 摘要均在 `task_manifest.json`。
- `source_expected_files.json` 保存从官方 Hugging Face 固定 revision API 取得的文件/LFS 元数据。远端使用同 revision 的镜像下载，179 个选定 parquet/README 文件全部通过官方 SHA-256 核验，见 `dataset-source-verification.json`。
- HumanEval：官方 `openai/human-eval` commit `b9453e8f1865df0a0057a1383767caa400acfbcf`。数据 gzip 与该 commit 的 Git blob 逐字节一致，见 `humaneval-data-source-verification.json`。
- `validation/token_length_audit.json` 及逐题 `token_lengths.jsonl` 使用实际本地 tokenizer 和引擎的编码函数，确认全部正式/开发请求无需截断；未加载模型权重。

首轮直连 HF 无法访问，118 秒后停止本任务自己的 CPU 进程，保留 r01 日志。固定版本镜像路线 r02 用时 279 秒并成功。r03 在离线缓存上用时 106 秒，全部题目、开发题和清单逐字节重建一致。完整运行状态与摘要见 `task-preparation-receipt.json`。

首次长度审计发现 MMLU `mmlu_management:39` 含合法 U+0085 字符，`str.splitlines()` 会错误拆分 JSON 字符串。冻结数据未改；读取改为真正的 JSONL 换行后审计通过。失败源码和日志保留在 `validation/token-length-audit-r01.*`。后续读取应使用文件逐行迭代，或仅按 `\n` 切分。

## 无损归档与恢复

服务器保留 `items/*.jsonl` 原文件供执行。仓库以 `items/*.jsonl.gz` 保存相同内容；`compressed-asset-manifest.json` 同时记录压缩文件及解压内容的 SHA-256，总压缩大小约 7.4 MB。`task_manifest.json` 继续指向原始 JSONL 名称及摘要。以下命令在本目录执行，恢复时拒绝覆盖不同内容：

```python
import gzip, hashlib, json
from pathlib import Path

manifest = json.loads(Path("compressed-asset-manifest.json").read_text())
for info in manifest["files"].values():
    archive = Path(info["file"])
    packed = archive.read_bytes()
    assert hashlib.sha256(packed).hexdigest() == info["sha256"]
    raw = gzip.decompress(packed)
    assert hashlib.sha256(raw).hexdigest() == info["uncompressed_sha256"]
    output = archive.with_suffix("")
    if output.exists():
        assert output.read_bytes() == raw
    else:
        output.write_bytes(raw)
```

模型、虚拟环境、上游仓库和数据缓存仍在外部；不随本目录进入 Git。`run_prepare_r0*.sh` 保留本次服务器的实际参数和路径，跨机器重建时需明确替换这些外部资产位置。
