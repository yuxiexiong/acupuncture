# 106．DIV：阈值附近的STOP/CLEAN分裂第零步

[返回总时间线](../README.zh-CN.md)

**时间定位**：已提取运行收据的最早时间锚点（可含预检） 2026-11-03T18:16:20.232549+08:00；不能当作全部子运行起止。

**当时的目的与设计**

按预定剂量和输入寻找同范数但行为分裂的条件，先过够数闸再考虑后续比较。

**实际过程、结果与后来更正**

完成336条，第零步够数闸FAIL，未形成需要的STOP/CLEAN对照，按合同停止。不是理论假设已被否证，也不能把离散剂量结果写成所有通道精确阈值。

**来源身份**：`div01-threshold-split-survey-v1-2026-11-03`；本章主体来源提交 `7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8`。下方原文中的状态是各文件写作时的状态，不能把早期“尚未运行”覆盖后期正式收据，也不能将后期结果倒填进早期设计。


## 原设计、执行过程、结果与更正全文

以下按“设计与题目 → 工程/执行记录 → 结果/更正 → 其他历史说明”组织；同类内没有可靠时间时保留路径顺序，不冒充严格先后。正文未删段；仅为本章节重排标题层级、把相对链接指向固定提交。原始字节另外完整保存。

### 原件 1：DIV-01 第零步：4B L0 阈值附近同范数分裂普查

原路径：`experiments/div01-threshold-split-survey-v1-2026-11-03/PROTOCOL.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/div01-threshold-split-survey-v1-2026-11-03/PROTOCOL.zh-CN.md) · [单独阅读副本](../library/c8bebae7ef86589a.md)；SHA-256：`c8bebae7ef86589a8b5a73a3ea6fc0c7d76ef5f65145bf3e05bad8e1d530c539`。

---

#### DIV-01 第零步：4B L0 阈值附近同范数分裂普查

2026-11-03。目的：为 DIV-01（同范数分岔定位）找配对对照。9B/4B/2B L0 在剂量 +1 下 30 个通道无一干净（9B 的"0/8"全是单 token 崩溃），故在 4B L0 阈值附近重找。

- 模型/层：Qwen3.5-4B，第 0 层；沿用剂量调查冻结的 down_proj 前置钩子，唯一改动是剂量白名单加入 0.75。
- 通道：已有 10 个 + 按种子 `acupuncture-div01-v1:4b:0` 新抽 10 个（排除已有）。抽样在看结果之前。
- 剂量：0.5、0.75；题目 Q01–Q08；贪心，128 新 token。
- 复现闸：每卡先跑对照（基线 ×8、N4146@0.5 ×8），与存档 token 逐位一致才继续。
- 判据见 contract.json 与 rubric.py；判据已在存档真实记录上预演，能判出 CLEAN、STOP、OTHER。
- 够数闸：同一剂量下 STOP ≥3 且 CLEAN ≥3 即通过；两档都不过就停，不加剂量、不换题。
- 不测深状态与 logits。

---

### 原件 2：DIV-01 第零步报告：4B L0 阈值附近同范数分裂普查

原路径：`experiments/div01-threshold-split-survey-v1-2026-11-03/REPORT.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/div01-threshold-split-survey-v1-2026-11-03/REPORT.zh-CN.md) · [单独阅读副本](../library/fa57d51c5782489f.md)；SHA-256：`fa57d51c5782489f47f3d48829cb550b3d4664973b3a1467f1ac7f58598ee0e5`。

---

#### DIV-01 第零步报告：4B L0 阈值附近同范数分裂普查

2026-11-03。合同 `contract.json`，冻结哈希 `freeze.json`（10:16:10Z）。两卡共 336 条，复现闸 16/16 逐位一致，钩子已移除、权重哈希不变。

##### 判定（按合同）

**够数闸 FAIL。** 0.5：STOP 5（N3846/3959/6137/7542/9105）、CLEAN 0、OTHER 15。0.75：20/20 STOP。按停止条件，本轮到此为止，不加剂量、不换题。

失败类型：**没拿到结果**（合同执行完整，但对照集凑不出来）。这不是对 DIV-01 假设的否证。

##### 描述性观察（合同外，不当判据）

1. **EOS 阈值在全部 20 个通道上都落在 0.5–0.75 这一窄带里**：0.75 剂量下所有通道都是 8/8 EOS，在册的 1.0 剂量下 L0 是 10/10。同范数下，方向只能在小于 1.5 倍的剂量区间里移动阈值位置，而不决定"停或不停"。这对 DIV-01 的前提不利：L0 的停止主要由写入幅度决定，方向调节的是阈值。
2. **在 0.5 剂量下不停的通道，大多也不干净**：15 个 OTHER 中有 9 个以 COLLAPSE 或 EOS 为主。接近干净的有 N1210、N2191、N383、N915、N6547，各自在 1–2 题上崩溃或答错。N1210 和 N4146 是 CFM 深挖过的通道。
3. **结局在通道内部按题变化**：例如 N8883 在 5 题上 EOS、2 题上 OK。在 0.5 剂量下，Q08 有 10 个通道 OK、3 个 EOS；Q04 有 6 个 OK、10 个 EOS；Q02 有 7 个 OK、5 个 EOS。

##### 对下一步的含义（待用户裁决，未执行）

- 整通道配对在 L0 走不通：要么全停，要么残损。
- 可选一：改用**(题, 通道)配对**。同题、同剂量 0.5、同范数下，比较 EOS 与 OK 两种结局（Q02/Q04/Q08 各有 ≥5 对）。需要另立实验卡。
- 可选二：把 DIV-01 的对象从"停与不停"改为"**各通道自己的阈值位置**"，因变量是触发 EOS 所需的剂量。这与观察 1 一致，也更直接地检验特异性。

---


## 时间、运行与停止收据索引

下面是所收集JSON的原有时间字段与状态，不把预计结束时间当实际完成时间。未列时间的文件仍有原件链接。完整JSON全部保存在原文归档，不能以此索引中的标量代替完整嵌套内容。

| 原件 | 原记录状态/阶段 | 原时间字段（原时区） |
|---|---|---|
| [run-r01/w0/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/div01-threshold-split-survey-v1-2026-11-03/run-r01/w0/receipt.json) | {"status": "completed"} | {"started_utc": "2026-11-03T10:16:20.232569+00:00", "ended_utc": "2026-11-03T10:19:35.996815+00:00"} |
| [run-r01/w1/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/div01-threshold-split-survey-v1-2026-11-03/run-r01/w1/receipt.json) | {"status": "completed"} | {"started_utc": "2026-11-03T10:16:20.232549+00:00", "ended_utc": "2026-11-03T10:22:16.969986+00:00"} |

## 全部原始资产入口

本目录在固定提交下共有351个跟踪文件，包含代码、原回答、失败、收据和压缩证据；文件数不是样本数。[逐文件完整账本](../assets/106-div01-threshold-split-survey-v1-2026-11-03.tsv) · [原目录](https://github.com/yuxiexiong/acupuncture/tree/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/div01-threshold-split-survey-v1-2026-11-03)。未复制模型权重、环境或凭据。
