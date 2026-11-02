# QST-01 v1 设计与CPU自查资产

身份：2026-11-02完整设计附件，**不是运行结果或GPU授权**。源证据核对至 `115dc2e9bd73ac4604fdbf1dce2de30fec32c2a2`；新增模型前向0。计划检验同一接收者换入两个不同查询的q/k卷积历史后，完整答案是否跟随供体，以及受针供体是否改变这种作用。

- [完整计划](../../docs/cache-query-state-transfer-plan-v1-2026-11-02.zh-CN.md)：操作、读数、科学出口、工程规则及完整预算。
- [作者自查](../../docs/cache-query-state-transfer-self-check-v1-2026-11-02.zh-CN.md)：设计卡、C01–C14、E01–E26、反例与修订；非独立评审。
- [design-r01.json](design-r01.json)：48完整输入、132配对、36双外来供体主对照、固定预检输入、阈值、资源预算、旧来源哈希。
- [cpu_design_check.py](cpu_design_check.py) / [cpu-check-r01.json](cpu-check-r01.json)：标准库清单与逻辑检查、合成反例，不是模型复现。

从仓库根运行 `python3 experiments/cache-query-state-transfer-design-v1-2026-11-02/cpu_design_check.py`（在其他目录可传脚本绝对路径）。脚本在本目录确定性再生两个JSON，不修改旧证据，不访问网络，不运行模型。

正式拟运行1380条自然轨迹；含固定预检1530，含唯一一次工程预检重试最大1680。实际GPU运行0；缓存重建和数值验收尚未完成。原始面板已见，主比较只覆盖四基础场景，不能把36个接收者或多方向重复当独立题。
