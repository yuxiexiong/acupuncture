# 完整研究报告 HTML 扩展

交付：`docs/Acupuncture_实验结果_导师展示_2026-10-28.html`。文件名沿用原入口，页面标注 2026-10-29 更新。

本次只读取归档数据，没有模型加载或新增推理。旧版全部正文、12 张 SVG、脚本及内嵌 MD 保留；原字节快照在 `original-report-20261028.html`。

新增 8 张统计图，以及联合测量、早层深度比较、时段/位置、撤针/重建、局部替换和事实敏感度的解释、设计、结果与研究关系。完整原文查看器内嵌四模型 18,272 份去重来源、联合测量 3,720 份、早层六阶段 11,890 条计划记录（含 676 条不适用）。这些分母不能当作独立样本相加。统计表、原文和合同可离线查询/导出。

用户明确排除正在运行的最新实验结果：缓存定位和公开配方复现仅收录设计，不收录任何阶段原文、统计或结论。缓存定位只读取 `CONTRACT.zh-CN.md`，公开配方只读取 `PROTOCOL.zh-CN.md`。

## 构建与核验

在具备归档数据的仓库根目录执行：

```sh
python3 experiments/advisor-report-v2-2026-10-29/build.py
python3 experiments/advisor-report-v2-2026-10-29/verify_report.py
```

构建复用原报告的 Python/matplotlib 和 macOS 宋体，需要 `zstd`。原 HTML 锁定为 Git `585e2c0a` 中的版本；联合测量与公开配方方案读取主仓库现有归档。输入路径和 SHA-256 逐项记在 `build-audit.json`；重建需要这些来源，不依赖远端运行状态。

`verification.json` 核对旧内容保留、来源哈希、内嵌数据覆盖、完整条件分母、NA、链接、资源离线性及进行中结果排除。浏览器交互验收另见 `browser-verification.json`。`report-extension.md` 是内嵌完整源文档的汇集，不替代主 HTML 的图文解释。

源事实敏感度报告中的 clean S 汇总与 JSON 不一致；HTML 明示重算值与限制，同时保留源报告原文。未修改实验原始结果或历史合同。
