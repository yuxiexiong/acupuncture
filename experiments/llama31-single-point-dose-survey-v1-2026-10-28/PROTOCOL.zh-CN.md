# Llama逐层单点正负剂量：独立实验B合同

2026-10-28。执行用户“与前面完全一样、两个实验分别做”的纠正。实验A先完成每层十点+1探索，本实验每层仅选其中一点；不把十点×十剂量继续运行。测试通过后直接运行的既有授权继续有效。

模型固定为meta-llama/Llama-3.1-8B-Instruct@0e9e39f249a16976918f6564b8830bc894c89659，32层。原Q01–Q08题面和中文指令逐字沿用千问；BF16、eager、batch1、每worker四CPU线程、greedy、fresh context/cache。每题最多128新token，EOS提前结束保留原长和结束token；不补齐、不续写、不按语义重试、不评分。模型原生词表/模板/EOS不可硬套千问；Llama停止ID128001/128008/128009，native模板日期固定26 Oct2026，BOS一次，thinking不适用。干净提示逐层block输出token L2中位数（排除首token）作为m，单个gated MLP通道在down_proj前加入c(d)=d*m/||Wdown[:,n]||2；原double比例每档独立转BF16，prompt和所有decode步注入，每次撤hook，不改权重。全部raw/token、失败、运行身份和源哈希保留。

## 固定选点和剂量

每层将A原10点按通道升序，random.Random(f"acupuncture-layer-dose-v1:{model_id}:{layer}").choice(candidates)选一个。model_id=llama31-8b-instruct，32个点在B输出前冻结，不按回答效果换点。每点正负五档±1/16、±1/8、±1/4、±1/2、±1，无0.75；0为原版。八题均独立上下文。正负同模型/层/通道/题/clean校准；请求和BF16偏移互为相反数，激活加法舍入后的delta和生成行为不强制反向。

复用A入选点的256份+1及8份唯一基线；新增其余9档32×8×9=2304份。共2568唯一来源、320个非零八题条件、256组十一栏、2816展示单元。两卡按layer%2，每卡16层、1152份新回答。A与B合计4872唯一正式来源，不把264复用再算新增。A/B是两个独立实验、各自合同/冻结/输出/完成条件；展示−1、−.5、−.25、−.125、−.0625、0、+.0625、+.125、+.25、+.5、+1。

## 来源与验收

只接受A全部完成且两worker exit0、全量hash/token/权重/hook通过的来源。授权绑定A controller和receipt哈希，逐份复用保留原路径与hash；源分片不随本批卡号改变。B clean calibration、实际context/inputtokenhash、列范数及metadata必须与来源一致（仅device可不同）。中断的旧合并实验不复用。

CPU验证32点选择、九个新增档和十个展示档、1152+1152、复用来源、部分结果禁止完整导出。GPU预检每worker44次共88次：原8题，首/中/末点各Q01/Q04/Q08做zero、十档、restored；基线和+1逐token重放A来源，zero/restored精确恢复。实际hook偏移/位置、32层目标权重hash及移除通过；两worker预检exit0/独立审查通过后才正式生成。正式metadata/clean校准与自己预检精确一致。

两worker正式完成exit0、文件/token/完整八题覆盖及来源核验后自动导出十一栏，取回全量证据并本地验hash。计时/排队/导出归档/阅读分别记，半小时巡检沿用用户要求；原文开放逐组阅读、逐层笔记保留覆盖、反例、不确定性，不新增推理/语义评分/人格命名。全部交付后结束巡检。
