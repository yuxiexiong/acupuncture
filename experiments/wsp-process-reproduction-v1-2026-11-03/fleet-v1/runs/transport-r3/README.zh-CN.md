# 0.8B 数学 turn048 传输中断恢复

2026-11-04，北京时间14:41巡检发现控制器退出。用户此前明确授权在原预算内修复可恢复工程故障。范围仅0.8B数学；4B数学已完成阴性，两个编程实验继续暂停。

## 真实实验进展

已完成19/50成功forward。最近一次turn046为48题×5采样，original/edited各240回答，上限32768；完整动作2044秒。原模型24/240正确，edited0/240正确，所有edited输出触顶，有重复数字与短语退化。该候选有害，编辑器在turn047/048已拒绝它，拟降低增益并分析自然重复。没有可靠阳性，不将这支候选失败等同整轮结束。

## 故障及排查

SSH日志为Connection reset by peer / Broken pipe。控制器针对下一条CPU动作turn048未找到保存响应而停止；没有自动重放动作。复查SSH还遇到多次banner exchange超时，独立连接ConnectTimeout=60后恢复；服务器正常、无实验GPU进程。

14:46在broker锁内确认：turn048动作目录不存在；没有其他缺响应动作；state与turn047已保存响应完全相同（Python25、forward尝试20、成功19、GPU秒10633.769173476845）；该CPU代码拟写出的natural_repetition_scores.npy也不存在。由broker实现的先建动作目录、先记Python尝试再执行顺序，可以判定此动作未被接受，不是执行到一半且丢失响应。

reconcile.py在再次核对上述条件后，仅保存原动作身份、SHA和未执行失败响应，未执行其代码、未重放模型、未改权重或消耗计数。初始失败日志、原请求与核查收据留在transport-r3，服务器对应动作目录保留transport-reconciliation.json。编辑器收到“请求未执行、内核变量已丢失、需从自己的保存文件恢复”这一事实，不提供作者解法。

## 恢复

沿用现有controller.py及resume_after_fleet.py，无产品代码改动。CONFIG_GATE_OK；新版本配置resume_completed_turn=48，同thread从turn049继续。50成功pass和28800GPU秒上限不变；已用10633.769173秒，剩余18166.230827秒约5.046GPU小时，不能当作完成ETA。

新实时根external/wsp-fleet-v2/math-0p8b-author-aligned-r2。启动时launcher PID70732、controller PID70747。旧author-aligned状态和失败日志不覆盖；半小时监控已更新到新根，仅单项续跑，不启动旧fleet或其他实验。原实验日志仍在external/wsp-fleet-v1/math-0p8b/experiment。

本记录属于传输故障恢复，不新增科学设计、测试面板或资源预算。自动审批此前拒绝的作者压缩证据包继续留本地，本次只交付经检查的简洁恢复代码、配置和收据。
