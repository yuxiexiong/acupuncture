# Gemma v9 C：30轮最终交付

2026-11-06 19:14，C完成30个不同非零候选完整开发评价，机制报告记录成功，冻结R28并正常退出。未运行第31轮。服务2386898与本地控制器45613退出已实测；GPU0无计算进程，仅3MiB驻留。其他项目未被干预。

最终R28 `c-58e249de16eeca1aa958e979e07beb5a6423db5cd815a3de9c37fa757730a4d1`：主分数33.984375%→36.328125%（+2.34375pp），全体79.140625%→79.7265625%，修对22/改错7，保护通过。修改L15 MLP down_proj原64列方案的61列互补部分，156137个实际BF16标量，L2=2.0688491019。完整说明见[四组比较](../../wsp-gemma-v8-v9-final-comparison-2026-11-06/REPORT.zh-CN.md)。

[冻结原件](frozen-candidate.json)明确为development selection pending reload/new confirmation。[机制报告原件](mechanism-report.json)记录成功不等于自动机制验证、独立审查或独立泛化。R28同路径局部写入吻合预测，但七探针有一条正式修复未在fresh诊断复现；方向随机控制和拆分反例均保留。

## 成本与停止

最终目标样本79890、目标tokens21090336、Python CPU111.099139677秒、Astra线程累计24273799 tokens（含缓存输入）。工程133生成/142前向另计。失败turn99单次usage未知，不填0；累计线程成本保留。收尾turn144 CPU汇总发生字典类型错误，145核对、146纠正成功，无目标前向重放或模型重启；147机制报告、148冻结成功，原始错误及partial未删除。

[C恢复结束回执](C-continuation-receipt.json)、[最终状态](C-continuation-status.json)、[远端实测](remote.json)、[本地实测](local.json)共同确认结束。科学评价与收尾ETA均已结束；本次收尾只进行CPU/网络归档。19:15工作盘117.128GiB；v9 B1.218/C2.795GiB，各低于12GiB，余量高于20GiB。未清理证据。

## 原始证据与复算

[archive-sha256.json](archive-sha256.json)列出两个压缩档案的整包SHA及有序分片；按`parts_in_order`顺序拼接即可还原tar.gz，不按时间或字典猜顺序。远端证据含原始回答、完整评分、动作/失败/partial、候选清单、研究工作文件、机制报告及冻结；研究者轨迹含所有本地原生回合、回答、收据和失败。完整压缩档本地同时保留在external对应delivery-final-C目录。

权重、捕获数组等大型二进制（npy/npz/pt/pth/safetensors）保留远端原路径，不进Git；[逐文件manifest](C-remote-file-manifest.json)记录全部文件SHA、大小、是否包含和原路径，冻结补丁文件SHA已与manifest对账。这里不声称这些排除的二进制已下载。

[verify.py](verify.py)可直接离线核验分片和整包、每个纳入的远端文件、31份完整评分、科学完成与最终缓存一致、选中/报告/冻结身份一致及停止快照。[verification.json](verification.json)为本次通过结果。诊断、基线和部分评价不计30轮。四组既有档案及最终结果统一在[总入口](../../wsp-gemma-v8-v9-final-comparison-2026-11-06/REPORT.zh-CN.md)。

所有结果为已见开发集选择。本次不恢复Qwen、旧Gemma或其他已结束队列，不新增模型实验。
