# 公开来源更新核对（2026-10-29）

本轮只做公开资料核对，没有加载或运行模型。已从 Lyra 官方工具新增的 Neuronary 公共 API 固定取得 **187 条记录及全部 187 条详情**；其中 **178 条标为 Qwen3.5-4B**，其余 9 条属于其他模型。完整参数事实在 [参数快照](sources/neuronary_parameter_snapshot.json)，统计、版本与来源边界在 [核对回执](public_source_updates.json)。第三方示例回答没有整批复制入 Git。

## 能直接交给本次 runner 的内容

- 178 条 4B 记录都有完整层、通道和带符号剂量；全部坐标合法，无空配方、零剂量、同条重复坐标或非有限数。每条 1–7 个通道，最大绝对剂量 1.5。178 个坐标与剂量组合彼此不同。
- 没有目标记录要求乘法、赋值、按条件触发或仅生成阶段注入。静态加法在这里指固定干预规则，**不指修改模型权重文件**。
- **167 条**沿用官方 Explorer 公开合同的固定尺度；单条记录多数未公布尺度数值，因此这是公开默认合同下的复刻约定，不是已知其原实验的逐项完全配置。
- **11 条**（jacobmolbio）明确要求：每道题先做干净前向；取离开层的 prompt tokens `1:` 残差 L2 下中位数，除以 `down_proj` 对应列的 L2 范数，冻结幅度，再加到全部 prompt 与生成 token，包括首 token。这 11 条明确模型 revision 为 `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`。
- 保留正式 `sampling` 与 notes 的有效设置，合计 9 个解码组合（将 0 与 0.0 等数值等价表示合并）。其中 **Can't stop giggling** 的 notes 补全 `temperature=0.7, top_p=0.8, top_k=20, repetition_penalty=1.1`；其正式 sampling 对象没有 top-p/top-k。原版对照应读取相同有效设置。
- [另存 4 个完整 notes 变体](sources/additional_notes_variants.json)：Primal Storyteller 加一通道、其采样替代设置、Caveman harder 五点组合、Caveman 六点不稳定组合。没有自动展开所有剂量曲线或反向控制备注。

参数快照保留全部 187 个 ID，作者名、原始 recipe 参数字符串、来源链接、日期、标签、采样和方法字段，以及详情响应 SHA-256。API 只有日精度 `date`，没有创建或更新时间；不能称其为精确发表时刻。4B 记录中 156 条标 10 月 28 日、21 条标 10 月 27 日、1 条标 10 月 26 日。`author` 是公开服务的作者字段，不是本次重新认证 X 身份的结果。

## 固定版本与尺度来源

[Lyra neuron-explorer](https://github.com/lyramakesmusic/neuron-explorer/commit/6a6f0e95bf49ad6626940021148f775d7d55d1e4) 从旧 `e566e83…` 前进 10 个提交；本次固定为 `6a6f0e95bf49ad6626940021148f775d7d55d1e4`。主要新增 Neuronary 查询、取详情、发布和修改接口，以及采样参数处理；原 `agent_methodology.md` 没有变化。公共只读接口由 [agent_mcp.py](https://github.com/lyramakesmusic/neuron-explorer/blob/6a6f0e95bf49ad6626940021148f775d7d55d1e4/explorer/agent_mcp.py#L202-L322) 明确提供，不需要凭据。本轮没有发帖、修改或回报复现结果到该服务。

[runtime.py 的尺度读取逻辑](https://github.com/lyramakesmusic/neuron-explorer/blob/6a6f0e95bf49ad6626940021148f775d7d55d1e4/explorer/runtime.py#L543-L563) 优先读取 `stats/q35-4b_L{layer}.npz` 的 `resid_norm_q10_50_90[1]`；没有该文件才在固定 `REFERENCE_TEXT` 上做干净前向，跳首 token 后取 `torch.median`。当前 Git 树没有这 32 个 stats 文件，`stats/` 被 gitignore 排除，所有 recipe 详情也未给 32 层数值。`act_scale.npz` 是神经元激活范围，不能代替残差尺度。预计算 stats 的分位数分支与 fallback 的下中位数分支也不能混称同一个标定值。

官方运行器使用 BF16，关闭 thinking；默认贪婪、重复惩罚 1、seed 0、min-p 0。重复惩罚覆盖完整 prompt 加已生成 token，无窗口。正温度时作者实现使用 CPU generator 采样；使用其他生成实现需要在本次回执中保留差异。作者运行器未固定模型 revision。

[makefunstuff/qwen-neurons](https://github.com/makefunstuff/qwen-neurons/commit/2a780d8a2fdc3735bac13987da93148a8683102c) 仍是旧 `2a780d8a2fdc3735bac13987da93148a8683102c`，24 个 preset 没有新提交。其 Zoo 对 Lyra 的归因来自第三方仓库，不能升级为逐项已找到作者原帖。

## 新资料给出的经验及限制

公开词典中已有海盗、惊恐、迎合、宗教叙述、说唱、主观化、不同话题偏置等正式带剂量记录；这些名称是作者为观察到的输出取的标签，不是本项目已证实的人格或功能模块。

本轮详情包含几类作者报告的查找路径：从 system-prompt 风格对比产生的残差方向找受影响最大的 MLP 通道；按 steer-lens token 的语义集中程度排候选再生成筛查；用笑话/非笑话语料中回复起点激活与笑声开头概率的相关性定位；用短句和完整句的匹配对比寻找省略语法的组合。多篇记录报告持出题、随机通道对照、盲评和复测，但这些均为外部作者叙述，本次未重算其统计。

失败信息同样保留：Thermal-water 标为探索性且严格验证失败；Plasmid 曾失败，后续同时更换题目和输出上限；Nuclear 第二轮仍待做；Meow 和 Batman 记载过早期未通过再复测。Caveman harder 与六点变体明确存在塌缩或不稳定。部分 treetowntree 记录明确用了 RTX4090/PyTorch，并称其他批次用了 MLX。不能把所有记录当成同一后端、同一题集或同一质量水平的结果。

本轮不是 X 登录评论区的新一轮抓取。来源字段实际指向 X 的条目保留其 X 链接，其余准确标为从官方工具所连接的公开词典取得。只固定这 187 个 ID，没有继续无限抓取全站。
