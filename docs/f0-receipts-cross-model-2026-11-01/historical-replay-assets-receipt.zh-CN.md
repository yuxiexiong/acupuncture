# F0 收据 2：历史协议回放对照（L2/N5063 +1）的资产定位

日期：2026-11-01。对象：PLAN r2 §8.1 "历史协议回放对照"所需的旧资产：输入、模板、剂量定义、精度、模型 revision、代码实现、解码与 k 定义、运行收据。方法：ssh 只读列目录与读 JSON；本地读仓库 `experiments/early-input-control-v1-2026-10-29/` 的 CONTRACT/EXECUTION/REPORT。没有运行模型。

## 1. 结论

**回放资产齐全，可以执行；但有两项与新协议的差异必须写进合同。**

## 2. 资产清单（服务器 `/workspace/acupuncture/experiments/early-input-control-v1-2026-10-29/`，6.5G runs + 3.7M exports）

| 项 | 位置 | 身份 |
|---|---|---|
| 代码冻结 | `freeze-r03.json` | sha256 `dc0556c76c10820b71597d42b26939b3967e7b543168775a701a64058a463aca`；文件内列出 control_engine.py、execution.py、experiment.py、task_data.py、launch.py、preflight.py 等 12 个代码文件与 data/*.json 的逐文件 sha256。机制阶段两个 run 的 `controller.json` / `execution.json` / `worker-*/authorization.json` 均绑定该 freeze_sha256，`freeze_path: freeze-r03.json` |
| 模型 | `worker-0/metadata.json` | `model_class: Qwen3_5ForConditionalGeneration`，`model_path: /data/models/Qwen3.5-4B-851bf6e`（= HF 851bf6e，见收据 1），dtype bfloat16，softmax float32，attention_backend eager，batch 1 |
| 环境 | 同上 | torch 2.6.0+cu124，transformers 5.20.2，cuda 12.4，cudnn 90100（= `.venv-bench`） |
| 解码 | `contract.json.generation` | max_new_tokens 128，greedy，thinking false，EOS 集合 `[248044, 248046]`，`branch_budget_includes_prefix: true`，`fork_steps: [4, 16]` |
| 输入 | `data/development.json`、`data/confirmation.json`、`data/anchors.json`（哈希在 freeze-r03） | **中文**提示 + 固定中文指令（"请用中文简短回答，通常一至三句话……"）；anchors 来自 `layer-survey-toy-v1-2026-10-27/questions.json` |
| 针 | `selection.json`、`data/directions.json` | 层 0–3/12–15/24–27，每层 2 个原生通道 + 10 候选；L2 的 selected 是 [5251, 575]，**N5063 在 L2 候选表内**，作为"开发锚点/历史针"进入机制阶段（REPORT 表格标"开发锚点"） |
| 机制阶段运行 | `runs/mechanism-development-r01/`（1,210 记录）、`runs/mechanism-confirmation-r01/`（1,440 记录） | 每个 worker 下 `branch-comparisons/<输入>__N_L02_C5063_D+1__fork004|016.json`；开发 16 个文件、确认 48 个文件。确认集 48 个中 `completed` 29、`not_applicable` 19（源提前 EOS 或未到 k） |
| 分支记录结构 | 例 `CAR01-f0-required__N_L02_C5063_D+1__fork004.json` | 键：`status, key, fork_step, prefix_token_sha256, actual_token_union, branches{continue, withdraw, rebuild}` |
| 其余针 | 同目录 | N_L00_C4146_D+1、N_L02_C5251_D−1、N_L12_C8296_D−1、N_L13_C248_D+1、N_L25_C2747_D+1 各 48 个确认文件，可一并回放 |
| 盲读与裁决 | `reading/mechanism-*/lock.json`、`readiness/mechanism-selection-r01.json`（status locked，绑定 freeze 与 joined.json 哈希） | 行为标签来自盲读，不是机械解析 |
| 导出 | `exports/mechanism-*-answers.jsonl.zst` | 答案文本导出 |

## 3. 旧协议的 k 与分支定义（CONTRACT §97–§107 原文要点）

- 分叉边界：前 k−1 个生成 token 已增量读入，第 k 个已选出但尚未读入模型。
- continue：full 历史状态，继续原针；withdraw：同一 full 历史状态，关闭原针；rebuild：无针增量重建同一文字历史的状态，无针。
- 各分支先读入相同的第 k 个 token，在自由选择下一个 token 前记录可比较的预测，随后各自自由生成。
- 已 EOS 或未达 k：记不适用，不强行生成、不填零、不换分叉步。每分支已有前缀 + 后续生成总长 ≤ 128。

**与 PLAN r2 §6 的映射**：pending token 定义逐字相同（"第 k 个已选出但尚未送入"）；三臂定义相同。可做显式边界映射，无需"数字相同当操作相同"的担心。

## 4. 必须写进回放合同的两项差异

1. **输入语言**：旧协议是中文提示与中文指令；PLAN r2 §3 主面板是英文。回放只能用旧的中文输入（PLAN §8.1 已规定"用原来的输入/模板"），因此回放结果与新面板**不共享任何输入**，只校验协议与实现，不校验跨语言。
2. **剂量定义**：旧针是 ±1 "原生剂量"（按 10-27 toy 的参考尺度），PLAN r2 §4 是按有效投影列范数与残差 RMS 配平的 d。回放必须用旧的剂量实现（freeze-r03 的 control_engine.py），不能换成新配平；两者的实际 Δresidual 要各自记录，不比较。
3. **分支长度**：旧的分支总长 ≤128（含前缀），新协议源 80 / 派生 64。回放按旧值。
4. **行为标签**：旧结果是盲读标签；PLAN §6 新协议用机械解析。回放时若用机械解析重判旧文本，要与旧盲读标签一并报告，不替换。

## 5. 执行所需的最小步骤（F1 内，PLAN §8.1）

1. 锁定：复制 `freeze-r03.json` 清单，对服务器上 12 个代码文件与 data/*.json 重算 sha256，与冻结值逐一比对；对 `/data/models/Qwen3.5-4B-851bf6e/config.json` 比对 `ddc63e1c…`。
2. 选 `data/development.json` 中按情景 ID 排序的前 4 个完整开发情景（PLAN §8.1），在 `.venv-bench` 内用旧 `execution.py` 路径对 N_L02_C5063_D+1 跑 k=4/16 的 continue/withdraw/rebuild（共享源 ≤20 条生成）。
3. 比较：生成 token 序列与旧 `branch-comparisons` 文件的 `prefix_token_sha256`、`actual_token_union`、各分支首步预测逐位比对；不一致按 §4 的差异清单先排工程。
4. 记录：输出 `readiness/historical-replay-r01.json`，含 freeze 比对、模型哈希、逐条比对结果；不进入 A/B 主估计。

## 6. 边界

- 没有打开任何旧结果的内容做重新判读；只核对了文件存在、键结构与 status 计数。
- `freeze-r03.json` 中代码文件哈希**未**在本次重算（只读了冻结清单与 run 收据的绑定）；步骤 1 要做。
- 旧实验的 worker 日志与 `.runtime` 目录未查。
- 本收据不授权运行；回放属于 F1。
