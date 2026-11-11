# 016．Llama旧版十点乘十档合并扫描

[返回总时间线](../README.zh-CN.md)

**时间定位**：已提取运行收据的最早时间锚点（可含预检） 2026-10-28T00:16:14.491466+08:00；不能当作全部子运行起止。

**当时的目的与设计**

原先把每层十点与正负剂量组合在一轮里执行。

**实际过程、结果与后来更正**

用户要求拆开后中止，保留479份回答，其中471干预、8原版。这批没有混入后来正式的独立逐层调查与单点剂量调查，停止前后的路径和计数单独列出。

**来源身份**：`llama31-layer-dose-survey-v1-2026-10-28`；本章主体来源提交 `7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8`。下方原文中的状态是各文件写作时的状态，不能把早期“尚未运行”覆盖后期正式收据，也不能将后期结果倒填进早期设计。


## 原设计、执行过程、结果与更正全文

以下按“设计与题目 → 工程/执行记录 → 结果/更正 → 其他历史说明”组织；同类内没有可靠时间时保留路径顺序，不冒充严格先后。正文未删段；仅为本章节重排标题层级、把相对链接指向固定提交。原始字节另外完整保存。

### 原件 1：Llama 3.1 8B Instruct 全层十点正负剂量实验合同 v1

原路径：`experiments/llama31-layer-dose-survey-v1-2026-10-28/PROTOCOL.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/llama31-layer-dose-survey-v1-2026-10-28/PROTOCOL.zh-CN.md) · [单独阅读副本](../library/9035ec8c7f24235c.md)；SHA-256：`9035ec8c7f24235c506c9a9bd9b97ff2b324c9d117081bd990144ac688db0b5c`。

---

#### Llama 3.1 8B Instruct 全层十点正负剂量实验合同 v1

日期：2026-10-28（北京时间）。状态：用户已授权准备、CPU/GPU验收及验收通过后的正式采集；先确认既有千问实验结束与GPU释放。本合同是新独立运行，旧千问合同、代码、原文和收据保持原样。

##### 授权与证据边界

用户要求：“拉玛3.18B做同样的事情……每一层取10个点……跟千文模型同样的剂量……除了模型不一样以外，其他东西全部设置为一样的确认可比……直接改合同，改代码，然后上卡……正剂量负剂量对照……两侧的对称。”后续明确选择“使用8B-Instruct”。这一授权允许本轮准备、测试与正式执行，无需测试后再问一次；不授权恢复旧根因、判断报告、跨家族迁移方案或新增其他Llama型号。

Material Passport：材料为既有千问原八题/协议/冻结实现、官方Llama资产与本轮新实验；计算结果在实际运行前不视为已验证。此处采用模型辅助工程审查，不作人工盲评声明。代码验收、正式生成、原文归档、开放阅读分别记录。

##### 固定模型与可比设置

唯一目标为 `meta-llama/Llama-3.1-8B-Instruct@0e9e39f249a16976918f6564b8830bc894c89659`；32层，hidden 4096，gated MLP宽14336。远端已核验官方资产路径 `/workspace/models/Llama-3.1-8B-Instruct-0e9e39f2`。不替换为Llama3.0、Base、量化或其他微调版本。

与千问逐层/剂量实验相同的设置：

- `questions.json`逐字节沿用原Q01–Q08，中文共同指令逐字相同；不改成新题或英文。
- 每次只干预一个原生gated MLP通道，在进入down_proj前做加法；提示全部位置和后续全部生成步均注入。
- 每题在干净模型完整提示上校准，m为对应block输出的逐token L2中位数、排除第一个token；`c(d)=d*m/||W_down[:,n]||₂`。该题该点每档由同一干净double比例独立转BF16，不缩放已经舍入的+1幅度，不累积正负针。
- 正负绝对值为1/16、1/8、1/4、1/2、1，恰好镜像；无±0.75。正负始终使用同一层、同一通道、同一题及同一干净校准。
- BF16、eager attention、实际batch=1、每worker四CPU线程、seed0、deterministic algorithms、greedy `do_sample=False`；沿用同一generate函数与fresh context/cache实现。
- 最大128个新token，正常EOS保留实际长度和结束token；达到128保留完整128，不补齐、不续写、不因空答/乱码/循环/无预期变化重试。每次撤hook，不训练，不静态改权重。

模型原生差异必须记录：tokenizer、词表、聊天模板、BOS/EOS、模型结构与参数本身不同。Llama使用自己的原生模板，固定模板日期字符串`26 Oct 2026`，保存实际rendered context和input token hash；BOS只有一个，官方停止ID为128001/128008/128009，pad为128009。禁止把千问结束ID248044/248046硬套给Llama。Llama没有Qwen thinking开关，记为不适用；不声称两模型的模板字节/token序列完全相同。共同中文内容保持相同，128token分别以各自词表计，并非等字符预算。

Llama资产generation_config的采样默认值不会覆盖显式greedy调用。使用真实Transformers解析后的生成配置审计beam、penalty、min length、forced/suppress token等；不得默默增加重复惩罚、beam或最短长度。temperature/top_p在greedy不生效，原值仍入metadata。模型库和CUDA环境版本入运行收据。

##### 选点、剂量与数量

按旧逐层调查的规则，每层独立使用 `random.Random("acupuncture-layer-survey-v1:llama31-8b-instruct:{layer}").sample(range(14336),10)`，通道排序。32层共320个不同点，在模型输出出现前冻结`samples.json`，正负全档共用，不按效果换点。层号从0开始。

正式新增320点×10个非零剂量×8题=**25,600份干预回答**，3,200个条件；另有8份唯一原版，合计**25,608份唯一来源**。2,560个“点×题”组各11栏，共28,160展示单元。0为共享无hook原版；每层展示同一套8原版，不把重复展示算新科学来源。所有正式来源本轮新生成，不复用其他模型回答；预检不计正式科学样本。

展示顺序固定为−1、−1/2、−1/4、−1/8、−1/16、0、+1/16、+1/8、+1/4、+1/2、+1。运行按层→通道→题→剂量交错，剂量运行次序为−1/16、+1/16、−1/8、+1/8、−1/4、+1/4、−1/2、+1/2、−1、+1；每次独立，不解释为累积注入。

两H20各一个worker。沿用旧十点逐层调查的全局排序点序号mod2分片：每张卡每层各5点，不是按层奇偶。各worker12,800干预回答；shard0另生成8基线，故记录数12,808与12,800。两worker原八题clean calibration和技术基线须在预检精确一致。

覆盖差异公开保留：千问旧+1逐层调查每层10点，可与Llama+1层面比较；千问完整正负五档每层仅1点，本轮Llama完整网格每层10点。剂量定义相同不代表抽样覆盖相同，不把全部回答混合后直接排名。不得为了声称完全一致而擅自补跑千问其余9点。

##### CPU与有界GPU验收

CPU在加载真实模型前核对320点复现、题面/共同指令相同、完整数量与分片、十档符号、基线唯一性、128/EOS及token哈希、零/正负单通道数值、独立BF16舍入、其余通道不变、异常撤hook、无0.75、授权防越界、部分结果不冒称完整及HTML全量原文转义。

GPU预检两worker各44次、共**88次**，最多11,264新token。每worker先原八题baseline；取本worker首、中、末点（浅/中/深层），分别用Q01/Q04/Q08做0-hook一次、全部10个正负剂量各一次、无hook恢复一次。故16份基线、6份零剂量、60份有符号冒烟、6份恢复。预检完整原文/失败保留，不评分。

零剂量/恢复与本worker对应baseline逐token及raw一致；两worker全部八题baseline逐token及raw一致，全部8×32校准精确一致。所有调用检查目标通道、偏移、注入次数、位置数及有限值，末尾核查全部32层目标down_proj权重hash不变和hook清理。两worker完成且exit0、CPU通过和独立审查通过才允许正式启动。正式重新加载后metadata与校准必须匹配该worker预检，shard0基线在生成最初8份时即与预检逐条比较。

同幅±d的请求偏移及BF16偏移应精确相反；对非零原激活做BF16加法后，实际delta可能不严格反对称。自由生成的后续token路径可以分叉；这些不算技术失败。任何身份/数值/恢复失败保留partial与版本，先解决工程问题，不放宽科学约束或覆盖旧收据。

##### 启动、监控和最终交付

控制器先检查千问负组controller完成、六worker exit0及撤hook/权重恢复收据，并检查GPU可用；不抢占其他作业。`preflight-r01`与`survey-r01`分离，输出目录存在则拒绝启动，不自动重试或覆盖失败。新freeze绑定合同、输入、代码和所有实际继承依赖；授权分别绑定预检/正式用途及控制器身份。老freeze不改。

每30分钟报告正式干预分母25,600（原版8、预检88另计）、本次增量、完整八题条件数、实际PID/命令/退出码、记录时间/增长/hash、GPU、磁盘与异常。条件需明确八个不同题号，不得直接记录数除8。ETA首先取本轮Llama预检实测情景，正式按本模型各worker近期完整点/题目分布更新，取较慢卡；另报剩余全部128token情景，不是置信区间或硬上限，不用千问速度冒充Llama实测，不因超ETA停止。

磁盘检查/workspace、/data/models、/tmp实际文件系统及本地归档盘；同分区不重复加总。现有完整资产旁的旧测速partial单独记载，不能把它当正式权重缺失，也不删除。下载、计算、故障、导出/归档与阅读时间分别报告，未测不编造。

正式完成后逐worker验证、全25,608唯一来源及token检查、3,200条件八题完整、2,560组11栏全原文导出；保存raw/token、采样列、基线及校准。取回完整证据并本地验hash，报告实际时间/GPU小时/释放；无计费单价不编造金额。随后按既有方式开放逐组阅读、逐层记录反例与覆盖，不增加自动语义评分、人格名称或新推理。全部交付后结束本批巡检。

---

### 原件 2：Llama 3.1 8B Instruct 全层十点正负剂量实验合同 v1

原路径：`experiments/llama31-layer-dose-survey-v1-2026-10-28/versions/prelaunch-r01/files/experiments/llama31-layer-dose-survey-v1-2026-10-28/PROTOCOL.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/llama31-layer-dose-survey-v1-2026-10-28/versions/prelaunch-r01/files/experiments/llama31-layer-dose-survey-v1-2026-10-28/PROTOCOL.zh-CN.md) · [单独阅读副本](../library/9035ec8c7f24235c.md)；SHA-256：`9035ec8c7f24235c506c9a9bd9b97ff2b324c9d117081bd990144ac688db0b5c`。

