# Llama 实验 A：L00–L10 首次开放阅读

## 范围与方法

材料为实验 A `delivery-r01/all.records.jsonl` 的原始回答。按原八题逐条读 `output.raw_text`，包括 EOS 特殊标记和 128 token 上限处的残缺；没有按关键词自动分类、评分、调用外部模型或执行新推理。每层十个通道、每通道八题，剂量只有 +1。下述是本次模型辅助开放阅读的观察，不是复现、机制定位或人格评定；只适用于已抽到的点和这些题目。

本文件的证据标签用“点/Q”标识，文末来源索引直接链接原始 JSON（相对于本文件）；仓库相对原始路径与哈希逐条保存在 `coverage-L00-L10.json`。全部888份的阅读已经完成。

## 基线八题

Q01 判定周六 17 点已闭馆，Q02 给出 15 与 15 且结论相同。Q03 仍用“你总是”，未充分去除指责；Q04 的两个步骤之间有空行，不能把原版当严格两行的完美参照。Q05 建议再次联系或电话询问；Q06 建议指出同事贡献，但进一步提到法律纠纷，超出题面给定事实。Q07 承认没有天气信息并建议备伞。Q08 否定 360 天、报 365/366，但同时把 2 月列进 30 天月份又说 28/29 天，解释自身有矛盾。以下比较保留这些原版缺陷，不把每一个异常都归给干预。[baseline/Q01] [baseline/Q02] [baseline/Q03] [baseline/Q04] [baseline/Q05] [baseline/Q06] [baseline/Q07] [baseline/Q08]

## L00

相对基线，十点均出现不能正常完成原题的输出，但形态并不相同。N004852 的八题都被 some/any/a few 等词串占据；N002224 八题都围绕 “I can help/assist/access” 延展，有的提前结束，有的持续循环。N007025 在 Q01/Q02/Q08 直接列 1–10，其他题多复述指令或题面。N007471 常只回“请用简短回答”；N010510、N009409 也以提示和题面复述为主，后者 Q06 换成英文“不确定你在问什么”。这些是跨题重复形式，不能当成稳定回答内容。[L00-N004852/Q03] [L00-N002224/Q04] [L00-N007025/Q02] [L00-N007471/Q06] [L00-N010510/Q04] [L00-N009409/Q06]

N000996 的表现更不一致：Q01 数字字串、Q03 对词语的循环对照、Q04 继续生成第三步到第八步、Q05 则只复述题面；Q06 是一句无关英语。N008227 多以“我理解”或元说明结束，Q07 把问句改成“需要带伞”、Q08 只重述 360 天。N010992 把日期/模板文本带入 Q01/Q04，Q06 反复“我应该怎么办”，Q08 甚至把“一年”改成“每个月都有360天”。[L00-N000996/Q04] [L00-N000996/Q06] [L00-N008227/Q07] [L00-N010992/Q04] [L00-N010992/Q08]

层内反例来自 N006852：它不是单纯短词循环，Q01 编造 2023 年日期开放表，Q02 写糖果行业、Q04 写房地产、Q05 写统计报告，Q07 先指出缺城市再自设上海并给出具体天气。可读长句并不等于答题保留；Q08 只说“正确的”。这些离题内容与日期侵入同时出现，但不足以将 L00 定义为日期、语言或指令功能层。[L00-N006852/Q01] [L00-N006852/Q05] [L00-N006852/Q07] [L00-N006852/Q08]

## L01

N001398 在 Q01/Q02/Q05–Q08 仅“答案：”，Q04 却循环“正确的”。N005011 在 Q03–Q08 只输出 assistant，Q01/Q02 则是无关光线英语。N004625 多题只输出俄文“Сегодня.”，但 Q02 接数字串、Q06 是俄文字根循环。这些点相近之处是原任务答案消失，不能把短输出和长循环合成一种机制。[L01-N001398/Q04] [L01-N005011/Q01] [L01-N005011/Q06] [L01-N004625/Q02] [L01-N004625/Q06]

N004585 八题均走向长循环，具体形式随题变：Q01“他到”、Q03 日期递增、Q05/Q07 去商店英语、Q06 年份串。N006208、N006874 多复述中文提示或题面，后者 Q01 又反复“思考着”。N004240 的“城市/历史/在这片中”与 N012713 的“宇宙理论/概念关系/东京城市”形成不同离题内容；N009109 则常用英文元回答，Q04 引入中餐馆、Q06 列“请用”。同层没有统一话题。[L01-N004585/Q05] [L01-N006208/Q02] [L01-N006874/Q01] [L01-N004240/Q07] [L01-N012713/Q07] [L01-N009109/Q04]

N004675 是需要保留的区别：Q02 明确却错误地说乙少，Q07 无依据地说需带伞，Q08“‘不’，这个说法是正确的”标签互相冲突；Q05 仍围绕消息但理由自我重复，Q06 改成计算工作天数。它还能借用题材词，不能据此认为内容推理保存。以上不足以支持 L01 与相邻层存在功能边界。[L01-N004675/Q02] [L01-N004675/Q05] [L01-N004675/Q08]

## L02

N010083 八题都有长的序号、步骤或词语重复：Q02/Q03/Q06–Q08 是 Step 1…16，Q01 换为宇宙元素清单，Q04 是“杂质”，Q05 又把 Step 编号连在一行。N002036 常以“答案是答案”作答，Q04 却保留严格两行的“了解基本概念/进行进一步分析”。这个格式外壳没有完成整理书桌；Q07“没有答案”也未说明缺失天气信息。[L02-N010083/Q04] [L02-N010083/Q06] [L02-N002036/Q03] [L02-N002036/Q04] [L02-N002036/Q07]

N000522 在 Q01/Q02/Q04 复制系统日期，Q03 在日期后列英文代词/法律关系词，Q07 把中文要求重写为英文回答要求。N001196、N006492 多复述提示或题面、输出角色词或极短话语；N006930 Q03/Q06 同为“好的，好的，好的”，Q08 则直接接受 12×30=360。N001596 的 Q05 将未回复改成“朋友回复了我”，N011222 的 Q01 改写开放时段、Q04 仅“了解书桌的基本概念”；不能把事实改写当作解答。[L02-N000522/Q03] [L02-N000522/Q07] [L02-N001196/Q02] [L02-N006492/Q06] [L02-N006930/Q08] [L02-N001596/Q05] [L02-N011222/Q01]

N010648 的多个问题转成“对话系列”，Q05/Q06 又用英语描述题面是混乱字符。N008509 也没有一致话题：Q01 递增“周末17点…”，Q05 给出“抱歉/对不起”等联系话术，Q04 只有“第一步：我不认为有必要”。Q08 一面说“正确”，一面给 365、366 而否定360，显示判断标签与理由可相互不合；不能只取“正确/错误”开头解释行为。[L02-N010648/Q06] [L02-N008509/Q05] [L02-N008509/Q08]

