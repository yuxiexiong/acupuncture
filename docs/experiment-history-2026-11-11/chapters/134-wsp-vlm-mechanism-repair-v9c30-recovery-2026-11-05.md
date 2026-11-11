# 134．v9 C恢复并改为30轮收尾

[返回总时间线](../README.zh-CN.md)

**时间定位**：版本/记录日期 2026-11-05；未从所选收据确定完整运行起止，不据目录名补写时刻。

**当时的目的与设计**

续接中断的C研究者，沿原账本完成累计30轮，然后尝试报告和冻结。

**实际过程、结果与后来更正**

30次完整评价完成，但报告字段错误与后续容量错误导致未正常冻结。原错误、恢复、实际最佳和未知用量均保留；用户停止交接在11月6日另列。

**来源身份**：`wsp-vlm-mechanism-repair-v9c30-recovery-2026-11-05`；本章主体来源提交 `2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274`。下方原文中的状态是各文件写作时的状态，不能把早期“尚未运行”覆盖后期正式收据，也不能将后期结果倒填进早期设计。


## 原设计、执行过程、结果与更正全文

以下按“设计与题目 → 工程/执行记录 → 结果/更正 → 其他历史说明”组织；同类内没有可靠时间时保留路径顺序，不冒充严格先后。正文未删段；仅为本章节重排标题层级、把相对链接指向固定提交。原始字节另外完整保存。

### 原件 1：C恢复：累计30轮后收尾

原路径：`experiments/wsp-vlm-mechanism-repair-v9c30-recovery-2026-11-05/README.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-mechanism-repair-v9c30-recovery-2026-11-05/README.zh-CN.md) · [单独阅读副本](../library/e8e6b0c24e167b67.md)；SHA-256：`e8e6b0c24e167b67804cbac6a16444b701c2da436ef615264da74b9ac8ddcaf7`。

---

#### C恢复：累计30轮后收尾

**2026-11-06最新用户指示已执行：C完成30组后直接结束并交给下一队列。** 原服务通过stop正常退出，报告/冻结收尾不再等待；原失败收据保留。Gemma已接手，见[停止、交接与完整归档](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-c30-user-stop-handoff-2026-11-06/REPORT.zh-CN.md)。下文恢复与失败状态均为历史。

用户最新授权“恢复工作，把C做到30轮，先不动B”。仅C从已完成26轮接到累计30轮；覆盖C先前50轮目标，B的现有进程和授权不变。旧2B/8B/Gemma不恢复。

第143研究者回合返回容量错误，无回复、无usage回执、无远端动作。第142回合Python类型错误已返回并留下partial状态。原C broker PID1852016与Python内存仍存活；恢复同一Astra线程，从turn144开始，不重放142/143、不重载目标模型、不重算W0、不清零成本。累计token承接142回执，143尝试计入回合数，用量缺失明确保留。

复用原v9的Remote、CodexResearcher和run_session；测量、评分、权重、合同与工程身份不变，原30轮硬上限本来就已生效。恢复前核对本地/远端工程hash、原服务身份、同线程、142原始反馈一致、无未决动作，旧C监督器和50轮等待器已退出。只允许一次新恢复进程；再次失败停止留证，不自动重试。原失败监督收据不覆盖，恢复状态见本目录status/preflight/receipt/failure。

成功条件：累计30个不同非零候选完整评价；提交对应实际最佳的机制报告并冻结；原始回答、失败、轨迹和成本完整交付。开发结果不是独立泛化。到30轮后不进入31轮；x50/C-target-superseded.json记录旧C接续已撤销。

##### 范围与自查

设计卡沿用原v9 PLAN：主问题仍是内部证据驱动修补；新增执行只完成尚缺4候选，候选由同一研究者自主选择，静态补丁、W0、数据和下游响应不变。C最佳60.9375%但有视觉损伤，保留负面；成功/阴性/不确定都以完整回答与控制评价，不承诺收益。原样本384000、研究者5000万token及CPU/动作预算不扩大；存储12GiB、全盘留20GiB不变。容量恢复不是科学成功。

| 检查 | 判定和理由 |
|---|---|
| C01–C04 | 通过：沿用问题、已完成资产和反例，完成4个剩余开发候选，不新增研究目标。 |
| C05–C07 | 通过：实验数值路径与共享权重不改，只恢复观察者连接；保留原活跃Python状态。 |
| C08–C10 | 通过：不以恢复/测量次数代替机制或完整回答改善，保持原评分和对照责任。 |
| C11 | 通过：容量失败、Python错误与科学阴性分别保存；已下发动作不重放。 |
| C12 | 通过：0基线/模型重载，保留累计预算和失败用量未知；不动B。 |
| C13 | 通过：失败目录不覆盖，从144继续，同线程/源码/最后反馈验证，验收和运行分开记录。 |
| C14 | 通过：30轮报告冻结后停止，不延伸C到50或恢复旧队列。 |

反方复查：失败回合没有usage不能当零成本；旧标记仍可能写waiting所以同时核对真实PID与失败收据；原C监督器failed保持不变，防止50续跑误触发；恢复时Python142局部副作用存在，明确交给研究者检查，不直接重放。相关历史错误E10/E16/E22/E23/E25均按上述完整回答、失败保留、开发边界、分离验收/执行及不扩范围处理。同一助手自查，不称独立审查。

CPU检查：有效恢复边界通过，10种不安全边界均拒绝，0模型调用。真实恢复状态以preflight.json、status.json及新turn回执为准。

**真实恢复已确认：** 原服务PID1852016、恢复进程4055；同一Astra线程完成turn144且工具成功返回。失败143目录保留，142状态由研究者检查而非重放。仍26/30，已恢复不代表剩余4轮已完成。半小时监控已更新为B保持原状、C30。见activation-receipt.json和startup-turn0144。

---


## 时间、运行与停止收据索引

下面是所收集JSON的原有时间字段与状态，不把预计结束时间当实际完成时间。未列时间的文件仍有原件链接。完整JSON全部保存在原文归档，不能以此索引中的标量代替完整嵌套内容。

| 原件 | 原记录状态/阶段 | 原时间字段（原时区） |
|---|---|---|
| [activation-receipt.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-mechanism-repair-v9c30-recovery-2026-11-05/activation-receipt.json) | {"status": "researcher_and_remote_tool_success"} | {"time_unix": "2026-11-05T14:51:54.624529+00:00"} |
| [launch-once.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-mechanism-repair-v9c30-recovery-2026-11-05/launch-once.json) | {} | {"time_unix": "2026-11-05T14:50:09.683850+00:00"} |
| [launcher.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-mechanism-repair-v9c30-recovery-2026-11-05/launcher.json) | {"scope": "C only, total30"} | {"time_unix": "2026-11-05T14:50:09.528375+00:00"} |
| [startup-turn0144/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-mechanism-repair-v9c30-recovery-2026-11-05/startup-turn0144/receipt.json) | {} | {} |
| [startup-turn0144/tool_result.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-mechanism-repair-v9c30-recovery-2026-11-05/startup-turn0144/tool_result.json) | {} | {} |

## 全部原始资产入口

本目录在固定提交下共有15个跟踪文件，包含代码、原回答、失败、收据和压缩证据；文件数不是样本数。[逐文件完整账本](../assets/134-wsp-vlm-mechanism-repair-v9c30-recovery-2026-11-05.tsv) · [原目录](https://github.com/yuxiexiong/acupuncture/tree/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-mechanism-repair-v9c30-recovery-2026-11-05)。未复制模型权重、环境或凭据。