---

#### Llama 3.1 8B Instruct 全层十点正负剂量实验合同 v1

日期：2026-10-28（北京时间）。状态：用户已授权准备、CPU/GPU验收及验收通过后的正式采集；先确认既有千问实验结束与GPU释放。本合同是新独立运行，旧千问合同、代码、原文和收据保持原样。

##### 授权与证据边界

用户要求：“拉玛3.18B做同样的事情……每一层取10个点……跟千文模型同样的剂量……除了模型不一样以外，其他东西全部设置为一样的确认可比……直接改合同，改代码，然后上卡……正剂量负剂量对照……两侧的对称。”后续明确选择“使用8B-Instruct”。这一授权允许本轮准备、测试与正式执行，无需测试后再问一次；不授权恢复旧根因、判断报告、跨家族迁移方案或新增其他Llama型号。

Material Passport：材料为既有千问原八题/协议/冻结实现、官方Llama资产与本轮新实验；计算结果在实际运行前不视为已验证。此处采用模型辅助工程审查，不作人工盲评声明。代码验收、正式生成、原文归档、开放阅读分别记录。

##### 固定模型与可比设置

唯一目标为 `meta-llama/Llama-3.1-8B-Instruct@0e9e39f249a16976918f6564b8830bc894c89659`；32层，hidden 4096，gated MLP宽14336。远端已核验官方资产路径 `/workspace/models/Llama-3.1-8B-Instruct-0e9e39f2`。不替换为Llama3.0、Base、量化或其他微调版本。

