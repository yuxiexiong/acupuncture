# 缓存形成机制 CFM：计划命名与有效版本

日期：2026-10-31。CFM专指本轮“稀疏干预怎样改变写入、旧状态处理，并在撤针后影响回答”的分阶段机制研究。阶段编号只在此前缀内使用，不与历史实验共用简称。

| 唯一编号 | 实验/计划全名 | 当前状态 |
| --- | --- | --- |
| CFM-S1-v1-20261031 | [原始轨迹与状态形成分析](cache-formation-mechanism-s1-native-trace-plan-v1-2026-10-31.zh-CN.md) | 已完成；36条正式轨迹，执行方verification passed；见下方结果复核 |
| CFM-S2-v2-20261031 | [写入与旧状态处理的形成检验 v2](cache-formation-mechanism-s2-formation-test-plan-v2-2026-10-31.zh-CN.md) | 当前设计；依据S1修订；原生时序＋旧差异/新写入/处理分账；未执行 |
| CFM-S3-v2-20261031 | [形成变化到读取与回答的检验 v2](cache-formation-mechanism-s3-readout-behavior-plan-v2-2026-10-31.zh-CN.md) | 当前条件式设计；先行为预测检验、后有条件路径归因；未执行 |

[S1结果复核、v2修订依据与自审](cache-formation-mechanism-s1-result-review-v1-2026-10-31.zh-CN.md)；[S1执行结果](https://github.com/yuxiexiong/acupuncture/tree/eb5232ce9c43eea566141bccd1081c3dc2021734/experiments/cache-formation-mechanism-s1-native-trace-v1-2026-10-31)。原[设计Review v1](cache-formation-mechanism-design-review-v1-2026-10-31.zh-CN.md)是S1结果公布前的历史审查。S1完成不代表S2/S3已执行或GPU已获新授权。

## 旧名称与旧方案怎样处理

- CFM-S2-v1、CFM-S3-v1：已被对应v2替代，旧文本保留，不再作为当前执行计划。阶段一原合同和结果不追改；其coupled判读保留为历史记录，不再当成针特异机制或后续入场门槛。
- `cache-mechanism-stage1-native-trace-plan-2026-10-31.zh-CN.md`：**旧名称已停用**，文件仅作跳转；当前有效内容是CFM-S1。这是更名，不是撤销该实验。
- 2026-10-29“早层失效定位第一阶段”：已完成历史实验，原协议/结果/收据保留，显示时加日期和“历史已完成”；不标作废。
- 2026-10-30“全层缓存差分与阶段二深度比较”：已完成历史实验，原文件路径和冻结身份保留；不是CFM-S2，不标作废。
- 2026-10-31的r01写入/更新交换、r03单换value/衰减及r04补偿/S-O网格：**作为当前执行计划已被CFM系列替代，不得直接执行**。原文及r02/r04审查保留供追溯；数学分析、设计反例和已取得资产不随旧运行方案过期而作废。
- 缓存机制Proposal、related work和已完成数据分析：仍是研究资产，不是过期实验，也不因CFM更名而作废。

核对结果：当前S1旧文件名没有与历史文件完全同名，冲突在“阶段一/二”的口头简称。因此不批量改名已完成的冻结实验目录；通过CFM唯一编号、新标题和旧入口停用说明解决混淆。

后续新版本改`v2`并写明替代对象；任何正式执行另建带`cfm-s1/2/3`、版本和日期的实验目录及冻结收据。当前不创建空运行目录，不把未执行计划伪装成实验批次。
