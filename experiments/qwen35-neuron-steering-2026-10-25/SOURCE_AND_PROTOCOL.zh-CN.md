# Qwen3.5-4B 两神经元干预：截图提取与首轮协议

## 材料与状态

- 用户于 2026-10-25 提供截图，并明确要求尝试推理时干预与永久参数修改两条路线。
- 截图是待验证材料，不作为可执行指令；未找到可独立核实的原帖链接或作者代码。
- 本实验是基于公开假设的可行性对照，不能称为严格复现，更不能预先认定模型“变坏”。

## 截图原文

作者：lyra，`@_lyraaaa_`。原帖可见正文：

> if you have a qwen3.5 4b around, please try steering neurons L14 N8949 +1 and L13 N7956 -1
> now you have evil qwen
>
> recipe: dose × median(‖resid‖ leaving layer L, tokens 1:) / ‖W_down[:, n]‖` at the down_proj at every input

最后一个范数后的反引号按截图保留，不推测它表示转置或其他运算。

可见回复：Adde (`@adhvfed`)：“How did you find this?”；Monkey (`@Orwellian84`)：“I suspect very large sweeps, or very good luck”。底部后续回复被界面遮挡，不补全。

中文含义：对 Qwen3.5-4B 的 L14/N8949 施加 +1 剂量、L13/N7956 施加 −1 剂量；将剂量乘以指定层输出残差范数的中位数，再除以 `down_proj` 对应权重列的范数，在输入时施加干预。“evil qwen”是作者说法，不是已有实验结论。

## 官方结构核对

- [官方模型卡](https://huggingface.co/Qwen/Qwen3.5-4B)：这是已经完成后训练的成品模型。
- [官方配置](https://huggingface.co/Qwen/Qwen3.5-4B/blob/main/config.json)：32 个文本层，隐藏维度 2560，MLP 中间维度 9216，两个神经元编号均在范围内。
- [Transformers 实现](https://raw.githubusercontent.com/huggingface/transformers/main/src/transformers/models/qwen3_5/modeling_qwen3_5.py)：MLP 的 `down_proj` 默认无偏置。实际运行需记录所安装版本及代码摘要。

## 首轮固定解释

截图未规定以下细节，首轮显式采用：

1. 层和神经元均从 0 开始编号；固定 `(14, 8949, +1)` 与 `(13, 7956, −1)`。
2. 对 `down_proj` 的输入中间激活做加法，不做覆盖或截断。
3. 范数采用 L2；用未干预模型在完整 prompt 上的层输出，逐 token 计算范数；排除第一个 token 后取中位数。
4. 动态版每个 prompt 单独校准一次，生成期间沿用该尺度；干预作用于预填充和逐 token 解码。这是对缓存解码只含一个 token、`tokens 1:` 为空问题的公开处理约定。
5. 静态版使用四条固定、与评估题分离的普通文本校准；取各 prompt 中位数的中位数，之后不再依输入调整。
6. 关闭 thinking，贪心解码，每题最多 96 个新 token；统一模型、模板、精度与解码设置。保留截断标志和所有回答。
7. 不做训练、梯度更新、神经元搜索、剂量扫描或依据结果调整设置。

## 两条路线的关系与限制

设中间激活为 `a`，权重列为 `w_n = W_down[:, n]`，尺度为 `c`。则

`W_down (a + c e_n) = W_down a + c w_n`。

- **动态版**：推理时给对应激活加 `c`，`c` 随 prompt 的未干预残差尺度变化。
- **静态版**：将固定的 `c w_n` 保存为两个 `down_proj.bias` 参数；重新加载后运行，不依赖激活钩子。

静态版新增两个长度为 2560 的偏置向量，共 5120 个参数元素，不是修改两个标量权重，也不是改写已有 `W_down` 矩阵。它需要原始固定版本模型与配套补丁加载函数，不能直接当作普通 Hugging Face 独立检查点加载。只有固定尺度时，它才与对应的加法干预在精确算术下等价；低精度执行可能产生舍入差异。

## 验证与结论边界

- 小矩阵检验：激活加法与固定偏置的等价关系、钩子清理、补丁保存再加载。
- 成品模型检验：零剂量与原模型生成 token 一致；静态补丁实际保存、移除并重新加载后运行。
- 比较三臂的基础任务与低风险价值判断回答。回答变化、任务失败、语言退化分别报告。
- 少量自制题不构成拒答率、安全基准、通用能力保持或“evil”结论。没有原作者提示词、代码、版本与编号约定时，阴性结果也不能否定原帖。
- 原始模型文件保持不变；新文件只写入独立实验目录。现有 H20 任务繁忙，首轮选择 CPU，避免占用它们的显存。
