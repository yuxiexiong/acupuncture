# 026．阶段一：异常留在哪一种缓存

[返回总时间线](../README.zh-CN.md)

**时间定位**：已提取运行收据的最早时间锚点（可含预检） 2026-10-29T17:35:41.459374+08:00；不能当作全部子运行起止。

**当时的目的与设计**

固定文字与干预历史，分别操作全注意力KV、递推状态和短卷积缓存，区分停止与事实候选读数；不是把撤针后状态视为自动恢复干净。

**实际过程、结果与后来更正**

阶段一实际执行完成。本章完整保留条件矩阵、各缓存组结果、运行收据和数值验收，后继阶段二另列，避免把不同范围的V或conv名称混成同一操作。

**来源身份**：`early-state-localization-v1-2026-10-29`；本章主体来源提交 `7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8`。下方原文中的状态是各文件写作时的状态，不能把早期“尚未运行”覆盖后期正式收据，也不能将后期结果倒填进早期设计。


## 原设计、执行过程、结果与更正全文

以下按“设计与题目 → 工程/执行记录 → 结果/更正 → 其他历史说明”组织；同类内没有可靠时间时保留路径顺序，不冒充严格先后。正文未删段；仅为本章节重排标题层级、把相对链接指向固定提交。原始字节另外完整保存。

### 原件 1：早层失效定位：污染存在哪一种缓存（合同 r01，第一阶段）

