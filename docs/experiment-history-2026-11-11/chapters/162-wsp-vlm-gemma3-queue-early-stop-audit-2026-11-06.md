# 162．Gemma v8 B四轮早停与队列修复

[返回总时间线](../README.zh-CN.md)

**时间定位**：版本/记录日期 2026-11-06；未从所选收据确定完整运行起止，不据目录名补写时刻。

**当时的目的与设计**

B4/30主动停止，原指令允许阴性早停；用户要求继续到累计30轮。保留前四候选与原停止证据，同线程从turn40接续。

**实际过程、结果与后来更正**

四轮主分数15.5172%、16.3793%、16.3793%、15.5172%，原版16.3793%，当时仍选W0。修复v9等待器误把前序早停当退出的问题；turn40接续成功且没有重算基线。ready收据将预计重载写成model_loads=1的计账错误另行更正。

**来源身份**：`wsp-vlm-gemma3-queue-early-stop-audit-2026-11-06`；本章主体来源提交 `2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274`。下方原文中的状态是各文件写作时的状态，不能把早期“尚未运行”覆盖后期正式收据，也不能将后期结果倒填进早期设计。


## 原设计、执行过程、结果与更正全文

以下按“设计与题目 → 工程/执行记录 → 结果/更正 → 其他历史说明”组织；同类内没有可靠时间时保留路径顺序，不冒充严格先后。正文未删段；仅为本章节重排标题层级、把相对链接指向固定提交。原始字节另外完整保存。

### 原件 1：Gemma v8 B早停核查、授权续跑与队列修复

