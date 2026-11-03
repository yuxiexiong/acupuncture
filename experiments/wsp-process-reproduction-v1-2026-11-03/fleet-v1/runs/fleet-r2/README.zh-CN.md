# 车队断线恢复记录

原车队在0.8B数学首个forward仍运行时SSH断线，随后因残留broker锁将后三项记录为工程跳过。第一pass在服务器正常完成，所有原始证据保留。

本次仅修复Mac控制器的传输恢复：核对action哈希、等待原broker退出、读取已保存结果，不重新执行不确定action。新增显式续接入口，沿用原Astra会话、pass计数和预算。SSH复用连接减少重复连接。未改变模型、采样、题集、精度、权重或GPU预算；没有新增GPU验收。测试覆盖不重复执行、缺失结果拒绝、原会话续接，连续队列6项检查通过。

恢复队列沿用原授权，状态文件为external/wsp-fleet-v2/state.json。0.8B数学实验目录仍在external/wsp-fleet-v1/math-0p8b/experiment，其余新本地目录在v2。服务器目录与原预算不变。

实际恢复已取回turn-002结果，并执行turn-003至005的CPU分析；turn-006被编辑器服务端以提示词政策检查拒绝（原始事件见math-0p8b-editor-rejection.jsonl）。未尝试绕过，0.8B数学以工程阻断保留1/50 pass，非阴性或完成。队列按用户规则继续4B数学；具体时点见status-snapshot.json。后续不得把已跳过项目当作完成，也不得自动重复其GPU调用。

性能审计见[首pass实测](../fleet-r1/PERFORMANCE.zh-CN.md)：17分钟中14.76分钟为385万token生成；未取得数倍提速结果。当前修复减少断线造成的流程损失，不宣称改善模型吞吐。
