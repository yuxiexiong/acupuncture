# 002．旧全量能力评测与中途停止

[返回总时间线](../README.zh-CN.md)

**时间定位**：已提取运行收据的最早时间锚点（可含预检） 2026-10-26T03:34:32.989247+08:00；不能当作全部子运行起止。

**当时的目的与设计**

原计划用四项全量基准比较原版和双针版，继续检查最初观察到的任务损伤。

**实际过程、结果与后来更正**

这轮被用户停止。保留10034对完整MMLU及部分记录，其余三项未启动；本章保留停止收据和部分完成身份，不能将后来的固定小面板成绩补算成这轮全量完成。

**来源身份**：`capability-damage-v2-2026-10-26`；本章主体来源提交 `7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8`。下方原文中的状态是各文件写作时的状态，不能把早期“尚未运行”覆盖后期正式收据，也不能将后期结果倒填进早期设计。


## 原设计、执行过程、结果与更正全文

以下按“设计与题目 → 工程/执行记录 → 结果/更正 → 其他历史说明”组织；同类内没有可靠时间时保留路径顺序，不冒充严格先后。正文未删段；仅为本章节重排标题层级、把相对链接指向固定提交。原始字节另外完整保存。

### 原件 1：Acupuncture：调整前后能力损伤对照方案 v2