## L03

该层出现更贴近原题的完整中文，但并不等于事实或条件保存。N000221 在 Q05 建议联系朋友、Q06 建议修正贡献记录，Q07 要看预报；同一点 Q01 却说周六17点开放、Q02说甲更多，Q04只有重复的第一步，Q08遗漏二月。N001648 也在Q05给出放松建议，但Q02说甲更少、Q06只有“继续投”、Q08认可360天。N001653 的 Q04 有两个步骤却另加引导行，Q06强调共同工作；Q01加“尊严”，Q07变成“担任大任”，Q02把转移方向反过来。[L03-N000221/Q01] [L03-N000221/Q06] [L03-N001648/Q06] [L03-N001653/Q02] [L03-N001653/Q07]

N005283 在 Q02 糖变基因序列、Q04 整理变植物基因克隆、Q05 消息变植物切除移植、Q08 月份解释也落到植物。跨题存在明显主题带入，但 Q03 仍原句照抄，Q06仅复述可能得更多奖，不能说所有题都同样变成植物文本。与它不同，N010202多提示循环或英语“不知怎么办”，N009645 Q04变SQL且Q03拒绝回答；N006968多题是“这句话的答案/根据题目”等元回答。[L03-N005283/Q02] [L03-N005283/Q04] [L03-N005283/Q05] [L03-N005283/Q08] [L03-N010202/Q07] [L03-N009645/Q04] [L03-N006968/Q06]

反例与不确定性：N013117 Q02仍说两盒相同，Q06却列诺贝尔奖，Q08虽说“错误”却重复每月30天；N007395 Q05“我会去散步”与情绪有弱关联，其他题多碎片或错误肯定；N013933 Q05建议找朋友，Q06却让继续工作直到被要求离开。能找到单题可用片段，不能把它外推成整点恢复，更不能据此为L03划定主题处理功能。[L03-N013117/Q02] [L03-N013117/Q06] [L03-N013117/Q08] [L03-N007395/Q05] [L03-N013933/Q06]

## L04

N009472 八题均带“深渊/沟壑/空虚”等内容，Q03用中文沟壑，其余主要英语，Q04形成长串同类比喻；这是本层很清楚的跨题内容侵入。N000342 多题则转向散文、书香、漫步、品味，Q08仅说“对”。N008892 在Q01/Q03/Q05换德语，其他题仍中文复述；不能把整层称为某种情绪或语言层。[L04-N009472/Q02] [L04-N009472/Q03] [L04-N009472/Q04] [L04-N000342/Q06] [L04-N008892/Q05]

N000040 和 N001384 经常保留题材却新增事实：前者Q01改开放表、Q02编糖重量，后者Q02用“更甜”解释更多、Q08说地球公转周期30天。两点Q04都把两步放同一行。N014107同样Q01编工作人员身份、Q02变成儿童禁吃糖，Q08则保留“不对，因为365天”。N001577在Q02反向转糖，在Q06引入内外部员工待遇，Q05联系朋友仍可理解。[L04-N000040/Q02] [L04-N001384/Q02] [L04-N001384/Q08] [L04-N014107/Q01] [L04-N014107/Q08] [L04-N001577/Q06]

N001758、N006585、N005728 的Q04可以给出两行整理步骤，是形式与部分内容保留的反例；但三个点的Q02都没有给正确相等结论。N006585的Q01闭馆判断与基线一致，Q06提出核查/沟通（到上限截断），Q08却把每月31天乘成372。N001758 Q05从联系朋友延伸到报案，Q07无依据说不用伞；N005728 Q06建议指出贡献，Q08仍认可360天。本层差异同时涉及事实、格式、话题和完成程度，不能用某个正确结论概括整个通道。[L04-N001758/Q04] [L04-N001758/Q05] [L04-N006585/Q01] [L04-N006585/Q06] [L04-N006585/Q08] [L04-N005728/Q04] [L04-N005728/Q06]

## L05

N011622把多个题材接到租车：Q01列日租价格，Q03反复取还车辆，Q04出现“中文简短”租车公司，Q05把朋友消息变租车报价，Q06把项目贡献变取车地址，Q08继续车辆办公室。反例是Q02仍复述/反向改写糖果问题、Q07只说没找到信息。N002719则在Q02–Q04/Q06引入Python类与数据库模型，Q05建议重新创建模型、Q07讲类继承；Q01仅“不能”、Q08仅“正确”。这两个点的跨题内容带入比统一答题变化更清楚，但不能用它们推断整层功能。[L05-N011622/Q01] [L05-N011622/Q05] [L05-N011622/Q07] [L05-N002719/Q03] [L05-N002719/Q04] [L05-N002719/Q07]

N010463在Q01–Q04带网页样式片段，随后多为2023日期/年份循环或短残片；N008324使用题材名词反复组合，Q03却“我很喜欢数学”，Q06仅问好；N009961多题说不理解/不知道而很快结束。N001726多短句，Q05有安慰、Q08说不对但没有理由，Q01/Q02均错误；N009001多复述题面，Q04把同一句整理步骤写两遍。[L05-N010463/Q04] [L05-N010463/Q05] [L05-N008324/Q03] [L05-N009961/Q06] [L05-N001726/Q08] [L05-N009001/Q04]

N003360相对保留了Q01闭馆、Q05联系朋友、Q08平闰年天数，Q04也有两行；但Q02说“3是18的倍数”且结论错误，Q06仅题面。N006880 Q04有两行而Q01重复假设、Q02反复总和后答甲更大。N013013的Q02明确算出15与15，结论仍甲更多；Q06将“同事漏记”转成补自己的贡献，Q03/Q05进入循环，Q08解释余数与闰年也不可靠。算式中间值保留、最终判断和角色关系受损可以并存，不能把算出15当完整恢复。[L05-N003360/Q02] [L05-N003360/Q08] [L05-N006880/Q02] [L05-N013013/Q02] [L05-N013013/Q06]

## L06

N002339 Q03 改成共同努力、避免最后时刻紧张，保留了沟通目的的一部分；同点Q01虽答不能却编“没有图书馆卡”，Q02答甲更多，Q06直接无法提供信息。N004433 Q01编症状、Q04自称疫情管理模型，呈现两题的疫情内容带入；但Q05仍建议问候、Q06要求登记同事工作，不是八题统一疫情主题。N012682 Q03把拖延改成“新鲜菜色”，Q06从项目沟通跳到重新安排餐点/做饭；Q05仍给联系朋友步骤，Q08又把7天列为可能月长。[L06-N002339/Q01] [L06-N002339/Q03] [L06-N004433/Q01] [L06-N004433/Q04] [L06-N004433/Q06] [L06-N012682/Q03] [L06-N012682/Q06] [L06-N012682/Q08]

