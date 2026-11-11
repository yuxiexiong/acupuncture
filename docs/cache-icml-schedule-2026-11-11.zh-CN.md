# 缓存机制线：ICML 2027 下一阶段 schedule

2026-11-11 更新。用户已确认上一轮建议并要求落成日程、推进第一步。本页是当前执行日程；[原建议及设计依据](cache-icml-preparation-2026-11-11.zh-CN.md)保留历史身份。负责人：本聊天中的 Codex 推进，用户作投入与模型预算决策。

日期均为北京时间的内部节点。ICML 2027 官方投稿日程截至本聊天 11/11 查询尚未公布，不把 1/4 写成官方截止。官方日程公布后调整并尽量保留两周终稿缓冲。本文件不创建定时自动任务，也不恢复已取消的服务器巡检。

## 当前执行表

| ID | 内部时间 | 工作 | 验收／交付 | 当前状态 |
|---|---|---|---|---|
| S0 | 11/11 | 固定日程、纠正当前入口 | 本表、To-do 与研究状态一致；旧记录保留历史身份 | 完成 |
| S1 | 11/11–11/13，最迟两个工作日 | 审查旧差异结果、SPF/DWB/DWC 与 NGC，形成解释—证据—反例—缺测量表 | 一个优先研究对象和具体设计障碍，或明确无有效比较；不重做大盘点 | **11/11 完成**：[首轮结论](cache-icml-first-step-2026-11-11.zh-CN.md)，37 数值检查通过 |
| S2 | 11/12–11/14；S1 后可提前开始 | 形成最小可判别设计 | 同来源写入在可比背景下的对象、终点、判读、成本及 C01–C14；预期阳性不能只重复背景依赖 | **11/11 完成**：[WSB-01](../experiments/cache-write-signal-background-v1-2026-11-11/PLAN.zh-CN.md)，作者自查与 CPU 设计核对通过；非执行合同 |
| S3 | 11/14–11/24，依 S2 结果 | 实现／数值验收及一轮有界关键测量 | 工程与科学结果分开；全部预算含加载、重建、重放、失败；真实结果与反例入稿 | **11/11 正式完成**：[WSB-01 结果](../experiments/cache-write-signal-background-v1-2026-11-11/REPORT.zh-CN.md)，CC/CH/HC/HH=0/0/0.003/0.882；全部有效作答、数值验收和原文复核通过。含首次失败及唯一重试，全包 0.505 GPUh／上限 3 |
| G1 | **11/25** | 判断是否继续集中投入 ICML | 重要部分关系获得新解释或有价值反证则继续；仅重复已知可操控端点则停止扩张重估；工程失败单独判断 | S3 已给出写入差值×接收背景配合的正向增量；建议有界继续，尚不等于整篇论文达到投稿门槛 |
| S4 | 11/26–12/10 | 核心关系的范围／预测检验 | 优先复用 9B 资产；检验同一关系，不重跑损伤扫描；新规则使用过的数据不算其新确认集 | 取决于 G1；不设模型／任务数量配额 |
| S5 | 12/11–12/20 | 收束主要结论并形成完整初稿 | 主文、图表、补充、阴性与复现入口，摘要每条主张可追溯 | 未开始本阶段；必要写作从第一周逐步推进 |
| S6 | 12/21–2027/01/04 | 完整稿审阅与修订 | 投稿就绪版本；只补影响核心结论的缺口 | 条件节点，随官方日程校正 |

## 执行边界与退出

- 用户随后明确“继续推进吧，实验结果出来后，再跟我汇报”。据此执行了 WSB-01 的真实预检和正式四格，全部尝试计入 3 GPUh 上限，实际 0.505 GPUh。此次执行已结束；旧 CWR9 及其他新实验未由此获准。
- S1/S2/S3 已结束，不按原日期重复整理或重跑。WSB-01 固定同一写入差值跨背景重放，支持指定条件下的配合效应；不将背景响应或行为交互直接命名纯读取／新内部模块。后续优先保持同一关系的解释与范围问题，具体方案仍须自查和相应授权。
- WSB-01 数值／身份验收或预算外推未通过就停；有效阴性按预写解释处理，不为日程自动扩样、扩层或换针。
- G1 不要求解释全部原生停答，也不要求统一所有方向。有效阴性不自动终止课题，但不自动触发扩层、加针、换题或更多卡时。
- NGC 已完成且四方向零修复；其旧 GPU Ready 状态不再是当前队列。WSP 不在本日程中。
- 新结果及时更新状态、版本与仓库链接；这不是后台自动执行或未来提醒的承诺。

## 本轮交付与验收

S1 详细证据、操作对照、反方检查和 C01–C14 见[首轮报告](cache-icml-first-step-2026-11-11.zh-CN.md)。数值核对见[机器收据](cache-icml-first-step-2026-11-11.audit.json)，复查命令为 `python docs/cache-icml-first-step-2026-11-11.audit.py`。本轮模型调用 0、GPU 进程小时 0；不改旧统计、原始回答和已审正文。

S2 的[方案](../experiments/cache-write-signal-background-v1-2026-11-11/PLAN.zh-CN.md)、[作者自查](../experiments/cache-write-signal-background-v1-2026-11-11/SELF_CHECK.zh-CN.md)和[CPU 设计收据](../experiments/cache-write-signal-background-v1-2026-11-11/design-audit.json)已交付。复查命令为 `python experiments/cache-write-signal-background-v1-2026-11-11/design_audit.py`；只做材料／计数／合成计算，不加载模型。S2 不包含真实实现或数值验收，实际模型调用和 GPU 小时均为 0。

S3a 的[实施记录](../experiments/cache-write-signal-background-v1-2026-11-11/IMPLEMENTATION.zh-CN.md)、[最终 CPU 收据](../experiments/cache-write-signal-background-v1-2026-11-11/readiness/cpu-local-r04.json)与[来源清单](../experiments/cache-write-signal-background-v1-2026-11-11/readiness/source-manifest-r02.json)已交付。上游 kernel 未在本地核验，不把合成 CPU 测试写成模型通过；未连接服务器、未排队。

S3b 的[服务器验收与修复](../experiments/cache-write-signal-background-v1-2026-11-11/SERVER_CPU_ACCEPTANCE.zh-CN.md)、[服务器 CPU 收据](../experiments/cache-write-signal-background-v1-2026-11-11/readiness/cpu-server-r02.json)、[环境清单](../experiments/cache-write-signal-background-v1-2026-11-11/readiness/environment-server-r02.json)与[预检就绪核对](../experiments/cache-write-signal-background-v1-2026-11-11/readiness/preflight-readiness-server-r01.json)已交付。用户只授权服务器 CPU 核对；真实预检与正式实验未启动，GPU 授权关闭。

S3c 的[正式报告](../experiments/cache-write-signal-background-v1-2026-11-11/REPORT.zh-CN.md)、[统计](../experiments/cache-write-signal-background-v1-2026-11-11/runs/formal-20261111-r01/analysis.json)与[作者侧原文复核](../experiments/cache-write-signal-background-v1-2026-11-11/readiness/final-local-audit.json)已交付。预检首轮接口失败后做最小修复，唯一重试通过；正式 348 配对和 2,184 自然轨迹完成。此前 S3a/S3b 的不上卡文字仅描述各自当时阶段。新发现限于 4B、N4146、48 已见输入，未新增跨模型确认。