原路径：`experiments/early-state-localization-v1-2026-10-29/CONTRACT.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-v1-2026-10-29/CONTRACT.zh-CN.md) · [单独阅读副本](../library/d305b4a6237828eb.md)；SHA-256：`d305b4a6237828eb66ec8ab035118bd8c8f8f129e051718508ebc0f52a2a52c7`。

---

#### 早层失效定位：污染存在哪一种缓存（合同 r01，第一阶段）

日期：2026-10-29。实验目录：`early-state-localization-v1-2026-10-29`。

**授权**：用户原话（2026-10-29）：“先只跑第一阶段，第二阶段不着急，把第一阶段的合同，代码都写好，做好测试后上gpu直接开跑”。据此本合同只授权第一阶段（§4.2 六臂与 §4.3 衰减臂），两个面板，最多两个 worker。**§4.4 第二阶段未授权**，触发规则保留为预先登记，结果出来后只报告是否满足触发条件，不运行。GPU 预检（§6）是开跑的第一步，不得跳过。冻结后记录 commit hash 与 freeze SHA。

##### 1. 问题

`early-input-control-v1-2026-10-29` 已确立（推导档，开发与新题确认一致）：

1. 早层（L0–L3）尺度校准的 ±1 写入下，回答几乎全部首 token 即 EOS（开发 120/144、确认 120/143）。
2. 只在“提示中最后位置之前”注入（`prompt_except_last`）、最后位置与全部生成不注入，L0/N4146 +1 与 L2/N5251 −1 仍 24/24 未交付——此时已生成文本为空、提示文本原样，**文本不可能是承载者**。
3. 强制续写两候选的事实敏感度保留比 R：早层 ±1 开发 0.03/0.05、确认 16/16 未检出（`early-stop-knowledge-readout-v1-2026-10-29`）。

因此，早层写入在提示位置留下的污染存于模型的缓存状态中，并使最后位置读不到题目事实。本实验回答：**污染存在哪一种缓存，以及在哪一段深度。**

Qwen3.5-4B 的缓存共三类（已核对 `cache_utils.py`、`modeling_qwen3_5.py` 与模型配置）：

| 缓存 | 所在层 | 性质 |
| --- | --- | --- |
| KV | 8 个全注意力层（L3、7、11、15、19、23、27、31） | 写入后不变，后续每个位置都读 |
| 递推状态 `recurrent_states` | 24 个线性注意力层（GatedDeltaNet） | 每个位置按 delta 规则更新，由遗忘门衰减 |
| 短卷积缓存 `conv_states` | 同上 24 层 | 只保存最近 3 个位置（卷积核 4） |

注入在第 L 层 MLP；同一层的注意力先于 MLP，所以只有 L 之后各层的缓存可能被污染。

##### 2. 假设与预先登记的预测

| 假设 | 内容 | 来源与档位 | 预测（见 §5 判读表） |
| --- | --- | --- | --- |
| H-rec | 污染主要在递推状态 | 类比：2609.04434 在 Qwen3.5-4B 上发现语言/人设类信息走递推状态；Yap 2603.16335 断言（未排除 KV） | 换干净递推状态即恢复，换干净 KV 不恢复 |
| H-kv | 污染主要在全注意力 KV | 推导：KV 不衰减，最后位置在 L3 起直接读所有被污染位置；反向证据 S0 Tuning 2604.01168（初始状态扰动到提示末尾只剩 0.03% KL） | 换干净 KV 即恢复，换递推状态不恢复 |
| H-both | 两者任一被污染都足以失效 | — | 单换任何一类都不恢复，全换才恢复 |
| H-either | 两者需同时被污染才失效 | — | 单换任何一类都恢复 |
| H-conv | 只在最近 3 个位置的卷积缓存 | 推导：`prompt_except_last` 的最后 3 个提示位置被注入 | 只换 conv 即恢复 |

**登记的主预测**：在新题确认面板上，三个锚定条件（L0/N4146 +1、L2/N5251 −1、L2/N5063 +1）多数落在 H-rec 的判读格。该预测以类比为据，可以不成立；不成立同样是可交付结果，不按结果改判读表。

**登记的理论预测（衰减）**：若承载者是递推状态，遗忘门使远离末位的污染贡献更小，则“只注入提示前半段”应比“只注入后半段（不含末位）”损伤更弱；若承载者是 KV，两者差别应小。判据见 §5.3。

##### 3. 对象

- 模型、精度、解码、聊天模板、校准、剂量公式、选点与数据全部沿用 `early-input-control-v1-2026-10-29`（freeze-r03 对应的 `contract.json`、`selection.json`、`data/`），不得改动。
- 条件（26 个）：
  - 早层原生 ±1：L0–L3 各 2 通道 × 2 符号 = 16；
  - 早层共同方向 ±1：L0、L3 × 2 方向 × 2 符号 = 8；
  - L2/N5063 +1（机制线锚点，新题面板上已有 full 记录）；
  - 阴性对照 L25/N2747 +1：已知 prefill-only 回答正常（开发 24/24、确认 21/24），预期各臂无差别。
- 面板：开发 24 输入（探索、调试读法），新题确认 24 输入（检验登记预测）。确认面板在开发判读锁定后才运行。

##### 4. 实验设计

###### 4.1 基本操作：拼缓存

对每个条件 × 输入：

1. 用同一引擎、同一校准（参考提示与 `early-input-control` 完全相同的 fact 0 清洁提示），在提示前 n−1 个位置上一次前向（显式 `position_ids = 0…n−2`）：带注入得 `cache_T`，不带注入得 `cache_C`（`cache_C` 按输入共享）。注入用 `ControlEngine._control_hooks(condition, reference, "prefill", n−1, …)`，即 n−1 个位置全部注入，与 `prompt_except_last` 的注入位置相同。
2. 按臂把三类缓存逐层拷贝拼成新缓存（深拷贝，不共享张量）。
3. 以拼好的缓存读入最后一个提示 token（不注入），之后不注入、greedy 生成，至多 128 新 token，EOS 原长。
4. 同一拼好的缓存再分别强制读入两条候选，得候选 log likelihood。

###### 4.2 第一阶段臂（每条件 × 输入 6 臂）

| 臂 | KV | 递推状态 | conv | 作用 |
| --- | --- | --- | --- | --- |
| A0 全污染 | T | T | T | 与 `prompt_except_last` 同设定（计算形状不同，见 §6.1） |
| A1 全干净 | C | C | C | 与原版同设定（计算形状不同，见 §6.1） |
| A2 只洗 KV | C | T | T | 检验 H-kv |
| A5 只洗线性层 | T | C | C | 检验 H-rec + H-conv（A2 的补集） |
| A3 只洗递推 | T | C | T | 在线性层内分离递推与卷积 |
| A4 只洗 conv | T | T | C | 检验 H-conv |

规模：26 条件 × 24 输入 × 6 臂 = 3,744 次生成/面板，每次附 2 次候选读取。A1 按输入共享，实际 3,744 − 25×24 = 3,144 次独立生成/面板。

###### 4.3 第一阶段附加臂：衰减检验（三个锚定条件）

- 记 m = ⌊(n−1)/2⌋。B1 只注入位置 0 … m−1；B2 只注入位置 m … n−2；末位与生成均不注入。
- 两臂均不拼缓存，直接从各自缓存生成并读候选。位置掩码 hook 与 `_control_hooks` 的写入数学逐字节相同（预检门槛 6）。
- 锚定条件：L0/N4146 +1、L2/N5251 −1、L2/N5063 +1。
- 规模：3 × 24 × 2 = 144/面板。

###### 4.4 第二阶段（条件触发，触发规则现在冻结）

若第一阶段确认面板判出单一承载类（KV 或递推），对三个锚定条件逐深度定位：只把承载类在某一组层洗干净（KV：每个全注意力层单独一组，共 8 组；递推：每 3 个线性层一组，与 KV 组对齐，共 8 组），其余保持污染。规模 3 × 24 × 8 = 576/面板。若第一阶段判 H-both 或 H-either，第二阶段改为“洗某组 KV + 某组递推”的同组联合洗，组数仍为 8。其他结局不触发第二阶段，如实报告。

###### 4.5 读数

- **主读数**：①首 token 是否 EOS（逐输入）；②事实敏感度 S(c,b) 与保留比 R(c)，定义与零分布完全沿用 `early-stop-knowledge-readout-v1-2026-10-29/CONTRACT.zh-CN.md`，参照带固定为开发面板已算出的 [0.897, 1.045]。
- **副读数（只报告，不入判据）**：
  - 首步 `stop_advantage`（EOS 最大 logit 减最强非 EOS logit）与首步 top5；
  - 末位查询在 8 个全注意力层对位置 0 的注意力占比（各头平均；`output_attentions` 只在末位一步开启，预检须证明开启与否 logits 哈希相同）——S 线竞争解释；
  - 每个线性层在建缓存时的遗忘门累积衰减：以 `g = −exp(A_log)·softplus(a + dt_bias)` 逐位置计算，记录位置 0 与半程位置的信息到提示末尾的存活比 `exp(Σ_{t>p} g_t)`（各头平均），T 与 C 各一份；
  - 自由回答原文全部保存；盲读在第一阶段两面板结束后进行，规则同 early-input-control（模型辅助、10% 第二读者、先锁后揭盲），不入本合同判据。

##### 5. 判读

###### 5.1 每个条件 × 臂的恢复档

| 档 | 判据 |
| --- | --- |
| 恢复 | R(臂) ≥ 参照带下界 0.897 |
| 部分恢复 | 未达“恢复”，但臂相对 A0 的逐基础情景差 S(臂,b)−S(A0,b) 经 2¹² 符号翻转精确置换单侧 p < 0.01 |
| 未恢复 | 其余 |

首步 EOS 计数与 R 并列报告；两者方向不一致的条件单列，不合成总分。

###### 5.2 每个条件的承载判读（按 A2、A5，再按 A3、A4 细分）

| A2 只洗 KV | A5 只洗线性层 | 判读 |
| --- | --- | --- |
| 恢复/部分 | 未恢复 | KV 承载 |
| 未恢复 | 恢复/部分 | 线性层承载；再看 A3/A4：A3 恢复→递推，A4 恢复→conv，二者都需→两者共同 |
| 恢复/部分 | 恢复/部分 | 需两类同时被污染才失效（H-either） |
| 未恢复 | 未恢复 | 任一类被污染都足以失效（H-both） |

另记 A0 本身未失效（R 在“恢复”档）的条件为“不适用”，不进入判读分母。

主预测（§2）在确认面板上成立的条件：三个锚定条件中至少 2 个判为“线性层承载 → 递推”。

###### 5.3 衰减预测判据

对三个锚定条件，逐基础情景比较 S(B1,b) 与 S(B2,b)：H-rec 预测 S(B1) > S(B2)（前半注入损伤更弱）。以 S(B1,b)−S(B2,b) 的均值做 2¹² 符号翻转精确置换，单侧 p < 0.01 记“衰减预测成立”；反向显著记“反向”；其余记“无法区分”。

##### 6. 工程门槛（任何一项不过即停，不进入正式阶段）

1. **同路径恒等（精确）**：全部臂走同一条“先读 n−1 个提示 token 建缓存、再单独读末位”的路径。未拼接的 T 路径与“由 T 各类拷贝拼回”的 A0 逐步全词表 logits 哈希一致；C 与 A1 同理。与 `early-input-control` 既有 `prompt_except_last`/原版 full 记录（一次读入 n 个 token 的另一计算形状）的一致只作**数值诊断**：报告逐 token 一致率、首个分歧步与末位 logits 最大差，不作停止条件、也不据此放宽本条精确门槛。
2. **可读性对照（防静默丢弃）**：对每类缓存，把其张量替换为同范数随机张量，末位 logits 必须改变（Δ = ‖logits(拼接) − logits(A0)‖∞ > 0）；三类各至少在预检全部样例上满足。任一类 Δ = 0 视为该类未被读取，停止。
3. **拼接正确**：A0 由 T 各类拷贝拼回后与未拼接的 T 逐步 logits 哈希一致；A1 同理。
4. **增量路径精确**：拼缓存后的生成与候选读取走与 `manual_score_one` 同一显式增量路径（显式 `position_ids`、全新缓存对象），在预检中与引擎生成路径逐步全词表 logits 哈希一致。
5. **hook 清除与权重哈希前后一致**；不覆盖已有目录；失败保留 partial 与日志。
6. **掩码 hook 等价**：位置掩码全为真时，掩码 hook 建出的缓存与 `_control_hooks("prefill")` 建出的缓存逐张量哈希一致。
7. **注意力读出不改变计算**：末位一步开启 `output_attentions` 与不开启的 logits 哈希一致。
8. **拼接来源审计**：每条正式记录逐层记录各缓存张量的哈希及其与 T、C 的匹配，必须与该臂的设计一致（例如 A2 中全注意力层 KV 全部等于 C、线性层状态全部等于 T）。

数值门槛不放宽；路径差异只作为诊断记录。

##### 7. 停止条件与失败类型

- 第 6 节任一门槛失败：合同执行失败，停止，修复后以新版本身份重跑预检。
- 确认面板只在开发判读、判读规则与第二阶段触发结果锁定后打开；打开后不得修改本合同任何判据。
- 某条件 A0 未失效：记“不适用”，不补选条件。
- 负面结果分三类报告：科学失败（预测被否）、没拿到结果（效应不显著）、合同执行失败（信息量为零，不作负面证据）。

##### 8. 复用与实现

- 引擎：在 `early-input-control-v1-2026-10-29/control_engine.py` 基础上新增“拼缓存 + 显式增量生成”入口，新代码放本目录，不修改旧冻结目录。
- 先读 2609.04434 公开实现（`github.com/kirillTerra/split-prefill`，提交 `22de30d`）的拆分与 Δ 检查做法，能复用则复用并记来源；与本项目 hook、校准接口不兼容的部分自写。
- 读数与判读复用 `early-stop-knowledge-readout-v1-2026-10-29/analyze.py` 的 S、R、置换函数。
- CPU 测试至少覆盖：拼接臂的组件来源正确、深拷贝无共享、A0/A1 拼回恒等、可读性对照在合成模型上 Δ>0、判读表全部四格及“不适用”可被触发、衰减判据三结局可被触发。

##### 9. 预算与 ETA（估计，未实测）

| 阶段 | 生成次数（每面板） | 估计（两卡，较慢 worker） |
| --- | ---: | --- |
| GPU 预检 | 每卡 2 输入 × 3 条件 × 全部臂，另加门槛检查 | 约 0.2 h |
| 第一阶段 4.2 | 3,144 | 1.5–2.5 h |
| 衰减 4.3 | 144 | 约 0.1 h |
| 第二阶段 | 576 | **未授权** |

依据：`development-r01` 4,632 次生成实测 2.32 h；本实验早层 A0 多为 1 token，恢复臂回答约 30–60 token。两面板合计约 4–6 h，另加阅读与核验。磁盘：原始记录预计每面板 1–2 GiB，服务器余量约 116 GiB。实测 ETA 以本实验 GPU 预检为准重估。

##### 10. 不做的事

- 不修改权重、不训练、不下载新模型。
- 不在确认面板上遍历组件或按修复效果挑层。
- 不把“恢复”写成“修复”或“找到根因”；定位结论只限于本面板、本模型、本剂量。

##### 11. 偏离记录

- **2026-10-29 共卡**：两张 GPU 被 `/workspace/jevrep` 的任务队列持续占用（各约 24 GB、利用率 95–100%，队列尚余 33 个任务）。用户原话：“允许共卡，现在就跑”。worker 的启动检查由“该卡无其他计算进程”改为“该卡空闲显存 ≥ 20 GiB”，并在 `execution.json` 记录启动时同卡进程与空闲显存。影响：只影响速度；同一 kernel 与数值路径不因共卡改变，贪心解码结果的可复现性由同路径恒等门槛与逐记录哈希核验。不抢占、不停止、不修改对方任务。freeze-r01 与 `readiness/authorization-preflight-r01.json` 保留不用，改用 freeze-r02。

---

### 原件 2：早层失效定位（第一阶段）：结果报告

原路径：`experiments/early-state-localization-v1-2026-10-29/REPORT.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-v1-2026-10-29/REPORT.zh-CN.md) · [单独阅读副本](../library/0fffb3c557aa875b.md)；SHA-256：`0fffb3c557aa875ba2b0117ec67108d71f28c447b6fc81b42b9f338e040e8b0a`。