原路径：`docs/damage-evaluation-plan-v2.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/docs/damage-evaluation-plan-v2.zh-CN.md) · [单独阅读副本](../library/8209bab934d379dc.md)；SHA-256：`8209bab934d379dc338041a2f7c140a6c2609d63f175915c990293c3df16d885`。

---

#### Acupuncture：调整前后能力损伤对照方案 v2

2026-10-26 · `DESIGN_ONLY / NOT_RUN`。本版按用户要求收敛为能力损伤测量，替代 [v1](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/docs/damage-evaluation-plan-v1.zh-CN.md) 作为当前损伤评测方案；v1 原文和已有实验结果完整保留。本次只修订方案，没有启动新评测。

**后续执行记录：** 用户已另行授权本方案的四项全量原版/EVO对照，现已通过逐题技术验收并启动。[运行协议与证据](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/capability-damage-v2-2026-10-26/PROTOCOL.zh-CN.md)单独保存；本文原有设计时状态保留，不以启动代替完成成绩。

##### 1. 唯一目标

**量化同一个模型在调整前后，各项任务表现下降了多少。**

每项能力分别报告原版分数、调整后分数、下降百分点和配对置信区间。这里的“能力损伤”指固定评测条件下的任务表现下降，不代表全部知识消失，也不把不同任务平均成一个总损伤分。

##### 2. 比较对象：两个版本

| 版本 | 定义 |
| --- | --- |
| O：原版 | 固定版本的原模型，不施加调整 |
| M：调整版 | 在同一原模型上，施加一份事前固定的调整配置 |

当前对象为 `Qwen/Qwen3.5-4B`，revision `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`。待测配置沿用已有动态干预：零起始 L14/N8949 +1、L13/N7956 −1，在 `down_proj` 输入加偏移，覆盖 prefill 和 decode。逐题用原版公共提示的残差尺度校准，排除 padding、待评分的候选续写及本题目标答案；同题所有候选共用尺度。完整定义见 [v1 §4](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/docs/damage-evaluation-plan-v1.zh-CN.md#4-干预定义与比较单位)。

当前改的是推理时激活，权重未改写。后续若评估永久权重修改，单独记录修改内容和新检查点身份，再与其原版按本协议比较。本协议不执行新的参数搜索；每个已确定的调整方案只新增一个 M，不自动附加单点、剂量或随机位置矩阵。

##### 3. 能力面板：沿用四项直接任务指标

保留 v1 已选的四项英文文本任务，精简比较条件和辅助指标，不随意缩减原方案的能力覆盖。正式比较使用各任务完整测试集。

| 能力侧重 | 基准 / 题数 | 主分数 | 沿用的评测设置 |
| --- | --- | --- | --- |
| 多学科知识与判断 | MMLU / 14,042 | 选项正确率 `acc` | 5-shot，按固定任务定义计算字母续写似然，保留其学科聚合权重 |
| 科学知识与推理 | ARC-Challenge / 1,172 | 归一化选项正确率 `acc_norm` | 25-shot，按固定任务定义计算完整选项似然 |
| 数学推理 | GSM8K / 1,319 | 最终数值正确率 `strict-match` | 5-shot，greedy，每题最多 2,048 新 token |
| 代码能力 | HumanEval / 164 | 测试通过率 `pass@1` | 原始函数补全提示，0-shot、greedy，每题一份代码，最多 1,024 新 token |

MMLU、ARC-C、GSM8K 使用固定 commit 的 LM Evaluation Harness 任务和评分器；HumanEval 使用固定版本数据及执行器，每题执行超时 3 秒。沿用 v1 的标准文本补全模式，不额外套聊天模板或人格提示。准确版本、few-shot 示例、任务继承配置和停止条件在运行前冻结。任务来源与既有核查见 [v1 参考资料](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/docs/damage-evaluation-plan-v1.zh-CN.md#参考文献与实现来源)及[来源审计](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/docs/literature/source-and-damage-audit-2026-10-26.json)。

GSM8K 的主分数固定为严格提取；同时预先固定上游 `flexible-extract` 作为格式敏感性附注，两版同算、单独列出，不择高替代主分数。它可能误取叙述数字，不等于人工语义判分。HumanEval 直接测试原始 completion，不人工修复或挑选代码块；执行环境禁网、无凭据并限制资源。

##### 4. 损伤怎样计算

```text
S0 = 原版任务分数（%）
S1 = 调整后任务分数（%）
D  = S0 − S1（百分点）
```

例如 80% 变成 65%，记为下降 15 个百分点。`D<0` 表示改善，不能截为零。不再同时增加“相对损伤率”“能力保留率”等重复口径。

每项差值给出 95% 配对 bootstrap 区间：固定种子 `20261026`、重采样 10,000 次，同一次抽样取两版对应的题目；MMLU 在学科内重采样并保留原聚合权重，共用上下文按上下文聚类。区间只描述题目抽样的不确定性。若两版不一致题极少，区间可能退化，不能用零差值或 `[0,0]` 宣称完全无损。本版不做“无损”阈值判定或多条件显著性筛选。

最终主表固定为：

| 基准 | 计划 / 完成题数 | 原版 S0 | 调整后 S1 | 下降 D（百分点） | D 的 95% 配对区间 |
| --- | --- | --- | --- | --- | --- |
| MMLU | 待运行 | — | — | — | — |
| ARC-C | 待运行 | — | — | — | — |
| GSM8K | 待运行 | — | — | — | — |
| HumanEval | 待运行 | — | — | — | — |

仅附一张简短的失败说明表：两版的截断数、解析失败数，以及 HumanEval 的语法错误 / 执行超时 / 测试失败分类。它们用于解释分差，不组成另一套能力分数。

##### 5. 保证前后比较公平

1. **只改变指定调整。** 同题、同提示、同精度、同后端、同 batch 策略、同生成预算、同停止条件和评分器。当前沿用 BF16、eager、greedy；不单独给调整版增加重复惩罚、强制答案、重试或额外长度。
2. **运行前确认实现有效。** 固定小型非测试样本检查零剂量 / 卸载恢复、目标位置与偏移、候选共用校准尺度、batch / 单题、结束标记和解析。逐题重新初始化 KV / 递归状态。当前动态干预前后权重摘要应一致；未来静态修改则核验实际差分符合修改清单。
3. **固定题集与规则。** 技术开发题不进正式分母；调整配置在查看正式结果前冻结。历史 GSM8K 100 题标记为已暴露，全量分数之外单列未暴露部分，实际数量以内容去重为准。任何基于测试结果的后续调参，需用新的确认材料验证。
4. **所有正常产生的回答都计分。** 答错、拒答、无可解析答案留在分母；截断按已有内容和固定评分器判分，有合法正确答案仍可得分。OOM、崩溃等基础设施失败标为未完成，不冒充模型答错；NaN、hook 失效或零剂量异常先修复，不发布正式成绩。
5. **保存可复核证据。** 保留调整配置、模型 / 数据 / 代码版本、每题两版原文或选项似然、逐题评分、结束原因和全部失败尝试；已完成的回答不覆盖，不挑最好一次。记录实际耗时及完成状态。

##### 6. 执行范围与交付

每个条件共 16,697 题，O 与一个 M 共 **33,394 个题目—条件单元**。这不是 forward 次数或耗时估计。只有模型、题目及整套评测设置完全相同且证据完整时，才可复用已有 O；历史 100 题快速评测的模板和预算不同，不能直接作为本版原版分数。

执行顺序只有三步：冻结配置并完成小样本验收 → 两版完成同一面板 → 复算主表和失败说明。正式运行前实测吞吐并确定资源预算；没有实测数据时不给虚构 ETA。结果保存到新的 `experiments/` 运行目录，至少包含协议与版本清单、逐题原始记录 / 评分、主表和运行收据。

**从本版移出：** 三套 CE、BPB、专门的重复率面板、剂量曲线、A/B 分解与随机位置矩阵、机制定位、跨模型比较、有害性 / 人格评分，以及非劣和多条件显著性判定。这些不再是完成一次能力损伤对照的前提。

已有 [RACE / GSM8K / LogiQA 快速结果](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/qwen35-neuron-steering-2026-10-25/benchmark-quick-2026-10-26/RESULTS.zh-CN.md)保持原样。本次授权为精简方案和同步仓库；未启动新模型运行、静态修改或历史 Q25–Q40 采集。

---

### 原件 2：四项全量能力损伤对照

原路径：`experiments/capability-damage-v2-2026-10-26/PROTOCOL.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/capability-damage-v2-2026-10-26/PROTOCOL.zh-CN.md) · [单独阅读副本](../library/a02c6865ab5f98b6.md)；SHA-256：`a02c6865ab5f98b6b50abd8e67ef58b1bdeafa5262ca5f5dc9e6a1619e49dfb3`。

