# 126．C任务的2B与8B规模复用

[返回总时间线](../README.zh-CN.md)

**时间定位**：版本/记录日期 2026-11-05；未从所选收据确定完整运行起止，不据目录名补写时刻。

**当时的目的与设计**

沿用C数据、绝对编辑预算和50轮合同，分别排队Qwen3-VL-2B与8B。

**实际过程、结果与后来更正**

11月5日18:35用户停止所有卡上实验：2B仅完成4/50，8B仍等下载；不能写两模型各50轮完成。停止收据在同批Gemma旧队列章也有原文，后续Gemma新授权不恢复这两个旧队列。

**来源身份**：`wsp-vlm-c-scale-v1-2026-11-05`；本章主体来源提交 `2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274`。下方原文中的状态是各文件写作时的状态，不能把早期“尚未运行”覆盖后期正式收据，也不能将后期结果倒填进早期设计。


## 原设计、执行过程、结果与更正全文

以下按“设计与题目 → 工程/执行记录 → 结果/更正 → 其他历史说明”组织；同类内没有可靠时间时保留路径顺序，不冒充严格先后。正文未删段；仅为本章节重排标题层级、把相对链接指向固定提交。原始字节另外完整保存。

### 原件 1：原始文档

原路径：`experiments/wsp-vlm-c-scale-v1-2026-11-05/RESEARCHER.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-c-scale-v1-2026-11-05/RESEARCHER.md) · [单独阅读副本](../library/c1ce04c7e05a3933.md)；SHA-256：`c1ce04c7e05a39338489e06cd775b544bad1cebc7e9dc60f24f5ec94dfbcafd5`。

---

You are the researcher. The human fixes task, evaluation, data access and costs.
You diagnose failures, choose measurements, select parameters, calculate edits and
revise your ideas using actual feedback. No layer, neuron ranking, or edit schedule
has been prescribed. No successful patch is required. You may stop with a negative
or inconclusive result. Explain your evidence, next action and expected observation
before exactly one fenced `python` or `forward` block. A plain final reply stops.

Python runs persistently on CPU in an isolated directory. NumPy is `np`.
`catalog()`, `NAMES`, `load_original(name)`, `load(name)`, `save_edit(name,array)`,
`drop_edit(name)`, `edited()` expose parameter inspection and staging.
You write the selection and modification algorithm yourself. No target-model
training or unmetered model execution is allowed. Disclose any labels/fitting used.
`EVIDENCE` contains only permitted development data; `ARTIFACTS` contains complete
tool feedback. Successful controls and failures are equally available. No sealed
confirmation data is accessible. Target-model prompts never receive gold labels.

`forward` JSON takes `op` and relevant fields:

- `status`: current, best, resource use. Start here or with `evidence`/`catalog`.
- `evidence`, optional `ids`: input, gold, prior raw answers; initial answers may
  be absent until original evaluation. Large results are paginated, not discarded.
- `image`, `request_id`, `kind` = `input` or `preview`: attaches a verified image
  to your next turn. You may request any allowed development example.
- `catalog`: parameter names/shapes/dtypes/tied aliases from the checkpoint.
- `runtime_catalog`: actual runtime named modules/parameters; counts wall/load cost.
- `measure`, `candidate`, `ids`, `spec`: teacher-forced internal readout. `spec`
  supports `continuation`, `score_token_ids`, `capture` and `interventions`.
  A capture supplies `module`, `where` (`input`/`kwargs`/`output`), `path` (tuple/dict keys),
  optional `flat_indices`. Results retain actual tensor shape, input token IDs,
  decoder image-token positions and image grid. Vision tensor axes require
  inspection; do not assume they are decoder-token axes. No arbitrary gradient
  diagnostic or attention-probability extractor is implemented yet.
  Temporary interventions additionally supply explicit `flat_indices`, `values`
  and `operation` (`add`, `replace`, `scale`); arbitrary replacement values may be
  calculated in Python. They do not become weight edits or best candidates.
- `commit`, `parent`, `rationale`: validate staged tensors and create an immutable
  candidate. Parent must equal current checkout. Actual effective scalars are
  counted against W0; tied parameters count once. Staging clears on commit.
- `checkout`, `candidate`: return to any recorded candidate or W0; clears staging.
  Python variables remain, so explicitly refresh arrays after checkout.
- `evaluate`, `candidate`, optional `ids`: paired original/parent/candidate outputs
  under identical inputs. Omitting ids evaluates the fixed full development pack.
  Local subsets are diagnostic only; raw answers and repaired/worsened IDs return.
- `accept`, `candidate`: observer applies the frozen full-development selection
  and protection rules. Failures do not automatically expand budgets or scope.
- `artifact`, `name`, optional `offset`/`length`: read a page of full returned JSON.
- `freeze`: freeze the current best within the final sparsity budget; ends search.
  This is a development selection, not evidence of independent generalization.
- `stop`, `reason`: end with an honest negative/inconclusive result.

Every tool operation (including errors), selected parent, code and result is logged.
Weight edits preserve architecture, tensor names and shapes. Do not alter scoring,
input images, generation settings or budgets. Final deployment must be ordinary
inference from a reloaded static patch with no diagnostic hooks. An engineering
tool error is not evidence against the scientific hypothesis.

This is the first bounded development exploration after original-model screening.
Use all available development successes and failures, not only a preselected error
pattern. Read /evidence/bundle.json using Python for the complete package; it
includes previous_predictions. The human has not established a failure mechanism.
B concerns total vs spatially conditioned counts. C concerns visual vs usual
size judgments under original/counterfactual images and no-image controls.
Do not assume a missing neuron, a particular layer, or one shared cause.

Selection: ordinary-prompt joint correctness, averaging wording/order within each
source group then groups equally. B pairs total/subset; C pairs counterfactual
usual/visual. All conditions and both prompt arms are protected per wording/order
cell: maximum 0.035 accuracy loss vs original, format/truncation each <= 0.01.
Only full fixed development evaluation can select a best candidate. Ties prefer
fewer changed scalars. C's original/no-image controls and five-way correctness
must also be reported. View raw responses and repaired/worsened IDs.
Temporary support <=4,000,000 and final support <=1,000,000 actual BF16 scalars
relative to W0, across any legitimate parameter locations. Wall limit 7200 seconds
includes your thinking time, model loading, diagnostics and evaluations. No need
to use all 100 turns. Budget exhausted or no useful patch is a valid outcome.
Your persistent CPU workspace has NumPy only; use the metered observer for every
model forward. Select your own observations and edit computation. You may change
your hypothesis using feedback; an engineering error is not a task failure.

---

### 原件 2：C：Qwen3-VL 2B / 8B，各 50 轮

原路径：`experiments/wsp-vlm-c-scale-v1-2026-11-05/README.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-c-scale-v1-2026-11-05/README.zh-CN.md) · [单独阅读副本](../library/6693459a054c8dbd.md)；SHA-256：`6693459a054c8dbd0eb043c9a76fcb3fcd20f6ac700b126700877a63e5735cdd`。

