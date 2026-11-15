# RCS-01：实现与已审协议一致性审查

2026-11-15；同一独立上下文 Advisor，承接设计 v2 与同人复核。审查范围为隔离工作树中的 `rcs_run.py`、`rcs_hooks.py`、`rcs_analysis.py`，回查其直接复用的 WSB/LVK/KRD 源码及本轮上游 kernel/norm 测试路径。只写本记录，不改代码，不运行模型、tokenizer、统计或实验。用户已经授权实现、测试后上卡；下列修改属于既有协议的工程纠错，不是新增审批要求。

**最终状态：实现与已审协议的静态一致性复核通过；I1–I4 已修复。** 下文保留发现与处理过程，最终验收边界见末节。服务器真实源码 CPU 验收与 GPU 工程运行尚未由本记录认证。

## 第一轮静态判断

科学操作与主要分析当前未见必须改变设计的硬伤。四臂 hook、自然续写、共同资格集合与主要判据已落到实现；发现的待修问题集中在失败记账、重复运行预算约束及被测上游源码身份。**修复并完成已有 CPU/冻结验收前，不能将当前实现称为已通过运行门槛。**

### 必修 I1：被强制停止的失败运行也必须可计费

初读 `authorize()` 对 prior receipt 无条件读取 `r['wall_seconds']`。supervisor 的 SIGTERM/kill 不保证执行 worker 的 `finally`，因此最近的 receipt 可能仍为 running、缺少 wall_seconds；虽有 exit.json 的 supervisor_wall_seconds，第二次工程授权仍会 KeyError。该情况正发生于协议规定的时间/存储失败停止，不能通过遗漏这次运行绕过。

要求：缺 worker 时长时以已保存的 supervisor 时长为依据，保留失败身份与已有工件；预算必须计入失败。应有相应无模型失败路径测试。若尚无 exit 回执，保守阻止启动并先落实实际终止/耗时，不能当作零耗时。

### 必修 I2：授权不得重复使用而绕过两次工程与总预算

初读 `authorize()` 只相信 JSON 提供的 prior_runs；相同 prior={} 的工程授权换一个新 output 即可再次通过。锁只防并发，不限制顺序重复。因此“两次工程、一次正式、3576 自然回答、总 6 小时”尚不是跨尝试的硬约束。

要求：将一次授权绑定唯一输出/尝试，并在锁内核对实验全部既有尝试与 prior 清单一致，或实现等价的单次消费记录。失败尝试也纳入，不能允许重用旧授权忽略它们。正式阶段不得因为新 output 而重跑整套已计费工作。该约束是实现原合同，不增加用户审批。

另应将 supervisor 的同级 `.log`、receipt/exit 等实际工件计入存储，复用来源包按实际文件大小核账；初读仅计 output 子树与 ΔH 名义张量负载。预算余量不应使这些记录从总账消失。

### 必修 I3：CPU 所测上游代码须绑定运行冻结身份

初读 freeze 通过 W.assets 记录当前 external_sources，authorize 对这些文件防漂移；但未见与 WSB 正式冻结的上游源码 hash 核对。CPU 回执只要求 `upstream_kernel_tested=True`，缺少所测文件 hash 与此次 freeze 的绑定。相同 transformers 版本号以及 RCS 自身源码 hash 均不能补上此缺口。

要求：记录实际 CPU 测试的 GDN 源文件身份，并与运行 freeze 一致；freeze 明确核对历史 WSB 的 GDN/cache 实际源码身份。若历史与当前字节不一致，先说明差异并按既定桥接要求处理，不能用公开文件测试成功冒充旧环境源码已核。

## 已核实的一致性

- `CapturingWriteHook` 复用 WSB t1 计算，保存实际 FP64 J 与对应 FP32 native_s，减回逐位核对；没有用请求 ΔH 直接替代实际 J。
- `ReadoutHook` 在每层当前调用内用同一驱动调用真/shadow recurrent kernel；检查 S1、驱动、卷积和缓存管理字段不被 shadow 修改，返回并验证提交真 S2。高层驱动由当前分支自然产生，并未误冻在其他臂。
- norm hook 使用已 cast 的 x0/x1 端点，保留 rsqrt、cast、weight、SiLU 的顺序；11 采用原输出并比对重算值。对缓存 S2 的核对与出 hook 后清理检查齐备。局部分账仅作为诊断保存。
- `V.natural` 只在第二生成 token 的 forward 使用 hook，后续自然续写无 hook，保留原 greedy/停止/长度规则。四臂从同一次 t1 缓存的独立深拷贝启动，源缓存 hash 再核；11 完整序列与旧 CH/HH 桥接。
- analyzer 保留全供体 D_tr、接收者等权和整场景重抽；R* 资格依赖共同 t1 前缀/候选映射，不依赖 logits 或效果。合格对象缺测会报错而不是按结果删样本。R* 的完整供体 D_tr 与冲突对连续诊断分开，强结论绑定同一 S1 撤回及全样本/R* 双行为门槛。
- Q 六项固定诊断、不以 Q 过滤；无效答案保留并计算最坏填补界；一般用途与更强余量结论分开。未见把局部向量较小误判为弱门坐标已获因果定位。