---

#### 早层失效定位（第一阶段）：结果报告

2026-10-29。Qwen3.5-4B，BF16，greedy，最多 128 新 token。合同 r01，代码冻结 freeze-r03（`e4d45b85…`）。判读按冻结脚本 `analyze_localize.py`；自由回答盲读为模型辅助子代理，不是人类评审。分档：**推导**＝本实验读数支撑；**类比**＝相邻证据；**推测**＝未验证。

##### 0. 先说不利的部分

1. **主假设被否证（科学失败，两面板一致）**：登记的主预测“早层提示位置的污染主要存在递推状态里”（≥2 个锚定条件判“线性层→递推”）在开发与确认面板都不成立。
2. **理论衰减预测被反向否证**：H-rec 预测“只污染提示前半段”应比后半段损伤更轻；实际前半段损伤更重（开发 3/3 反向；确认 2/3 反向、1/3 同向但不显著）。
3. **开发派生的 P-dev3 在确认面板不成立**：“多数早层失效条件判 either_needed”确认只有 11/25；“哪一类缓存承载更多”在两面板之间不稳定。
4. **工程偏离与失误**：
   - 共卡运行（用户授权“允许共卡，现在就跑”）：启动检查改为“空闲显存 ≥ 20 GiB”。
   - preflight-r01 因我写的汇总 bug 失败（`+=` 误用），修复后 preflight-r02 全部门槛通过。
   - confirmation-r01 的 launcher 收尾核验因我在运行中往实验顶层加入 `eval_predictions.py` 而报 “Frozen source changed”；冻结集合只多此一文件、无改动无缺失，worker 启动时冻结核验已通过，移出后两 worker 事后 verify 通过（`readiness/confirmation-verification-posthoc-r01.json`）；controller 的 failed 状态原样保留。
   - 运行吞吐受 CPU 侧开销（每臂缓存深拷贝与逐层哈希审计）限制；GPU 独占时利用率约 27%，未在冻结后改动。

