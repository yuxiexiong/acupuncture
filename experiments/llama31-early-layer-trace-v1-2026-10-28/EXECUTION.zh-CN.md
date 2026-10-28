# Llama 3.1 8B 前六层内部轨迹：执行记录

北京时间 **2026-10-28 05:00** 核验：合同、代码与920条来源已经冻结，服务器 **28/28 CPU测试通过、零失败零错误零跳过**。独立后台队列 **PID2326329** 已挂在Qwen 4B全层任务后，状态为`waiting / predecessor_running`，正式记录0/920。Llama真实GPU预检及正式采集尚未开始。

## 范围与过程记录

沿用已完成的独立Llama十点调查与单点正负剂量调查，选择 **L0–L5**：每层十个旧通道各+1×八题，另有原剂量点四档低正与五档负剂量×八题，每层152条；六层912条干预，加八份共享原版，合计 **920条**。不复用已停止的旧十点×十剂量合并partial。全部920条原始record、receipt、metadata、模型revision、源freeze和退出码已逐一核验。

每条观察Llama **全部32层、96个组件位置**的attention输出、MLP输出、层末残差；覆盖prompt全部位置及实际decode输入位置。保存清洁/干预范数、差分、相对变化、余弦及每步候选词、EOS竞争、前缀与首次预测分叉。无针参照用独立cache强制相同历史，保留原版自由回答和干预原文的来源关联。

采用与Qwen兼容的压缩轨迹schema，生成和干预则保留Llama原生模板/BOS/EOS及原BF16校准。这里是完整层与时间覆盖的摘要，不保存全部高维向量，也不把观察到的差分写成已确认根因。本次尚未生成Llama轨迹或把新结果接入三维界面。

合同：[CONTRACT.zh-CN.md](CONTRACT.zh-CN.md)；[机器合同](contract.json)；[来源清单与精确预检身份](source-manifest.json)。模型为`meta-llama/Llama-3.1-8B-Instruct@0e9e39f249a16976918f6564b8830bc894c89659`，使用已有核验资产，无新增下载。

## 最小实现与验收

- [trace_engine.py](trace_engine.py)直接继承原Llama引擎，只复用已有轨迹观察方法；[trace_run.py](trace_run.py)适配Llama原生检查，复用完整worker和结果验收逻辑。
- [source_prepare.py](source_prepare.py)只选择既有来源；[queue_run.py](queue_run.py)复用双卡进程管理，补全前驱完整性和Llama自身预检门禁。未修改正在运行或历史冻结代码。
- 本地28项中21项通过、7项因无torch明确跳过；服务器同28项 **全部通过**，CUDA被屏蔽且`cuda_initialized=false`，没有加载模型或占GPU。证据：[本地收据](readiness/local-cpu-tests-r01.json)、[服务器收据](readiness/cpu-tests-r01.json)、[完整日志](readiness/cpu-tests-r01.log)。
- 检查覆盖920条/464+456分片、来源冲突和旧partial拒绝、原生BOS/EOS、全32层组件、同前缀独立cache、观察器不改logits、零剂量/撤针及异常清理、授权/冻结篡改、前驱失败/失活、GPU等待、预检失败阻断正式和重复运行拒绝。
- 冻结SHA256：`5e635772da1afd588515dbccf8a3837aa73d761b151cf9ca0d0d78c559f557f0`，共57个文件。测试fixture准备问题已说明在[准备记录](readiness/preparation-notes.json)，不属于真实模型实验失败。

## 排队顺序与启动证据

1. 当前Qwen补齐前六层继续运行。
2. Qwen 4B L6–L31全部完成，追加总数达到4,560；两个阶段共六worker成功退出，前驱父进程退出，GPU0/1无计算进程。
3. Llama自己的双卡GPU预检：每卡七个观察案例＋五次关闭组件观察重放，合计 **14案例、38生成流**。最短历史案例为2 token，没有单token EOS；精确选择已经冻结。
4. 两卡预检全部通过后，自动正式采集 **920记录、1,840生成流**。任何验收失败保留证据并停止本次自身任务，不放宽标准或自行重跑。

直接前驱为`layer-trace-extension-v1-2026-10-28/execution-r01`，PID2295050/start_ticks1136269077，execution SHA `bbdb31eb8d8026d1b2ad972b31ca48dd9a9eb361efdd77f555bc48c2e248663e`。05:00时前驱仍在2B补齐阶段，557/4,560，GPU进程2322619/2322620属于前序采集。

新队列PID **2326329**、PPID **1**、start_ticks1137025527，已脱离SSH/Codex会话；输出目录为`/workspace/acupuncture/experiments/llama31-early-layer-trace-v1-2026-10-28/execution-r01`。证据：[授权](readiness/queue-authorization-r01.json)、[启动收据](readiness/queue-launch-r01.json)、[后台/资源核验](readiness/queue-verified-r01.json)、[排队快照](execution-r01/queue-state.json)。本地快照不是自动刷新的页面。

原半小时监控`acupuncture-3`已经加入本批，继续报告三段状态、ETA、磁盘与负载；A/B完成后仍监控Llama，三段总唯一记录数为 **7,632**。监控只读，不自动重启或清理。

## ETA与资源

920个来源输出共43,330 token；两片464/456条，输出20,844/22,486 token。旧单分支慢卡耗时约18.42分钟只是历史底座，不是本次内部轨迹实测。

本批含双分支观察、自身预检、加载与终验，暂预留 **追加1–1.5小时**，等待Qwen完成的时间另计；Llama真实GPU预检后按本模型`total_seconds`和输出长度重新估算，不把预算当停止阈值。详见[ETA.json](ETA.json)。可视化接图与研究分析不计入这段机器队列。

05:00核验工作盘仍约125 GiB可用、系统盘约48 GiB可用；本次复用已有模型和环境，新增主要为压缩轨迹。未删除缓存或结果，未中断现有任务。
