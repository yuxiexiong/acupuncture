# 辅导师决策账

状态入口：[STATE](STATE.zh-CN.md)；执行入口：[skill](../../.agents/skills/acupuncture-advisor/SKILL.md)。审查身份是独立上下文的AI意见，非独立复现或人类专家认证。

| 日期／编号 | 待审决定 | 辅导师建议 | 作者处理与执行状态 |
|---|---|---|---|
| 2026-11-12 / A001 | 共同计算失效候选的推荐强度与可行性；辅导师流程首次实际使用 | 修改后继续资料论证；暂缓共同原生致错原因的优先投入推荐 | 采纳六项纠正；候选保留，不撤销DWC等局部贡献；无新实验。[原始意见](reviews/2026-11-12-01-review.md)／[逐项处理](reviews/2026-11-12-01-disposition.md) |
| 2026-11-12 / A002 | 原线最值得继续的科研问题，正面比较重要性、可行性与已有支持；不设计新实验 | 首选历史信息的选择性依赖；明确延续旧Q1。DWC为最强正证据、WSB为约束；没有强论文保证 | 采纳初审与主报告聚焦复核全部纠正；范围、近邻及失败条件明确。[主报告](2026-11-12-mainline-recommendation.zh-CN.md)／[原始意见与复核](reviews/2026-11-12-02-review.md)／[处理](reviews/2026-11-12-02-disposition.md)。无新设计、模型或GPU运行 |
| 2026-11-13 / A003 | 推荐问题要形成什么核心结论、现有证据还差什么；不设计实验 | 保留首选；具体解释对象成立，计算机制未知；保留固定恢复条件下入口证据，不强求全机制 | 采纳初审及主报告聚焦核对全部纠正。[主报告](2026-11-13-core-claim-and-evidence-gap.zh-CN.md)／[原始意见](reviews/2026-11-13-03-review.md)／[处理](reviews/2026-11-13-03-disposition.md)。无新设计、评分、模型或GPU运行 |
| 2026-11-13 / A004 | 不改问题，比较具体机制解释、边界及优先级；不设计实验 | H1为最受支持部分链；WSB的H2为最简工作解释、H3首要竞争，不把优先级当真实性排序 | 采纳证据层级、位置读法、幅度证据及状态来源纠正。[机制比较](2026-11-13-mechanism-ranking.zh-CN.md)／[原始意见](reviews/2026-11-13-04-review.md)／[处理](reviews/2026-11-13-04-disposition.md)。无新设计或运行 |
| 2026-11-13 / A005 | 是否只研究窄针/任务/模型/量级机制，广度如何影响继续推荐 | 保留问题，修改投入推荐；有限双针/新材料不可清零，局部排序不等于广度成立 | 采纳全部纠正；范围不按阳性定义，不默认持续WSB细拆；[判断](2026-11-13-scope-and-generalization.zh-CN.md)／[审查](reviews/2026-11-13-05-review.md)／[处理](reviews/2026-11-13-05-disposition.md)。无新设计或运行 |
| 2026-11-13 / A006 | 下一阶段的具体中心与范围顺序 | 修改后继续；任务结构先，可比另一规模后，最小机制辨别同阶段；不另开新针轴 | 采纳并经同一审查者复核。[阶段建议](2026-11-13-next-stage-recommendation.zh-CN.md)／[审查](reviews/2026-11-13-06-review.md)／[处理](reviews/2026-11-13-06-disposition.md)。下一交付集中方案，本轮没有实验设计验收或运行 |
| 2026-11-13 / A007 | 设计下一阶段实验，导师审查，推Git，先不开始 | SRT-01 v2逻辑设计通过；关系与具体系数解释同阶段，9B有条件；工程待验 | 采纳背景差前提、交付/前缀、恢复分母、9B进入与完整存盘纠正，经同审查者复核。[方案](../../experiments/cache-structure-read-transfer-v1-2026-11-13/PLAN.zh-CN.md)／[审查](reviews/2026-11-13-07-review.md)／[处理](reviews/2026-11-13-07-disposition.md)。无模型/GPU运行 |
| 2026-11-13 / A008 | 对照对话核查覆盖范围与机制推进是否漂移 | 有限任务结构与局部机制检验保留；唯一JOIN/系数阳性后才9B的路线比A006收紧 | A007同一Advisor修正策略认可，作者采纳；[审计及处理](2026-11-13-design-alignment-audit.zh-CN.md)／[复核](reviews/2026-11-13-08-review.md)。本轮未改实验方案、未运行 |
| 2026-11-13 / A009 | 请Advisor直接评价机制推进与范围扩大是否拆成两个实验 | 推荐同阶段分别判读、各自可结束，可共享同条件采集；不以新机制阳性捆绑既有关系范围 | 作者采纳组织建议，保留证据依赖与共享身份；[直接意见及处理](reviews/2026-11-13-09-review.md)。未重写方案、未设计新矩阵、未运行 |
| 2026-11-13 / A010 | 按A009更新下一阶段实验方案 | 同一Advisor审查两个具体方案，纠正旧桥接缓存形成漏项、实际D差存盘/复算和跨模型同任务对齐 | 作者已修订，同一审查者v2复核两方案逻辑通过；[方案协调](2026-11-13-split-experiment-plan.zh-CN.md)／[审查](reviews/2026-11-13-10-review.md)／[处理](reviews/2026-11-13-10-disposition.md)。BRC与WUS分别判读；旧SRT历史保留。未实现、未运行 |
| 2026-11-15 / A011 | 课题有实质卡点，还是实验路径不对 | 两者兼有；未收敛为针相关可预测解释，不等于不可解释；保留DWC，限定NGC阴性，路径责任有A008依据但不可量化 | 作者采纳全部纠正；暂停沿局部阳性自动追加的推进方式，保留课题和现行未运行方案的身份。[判断、审查与处理](2026-11-15-bottleneck-assessment.zh-CN.md)。无新设计或运行 |
| 2026-11-15 / A012 | 改默认固定结构/计算规则是否有价值 | 保留历史混合B与中间归一化A为前期核查候选，证据距离B先；不承诺突破，C擦写解绑暂不优先 | 作者采纳，并保留NBR/NVB来源混淆及同审查者更正。[候选及处理](2026-11-15-structural-assumptions.zh-CN.md)。无新实验设计/实现/运行，现行BRC/WUS未改 |
| 2026-11-15 / A013 | 短卷积具体改什么、能否超越缓存拆分帮助解卡 | 历史去共同分量规则退出当前推进候选，只保留假设；时间模态无证据特异指向且判别增量不足，不因假设未知直接否决检验 | 作者采纳五项纠正；保留当前tap/全层全程选择缺证据，局部patch等价，不能自动解释原WSB。[判断及处理](2026-11-15-temporal-rule-assessment.zh-CN.md)／[草案自查](reviews/2026-11-15-13-input.md)／[审查](reviews/2026-11-15-13-review.md)。未改现行方案，无模型/GPU或科学运行 |
| 2026-11-15 / A014 | 用户纠正：方法如何解决机制研究的卡点 | 方法可作干预工具，但认识增量才是判据；改后效果不能直接解释原模型，不能要求先找到真实唯一机制 | 作者采纳三项补充并纠正上轮稳健性重心；WSB不是整体目的，去均值不恢复为候选。[用户纠正、原审查及处理](reviews/2026-11-15-14-clarification.md)。仅目的与判据澄清，无新设计或运行 |
| 2026-11-15 / A015 | 多路线探索固定结构/系数是否隐藏有价值的针响应关系，独立Advisor持续纠正 | 可交付资料审计，当前没有强候选；机制认识优先，非剂量等价仍需原系统连接，不要求新理论，A/B不确定排序，C独立实践备选 | 采纳全部实质纠正及P1新列范数条件；[主报告](../intervention-assumptions-2026-11-15/REPORT.zh-CN.md)／[综合初审](../intervention-assumptions-2026-11-15/reviews/synthesis-review.md)／[处理](../intervention-assumptions-2026-11-15/reviews/synthesis-disposition.md)／[同人复核](../intervention-assumptions-2026-11-15/reviews/synthesis-recheck.md)。两支线自身审查同包保留，无新设计或运行 |
| 2026-11-15 / A016 | 继续挖最有希望具体关系、已有现象与实质增量，不跑实验 | 正面推荐门前头内共享尺度的历史用途关系为首要论证对象；D/E三方向为竞争，不将相关前人清零或把公式当发现 | 同一Advisor初审/复核，作者采纳相对量、各次cast、±d条件、Muir近邻及C1343反证收紧。[报告](../intervention-assumptions-2026-11-15/round-02/REPORT.zh-CN.md)／[审查](../intervention-assumptions-2026-11-15/round-02/reviews/advisor-round-01.md)／[处理](../intervention-assumptions-2026-11-15/round-02/reviews/disposition.md)。仅具体假说与认识价值，非已成立机制或设计通过；0模型/GPU |
| 2026-11-15 / A017 | 按A016设计历史增量分子/分母用途实验，区分余量并允许正反认识 | 同一Advisor支持四臂价值，要求修正Q必要门槛、绑定原生撤回的行为/连续对比、弱门坐标归因、统一资格集合及记录成本 | 作者已修订v2并完成C01–C14复查，同人复核逻辑通过；[方案](../../experiments/cache-readout-content-scale-v1-2026-11-15/PLAN.zh-CN.md)／[初审](../../experiments/cache-readout-content-scale-v1-2026-11-15/reviews/advisor-round-01.md)／[处理](../../experiments/cache-readout-content-scale-v1-2026-11-15/reviews/disposition.md)。无模型/GPU/tokenizer/新统计，旧BRC/WUS未执行 |
| 2026-11-15—16 / A018 | 用户授权RCS实现、测试后上卡及修bug | 同一Advisor实现审查四项修正及结果解释审查均完成；分子大阳性、分母重要正向量级被区间排除、严格用途优势未成立分开报告；delta_e只反对窄余量解释 | 26项CPU、工程及正式48/348/2880通过。失败计费保留；总.724546小时、约88.24GiB。无追加实验。[报告](../../experiments/cache-readout-content-scale-v1-2026-11-15/REPORT.zh-CN.md)／[审查处理](../../experiments/cache-readout-content-scale-v1-2026-11-15/reviews/result-disposition.md) |
| 2026-11-16 / A019 | RCS三项结果的实质增量、旧解释修正；不追加实验 | 有内容的部分机制证据；用途依赖与背景总响应并列，不拼完整中介链；A016强分母预期退出本条件 | 采纳状态演化、m参照定义、行为与局部尺度、语义二分及ΔH范围纠正；同人复核通过。无新统计、设计或运行。[主稿](2026-11-16-rcs-knowledge-update.zh-CN.md)／[处理](reviews/2026-11-16-19-disposition.md) |
| 2026-11-16 / A020 | 优先旧数据解释H响应差，确缺测才提最小方案，先不跑 | 连续分子用途差已对齐；净读取与门转换并存。优先具体门场用途条件检验，保留净w竞争，不按热点选层 | CPU分析与原始审查留档，修正端点、样本、比率和数值身份；NGU仅设计，无模型/GPU。[结果](../../experiments/cache-readout-content-scale-v1-2026-11-15/analysis/background-response-r01/REPORT.zh-CN.md)／[方案](../../experiments/cache-numerator-gate-use-v1-2026-11-16/PLAN.zh-CN.md)／[采纳](reviews/2026-11-16-20-disposition.md) |
| 2026-11-16 / A021 | 用户授权NGU实现、测试后GPU及结果解释 | 同一Advisor实现修正和结果审查完成；具体门用途对H有条件任务/行为作用，双向+1量级未成立，残差不分账 | 32项CPU、2工程及正式48/348/2088完成，第一次预算阻断/源码保留，优化全252轨迹逐位回放；总1973.147秒、1.444GiB。采纳政策效果/范围/余量/ΔH及不对称边界，收束不追加。[报告](../../experiments/cache-numerator-gate-use-v1-2026-11-16/REPORT.zh-CN.md)／[原审查与处理](../../experiments/cache-numerator-gate-use-v1-2026-11-16/reviews/result-disposition.md) |