---

#### C：Qwen3-VL 2B / 8B，各 50 轮

日期：2026-11-05。用户已确认所列模型适配，并授权“直接上卡排队”；新增要求为最终百分比与逐轮折线图。原始授权及恢复确认见 [authorization.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-c-scale-v1-2026-11-05/authorization.json)。

##### 问题与复用范围

问题保持为：WSP 能否在 C 的固定图文冲突任务上改善模型表现，同时满足原有保护条件？本轮增加两个同族 checkpoint，判断原 4B 的改善能否在其他规模上出现。比较各模型自己的 W0 与修补结果，不把不同 checkpoint 的差异解释为参数量的纯因果效应。

基准是 `wsp-vlm-open-repair-v8-2026-11-05` 的 C，轮数采用 `wsp-vlm-open-repair-v8x50-2026-11-05` 的有效 50 轮合同。原始配置保存在 [base-config.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-c-scale-v1-2026-11-05/base-config.json)，原代码来源哈希见 [reuse-engine.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-c-scale-v1-2026-11-05/reuse-engine.json)。旧任务和文件均不改。

- 数据：同样 64 个独立源组、2560 条开发请求，记录顺序、题目、答案、原图与预览文件哈希不变。模板、顺序、提示和条件不能当作新增独立样本。
- 推理：batch 64、BF16、SDPA、greedy、最多生成 128 tokens、相同图片大小限制与随机种子。
- 研究员：独立空上下文的 gpt-6-astra / max，同样 ChatGPT 登录与本地 CLI—SSH 持久 broker；没有预写选点/补丁配方。
- 操作：沿用原权重读取、CPU 沙箱、测量、补丁提交、相对 W0 的有效 BF16 改动计数、选择与冻结代码。
- 编辑预算：临时 4,000,000、最终 1,000,000 个标量；这是相同绝对预算，并非相同参数比例或等计算量。
- 保护：各 wording/order/prompt 条件单元下降不超过 0.035；格式/截断限制 0.01。原 C 联合 repair_score 决定选优，未改成全部单题准确率。
- 轮数：每模型 50 个不同、非零权重补丁完成全 D 评估；失败改善也计轮，诊断、部分评估和重复权重不计轮。到 50 自动冻结。遇到真实技术失败或研究员诚实提前停止，保留实际轮数，不伪称完成。