原路径：`experiments/wsp-vlm-gemma3-queue-early-stop-audit-2026-11-06/REPORT.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-gemma3-queue-early-stop-audit-2026-11-06/REPORT.zh-CN.md) · [单独阅读副本](../library/c7617793920a06b0.md)；SHA-256：`c7617793920a06b0489a5d347dc99030a57be5a85fd26f23d10c3a24701e8a99`。

---

#### Gemma v8 B早停核查、授权续跑与队列修复

2026-11-06。v8 B研究者在4/30轮主动提交阴性结果并stop；原指令允许阴性早停，预算未耗尽，不是容量或GPU故障。用户核对后明确选择“继续B至累计30轮，保留此前结果”。本次保留早停证据，恢复同一线程从turn40开始，完成剩余26个不同非零候选的完整评价。

##### 观察与修复

B前4轮主分数依次15.5172%、16.3793%、16.3793%、15.5172%；基线16.3793%。最佳仍为W0，全体正确率43.5345%。第二候选修对7、改错3，但主指标打平且有非零修改，依原选优规则不选；其他候选还触发格式/截断保护。研究者观察到23组空空间子集的92个条件全部答错，四候选未修复；这是已见开发数据诊断，不推出整个模型不能稀疏修复。

v9等待器把前序early_stopped作为异常退出，使两个未开始工程的v9组连带退出。已修改为明确的waiting_gemma_v8_review，保持等待，不绕过科学门禁。6项测试通过，包括failed/early_stopped/controller_failed/paused_by_user均等待审查。旧失败收据和退出PID保留；新v9服务2125523/2125524，本地控制器57718/57720。均证明此前没有模型动作或Astra回合，不存在重放。

##### B同线程接续

[B授权](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-gemma3-queue-early-stop-audit-2026-11-06/B-continuation-authorization.json)覆盖早先允许阴性自愿早停的指令；不要求正结果，但要求累计30轮。原stop请求与回执、研究者回复、轮4状态检查点均保留。

[续跑器](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-gemma3-queue-early-stop-audit-2026-11-06/resume_B.py)复用原Gemma v8 Service、Backend、Candidates、Evidence、Remote和CodexResearcher；不编辑已验收v8引擎。核对原版源码及真实工程收据、完全相同配置/协议、W0已恢复、4轮和39动作、5份完整评分缓存hash、无未完成动作、GPU0空闲且原服务退出。9个边界检查通过（1允许、8拒绝），没有新增测试模型调用。

恢复仅将运行状态research_done从用户已覆盖的主动早停改为继续，原状态存入checkpoint-user-continue-round4。原候选、输入、评分缓存、结果、累计样本/token/CPU预算不变。B后端重建后按需加载，首次新前向才实际加载模型；就绪点加载数为0，不重跑W0或前4轮、不重放39及其他历史动作；Python内存变量重置，保存工作文件仍在，已明确告诉研究者按文件重建。

同一Astra线程`01a1adde-e3b8-7421-ad03-de7238ef0db4`从turn40继续，承接39回合累计2,912,134 token。原4轮停止的receipt保持历史；当前状态看B-continuation-status.json和远端user-continue-B30-ready.json。新服务PID2127635、本地58525，以实际进程为准。v8 C始终正常运行，本次未改动。B恢复search后v9自动回到waiting_gemma_v8，仍须前序结束再进入工程。

模型、输入、评分、保护、选优、批量32和30轮预算均不变；本次是执行边界修复和用户授权接续，不是新科学设计。后续已完成30轮后的报告/冻结/归档收尾失败不再阻塞资源交接，但不得把未完成评价或验收失败冒充完成。半小时心跳已更新最新授权与实际恢复身份。

计账更正：原ready收据的model_loads=1错误地将预计重载当作实测；见B-model-loading-clarification.json。原启动源码和收据保留，修正后源码仅更正计账字段与说明，没有重启运行或改变科学条件。

实际接续验收：同线程turn40完成并成功收到工具反馈，研究者累计token由2,912,134增至3,065,281；B样本仍为2,329，证明没有重算基线/前4轮。C同期推进到4/30；v9两组回到waiting_gemma_v8。详见B-resume-turn40、B-resume-live.json。

---


## 时间、运行与停止收据索引

下面是所收集JSON的原有时间字段与状态，不把预计结束时间当实际完成时间。未列时间的文件仍有原件链接。完整JSON全部保存在原文归档，不能以此索引中的标量代替完整嵌套内容。

| 原件 | 原记录状态/阶段 | 原时间字段（原时区） |
|---|---|---|
| [B-broker-launch.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-gemma3-queue-early-stop-audit-2026-11-06/B-broker-launch.json) | {} | {"time_unix": "2026-11-05T23:15:39.312492+00:00"} |
| [B-controller-launch.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-gemma3-queue-early-stop-audit-2026-11-06/B-controller-launch.json) | {} | {"time_unix": "2026-11-05T23:16:15.501071+00:00"} |
| [B-controller-once.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-gemma3-queue-early-stop-audit-2026-11-06/B-controller-once.json) | {} | {"time_unix": "2026-11-05T23:16:15.529687+00:00"} |
| [B-local-round4/conversation-receipt.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-gemma3-queue-early-stop-audit-2026-11-06/B-local-round4/conversation-receipt.json) | {"status": "stopped_or_frozen"} | {} |
| [B-local-round4/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-gemma3-queue-early-stop-audit-2026-11-06/B-local-round4/receipt.json) | {"status": "stopped_or_frozen"} | {} |
| [B-remote-round4/controller-status.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-gemma3-queue-early-stop-audit-2026-11-06/B-remote-round4/controller-status.json) | {"stage": "finished"} | {"time_unix": "2026-11-05T23:02:27.676347+00:00"} |
| [B-resume-turn40/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-gemma3-queue-early-stop-audit-2026-11-06/B-resume-turn40/receipt.json) | {} | {} |
| [B-resume-turn40/tool_result.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-gemma3-queue-early-stop-audit-2026-11-06/B-resume-turn40/tool_result.json) | {} | {} |
| [B-stop-turn39/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-gemma3-queue-early-stop-audit-2026-11-06/B-stop-turn39/receipt.json) | {} | {} |
| [B-stop-turn39/tool_result.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-gemma3-queue-early-stop-audit-2026-11-06/B-stop-turn39/tool_result.json) | {} | {} |
| [failed-queues/B/controller-status.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-gemma3-queue-early-stop-audit-2026-11-06/failed-queues/B/controller-status.json) | {"stage": "failed"} | {"time_unix": "2026-11-05T23:02:33.655145+00:00"} |
| [failed-queues/C/controller-status.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-gemma3-queue-early-stop-audit-2026-11-06/failed-queues/C/controller-status.json) | {"stage": "failed"} | {"time_unix": "2026-11-05T23:02:39.224479+00:00"} |

## 全部原始资产入口

本目录在固定提交下共有59个跟踪文件，包含代码、原回答、失败、收据和压缩证据；文件数不是样本数。[逐文件完整账本](../assets/162-wsp-vlm-gemma3-queue-early-stop-audit-2026-11-06.tsv) · [原目录](https://github.com/yuxiexiong/acupuncture/tree/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-gemma3-queue-early-stop-audit-2026-11-06)。未复制模型权重、环境或凭据。
