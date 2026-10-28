# 早层输入约束机制：准备、测试与 ETA

2026-10-29。用户本轮授权为“写合同，代码，做测试，然后报给我 ETA”。正式实验尚未获本轮启动授权；所有正式阶段仍须独立授权与对应证据关口。

## 当前准备

- 合同及代码保存在本独立目录；旧实验代码、冻结、原文和收据未改。
- 开发24输入、新确认24输入、历史锚点8输入已生成；56条材料独立模型辅助审核通过。
- 真实分词器验证56输入和候选边界通过；未加载模型、未生成确认题输出。
- 最新服务器CPU验收 `readiness/cpu-receipt-r04.json`：39项通过，失败/错误/跳过均0。包含独立逐token前向评分与生成评分的合成核对。不能把CPU测试当作真实GPU通过。
- 真实GPU `runs/preflight-r01` 未通过：候选整段forward与增量forward差值0.062502861 nats，超过原0.02检查。worker0退出1；worker1由控制器停止，退出-15，不是第二个独立失败。原始68个记录文件及10个资产文件已回传并核验哈希，旧代码保存在 `readiness/source-freeze-r01.tar.gz`。
- 修复后用独立manual forward＋fresh cache同路径逐token核对全词表hash和logprob精确一致；整段forward差异仍保留为数值诊断。科学条件/正式生成路径未改，也未直接提高容差。
- 当前冻结 `freeze-r02.json` SHA `4c372a47738657f8be5e10ea49b0265ad17a979d721d98fa34fe7265234a95c4`。旧 `freeze-r01.json` 与失败收据保留。修复后的GPU复验尚未启动；当前没有正式授权、没有自动队列、没有可用的整轮实测ETA。
- 2026-10-29用户要求立即交接至另一窗口；本窗口不继续启动GPU复验。修订独立静态审核 `readiness/independent-code-review-r03.json` 已通过。接手窗口应创建绑定最新freeze/CPU/审核的仅预检授权，在新 `runs/preflight-r02` 验证后再估ETA；旧r01授权与freeze不再适用于当前代码。

## 正式规模与限制

开发193条件×24输入＝4,632；新题确认145条件×24输入＝3,480，固定核心共8,112份。最多六干预条件的时段、撤针、位置拆分及最多四候选的局部替换另计；continue技术重放、源重放、donor、候选评分、校准、预检与阅读均不能隐藏在8,112内。

当前没有自动正式启动队列。确认问题只允许准备、真值审核、分词检查；不得在预检中读取其模型输出。

最近真实资源快照为北京时间2026-10-29 02:44:19：两GPU无计算进程、各3MiB，控制器与两个worker均退出；远端项目分区可用约123.35GiB，模型/tmp同一分区可用约48.35GiB。这是历史快照，接手启动前须重新检查。机器测试未验收，不报告整轮ETA，也不把预检原文当正式结果。

## 接手窗口执行记录（2026-10-29，北京时间）

用户原话（接手后）："你按照handoff指令一直跑到实验结束，如果有bug和问题，按照实验设计文档中的内容修复，然后续跑。半小时更新一次eta和实验运行情况"。据此按 handoff 顺序为各正式阶段逐个建立绑定证据的正式授权；每阶段门槛仍按合同执行。

| 时间（UTC） | 事件 | 类型 | 证据 |
| --- | --- | --- | --- |
| 18:59 | `preflight-r02`（freeze-r02）启动；worker0 在首次调用独立手工参照时崩溃（rotary 位置 45 对 1 token），worker1 被控制器停止（-15） | 合同执行失败（代码） | `readiness/preflight-failure-r02.json`，`runs/preflight-r02/` |
| 19:05 | 修复：手工参照显式传 generate 相同的文本 `position_ids`；CPU r05 39/0/0/0，新断言在 freeze-r02 代码上报错；独立静态复审 r04 passed_with_risks（指出新 CPU 测试只验位置算术，真实路径只能由 GPU 验） | 工程修订 | `cpu-receipt-r05.json`，`independent-code-review-r04.json`，`freeze-r03.json` |
| 19:10 | `preflight-r03` 两 worker 完成、exit 0，launcher 核验失败：我手写的授权文件缺结尾换行，与 worker 副本字节哈希不同 | 合同执行失败（操作者） | `readiness/preflight-failure-r03.json`；r03 不复用 |
| 19:17 | `preflight-r04`（授权 r04 经 `experiment.write` 生成）通过：两 worker exit 0、controller completed、verification passed、各99记录；逐 worker `experiment.py verify` passed；本地216文件哈希一致 | 工程验收 | `runs/preflight-r04/`，`readiness/preflight-verify-r04.json` |
| 19:23 | 精确同路径候选核对 8/8 通过；一次性整段 forward 差值 0.0026–0.104 nats，仅作数值诊断，未证实全部来自 BF16 | 诊断 | `runs/preflight-r04/worker-*/records/candidate-check-*.json` |
| 19:24 | ETA r01；development gate r01 与正式授权 r01 生成并干校验（其他阶段均拒绝）；`development-r01` 启动 | 正式阶段 | `timing-estimate-r01.json`，`stage-gate-development-r01.json`，`formal-authorization-development-r01.json` |

偏离记账：`development-r01` 启动命令多写了 `> /dev/null`，controller stdout 未进入 `readiness/development-controller-r01.log`；状态与错误仍由 `controller.json` 记录，worker 日志不受影响。不影响任何科学结论。

ETA r01（较慢 worker、阶段串行，仅机器时间）：实测长度情景 development 2.10 h、confirmation 1.57 h（固定网格 3.67 h），机制/替换按最大未选定工作量另计 3.47 h，合计 7.12 h；全128情景 6.37/4.84（固定 11.21 h），合计 19.51 h。阅读、审核等待、传输未计。原始证据 6.4–22.9 GiB：服务器足够，本地归档盘不足（5.9 GiB）。