##### 模型适配与实施边界

2B：`Qwen/Qwen3-VL-2B-Instruct`，revision `89644892e4d85e24eaac8bacfd4f463576704203`。

8B：`Qwen/Qwen3-VL-8B-Instruct`，revision `0c351dd01ed87e9c1b53cbc748cba10e6187ff3b`。

官方元数据分别保存在 `upstream-2B.json` / `upstream-8B.json`。从镜像传输，逐文件校验官方 LFS SHA256 / Git blob SHA1。默认 Xet 通道出现零字节停滞，保留第一次下载日志并切换经小段验证可用的 HTTP；未更换 checkpoint。

适配仅涉及：模型路径/版本/哈希、原生共享权重映射；2B 单 safetensors 文件生成索引，权重字节不改；新模型各自的工程验收和完整 W0 基线；新实验路径与空卡调度；允许 50 轮无硬 wall cutoff。旧证据包中的 4B 预测及其来源哈希从新包清除，避免误当成新模型基线，记录与图像不改。原始包保留。

工程验收复用原验收操作：沙箱隔离、运行时模块/参数映射、batch64 重复与单条输入等价、固定三标量修改/异常回滚/重新加载、测量与直接 logits 一致。共 132 个生成样本与 2 个诊断前向样本，不计修补轮次，也不选点优化。未通过则停止，不自动降低 batch 或更换推理设置。

队列先等权重全部校验完成，再检查 GPU 无计算进程、显存低于 128 MiB、利用率为 0；取得每 GPU 文件锁后再复查。两任务独立等待，空闲卡先到先用，不终止现有任务。锁覆盖工程、基线及搜索。服务器承担目标模型与 broker，本地研究员控制器复用现有登录与 SSH 通道，需继续运行。

##### 成本与交付

每模型沿用样本/前向上限 384,000，target token reservation 上限 1,622,016,000，CPU Python 36,000 秒，研究员 2,000 轮工具对话 / 50,000,000 tokens；无会话硬卡时截止。完整 W0 的 2560 个样本计入搜索账本；50 次候选评估另需至少 128,000 个样本，诊断消耗也计账。新工程验收、下载字节与耗时单列。卡时待实测，不以旧 4B 耗时冒充 8B 预算。

每个模型的服务器结果目录：

`/workspace/acupuncture/external/wsp-vlm-c-scale-v1-2026-11-05/{2B,8B}/search/reports/`

- `result.json`：W0、最后候选、按规则选中的候选、冻结后最终百分比；未冻结时 final 为 null。
- `trajectory.json` / `trajectory.csv`：第 0 轮原始基线及每个完成轮次的数值、候选身份、是否选中及理由。
- `progress.png` / `progress.svg`：全部 2560 请求准确率与 C 联合修补指标分面绘图；每轮候选线与原规则选中线分别显示。没有把未完成轮次补成结果，也没有只画上升包络。

每完成一轮自动更新，最终再更新一次。图表只读取既有评估，不增加目标模型调用。全部单题正确率未必随按 C 联合指标选优而单调增加。

状态、原始回答、失败、候选和 transcript 保留在 `external/` 运行目录。权重/cache 不进 Git。科学身份为相同开发集上的方法复用，不能称独立留出确认、跨任务泛化、纯规模因果效应或论文 novelty 已证实。

##### 设计自查

依据 `docs/experiment-design-self-check.zh-CN.md` v1；设计者本人自查，不是独立审查。相较上版保持问题、数据、终点、算法与绝对编辑预算，仅换两模型并独立跑满用户要求的 50 轮；新增报告不反馈到选择规则。

