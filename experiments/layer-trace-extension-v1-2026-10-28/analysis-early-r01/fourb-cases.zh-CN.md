# 4B 早层：三个失序链与反例（既有轨迹只读分析）

这些是人工挑选后核实的具体案例，不是总体发生率。全部来自已验收的本地归档，8 个案例的 `source_token_ids_match` 均为 true。没有加载模型、没有新增实验。完整逐步 logits 与选定步骤的全部 32 层数值见 [fourb-cases.json](fourb-cases.json)，复算见 [fourb-cases.py](fourb-cases.py)。

## 读数口径

- 层编号从 L0 开始。step 0 是完整 prompt 的最后一个输入位置，尚未生成任何回答；step 2 是生成第 3 个 token 前的计算。
- 干预加在指定 MLP 的 `down_proj` 前一个通道，覆盖 prompt 和 decode；`delta_norm` 为组件输出差向量范数，`relative_delta = delta_norm / clean_norm`。不是损伤率，也不是因果贡献份额。
- clean shadow 从 prompt 起全程无针、使用独立 cache，被强制喂入干预分支已经产生的相同 token 历史。它不是原版自由回答，也不是“保留干预历史 cache，仅当前步撤针”。
- “首个严格分叉”在此按实际生成 token 的 clean logit 严格低于 clean 最大值判定，避免 BF16 并列最大值与 top-k 排序造成伪分叉。分叉本身不代表答错。
- 本报告的首步层表都对齐 prompt 最后位置。它们能显示变化传播到哪里，不能识别哪一条下游边必要或充分；最大亮点不能直接叫根因。

## 案例 1：L0 N4146，同一点从能回答到立即结束

问题 Q04：列出整理书桌的两个步骤，严格两行。

原版：
> 第一步：将书桌上的物品分类并归位。  
> 第二步：清理桌面杂物，只保留当前使用工具。

`4b-L00-N004146-D+1__Q04`：只生成一个 `<|im_end|>`，正文为空。首步 L0 attention 完全相同；直接变化在 L0 MLP，Δ=2.8370。下一层 attention Δ=2.5037、MLP Δ=2.6618；从此影响后续层，最后改变第一个输出决策。

| step 0 组件 | Δ | 相对 Δ | clean/steer 余弦 |
|---|---:|---:|---:|
| L0 attention | 0 | 0 | 1.0000 |
| L0 MLP | 2.8370 | 5.6869 | — |
| L0 residual | 2.8368 | 1.3530 | 0.5929 |
| L1 residual | 4.2706 | 1.8704 | 0.6273 |
| L2 residual | 4.1599 | 1.8391 | 0.4878 |
| L7 residual | 7.0179 | 1.0837 | 0.3708 |
| L15 residual | 11.6776 | 1.2272 | 0.2531 |
| L31 residual | 69.9652 | 1.2994 | 0.4238 |

末端读出很明确：原版“第一步”logit 27.0，干预后 6.1875；EOS 从 9.3125 到 15.3125。停止优势（最佳 EOS 减最佳非 EOS）从 −17.6875 变为 +3.0625，因此 greedy 直接结束。这里是停止决策被翻转，不是先生成了乱码才停止。

同点剂量反例：

| 剂量 | 输出 | 首步末层 residual 相对 Δ / 余弦 | 首步停止优势 |
|---|---|---:|---:|
| +0.25 | 两行有效步骤，24 token | 0.1841 / 0.9852 | −17.0000 |
| +0.5 | 两行有效步骤，27 token | 0.7200 / 0.7940 | −8.2500 |
| +1 | 只有 EOS，1 token | 1.2994 / 0.4238 | +3.0625 |

+0.5 正文：“第一步：整理桌面物品，将不需要的物品移出桌面。第二步：将桌面物品分类摆放，保持桌面整洁。”虽然网络大面积有差异，而且第 3 token 就和原版分叉，任务仍完成。不能用“看见全图亮了”判定功能已坏，也不能把这一个点的剂量阈值推广到所有通道。

## 案例 2：L2 N5063，进入标记循环后持续把出口压下去

`4b-L02-N005063-D+1__Q04`：128 token 是 64 次 `<think>` 加双换行，达到长度上限，没有正文。

首步 L0–L1 所有组件及 L2 attention 差为 0；变化始于 L2 MLP（Δ=3.4042、相对 Δ=2.7844）。紧接 L3 attention（该层是 self-attention）Δ=8.8509、相对 Δ=3.9414；L3 residual Δ=7.6551。L4/L5 residual Δ反而降为 7.4379/6.6979，之后才又变化到 L31 Δ=65.0392、相对 Δ=1.2079。传播不是逐层单调放大。

首 token 原版偏好“第一步”，干预改为 `<think>`；后者在 clean 下比最大 logit 低 14.75。此时最佳 EOS 仍比最佳非 EOS 低 0.3125，因此没有像案例 1 那样立即停止。

| 生成 step | 已有关键前缀 | clean shadow 首选 | 实际输出 | 实际 token 的 clean logit 距最大值 |
|---:|---|---|---|---:|
| 0 | 原始 prompt | 第一步 | `<think>` | −14.7500 |
| 2 | `<think>\n\n` | `</think>` | `<think>` | −5.9375 |
| 4 | 已出现两次 `<think>` | `</think>` | `<think>` | −6.4375 |
| 20 | 重复前缀 | `</think>` | `<think>` | −1.8750 |
| 126 | 长重复前缀 | `</think>` | `<think>` | −0.7500 |