与千问逐层/剂量实验相同的设置：

- `questions.json`逐字节沿用原Q01–Q08，中文共同指令逐字相同；不改成新题或英文。
- 每次只干预一个原生gated MLP通道，在进入down_proj前做加法；提示全部位置和后续全部生成步均注入。
- 每题在干净模型完整提示上校准，m为对应block输出的逐token L2中位数、排除第一个token；`c(d)=d*m/||W_down[:,n]||₂`。该题该点每档由同一干净double比例独立转BF16，不缩放已经舍入的+1幅度，不累积正负针。
- 正负绝对值为1/16、1/8、1/4、1/2、1，恰好镜像；无±0.75。正负始终使用同一层、同一通道、同一题及同一干净校准。
- BF16、eager attention、实际batch=1、每worker四CPU线程、seed0、deterministic algorithms、greedy `do_sample=False`；沿用同一generate函数与fresh context/cache实现。
- 最大128个新token，正常EOS保留实际长度和结束token；达到128保留完整128，不补齐、不续写、不因空答/乱码/循环/无预期变化重试。每次撤hook，不训练，不静态改权重。

模型原生差异必须记录：tokenizer、词表、聊天模板、BOS/EOS、模型结构与参数本身不同。Llama使用自己的原生模板，固定模板日期字符串`26 Oct 2026`，保存实际rendered context和input token hash；BOS只有一个，官方停止ID为128001/128008/128009，pad为128009。禁止把千问结束ID248044/248046硬套给Llama。Llama没有Qwen thinking开关，记为不适用；不声称两模型的模板字节/token序列完全相同。共同中文内容保持相同，128token分别以各自词表计，并非等字符预算。

