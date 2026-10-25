# Acupuncture：研究状态与后续方向

更新日期：2026-10-26。项目名称与唯一 GitHub 仓库已经由用户指定；本文接续聊天中的研究讨论，不代表新增模型实验已获执行授权。

## 已有证据

首轮 Qwen3.5-4B 的 24 题原文及完整分析见 [实验目录](../experiments/qwen35-neuron-steering-2026-10-25/)。普通问题在双通道动态干预后出现主动恐吓、操控或破坏性建议，同时伴随任务失败、重复与语言退化。不能据此宣称能力完整保留或模型具备稳定的“邪恶人格”。

完整性依据是独立 [停止收据](../experiments/qwen35-neuron-steering-2026-10-25/stop-after-q24/receipt.json)。原 40 题运行 receipt 保持历史 `started` 状态，退出码 143 对应用户要求的停止；不能改写成全 40 题完成。

能力基准材料另见 [既有协议](../experiments/qwen35-neuron-steering-2026-10-25/benchmark-quick-2026-10-26/PROTOCOL.zh-CN.md)。它记载了另一轮授权及吞吐修订。本次仅迁移已有材料；基准是否完成及具体分数须读取对应结果收据，不能根据代码或协议推断。

## 新找到的原作者材料

截图作者 GitHub 主页与 X 账号互链：[lyramakesmusic](https://github.com/lyramakesmusic)。项目为 [neuron-explorer](https://github.com/lyramakesmusic/neuron-explorer)，此次读取固定提交 `f79b2196e29aacbad89684938baac8d97b172fd1`。

已保存 [两神经元缓存读数](../experiments/qwen35-neuron-steering-2026-10-25/literature-2026-10-26/author_cache_two_neurons.json)：

- L14/N8949 的正向干预在作者缓存中提高粗口与 `evil` 等词的下一词对数概率。
- L13/N7956 的正向干预提高 `normal`、`normally`、`正常` 等表达；截图采用的负向效果没有同样清晰的词族，不能命名为“去掉安全”。
- 缓存剂量为 ±0.8。对应脚本在四个短上下文上做单次前向；这不是完整回答，也没有确认自然激活条件。作者没有固定公开缓存的模型权重 revision。
- 直接 logit lens 与经过后续层的 steer lens 可以不同，不能仅靠权重列词表投影确定功能。
- 作者 live runtime 使用固定参考残差尺度，首轮本地实现则逐题校准；原作者显式使用聊天结束标记。后续对齐应使用新运行，不改旧证据。

相关原始研究：[Perturbation Probing](https://arxiv.org/html/2604.27401v1)、[When Thinking Backfires](https://arxiv.org/html/2509.00544v4)、[User Persona Subspaces](https://github.com/tz1211/user-persona-geometry)。其中 Qwen3-4B 的证据不能直接当作 Qwen3.5-4B 这两个通道的功能认证。

## 待讨论与执行的路线

用户于 2026-10-26 明确：Acupuncture 的贡献目标是**定位方法与可检验规律**，已有坐标的行为变化仅是起点。当前路线调整为“源模型功能画像 → 冻结定位规则 → 同家族预测验证”；“前额叶”只作类比，不预设存在统一脑区。结构、原作者方法、Qwen-Scope 和社区图谱的查证，以及未执行方案见 [定位研究方向记录](acupuncture-localization-direction-2026-10-26.json)。

先在源模型建立功能画像，再迁移：分别检查自然激活条件、正负干预的输出分布、单点与双点组合、剂量效应及同强度随机对照。将词语偏移、主动有害建议、拒绝措辞、任务完成和语言退化分开。

迁移分清三种主张：原坐标直接移植；不依据目标有害输出选点的候选对应映射；在目标模型重新搜索。后者不能冒充无目标反馈的迁移。

讨论中的候选面板是 Qwen3.5-2B/4B/9B、Qwen3-4B、Qwen3-VL-4B-Instruct，以及 Gemma-3-4B-it、Llama-3.1-8B-Instruct。2B 的中间维度为 6144，两个原编号均越界；跨族要检查模型原生模板、停止标记、有效扰动强度和语言基线。纯文本测试不证明图像任务上的迁移，MoE 需要另行定义专家与路由。

旧 24 题仅用于复核和开发；确认题须事前冻结并与匹配文本分离。前次讨论提出 256 段匹配文本和 96 个新确认场景作为预算草案，尚未固定为执行合同。保留全部模型原文，盲评有害建议、任务完成与连贯性，并单列技术异常；按场景做成对比较，不把中英文版本或预算延长当作独立样本。

本项目参考 Han Lab 本地总结中“竞争解释、强简单对照、真实终点、完整成本、允许失败”的论证方式。这些总结不是本现象的直接证据，也没有证明迁移已经成立。
