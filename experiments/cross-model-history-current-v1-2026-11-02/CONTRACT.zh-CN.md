# 合同 r01（草案，未冻结）：跨模型实验 A——固定文字下的历史×当前干预

日期：2026-11-02。依据：[PLAN r3](../../docs/cross-model-foundation-v1-2026-11-02/PLAN.zh-CN.md)（a93917f）§2–§5、§7–§11；[F0 收据](../../docs/f0-receipts-cross-model-2026-11-01/)。共用代码：[`../cross-model-foundation-common-v1-2026-11-02/`](../cross-model-foundation-common-v1-2026-11-02/)。决策日志：同目录 [DECISIONS](../cross-model-foundation-common-v1-2026-11-02/DECISIONS.zh-CN.md)。

**状态：草案。** 冻结前必须同时满足：(1) 四模型 F1 预检全部闸门判定完成并登记；(2) §4.1 量程校准产出共同 d_high / d_low；(3) storage-receipt 按 §10.1 公式给出 Q，且实测深包字节数可装下；(4) DECISIONS 中标"待决"的条目已由计划所有者裁决。冻结时记录代码提交哈希与 freeze 文件 sha256。本文件不构成正式采集授权。

## 1. 身份与环境

| 模型键 | 路径 | 版本身份 | 层数 / 隐藏维 / MLP 中间维 | 取层（§4） | 取层的 mixer |
|---|---|---|---|---|---|
| qwen35_4b | /data/models/Qwen3.5-4B-851bf6e | HF 851bf6e8… | 32 / 2560 / 9216 | 3, 15, 26 | 全注意力、全注意力、线性注意力（相邻层均为线性注意力；26 的下一层为全注意力） |
| qwen3_4b | /workspace/models/Qwen3-4B-1cfa9a72 | HF 1cfa9a72… | 36 / 2560 / 9728 | 3, 17, 29 | 全注意力 |
| llama32_3b | /workspace/deployed_regime/models/Llama-3.2-3B-Instruct | ModelScope 镜像文件哈希（未独立核验 HF 官方权重） | 28 / 3072 / 8192 | 2, 13, 22 | 全注意力 |
| falcon_h1_3b | /workspace/models/Falcon-H1-3B-Instruct-01087ec4 | HF 01087ec4… | 32 / 2560 / 6144 | 3, 15, 26 | 每层并行 attention + Mamba-2 |

环境：`/workspace/acupuncture/.venv-bench`，torch 2.6.0+cu124，transformers 5.20.2；BF16 权重，`attn_implementation="eager"`；`torch.use_deterministic_algorithms(True, warn_only=True)`，`CUBLAS_WORKSPACE_CONFIG=:4096:8`；batch 1；无采样。Qwen3.5 只用文本路径（`Qwen3_5ForConditionalGeneration`，与 10-29 资产一致），不启用 MTP。停止集合取各模型 generation_config（Qwen3.5 无此文件时取 config）并并入 tokenizer eos：Qwen3.5 [248044, 248046]，Qwen3 [151643, 151645]，Llama [128001, 128008, 128009]，Falcon [11, 228]。对话模板：Qwen 系 `enable_thinking=False`；Llama `date_string="26 Jul 2024"`（模板默认读当天日期，必须固定，D6）；Falcon 无参数。四模型都已验证"模板渲染文本重新分词 == 模板直接分词"。

## 2. 输入

`panel.py`，面板 sha256 `e7f9e4f066690f9c2c120e5bb42e872bbcf5d74a34a5812b9114ddda357f4b4e`。36 情景（12 开发 / 12 分析 / 12 锁定，每份每任务族 4），每情景 7 行记录（D1），两事实版本互换目标行与一个干扰行的被问值。锁定包使用另一套措辞模板（行格式、引导语、问句、指令均不同）。四模型 token 数：Qwen3.5 174–208、Qwen3 172–207、Llama 185–216、Falcon 194–234，均在 128–256。

A 指令（主/锁定）：`Answer with exactly one of these two options: {c1} or {c2}. Reply with the option only.` / `Choose one option, {c1} or {c2}, and write only that option.` 两候选在同一情景两事实中的显示顺序相同，跨情景正确项先列 18/36。候选续写不加前导空格（助手轮在模板换行之后开始，D2），由"提示+候选"整体分词前缀相等核验；四分词器下候选长度 1–5 token，无切分失败。

