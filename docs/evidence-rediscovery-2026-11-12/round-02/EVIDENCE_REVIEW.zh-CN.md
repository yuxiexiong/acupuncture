# 第二轮证据复查：支持问题，也约束问题

2026-11-12。沿用第一轮171目录账，不重编号、不更改旧目的。下列9个实验目录的报告／首轮阅读报告在本轮补读或重读；其余连接继承第一轮19卡、31目录的核查，不冒充本轮重新逐样本验收。第一轮5374来源版本哈希核对也不冒充本轮重新执行。

旧来源分支main固定于`7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8`，wsp固定于`2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274`；NGC/WSB使用本次隔离工作树的交付基线`7eda17df2af7ac900e41a0d80f38943d4b33dc5d`。文件身份与阅读层级在[source-read-manifest.json](source-read-manifest.json)记录。哈希只核身份，不验证科学结论。

## 1. 重新纳入选题的早期证据

| 来源 | 原目的与实际证据 | 对重选问题的约束 |
|---|---|---|
| E003，2026-10-26，[能力摸底](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/capability-screen-v3-2026-10-26/RESULTS.zh-CN.md) | 固定双针与原版1400对，MMLU按学科加权67.99→29.74；ARC归一化65→38；GSM88→0；HumanEval53→4。718对MMLU来自旧完整配对，其余新算 | 有严重能力损伤，不证明特殊语义控制；任务、评分和格式不同，不把下降顺序解释为天然能力层级 |
| E004，2026-10-26，[跨尺寸迁移](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/transfer-toy-v1-2026-10-26/RESULTS.zh-CN.md) | 用共同文本映射源双针到9B/2B；目标完整能力面板仍严重下降，随机流程也损伤。此结果报告的行为盲评尚未完成 | 损伤迁移不能证明任务或“人格”迁移。该报告未完成的标注不代表后来全项目没有其他行为分析；本轮不外推其时态 |
| E013，2026-10-27，[Qwen全层开放阅读](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-survey-toy-v1-2026-10-27/qualitative-pass-r01/FIRST_PASS.zh-CN.md) | 2B/4B/9B共880点、7040针下回答和24原版。前部停止、跨题主题侵入、后部保骨架但细节错等粗差异；强同层异质性 | 这是开放式模型辅助历史阅读，不是本轮重读7040回答，也不是预注册故障率；不能命名天然功能区 |
| E018，2026-10-28，[Llama正负剂量阅读](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/llama31-single-point-dose-survey-v1-2026-10-28/qualitative-pass-r01/FIRST_PASS.zh-CN.md) | 每层一个冻结点、正负五档，2304新输出、264复用。存在中档循环、强档恢复，也有两符号都受损 | 非单调是具体回答反例，不能用少数例子估计普遍性；正负设置对称不意味着语义相反 |
| E025，2026-10-29，[早层控制与撤针重建](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/early-input-control-v1-2026-10-29/REPORT.zh-CN.md) | N5063确认k=4有18/20仅重建恢复，k=16为9/9；中后层还有撤针即恢复、重建仍异常及反向例 | 不同维持方式共存；某条件的重建效果不代表全部针。报告顶部更正引用后续事实敏感度，必须连同更正读，不能沿用“知道但停嘴” |

E003协议已全文复读；完成收据只抽取状态和步骤信息，不声称重跑官方评分。E004协议本轮读到目的、边界、模型、判读等可见部分，中段显示截断；报告与第一轮来源核验支撑本轮使用的结果，不能将该次协议读取登记为全文。其余原合同／回执身份继承第一轮与冻结档案。

## 2. WSP从“搜索够不够”回到行为问题

### E128：原始失败筛查，2026-11-05

[报告](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-failure-discovery-run-v1-2026-11-05/REPORT.zh-CN.md)使用Qwen3-VL-4B-Instruct，不能与缓存线Qwen3.5-4B混同。

原目的为筛选值得诊断的稳定失败，没有内部编辑。C留出96个来源组中，原图通常94/96、反事实图通常74/96；反事实图视觉T0为90/96。严格行为模式15/96要求无图常识、原图常识、反事实视觉均正确，而反事实常识错成视觉答案。改写T1的视觉表现降为59/96，不能只报最有利模板。一次规则提示没有稳定改善，不代表所有提示无效。