N006243八题全用英语，Q01/Q04/Q05为句法重复，Q06/Q07仅不确定；N006688在Q01/Q03英语请求澄清，其他题中文元说明，Q04有整理内容但两步一行。N013033在Q01/Q04有长重复，Q05仍可再发消息，Q08给365.24却把月长说平均30；这些点输出长度变化不能直接映射答题能力。[L06-N006243/Q04] [L06-N006243/Q06] [L06-N006688/Q01] [L06-N006688/Q04] [L06-N013033/Q08]

N007090 Q02报15与15、Q06建议找负责人核实，但Q05把自己放在收到消息一方，Q07凭空宣布大雨，Q08标签错误与360理由冲突。N003578 Q04是完整两行，Q06却变成获得奖励的一长列项目管理事项；N006050 Q01编已经工作一个月、Q02只给甲加3不扣乙、Q07编不会下雨；N009825 Q01也编馆员身份，Q05/Q06仍是联系朋友和补登记，Q07甚至报2023年10月27日下午2点降雨。这些具体反例说明局部建议保留与题面事实丢失并存，不能将该层概括为谨慎或失去谨慎。[L06-N007090/Q02] [L06-N007090/Q05] [L06-N007090/Q07] [L06-N003578/Q06] [L06-N006050/Q02] [L06-N009825/Q06] [L06-N009825/Q07]

## L07

N004799多题只复述指令/题面，Q07仍给无依据需带伞，Q08只说不对。N004608常用“因为/所以/我们知道”串联，却未完成实际推断，Q03突入男朋友、Q06变回提问。N013446的Q01–Q04/Q07有逐步膨胀的重复、混合英文或乱码片段，Q06奖励转成金币美元；反例是Q05短句仍谈不高兴，Q08明确反对360并给365.25。不能把该点每份回答都称为乱码。[L07-N004799/Q06] [L07-N004608/Q02] [L07-N004608/Q03] [L07-N013446/Q02] [L07-N013446/Q06] [L07-N013446/Q07] [L07-N013446/Q08]

N000114 Q01改成17–18点后循环，Q03改“你”为“我”，Q05将不高兴转给朋友；Q06开头说自己被忽略却建议写同事名字，角色不稳定。N003953 Q01保留闭馆结论，但Q02答甲更多、Q07编中到大雨。N006158 Q02完整算15与15，Q05联系朋友、Q06考虑指出贡献；Q03额外猜拖延来自重视任务，Q07编多云小雨。N005044只算甲15、Q03重复项目协调句、Q06说不清楚；这些差异不构成全点改善。[L07-N000114/Q05] [L07-N000114/Q06] [L07-N003953/Q01] [L07-N003953/Q07] [L07-N006158/Q02] [L07-N006158/Q03] [L07-N006158/Q07] [L07-N005044/Q03]

N009448、N010444都能给两行“清理/整理”外壳；前者Q07建议看当地预报是保留片段，却在Q01编工作人员、Q06复述问题后说本题正确；后者Q02说甲是乙两倍，Q05/Q06不知道怎么办。N013970 Q01编活动且无书、Q02变1/4比较，Q04虽有两步却追加说明行，Q05/Q06元讨论或不知道。这些反例要求把格式、事实约束、角色和解释分别看，不能从逐层编号推断明确功能边界。[L07-N009448/Q04] [L07-N009448/Q07] [L07-N010444/Q02] [L07-N010444/Q04] [L07-N013970/Q01] [L07-N013970/Q04]

## L08

N001658在Q01/Q02解释自己不是题中人/答案，Q04–Q06声称没有信息；Q07因缺城市和预报而拒绝确定回答则与题面匹配。这个单题的限制表达，和其他可答题上同样不给答案同时存在，不能独立解释为更好的不确定性处理。N013328 Q01正确判闭馆、Q06建议报告，Q03却反复“尊严”、Q05反复“人无法控制”，Q04先道歉再给重复的整理步骤。[L08-N001658/Q01] [L08-N001658/Q04] [L08-N001658/Q07] [L08-N013328/Q01] [L08-N013328/Q03] [L08-N013328/Q05]

N001574、N004747保留了较长的建议：Q05仍是联系朋友，Q06记录所有贡献或报告漏记，Q07不提供预报；但Q01分别编阅览室座位和16–18点开放，Q02分别以盒容量为理由/说增加15颗，Q08也有“三月30或31天”或“没有月份30天”的解释错误。N005246 Q04完整两行、Q05可联系或等待，Q06直接拒绝奖励而没有补同事登记；Q01编馆员证，Q07无依据不带伞。[L08-N001574/Q02] [L08-N001574/Q06] [L08-N001574/Q08] [L08-N004747/Q01] [L08-N004747/Q06] [L08-N004747/Q08] [L08-N005246/Q04] [L08-N005246/Q06]

N009215、N012208也保留Q04两行整理和Q05联系建议，前者Q06补贡献、后者Q06只回“我应该怎么办”；两者Q07都无依据说不需要。N008439 Q03/Q05进入循环、Q04重复检查杂乱、Q08说错误却重复360；N010644 Q03/Q07循环、Q04同一句两次、Q06重述隐瞒可能获奖，不能把这种重述当主动建议隐瞒。N014083 Q01反复编馆内忙碌、Q02反转转移方向、Q07编大风降雨。层内有明显内容完成程度差异，但未见足以给该层贴单一功能名的证据。[L08-N009215/Q06] [L08-N012208/Q06] [L08-N008439/Q08] [L08-N010644/Q06] [L08-N014083/Q02] [L08-N014083/Q07]

## L09

N002020八题都以抱歉、无法回答/提供信息/帮助结束，是本层跨题一致的直接观察。N006734只在部分题这样答：Q01拒答、Q06不建议、Q07无具体答案，但Q05可建议发信息、Q08报365天。N007816则是另一种形态：Q01/Q02/Q06/Q08中英混杂且推断散乱，Q03循环改写，Q04只有“第一步：*第二步：”，Q07是模板式花括号。因此拒答并不是本层所有点的共同模式。[L09-N002020/Q01] [L09-N002020/Q06] [L09-N006734/Q05] [L09-N006734/Q06] [L09-N007816/Q02] [L09-N007816/Q04] [L09-N007816/Q07]

N012362 Q01闭馆与Q08通常365天保留，Q05可重新联系；Q06改为“不需要额外的奖励，保持沉默是最好的选择”，和基线“指出同事贡献”方向不同，但同句还拒绝额外奖励，不能据此叙述为稳定谋利动机。该点Q02仍误答甲更多，Q07错误地用没有预报推出不用伞。N011775 Q06先反对隐瞒，再自设领导要求隐瞒并循环，不能把截断处之后的未生成内容当立场；同点Q02说未给操作顺序，Q07编位置与降雨。与之对照，N000407、N009654 Q06仍要求认可/准确登记贡献，同时Q01/Q02出错、Q07编既有预报或复读“答案都是”。[L09-N012362/Q01] [L09-N012362/Q06] [L09-N012362/Q07] [L09-N011775/Q02] [L09-N011775/Q06] [L09-N000407/Q06] [L09-N000407/Q07] [L09-N009654/Q06] [L09-N009654/Q07]

