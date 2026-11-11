# 164．Gemma v9额度故障与C剩余十轮恢复

[返回总时间线](../README.zh-CN.md)

**时间定位**：版本/记录日期 2026-11-06；未从所选收据确定完整运行起止，不据目录名补写时刻。

**当时的目的与设计**

B已30轮、C20轮时研究者账户额度耗尽；用户恢复额度后仅接续C，不重启B和旧队列。

**实际过程、结果与后来更正**

B无合格改善仍选W0，缺报告/冻结按用户豁免保留；C从已提交未评的21轮继续，后完成30轮，最终R28主36.328125%、全体79.7265625%、修22错7。恢复、逐次控制、最后一轮及最终收尾原文全部保留，不把过程快照当最终结果。

**来源身份**：`wsp-vlm-gemma3-v9-quota-recovery-2026-11-06`；本章主体来源提交 `2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274`。下方原文中的状态是各文件写作时的状态，不能把早期“尚未运行”覆盖后期正式收据，也不能将后期结果倒填进早期设计。


## 原设计、执行过程、结果与更正全文

以下按“设计与题目 → 工程/执行记录 → 结果/更正 → 其他历史说明”组织；同类内没有可靠时间时保留路径顺序，不冒充严格先后。正文未删段；仅为本章节重排标题层级、把相对链接指向固定提交。原始字节另外完整保存。

### 原件 1：Gemma v9 C：额度恢复后接续至30轮