---

#### 四项全量能力损伤对照

本次运行依据 [精简方案 v2](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/docs/damage-evaluation-plan-v2.zh-CN.md)。用户已明确授权原版 Qwen3.5-4B 与 EVO 完成四项 benchmark，并报告各项原版分数、调整后分数和下降幅度。

##### 比较对象与口径

原模型固定为 `Qwen/Qwen3.5-4B@851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`。EVO 沿用动态激活干预：零起始 L14/N8949 +1、L13/N7956 −1，在各层 `down_proj` 输入加偏移，覆盖提示与生成。每题以原版公共提示的残差范数中位数校准，排除首 token、padding、候选续写及目标答案。权重不改写；关闭钩子后必须恢复原版行为。

| 基准 | 全量题数 | 设置 | 主分数 |
|---|---:|---|---|
| MMLU | 14,042 | 5-shot，字母续写似然 | acc，按学科题数加权 |
| ARC-Challenge | 1,172 | 25-shot，完整选项似然 | acc_norm，按选项字符数归一化 |
| GSM8K | 1,319 | 5-shot，greedy，最多 2,048 新 token | strict-match |
| HumanEval | 164 | 原始函数补全，0-shot，greedy，最多 1,024 新 token | pass@1，官方测试每份 3 秒 |

均采用上游标准文本补全提示，不套聊天模板；两版同题、同提示、同精度、同后端、同批处理策略、同预算与停止条件。原版和 EVO 在同一不可变模型实例上依次执行，每次调用新建状态。任务批次固定按提示 token 长度排序，两版执行顺序按批次交替。

`D = 原版分数 − EVO 分数`，单位为百分点；负值保留为改善。各项单独报告，不计算总能力分。95% 配对 bootstrap 固定种子 20261026、10,000 次；MMLU 保留学科权重。GSM8K 同时报告固定的上游 flexible-extract，但不能替代主分数；历史已暴露 100 题单独标记，另列未暴露 1,219 题。

##### 验收、执行与证据

正式推理前，冻结 `task_manifest.json` 的题目、提示、数据 revision、上游任务配置和哈希；`protocol.json` 冻结实际批处理大小、代码哈希及通过的验收收据。验收覆盖模型资产、零剂量、撤销恢复、单题与批量、候选共用尺度、似然位置、停止条件与评分器。只用非测试材料开发实现和测吞吐。

HumanEval 代码在禁网、非 root 的独立命名空间中执行，隐藏服务器工作区与凭据，限制 CPU、内存、文件和墙钟时间。正确代码、错误代码、语法错误、超时和隔离控制必须先通过，才执行原始模型 completion；不修复代码，不抽取“较好”的代码块。

正常答案全部进入分母，包括无答案、解析失败、截断和答错。基础设施失败保留为未完成，不能当成答错。每批保存两版原文或选项似然、校准量、token、停止原因与耗时；失败尝试保留，已完成回答不覆盖。评分复算检查所有 16,697 对、33,394 个题目—条件单元及对应身份和哈希。

此前三项各 100 题的快速测试使用不同提示与预算，不能复用其原版成绩作为本轮对照。本次没有授权或执行静态权重修改、位置/剂量搜索、历史 Q25–Q40 续跑或机制实验。

##### 准备过程记录