Llama资产generation_config的采样默认值不会覆盖显式greedy调用。使用真实Transformers解析后的生成配置审计beam、penalty、min length、forced/suppress token等；不得默默增加重复惩罚、beam或最短长度。temperature/top_p在greedy不生效，原值仍入metadata。模型库和CUDA环境版本入运行收据。

##### 选点、剂量与数量

按旧逐层调查的规则，每层独立使用 `random.Random("acupuncture-layer-survey-v1:llama31-8b-instruct:{layer}").sample(range(14336),10)`，通道排序。32层共320个不同点，在模型输出出现前冻结`samples.json`，正负全档共用，不按效果换点。层号从0开始。

正式新增320点×10个非零剂量×8题=**25,600份干预回答**，3,200个条件；另有8份唯一原版，合计**25,608份唯一来源**。2,560个“点×题”组各11栏，共28,160展示单元。0为共享无hook原版；每层展示同一套8原版，不把重复展示算新科学来源。所有正式来源本轮新生成，不复用其他模型回答；预检不计正式科学样本。

展示顺序固定为−1、−1/2、−1/4、−1/8、−1/16、0、+1/16、+1/8、+1/4、+1/2、+1。运行按层→通道→题→剂量交错，剂量运行次序为−1/16、+1/16、−1/8、+1/8、−1/4、+1/4、−1/2、+1/2、−1、+1；每次独立，不解释为累积注入。

两H20各一个worker。沿用旧十点逐层调查的全局排序点序号mod2分片：每张卡每层各5点，不是按层奇偶。各worker12,800干预回答；shard0另生成8基线，故记录数12,808与12,800。两worker原八题clean calibration和技术基线须在预检精确一致。

覆盖差异公开保留：千问旧+1逐层调查每层10点，可与Llama+1层面比较；千问完整正负五档每层仅1点，本轮Llama完整网格每层10点。剂量定义相同不代表抽样覆盖相同，不把全部回答混合后直接排名。不得为了声称完全一致而擅自补跑千问其余9点。

##### CPU与有界GPU验收

CPU在加载真实模型前核对320点复现、题面/共同指令相同、完整数量与分片、十档符号、基线唯一性、128/EOS及token哈希、零/正负单通道数值、独立BF16舍入、其余通道不变、异常撤hook、无0.75、授权防越界、部分结果不冒称完整及HTML全量原文转义。

