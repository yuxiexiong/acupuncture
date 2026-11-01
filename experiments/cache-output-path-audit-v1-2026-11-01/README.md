# 原生输出路径：旧数据CPU分析

[结果与下一切入点](REPORT.zh-CN.md) · [设计自查](SELF_CHECK.zh-CN.md) · [汇总](summary.json) · [逐层表](layer-accounting.csv) · [来源](input-manifest.json)

全部为已有BRIDGE/LOCAL张量的探索性分析，0模型前向、0GPU。原生与混合背景分开；固定词对、动态赢家、最终尺度及舍入分开。投影不是因果贡献。原“当前入口×深层历史缺格”建议已因遗漏E2 d撤回，见[后续更正](../cache-conv-factor-design-audit-v1-2026-11-01/REPORT.zh-CN.md)；原始数值不变，新计划未运行。

在原归档服务器，用既有torch/safetensors环境复算：

```sh
CUDA_VISIBLE_DEVICES='' OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 python analyze_cpu.py input-manifest.json > readouts-r02.json
```

该脚本只CPU读取旧文件和静态输出权重，源路径固定在脚本；不会加载模型。复算时请输出到新目录，保留已交付结果。

本地仅需Python标准库：

```sh
python summarize.py
python verify.py /path/to/checkout-of-2699a9c
```

`readouts-r01.json`是第一轮分析快照；`readouts-r02.json`补充赢家两侧和已有全注意力输出分解。公共13,526字段一致，最终以r02为准。两个execution日志只有连接提示，无模型运行输出。