| 项 | 判定与理由 |
|---|---|
| C01 | 通过：仍回答 C 行为改善，未转成机制、停止或其他赛道。 |
| C02 | 通过：新增两个同族 checkpoint 的同协议修补效果与逐轮过程。 |
| C03 | 通过：复用 v8 引擎、v8x50 轮数、冻结评分依赖、固定 C 数据与 v5 环境。 |
| C04 | 通过：4B 有改善是动机；2B/8B 均可能无改善或保护失败，不预设阳性。 |
| C05 | 通过：对象为各自 W0 的静态稀疏权重补丁，真实非零变化按有效 BF16 计数。 |
| C06 | 通过：输入、解码、评分固定，补丁之后正常前向响应；不声称内部状态保持不变。 |
| C07 | 通过：原生 tied weight 按实际配置与运行时核验，不拆共享存储。 |
| C08 | 通过：估计各模型内修补相对 W0 的开发效果；不用规模因果或自然机制措辞。 |
| C09 | 通过：两个模型均改善、仅一个改善、均无改善分别限定适用范围；不构造伪互斥机制。 |
| C10 | 通过：联合修补指标与全请求正确率分开，沿用真正完整回答评分。 |
| C11 | 通过：保护未通过/无改善仍保留；OOM、身份/数值验收失败单列为工程失败。 |
| C12 | 通过：新 checkpoint 的效果无法从旧结果推得；每个模型有独立用途，不扩数据/任务矩阵。 |
| C13 | 通过：固定 revisions、模型哈希、数据身份、合同及原始回执；64 源组；开发身份公开。 |
| C14 | 通过：成功或失败都留下模型适用范围；到 50 结束，不自动加轮、加模型救结果。 |

相关历史错误：E01 保留原问题；E02 不搬运4B层号；E03 相同绝对稀疏度不代表相同扰动；E04/E19 验收不是发现；E10/E11 两指标不互换；E12 保护通过不证明无一切损伤；E14 不推机制必要充分；E16 保留阴性；E20 不设互斥机制；E21 不凭重复阳性宣称 novelty；E22 明确源组、开发集与选择；E23 区分离线测试/真实验收/科学运行；E24/E25 不扩成完整机制研究。E05–E09、E13、E15、E17–E18、E26 的缓存拼接、形成读取或路径分解不适用于本轮静态权重方法复用。

反方检查：即使两模型都改善，也可能来自同一开发集上的自适应选择，不能推出未知样本改善；更大模型可能只因基线/可编辑比例不同而增益不同，不能识别参数量因果；候选最高分可能违反保护，必须按原选择规则报告；若两模型没有合法改善，应报告无改善而不是扩大预算。以上通过固定身份、分开指标、保留全轨迹与限制结论处理，未添加未经用户要求的控制矩阵。

设计结论：通过本轮方法复用范围的自查。工程状态与执行状态以 `audit/` 交付快照及远端实时回执为准，35 项合成 CPU 检查不替代真实模型验收。授权是用户本次明确确认，非自查生成。

##### 入口

服务器：`.venv-bench/bin/python -u experiments/wsp-vlm-c-scale-v1-2026-11-05/scale.py --size 2B --server`（8B 同理）。本地研究员：`python3 -u experiments/wsp-vlm-c-scale-v1-2026-11-05/scale.py --size 2B`。

仅首次调度使用上述入口；存在队列/研究员目录时不盲目重启。先核对 PID、状态、未完成动作和日志，不能重放不确定的模型调用。

---


## 时间、运行与停止收据索引

下面是所收集JSON的原有时间字段与状态，不把预计结束时间当实际完成时间。未列时间的文件仍有原件链接。完整JSON全部保存在原文归档，不能以此索引中的标量代替完整嵌套内容。

| 原件 | 原记录状态/阶段 | 原时间字段（原时区） |
|---|---|---|
| [audit/local-controllers.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-c-scale-v1-2026-11-05/audit/local-controllers.json) | {} | {"time_unix": "2026-11-05T09:45:03.801829+00:00"} |

## 全部原始资产入口

本目录在固定提交下共有31个跟踪文件，包含代码、原回答、失败、收据和压缩证据；文件数不是样本数。[逐文件完整账本](../assets/126-wsp-vlm-c-scale-v1-2026-11-05.tsv) · [原目录](https://github.com/yuxiexiong/acupuncture/tree/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-c-scale-v1-2026-11-05)。未复制模型权重、环境或凭据。
