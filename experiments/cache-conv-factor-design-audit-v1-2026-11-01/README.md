# 卷积材料计划：旧证据核对与离线设计检查

[审计结果](REPORT.zh-CN.md) · [实验计划及自查](../../docs/cache-conv-value-qk-readout-plan-v1-2026-11-01.zh-CN.md) · [矩阵](design.json) · [检查结果](design-check.json) · [文件清单](manifest.json)

本目录是已完成的CPU核对及未执行计划，不是新模型实验结果。0模型调用、0GPU。

标准库可复算E2及设计检查；输出写新文件，保留原记录：

```sh
python audit_e2.py /path/to/checkout-of-233ab58 > /tmp/e2-audit-recheck.json
python check_plan.py
```

`read_saved_logits.py`为本次服务器实际使用的脚本，只CPU加载旧张量，不实例化模型。复算需原服务器的`/workspace/acupuncture`归档，以及将仓库`experiments/cache-output-path-audit-v1-2026-11-01/input-manifest.json`置于脚本固定的`/tmp/acupuncture-output-path-audit-20261101-r01/input-manifest.json`。该manifest的来源由旧报告固定，脚本逐文件检查记录及张量SHA。

```sh
CUDA_VISIBLE_DEVICES='' OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 python read_saved_logits.py > /tmp/saved-logits-recheck.json
```

保存的`seconds`是当次CPU墙钟，复算不会逐字相同。`cpu-execution.log`仅为SSH连接提示。`installed-conv-source.txt`记录当时安装源码SHA、相关代码片段及配置，非完整模型源码；新runner仍需实际路径验收。
