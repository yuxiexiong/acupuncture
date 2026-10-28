# Llama逐层十点探索：独立实验A合同

2026-10-28。用户明确纠正：“不要合到一起，做两个分别的不同的东西。每层点数十个，然后做剂量的时候，每层就选一个点去做，和前面做完全一样的东西就行。”本版替代已停止的十点×十剂量设计；旧冻结/原文/收据不覆盖。继续执行既有授权的CPU、GPU验收及通过后直接正式运行。

模型固定为meta-llama/Llama-3.1-8B-Instruct@0e9e39f249a16976918f6564b8830bc894c89659，32层。原Q01–Q08题面和中文指令逐字沿用千问；BF16、eager、batch1、每worker四CPU线程、greedy、fresh context/cache。每题最多128新token，EOS提前结束保留原长和结束token；不补齐、不续写、不按语义重试、不评分。模型原生词表/模板/EOS不可硬套千问；Llama停止ID128001/128008/128009，native模板日期固定26 Oct2026，BOS一次，thinking不适用。干净提示逐层block输出token L2中位数（排除首token）作为m，单个gated MLP通道在down_proj前加入c(d)=d*m/||Wdown[:,n]||2；原double比例每档独立转BF16，prompt和所有decode步注入，每次撤hook，不改权重。全部raw/token、失败、运行身份和源哈希保留。

## 固定设计

每层10点，沿用已冻结Llama原320点及千问的确定性抽样公式random.Random(f"acupuncture-layer-survey-v1:{model_id}:{layer}").sample(range(14336),10)，按通道升序。只做+1；每点原八题。正式2560干预+8唯一原版=2568来源，320个八题条件、2560组双栏、5120展示单元。两卡按全局点序号%2，各1280干预；GPU0另8基线。旧中断合并实验只归档，不混入本批科学样本。

## 验收和交付

CPU验证抽样、+1唯一档、两卡分片、记录/token、128/EOS、撤hook与双栏完整性。两worker预检各17次：原八题+首/中/末点Q01/Q04/Q08各zero/+1/restored，共34次。零与恢复必须与基线逐token相同，跨卡八题及clean calibration一致，目标32层权重hash及hook移除通过。核验旧合并实验user-stop receipt和进程退出、GPU空闲后才加载。两worker预检完成exit0并独立审查通过后正式运行，不能复用旧冻结给新设计授权。

正式两worker完成exit0、全量记录与权重/hook核验后自动导出双栏；此后实验B使用自己的合同/冻结/预检和输出。保留完整计时、原文与来源。每30分钟汇报本批完成量、增量、ETA（两卡取慢）、GPU/进程和磁盘，未测阅读不编ETA。机器完成与归档/逐组开放阅读分开，不新增评分或模型实验。