所有 64 个 `<think>` 选择都严格不是 clean shadow 的最大 logit token，另外 64 个双换行是 clean 支持的续写。因而本例可观察到：持续干预连同其内部状态历史，多次把原本更偏好的闭合标记改成再开一个标记。数据支持这一具体竞争变化；还不能说某个下游层就是“循环控制区”，也不能证明实际撤针便一定恢复正常回答。

同为 L2 的另一种循环要分开：`4b-L02-N005251-D+1__Q05` 从 `<think>\n\nThinking Process:` 开始，反复英文描述“用户要求简短中文回答”，128 token 截断。它有 112/128 个实际 token 也是 clean shadow 的并列或唯一最优；开头改轨后，大量后续词只是同一坏前缀下两分支都容易续写的词。这与 N5063 每个循环入口都被持续改变不同。同点 +0.5 的 Q05 则是 39 token 正常社交建议，首步最终 residual 相对 Δ=0.4115。

## 案例 3：L4 N5428，外壳保留而填入无关人名

`4b-L04-N005428-D+1__Q04` 输出：
> 第一步：李达。第二步：李斯。

11 token 后自然 EOS。首步 L0–L3 与 L4 attention 完全相同；L4 MLP Δ=5.3957，L5 attention Δ=1.7112、MLP Δ=3.5949，L31 residual Δ=49.9866、相对 Δ=0.9284。首两个 token 仍是“第一步”“：”，故仅看输出开头会误以为正常。

到 step 2（此时原版与干预文本历史仍都是“第一步：”），原版首选“将”，干预输出“李”。“李”在 clean 下比最大 logit 低 18.6094，而干预分支选中了它。该步 L4 MLP Δ=5.4035，L23 residual 相对 Δ=1.081、余弦0.255；L31 residual 相对 Δ=1.230、余弦0.229。之后继续生成“达”“。第二步：李斯”。这是格式骨架部分保留、内容选择失去题意约束的可见例子；它不是编码字节损坏，也不能仅凭人名就给 N5428 命名为“姓名神经元”。

反例：`4b-L03-N007666-D+1__Q04` 仍输出两行可理解步骤：“第一步：整理书桌。第二步：将物品分类摆放整齐。”首步 L31 residual 相对 Δ=0.7694、余弦0.7986；也在 step 2 改写了词。再次说明“内部变化很大”和“第三个 token 分叉”本身都不能代替任务效果评判。

## 这几条链最直接支持什么

1. **注入点到后续计算再到输出竞争的链条已经能看见。** 首步不受回答文本不同干扰：注入层之前不变，MLP 直接改变，下一层 attention/MLP 开始改变，最终 logits 发生不同类型翻转。
2. **至少要区分三种终点：EOS 提前胜出、特殊标记循环、题意无关的内容填充。** 它们不是一个“乱码程度”标尺，也不能自动合并成统一脑区。
3. **剂量改变了竞争的结果，但有大扰动仍有效回答的反例。** 带文本/词表决策的 3D 轨迹比只看亮度更有价值。不同层/通道不能只比较绝对 Δ，因为正常 residual 范数随深度变化。
4. **尚未定位必要的中介组件。** 当前是配对观察，不是逐层修复/消融；也没有把 prompt 阶段与 decode 阶段注入、当前步效应与缓存累积分别拆开。Qwen 的 attention 中含 GatedDeltaNet/linear-attention，不能把所有亮点解释为普通 attention 权重变化。

## 本地证据入口

| case ID | 轨迹（归档，gzip JSON） |
|---|---|
| `4b-L00-N004146-D+0.25__Q04` | [trace](../../early-layer-mechanism-v1-2026-10-28/archive-r01/execution-r01/survey/4b-shard-0/traces/0043-4b-L00-N004146-D+0.25__Q04.json.gz) |
| `4b-L00-N004146-D+0.5__Q04` | [trace](../../early-layer-mechanism-v1-2026-10-28/archive-r01/execution-r01/survey/4b-shard-1/traces/0027-4b-L00-N004146-D+0.5__Q04.json.gz) |
| `4b-L00-N004146-D+1__Q04` | [trace](../../early-layer-mechanism-v1-2026-10-28/archive-r01/execution-r01/survey/4b-shard-0/traces/0051-4b-L00-N004146-D+1__Q04.json.gz) |
| `4b-L02-N005063-D+1__Q04` | [trace](../../early-layer-mechanism-v1-2026-10-28/archive-r01/execution-r01/survey/4b-shard-1/traces/0163-4b-L02-N005063-D+1__Q04.json.gz) |
| `4b-L02-N005251-D+0.5__Q05` | [trace](../../early-layer-mechanism-v1-2026-10-28/archive-r01/execution-r01/survey/4b-shard-0/traces/0188-4b-L02-N005251-D+0.5__Q05.json.gz) |
| `4b-L02-N005251-D+1__Q05` | [trace](../../early-layer-mechanism-v1-2026-10-28/archive-r01/execution-r01/survey/4b-shard-1/traces/0188-4b-L02-N005251-D+1__Q05.json.gz) |
| `4b-L04-N005428-D+1__Q04` | [trace](../archive-r01/execution-r01/six-layer/survey/4b-shard-0/traces/0059-4b-L04-N005428-D+1__Q04.json.gz) |
| `4b-L03-N007666-D+1__Q04` | [trace](../../early-layer-mechanism-v1-2026-10-28/archive-r01/execution-r01/survey/4b-shard-1/traces/0275-4b-L03-N007666-D+1__Q04.json.gz) |

源回答与其原始文件/hash 见相应 `sources.jsonl` 及本目录 JSON 的 `source_provenance`；原版全文已随本目录 JSON 保存。数据的 hook 与 stop advantage 定义见 [trace_engine.py](../../early-layer-mechanism-v1-2026-10-28/trace_engine.py)。