原路径：`experiments/wsp-vlm-gemma3-v9-quota-recovery-2026-11-06/README.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-gemma3-v9-quota-recovery-2026-11-06/README.zh-CN.md) · [单独阅读副本](../library/164921e25d4be319.md)；SHA-256：`164921e25d4be3195490032869774696e3d246eab499877dacfe3f38752674d2`。

---

#### Gemma v9 C：额度恢复后接续至30轮

用户明确回复“额度已恢复，接续 C”。仅恢复C，保留此前20个完整非零候选、21份含W0的完整评分及原线程。B已30轮不重启；其冻结/研究者机制报告缺失按已有收尾豁免如实归档。

14:16 C turn99因账户usage limit失败，无回答、usage回执或远端动作；最后turn98已提交第21候选但未评价。失败原件保留，下一回合turn100。同Astra/max、同W0/协议/模型/评分/batch32、累计14795788研究者token承接；失败单次用量未知，不填0。Python内存重建，工作文件保留。不重新提交21、不重算W0、不重放历史动作。总目标仍30，最后须对应实际最佳的机制报告/冻结/停止。若仅收尾失败，保全后释放，不新增第31轮。

复用auth-recovery恢复器，改为v9 targeted合同与精确边界。工程验收原件与源码24项必须继续通过；恢复入口检查原state完整相等、最后action预算一致、无pending/partial、评分逐SHA、旧PID已退出、原协议hash一致。新增CPU边界测试通过不等于新模型验收；复用原真实验收，不伪改。

依据用户显存充足可并行授权，GPU0只容许已核对PID2372133（启动时刻和cmdline SHA同时绑定）或空卡，两次空闲至少56GiB检查，本组共享锁和队列锁。该进程为其他项目behav_many评价，初始占约14.4GiB，Gemma C已测峰值14.682GiB；本次不暂停/修改它。陌生PID或身份变化拒绝准入；不要求整卡空闲。全盘仍保留至少20GiB，各组12GiB，启动需38GiB余量。采样非未来峰值保证。

仅一次用户授权后的接续，若再次容量失败保留并报告，不自动重复。ready处backend懒加载计0，首次新前向才加载。原CLI SHA未变，不改原配置/验收。状态以本目录C-continuation-status和真实PID为准。

##### 准入复查修正

恢复等待期间GPU0新增已核实评价进程2384262/2384263，各约14.4–14.6GiB，原2372133仍在；空闲由80.8降至51.7GiB。r1仅在waiting阶段，无ready、无turn100、无模型/研究者调用；保全停止记录后替换为resume_C_r2.py。准入核对三进程各自启动时刻及cmdline SHA，40GiB空闲两检，按Gemma已测14.682GiB峰值预留约25GiB门槛余量；陌生进程仍拒绝。只改准入名单/余量及一次性启动记录后缀，模型/评分/研究条件不变。test_recovery_r2通过。最新C-broker-launch与C-controller-launch为准，r1原件保留。

##### 首次在线验证

新broker2386898/controller45613，原线程turn100成功，14998059累计tokens，36.33秒整回合；额度已在线验证。工具核对第21已提交候选成功，未重新提交/评价W0，新增目标样本0。失败99单独用量仍不能从累计差分中分离，不能填0。ready收据模型加载0，须首次新前向后再报实际加载。

17:19后turn101已首次派发原第21候选完整评价，实际目标样本增加，已加载模型；20/30仍为完整候选计数，不能把在途第21轮算完成。GPU0本服务15550MiB、整卡空闲52038MiB，其他任务仍运行。原独占速度不能作为共卡ETA；后续30分钟巡检记录完整新周期。

---


## 时间、运行与停止收据索引

下面是所收集JSON的原有时间字段与状态，不把预计结束时间当实际完成时间。未列时间的文件仍有原件链接。完整JSON全部保存在原文归档，不能以此索引中的标量代替完整嵌套内容。

| 原件 | 原记录状态/阶段 | 原时间字段（原时区） |
|---|---|---|
| [C-broker-launch-r1.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-gemma3-v9-quota-recovery-2026-11-06/C-broker-launch-r1.json) | {} | {"time_unix": "2026-11-06T09:13:03.115652+00:00"} |
| [C-broker-launch.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-gemma3-v9-quota-recovery-2026-11-06/C-broker-launch.json) | {} | {"time_unix": "2026-11-06T09:16:57.541927+00:00"} |
| [C-controller-launch-r1.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-gemma3-v9-quota-recovery-2026-11-06/C-controller-launch-r1.json) | {} | {"time_unix": "2026-11-06T09:13:38.608308+00:00"} |
| [C-controller-launch.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-gemma3-v9-quota-recovery-2026-11-06/C-controller-launch.json) | {} | {"time_unix": "2026-11-06T09:17:20.090716+00:00"} |
| [C-controller-once.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-gemma3-v9-quota-recovery-2026-11-06/C-controller-once.json) | {} | {"time_unix": "2026-11-06T09:13:38.760412+00:00"} |
| [C-controller-r2-once.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-gemma3-v9-quota-recovery-2026-11-06/C-controller-r2-once.json) | {} | {"time_unix": "2026-11-06T09:17:20.119664+00:00"} |
| [C-turn0100-receipt.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-gemma3-v9-quota-recovery-2026-11-06/C-turn0100-receipt.json) | {} | {} |
| [C-turn0100-tool_result.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-gemma3-v9-quota-recovery-2026-11-06/C-turn0100-tool_result.json) | {} | {} |
| [admission-r1-local-stop.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-gemma3-v9-quota-recovery-2026-11-06/admission-r1-local-stop.json) | {} | {"time_unix": "2026-11-06T09:16:30.789624+00:00"} |
| [admission-r1-remote-stop.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-gemma3-v9-quota-recovery-2026-11-06/admission-r1-remote-stop.json) | {} | {"time_unix": "2026-11-06T09:16:31.954791+00:00"} |
| [live-generation-verification.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-gemma3-v9-quota-recovery-2026-11-06/live-generation-verification.json) | {} | {} |

## 全部原始资产入口

本目录在固定提交下共有38个跟踪文件，包含代码、原回答、失败、收据和压缩证据；文件数不是样本数。[逐文件完整账本](../assets/164-wsp-vlm-gemma3-v9-quota-recovery-2026-11-06.tsv) · [原目录](https://github.com/yuxiexiong/acupuncture/tree/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-gemma3-v9-quota-recovery-2026-11-06)。未复制模型权重、环境或凭据。
