# 既有更新—读取证据CPU审计

[报告](REPORT.zh-CN.md) · [自查](SELF_CHECK.zh-CN.md) · [紧凑结果](summary.json) · [张量审计](tensor-audit.json) · [来源与文件哈希](manifest.json)

仅复算固定旧运行，无模型或GPU调用。原生停止8/12与混合0/12的同协议边际已核清；原生针与V钉入在首个深层GDN核心交互上不同，未证明该差异决定最终回答。先读报告§6的缺口，再决定具体新实验。

本地重算汇总：`python3 experiments/cache-update-readout-audit-v1-2026-11-01/summarize.py`。

`audit_cpu.py`只读取归档服务器既有张量，须以`CUDA_VISIBLE_DEVICES=''`在CPU执行；stdout保存为`tensor-audit.json`。原大张量不入Git，不运行源目录中的历史实验代码。完整来源身份与重构容差见报告。
