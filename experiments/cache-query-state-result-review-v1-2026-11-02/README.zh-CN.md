# QST-01结果CPU复核与QCO-01预算附件

核对源提交8ecdfe75；新增模型/GPU为0。验证18份QST正式记录的receipt哈希，复算1380轨迹的冻结分析，比对624份QCD参照记录；不是独立模型复现。

- [结果核对及下一阶段计划](../../docs/cache-qst-review-and-common-offset-plan-v1-2026-11-02.zh-CN.md)
- [作者自查](../../docs/cache-qco-self-check-v1-2026-11-02.zh-CN.md)
- [review-r01.json](review-r01.json)：读数、R0单格例外、耗时、来源哈希与QCO全预算。
- [review_qst.py](review_qst.py)：标准库CPU复算。从仓库根运行 `python3 experiments/cache-query-state-result-review-v1-2026-11-02/review_qst.py`；仅再生本目录review-r01.json，不覆盖旧结果或加载模型。

核心核对：无稳定定向转移；U及四方向H_C外来供体各84/84仍答原题。R0 H_T有一条输出变化，但没有跟随供体目标，W仍全0；不能写所有臂逐格完全不变。QST保存的是logits，并无原始q/k距离支持“张量几乎相同”。下一阶段仅提出跨场景共同差分的双向检验，尚未执行。