## 3. 操作

- **P / q**：q 为最后一个提示 token（四模型均为模板的换行 token）；P 为其余全部。
- **H 操作位置**：字符区间完全落在记录块内的 token（四模型跨界 token 数均为 0）。
- **针**：每模型每层 `needle_set`：原生通道 = `random.Random("20261102|<模型键>|<层>|native").sample(range(中间维), 4)`；随机方向 j∈{0,1} = 以 `sha256("20261102|<模型键>|<层>|dir<j>")` 前 15 位十六进制为种子的 float64 标准高斯，单位化。冻结于运行前，与任何输出无关。
- **写入**：要求写入范数 N = |d|·s·√H。s = 开发 12 情景 × 2 事实 A 输入的清洁运行中，该层 MLP 前残差（pre-MLP norm 的输入）逐位置 RMS 的中位数，**去掉第 0 位置**（注意力汇点范数异常，D3）。原生针在 down_proj 输入第 c 维加常数 a = sign·N/‖m·W[:,c]‖，m 为 MLP 输出乘子（Falcon 0.078125，其余 1）；方向针在 MLP 模块输出加 sign·N·u。实际写入按位置记录（重算同 dtype 清洁输出求差）。
- **四格**：00/01 共享清洁 P 缓存，10/11 共享有针 P 缓存；每格从 deepcopy 出发处理 q；q 之后不注入；候选逐 token 在 deepcopy 上单 token 前向评分。
- **已有缓存时只许单 token 前向**（HF 混合层只在 seq_len==1 读恢复状态），引擎断言。

## 4. 读数

主 Y = 两候选完整对数似然的二元 softmax 中正确项的概率；H、C、J 按 PLAN §5 A2。辅助：首步停止集合概率、贪心首步是否停止、熵、top-32、完整 logits（fp16，轻记录）。分析规则、δ=0.05、四档判读、区间与多重性一律按 PLAN §9，不在此重述、不改。

## 5. 工程闸门（PLAN §8 映射；预检实测见 PREFLIGHT 报告）

| 编号 | 检查 | 判据 |
|---|---|---|
| G1 | 权重前后哈希 | 相等 |
| G2 | P 缓存复用 / 重复 prefill | logits 逐位相等 |
| G3 | 记录器开关 | 逐位相等 |
| G4 | 挂钩已装、无激活位置 | 逐位相等 |
| G5 | 零剂量全激活 | 逐位相等 |
| G6 | 缓存深拷贝隔离 | 分支前后共享缓存指纹相等 |
| G7 | 非激活位置 | 注入层 MLP 输出改变量严格为 0 |
| G8 | 实际写入/要求写入 | PLAN §8.6 写的是 ≤1%；**预检在 1/64 剂量下未全过（Qwen3 每组最少 89% 位置在 1% 内，比值 0.991–1.036），待决 D4** |
| G9 | 分段（P+q）对整段 prefill | 不要求逐位；Y 差 ≤0.005 且贪心一致。**干净 Y 饱和时 Y 差无检验力，补报对数概率差（D7）** |
| G10 | 新进程从磁盘快照重算四格 | logits 逐位相等、Y 差 0 |
| G11 | 深包分片关闭—重读—SHA256 | 全部一致 |

任一 G1–G7、G10、G11 失败：停止该模型 worker，修实现，不改剂量或换模型。

## 6. 深记录与存储

PLAN §7.2–§7.3 与 §10.1 原样适用：384 逻辑格（2 情景、每情景一个事实），局部轨迹位置 = 记录块首、1/3、2/3、末与 q；全层保存 block 输入、MLP 前残差、MLP 写入、最终表示（Falcon 另存 attention 与 SSM 写入）；P 末完整缓存。预检实测单个完整 A 深包字节数见 PREFLIGHT 报告，用于冻结前的容量核算。

## 7. 规模与停止

PLAN §5 A3 与 §11 不变：先开发量程校准（§4.1）、再 S0 小批次（四模型 × 分析集前 3 情景）、过扩容门后补齐。扩容只看工程与容量条件，不看结果。
