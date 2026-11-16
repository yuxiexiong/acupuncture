# TGA-01 / A023 实现一致性审查

2026-11-16，同一独立 Advisor。对照已审 A022 最小测量卡读取 IMPLEMENTATION、tg_hooks/run/analysis、test_tg、cpu_accept，回看旧 fwd/L.forward、复用计量/授权代码及原生 recurrent kernel。未运行模型、GPU 或新实验，未改源码。

## 关键判断

**当前实现维持已审科学对象；allow_mutation_on_saved_tensors 属于可接受的梯度工程处理，不是被禁止的 kernel/模型替代。** 它保留 backward 所需的原值，不改变 forward 的原位缓存更新、输出 dtype 或依赖图。代码将 forward 和 backward 放在同一上下文，符合 [PyTorch 2.6 官方 API 合同](https://docs.pytorch.org/docs/2.6/autograd.html#torch.autograd.graph.allow_mutation_on_saved_tensors)。同一原 kernel 的有/无 cache.copy_ 输出及梯度对照、真实设备逐位端点桥接，仍必须通过；只凭 forward 相同不足以认可梯度。

旧 fwd 的 inference_mode 包装确会禁图；本轮 t2 直接调用同一个 L.forward 并启用 grad，是测量所需的包装调整。原生控制和冻结 P 都执行 FP64 native+control 再 cast 原 dtype；native.double 不 detach，独立零叶子及后续 requires_grad/allow_unused=False 检查保留。历史缓存独立复制，权重冻结且无 optimizer，符合只测 t2 surrogate 的合同。

## 初审发现及修复复核

**I1：形成预算上界误作完成精确值。** 初稿要求 formation_token_forwards=56R；旧实际工程为322而不是336、正式为2556而不是2688，会使正确运行在收尾误报失败。修订已改用冻结 ledger 的 Σ2(e−p+1) 核精确完成值，56R 仅保留为预算上界；新 panel-budget 回归针对这一差别。已回读通过。

**I2：backward/桥接失败丢失已获得端点和梯度。** 初稿在 backward 完成并返回后才保存 logits，返回后的桥接又早于梯度登记。修订将 logits/score 放入 hook 失败上下文，已得 gradients 先登记再核有限性，调用方返回后立即保留 g；failure 文件同时保存当前 hook 值、梯度、t1 states/records 与记录。新增直接调用 task_forward 的两 tap D−Y 解析梯度及故意 backward 失败测试。已回读主修；另外已指出 logits 快照应先于非有限断言，避免数值失败向量被丢失。这只是同一现场保存修复，不改变调用数或设计。

## 其余已核合同

- 零控制按原11 native/patch，冻结直接 P 按原X native/patch核各 tap，候选/停止分数及完整 t2 logits SHA桥接；没有使用包含继承漂移的总差。多 tap 原生图保持，hooks在异常退出时清理。
- D−Y 索引沿旧 token 映射；P_H 的方向取反，校准与2×2投影符号一致。MAE、零预测减半、偏差、接收者误差覆盖、合格符号率及无定义处理符合原卡，所有近零对仍进入误差；pair分位数显式标记未加权。cross始终只是保存的surrogate诊断，只有两背景校准合取通过才准解释。
- 固定工程20/正式168对；形成/t1/两类t2及backward计数，没有自然回答。每次forward/backward前检查上限，失败也计费。正式只在数值/来源/图/预算通过后进入，不由工程校准阳性选择是否继续。
- 复用授权输出绑定、全部既有尝试计费、单worker锁、监督时间/全runs存储、工程保守投影及正式门槛。pair_total含forward/backward/桥接/IO，形成计量另列，未用只算梯度的时间冒充总成本。
- 源冻结绑定新代码/方案/旧输入资产及当前外部源码；没有恢复BRC/WUS或扩大样本/层/剂量。实际新freeze和CPU回执仍须绑定修订后的文件。

## 核验深度与进入条件

已实读早期 cpu-local-r01：5项TGA测试执行通过、1项真实上游跳过，另7项RCS hook通过，0模型前向/CUDA未初始化。新计数和 task_forward 回归的源码已读，作者报告新增后本地7通过/1上游待服务器；在本次记录时最终服务器回执尚未同步，不冒称已完成设备或真实上游验收。

已核范围没有科学定义偏移；I1关闭，I2的最后快照顺序落实后没有其他已知实现阻断。可在当前用户授权下完成服务器CPU、来源冻结，再进入规定的GPU工程；不新增审批。真实backward/缓存/端点/资源验收仍是硬门槛，工程通过不预先证明一阶预测成功，科学失败不自动追加。

### 最终局部复核

随后已回读 logits 快照先于有限性断言，I2关闭。已实读 cpu-local-r02：TGA共8项（7通过、真实上游1项跳过），RCS hook7项通过，0模型前向/CUDA未初始化、source_stable=true，source_hashes与当前全部本轮Python文件一致。服务器真实上游/新freeze仍待最终验收绑定。**当前源码审查无遗留实现阻断。**
