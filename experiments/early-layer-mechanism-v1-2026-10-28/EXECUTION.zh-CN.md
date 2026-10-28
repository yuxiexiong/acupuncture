# 三模型早层内部轨迹：准备与执行记录

2026-10-28 02:23（北京时间）快照：**合同、代码和服务器24项CPU测试通过；后台队列已启动，正在等待前置Llama实验。GPU预检和正式采集均尚未开始。**

## 范围与交付

沿用2B、4B、9B已有全层十点及单点正负剂量结果，给早层核心和相邻边界层的旧条件补内部轨迹：2B L0–L3共616条、4B L0–L3共616条、9B L0–L5共920条，合计2,152条来源（24原版、2,128干预）。每条均观察模型全部层的attention/GatedDeltaNet输出、MLP输出和残差。无新科学条件、无修复/反向替换实验。

自由生成仍走冻结的原引擎；每条输出必须与旧来源逐token一致。另用独立cache强制相同历史，记录无针参照；它不是原版自由回答。保存逐位置范数/差分/余弦、逐步EOS竞争和候选词评分，以及全部身份、原文和hash；不落盘全部高维激活。结果可供后续三维轨迹与原文联动，此时尚无新的轨迹结果或机制结论。

合同：[CONTRACT.zh-CN.md](CONTRACT.zh-CN.md)；来源：[source-manifest.json](source-manifest.json)；代码：[trace_engine.py](trace_engine.py)、[trace_run.py](trace_run.py)、[queue_run.py](queue_run.py)。冻结SHA256：`23374b5a0b86835fd8c95801c32839ae49d8850f3d08b2a589957fba77d94620`。

## 验收

- 全三源SHA、13,400唯一条件题记录、4,272重复引用一致性通过；本轮2,152条已逐一对回原始record、完成收据及模型metadata。
- 本地24项测试：18项通过，6项因本机无torch明确跳过，未将其标记为数值验收通过。
- 服务器冻结版本CPU测试：**24/24通过，0失败、0错误、0跳过**。`CUDA_VISIBLE_DEVICES`为空；仅使用CPU小型mock，没有加载真实模型。证据：[CPU收据](readiness/cpu-tests-r01.json)、[完整日志](readiness/cpu-tests-r01.log)。
- 测试覆盖完整范围、重复冲突、分片、固定预检身份、EOS/128上限、同前缀独立cache、组件观察不改变输出logits、零剂量/撤针、异常hook清理、权重不变、授权/冻结篡改、前驱/GPU占用/重复队列，以及预检失败阻断正式实验。
- 两次CPU准备失败已保留：[失败记录](readiness/cpu-failed-attempts.json)。分别为测试隔离导致重复导入torch，以及远端缺少本地汇总源文件；均已修复。未删除实验失败回答或放宽任何科学验收阈值。

GPU预检固定六worker，每worker七条有组件观察（各两分支）及五条无组件观察重放，共42条案例、114条生成流。六worker全部通过后才运行正式2,152条/4,304条生成流。任一来源重放、校准、偏移、数值或完整性检查失败即停，保留部分证据。

## 服务器队列

- 服务器：`gqa-h20`；后台PID `2285813`，实查PPID=1，已脱离SSH/Codex会话。
- 远端：`/workspace/acupuncture/experiments/early-layer-mechanism-v1-2026-10-28/execution-r01`。
- [用户授权与预算](readiness/queue-authorization-r01.json)、[启动收据](readiness/queue-launch-r01.json)、[排队快照](execution-r01/queue-state.json)。快照不是自动刷新的本地实时页面。
- 前置任务：Llama 3.1 8B单点正负剂量`survey-r01`，02:23实查仍运行，两个worker共1,840/2,304，PID 2275684/2275685各占约16,198MiB。新增队列未加载模型，没有增加GPU进程。
- 每10秒检查前驱成功收据、worker退出码和绑定PID实例；前驱进程退出且两张GPU均无其他计算进程后，按4B→2B→9B做预检，再按相同顺序正式采集。每模型两卡分片，不抢占现有实验。
- 程序在服务器独立运行；关闭Codex不会使这个排队进程退出。失败时只停止自身子进程并保留日志，不终止前驱或其他人的任务。

## ETA

沿用[ETA.json](ETA.json)中的规划估算：正式机器采集约2.5–4.5小时，**不含排队，也尚未用本轮GPU测量校准hook开销**。源实验重放底座45.2分钟，新增成对前向与观察开销仍属假设。GPU预检完成后应以真实短/长输出时间更新，不在排队阶段承诺完成钟点。