| 2026-11-16 / A022 | 解释H换C门与C换H门不对称，优先旧数据、先不跑 | 净读取幅度与同门差适配可区分，局部不等不能折算任务份额；有条件推荐可失败的任务VJP近似卡 | 673文件SHA与14权重核验，2352记录，CPU21.645秒/0模型GPU；采纳raw/cast分列与helper来源闭合。最小卡单列逻辑/工程身份，不追加运行。[报告](../../experiments/cache-numerator-gate-use-v1-2026-11-16/analysis/asymmetry-r01/REPORT.zh-CN.md)／[审查处理](../../experiments/cache-numerator-gate-use-v1-2026-11-16/analysis/asymmetry-r01/reviews/disposition.md) |

| 2026-11-16 / A023 | 用户授权最小任务梯度实现、验收后GPU，判断一阶预测及不对称解释 | 原幅度双对角校准通过，限定已存P条件；指定方向的平均任务映射差可诊断，U表未有限验证；保留H局部不足并收束 | 15项服务器CPU、工程20对/正式168对成功；4060前向/376反向，总655.829秒。采纳范围/单位/实际P与原生d区别及无份额解释，0新自然回答、不追加。[报告](../../experiments/cache-task-gradient-v1-2026-11-16/REPORT.zh-CN.md)／[结果采纳](../../experiments/cache-task-gradient-v1-2026-11-16/reviews/result-disposition.md) |

