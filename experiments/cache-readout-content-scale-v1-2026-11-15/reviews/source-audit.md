# 门前尺度四臂草案：限定源码与资产审查

日期：2026-11-15。审查者：动力学子 agent；这是源码/资产审查，不代替正式 Advisor 或完整 C01–C14 设计审查。只读取资料，没有执行实验、模型、tokenizer、张量统计、测试或运行器。读取固定工作树 HEAD `a224f14ef1e12f60d5589970cb743591b93219a0`；本文件写回主项目根。

**结论：草案可精确定义，但需要四项限定：实际 J 不等于旧请求 Δ；x0 是同层局部撤除反事实，不是无增量轨迹；norm 必须保留原来的中间 cast；旧包可免来源形成，但接收者形成和新的 kernel shadow 不能漏计。** 没有发现必须保存整模型缓存才能复算 norm patch 的障碍。历史外部包现在是否仍完整可读尚未核验，不能标为资源已就绪。

## 1. t1 实际 J 与 t2 的 S1−J

[wsb_core.py:55–89](../../cache-write-signal-background-v1-2026-11-11/wsb_core.py#L55) 的顺序明确：

1. 第 62 行先按本层**当前实际驱动**算 `native_s`。
2. 第 84 行接收旧包：`state=(native_s.double()+delta.to(device)).float()`。
3. 第 85–86 行由这个实际 FP32 state 重算当前输出，再转回 query dtype。

因此建议把草案中的记录精确写成 `J=state.double()−native_s.double()`。现存 `update` 返回的 delta 和 `WriteHook.records.delta_sha256` 仍是请求 Δ 的身份，不是新重放实际 J；不能直接复用其字段名称就假定已记录 J。[wsb_run.py:152–162](../../cache-write-signal-background-v1-2026-11-11/wsb_run.py#L152)

同一个来源 Δ_H 在 C/H 背景里的实际 J 可因 native_s 与 FP32 舍入而不同。若高层 t1 输入已经响应低层 Δ，`native_s` 是该高层在这条受影响轨迹上的局部未加回状态，不是完整无 Δ 运行的该层状态。J 不包含低层操作已经改变的其他缓存与高层驱动。

**S1−J 的数值定义：** 若采用重建，应在 FP64 做减法再转回原 state dtype，且把与 t1 留下的 native_s 身份核对作为未来验收项；不能把有限精度加减的形式恒等当逐位恢复证明。更简单的实现语义是：在 t1 至 t2 这段暂存每个 G 层的 `native_s.detach().clone()` 作为影子输入，J 仍按上式记录。它不要求持久保存整模型 cache。选择哪一种须在设计中写定，不能验收不一致后静默切换。

若用户坚持以 S1−J 为正式定义，native_s 可仅作重建核对参考；重建失败属于工程阻塞，不是科学阴性。不能改用旧 Δ_H、低精度 J 或秩一拟合 J 补救，因为它们对应不同的状态撤除操作。

## 2. shadow 可以只读，但必须停在 kernel 边界

项目历史 [kuc_run.py:122–160](../../cache-k-update-causal-v1-2026-11-03/kuc_run.py#L122) 的 `custom_update`：第 135 行读取 initial_state，142/146/147 行均为新张量赋值，未原位改 initial_state；返回 out 与新 state。原 norm 前输出在第 159 行已转回输入 dtype。其 oracle 是 FP64 条件核对，不是另一条模型轨迹。

可据此定义：在每臂、本层真实 t2 kernel 接口截取 q/k/v/g/β 和初始 S1；真实 kernel 产生 x1/S2；影子用完全相同的驱动和重建状态产生 x0，丢弃影子新 state。仅真实 S2 返回给模型的 cache 更新调用。**不要为取得 x0 再调用完整 linear-attention 模块**，否则会第二次更新 conv cache、产生额外投影/门控或触发嵌套 hook。

公共固定版本 [Qwen3.5 v5.20.2 源码](https://github.com/huggingface/transformers/blob/v5.20.2/src/transformers/models/qwen3_5/modeling_qwen3_5.py) 的 `torch_recurrent_gated_delta_rule` 与上面的调用顺序相符；`Qwen3_5GatedDeltaNet.forward` 先更新 recurrent state，再做 norm 与输出投影。该历史环境确认为 torch fallback、无 FLA/kernels/causal-conv1d 加速包：[environment-server-r03.json:399–418](../../cache-write-signal-background-v1-2026-11-11/readiness/environment-server-r03.json#L399)，模型源码 hash 为 `b4b17fe08d8d54da34a0fce78639666279ae7fd0a9e4ec06fce6602774707ca3`。本次没有访问该服务器源码文件重验 bytes；未来若换 fused backend，不能沿用只读判断。

最小副作用验收应针对输入 S1、conv cache 及缓存管理字段：shadow 前后不变，返回模型的是实算 S2；不要仅检查 shadow 输出值。历史 [snapshot:233–246](../../cache-write-signal-background-v1-2026-11-11/wsb_run.py#L233) 已示范记录 cache tensor/hash 与 scalar 管理字段，未必要保存这些 tensor 的完整副本。

“保留真实 S2”的正确含义是**每臂当前驱动所产生的真实 S2**。低层 norm patch 改变高层输入，所以高层 S2 可跨臂不同；不能说四臂 S2 全部固定。四臂 t2 开始时可共享同一 t1 结束缓存的独立副本；高层 q/k/v/g/β/z 随本臂自然响应。每臂 x0/x1 的配对只在本臂本层局部驱动下成立。

## 3. 四臂的 cast 不能用实数公式代替

草案的 `N_cs=γ·SiLU(z)·[x0+c(x1−x0)]/r[x0+s(x1−x0)]` 适合数学描述，但不能直接作为实现表达式。

原 [Qwen3_5RMSNormGated.forward](https://github.com/huggingface/transformers/blob/v5.20.2/src/transformers/models/qwen3_5/modeling_qwen3_5.py) 顺序为：输入转 FP32 → 平方均值/epsilon/rsqrt → FP32 相乘 → **转回原输入 dtype** → 乘 learned weight → 乘 FP32 SiLU(gate) → 最终转回输入 dtype。weight 的真实 dtype 也须保留，不能默认 FP32。

建议设计精确定义为以下运算序列（只是语义，不是运行器）：

- `xc` 直接选实际 kernel 返回的 x0 或 x1，`xs` 同理；c/s 为二值时不通过 `x0+(x1−x0)` 恢复 x1，避免额外舍入破坏 11 原生端点。
- 以 `xs.float()` 计算原实现的 `rsqrt(mean(xs²)+epsilon)`；以 `xc.float()` 作 numerator。
- 相乘后的 normalized vector 先 cast 回实际 kernel 输出 dtype；再按原顺序乘 weight 与 `SiLU(z.float())`，最后 cast 回输入 dtype。
- 00、11 分别走原 norm(x0,z)、norm(x1,z) 的同样运算路径；11 是本臂局部原样输出。01/10 是刻意拆分分子/分母的反事实。

不能预合并 `γ·SiLU(z)`，不能先乘 gate 再算分母，也不能把 rsqrt 乘法替成 sqrt 后除法并声称逐位等价。x0/x1 定义在**实际低精度 kernel 输出、进入 norm 之前**，不是未舍入的 FP32 输出。若希望另研究 FP32 核输出那是另一设计，不应在此静默更换。

补充判读：全层 11 理论上可桥接自然 t2；全层 00 仍保留真实 J 缓存、先前 t1 的影响、各臂自然响应的驱动，**不是完整无写入参照**。t3 无 hook 不会撤销 t1 写入，也不会撤销 t2 高层缓存已形成的差异。

## 4. Δ_H 包确实能省掉哪些形成，不能省掉什么

旧 source 路径在 [wsb_run.py:337–345](../../cache-write-signal-background-v1-2026-11-11/wsb_run.py#L337)：从 C[d] 的 conv history 取 donor，用 source C/H 的当前轨迹形成局部差，保存 `{'delta': h.deltas,'local':h.records}`。重放路径 L350–369 已直接载入同一个不可变文件，不重新形成 Δ。

每个 `packages/{receiver}/{donor}-H.pt` 已含全部 G14 层的 dense FP64 delta；其 local 中还保存源轨迹 q/k/vo/vd/β/log_decay/α。因而**重放 H 包不需要重新形成 donor C[d]，不需要 donor 的卷积影子，不需要 H-source 轨迹或来源回答续写**。不能重新算一次公式近似 Δ，然后称“复用原包”。

但这些包不含接收者的完整 C/H 前缀缓存，也不含 native_s 或 t2 状态；[asset-inventory.json:32–39](../../cache-write-signal-background-v1-2026-11-11/analysis/cpu-pairing-r01/asset-inventory.json#L32) 明列缺口。接收背景形成仍需 [wsb_run.py:308–317](../../cache-write-signal-background-v1-2026-11-11/wsb_run.py#L308) 的 prefix/clean/native needle 历史以及 H compose，除非另有逐张量可验证的等价现成 cache。当前没有这样的资产证明。

旧包的永久身份与位置见 [external-tensor-manifest.json](../../cache-write-signal-background-v1-2026-11-11/readiness/external-tensor-manifest.json)：服务器 `gqa-h20`，正式根 `/workspace/acupuncture/experiments/cache-write-signal-background-v1-2026-11-11/runs/formal-20261111-r01`。历史 CPU 报告记录 696 包逐 hash 核对，其中 H 来源对应原 348 配对。本轮没有重新读服务器包；“历史存在且有 hash”与“当前全包可读”分开。

计数与复用必须明确：

- 可取消的是 donor/source 形成及 source shadow，不是接收者形成。若同一输入既为 receiver 又为 donor，不能因此把其 receiver 形成费用也删掉。
- 同一 receiver/background/pair 的 t1 写入结果与实际 J 在四个 t2 臂间可以共享生成后深拷贝，但保存、恢复/拷贝和四条续写都需计入相应类别；不能共享被前一臂改动的 cache 对象。
- 新 shadow 是 **t2 recurrent kernel 调用**。历史 `counts['shadow'] += hook.base.n_shadow` 只接收 conv shadow 数：[wsb_run.py:294–298](../../cache-write-signal-background-v1-2026-11-11/wsb_run.py#L294)、[lvk_run.py:160–175](../../cache-local-v-k-v1-2026-11-03/lvk_run.py#L160)。直接复用会把新 kernel shadow 记成零，必须分列。
- t1 native kernel 加 Δ 的计算、t2 real/shadow kernel、natural continuation、接收背景重建、必要桥接/零补丁检查是不同成本。旧 `limits` 面向双来源四格，不能原封不动套新四臂。

这里只指出计数类别，没有产生新样本量、调用上限或预算。

## 5. 最小持久记录：足够复算局部 patch，不等于重跑全模型

| 必存内容 | 保存频率/用途 |
|---|---|
| receiver、donor、C/H、臂 c/s、层/头、timestep、实际输入 token/position，模型/代码/环境/包 hash | 防止不同背景、来源轨迹或时间混用；不要求本轮 tokenizer 运行 |
| 实际 J，保留计算时 FP64 dtype；对应请求 Δ_H 的文件/hash；S_after/S_native/S_reconstructed 的 shape/dtype/hash 与重建检查结果 | t1 每接收背景/配对一次，可跨四臂引用；不能只存请求 Δ 的 hash。若用户要求保存 J，就保存实际 dense J，不用秩一因素冒充逐位值 |
| **实际 x0、x1 原 dtype，以及 z 原 dtype** | t2 每臂每 G 层全头；可离线按冻结 norm 语义复算四种局部 patch，且保留“门抑制的哪些坐标仍进入分母”的坐标级证据 |
| norm weight 原 dtype、epsilon、张量形状/头顺序、完整 cast/乘法顺序、kernel/norm 来源 hash | weight/epsilon 每模型层保存一次或引用可验证的小静态资产；只有权重文件总 hash 不方便局部独立复算 |
| 实际送往 out_proj 的 norm 输出（原 dtype）及相应原 norm(x1,z) 输出身份；使用的 reciprocal-rms 标量 | 用于比较复算与实际注入，防止只复算了理想式；标量很小，可避免将后端 reduction 差误认机制差 |
| t1 快照身份、t2 shadow 输入未变/真实 S2 返回/conv cache 未变的检查记录；hook 调用次数与卸载结果 | 接收者桥接、shadow 只读、真实缓存和 t3 无 hook 的工程证据 |

对纯 norm patch 的复算，x0/x1/z/weight/epsilon/顺序已经足够；**不需要保存所有层的 attention KV、conv cache 或整模型 hidden states**。t1 native_s 可只在 t2 前暂存，用完释放。实际 J 按草案要求持久保存，可共享引用，不能按四臂复制存四遍。

此最小记录不承诺独立重演 t2 kernel 从 S1 到 x0/x1 的每个浮点运算。若正式设计还承诺这一级复算，需额外保存 G14 局部初始 state 与实际 q/k/v/g/β；那是额外数据承诺和存储成本，不应暗中以几个投影代替。仅验证 norm patch 和 shadow 副作用时，不应为“完整感”强行加全状态。行为终点所需的原始回答、token/终止状态及正式设计指定的任务读数仍须保存，本表不替代其分析合同。

## 6. 当前阻碍与可修事项

1. **可修、须写进设计：** 明确实际 J；明确 x0 的局部身份；二值端点直接选择；复刻 cast；每臂自然高层 S2；新 kernel shadow 单列。
2. **未来工程验收，当前未完成：** S1−J 的实际重建一致；11 与原 norm/原续写桥接；shadow 不改缓存；hook 在 t3 前卸载；冻结 runtime 与历史源码身份相符。
3. **资产就绪未核：** 原 H 包目前的服务器可读性、hash、shape/dtype，以及接收者形成所需历史依赖的当前可用性。不能据旧回执写成当前通过；也不需要为本次设计提前加载模型。
4. **不属于本审查的已通过项：** 四臂能否支持所承诺的科学归因、行为 estimand、无写入基线如何组织、科学阴性如何判读，由主作者与正式 Advisor 处理；本报告不以源码可实现替代研究价值判断。

来源锚纠正：初稿公共源码行号取自网页工具的文本视图，未核为 GitHub 文件物理行号，也不是本次读取历史服务器环境所得的行号。现统一以固定 tag 下的类/函数名定位；仓库内 `nl -ba` 已核行号保留。此修正不改变操作审查结论。
