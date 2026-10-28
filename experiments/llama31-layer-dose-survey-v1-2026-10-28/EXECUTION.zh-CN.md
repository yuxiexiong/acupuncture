**2026-10-28 00:32:47已按用户纠正停止。** 十点×十剂量合并设计作废，不再运行。479份已保存回答（471干预+8原版）和原始收据完整保留，本地文件/token核验通过；不复用到更正后的正式实验。两个worker退出-15由用户停止造成，两卡已释放，不宣称中断整轮的最终权重/hook验收完成。见[user-stop-split-r01/receipt.json](user-stop-split-r01/receipt.json)。新设计为独立逐层十点+1实验、随后逐层单点剂量实验。以下保留历史启动记录。

# Llama 3.1 8B Instruct 十点正负剂量执行记录

**当前状态：正式实验已运行，尚未完成。** 北京时间2026-10-28 00:22:25启动，两H20并行；当前freeze为`70f313c5e643bc4006782159c9a325de98527399be8d11610deddcb68ff1385f`。用户明确选用8B-Instruct，已授权验收通过后直接运行。

最终本地/远端CPU 22/22通过（r03），真实5.20.2生成配置解析通过，独立设计/代码/启动审查通过。GPU预检preflight-r02为88/88、5,601 token，80 EOS+8达到128；8组跨卡基线、6份zero、6份恢复全exact，30个±配对通过，全部32层目标权重恢复及hook清理通过。控制器实耗175.05秒，两exit0、进程退出后才开始正式。完整102文件11,019,458字节取回，全部record/token及metadata/calibration/sampled columns本地复核通过。

正式科学分母为25,600干预（每worker12,800），原版8另计，合计25,608唯一来源。32层各十点，±1/16、±1/8、±1/4、±1/2、±1和原八题；输出最多128新token/EOS原长。任务、生成代码、校准与剂量规则对齐千问；Llama原生模板/词表/EOS与千问不同，旧千问全剂量每层一点、本次每层十点，覆盖差异不伪装为相同。

00:24:11现场：47/25,600干预＋8/8基线（两worker干预19与28），0/3,200个完整八题条件；交错运行尚未覆盖首点八题，不能按记录数除8。55份文件/token哈希通过，controller2254533与worker2254534/2254535真实命令一致，最新记录距快照约3–5秒，无错误。两H20各16,205MiB，GPU利用率34%/33%。

初始预检主情景11小时42分19秒；00:24快照剩余11小时40分09秒，预计北京时间**10月28日12:04**计算完成。剩余全部128情景约21小时38分09秒，完成点**22:02**；不是CI或硬上限。首个完整八题通道尚未完成，暂沿用各卡自身预检情景，不用前几条短题推算全程。初始正式worker约22.730 GPUh、两卡预留约23.410 GPUh是推算，实际成本结束后另报；没有计费单价。导出、归档与阅读另计，未测不编ETA。

快照工作盘95%、可用126.22GiB；/data/models与/tmp共用根盘91%、可用43.60GiB；本地52.78%、可用877.38GiB。本轮目录22.15MiB、正式输出11.14MiB（含两份采样列），当前空间充足。正式记录文件按预检实测平均大小的投影保存于readiness/storage-estimate-r01.json，不将投影当硬上限，无任何删除。

半小时心跳`llama-3-1`已ACTIVE，只跟踪本批；旧千问心跳已结束，其他暂停实验不恢复。完成后controller将核验两worker并自动导出2,560组十一栏。原文/全部证据取回核验及开放逐组阅读、逐层笔记和覆盖完成后，才最终交付并结束巡检。

执行证据：[合同](PROTOCOL.zh-CN.md)、[正式授权](readiness/formal-authorization-r01.json)、[启动身份](readiness/formal-launch-r01.json)、[最新快照](monitoring/latest.json)、[计时估计](readiness/timing-estimate-r01.json)、[独立计时复核](readiness/timing-independent-review-r01.json)、[预检本地核验](readiness/preflight-local-verification-r02.json)。

## 历史准备与启动前修复


2026-10-28（北京时间）。用户已确认8B-Instruct，并授权CPU/GPU验收通过后直接正式运行。官方模型资产14文件当前完整hash通过，千问负组已经完成且两H20空闲。

本地和远端最终22项CPU测试全部通过；真实远端Transformers5.20.2解析后的生成策略核验通过，无真实模型加载。新freeze为`41f27e01643a3db8408651111c84968cfa0a348caba41014908ad9bc6510fe8f`，共19个源/合同/依赖文件；旧千问freeze不改。代码及设计审查通过，GPU预检授权已保存，尚待启动结果。

固定32层每层十点、320点、±1/16、±1/8、±1/4、±1/2、±1，每点每档原八题；正式25,600干预+8基线=25,608唯一来源，2,560组十一栏。预检88另计。每worker每层5点，正式各12,800干预，shard0另8基线。模型原生模板/词表/结束符不同，旧千问完整剂量每层1点的覆盖差异明确保留。

见[合同](PROTOCOL.zh-CN.md)、`readiness/cpu-local-r02.json`、`cpu-remote-r02.json`、`native-generation-config-check-r01.json`、`independent-launch-review-r01.json`与`preflight-authorization-r01.json`。正式ETA以Llama预检实测更新，不套用千问速度。

启动前路径检查曾阻断r01（未加载模型、未创建GPU预检输出）；前置路径补齐experiments/后，本地/远端22项CPU均再次通过，旧19文件与freeze完整保存在versions/prelaunch-r01。新freeze `70f313c5e643bc4006782159c9a325de98527399be8d11610deddcb68ff1385f`，预检目录改为preflight-r02，所有科学设置不变，独立修复审查通过。

GPU预检r02于北京时间2026-10-28 00:16:14实际启动，controller PID2252729，两worker2252730/2252731。00:17:07现场16/88、790token、两卡各16193MiB及34–35%，文件/token核验通过，未见异常。正式阶段尚未启动。