GPU预检两worker各44次、共**88次**，最多11,264新token。每worker先原八题baseline；取本worker首、中、末点（浅/中/深层），分别用Q01/Q04/Q08做0-hook一次、全部10个正负剂量各一次、无hook恢复一次。故16份基线、6份零剂量、60份有符号冒烟、6份恢复。预检完整原文/失败保留，不评分。

零剂量/恢复与本worker对应baseline逐token及raw一致；两worker全部八题baseline逐token及raw一致，全部8×32校准精确一致。所有调用检查目标通道、偏移、注入次数、位置数及有限值，末尾核查全部32层目标down_proj权重hash不变和hook清理。两worker完成且exit0、CPU通过和独立审查通过才允许正式启动。正式重新加载后metadata与校准必须匹配该worker预检，shard0基线在生成最初8份时即与预检逐条比较。

同幅±d的请求偏移及BF16偏移应精确相反；对非零原激活做BF16加法后，实际delta可能不严格反对称。自由生成的后续token路径可以分叉；这些不算技术失败。任何身份/数值/恢复失败保留partial与版本，先解决工程问题，不放宽科学约束或覆盖旧收据。

##### 启动、监控和最终交付

控制器先检查千问负组controller完成、六worker exit0及撤hook/权重恢复收据，并检查GPU可用；不抢占其他作业。`preflight-r01`与`survey-r01`分离，输出目录存在则拒绝启动，不自动重试或覆盖失败。新freeze绑定合同、输入、代码和所有实际继承依赖；授权分别绑定预检/正式用途及控制器身份。老freeze不改。

每30分钟报告正式干预分母25,600（原版8、预检88另计）、本次增量、完整八题条件数、实际PID/命令/退出码、记录时间/增长/hash、GPU、磁盘与异常。条件需明确八个不同题号，不得直接记录数除8。ETA首先取本轮Llama预检实测情景，正式按本模型各worker近期完整点/题目分布更新，取较慢卡；另报剩余全部128token情景，不是置信区间或硬上限，不用千问速度冒充Llama实测，不因超ETA停止。

磁盘检查/workspace、/data/models、/tmp实际文件系统及本地归档盘；同分区不重复加总。现有完整资产旁的旧测速partial单独记载，不能把它当正式权重缺失，也不删除。下载、计算、故障、导出/归档与阅读时间分别报告，未测不编造。

正式完成后逐worker验证、全25,608唯一来源及token检查、3,200条件八题完整、2,560组11栏全原文导出；保存raw/token、采样列、基线及校准。取回完整证据并本地验hash，报告实际时间/GPU小时/释放；无计费单价不编造金额。随后按既有方式开放逐组阅读、逐层记录反例与覆盖，不增加自动语义评分、人格名称或新推理。全部交付后结束本批巡检。

---

### 原件 3：Llama 3.1 8B Instruct 十点正负剂量执行记录