- 远端直连 GitHub TLS 失败，改为在本地取得固定 commit 后传输并核验 Git 身份；运行环境独立安装在 `/workspace/acupuncture/.venv-bench`，复用已有模型和 PyTorch。
- 远端直连 Hugging Face 不可达，首轮数据准备退出 143；使用镜像重新取得相同固定 revision，并与官方仓库文件哈希核验。下载线路不改变任务定义。
- 第一次 batch=64 合成验收未通过单题/批量一致性，不能作为正式评测实现。失败记录保留，修复与复验另存，正式运行仅接受通过的版本。
- HumanEval 沙箱 r01–r03 的配置排查与 r04–r05 的成功控制均保留在 `validation/humaneval-sandbox/`。这些是技术验收，不是模型成绩。

运行与得分状态以最终运行收据和结果报告为准；本文不把准备或验收计为完成四项评测。

---

### 原件 3：冻结评测题目与来源

原路径：`experiments/capability-damage-v2-2026-10-26/ASSETS.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/capability-damage-v2-2026-10-26/ASSETS.zh-CN.md) · [单独阅读副本](../library/884dfa806566cfad.md)；SHA-256：`884dfa806566cfad2648e5799fe54676274aa72126917b4fa87d068c60a83f3d`。

---

#### 冻结评测题目与来源

2026-10-26。本文记录 CPU 数据准备，**不是模型评分结果**。同一份题目用于原版与 EVO。

| 任务 | 正式题数 | 固定设置 | 最大提示 token | 最大提示加候选/生成预算 |
| --- | ---: | --- | ---: | ---: |
| MMLU | 14,042 | 5-shot；字母续写似然；官方按学科题数加权 | 3,138 | 3,139 |
| ARC-Challenge | 1,172 | 25-shot；完整选项似然；按裸选项 Unicode 字符数归一化 | 1,283 | 1,294 |
| GSM8K | 1,319 | 5-shot；greedy；最多 2,048 新 token；官方 strict/flexible filters | 1,602 | 3,650 |
| HumanEval | 164 | 原始函数补全；0-shot；greedy；最多 1,024 新 token | 407 | 1,431 |

共 16,697 题；另有 6 道不计分的技术开发题。开发题来自 MMLU/ARC validation 和 GSM8K train；生成开发题后重置 few-shot 随机种子，未改变正式题目。全部请求均未套聊天模板。种子为 `20261026`。

`prepare_tasks.py` 使用固定版 Harness 的实际 `ConfigurableTask`、采样器、`fewshot_context` 和 `construct_requests` 导出请求，没有重写提示模板。所有候选保存相同的公共 `context`；`continuations` 保留官方前置分隔符，`choices` 保留供 ARC 归一化使用的裸选项。`doc`、`target` 只供评分，不能拼入当前题的公共校准提示。GSM8K 标记旧快速评测已暴露 100 题、未暴露 1,219 题。

##### 固定来源与验证

- LM Evaluation Harness：`d6de81643928d653435c431bae19945d41d32520`。70 个准备过程使用的源码/配置文件哈希与同 commit 的干净上游副本一致，见 `harness-source-verification.json`。
- 三份 HF 数据 revision、逐任务配置、各 split 内容摘要、实际依赖版本及正式 JSONL 摘要均在 `task_manifest.json`。
- `source_expected_files.json` 保存从官方 Hugging Face 固定 revision API 取得的文件/LFS 元数据。远端使用同 revision 的镜像下载，179 个选定 parquet/README 文件全部通过官方 SHA-256 核验，见 `dataset-source-verification.json`。
- HumanEval：官方 `openai/human-eval` commit `b9453e8f1865df0a0057a1383767caa400acfbcf`。数据 gzip 与该 commit 的 Git blob 逐字节一致，见 `humaneval-data-source-verification.json`。
- `validation/token_length_audit.json` 及逐题 `token_lengths.jsonl` 使用实际本地 tokenizer 和引擎的编码函数，确认全部正式/开发请求无需截断；未加载模型权重。

首轮直连 HF 无法访问，118 秒后停止本任务自己的 CPU 进程，保留 r01 日志。固定版本镜像路线 r02 用时 279 秒并成功。r03 在离线缓存上用时 106 秒，全部题目、开发题和清单逐字节重建一致。完整运行状态与摘要见 `task-preparation-receipt.json`。

首次长度审计发现 MMLU `mmlu_management:39` 含合法 U+0085 字符，`str.splitlines()` 会错误拆分 JSON 字符串。冻结数据未改；读取改为真正的 JSONL 换行后审计通过。失败源码和日志保留在 `validation/token-length-audit-r01.*`。后续读取应使用文件逐行迭代，或仅按 `\n` 切分。

##### 无损归档与恢复

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

---

### 原件 4：已授权的全量评测车队

原路径：`experiments/capability-damage-v2-2026-10-26/CONVOY.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/capability-damage-v2-2026-10-26/CONVOY.zh-CN.md) · [单独阅读副本](../library/3dda2322782817a6.md)；SHA-256：`3dda2322782817a66eb8a163a17975e32bf8225f1eabf5b540d243e5e42143e5`。