##### 1. 问题与设计

上一实验已推出：早层（L0–L3）写入只作用于“提示中最后位置之前”时，回答仍然失效，此时文本未被改动，污染只能存于缓存。本实验把提示前 n−1 个位置分别在“注入/不注入”下建缓存（T/C），按三类缓存——全注意力 KV（8 层）、GatedDeltaNet 递推状态（24 层）、短卷积缓存 conv（24 层，只含最近 3 个位置）——逐类拼接，再读末位并生成：

| 臂 | 洗干净的缓存 |
| --- | --- |
| A0 | 无 |
| A1 | 全部（原版） |
| A2 | KV |
| A3 | 递推 |
| A4 | conv |
| A5 | 递推 + conv |
| B1 / B2 | 不拼接；只污染提示前半段 / 后半段（三锚定条件） |

26 条件（早层原生 ±1 共 16、早层共同方向 ±1 共 8、L2/N5063 +1、阴性对照 L25/N2747 +1）× 24 输入，开发与确认各 3,288 条。主读数：首步 EOS；事实敏感度保留比 R（两事实候选偏好差的差分，相对原版；参照带下界 0.897）。

##### 2. 工程验收

| 运行 | 记录 | worker exit | launcher 核验 | 逐 worker verify | 本地归档 | 墙钟 h |
| --- | ---: | --- | --- | --- | --- | ---: |
| preflight-r01 | 40+40 | 1 / −15 | 失败（汇总 bug） | — | 随 Git | 0.07 |
| preflight-r02 | 40+40 | 0 / 0 | passed | passed | 随 Git | 0.07 |
| development-r01 | 3,288 | 0 / 0 | passed | passed | passed（0 缺失 0 不符） | 2.38 |
| confirmation-r01 | 3,288 | 0 / 0 | 失败（运行中加入文件） | **事后 passed** | passed | 3.44 |