| 2026-11-16 / A024 | 优先旧梯度/中间记录与理论解释同方向H更强、NQ03/04误差，先不跑 | 非比例梯度的指定任务投影与正项增强得到CPU约束；终RMS径向与pre-h映射未分开，末端舍入单独不足 | 841来源/168投影，4项合成验收，CPU7.934秒/0模型GPU；采纳计权、机器VJP、撤回望远镜来源定位。交叉seed最小卡仅逻辑通过，未实现/运行。[报告](../../experiments/cache-task-gradient-v1-2026-11-16/analysis/downstream-response-r01/REPORT.zh-CN.md)／[采纳](../../experiments/cache-task-gradient-v1-2026-11-16/analysis/downstream-response-r01/reviews/disposition.md) |

| 2026-11-16 / A025 | 用户要求回顾主线、判断偏移及细节/缺口位置 | 未换题但重心局部化；RCS/NGU补条件用途，TGA/A024有模型认识却不自动成为全局优先；先整合，不要求全机制 | 同一Advisor重新评估路线，采纳DWC已有机制、保留梯度价值与具体核心句；交叉seed卡逻辑身份保留但非默认续项。0新设计/统计/模型GPU。[主稿](2026-11-16-mainline-realignment.zh-CN.md)／[采纳](reviews/2026-11-16-25-disposition.md) |