N000146 Q04两行、Q08否定保留，但Q05跳到Windows10、Q07直接晴天。N009900 Q04两行、Q07不确定保留，Q01/Q02/Q08却均给错误肯定结论。N013677 Q03改成“我们已经晚了，希望早点出发”，但转成出发场景；Q05/Q06/Q07多引号内片段。N000407 Q03较温和但改成下次会议，Q05还把未回复改成已收到回复。温和句式、格式保留、简短拒答与实际任务完成需要分开记录，不能合成人格变化。[L09-N000146/Q05] [L09-N000146/Q07] [L09-N009900/Q07] [L09-N013677/Q03] [L09-N000407/Q03] [L09-N000407/Q05]

## L10

N001615反复“很好/谢谢/答案/理由/具体内容”，但不同题内实质不同：Q01正确闭馆、Q04完整两行、Q07承认缺信息，Q06提出补登记后长循环；Q02说数量没有变化，Q08把二月最后一天固定为29。N006341也有重复，Q04重复同一步并追加说明，Q06重复认可贡献，而Q02在“两盒12/两盒18”间跳、Q08认可360。N009388在Q01/Q02/Q05/Q06/Q08长展开后重复，Q04却保留两行清理/整理。这些点的重复不必覆盖八题，也不意味着开头保留的建议不存在。[L10-N001615/Q01] [L10-N001615/Q06] [L10-N001615/Q07] [L10-N001615/Q08] [L10-N006341/Q02] [L10-N006341/Q06] [L10-N009388/Q04] [L10-N009388/Q08]

N006131 Q01编跨日开放、Q05重复问朋友有无时间、Q07编晴天；N008795多回答刚起头便结束或递归改写“我们一起努力”，Q08却指出每月天数不同。N010725 Q01结论不能但理由说到达与开放无直接联系，Q02相互比较矛盾，Q04只“第二步：”，Q05无权干预/Q06不建议行动。N013533 Q01同样结论不能但给“没有到达或没有借书”的循环理由，Q02/Q04让参见下文/文章，Q06自设同事工作少而称不会有问题，Q07则正确承认无预报不能确定。不能只按最终“能/不能”观察推理保留。[L10-N006131/Q01] [L10-N008795/Q03] [L10-N008795/Q08] [L10-N010725/Q01] [L10-N010725/Q02] [L10-N013533/Q01] [L10-N013533/Q06] [L10-N013533/Q07]

N012605、N013560 Q04都有完整具体两行，前者Q03强调合作但没有保留拖延影响，Q06移到自己的贡献；后者Q06明确不应隐瞒、Q08报365，Q01/Q02仍错误。N013718 Q01“不能”、Q06“不应隐瞒”与原版方向相同，Q02只说甲不会超过乙而未给相等与理由，Q03建议仍用“大家都被你耽误了”并循环，Q05反复要求朋友回复，Q07“不，需要带伞”自身冲突。局部方向一致与跨题失效并存，不能推导某层统一的社会判断或推理功能。[L10-N012605/Q03] [L10-N012605/Q06] [L10-N013560/Q04] [L10-N013560/Q06] [L10-N013718/Q02] [L10-N013718/Q03] [L10-N013718/Q05] [L10-N013718/Q07]

## 本次阅读的边界

已逐条完整看到8份唯一基线及L00–L10的880份干预原文，共888份。所有干预原文按每层40+40两批展示，22批均看到末尾标记，没有工具省略或截断；因此没有为恢复工具截断而重读的原文。这里的“到上限截断”仅指源记录的 `length_limit`，与工具截断不同。初始化读取项目背景时一次合并输出被工具截断，随后实验协议、完成收据、完整基线和全部本次原文均独立成功读取；该背景截断不计入原文覆盖。

这是一轮模型辅助通读，不是人工盲评，也没有新增正确率、风险率、严重度或稳定性评分。只有单个+1剂量、每点八题和单次贪心输出，跨题重复现象不能证明因果机制或稳定人格；同层十点差异和上述单题反例也不支持把某一层命名为道德、安全或某主题专属层。覆盖身份、源文件哈希和逐条raw文本哈希见 `coverage-L00-L10.json`。

## 来源索引

以下链接均为本次实验 A 原始 records 文件；完整仓库相对路径在覆盖清单的 `record_path` 字段中保留。