预检在真实数据上通过：同路径恒等（拼接 vs 未拼接逐步 logits 哈希一致）；三类缓存可读性（随机化每类均改变末位 logits，排除静默丢弃）；显式增量路径与引擎生成路径逐步 logits 哈希一致；位置掩码 hook 与原引擎逐字节等价；注意力读出不改变计算。每条正式记录逐层审计缓存张量来源（与 T/C 匹配），verify 全部通过。合计约 5.9 h 墙钟、双卡约 11.9 GPU 小时（共卡）；无单价，不估金额。GPU 已释放本实验进程。

##### 3. 结果

###### 3.1 冻结预测

| 预测 | 开发 | 确认 |
| --- | --- | --- |
| 主预测：递推承载（≥2/3 锚定） | 不成立（1/3） | **不成立**（0/3） |
| H-rec 衰减：前半段损伤更轻 | 不成立（3/3 反向） | **不成立** |
| P-dev1：首步停止由线性层承载（EOS(A3)<EOS(A0) 且 EOS(A2)≥EOS(A3)） | 成立 | **成立 4/4** |
| P-dev2：前半段更关键（≥2/3 反向） | 成立 | **成立 2/3** |
| P-dev3：多数判 either_needed | 成立 | **不成立 11/25** |

###### 3.2 首步停止 vs 事实可用性：两种损伤，两个承载者（推导）

**首步停止由线性注意力层的局部状态承载。** A0 首步 EOS ≥12/24 的条件中（确认：N_L00_C1210 −1、N4146 ±1、V1_L00 −1），只洗递推或只洗 conv（最近 3 个位置）后首步 EOS 全部为 0；只洗 KV 仍有 18、24、19、23 个。开发面板同型。