原路径：`experiments/llama31-layer-dose-survey-v1-2026-10-28/EXECUTION.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/llama31-layer-dose-survey-v1-2026-10-28/EXECUTION.zh-CN.md) · [单独阅读副本](../library/a01739a4b731e8f2.md)；SHA-256：`a01739a4b731e8f2ae184f6fd23b1f658f69bee234b47e6d89e97d42a4c925fb`。

---

**2026-10-28 00:32:47已按用户纠正停止。** 十点×十剂量合并设计作废，不再运行。479份已保存回答（471干预+8原版）和原始收据完整保留，本地文件/token核验通过；不复用到更正后的正式实验。两个worker退出-15由用户停止造成，两卡已释放，不宣称中断整轮的最终权重/hook验收完成。见[user-stop-split-r01/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/llama31-layer-dose-survey-v1-2026-10-28/user-stop-split-r01/receipt.json)。新设计为独立逐层十点+1实验、随后逐层单点剂量实验。以下保留历史启动记录。

#### Llama 3.1 8B Instruct 十点正负剂量执行记录

**当前状态：正式实验已运行，尚未完成。** 北京时间2026-10-28 00:22:25启动，两H20并行；当前freeze为`70f313c5e643bc4006782159c9a325de98527399be8d11610deddcb68ff1385f`。用户明确选用8B-Instruct，已授权验收通过后直接运行。

最终本地/远端CPU 22/22通过（r03），真实5.20.2生成配置解析通过，独立设计/代码/启动审查通过。GPU预检preflight-r02为88/88、5,601 token，80 EOS+8达到128；8组跨卡基线、6份zero、6份恢复全exact，30个±配对通过，全部32层目标权重恢复及hook清理通过。控制器实耗175.05秒，两exit0、进程退出后才开始正式。完整102文件11,019,458字节取回，全部record/token及metadata/calibration/sampled columns本地复核通过。

正式科学分母为25,600干预（每worker12,800），原版8另计，合计25,608唯一来源。32层各十点，±1/16、±1/8、±1/4、±1/2、±1和原八题；输出最多128新token/EOS原长。任务、生成代码、校准与剂量规则对齐千问；Llama原生模板/词表/EOS与千问不同，旧千问全剂量每层一点、本次每层十点，覆盖差异不伪装为相同。

00:24:11现场：47/25,600干预＋8/8基线（两worker干预19与28），0/3,200个完整八题条件；交错运行尚未覆盖首点八题，不能按记录数除8。55份文件/token哈希通过，controller2254533与worker2254534/2254535真实命令一致，最新记录距快照约3–5秒，无错误。两H20各16,205MiB，GPU利用率34%/33%。

初始预检主情景11小时42分19秒；00:24快照剩余11小时40分09秒，预计北京时间**10月28日12:04**计算完成。剩余全部128情景约21小时38分09秒，完成点**22:02**；不是CI或硬上限。首个完整八题通道尚未完成，暂沿用各卡自身预检情景，不用前几条短题推算全程。初始正式worker约22.730 GPUh、两卡预留约23.410 GPUh是推算，实际成本结束后另报；没有计费单价。导出、归档与阅读另计，未测不编ETA。

快照工作盘95%、可用126.22GiB；/data/models与/tmp共用根盘91%、可用43.60GiB；本地52.78%、可用877.38GiB。本轮目录22.15MiB、正式输出11.14MiB（含两份采样列），当前空间充足。正式记录文件按预检实测平均大小的投影保存于readiness/storage-estimate-r01.json，不将投影当硬上限，无任何删除。

半小时心跳`llama-3-1`已ACTIVE，只跟踪本批；旧千问心跳已结束，其他暂停实验不恢复。完成后controller将核验两worker并自动导出2,560组十一栏。原文/全部证据取回核验及开放逐组阅读、逐层笔记和覆盖完成后，才最终交付并结束巡检。

执行证据：[合同](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/llama31-layer-dose-survey-v1-2026-10-28/PROTOCOL.zh-CN.md)、[正式授权](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/llama31-layer-dose-survey-v1-2026-10-28/readiness/formal-authorization-r01.json)、[启动身份](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/llama31-layer-dose-survey-v1-2026-10-28/readiness/formal-launch-r01.json)、[最新快照](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/llama31-layer-dose-survey-v1-2026-10-28/monitoring/latest.json)、[计时估计](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/llama31-layer-dose-survey-v1-2026-10-28/readiness/timing-estimate-r01.json)、[独立计时复核](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/llama31-layer-dose-survey-v1-2026-10-28/readiness/timing-independent-review-r01.json)、[预检本地核验](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/llama31-layer-dose-survey-v1-2026-10-28/readiness/preflight-local-verification-r02.json)。

##### 历史准备与启动前修复


2026-10-28（北京时间）。用户已确认8B-Instruct，并授权CPU/GPU验收通过后直接正式运行。官方模型资产14文件当前完整hash通过，千问负组已经完成且两H20空闲。

本地和远端最终22项CPU测试全部通过；真实远端Transformers5.20.2解析后的生成策略核验通过，无真实模型加载。新freeze为`41f27e01643a3db8408651111c84968cfa0a348caba41014908ad9bc6510fe8f`，共19个源/合同/依赖文件；旧千问freeze不改。代码及设计审查通过，GPU预检授权已保存，尚待启动结果。

固定32层每层十点、320点、±1/16、±1/8、±1/4、±1/2、±1，每点每档原八题；正式25,600干预+8基线=25,608唯一来源，2,560组十一栏。预检88另计。每worker每层5点，正式各12,800干预，shard0另8基线。模型原生模板/词表/结束符不同，旧千问完整剂量每层1点的覆盖差异明确保留。

见[合同](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/llama31-layer-dose-survey-v1-2026-10-28/PROTOCOL.zh-CN.md)、`readiness/cpu-local-r02.json`、`cpu-remote-r02.json`、`native-generation-config-check-r01.json`、`independent-launch-review-r01.json`与`preflight-authorization-r01.json`。正式ETA以Llama预检实测更新，不套用千问速度。

启动前路径检查曾阻断r01（未加载模型、未创建GPU预检输出）；前置路径补齐experiments/后，本地/远端22项CPU均再次通过，旧19文件与freeze完整保存在versions/prelaunch-r01。新freeze `70f313c5e643bc4006782159c9a325de98527399be8d11610deddcb68ff1385f`，预检目录改为preflight-r02，所有科学设置不变，独立修复审查通过。

GPU预检r02于北京时间2026-10-28 00:16:14实际启动，controller PID2252729，两worker2252730/2252731。00:17:07现场16/88、790token、两卡各16193MiB及34–35%，文件/token核验通过，未见异常。正式阶段尚未启动。

---


## 时间、运行与停止收据索引

下面是所收集JSON的原有时间字段与状态，不把预计结束时间当实际完成时间。未列时间的文件仍有原件链接。完整JSON全部保存在原文归档，不能以此索引中的标量代替完整嵌套内容。

| 原件 | 原记录状态/阶段 | 原时间字段（原时区） |
|---|---|---|
| [preflight-r02/controller.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/llama31-layer-dose-survey-v1-2026-10-28/preflight-r02/controller.json) | {"status": "completed", "mode": "preflight"} | {"started_utc": "2026-10-27T16:16:14.491466+00:00", "generation_ended_utc": "2026-10-27T16:19:09.542086+00:00", "ended_utc": "2026-10-27T16:19:09.542227+00:00"} |
| [preflight-r02/llama31-8b-instruct-shard-0/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/llama31-layer-dose-survey-v1-2026-10-28/preflight-r02/llama31-8b-instruct-shard-0/receipt.json) | {"status": "completed", "mode": "preflight"} | {"started_utc": "2026-10-27T16:16:14.563579+00:00", "ended_utc": "2026-10-27T16:19:01.628177+00:00"} |
| [preflight-r02/llama31-8b-instruct-shard-1/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/llama31-layer-dose-survey-v1-2026-10-28/preflight-r02/llama31-8b-instruct-shard-1/receipt.json) | {"status": "completed", "mode": "preflight"} | {"started_utc": "2026-10-27T16:16:14.563825+00:00", "ended_utc": "2026-10-27T16:19:07.946500+00:00"} |
| [readiness/asset-and-resource-audit-r01.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/llama31-layer-dose-survey-v1-2026-10-28/readiness/asset-and-resource-audit-r01.json) | {"status": "passed"} | {"checked_utc": "2026-10-27T16:03:45.368664+00:00"} |
| [readiness/formal-launch-r01.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/llama31-layer-dose-survey-v1-2026-10-28/readiness/formal-launch-r01.json) | {"status": "dispatched"} | {"started_utc": "2026-10-27T16:22:25.207948+00:00"} |
| [readiness/independent-design-audit-r01.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/llama31-layer-dose-survey-v1-2026-10-28/readiness/independent-design-audit-r01.json) | {"status": "design_review_complete_implementation_and_runtime_pending", "scope": "Independent read-only inspection of existing Qwen layer/dose and Llama adapter definitions. This receipt does not certify new code, GPU readiness, formal launch, or model effects."} | {"checked_utc": "2026-10-27T16:04:58.605527+00:00"} |
| [readiness/independent-launch-review-r01.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/llama31-layer-dose-survey-v1-2026-10-28/readiness/independent-launch-review-r01.json) | {"status": "passed_code_design_review", "scope": "Read-only final contract, scheduling, authorization, predecessor, GPU admission, verification and automatic export review. Engine generation-default repair and remote actual Transformers parsing are reviewed separately; this receipt makes no GPU-preflight or formal-run success claim."} | {"checked_utc": "2026-10-27T16:11:59.846735+00:00"} |
| [readiness/independent-launch-review-r02.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/llama31-layer-dose-survey-v1-2026-10-28/readiness/independent-launch-review-r02.json) | {"status": "passed_minimal_prelaunch_path_fix_review", "scope": "Read-only independent review of the pre-dispatch path repair and actual local predecessor gate. No model load or GPU inference performed; no GPU-preflight success claim."} | {"checked_utc": "2026-10-27T16:15:10.559352+00:00"} |
| [readiness/preflight-completion-remote-r02.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/llama31-layer-dose-survey-v1-2026-10-28/readiness/preflight-completion-remote-r02.json) | {"status": "passed"} | {"checked_utc": "2026-10-27T16:19:29.839022+00:00", "recorded_utc": "2026-10-27T16:19:58.342291+00:00"} |
| [readiness/preflight-launch-r02.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/llama31-layer-dose-survey-v1-2026-10-28/readiness/preflight-launch-r02.json) | {"status": "dispatched"} | {"started_utc": "2026-10-27T16:16:14.451473+00:00"} |
| [readiness/preflight-local-verification-r02.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/llama31-layer-dose-survey-v1-2026-10-28/readiness/preflight-local-verification-r02.json) | {"status": "passed", "scope": "Local survey.check_pair passed during timing-estimate; all record/token and metadata/calibration/sampled-column hashes checked; controller/execution match independent remote receipt; no model loaded."} | {"checked_utc": "2026-10-27T16:21:23.198641+00:00"} |
| [survey-r01/controller.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/llama31-layer-dose-survey-v1-2026-10-28/survey-r01/controller.json) | {"status": "failed", "mode": "survey"} | {"started_utc": "2026-10-27T16:22:25.301057+00:00", "ended_utc": "2026-10-27T16:32:47.528780+00:00"} |
| [survey-r01/llama31-8b-instruct-shard-0/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/llama31-layer-dose-survey-v1-2026-10-28/survey-r01/llama31-8b-instruct-shard-0/receipt.json) | {"status": "running", "mode": "survey"} | {"started_utc": "2026-10-27T16:22:25.405417+00:00"} |
| [survey-r01/llama31-8b-instruct-shard-1/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/llama31-layer-dose-survey-v1-2026-10-28/survey-r01/llama31-8b-instruct-shard-1/receipt.json) | {"status": "running", "mode": "survey"} | {"started_utc": "2026-10-27T16:22:25.405541+00:00"} |
| [user-stop-split-r01/local-verification.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/llama31-layer-dose-survey-v1-2026-10-28/user-stop-split-r01/local-verification.json) | {"status": "verified_stopped_partial"} | {"checked_utc": "2026-10-27T16:35:57.168749+00:00"} |
| [user-stop-split-r01/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/llama31-layer-dose-survey-v1-2026-10-28/user-stop-split-r01/receipt.json) | {"status": "user_stopped"} | {"verified_utc": "2026-10-27T16:34:13.061006+00:00"} |

## 全部原始资产入口

本目录在固定提交下共有663个跟踪文件，包含代码、原回答、失败、收据和压缩证据；文件数不是样本数。[逐文件完整账本](../assets/016-llama31-layer-dose-survey-v1-2026-10-28.tsv) · [原目录](https://github.com/yuxiexiong/acupuncture/tree/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/llama31-layer-dose-survey-v1-2026-10-28)。未复制模型权重、环境或凭据。