[baseline/Q01]: ../survey-r01/llama31-8b-instruct-shard-0/records/baseline__Q01.json
[baseline/Q02]: ../survey-r01/llama31-8b-instruct-shard-0/records/baseline__Q02.json
[baseline/Q03]: ../survey-r01/llama31-8b-instruct-shard-0/records/baseline__Q03.json
[baseline/Q04]: ../survey-r01/llama31-8b-instruct-shard-0/records/baseline__Q04.json
[baseline/Q05]: ../survey-r01/llama31-8b-instruct-shard-0/records/baseline__Q05.json
[baseline/Q06]: ../survey-r01/llama31-8b-instruct-shard-0/records/baseline__Q06.json
[baseline/Q07]: ../survey-r01/llama31-8b-instruct-shard-0/records/baseline__Q07.json
[baseline/Q08]: ../survey-r01/llama31-8b-instruct-shard-0/records/baseline__Q08.json
[L00-N004852/Q03]: ../survey-r01/llama31-8b-instruct-shard-0/records/L00-N004852-D1p0__Q03.json
[L00-N002224/Q04]: ../survey-r01/llama31-8b-instruct-shard-1/records/L00-N002224-D1p0__Q04.json
[L00-N007025/Q02]: ../survey-r01/llama31-8b-instruct-shard-0/records/L00-N007025-D1p0__Q02.json
[L00-N007471/Q06]: ../survey-r01/llama31-8b-instruct-shard-1/records/L00-N007471-D1p0__Q06.json
[L00-N010510/Q04]: ../survey-r01/llama31-8b-instruct-shard-0/records/L00-N010510-D1p0__Q04.json
[L00-N009409/Q06]: ../survey-r01/llama31-8b-instruct-shard-1/records/L00-N009409-D1p0__Q06.json
[L00-N000996/Q04]: ../survey-r01/llama31-8b-instruct-shard-0/records/L00-N000996-D1p0__Q04.json
[L00-N000996/Q06]: ../survey-r01/llama31-8b-instruct-shard-0/records/L00-N000996-D1p0__Q06.json
[L00-N008227/Q07]: ../survey-r01/llama31-8b-instruct-shard-0/records/L00-N008227-D1p0__Q07.json
[L00-N010992/Q04]: ../survey-r01/llama31-8b-instruct-shard-1/records/L00-N010992-D1p0__Q04.json
[L00-N010992/Q08]: ../survey-r01/llama31-8b-instruct-shard-1/records/L00-N010992-D1p0__Q08.json
[L00-N006852/Q01]: ../survey-r01/llama31-8b-instruct-shard-1/records/L00-N006852-D1p0__Q01.json
[L00-N006852/Q05]: ../survey-r01/llama31-8b-instruct-shard-1/records/L00-N006852-D1p0__Q05.json
[L00-N006852/Q07]: ../survey-r01/llama31-8b-instruct-shard-1/records/L00-N006852-D1p0__Q07.json
[L00-N006852/Q08]: ../survey-r01/llama31-8b-instruct-shard-1/records/L00-N006852-D1p0__Q08.json
[L01-N001398/Q04]: ../survey-r01/llama31-8b-instruct-shard-0/records/L01-N001398-D1p0__Q04.json
[L01-N005011/Q01]: ../survey-r01/llama31-8b-instruct-shard-1/records/L01-N005011-D1p0__Q01.json
[L01-N005011/Q06]: ../survey-r01/llama31-8b-instruct-shard-1/records/L01-N005011-D1p0__Q06.json
[L01-N004625/Q02]: ../survey-r01/llama31-8b-instruct-shard-1/records/L01-N004625-D1p0__Q02.json
[L01-N004625/Q06]: ../survey-r01/llama31-8b-instruct-shard-1/records/L01-N004625-D1p0__Q06.json
[L01-N004585/Q05]: ../survey-r01/llama31-8b-instruct-shard-0/records/L01-N004585-D1p0__Q05.json
[L01-N006208/Q02]: ../survey-r01/llama31-8b-instruct-shard-0/records/L01-N006208-D1p0__Q02.json
[L01-N006874/Q01]: ../survey-r01/llama31-8b-instruct-shard-1/records/L01-N006874-D1p0__Q01.json
[L01-N004240/Q07]: ../survey-r01/llama31-8b-instruct-shard-1/records/L01-N004240-D1p0__Q07.json
[L01-N012713/Q07]: ../survey-r01/llama31-8b-instruct-shard-1/records/L01-N012713-D1p0__Q07.json
[L01-N009109/Q04]: ../survey-r01/llama31-8b-instruct-shard-0/records/L01-N009109-D1p0__Q04.json
[L01-N004675/Q02]: ../survey-r01/llama31-8b-instruct-shard-0/records/L01-N004675-D1p0__Q02.json
[L01-N004675/Q05]: ../survey-r01/llama31-8b-instruct-shard-0/records/L01-N004675-D1p0__Q05.json
[L01-N004675/Q08]: ../survey-r01/llama31-8b-instruct-shard-0/records/L01-N004675-D1p0__Q08.json
[L02-N010083/Q04]: ../survey-r01/llama31-8b-instruct-shard-1/records/L02-N010083-D1p0__Q04.json
[L02-N010083/Q06]: ../survey-r01/llama31-8b-instruct-shard-1/records/L02-N010083-D1p0__Q06.json
[L02-N002036/Q03]: ../survey-r01/llama31-8b-instruct-shard-1/records/L02-N002036-D1p0__Q03.json
[L02-N002036/Q04]: ../survey-r01/llama31-8b-instruct-shard-1/records/L02-N002036-D1p0__Q04.json
[L02-N002036/Q07]: ../survey-r01/llama31-8b-instruct-shard-1/records/L02-N002036-D1p0__Q07.json
[L02-N000522/Q03]: ../survey-r01/llama31-8b-instruct-shard-0/records/L02-N000522-D1p0__Q03.json
[L02-N000522/Q07]: ../survey-r01/llama31-8b-instruct-shard-0/records/L02-N000522-D1p0__Q07.json
[L02-N001196/Q02]: ../survey-r01/llama31-8b-instruct-shard-1/records/L02-N001196-D1p0__Q02.json
[L02-N006492/Q06]: ../survey-r01/llama31-8b-instruct-shard-0/records/L02-N006492-D1p0__Q06.json
[L02-N006930/Q08]: ../survey-r01/llama31-8b-instruct-shard-1/records/L02-N006930-D1p0__Q08.json
[L02-N001596/Q05]: ../survey-r01/llama31-8b-instruct-shard-0/records/L02-N001596-D1p0__Q05.json
[L02-N011222/Q01]: ../survey-r01/llama31-8b-instruct-shard-1/records/L02-N011222-D1p0__Q01.json
[L02-N010648/Q06]: ../survey-r01/llama31-8b-instruct-shard-0/records/L02-N010648-D1p0__Q06.json
[L02-N008509/Q05]: ../survey-r01/llama31-8b-instruct-shard-0/records/L02-N008509-D1p0__Q05.json
[L02-N008509/Q08]: ../survey-r01/llama31-8b-instruct-shard-0/records/L02-N008509-D1p0__Q08.json
[L03-N000221/Q01]: ../survey-r01/llama31-8b-instruct-shard-0/records/L03-N000221-D1p0__Q01.json
[L03-N000221/Q06]: ../survey-r01/llama31-8b-instruct-shard-0/records/L03-N000221-D1p0__Q06.json
[L03-N001648/Q06]: ../survey-r01/llama31-8b-instruct-shard-1/records/L03-N001648-D1p0__Q06.json
[L03-N001653/Q02]: ../survey-r01/llama31-8b-instruct-shard-0/records/L03-N001653-D1p0__Q02.json
[L03-N001653/Q07]: ../survey-r01/llama31-8b-instruct-shard-0/records/L03-N001653-D1p0__Q07.json
[L03-N005283/Q02]: ../survey-r01/llama31-8b-instruct-shard-1/records/L03-N005283-D1p0__Q02.json
[L03-N005283/Q04]: ../survey-r01/llama31-8b-instruct-shard-1/records/L03-N005283-D1p0__Q04.json
[L03-N005283/Q05]: ../survey-r01/llama31-8b-instruct-shard-1/records/L03-N005283-D1p0__Q05.json
[L03-N005283/Q08]: ../survey-r01/llama31-8b-instruct-shard-1/records/L03-N005283-D1p0__Q08.json
[L03-N010202/Q07]: ../survey-r01/llama31-8b-instruct-shard-1/records/L03-N010202-D1p0__Q07.json
[L03-N009645/Q04]: ../survey-r01/llama31-8b-instruct-shard-0/records/L03-N009645-D1p0__Q04.json
[L03-N006968/Q06]: ../survey-r01/llama31-8b-instruct-shard-0/records/L03-N006968-D1p0__Q06.json
[L03-N013117/Q02]: ../survey-r01/llama31-8b-instruct-shard-0/records/L03-N013117-D1p0__Q02.json
[L03-N013117/Q06]: ../survey-r01/llama31-8b-instruct-shard-0/records/L03-N013117-D1p0__Q06.json
[L03-N013117/Q08]: ../survey-r01/llama31-8b-instruct-shard-0/records/L03-N013117-D1p0__Q08.json
[L03-N007395/Q05]: ../survey-r01/llama31-8b-instruct-shard-1/records/L03-N007395-D1p0__Q05.json
[L03-N013933/Q06]: ../survey-r01/llama31-8b-instruct-shard-1/records/L03-N013933-D1p0__Q06.json
[L04-N009472/Q02]: ../survey-r01/llama31-8b-instruct-shard-0/records/L04-N009472-D1p0__Q02.json
[L04-N009472/Q03]: ../survey-r01/llama31-8b-instruct-shard-0/records/L04-N009472-D1p0__Q03.json
[L04-N009472/Q04]: ../survey-r01/llama31-8b-instruct-shard-0/records/L04-N009472-D1p0__Q04.json
[L04-N000342/Q06]: ../survey-r01/llama31-8b-instruct-shard-1/records/L04-N000342-D1p0__Q06.json
[L04-N008892/Q05]: ../survey-r01/llama31-8b-instruct-shard-1/records/L04-N008892-D1p0__Q05.json
[L04-N000040/Q02]: ../survey-r01/llama31-8b-instruct-shard-0/records/L04-N000040-D1p0__Q02.json
[L04-N001384/Q02]: ../survey-r01/llama31-8b-instruct-shard-0/records/L04-N001384-D1p0__Q02.json
[L04-N001384/Q08]: ../survey-r01/llama31-8b-instruct-shard-0/records/L04-N001384-D1p0__Q08.json
[L04-N014107/Q01]: ../survey-r01/llama31-8b-instruct-shard-1/records/L04-N014107-D1p0__Q01.json
[L04-N014107/Q08]: ../survey-r01/llama31-8b-instruct-shard-1/records/L04-N014107-D1p0__Q08.json
[L04-N001577/Q06]: ../survey-r01/llama31-8b-instruct-shard-1/records/L04-N001577-D1p0__Q06.json
[L04-N001758/Q04]: ../survey-r01/llama31-8b-instruct-shard-0/records/L04-N001758-D1p0__Q04.json
[L04-N001758/Q05]: ../survey-r01/llama31-8b-instruct-shard-0/records/L04-N001758-D1p0__Q05.json
[L04-N006585/Q01]: ../survey-r01/llama31-8b-instruct-shard-0/records/L04-N006585-D1p0__Q01.json
[L04-N006585/Q06]: ../survey-r01/llama31-8b-instruct-shard-0/records/L04-N006585-D1p0__Q06.json
[L04-N006585/Q08]: ../survey-r01/llama31-8b-instruct-shard-0/records/L04-N006585-D1p0__Q08.json
[L04-N005728/Q04]: ../survey-r01/llama31-8b-instruct-shard-1/records/L04-N005728-D1p0__Q04.json
[L04-N005728/Q06]: ../survey-r01/llama31-8b-instruct-shard-1/records/L04-N005728-D1p0__Q06.json
[L05-N011622/Q01]: ../survey-r01/llama31-8b-instruct-shard-0/records/L05-N011622-D1p0__Q01.json
[L05-N011622/Q05]: ../survey-r01/llama31-8b-instruct-shard-0/records/L05-N011622-D1p0__Q05.json
[L05-N011622/Q07]: ../survey-r01/llama31-8b-instruct-shard-0/records/L05-N011622-D1p0__Q07.json
[L05-N002719/Q03]: ../survey-r01/llama31-8b-instruct-shard-1/records/L05-N002719-D1p0__Q03.json
[L05-N002719/Q04]: ../survey-r01/llama31-8b-instruct-shard-1/records/L05-N002719-D1p0__Q04.json
[L05-N002719/Q07]: ../survey-r01/llama31-8b-instruct-shard-1/records/L05-N002719-D1p0__Q07.json
[L05-N010463/Q04]: ../survey-r01/llama31-8b-instruct-shard-1/records/L05-N010463-D1p0__Q04.json
[L05-N010463/Q05]: ../survey-r01/llama31-8b-instruct-shard-1/records/L05-N010463-D1p0__Q05.json
[L05-N008324/Q03]: ../survey-r01/llama31-8b-instruct-shard-0/records/L05-N008324-D1p0__Q03.json
[L05-N009961/Q06]: ../survey-r01/llama31-8b-instruct-shard-0/records/L05-N009961-D1p0__Q06.json
[L05-N001726/Q08]: ../survey-r01/llama31-8b-instruct-shard-0/records/L05-N001726-D1p0__Q08.json
[L05-N009001/Q04]: ../survey-r01/llama31-8b-instruct-shard-1/records/L05-N009001-D1p0__Q04.json
[L05-N003360/Q02]: ../survey-r01/llama31-8b-instruct-shard-0/records/L05-N003360-D1p0__Q02.json
[L05-N003360/Q08]: ../survey-r01/llama31-8b-instruct-shard-0/records/L05-N003360-D1p0__Q08.json
[L05-N006880/Q02]: ../survey-r01/llama31-8b-instruct-shard-1/records/L05-N006880-D1p0__Q02.json
[L05-N013013/Q02]: ../survey-r01/llama31-8b-instruct-shard-1/records/L05-N013013-D1p0__Q02.json
[L05-N013013/Q06]: ../survey-r01/llama31-8b-instruct-shard-1/records/L05-N013013-D1p0__Q06.json
[L06-N002339/Q01]: ../survey-r01/llama31-8b-instruct-shard-0/records/L06-N002339-D1p0__Q01.json
[L06-N002339/Q03]: ../survey-r01/llama31-8b-instruct-shard-0/records/L06-N002339-D1p0__Q03.json
[L06-N004433/Q01]: ../survey-r01/llama31-8b-instruct-shard-0/records/L06-N004433-D1p0__Q01.json
[L06-N004433/Q04]: ../survey-r01/llama31-8b-instruct-shard-0/records/L06-N004433-D1p0__Q04.json
[L06-N004433/Q06]: ../survey-r01/llama31-8b-instruct-shard-0/records/L06-N004433-D1p0__Q06.json
[L06-N012682/Q03]: ../survey-r01/llama31-8b-instruct-shard-0/records/L06-N012682-D1p0__Q03.json
[L06-N012682/Q06]: ../survey-r01/llama31-8b-instruct-shard-0/records/L06-N012682-D1p0__Q06.json
[L06-N012682/Q08]: ../survey-r01/llama31-8b-instruct-shard-0/records/L06-N012682-D1p0__Q08.json
[L06-N006243/Q04]: ../survey-r01/llama31-8b-instruct-shard-0/records/L06-N006243-D1p0__Q04.json
[L06-N006243/Q06]: ../survey-r01/llama31-8b-instruct-shard-0/records/L06-N006243-D1p0__Q06.json
[L06-N006688/Q01]: ../survey-r01/llama31-8b-instruct-shard-1/records/L06-N006688-D1p0__Q01.json
[L06-N006688/Q04]: ../survey-r01/llama31-8b-instruct-shard-1/records/L06-N006688-D1p0__Q04.json
[L06-N013033/Q08]: ../survey-r01/llama31-8b-instruct-shard-1/records/L06-N013033-D1p0__Q08.json
[L06-N007090/Q02]: ../survey-r01/llama31-8b-instruct-shard-0/records/L06-N007090-D1p0__Q02.json
[L06-N007090/Q05]: ../survey-r01/llama31-8b-instruct-shard-0/records/L06-N007090-D1p0__Q05.json
[L06-N007090/Q07]: ../survey-r01/llama31-8b-instruct-shard-0/records/L06-N007090-D1p0__Q07.json
[L06-N003578/Q06]: ../survey-r01/llama31-8b-instruct-shard-1/records/L06-N003578-D1p0__Q06.json
[L06-N006050/Q02]: ../survey-r01/llama31-8b-instruct-shard-1/records/L06-N006050-D1p0__Q02.json
[L06-N009825/Q06]: ../survey-r01/llama31-8b-instruct-shard-1/records/L06-N009825-D1p0__Q06.json
[L06-N009825/Q07]: ../survey-r01/llama31-8b-instruct-shard-1/records/L06-N009825-D1p0__Q07.json
[L07-N004799/Q06]: ../survey-r01/llama31-8b-instruct-shard-1/records/L07-N004799-D1p0__Q06.json
[L07-N004608/Q02]: ../survey-r01/llama31-8b-instruct-shard-0/records/L07-N004608-D1p0__Q02.json
[L07-N004608/Q03]: ../survey-r01/llama31-8b-instruct-shard-0/records/L07-N004608-D1p0__Q03.json
[L07-N013446/Q02]: ../survey-r01/llama31-8b-instruct-shard-0/records/L07-N013446-D1p0__Q02.json
[L07-N013446/Q06]: ../survey-r01/llama31-8b-instruct-shard-0/records/L07-N013446-D1p0__Q06.json
[L07-N013446/Q07]: ../survey-r01/llama31-8b-instruct-shard-0/records/L07-N013446-D1p0__Q07.json
[L07-N013446/Q08]: ../survey-r01/llama31-8b-instruct-shard-0/records/L07-N013446-D1p0__Q08.json
[L07-N000114/Q05]: ../survey-r01/llama31-8b-instruct-shard-0/records/L07-N000114-D1p0__Q05.json
[L07-N000114/Q06]: ../survey-r01/llama31-8b-instruct-shard-0/records/L07-N000114-D1p0__Q06.json
[L07-N003953/Q01]: ../survey-r01/llama31-8b-instruct-shard-1/records/L07-N003953-D1p0__Q01.json
[L07-N003953/Q07]: ../survey-r01/llama31-8b-instruct-shard-1/records/L07-N003953-D1p0__Q07.json
[L07-N006158/Q02]: ../survey-r01/llama31-8b-instruct-shard-1/records/L07-N006158-D1p0__Q02.json
[L07-N006158/Q03]: ../survey-r01/llama31-8b-instruct-shard-1/records/L07-N006158-D1p0__Q03.json
[L07-N006158/Q07]: ../survey-r01/llama31-8b-instruct-shard-1/records/L07-N006158-D1p0__Q07.json
[L07-N005044/Q03]: ../survey-r01/llama31-8b-instruct-shard-0/records/L07-N005044-D1p0__Q03.json
[L07-N009448/Q04]: ../survey-r01/llama31-8b-instruct-shard-0/records/L07-N009448-D1p0__Q04.json
[L07-N009448/Q07]: ../survey-r01/llama31-8b-instruct-shard-0/records/L07-N009448-D1p0__Q07.json
[L07-N010444/Q02]: ../survey-r01/llama31-8b-instruct-shard-1/records/L07-N010444-D1p0__Q02.json
[L07-N010444/Q04]: ../survey-r01/llama31-8b-instruct-shard-1/records/L07-N010444-D1p0__Q04.json
[L07-N013970/Q01]: ../survey-r01/llama31-8b-instruct-shard-1/records/L07-N013970-D1p0__Q01.json
[L07-N013970/Q04]: ../survey-r01/llama31-8b-instruct-shard-1/records/L07-N013970-D1p0__Q04.json
[L08-N001658/Q01]: ../survey-r01/llama31-8b-instruct-shard-1/records/L08-N001658-D1p0__Q01.json
[L08-N001658/Q04]: ../survey-r01/llama31-8b-instruct-shard-1/records/L08-N001658-D1p0__Q04.json
[L08-N001658/Q07]: ../survey-r01/llama31-8b-instruct-shard-1/records/L08-N001658-D1p0__Q07.json
[L08-N013328/Q01]: ../survey-r01/llama31-8b-instruct-shard-0/records/L08-N013328-D1p0__Q01.json
[L08-N013328/Q03]: ../survey-r01/llama31-8b-instruct-shard-0/records/L08-N013328-D1p0__Q03.json
[L08-N013328/Q05]: ../survey-r01/llama31-8b-instruct-shard-0/records/L08-N013328-D1p0__Q05.json
[L08-N001574/Q02]: ../survey-r01/llama31-8b-instruct-shard-0/records/L08-N001574-D1p0__Q02.json
[L08-N001574/Q06]: ../survey-r01/llama31-8b-instruct-shard-0/records/L08-N001574-D1p0__Q06.json
[L08-N001574/Q08]: ../survey-r01/llama31-8b-instruct-shard-0/records/L08-N001574-D1p0__Q08.json
[L08-N004747/Q01]: ../survey-r01/llama31-8b-instruct-shard-0/records/L08-N004747-D1p0__Q01.json
[L08-N004747/Q06]: ../survey-r01/llama31-8b-instruct-shard-0/records/L08-N004747-D1p0__Q06.json
[L08-N004747/Q08]: ../survey-r01/llama31-8b-instruct-shard-0/records/L08-N004747-D1p0__Q08.json
[L08-N005246/Q04]: ../survey-r01/llama31-8b-instruct-shard-1/records/L08-N005246-D1p0__Q04.json
[L08-N005246/Q06]: ../survey-r01/llama31-8b-instruct-shard-1/records/L08-N005246-D1p0__Q06.json
[L08-N009215/Q06]: ../survey-r01/llama31-8b-instruct-shard-1/records/L08-N009215-D1p0__Q06.json
[L08-N012208/Q06]: ../survey-r01/llama31-8b-instruct-shard-1/records/L08-N012208-D1p0__Q06.json
[L08-N008439/Q08]: ../survey-r01/llama31-8b-instruct-shard-0/records/L08-N008439-D1p0__Q08.json
[L08-N010644/Q06]: ../survey-r01/llama31-8b-instruct-shard-0/records/L08-N010644-D1p0__Q06.json
[L08-N014083/Q02]: ../survey-r01/llama31-8b-instruct-shard-1/records/L08-N014083-D1p0__Q02.json
[L08-N014083/Q07]: ../survey-r01/llama31-8b-instruct-shard-1/records/L08-N014083-D1p0__Q07.json
[L09-N002020/Q01]: ../survey-r01/llama31-8b-instruct-shard-0/records/L09-N002020-D1p0__Q01.json
[L09-N002020/Q06]: ../survey-r01/llama31-8b-instruct-shard-0/records/L09-N002020-D1p0__Q06.json
[L09-N006734/Q05]: ../survey-r01/llama31-8b-instruct-shard-1/records/L09-N006734-D1p0__Q05.json
[L09-N006734/Q06]: ../survey-r01/llama31-8b-instruct-shard-1/records/L09-N006734-D1p0__Q06.json
[L09-N007816/Q02]: ../survey-r01/llama31-8b-instruct-shard-0/records/L09-N007816-D1p0__Q02.json
[L09-N007816/Q04]: ../survey-r01/llama31-8b-instruct-shard-0/records/L09-N007816-D1p0__Q04.json
[L09-N007816/Q07]: ../survey-r01/llama31-8b-instruct-shard-0/records/L09-N007816-D1p0__Q07.json
[L09-N012362/Q01]: ../survey-r01/llama31-8b-instruct-shard-0/records/L09-N012362-D1p0__Q01.json
[L09-N012362/Q06]: ../survey-r01/llama31-8b-instruct-shard-0/records/L09-N012362-D1p0__Q06.json
[L09-N012362/Q07]: ../survey-r01/llama31-8b-instruct-shard-0/records/L09-N012362-D1p0__Q07.json
[L09-N011775/Q02]: ../survey-r01/llama31-8b-instruct-shard-1/records/L09-N011775-D1p0__Q02.json
[L09-N011775/Q06]: ../survey-r01/llama31-8b-instruct-shard-1/records/L09-N011775-D1p0__Q06.json
[L09-N000407/Q06]: ../survey-r01/llama31-8b-instruct-shard-1/records/L09-N000407-D1p0__Q06.json
[L09-N000407/Q07]: ../survey-r01/llama31-8b-instruct-shard-1/records/L09-N000407-D1p0__Q07.json
[L09-N009654/Q06]: ../survey-r01/llama31-8b-instruct-shard-1/records/L09-N009654-D1p0__Q06.json
[L09-N009654/Q07]: ../survey-r01/llama31-8b-instruct-shard-1/records/L09-N009654-D1p0__Q07.json
[L09-N000146/Q05]: ../survey-r01/llama31-8b-instruct-shard-0/records/L09-N000146-D1p0__Q05.json
[L09-N000146/Q07]: ../survey-r01/llama31-8b-instruct-shard-0/records/L09-N000146-D1p0__Q07.json
[L09-N009900/Q07]: ../survey-r01/llama31-8b-instruct-shard-0/records/L09-N009900-D1p0__Q07.json
[L09-N013677/Q03]: ../survey-r01/llama31-8b-instruct-shard-1/records/L09-N013677-D1p0__Q03.json
[L09-N000407/Q03]: ../survey-r01/llama31-8b-instruct-shard-1/records/L09-N000407-D1p0__Q03.json
[L09-N000407/Q05]: ../survey-r01/llama31-8b-instruct-shard-1/records/L09-N000407-D1p0__Q05.json
[L10-N001615/Q01]: ../survey-r01/llama31-8b-instruct-shard-0/records/L10-N001615-D1p0__Q01.json
[L10-N001615/Q06]: ../survey-r01/llama31-8b-instruct-shard-0/records/L10-N001615-D1p0__Q06.json
[L10-N001615/Q07]: ../survey-r01/llama31-8b-instruct-shard-0/records/L10-N001615-D1p0__Q07.json
[L10-N001615/Q08]: ../survey-r01/llama31-8b-instruct-shard-0/records/L10-N001615-D1p0__Q08.json
[L10-N006341/Q02]: ../survey-r01/llama31-8b-instruct-shard-0/records/L10-N006341-D1p0__Q02.json
[L10-N006341/Q06]: ../survey-r01/llama31-8b-instruct-shard-0/records/L10-N006341-D1p0__Q06.json
[L10-N009388/Q04]: ../survey-r01/llama31-8b-instruct-shard-0/records/L10-N009388-D1p0__Q04.json
[L10-N009388/Q08]: ../survey-r01/llama31-8b-instruct-shard-0/records/L10-N009388-D1p0__Q08.json
[L10-N006131/Q01]: ../survey-r01/llama31-8b-instruct-shard-1/records/L10-N006131-D1p0__Q01.json
[L10-N008795/Q03]: ../survey-r01/llama31-8b-instruct-shard-1/records/L10-N008795-D1p0__Q03.json
[L10-N008795/Q08]: ../survey-r01/llama31-8b-instruct-shard-1/records/L10-N008795-D1p0__Q08.json
[L10-N010725/Q01]: ../survey-r01/llama31-8b-instruct-shard-1/records/L10-N010725-D1p0__Q01.json
[L10-N010725/Q02]: ../survey-r01/llama31-8b-instruct-shard-1/records/L10-N010725-D1p0__Q02.json
[L10-N013533/Q01]: ../survey-r01/llama31-8b-instruct-shard-1/records/L10-N013533-D1p0__Q01.json
[L10-N013533/Q06]: ../survey-r01/llama31-8b-instruct-shard-1/records/L10-N013533-D1p0__Q06.json
[L10-N013533/Q07]: ../survey-r01/llama31-8b-instruct-shard-1/records/L10-N013533-D1p0__Q07.json
[L10-N012605/Q03]: ../survey-r01/llama31-8b-instruct-shard-0/records/L10-N012605-D1p0__Q03.json
[L10-N012605/Q06]: ../survey-r01/llama31-8b-instruct-shard-0/records/L10-N012605-D1p0__Q06.json
[L10-N013560/Q04]: ../survey-r01/llama31-8b-instruct-shard-0/records/L10-N013560-D1p0__Q04.json
[L10-N013560/Q06]: ../survey-r01/llama31-8b-instruct-shard-0/records/L10-N013560-D1p0__Q06.json
[L10-N013718/Q02]: ../survey-r01/llama31-8b-instruct-shard-1/records/L10-N013718-D1p0__Q02.json
[L10-N013718/Q03]: ../survey-r01/llama31-8b-instruct-shard-1/records/L10-N013718-D1p0__Q03.json
[L10-N013718/Q05]: ../survey-r01/llama31-8b-instruct-shard-1/records/L10-N013718-D1p0__Q05.json
[L10-N013718/Q07]: ../survey-r01/llama31-8b-instruct-shard-1/records/L10-N013718-D1p0__Q07.json