这比“搜索没有找到稳定补丁”更接近科学对象，但仍是行为证据；没有证明内部知识和感知在错误当步完整可用。

### E152：失败结构审计，2026-11-06

[报告](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-c-failure-structure-audit-2026-11-06/REPORT.zh-CN.md)、[事前分析卡](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-c-failure-structure-audit-2026-11-06/DESIGN.zh-CN.md)、[旧执行核验](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-c-failure-structure-audit-2026-11-06/verification.json)本轮均已读。

旧分析重评分144份正式评价、368640回答，140候选；这不是144次独立科学重复。每个T0双名称顺序面板为64来源、128配对。

| 模型W0，B0:T0 | 两问都对 | 两问同选视觉 | 两问同选常识 | 两问答反 |
|---|---:|---:|---:|---:|
| Qwen | 97 | 27 | 4 | 0 |
| Gemma | 48 | 47 | 32 | 1 |

本轮从固定wsp Git对象读取`analysis.json`，核对上表和Gemma v8 R23的记录；另读`selected-T0-answer-changes.json`核对两个方向的具体修复。没有重新解压并重评分368640原始回答。提取结果和原文件哈希保存为[claim-check.json](claim-check.json)。

Gemma v8 R23记录的操作是第7层post_attention_layernorm相对W0增益1.075，其T0通常题净+3、视觉题净+2、联合48→53，已正确配对没有被改错。T1另有1个联合正确配对被改错，故不能把“T0无损”扩成所有条件无损。该候选属于开发选择，不是独立确认。

两项实际变化：C-086/O1的通常答案Container ship保留，视觉从Container ship改为Boat；C-108/O0的视觉Buffalo保留，通常从Buffalo改为Space shuttle。它们足以反驳“静态补丁必然只把正确数从一端搬到另一端”，却不足以证明共享任务规则被修好。

正常图控制与知识控制在失败组内并不全对；Qwen两问同选视觉的27配对中，无图常识仅16对，Gemma对应27/47。不能把所有同答都命名为“模型知道、看见，却不听指令”。

## 3. 最近结果作为限制，不作为默认下一步

| 来源 | 本轮保留的准确结果 | 禁止外推 |
|---|---|---|
| E170，[NGC](https://github.com/yuxiexiong/acupuncture/blob/7eda17df2af7ac900e41a0d80f38943d4b33dc5d/experiments/cache-native-gain-v1-2026-11-08/REPORT.zh-CN.md)，实际完成2026-11-11 | 四方向、48已见输入、1008自然轨迹；目标配置均未修回任何原本错误的完整答案；跨场景内部增益预测有效 | 不能称全部增益机制被否定，也不能把辅助分数变化宣传成完整回答修复 |
| E171，[WSB](https://github.com/yuxiexiong/acupuncture/blob/7eda17df2af7ac900e41a0d80f38943d4b33dc5d/experiments/cache-write-signal-background-v1-2026-11-11/REPORT.zh-CN.md)，2026-11-11 | 固定实际写入差值跨C/H重放；D_tr为0/0/.003/.882，四格均348有效；H是已修卷积的混合背景 | 不能称原生受针恢复、唯一读取原因、独立跨模型确认或88.2%准确率；6情境不等于348独立样本 |

两篇本轮全文重读。第一轮关键数字／评分定义和机器结果核验继续有效，本轮没有再运行其审计脚本。DWC的新材料确认、WIN条件、SPF失败及FBR随机竞争等来自[第一轮比较卡](../EVIDENCE_CARDS.zh-CN.md)，没有偷偷提升为本轮全量复算。

## 4. 这轮没有做的事

没有给所有输出重新贴语义标签，没有拟合故障分类器，没有从剂量例子计算新的显著性，没有混用两条线构造合并成功率，没有把新增候选问题转成新的运行合同。

新的贡献是研究问题的取舍与已知证据边界的重组；它不改变旧实验的科学身份。若A最终没有得到具体计算解释，不能把本轮的问题表述本身记作机制进展；若B最终不推进，原失败与修补记录也照常保留。
