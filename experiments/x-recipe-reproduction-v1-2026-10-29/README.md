# 4B 公开配方复现：每配置五题，每题128新token

**2026-10-30：正式1,170条采集已完成并核验。** 用户批准后（[formal_approval.json](formal_approval.json)，冻结哈希一致）双卡各585条于北京时间20:33–21:40运行，两片退出码0、`verify`均为completed，两片合并恰等于完整排程（1,050插针＋120原版，无重复）。结束原因：原版EOS 33／满128 87，插针EOS 352／满128 698。结果在[run-gpu0-r01](run-gpu0-r01)与[run-gpu1-r01](run-gpu1-r01)；并排报告尚未撰写。

入口：[实验设计](DESIGN.zh-CN.md) · [全部配方和题目](RECIPE_CATALOG.zh-CN.md) · [GPU Ready验收](GPU_READY.zh-CN.md)。

## 固定范围

| 项目 | 数量 |
|---|---:|
| 历史完整配置记录 | 50 |
| Neuronary快照内4B记录 | 178 |
| 备注里的完整变体 | 4 |
| 来源记录合计 | 232 |
| 完全重复来源记录 | 22 |
| 待执行不同配置 | 210 |
| 每配置题数 | 5 |
| 干预回答 | 1,050 |
| 按题目和有效解码去重的原版回答 | 120 |
| 正式生成调用合计 | 1,170 |
| 不同英文提示 / 有效解码组 | 47 / 10 |

每条回答最多128个新token，遇EOS正常提前结束。每个配置使用三道共同题和两道中性情境题；完整原版对照与失败记录均保留。配方是推理时MLP通道加法干预，不写模型权重。

## 可核查材料

- [执行协议](PROTOCOL.zh-CN.md)、[运行约定](contract.json)。
- [当前来源更新](public_source_updates.zh-CN.md)、[来源核对数据](public_source_updates.json)。本轮X浏览器不可用，用户已同意继续使用历史记录与公开仓库；没有声称重新抓全X评论区。
- [210个执行配置](recipes.json)、[232条来源到执行配置的映射](catalog.json)。
- [最终47题及中文译文](questions.json)、[全部来源条目的题目设计](question_design.json)。
- [历史50个配置](prior_recipes.json)、[公开187条参数快照](sources/neuronary_parameter_snapshot.json)、[4个完整变体](sources/additional_notes_variants.json)、[重复及缺失参数核对](sources/eligibility_audit.json)。9条其他模型配置不执行；旧待补清单15项中2项已由新资料补齐，其余13项仍标记缺失。
- [模型运行器](run_recipes.py)、[多通道干预实现](recipe_engine.py)、[参数合并脚本](build_manifest.py)、[CPU测试](test_recipe_runner.py)。
- [资源核查](resource-availability-2026-10-29.json)。

已生成并验证`scales.json`和`freeze.json`。正式数据的`receipt.json`必须完成，退出状态必须成功，全部配置与原版对照通过完整性校验，才能标记采集完成。报告和并排原文会在这些实际结果产生后生成；不以来源标签预先判断复现成功。

## 本次实现与外部原实验的边界

目标固定为Qwen3.5-4B revision `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`，BF16、关闭thinking。11条新配方明确要求逐提示clean lower-median校准；其余配置采用作者公开的固定参考文本回退。作者私有32层统计未公开，缺失的历史解码设置采用已声明的greedy/重复惩罚1。本轮保持每条已公布的温度、重复惩罚及过滤设置，使用HF生成器；不声称逐token重放作者的CPU随机抽样结果。

五题结果用于观察具体场景下的变化，不把某个配方名认证为稳定人格或天然功能区。历史停止的Q25–40、其他模型和静态参数修改不属于本轮。