---

#### 已授权的全量评测车队

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

---


## 时间、运行与停止收据索引

下面是所收集JSON的原有时间字段与状态，不把预计结束时间当实际完成时间。未列时间的文件仍有原件链接。完整JSON全部保存在原文归档，不能以此索引中的标量代替完整嵌套内容。

| 原件 | 原记录状态/阶段 | 原时间字段（原时区） |
|---|---|---|
| [dataset-source-verification.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/capability-damage-v2-2026-10-26/dataset-source-verification.json) | {"status": "all_pinned_dataset_source_bytes_verified_against_official_huggingface_metadata"} | {} |
| [finish-launch.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/capability-damage-v2-2026-10-26/finish-launch.json) | {"status": "launched"} | {"launched_utc": "2026-10-25T19:55:21.390919+00:00"} |
| [harness-source-verification.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/capability-damage-v2-2026-10-26/harness-source-verification.json) | {"status": "passed"} | {} |
| [humaneval-data-source-verification.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/capability-damage-v2-2026-10-26/humaneval-data-source-verification.json) | {} | {} |
| [task-preparation-receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/capability-damage-v2-2026-10-26/task-preparation-receipt.json) | {"status": "task_assets_ready_not_model_results"} | {} |
| [user-stop-20261026-r01/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/capability-damage-v2-2026-10-26/user-stop-20261026-r01/receipt.json) | {"status": "stopped_by_user"} | {"started_utc": "2026-10-25T20:43:07.155356+00:00", "ended_utc": "2026-10-25T20:43:15.066225+00:00"} |
| [validation/early_mmlu_audit-r01.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/capability-damage-v2-2026-10-26/validation/early_mmlu_audit-r01.json) | {"status": "failed", "scope": "First three completed MMLU pairs per shard; no score interpretation or GPU inference"} | {"started_utc": "2026-10-25T19:42:11.565831+00:00", "ended_utc": "2026-10-25T19:42:11.907443+00:00"} |
| [validation/early_mmlu_audit-r02.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/capability-damage-v2-2026-10-26/validation/early_mmlu_audit-r02.json) | {"status": "completed", "scope": "First three completed MMLU pairs per shard; no score interpretation or GPU inference"} | {"started_utc": "2026-10-25T19:42:40.482351+00:00", "ended_utc": "2026-10-25T19:42:45.437190+00:00"} |
| [validation/humaneval-sandbox/self-test-r04.jsonl.receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/capability-damage-v2-2026-10-26/validation/humaneval-sandbox/self-test-r04.jsonl.receipt.json) | {"status": "completed"} | {"created_utc": "2026-10-25T19:26:45.136308+00:00"} |
| [validation/humaneval-sandbox/self-test-r05.jsonl.receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/capability-damage-v2-2026-10-26/validation/humaneval-sandbox/self-test-r05.jsonl.receipt.json) | {"status": "completed"} | {"created_utc": "2026-10-25T19:27:25.945804+00:00"} |
| [validation/preflight-gpu0-b1-r01/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/capability-damage-v2-2026-10-26/validation/preflight-gpu0-b1-r01/receipt.json) | {"status": "completed"} | {"started_utc": "2026-10-25T19:34:33.097744+00:00", "ended_utc": "2026-10-25T19:35:01.552091+00:00"} |
| [validation/preflight-gpu1-b1-r01/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/capability-damage-v2-2026-10-26/validation/preflight-gpu1-b1-r01/receipt.json) | {"status": "completed"} | {"started_utc": "2026-10-25T19:34:32.989247+00:00", "ended_utc": "2026-10-25T19:35:01.378583+00:00"} |
| [validation/token_length_audit.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/capability-damage-v2-2026-10-26/validation/token_length_audit.json) | {"status": "all_requests_fit_without_truncation"} | {} |

## 全部原始资产入口

本目录在固定提交下共有100个跟踪文件，包含代码、原回答、失败、收据和压缩证据；文件数不是样本数。[逐文件完整账本](../assets/002-capability-damage-v2-2026-10-26.tsv) · [原目录](https://github.com/yuxiexiong/acupuncture/tree/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/capability-damage-v2-2026-10-26)。未复制模型权重、环境或凭据。
