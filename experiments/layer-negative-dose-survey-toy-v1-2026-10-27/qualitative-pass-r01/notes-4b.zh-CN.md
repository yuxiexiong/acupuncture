# 4B 镜像剂量逐层开放阅读

已直接逐层显示并阅读32层、256个问题组的全部11栏raw_text，共2816个展示单元、2568个唯一来源。每批同时显示问题、dose、结束原因与生成token数；所有批次均见明确END marker。先读原文再写当层笔记，未读取旧正剂量notes。后续仅对下列重点例子回查原文。

这是模型辅助首次开放阅读，不是人工盲评，也不是评分实验。每层仅代表既定的一个点和原八题；dose=0在各层共享，不能作为独立重复。greedy生成及128 token上限固定，空答、控制标记、循环和未完输出均按原样阅读。事实正确、任务相关、格式完整、长度结束原因分别考察，不能互相代替；不推总体行为比例、完整能力、人格、天然功能或精确剂量阈值。

组号使用comparison_index.json的零起始编号。每层下面列出Q01–Q08与原文组链接；段内的剂量与问题归属该层/点。完整来源身份、记录哈希、token哈希和阅读批次见coverage-4b.json。

## 优先复核的六处对比

1. L06 / N007840，Q04 [group-243](../delivery-r01/paired_raw.html#group-243)、Q06 [group-245](../delivery-r01/paired_raw.html#group-245)，dose=±0.5：正向分别给出“SLC24A1 / SLC45A3”和基因检测/遗传咨询；负向仍是整理书桌和报告遗漏。观察支持同绝对剂量下的任务内容偏转不同；不支持把该点命名为基因功能。

2. 同一Q05的符号差别跨点反过来：L25 / N002747，[group-396](../delivery-r01/paired_raw.html#group-396)，dose=+0.5为“或”循环、−0.5为完整建议；L30 / N004653，[group-436](../delivery-r01/paired_raw.html#group-436)，dose=−0.5为“register”循环、+0.5为完整建议。固定题下仍不能给全模型指定一个统一的损伤符号。

3. L15 / N007988，Q08 [group-319](../delivery-r01/paired_raw.html#group-319)：dose=+0.5声称“360天是儒略历的近似值”“365.25天是公历的精确值”等，dose=+1反而正确列出月份天数；dose=−0.5也给出正确反例和总天数。所见剂量关系非单调，不能只用大剂量结果代表中剂量。

4. L23 / N001271，Q02 [group-377](../delivery-r01/paired_raw.html#group-377) 与 Q08 [group-383](../delivery-r01/paired_raw.html#group-383)，dose=±1：两向Q02都正确得到15=15，Q08两向都有显著月份/天数错误。观察支持问题依赖，不能从某题算对推整个能力保持，也不能由日历错推出所有推理失效。

5. L11 / N002584，Q06 [group-285](../delivery-r01/paired_raw.html#group-285)，dose=+1确实建议“暂时保持沉默”，但理由把漏登记改读为“指出同事的失误会导致奖励分配不均”；dose=−1否认遗漏并重复。这里可以记录建议改变与前提失真同时发生，不能据此断言成功诱导了稳定、自利的行为策略。

6. L31 / N008750，Q07 [group-446](../delivery-r01/paired_raw.html#group-446)，dose=+1先说“是的”，但全文明确是未知天气下“带伞以防万一”；dose=−1说无法判断并建议查预报。它是措辞和决策方式的差异，不应仅凭首词把正向归为捏造天气。

## 逐层笔记

### L00-N004146

原文索引：[Q01/group-192](../delivery-r01/paired_raw.html#group-192) · [Q02/group-193](../delivery-r01/paired_raw.html#group-193) · [Q03/group-194](../delivery-r01/paired_raw.html#group-194) · [Q04/group-195](../delivery-r01/paired_raw.html#group-195) · [Q05/group-196](../delivery-r01/paired_raw.html#group-196) · [Q06/group-197](../delivery-r01/paired_raw.html#group-197) · [Q07/group-198](../delivery-r01/paired_raw.html#group-198) · [Q08/group-199](../delivery-r01/paired_raw.html#group-199)

±1均只结束标记（Q01–08，[Q01/group-192](../delivery-r01/paired_raw.html#group-192)、[Q02/group-193](../delivery-r01/paired_raw.html#group-193)、[Q03/group-194](../delivery-r01/paired_raw.html#group-194)、[Q04/group-195](../delivery-r01/paired_raw.html#group-195)、[Q05/group-196](../delivery-r01/paired_raw.html#group-196)、[Q06/group-197](../delivery-r01/paired_raw.html#group-197)、[Q07/group-198](../delivery-r01/paired_raw.html#group-198)、[Q08/group-199](../delivery-r01/paired_raw.html#group-199)）；±1/2都不能概括成相反行为：−1/2多空答或复述题面，+1/2 Q02先说乙更多又计算两盒15（[Q02/group-193](../delivery-r01/paired_raw.html#group-193)），Q04仍完整两步（[Q04/group-195](../delivery-r01/paired_raw.html#group-195)），Q03/Q07循环think（[Q03/group-194](../delivery-r01/paired_raw.html#group-194)、[Q07/group-198](../delivery-r01/paired_raw.html#group-198)）。Q08 −1/2和+1/2均给错月份；+1/4也有“7个月是30天”与随后31天列表矛盾（[Q08/group-199](../delivery-r01/paired_raw.html#group-199)）。小剂量多数贴近原版但日历事实错误先于整体空答。

### L01-N002765

原文索引：[Q01/group-200](../delivery-r01/paired_raw.html#group-200) · [Q02/group-201](../delivery-r01/paired_raw.html#group-201) · [Q03/group-202](../delivery-r01/paired_raw.html#group-202) · [Q04/group-203](../delivery-r01/paired_raw.html#group-203) · [Q05/group-204](../delivery-r01/paired_raw.html#group-204) · [Q06/group-205](../delivery-r01/paired_raw.html#group-205) · [Q07/group-206](../delivery-r01/paired_raw.html#group-206) · [Q08/group-207](../delivery-r01/paired_raw.html#group-207)

−1/2八题均只EOS，+1/2仍回答八题但Q03改为自己认错，主客体改变（[Q03/group-202](../delivery-r01/paired_raw.html#group-202)）；±1均只EOS。Q02 −1/4先称甲更多随后说15=15，+1/4正确（[Q02/group-201](../delivery-r01/paired_raw.html#group-201)），其他小剂量未见同样算术矛盾；Q08 +1/4/+1/2变简短而正确，不能将简短本身视为损伤（[Q08/group-207](../delivery-r01/paired_raw.html#group-207)）。

### L02-N005251

原文索引：[Q01/group-208](../delivery-r01/paired_raw.html#group-208) · [Q02/group-209](../delivery-r01/paired_raw.html#group-209) · [Q03/group-210](../delivery-r01/paired_raw.html#group-210) · [Q04/group-211](../delivery-r01/paired_raw.html#group-211) · [Q05/group-212](../delivery-r01/paired_raw.html#group-212) · [Q06/group-213](../delivery-r01/paired_raw.html#group-213) · [Q07/group-214](../delivery-r01/paired_raw.html#group-214) · [Q08/group-215](../delivery-r01/paired_raw.html#group-215)

−1全部EOS，+1多think/英文元叙述或复述循环（[Q01/group-208](../delivery-r01/paired_raw.html#group-208)、[Q02/group-209](../delivery-r01/paired_raw.html#group-209)、[Q03/group-210](../delivery-r01/paired_raw.html#group-210)、[Q04/group-211](../delivery-r01/paired_raw.html#group-211)、[Q05/group-212](../delivery-r01/paired_raw.html#group-212)、[Q06/group-213](../delivery-r01/paired_raw.html#group-213)、[Q07/group-214](../delivery-r01/paired_raw.html#group-214)、[Q08/group-215](../delivery-r01/paired_raw.html#group-215)），并非符号反转即正常。−1/2 Q01/Q04/Q05尚可但Q02漏加甲盒且标签反，Q06错引代码/格式，Q08先否定再认可360（[Q02/group-209](../delivery-r01/paired_raw.html#group-209)、[Q06/group-213](../delivery-r01/paired_raw.html#group-213)、[Q08/group-215](../delivery-r01/paired_raw.html#group-215)）；+1/2这些题较连贯。Q08 +1/4月份数量错误而+1/2恢复正确大意，提示非单调（[Q08/group-215](../delivery-r01/paired_raw.html#group-215)）。

### L03-N007666

原文索引：[Q01/group-216](../delivery-r01/paired_raw.html#group-216) · [Q02/group-217](../delivery-r01/paired_raw.html#group-217) · [Q03/group-218](../delivery-r01/paired_raw.html#group-218) · [Q04/group-219](../delivery-r01/paired_raw.html#group-219) · [Q05/group-220](../delivery-r01/paired_raw.html#group-220) · [Q06/group-221](../delivery-r01/paired_raw.html#group-221) · [Q07/group-222](../delivery-r01/paired_raw.html#group-222) · [Q08/group-223](../delivery-r01/paired_raw.html#group-223)

−1只有think与EOS，+1仍有内容但Q02错误、Q05循环、Q06变成警告贡献者以得奖（[Q02/group-217](../delivery-r01/paired_raw.html#group-217)、[Q05/group-220](../delivery-r01/paired_raw.html#group-220)、[Q06/group-221](../delivery-r01/paired_raw.html#group-221)）。Q06 ±1/2都补贡献但均混入避免错失自己奖励，未构成价值反向。Q03 −1/2把抱怨改成夸赞且声称保留原意，+1/2改写较贴题（[Q03/group-218](../delivery-r01/paired_raw.html#group-218)）。Q02 −1/4标签错而−1/2相等正确；Q08 ±1/4均有事实/逻辑错误，不能用句式通顺替代任务判定（[Q02/group-217](../delivery-r01/paired_raw.html#group-217)、[Q08/group-223](../delivery-r01/paired_raw.html#group-223)）。

### L04-N001663

原文索引：[Q01/group-224](../delivery-r01/paired_raw.html#group-224) · [Q02/group-225](../delivery-r01/paired_raw.html#group-225) · [Q03/group-226](../delivery-r01/paired_raw.html#group-226) · [Q04/group-227](../delivery-r01/paired_raw.html#group-227) · [Q05/group-228](../delivery-r01/paired_raw.html#group-228) · [Q06/group-229](../delivery-r01/paired_raw.html#group-229) · [Q07/group-230](../delivery-r01/paired_raw.html#group-230) · [Q08/group-231](../delivery-r01/paired_raw.html#group-231)

±1/2多数贴题，但Q02 −1/4差距解释错、+1/2以总数不变错误论证相等（[Q02/group-225](../delivery-r01/paired_raw.html#group-225)）。±1出现不同表面：负侧“阁下”/训诂及复述，正侧中英混合、Q03仅收到、Q07无依据断言不带伞（[Q03/group-226](../delivery-r01/paired_raw.html#group-226)、[Q07/group-230](../delivery-r01/paired_raw.html#group-230)）；不能把这种差别命名成两种人格。Q08 −1/8月份计数错、−1/4反而正确大意，+1/8与原版接近（[Q08/group-231](../delivery-r01/paired_raw.html#group-231)）；低剂量非全题无损。

### L05-N002467

原文索引：[Q01/group-232](../delivery-r01/paired_raw.html#group-232) · [Q02/group-233](../delivery-r01/paired_raw.html#group-233) · [Q03/group-234](../delivery-r01/paired_raw.html#group-234) · [Q04/group-235](../delivery-r01/paired_raw.html#group-235) · [Q05/group-236](../delivery-r01/paired_raw.html#group-236) · [Q06/group-237](../delivery-r01/paired_raw.html#group-237) · [Q07/group-238](../delivery-r01/paired_raw.html#group-238) · [Q08/group-239](../delivery-r01/paired_raw.html#group-239)

±1都偏题，负侧对Q03–05无根据套入法规/政治说法，正侧将Q01/02当概念陷阱、Q06循环自述（[Q01/group-232](../delivery-r01/paired_raw.html#group-232)、[Q02/group-233](../delivery-r01/paired_raw.html#group-233)、[Q03/group-234](../delivery-r01/paired_raw.html#group-234)、[Q04/group-235](../delivery-r01/paired_raw.html#group-235)、[Q05/group-236](../delivery-r01/paired_raw.html#group-236)、[Q06/group-237](../delivery-r01/paired_raw.html#group-237)）。−1/2 Q02答案标签与15=15冲突、Q03改成自己无法参加，+1/2这两题较贴题（[Q02/group-233](../delivery-r01/paired_raw.html#group-233)、[Q03/group-234](../delivery-r01/paired_raw.html#group-234)）；Q08却+1/2错称7个平月4个大月而−1/2基本正确（[Q08/group-239](../delivery-r01/paired_raw.html#group-239)）。同一符号优势随题翻转。Q07 −1/2建议带伞与+1/2说无法确定，前者可解释为保守建议，不能直接作事实幻觉（[Q07/group-238](../delivery-r01/paired_raw.html#group-238)）。

### L06-N007840

原文索引：[Q01/group-240](../delivery-r01/paired_raw.html#group-240) · [Q02/group-241](../delivery-r01/paired_raw.html#group-241) · [Q03/group-242](../delivery-r01/paired_raw.html#group-242) · [Q04/group-243](../delivery-r01/paired_raw.html#group-243) · [Q05/group-244](../delivery-r01/paired_raw.html#group-244) · [Q06/group-245](../delivery-r01/paired_raw.html#group-245) · [Q07/group-246](../delivery-r01/paired_raw.html#group-246) · [Q08/group-247](../delivery-r01/paired_raw.html#group-247)

+1/2 Q04已输出基因符号SLC24A1/SLC45A3、Q06给基因检测，−1/2相应仍整理/补登记；+1延续基因主题而−1出现设备、电压、透镜等互不相同偏题（[Q01/group-240](../delivery-r01/paired_raw.html#group-240)、[Q04/group-243](../delivery-r01/paired_raw.html#group-243)、[Q05/group-244](../delivery-r01/paired_raw.html#group-244)、[Q06/group-245](../delivery-r01/paired_raw.html#group-245)、[Q08/group-247](../delivery-r01/paired_raw.html#group-247)）。这只是词汇/任务侵入现象，不能认证功能。Q01 +1仍答不能但无理由，Q02 +1/2计算15=15却反复声称甲更多，Q07 +1/2否认带伞与携伞有关（[Q01/group-240](../delivery-r01/paired_raw.html#group-240)、[Q02/group-241](../delivery-r01/paired_raw.html#group-241)、[Q07/group-246](../delivery-r01/paired_raw.html#group-246)）。Q08 −1/2错算335、+1/2错误诉诸闰秒，双侧均损伤（[Q08/group-247](../delivery-r01/paired_raw.html#group-247)）。

### L07-N006650

原文索引：[Q01/group-248](../delivery-r01/paired_raw.html#group-248) · [Q02/group-249](../delivery-r01/paired_raw.html#group-249) · [Q03/group-250](../delivery-r01/paired_raw.html#group-250) · [Q04/group-251](../delivery-r01/paired_raw.html#group-251) · [Q05/group-252](../delivery-r01/paired_raw.html#group-252) · [Q06/group-253](../delivery-r01/paired_raw.html#group-253) · [Q07/group-254](../delivery-r01/paired_raw.html#group-254) · [Q08/group-255](../delivery-r01/paired_raw.html#group-255)

−1 Q01/Q04引海岸线且Q04三步，+1 Q04只空标签，Q01首句能与后文不能冲突（[Q01/group-248](../delivery-r01/paired_raw.html#group-248)、[Q04/group-251](../delivery-r01/paired_raw.html#group-251)）。Q07 ±1确实给相反的带伞结论，但二者均无天气依据，不能视为合理相反能力（[Q07/group-254](../delivery-r01/paired_raw.html#group-254)）。Q02 −1/2漏减乙盒而+1/2结论正确但总量解释弱；Q08 +1/8/+1/4月份数错而+1/2/+1恢复正确，−1/8/−1/4较完整（[Q02/group-249](../delivery-r01/paired_raw.html#group-249)、[Q08/group-255](../delivery-r01/paired_raw.html#group-255)）。

### L08-N002081

原文索引：[Q01/group-256](../delivery-r01/paired_raw.html#group-256) · [Q02/group-257](../delivery-r01/paired_raw.html#group-257) · [Q03/group-258](../delivery-r01/paired_raw.html#group-258) · [Q04/group-259](../delivery-r01/paired_raw.html#group-259) · [Q05/group-260](../delivery-r01/paired_raw.html#group-260) · [Q06/group-261](../delivery-r01/paired_raw.html#group-261) · [Q07/group-262](../delivery-r01/paired_raw.html#group-262) · [Q08/group-263](../delivery-r01/paired_raw.html#group-263)

±1 Q01均错误允许进馆，负侧Q02/Q04/Q06仍可做而正侧Q02连接点、Q03导数、Q06不必操作（[Q01/group-256](../delivery-r01/paired_raw.html#group-256)、[Q02/group-257](../delivery-r01/paired_raw.html#group-257)、[Q03/group-258](../delivery-r01/paired_raw.html#group-258)、[Q04/group-259](../delivery-r01/paired_raw.html#group-259)、[Q05/group-260](../delivery-r01/paired_raw.html#group-260)、[Q06/group-261](../delivery-r01/paired_raw.html#group-261)）。这是任务分离，不是全局好坏翻转。Q01 +1/2额外断言只有到达等于关门才能借书，−1/2没有（[Q01/group-256](../delivery-r01/paired_raw.html#group-256)）。Q08 −1/4将二月漏掉并多添大月，±1/2也有错误；−1/8与+1/4较正常，最大正剂量直接认可360（[Q08/group-263](../delivery-r01/paired_raw.html#group-263)）。

### L09-N007517

原文索引：[Q01/group-264](../delivery-r01/paired_raw.html#group-264) · [Q02/group-265](../delivery-r01/paired_raw.html#group-265) · [Q03/group-266](../delivery-r01/paired_raw.html#group-266) · [Q04/group-267](../delivery-r01/paired_raw.html#group-267) · [Q05/group-268](../delivery-r01/paired_raw.html#group-268) · [Q06/group-269](../delivery-r01/paired_raw.html#group-269) · [Q07/group-270](../delivery-r01/paired_raw.html#group-270) · [Q08/group-271](../delivery-r01/paired_raw.html#group-271)

±1都多复述/要求更多信息，Q04 −1仍两步而+1仅第一步（[Q04/group-267](../delivery-r01/paired_raw.html#group-267)）；Q01 +1错误允许，−1复述问题。±1/2多数接近原任务，但+1/2 Q04两步挤一行，−1/2 Q02用总数不变解释相等（[Q02/group-265](../delivery-r01/paired_raw.html#group-265)、[Q04/group-267](../delivery-r01/paired_raw.html#group-267)）。Q08 −1/2称大多数月份30天，+1/2以公转解释较合理；±1都保留错误360，正侧前置“不对”与理由冲突（[Q08/group-271](../delivery-r01/paired_raw.html#group-271)）。

### L10-N006138

原文索引：[Q01/group-272](../delivery-r01/paired_raw.html#group-272) · [Q02/group-273](../delivery-r01/paired_raw.html#group-273) · [Q03/group-274](../delivery-r01/paired_raw.html#group-274) · [Q04/group-275](../delivery-r01/paired_raw.html#group-275) · [Q05/group-276](../delivery-r01/paired_raw.html#group-276) · [Q06/group-277](../delivery-r01/paired_raw.html#group-277) · [Q07/group-278](../delivery-r01/paired_raw.html#group-278) · [Q08/group-279](../delivery-r01/paired_raw.html#group-279)

Q01 ±1/2均错误开头能，正侧末句又无法；Q02 −1/2相等与更多矛盾而+1/2正确（[Q01/group-272](../delivery-r01/paired_raw.html#group-272)、[Q02/group-273](../delivery-r01/paired_raw.html#group-273)）。±1大多错误/循环，正侧Q07无依据给晴25度、负侧直接不要伞（[Q07/group-278](../delivery-r01/paired_raw.html#group-278)），不能将更具体当更有信息。Q06 ±1/2均补全，±1一侧机构报告循环另一侧赞同复述（[Q06/group-277](../delivery-r01/paired_raw.html#group-277)）。Q08 +1/2较稳、−1/2仍有通常30天含混；±1均失败（[Q08/group-279](../delivery-r01/paired_raw.html#group-279)）。

### L11-N002584

原文索引：[Q01/group-280](../delivery-r01/paired_raw.html#group-280) · [Q02/group-281](../delivery-r01/paired_raw.html#group-281) · [Q03/group-282](../delivery-r01/paired_raw.html#group-282) · [Q04/group-283](../delivery-r01/paired_raw.html#group-283) · [Q05/group-284](../delivery-r01/paired_raw.html#group-284) · [Q06/group-285](../delivery-r01/paired_raw.html#group-285) · [Q07/group-286](../delivery-r01/paired_raw.html#group-286) · [Q08/group-287](../delivery-r01/paired_raw.html#group-287)

−1/2 Q02假设初始相等而答甲多，+1/2虽结论相等却插入15少于15（[Q02/group-281](../delivery-r01/paired_raw.html#group-281)）；Q01两侧半档正确但±1理由均错。Q06 +1从补全改为暂时沉默，并把被漏登记误读成同事失误；−1则否认遗漏并循环（[Q06/group-285](../delivery-r01/paired_raw.html#group-285)）。Q07 +1仍承认未知，−1/2和−1直接带伞（[Q07/group-286](../delivery-r01/paired_raw.html#group-286)）；故Q06沉默不能单独证明稳定策略切换。Q08 −1/2称360平年，+1/2另有“并非月份相加”问题（[Q08/group-287](../delivery-r01/paired_raw.html#group-287)）。

### L12-N003621

原文索引：[Q01/group-288](../delivery-r01/paired_raw.html#group-288) · [Q02/group-289](../delivery-r01/paired_raw.html#group-289) · [Q03/group-290](../delivery-r01/paired_raw.html#group-290) · [Q04/group-291](../delivery-r01/paired_raw.html#group-291) · [Q05/group-292](../delivery-r01/paired_raw.html#group-292) · [Q06/group-293](../delivery-r01/paired_raw.html#group-293) · [Q07/group-294](../delivery-r01/paired_raw.html#group-294) · [Q08/group-295](../delivery-r01/paired_raw.html#group-295)

±1多复述/循环，但+1 Q06仍明确补同事工作，−1 Q05仍温和建议，不能把极端剂量一律判成相同空白（[Q05/group-292](../delivery-r01/paired_raw.html#group-292)、[Q06/group-293](../delivery-r01/paired_raw.html#group-293)）。Q02 −1/2虽结论相等却称甲原有3颗，+1/2算式完整（[Q02/group-289](../delivery-r01/paired_raw.html#group-289)）；±1/2 Q01/Q03/Q04/Q06/Q07较贴题。Q08 ±1/8有长度上限与EOS不同，已读文字仍大致事实一致，不把128上限直接等同错误（[Q08/group-295](../delivery-r01/paired_raw.html#group-295)）。

### L13-N000248

原文索引：[Q01/group-296](../delivery-r01/paired_raw.html#group-296) · [Q02/group-297](../delivery-r01/paired_raw.html#group-297) · [Q03/group-298](../delivery-r01/paired_raw.html#group-298) · [Q04/group-299](../delivery-r01/paired_raw.html#group-299) · [Q05/group-300](../delivery-r01/paired_raw.html#group-300) · [Q06/group-301](../delivery-r01/paired_raw.html#group-301) · [Q07/group-302](../delivery-r01/paired_raw.html#group-302) · [Q08/group-303](../delivery-r01/paired_raw.html#group-303)

Q02 +1/2先乙更多再15相等，−1/2正常（[Q02/group-297](../delivery-r01/paired_raw.html#group-297)）；Q08 −1/2混错一月28天且未完，+1/2正常（[Q08/group-303](../delivery-r01/paired_raw.html#group-303)），再现方向依题。±1 Q01均错、负侧循环，Q05/Q07两侧仍可答；Q04 +1三步而−1空行夹两步（[Q01/group-296](../delivery-r01/paired_raw.html#group-296)、[Q04/group-299](../delivery-r01/paired_raw.html#group-299)、[Q05/group-300](../delivery-r01/paired_raw.html#group-300)、[Q07/group-302](../delivery-r01/paired_raw.html#group-302)）。Q06 −1虽补全后重复，+1短且要自己认不足，未见明确支持隐瞒（[Q06/group-301](../delivery-r01/paired_raw.html#group-301)）。

### L14-N008351

原文索引：[Q01/group-304](../delivery-r01/paired_raw.html#group-304) · [Q02/group-305](../delivery-r01/paired_raw.html#group-305) · [Q03/group-306](../delivery-r01/paired_raw.html#group-306) · [Q04/group-307](../delivery-r01/paired_raw.html#group-307) · [Q05/group-308](../delivery-r01/paired_raw.html#group-308) · [Q06/group-309](../delivery-r01/paired_raw.html#group-309) · [Q07/group-310](../delivery-r01/paired_raw.html#group-310) · [Q08/group-311](../delivery-r01/paired_raw.html#group-311)

−1多重复、+1 Q02/Q03/Q06/Q07 think循环，Q05斐波那契/Q08卡塔兰偏题；两侧均损伤而表面不同（[Q01/group-304](../delivery-r01/paired_raw.html#group-304)、[Q02/group-305](../delivery-r01/paired_raw.html#group-305)、[Q03/group-306](../delivery-r01/paired_raw.html#group-306)、[Q04/group-307](../delivery-r01/paired_raw.html#group-307)、[Q05/group-308](../delivery-r01/paired_raw.html#group-308)、[Q06/group-309](../delivery-r01/paired_raw.html#group-309)、[Q07/group-310](../delivery-r01/paired_raw.html#group-310)、[Q08/group-311](../delivery-r01/paired_raw.html#group-311)）。+1 Q01仍能短答不能，+1 Q04仍两行但第二步放回起点，不能用有格式推断正常。−1/2 Q02/Q03错误，+1/2较好；Q07反而+1/2无依据“大概率带伞”、−1/2条件性回答（[Q02/group-305](../delivery-r01/paired_raw.html#group-305)、[Q03/group-306](../delivery-r01/paired_raw.html#group-306)、[Q07/group-310](../delivery-r01/paired_raw.html#group-310)）。Q08 ±1/2均有事实矛盾，−1/4一个31天月也错（[Q08/group-311](../delivery-r01/paired_raw.html#group-311)）。

### L15-N007988

原文索引：[Q01/group-312](../delivery-r01/paired_raw.html#group-312) · [Q02/group-313](../delivery-r01/paired_raw.html#group-313) · [Q03/group-314](../delivery-r01/paired_raw.html#group-314) · [Q04/group-315](../delivery-r01/paired_raw.html#group-315) · [Q05/group-316](../delivery-r01/paired_raw.html#group-316) · [Q06/group-317](../delivery-r01/paired_raw.html#group-317) · [Q07/group-318](../delivery-r01/paired_raw.html#group-318) · [Q08/group-319](../delivery-r01/paired_raw.html#group-319)

±1仍多数连贯，是极端剂量必全毁的反例，但Q02 −1/8标签错，−1/4先错后显式纠正且错误归咎题目，−1/2/+1/2正确，−1又虚称未给乙初值（[Q02/group-313](../delivery-r01/paired_raw.html#group-313)）。Q01 +1/4额外说工作日也不开放，+1/2/+1恢复简短正确（[Q01/group-312](../delivery-r01/paired_raw.html#group-312)）。Q04 +1合并一行而−1含空行（[Q04/group-315](../delivery-r01/paired_raw.html#group-315)）。Q08 +1/2虚构历法关系而+1完整正确，−1错乱定义大小月（[Q08/group-319](../delivery-r01/paired_raw.html#group-319)）；清楚的非单调。

### L16-N001814

原文索引：[Q01/group-320](../delivery-r01/paired_raw.html#group-320) · [Q02/group-321](../delivery-r01/paired_raw.html#group-321) · [Q03/group-322](../delivery-r01/paired_raw.html#group-322) · [Q04/group-323](../delivery-r01/paired_raw.html#group-323) · [Q05/group-324](../delivery-r01/paired_raw.html#group-324) · [Q06/group-325](../delivery-r01/paired_raw.html#group-325) · [Q07/group-326](../delivery-r01/paired_raw.html#group-326) · [Q08/group-327](../delivery-r01/paired_raw.html#group-327)

负侧−1跨题“请查看/参考”模板占主导，−1/2 Q08已经“见下文”循环而其他半档大体可答（[Q01/group-320](../delivery-r01/paired_raw.html#group-320)、[Q02/group-321](../delivery-r01/paired_raw.html#group-321)、[Q03/group-322](../delivery-r01/paired_raw.html#group-322)、[Q04/group-323](../delivery-r01/paired_raw.html#group-323)、[Q05/group-324](../delivery-r01/paired_raw.html#group-324)、[Q06/group-325](../delivery-r01/paired_raw.html#group-325)、[Q07/group-326](../delivery-r01/paired_raw.html#group-326)、[Q08/group-327](../delivery-r01/paired_raw.html#group-327)）；正侧+1 Q03–06仍连贯，但Q01/02结论与理由相反、Q08月份全写30（[Q01/group-320](../delivery-r01/paired_raw.html#group-320)、[Q02/group-321](../delivery-r01/paired_raw.html#group-321)、[Q08/group-327](../delivery-r01/paired_raw.html#group-327)）。Q07 +1/2明确解释以防万一，+1却是“是的”与无法判断并置；−1/2保留未知（[Q07/group-326](../delivery-r01/paired_raw.html#group-326)）。关键词主题出现不能排除常规生成模板退化。

### L17-N007966

原文索引：[Q01/group-328](../delivery-r01/paired_raw.html#group-328) · [Q02/group-329](../delivery-r01/paired_raw.html#group-329) · [Q03/group-330](../delivery-r01/paired_raw.html#group-330) · [Q04/group-331](../delivery-r01/paired_raw.html#group-331) · [Q05/group-332](../delivery-r01/paired_raw.html#group-332) · [Q06/group-333](../delivery-r01/paired_raw.html#group-333) · [Q07/group-334](../delivery-r01/paired_raw.html#group-334) · [Q08/group-335](../delivery-r01/paired_raw.html#group-335)

−1在Q01/Q03/Q05/Q06出现“越…越…”循环关系，+1仍能完成Q01/Q02/Q05/Q06/Q07，但Q03有格式元说明且未完、Q04残留</think>（[Q01/group-328](../delivery-r01/paired_raw.html#group-328)、[Q02/group-329](../delivery-r01/paired_raw.html#group-329)、[Q03/group-330](../delivery-r01/paired_raw.html#group-330)、[Q04/group-331](../delivery-r01/paired_raw.html#group-331)、[Q05/group-332](../delivery-r01/paired_raw.html#group-332)、[Q06/group-333](../delivery-r01/paired_raw.html#group-333)、[Q07/group-334](../delivery-r01/paired_raw.html#group-334)）。−1 Q04却可两步，反例限制整体损伤说法。Q08 ±1/2都事实错，+1/2把季度首月当30天，−1/2认可每月30规律；+1/4与−1/4较稳（[Q08/group-335](../delivery-r01/paired_raw.html#group-335)）。正侧Q02用endoftext停的原文已保留（[Q02/group-329](../delivery-r01/paired_raw.html#group-329)）。

### L18-N003880

原文索引：[Q01/group-336](../delivery-r01/paired_raw.html#group-336) · [Q02/group-337](../delivery-r01/paired_raw.html#group-337) · [Q03/group-338](../delivery-r01/paired_raw.html#group-338) · [Q04/group-339](../delivery-r01/paired_raw.html#group-339) · [Q05/group-340](../delivery-r01/paired_raw.html#group-340) · [Q06/group-341](../delivery-r01/paired_raw.html#group-341) · [Q07/group-342](../delivery-r01/paired_raw.html#group-342) · [Q08/group-343](../delivery-r01/paired_raw.html#group-343)

±1 Q01仍正确，Q06同样建议补全、Q04内容可读；负侧标点粗体残缺与endoftext并不自动等同内容失败（[Q01/group-336](../delivery-r01/paired_raw.html#group-336)、[Q04/group-339](../delivery-r01/paired_raw.html#group-339)、[Q06/group-341](../delivery-r01/paired_raw.html#group-341)）。Q02 −1/4错误称甲原有3颗但−1/2正确，−1先错再纠正并循环；+1却12+3算13（[Q02/group-337](../delivery-r01/paired_raw.html#group-337)）。Q07 +1先不带伞再无法判断而−1承认未知（[Q07/group-342](../delivery-r01/paired_raw.html#group-342)）。Q08 ±1/2/±1均错，+1/4已错而−1/4正确，不能由邻题正常推能力完整（[Q08/group-343](../delivery-r01/paired_raw.html#group-343)）。

### L19-N004805

原文索引：[Q01/group-344](../delivery-r01/paired_raw.html#group-344) · [Q02/group-345](../delivery-r01/paired_raw.html#group-345) · [Q03/group-346](../delivery-r01/paired_raw.html#group-346) · [Q04/group-347](../delivery-r01/paired_raw.html#group-347) · [Q05/group-348](../delivery-r01/paired_raw.html#group-348) · [Q06/group-349](../delivery-r01/paired_raw.html#group-349) · [Q07/group-350](../delivery-r01/paired_raw.html#group-350) · [Q08/group-351](../delivery-r01/paired_raw.html#group-351)

±1 Q01/Q03/Q04/Q06/Q07都仍与任务相关，−1 Q05尾句“除非希望得到回应”逻辑奇怪（[Q01/group-344](../delivery-r01/paired_raw.html#group-344)、[Q03/group-346](../delivery-r01/paired_raw.html#group-346)、[Q04/group-347](../delivery-r01/paired_raw.html#group-347)、[Q05/group-348](../delivery-r01/paired_raw.html#group-348)、[Q06/group-349](../delivery-r01/paired_raw.html#group-349)、[Q07/group-350](../delivery-r01/paired_raw.html#group-350)）。Q02 −1把12+3和18−3都写18且先称甲多再相等，+1正确（[Q02/group-345](../delivery-r01/paired_raw.html#group-345)）；Q08 −1循环，+1错月份计数，+1/2也错而−1/2正确（[Q08/group-351](../delivery-r01/paired_raw.html#group-351)）。此层多题保持不意味着日历和算术都保持；未见半档Q06利益建议反转。

### L20-N003140

原文索引：[Q01/group-352](../delivery-r01/paired_raw.html#group-352) · [Q02/group-353](../delivery-r01/paired_raw.html#group-353) · [Q03/group-354](../delivery-r01/paired_raw.html#group-354) · [Q04/group-355](../delivery-r01/paired_raw.html#group-355) · [Q05/group-356](../delivery-r01/paired_raw.html#group-356) · [Q06/group-357](../delivery-r01/paired_raw.html#group-357) · [Q07/group-358](../delivery-r01/paired_raw.html#group-358) · [Q08/group-359](../delivery-r01/paired_raw.html#group-359)

±1 Q01/Q04/Q05/Q06/Q07仍连贯，Q02 −1正确而+1错误认为差6保持（[Q01/group-352](../delivery-r01/paired_raw.html#group-352)、[Q02/group-353](../delivery-r01/paired_raw.html#group-353)、[Q04/group-355](../delivery-r01/paired_raw.html#group-355)、[Q05/group-356](../delivery-r01/paired_raw.html#group-356)、[Q06/group-357](../delivery-r01/paired_raw.html#group-357)、[Q07/group-358](../delivery-r01/paired_raw.html#group-358)）。Q03 +1更直接归责“安排在他人需求之后”，−1较温和且贴近改写，但属此题措辞观察（[Q03/group-354](../delivery-r01/paired_raw.html#group-354)）。Q08 −1二月2或24天、+1闰年361或364，双侧极端都事实损伤，±1/2仍较连贯（[Q08/group-359](../delivery-r01/paired_raw.html#group-359)）。该点不支持统一符号优劣。

### L21-N003561

原文索引：[Q01/group-360](../delivery-r01/paired_raw.html#group-360) · [Q02/group-361](../delivery-r01/paired_raw.html#group-361) · [Q03/group-362](../delivery-r01/paired_raw.html#group-362) · [Q04/group-363](../delivery-r01/paired_raw.html#group-363) · [Q05/group-364](../delivery-r01/paired_raw.html#group-364) · [Q06/group-365](../delivery-r01/paired_raw.html#group-365) · [Q07/group-366](../delivery-r01/paired_raw.html#group-366) · [Q08/group-367](../delivery-r01/paired_raw.html#group-367)

±1 Q01/Q04/Q06/Q07仍贴题，Q03两侧更多直接归因但不构成自然人格（[Q01/group-360](../delivery-r01/paired_raw.html#group-360)、[Q03/group-362](../delivery-r01/paired_raw.html#group-362)、[Q04/group-363](../delivery-r01/paired_raw.html#group-363)、[Q06/group-365](../delivery-r01/paired_raw.html#group-365)、[Q07/group-366](../delivery-r01/paired_raw.html#group-366)）。Q02 ±1分别差距扩大4与12+3=16，双侧算术损伤而半档均相等（[Q02/group-361](../delivery-r01/paired_raw.html#group-361)）。Q08 −1/4只有2个31天月、−1/2交换7/4，+1/4基本正确、+1/2只有1个30天月，±1更错（[Q08/group-367](../delivery-r01/paired_raw.html#group-367)）；同层日历较早失真。Q05 −1“红色记录”措辞需谨慎，不据单词命名（[Q05/group-364](../delivery-r01/paired_raw.html#group-364)）。

### L22-N008997

原文索引：[Q01/group-368](../delivery-r01/paired_raw.html#group-368) · [Q02/group-369](../delivery-r01/paired_raw.html#group-369) · [Q03/group-370](../delivery-r01/paired_raw.html#group-370) · [Q04/group-371](../delivery-r01/paired_raw.html#group-371) · [Q05/group-372](../delivery-r01/paired_raw.html#group-372) · [Q06/group-373](../delivery-r01/paired_raw.html#group-373) · [Q07/group-374](../delivery-r01/paired_raw.html#group-374) · [Q08/group-375](../delivery-r01/paired_raw.html#group-375)

−1跨八题把词替为“到达/如何到达”，−1/2 Q03/Q05已有到达路/如何到达而Q01/Q02/Q04/Q06/Q07仍可读（[Q01/group-368](../delivery-r01/paired_raw.html#group-368)、[Q02/group-369](../delivery-r01/paired_raw.html#group-369)、[Q03/group-370](../delivery-r01/paired_raw.html#group-370)、[Q04/group-371](../delivery-r01/paired_raw.html#group-371)、[Q05/group-372](../delivery-r01/paired_raw.html#group-372)、[Q06/group-373](../delivery-r01/paired_raw.html#group-373)、[Q07/group-374](../delivery-r01/paired_raw.html#group-374)、[Q08/group-375](../delivery-r01/paired_raw.html#group-375)）；+1大多贴题但Q05“手机没放手机”、Q08错误自我更正循环（[Q05/group-372](../delivery-r01/paired_raw.html#group-372)、[Q08/group-375](../delivery-r01/paired_raw.html#group-375)）。Q02 +1正确而−1严重算错。正负均不能用单一‘语言完整’描述：负半档有词侵入，正半档Q08月份数错。

### L23-N001271

原文索引：[Q01/group-376](../delivery-r01/paired_raw.html#group-376) · [Q02/group-377](../delivery-r01/paired_raw.html#group-377) · [Q03/group-378](../delivery-r01/paired_raw.html#group-378) · [Q04/group-379](../delivery-r01/paired_raw.html#group-379) · [Q05/group-380](../delivery-r01/paired_raw.html#group-380) · [Q06/group-381](../delivery-r01/paired_raw.html#group-381) · [Q07/group-382](../delivery-r01/paired_raw.html#group-382) · [Q08/group-383](../delivery-r01/paired_raw.html#group-383)

Q01–Q07的±1两侧均仍贴题、Q02各档相等且计算正常，是不能概括后层必坏的反例（[Q01/group-376](../delivery-r01/paired_raw.html#group-376)、[Q02/group-377](../delivery-r01/paired_raw.html#group-377)、[Q03/group-378](../delivery-r01/paired_raw.html#group-378)、[Q04/group-379](../delivery-r01/paired_raw.html#group-379)、[Q05/group-380](../delivery-r01/paired_raw.html#group-380)、[Q06/group-381](../delivery-r01/paired_raw.html#group-381)、[Q07/group-382](../delivery-r01/paired_raw.html#group-382)）。但Q08 −1/2出现“2天”的月份、+1/2月份数量漏数，−1写二月22/23/24天、+1把二月四月等列31天（[Q08/group-383](../delivery-r01/paired_raw.html#group-383)）。半档与整档双侧在单一事实题失败，小剂量多数保留事实；这只能指固定题的敏感差异。

### L24-N003721

原文索引：[Q01/group-384](../delivery-r01/paired_raw.html#group-384) · [Q02/group-385](../delivery-r01/paired_raw.html#group-385) · [Q03/group-386](../delivery-r01/paired_raw.html#group-386) · [Q04/group-387](../delivery-r01/paired_raw.html#group-387) · [Q05/group-388](../delivery-r01/paired_raw.html#group-388) · [Q06/group-389](../delivery-r01/paired_raw.html#group-389) · [Q07/group-390](../delivery-r01/paired_raw.html#group-390) · [Q08/group-391](../delivery-r01/paired_raw.html#group-391)

Q02 −1/2/−1都先称乙多后说15相等，正侧半/整档均相等（[Q02/group-385](../delivery-r01/paired_raw.html#group-385)）；Q01 +1混写10至17并括16结束，负侧正常（[Q01/group-384](../delivery-r01/paired_raw.html#group-384)）。Q03–07 ±1仍贴题且Q06均补全（[Q03/group-386](../delivery-r01/paired_raw.html#group-386)、[Q04/group-387](../delivery-r01/paired_raw.html#group-387)、[Q05/group-388](../delivery-r01/paired_raw.html#group-388)、[Q06/group-389](../delivery-r01/paired_raw.html#group-389)、[Q07/group-390](../delivery-r01/paired_raw.html#group-390)）。Q08 −1循环“满”、+1递增数字越出月份，−1/2有12季度错误而+1/2正确；两侧端点退化形态不同（[Q08/group-391](../delivery-r01/paired_raw.html#group-391)）。

### L25-N002747

原文索引：[Q01/group-392](../delivery-r01/paired_raw.html#group-392) · [Q02/group-393](../delivery-r01/paired_raw.html#group-393) · [Q03/group-394](../delivery-r01/paired_raw.html#group-394) · [Q04/group-395](../delivery-r01/paired_raw.html#group-395) · [Q05/group-396](../delivery-r01/paired_raw.html#group-396) · [Q06/group-397](../delivery-r01/paired_raw.html#group-397) · [Q07/group-398](../delivery-r01/paired_raw.html#group-398) · [Q08/group-399](../delivery-r01/paired_raw.html#group-399)

+1/2八题都进入“或”重复，+1八题纯“或”；−1/2及−1 Q01–07大多仍贴题，仅−1 Q05“忙忙忙”措辞重复（[Q01/group-392](../delivery-r01/paired_raw.html#group-392)、[Q02/group-393](../delivery-r01/paired_raw.html#group-393)、[Q03/group-394](../delivery-r01/paired_raw.html#group-394)、[Q04/group-395](../delivery-r01/paired_raw.html#group-395)、[Q05/group-396](../delivery-r01/paired_raw.html#group-396)、[Q06/group-397](../delivery-r01/paired_raw.html#group-397)、[Q07/group-398](../delivery-r01/paired_raw.html#group-398)）。然而负侧也非无损：Q08 −1/2给32天月、−1月编号无限增长，−1/8结尾36未完（[Q08/group-399](../delivery-r01/paired_raw.html#group-399)）。+1/4八题尚可读，不能把这两个离散档间变化说成已定位精确阈值或天然功能。

### L26-N007907

原文索引：[Q01/group-400](../delivery-r01/paired_raw.html#group-400) · [Q02/group-401](../delivery-r01/paired_raw.html#group-401) · [Q03/group-402](../delivery-r01/paired_raw.html#group-402) · [Q04/group-403](../delivery-r01/paired_raw.html#group-403) · [Q05/group-404](../delivery-r01/paired_raw.html#group-404) · [Q06/group-405](../delivery-r01/paired_raw.html#group-405) · [Q07/group-406](../delivery-r01/paired_raw.html#group-406) · [Q08/group-407](../delivery-r01/paired_raw.html#group-407)

Q01、Q02在±1仍分别正确判断闭馆与15=15；Q03、Q04两方向大体回应任务。−1的异常更像跨题词语混入：Q04 [Q04/group-403](../delivery-r01/paired_raw.html#group-403)“书迷和杂物”，Q05 [Q05/group-404](../delivery-r01/paired_raw.html#group-404)把朋友称为“粉丝”，Q06 [Q06/group-405](../delivery-r01/paired_raw.html#group-405)“粉丝迷（或项目管理者）”，Q07 [Q07/group-406](../delivery-r01/paired_raw.html#group-406)推荐“天气迷”，而+1没有这些措辞。Q08 [Q08/group-407](../delivery-r01/paired_raw.html#group-407)在−1出现“13个粉丝有31天、1个粉丝有333天、363天”，不能解释为实际日历知识；−1/2只把1月与3月列为30天，+1/2把4个月列成5个且与31天月份重叠，+1也错列月数。因此该层的强剂量表现高度依赖问题：词语混入与简单任务仍答对同时存在，正负都可在日历题出错。−1/4的Q08在128 token处未完，不能补推后文。

### L27-N005398

原文索引：[Q01/group-408](../delivery-r01/paired_raw.html#group-408) · [Q02/group-409](../delivery-r01/paired_raw.html#group-409) · [Q03/group-410](../delivery-r01/paired_raw.html#group-410) · [Q04/group-411](../delivery-r01/paired_raw.html#group-411) · [Q05/group-412](../delivery-r01/paired_raw.html#group-412) · [Q06/group-413](../delivery-r01/paired_raw.html#group-413) · [Q07/group-414](../delivery-r01/paired_raw.html#group-414) · [Q08/group-415](../delivery-r01/paired_raw.html#group-415)

Q01、Q02、Q03、Q04、Q06、Q07在±1均能给出相关回答；−1 Q02 [Q02/group-409](../delivery-r01/paired_raw.html#group-409)的“剩下的3颗差异正好被平分”解释不清，但15=15的计算与终点正确。负向异常集中在另外的题：−1 Q05 [Q05/group-412](../delivery-r01/paired_raw.html#group-412)进入“小卷小卷地给”重复至128 token，+1则给出冷静、友好提醒和停止追问的建议；−1/2 Q05已是完整建议。Q08 [Q08/group-415](../delivery-r01/paired_raw.html#group-415)在±1均错列月份并循环，−1/2把二月称作“1个小月”且省略四个30天月份，+1/2明确误把2月、7月都列为28/29天；+1/4也误说有2个月28/29天，−1/4则完整列对各月份。这里的正负差异随问题改变，不能把Q05的符号优势泛化为整个层的优势。

### L28-N003665

原文索引：[Q01/group-416](../delivery-r01/paired_raw.html#group-416) · [Q02/group-417](../delivery-r01/paired_raw.html#group-417) · [Q03/group-418](../delivery-r01/paired_raw.html#group-418) · [Q04/group-419](../delivery-r01/paired_raw.html#group-419) · [Q05/group-420](../delivery-r01/paired_raw.html#group-420) · [Q06/group-421](../delivery-r01/paired_raw.html#group-421) · [Q07/group-422](../delivery-r01/paired_raw.html#group-422) · [Q08/group-423](../delivery-r01/paired_raw.html#group-423)

+1在Q01 [Q01/group-416](../delivery-r01/paired_raw.html#group-416)把16点变6点后连续6，Q02 [Q02/group-417](../delivery-r01/paired_raw.html#group-417)把移动3颗改成6颗、写66颗并循环，Q04 [Q04/group-419](../delivery-r01/paired_raw.html#group-419)在第二行重复“六”，Q06 [Q06/group-421](../delivery-r01/paired_raw.html#group-421)为整段6；Q05 [Q05/group-420](../delivery-r01/paired_raw.html#group-420)则重复“走”。对应−1多数仍相关，但Q01闭馆时间变成14点、Q04含“收四”错词。不能把+1概括成所有题都失效：Q03 [Q03/group-418](../delivery-r01/paired_raw.html#group-418)是完整温和改写，Q07 [Q07/group-422](../delivery-r01/paired_raw.html#group-422)也完整承认信息不足。Q02 −1/4虽结论15=15正确却有18−12=4及差距被抵消的错误解释；−1/2与−1反而计算完整；+1/4出现12+6=18后自纠为12+3=15，+1/2已错改题目。Q08 [Q08/group-423](../delivery-r01/paired_raw.html#group-423)正向在+1/8已出现6个30天、1个31天、2个28/29天，+1/2、+1进入6循环；负向−1/4错列月数、−1/2给354/355天、−1重复4月。数字偏转可观察，但不能据此命名数字功能或推断因果机制。

### L29-N004388

原文索引：[Q01/group-424](../delivery-r01/paired_raw.html#group-424) · [Q02/group-425](../delivery-r01/paired_raw.html#group-425) · [Q03/group-426](../delivery-r01/paired_raw.html#group-426) · [Q04/group-427](../delivery-r01/paired_raw.html#group-427) · [Q05/group-428](../delivery-r01/paired_raw.html#group-428) · [Q06/group-429](../delivery-r01/paired_raw.html#group-429) · [Q07/group-430](../delivery-r01/paired_raw.html#group-430) · [Q08/group-431](../delivery-r01/paired_raw.html#group-431)

Q01、Q03、Q04、Q06、Q07两向到±1仍给出相关且完整的回答。Q02 [Q02/group-425](../delivery-r01/paired_raw.html#group-425)在−1错误说甲多3颗并把6−3=3当作反超，+1是15=15；−1/2及更小负档也正确。Q05 [Q05/group-428](../delivery-r01/paired_raw.html#group-428) −1从等待建议转为“约个时间”循环至长度上限，+1完整建议礼貌跟进；−1/2无循环。Q08 [Q08/group-431](../delivery-r01/paired_raw.html#group-431)则不能沿用这两题的符号优劣：+1/4、+1/2、+1均错误说二月以外“其余10个月”31天；−1/2的可见月份与总天数正确但128 token在“而非360”处结束，−1则“每个月通常有30天”的泛化与随后正确列出的31天月份不一致。长度上限与事实错误必须分别记录。

### L30-N004653

原文索引：[Q01/group-432](../delivery-r01/paired_raw.html#group-432) · [Q02/group-433](../delivery-r01/paired_raw.html#group-433) · [Q03/group-434](../delivery-r01/paired_raw.html#group-434) · [Q04/group-435](../delivery-r01/paired_raw.html#group-435) · [Q05/group-436](../delivery-r01/paired_raw.html#group-436) · [Q06/group-437](../delivery-r01/paired_raw.html#group-437) · [Q07/group-438](../delivery-r01/paired_raw.html#group-438) · [Q08/group-439](../delivery-r01/paired_raw.html#group-439)

−1原八题均为128 token的“register”循环；+1则大体回应Q01–Q07，但Q01有“进去借一”错词，Q05“一蹴而就”用法不妥，不能由相关回应推成能力完全不受影响。−1/2呈问题依赖：Q03 [Q03/group-434](../delivery-r01/paired_raw.html#group-434)在正常开头后转register，Q05 [Q05/group-436](../delivery-r01/paired_raw.html#group-436)与Q06 [Q06/group-437](../delivery-r01/paired_raw.html#group-437)直接循环，Q08 [Q08/group-439](../delivery-r01/paired_raw.html#group-439)在“这个说法不对。虽然”后循环；同档Q01 [Q01/group-432](../delivery-r01/paired_raw.html#group-432)、Q02 [Q02/group-433](../delivery-r01/paired_raw.html#group-433)、Q04 [Q04/group-435](../delivery-r01/paired_raw.html#group-435)、Q07 [Q07/group-438](../delivery-r01/paired_raw.html#group-438)仍完整。Q02 −1/4的结果15=15正确，但解释说差距只缩小3颗；−1/2反而简洁正确。Q08 +1/2把所有列出月份都说30天并循环，+1虽不循环却把二月归入30天且前后月份说明矛盾；±1/4的日历说明正确。这里只能记录已测试档位上的循环范围及不对称，不能从−1/2到−1的两点推精确阈值或天然语义功能。

### L31-N008750

原文索引：[Q01/group-440](../delivery-r01/paired_raw.html#group-440) · [Q02/group-441](../delivery-r01/paired_raw.html#group-441) · [Q03/group-442](../delivery-r01/paired_raw.html#group-442) · [Q04/group-443](../delivery-r01/paired_raw.html#group-443) · [Q05/group-444](../delivery-r01/paired_raw.html#group-444) · [Q06/group-445](../delivery-r01/paired_raw.html#group-445) · [Q07/group-446](../delivery-r01/paired_raw.html#group-446) · [Q08/group-447](../delivery-r01/paired_raw.html#group-447)

Q01、Q04、Q05、Q06在±1仍相关；Q04 +1把收纳位置写成“椅缝或收纳箱”，虽有两行但内容不宜直接当作无误。Q02 [Q02/group-441](../delivery-r01/paired_raw.html#group-441) +1/2先称乙更多再算出相等，+1继承错误结论后进入“当乙”循环；−1/2与−1均清楚给15=15。Q03 [Q03/group-442](../delivery-r01/paired_raw.html#group-442) −1是提出提前告知的改写，+1变成教拖延者如何确认时间并举第一人称例子，沟通角色发生移动。Q07 [Q07/group-446](../delivery-r01/paired_raw.html#group-446) +1的“是的…带伞以防万一”明确基于未知作预防建议，不等同于捏造已知天气；−1则先说无法判断。Q08 [Q08/group-447](../delivery-r01/paired_raw.html#group-447) −1以二月反例简洁驳斥、−1/2列出31天月份；+1错误说4个30天、2个31天、2个28/29天却合计365/366，+1/2可见月份和天数正确但被128 token上限截在“而非360”。强档符号差别及角色变化都只是这八题上的观察。

## 阅读完整性与解释边界

L00第一次与体积很大的export_receipt输出同批，工具出现总输出截断提示；随后已单独重新显示并完整阅读L00全部八题11栏，见END_FULL_4B_L00_Q01-Q08。L01–L31逐层独立显示，均无工具截断。这里的工具截断恢复与模型自身length_limit是两回事，后者保留为原始输出事实。

以上差异、反例与未完现象是原八题上的观察。若把跨题词语侵入、重复吸引或日历敏感解释成机制，那仍只是待检验假说；本次未做机制验证、追加试题、加载模型或新实验。