作者已预先提出并修复的 analysis 问题亦已回读：面板缺失的 question/first_listed 等来自冻结 LVK 原 item，保留旧完整答案分类；load 要求 completed、stage 匹配、exit=0、记录清单与 hash 一致。runner 保存 bases.item，analysis 将其与冻结原文核对。这些是正确修复，不改变评分对象。

## 验收身份

本记录是静态协议一致性审查，不是独立执行 CPU 测试或 GPU 复现。真实上游 kernel/norm 测试代码已读取，其路径确实调用实际函数；测试结果与源码身份仍须以冻结回执为准。旧包当前完整性、服务器环境、端到端工程桥接、计费与存储实测不因本审查自动通过。修复上述项后由同一审查者针对改动复核即可，不需要新增科学控制或扩大矩阵。

## 同人实现复核（一）

作者修复后重读 `rcs_run.py` 与新增 `cpu_accept.py`，I1–I3 的主要缺口已关闭：prior_usage 使用 supervisor 时长兜底，supervisor 写失败回执；授权绑定唯一 output，锁内重验全部尝试目录，失败纳入 prior；实际 runs 树包含同级日志并加旧包实际大小；CPU 回执记录外部代码 hash 并与 freeze 绑定，freeze 核对旧 WSB 授权所锁的冻结源码/模型/版本。RunMeter 的 finally 计时与 attempted_model_forward_calls 也覆盖抛错的 forward。此处确认源码实现，不宣称相关运行测试已经独立执行。

追加发现 I4，须在结束实现审查前修复：pair JSON 当前仅在两背景八臂全部结束后保存；后臂失败时，已完成臂的自然原文仍在内存，只有 tensor 已落盘。11 桥接断言也先于 record 赋值，因此桥接失败的实际原文会丢。baseline 类似：后续零 J 或另一背景失败可能使已经生成的 U 原文未保存。这违反原协议“原文及失败不丢”，且影响工程错误的事后复核。

最小修复为每臂完成即保留原始 trajectory（在桥接断言之前），或异常路径保存累计 partial record、当前 trajectory、bases/t1 记录。partial 必须与完整记录区分；completed/exit/hash 的分析闸门保持，不能把不完整工件纳入科学评分。无需增加模型调用。

## 同人最终复核与后续边界

已再次读取 I4 修订代码：baseline 原文及每条已完成臂的原文即时落盘，在后续 tensor 保存、桥接或下一臂之前；pair t1 的实际 states/meta 先保存再进行快照桥接，baseline t1 快照同样先保存，桥接失败不会继续生成。t1 forward/hook 抛错保留已捕获 states/records；t2 失败保留 partial records/tensors/shadow_calls，shadow 计数在 finally 累加一次，避免后续 decode 失败把已执行 shadow 记为零。八臂齐全才生成正式 pair JSON，分析的 completed/exit/hash 闸门未被放松。I4 关闭。

本审查直接读取本地 `cpu-local-r02.json` 与 `cpu-local-r03.json`：r02 为 failed，失败档保留；r03 三套命令 returncode 均为 0、status=passed、model_forwards=0、cuda_initialized=false、source_stable=true，且 upstream_kernel_tested=false。因此只能称本地 CPU 测试通过，不能称真实服务器源码验收完成。最终顺序修订后的 r04 当时由作者运行中，本记录不预先写成通过。最终运行的 CPU 回执必须与冻结代码 hash 一致；这已由 authorize 代码约束，不靠本审查豁免。

**未发现仍未解决、会改变四臂估计对象或主要判读的实现硬伤。** 可结束本轮 Advisor 实现一致性审查。主作者按用户已有授权继续最终 CPU、服务器真实源码/资产冻结及工程验收；通过现有闸门再按协议执行，失败按既定额度保留并纠错。无需为不改变科学定义的工程修复重复咨询，也不需要新增用户审批。

此结论不承诺 GPU 上逐位桥接一定成功、资源实测一定够用或实验会出现机制阳性；这些仍由已审合同的实际验收与结果区分。若操作、主要终点、样本资格、失败判读或预算范围发生实质改变，则属于新的设计变更，不能借本次静态通过覆盖。
