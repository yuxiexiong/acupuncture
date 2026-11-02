# QCD-01 设计来源与预算核对（零模型运行）

日期：2026-11-02。此目录仅存设计依据，不是QCD实验结果。

- [计划](../../docs/cache-coverage-dose-plan-v1-2026-11-02.zh-CN.md)
- [作者自查](../../docs/cache-coverage-dose-self-check-v1-2026-11-02.zh-CN.md)
- [来源、CPU复算及最终预算](source-audit-and-budget-r01.json)

以远端50bbdc51为基线读取QC合同、报告、runner、token审计及回执。调用既有qc_analysis.load_all/ analyse，逐键与analysis/qc-readouts-r01.json比较，全部相等；独立遍历两个worker回执核对276份正式记录的SHA256。复算是同一助手调用同一冻结判读代码，不是独立统计方法或模型复现。供体数值辅助量由记录中的C_nat.first与C_nat.diag.watch直接计算，没有读取完整缓存或启动模型。附件中source_sha256固定本次使用的来源。

预算依据108文本的既有token审计：宽长度总和2895（87×27＋21×26），两个预检文本均L=27；G形成步数Σ(9L+100)，S为Σ20L。自然轨迹G为每文本46，S为每文本40；预检另计，LA额外重建C/T两次。共3742形成、9462自然轨迹与9462诊断，96575个形成token前向、220预填/7609预填token，最多302784解码前向。此处全部是拟运行算术，不是完成收据。

只读CPU核对的失败尝试和修复在JSON的audit_attempts列出。基础知识审计原文件来自canonical本地仓库，逐字节补交远端；没有重写其历史结论。无新模型/GPU计算、无运行命令、无运行授权。

基础审计保留原样，其中三处历史本地链接尚未随原分析归档远端。本轮没有使用这些缺失分析的新数值支持QCD结论，不递归迁入整条旧实验线。两份源码/回执另有已核对SHA256完全相同的远端版本：[stage2.py](../early-state-localization-stage2-v2-2026-10-30/stage2.py)、[II-B回执](../early-state-localization-stage2-v2-2026-10-30/runs/b_validate-r01/worker-0/receipt.json)；路径审计笔记仍在canonical本地docs目录，其原链接保留为历史来源，不声称本轮远端可读。具体缺失路径列于JSON的historical_reference_delivery。QCD计划、自查和本轮结果附件的直接链接均核对存在。