**事实不可用没有单一承载者。** 只洗任何一类都恢复不到参照带：开发 25 个失效条件中 2 个、确认 0/25。中位 R：

| | A0 | A2 KV | A3 递推 | A4 conv | A5 线性层 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 开发 | 0.09 | 0.61 | 0.57 | 0.30 | 0.63 |
| 确认 | 0.10 | 0.56 | 0.41 | 0.15 | 0.45 |

KV 与线性层各自恢复约一半，二者相加接近原版；A2>A5 的条件开发 12/25、确认 18/25，相对大小不稳定。

**提示前部位置决定事实可用性。** 只污染前半段（B1）R：开发 0.007/0.28/0.30，确认 0.06/0.21/0.13；只污染后半段（B2）：开发 0.48/0.77/0.83，确认 0.24/0.85/0.60。

###### 3.3 自由回答（副读数，盲读锁定后揭盲）

原版 A1 两面板 24/24 跟随事实；第二读者 fact 一致 241/249（开发）、279/293（确认）。A0 失效早层条件的自由回答（开发/确认）：

| 臂 | 跟随事实 | 未交付 | 其他错答 |
| --- | ---: | ---: | ---: |
| A0 | 0.35 / 0.20 | 0.59 / 0.70 | 0.05 / 0.08 |
| A2 KV | 0.79 / 0.67 | 0.20 / 0.23 | 0.01 / 0.07 |
| A3 递推 | 0.83 / 0.53 | 0.05 / 0.23 | 0.07 / 0.17 |
| A4 conv | 0.42 / 0.26 | 0.51 / 0.62 | 0.05 / 0.09 |
| A5 线性层 | 0.88 / 0.54 | 0.03 / 0.17 | 0.07 / 0.21 |
| B1 前半段 | 0.26 / 0.29 | 0.07 / 0.01 | **0.64 / 0.60** |
| B2 后半段 | 0.61 / 0.50 | **0.38 / 0.44** | 0.00 / 0.03 |

前半段污染的模型**会作答但答错**（多为“无法判断”、答非所问）；后半段污染主要是**不交付**。与 §3.2 一致：停嘴由末端附近的局部状态触发，事实丢失来自提示前部。只洗 conv 消除首步 EOS，但一半以上回答仍未交付（之后停止或跑题），说明 conv 只承载“首步”这一处停止。确认面板 other_fact 多为推错/读错条件碰巧落在另一事实（读者报告），不作“采用另一事实”的证据。

###### 3.4 sink 竞争解释（推导，读数粗）

末位查询对首 token 的注意力：A0 高于原版（N4146 +1 在 L3 0.21 对 0.09），损伤最重的 B1 与原版相近（0.11）。“sink 注意力被削弱”不是本面板的机制。

##### 4. 解释：早层猜想推进到哪里

- **早层写入同时造成两种可分离的损伤**：①**停嘴**——由线性注意力层中靠近末位的局部状态（递推状态，乃至只含最近 3 个位置的 conv 缓存）触发；②**题目事实不可用**——分布在 KV 与线性层两类缓存中，主要来自提示前部位置；只修任何一类都只恢复约一半。
- 原假设“污染住在递推状态里”只对①成立；对②不成立。理论上“递推状态遗忘、KV 不遗忘”的衰减图景被前部位置更关键的结果否定——前部位置的污染通过两类缓存都能持续影响末位。
- 这与上一实验的读数一致并推进一步：“早层停嘴时事实不可用”（`early-stop-knowledge-readout`）现在可以拆成“停嘴”与“事实丢失”两个通路，且它们的承载者不同。
- **仍未解决/竞争解释**：前部位置为何关键（题面事实所在位置？聊天模板头部？）未拆；KV 与线性层各贡献一半是否只是两条读出路径并行的结果（任一路径带有干净信息即可部分恢复）未检验；单模型、每层两通道、两条随机方向，不推广。
- **下一步（未授权，第二阶段已预先登记但不满足其“单一承载类”触发条件）**：按位置窗口（题面事实所在区间 vs 模板头部）拆分污染；对“停嘴”通路在 conv 与递推之间逐层定位。

##### 5. 交付

- 合同、代码、测试与收据：`CONTRACT.zh-CN.md`（r01，§11 偏离）、`localize.py`、`analyze_localize.py`、`test_localize.py`、`readiness/`（CPU r01–r03、freeze r01–r03、授权、预检失败与核验、开发锁定与解释、事后核验）。
- 判读：`analysis/development-r01.json`、`analysis/confirmation-r01.json`、`analysis/predictions-confirmation-r01.json`。
- 盲读：`reading/{development,confirmation}-r01/`（packets、labels、second-read、lock、key/joined 压缩）。
- 原始记录（每条含逐步读数、候选读数、缓存来源审计、门衰减、注意力副读数）：服务器 `runs/`，本机 `~/acupuncture-archive/early-state-localization-v1/*.tar.zst`，核验收据 `readiness/archive-verify-*.json`。

