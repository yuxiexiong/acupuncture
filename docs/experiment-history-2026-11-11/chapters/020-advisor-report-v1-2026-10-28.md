# 020．首次导师报告与旧记录核对

[返回总时间线](../README.zh-CN.md)

**时间定位**：版本/记录日期 2026-10-28；未从所选收据确定完整运行起止，不据目录名补写时刻。

**当时的目的与设计**

把已完成的随机针、剂量和迁移等旧资料整理为展示报告；工作对象是已有Markdown、回答账本和收据。

**实际过程、结果与后来更正**

只做历史材料分析，没有新增模型推理。审计修正了N667与N1741的个别计数表述，明确迁移结构化行为终点未判定，并保留停止的Llama记录边界。此项是报告交付，不是一轮新插针。

**来源身份**：`advisor-report-v1-2026-10-28`；本章主体来源提交 `7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8`。下方原文中的状态是各文件写作时的状态，不能把早期“尚未运行”覆盖后期正式收据，也不能将后期结果倒填进早期设计。


## 原设计、执行过程、结果与更正全文

以下按“设计与题目 → 工程/执行记录 → 结果/更正 → 其他历史说明”组织；同类内没有可靠时间时保留路径顺序，不冒充严格先后。正文未删段；仅为本章节重排标题层级、把相对链接指向固定提交。原始字节另外完整保存。

本目录没有已收集的Markdown说明；本章按现存JSON身份记录，不为它编造方案或科学结论。完整JSON见收据索引和无损归档。


## 时间、运行与停止收据索引

下面是所收集JSON的原有时间字段与状态，不把预计结束时间当实际完成时间。未列时间的文件仍有原件链接。完整JSON全部保存在原文归档，不能以此索引中的标量代替完整嵌套内容。

| 原件 | 原记录状态/阶段 | 原时间字段（原时区） |
|---|---|---|
| [audit.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/advisor-report-v1-2026-10-28/audit.json) | {"status": "ANALYZED", "new_model_inference": false, "scope": "Existing MD, raw JSONL counts, receipt/trace and historical result cross-check; no model rerun."} | {} |

## 全部原始资产入口

本目录在固定提交下共有2个跟踪文件，包含代码、原回答、失败、收据和压缩证据；文件数不是样本数。[逐文件完整账本](../assets/020-advisor-report-v1-2026-10-28.tsv) · [原目录](https://github.com/yuxiexiong/acupuncture/tree/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/advisor-report-v1-2026-10-28)。未复制模型权重、环境或凭据。
