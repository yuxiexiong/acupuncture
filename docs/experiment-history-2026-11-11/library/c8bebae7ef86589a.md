# DIV-01 第零步：4B L0 阈值附近同范数分裂普查

历史原件；不是本次提出的假设、论证或运行要求。

原路径：`experiments/div01-threshold-split-survey-v1-2026-11-03/PROTOCOL.zh-CN.md`。来源：[固定提交原件](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/div01-threshold-split-survey-v1-2026-11-03/PROTOCOL.zh-CN.md)；SHA-256：`c8bebae7ef86589a8b5a73a3ea6fc0c7d76ef5f65145bf3e05bad8e1d530c539`。精确字节见原文归档。

---

# DIV-01 第零步：4B L0 阈值附近同范数分裂普查

2026-11-03。目的：为 DIV-01（同范数分岔定位）找配对对照。9B/4B/2B L0 在剂量 +1 下 30 个通道无一干净（9B 的"0/8"全是单 token 崩溃），故在 4B L0 阈值附近重找。

- 模型/层：Qwen3.5-4B，第 0 层；沿用剂量调查冻结的 down_proj 前置钩子，唯一改动是剂量白名单加入 0.75。
- 通道：已有 10 个 + 按种子 `acupuncture-div01-v1:4b:0` 新抽 10 个（排除已有）。抽样在看结果之前。
- 剂量：0.5、0.75；题目 Q01–Q08；贪心，128 新 token。
- 复现闸：每卡先跑对照（基线 ×8、N4146@0.5 ×8），与存档 token 逐位一致才继续。
- 判据见 contract.json 与 rubric.py；判据已在存档真实记录上预演，能判出 CLEAN、STOP、OTHER。
- 够数闸：同一剂量下 STOP ≥3 且 CLEAN ≥3 即通过；两档都不过就停，不加剂量、不换题。
- 不测深状态与 logits。