---

### 原件 3：开发面板判读与确认前锁定（r01）

原路径：`experiments/early-state-localization-v1-2026-10-29/readiness/development-interpretation-r01.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-v1-2026-10-29/readiness/development-interpretation-r01.zh-CN.md) · [单独阅读副本](../library/6dc6f1adaef4fd0a.md)；SHA-256：`6dc6f1adaef4fd0aa0ad5f5afaee98a3b957c1c7110ce624f95634bedefd1e54`。

---

#### 开发面板判读与确认前锁定（r01）

开发面板 development-r01：3,288 条，两 worker exit 0，launcher 与逐 worker verify 通过；墙钟 2.38 h（与 jevrep 共卡）。判读按冻结脚本 analyze_localize.py（freeze-r03）。确认面板此前从未运行，无任何确认输出。

##### 开发观察（锁定）

1. 主预测（≥2 个锚定条件判“线性层→递推”）在开发面板不成立：N4146 +1 递推；N5251 −1 线性层两者；N5063 +1 单洗任一类均部分恢复。
2. 衰减预测（H-rec：前半段注入损伤更轻）三锚定条件均“反向”：B1 R=0.007/0.28/0.30，B2 R=0.48/0.77/0.83。提示前部位置更关键。
3. 26 条件中 16 个判“either_needed”（只洗 KV 与只洗线性层都达部分恢复但均未入参照带）；按数值读作两类缓存各承载一部分损伤（如 N4146 +1：A2 0.45、A5 0.50）。判读表命名不改，报告中并列此读法。
4. 首步 EOS 与 R 指向不同承载者：只洗递推（A3）或只洗 conv（A4）后首步 EOS 在所有条件为 0；只洗 KV（A2）在 N4146 +1（24→16）、N4146 −1（24→24）、V1_L00 −1（24→24）、V0_L00 +1（5→13）仍有 EOS。R 则以 A2 恢复最多（0.45–0.66），A4 最少（约 0.1）。
5. 末位对首 token 的注意力：A0 高于原版（L3 0.21 对 0.09）；损伤最重的 B1 与原版相近（0.11）。sink 注意力被削弱不是本面板的机制（读数粗，推导档）。
6. 阴性对照 L25/N2747 +1 A0 R=0.87，各臂无实质差别，符合预期。

##### 确认面板预测（在任何确认输出出现前冻结）

- 原主预测（合同 §2/§5.2）不改。
- 原衰减预测（合同 §5.3，H-rec 方向）不改。
- P-dev1：A0 首步 EOS ≥ 12/24 的条件中，多数满足 EOS(A3) < EOS(A0) 且 EOS(A2) ≥ EOS(A3)。
- P-dev2：三锚定条件中至少 2 个衰减检验判“reversed”。
- P-dev3：A0 判 failed 的早层条件中，多数判 either_needed。
判读脚本、参照带、档界不变；结果按“成立/不成立/无法判断（分母为 0）”报告。

---


## 时间、运行与停止收据索引

下面是所收集JSON的原有时间字段与状态，不把预计结束时间当实际完成时间。未列时间的文件仍有原件链接。完整JSON全部保存在原文归档，不能以此索引中的标量代替完整嵌套内容。

| 原件 | 原记录状态/阶段 | 原时间字段（原时区） |
|---|---|---|
| [readiness/confirmation-verification-posthoc-r01.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-v1-2026-10-29/readiness/confirmation-verification-posthoc-r01.json) | {"status": "passed_posthoc"} | {"at": "2026-10-29T15:39:40.017801+00:00"} |
| [readiness/cpu-receipt-r01.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-v1-2026-10-29/readiness/cpu-receipt-r01.json) | {"status": "passed"} | {"created_at": "2026-10-29T04:59:11.255474+00:00"} |
| [readiness/cpu-receipt-r02.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-v1-2026-10-29/readiness/cpu-receipt-r02.json) | {"status": "passed"} | {"created_at": "2026-10-29T09:35:31.817216+00:00"} |
| [readiness/cpu-receipt-r03.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-v1-2026-10-29/readiness/cpu-receipt-r03.json) | {"status": "passed"} | {"created_at": "2026-10-29T09:40:47.401749+00:00"} |
| [runs/confirmation-r01/controller.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-v1-2026-10-29/runs/confirmation-r01/controller.json) | {"status": "failed", "stage": "confirmation"} | {"started_at": "2026-10-29T12:10:45.108764+00:00", "finished_at": "2026-10-29T15:36:53.835926+00:00"} |
| [runs/confirmation-r01/worker-0/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-v1-2026-10-29/runs/confirmation-r01/worker-0/receipt.json) | {"status": "completed", "stage": "confirmation"} | {"started_at": "2026-10-29T12:10:45.181919+00:00", "last_record_at": "2026-10-29T15:35:23.010762+00:00", "finished_at": "2026-10-29T15:35:25.080623+00:00"} |
| [runs/confirmation-r01/worker-1/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-v1-2026-10-29/runs/confirmation-r01/worker-1/receipt.json) | {"status": "completed", "stage": "confirmation"} | {"started_at": "2026-10-29T12:10:45.182647+00:00", "last_record_at": "2026-10-29T15:36:50.822879+00:00", "finished_at": "2026-10-29T15:36:52.928230+00:00"} |
| [runs/development-r01/controller.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-v1-2026-10-29/runs/development-r01/controller.json) | {"status": "completed", "stage": "development"} | {"started_at": "2026-10-29T09:45:36.368643+00:00", "finished_at": "2026-10-29T12:08:15.333053+00:00"} |
| [runs/development-r01/verification.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-v1-2026-10-29/runs/development-r01/verification.json) | {"status": "passed"} | {"verified_at": "2026-10-29T12:08:15.332864+00:00"} |
| [runs/development-r01/worker-0/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-v1-2026-10-29/runs/development-r01/worker-0/receipt.json) | {"status": "completed", "stage": "development"} | {"started_at": "2026-10-29T09:45:36.441905+00:00", "last_record_at": "2026-10-29T12:08:11.015446+00:00", "finished_at": "2026-10-29T12:08:13.158814+00:00"} |
| [runs/development-r01/worker-1/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-v1-2026-10-29/runs/development-r01/worker-1/receipt.json) | {"status": "completed", "stage": "development"} | {"started_at": "2026-10-29T09:45:36.442014+00:00", "last_record_at": "2026-10-29T12:05:42.366041+00:00", "finished_at": "2026-10-29T12:05:44.494511+00:00"} |
| [runs/preflight-r01/controller.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-v1-2026-10-29/runs/preflight-r01/controller.json) | {"status": "failed", "stage": "preflight"} | {"started_at": "2026-10-29T09:35:41.459374+00:00", "finished_at": "2026-10-29T09:39:31.512820+00:00"} |
| [runs/preflight-r01/worker-0/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-v1-2026-10-29/runs/preflight-r01/worker-0/receipt.json) | {"status": "running", "stage": "preflight"} | {"started_at": "2026-10-29T09:35:41.529676+00:00", "last_record_at": "2026-10-29T09:39:28.961680+00:00"} |
| [runs/preflight-r01/worker-1/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-v1-2026-10-29/runs/preflight-r01/worker-1/receipt.json) | {"status": "failed", "stage": "preflight"} | {"started_at": "2026-10-29T09:35:41.531293+00:00", "last_record_at": "2026-10-29T09:39:15.777937+00:00", "finished_at": "2026-10-29T09:39:28.368722+00:00"} |
| [runs/preflight-r02/controller.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-v1-2026-10-29/runs/preflight-r02/controller.json) | {"status": "completed", "stage": "preflight"} | {"started_at": "2026-10-29T09:40:47.470688+00:00", "finished_at": "2026-10-29T09:44:43.553907+00:00"} |
| [runs/preflight-r02/verification.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-v1-2026-10-29/runs/preflight-r02/verification.json) | {"status": "passed"} | {"verified_at": "2026-10-29T09:44:43.553784+00:00"} |
| [runs/preflight-r02/worker-0/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-v1-2026-10-29/runs/preflight-r02/worker-0/receipt.json) | {"status": "completed", "stage": "preflight"} | {"started_at": "2026-10-29T09:40:47.543011+00:00", "last_record_at": "2026-10-29T09:44:17.269391+00:00", "finished_at": "2026-10-29T09:44:26.778547+00:00"} |
| [runs/preflight-r02/worker-1/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-v1-2026-10-29/runs/preflight-r02/worker-1/receipt.json) | {"status": "completed", "stage": "preflight"} | {"started_at": "2026-10-29T09:40:47.543138+00:00", "last_record_at": "2026-10-29T09:44:27.248060+00:00", "finished_at": "2026-10-29T09:44:42.143898+00:00"} |

## 全部原始资产入口

本目录在固定提交下共有343个跟踪文件，包含代码、原回答、失败、收据和压缩证据；文件数不是样本数。[逐文件完整账本](../assets/026-early-state-localization-v1-2026-10-29.tsv) · [原目录](https://github.com/yuxiexiong/acupuncture/tree/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-state-localization-v1-2026-10-29)。未复制模型权重、环境或凭据。