| 2026-11-16 / A026 | 与Advisor整理完整主线、核心结论、证据层级和真正关键连接；不设计运行 | 支持条件性部分机制论证，纠正A020连续用途差被整体降级；承认已有桥，把缺口固定为同ΔH用途强弱的计算解释 | 作者采纳主干分级、余量窄解释、DWC独立身份和关键连接纠正。无新设计/统计/模型GPU。[主稿](../cache-mechanism-main-argument-2026-11-16.zh-CN.md)／[审查处理](reviews/2026-11-16-26-disposition.md) |

| 2026-11-16 / A027 | 判断相对前人实质增量、核心贡献及关键连接必要性；不设计运行 | 受限因果案例有信息量，强中心贡献尚未建立；有限结论无需缺桥才成立，原计算原因目标仍需它，但补桥非强论文保证 | 作者采纳前人覆盖、非稻草人但有限增量与三层必要性；保留A005范围风险，无新设计/统计/模型GPU。[主稿](2026-11-16-contribution-and-gap-assessment.zh-CN.md)／[处理](reviews/2026-11-16-27-disposition.md) |

| 2026-11-16 / A028 | 作者与Advisor分别给下一阶段走向，不设计运行 | 当前收束 > 范围候选 > 继续局部细拆，非执行队列；没有值得正面推荐新增投入的具体候选，不再以无限找假说续项 | 作者从初始范围优先经旧WUS与近邻对照改为收束，采纳Advisor排序；原目标未完成、已有成果保留，不启动任务/模型/新设计。[决策及审查](2026-11-16-next-stage-investment-decision.zh-CN.md) |

此前重要纠正：可恢复性从主问题推荐降为组织主题；WSP不再推荐继续，原目的为方法迁移且尚未有效；共同恢复响应不等于共同致错原因。以上来自用户与作者对话，不冒称辅导师已经审查。


| 2026-11-16 / A029 | 用户纠正需判断整个Acupuncture，而非H/C局部分支；不设计运行 | 正面选择形成历史→任务信息利用/恢复需求；P6为计算锚点，P1/P4独立保留但不切换，P3/P5低优先；暂不承诺大投入或具体执行 | 同一Advisor纠正作者初稿把无现成执行项推为全项目暂停；重读WIN预留关系及失败后采纳。三组不同操作不拼原生机制；[项目判断](2026-11-16-project-wide-direction-assessment.zh-CN.md)／[审查](reviews/2026-11-16-29-review.md)。0新设计、统计、模型/GPU |


| 2026-11-16 / A030 | 用户要求从针进入到机制解释详细梳理总问题已解与未解，不再选方向 | 已有S2/S3实际停止、FX完整恢复、DWC来源写读与RCS/NGU用途的条件因果段；不是顺序完成到第n步；原生中介连接、强弱原因及范围仍未贯通 | 采纳同一Advisor对早期因果桥的提升、固定token边界、S3参照身份及不同操作不得拼链。A029具体阶段题选择仍未完成；[主稿](2026-11-16-mechanism-chain-progress.zh-CN.md)／[审查](reviews/2026-11-16-30-review.md)。无新选题、设计、统计、模型/GPU |
