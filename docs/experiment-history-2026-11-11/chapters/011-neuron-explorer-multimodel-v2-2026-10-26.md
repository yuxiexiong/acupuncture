# 011．多模型Neuron Explorer与历史结果接入

[返回总时间线](../README.zh-CN.md)

**时间定位**：版本/记录日期 2026-10-26；未从所选收据确定完整运行起止，不据目录名补写时刻。

**当时的目的与设计**

将Qwen2B/4B/9B布局及后来的随机针、剂量、内部轨迹接入三维界面；Llama使用编号布局。

**实际过程、结果与后来更正**

10月27日旧四服务按用户要求停止后，后续以只读模式接入已有回答；10月28日接入7632条正式trace和56条预检，缺失/额外/重复均0。界面接入不是新增科学样本，采集本身在各trace条目另列。

**来源身份**：`neuron-explorer-multimodel-v2-2026-10-26`；本章主体来源提交 `7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8`。下方原文中的状态是各文件写作时的状态，不能把早期“尚未运行”覆盖后期正式收据，也不能将后期结果倒填进早期设计。


## 原设计、执行过程、结果与更正全文

以下按“设计与题目 → 工程/执行记录 → 结果/更正 → 其他历史说明”组织；同类内没有可靠时间时保留路径顺序，不冒充严格先后。正文未删段；仅为本章节重排标题层级、把相对链接指向固定提交。原始字节另外完整保存。

### 原件 1：原版 Neuron Explorer 多模型版 v2

原路径：`experiments/neuron-explorer-multimodel-v2-2026-10-26/PROTOCOL.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/neuron-explorer-multimodel-v2-2026-10-26/PROTOCOL.zh-CN.md) · [单独阅读副本](../library/7d763d55af20aade.md)；SHA-256：`7d763d55af20aade40bc8f15b5d148e7cade4085ca19717d6984e2f03d955af5`。

---

#### 原版 Neuron Explorer 多模型版 v2

用户要求保持一模一样的工具，将 Qwen3.5-2B、9B 加入现有4B。本轮授权范围是模型适配、各自必要可视化缓存、交互与有限功能验收；不重启旧行为或能力实验。原v1与历史证据保留不改。

- 原始源码固定 ddb144e4121fbeb16ec080077dd67247e499132d；沿用v1两处修复，新增适配另存补丁。
- 三模型的路径、revision、结构、端口见 models.json；每模型独立缓存、命名和会话。模型切换不把原通道当作对应位置。
- 保留原三维图、搜索、读取、干预对照与详情交互。每个新增缓存从相应模型计算，不能把4B数组用于2B/9B。缓存生成方法、耗时与缺失范围必须记录。
- 已有后台任务不停止。缓存构建可顺序运行，模型推理仅用于资源准备和下列有限验收。
- 各模型固定自然文本 The sky is blue.、提示 Name two colors.，取合法位置L10/N100，add=0及0.1，每列最多12新token，贪心生成。验证零剂量三列相同，非零只要求成功与记录，不要求特定行为。另检查边界坐标、布局、词表、连接、搜索、三模型切换及缓存身份隔离。
- 剂量/正常化保留工具定义；缓存或读取变化不能声称复现人格行为或机制。

缓存校准补充：服务器不能访问原数据流，改为官方 datasets-server 获取的 sample-10BT 前1100条完整记录；固定子集以 IterableDataset.shuffle(seed=0,buffer_size=1000) 重排，每模型独立测20段512token并跳过首位置，保留token IDs和来源。它不是作者缓存的同一文本样本，尺度定义相同。

用户进一步明确选择“完整补齐全图，与4B保持相同搜索功能”。因此2B覆盖24×6144、9B覆盖32×12288的正负干预词表图；四个原上下文、dose=0.8、每批96通道，所有分层完整输出校验后合并，局部计时文件不混入。可将模型各层分配两张卡，保留每段实际设备、耗时和哈希。

---

### 原件 2：Neuron Explorer：Qwen3.5 2B / 4B / 9B

原路径：`experiments/neuron-explorer-multimodel-v2-2026-10-26/README.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/neuron-explorer-multimodel-v2-2026-10-26/README.zh-CN.md) · [单独阅读副本](../library/d761df586e1e7fdc.md)；SHA-256：`d761df586e1e7fdcb46ac3f2900d1ca2d710adce95be1da680e9fe94c58c4092`。

---

#### Neuron Explorer：Qwen3.5 2B / 4B / 9B

**2026-10-28 本地内部轨迹已接入：** 7,632条正式记录（2B920、4B4,872、9B920、Llama920）及56条单列预检已完整回传，逐文件与逐条轨迹核验通过，缺失/额外/重复均为0。双击 `open-brainmap.command` 现在打开**本地** `http://127.0.0.1:8794/?model=4b`；四模型共用此端口，按注入层、通道、正负剂量和题目选择，逐token查看全部层的Attention/MLP/残差差分，点板查看数值，右侧对比原版与干预回答。原Three.js界面、三Qwen布局/词表/连接缓存保留；Llama明确使用编号布局。窄窗口点左上角 `›` 展开筛选，“定位注入层”可放大观察。无模型加载、无新实验、无需SSH；完整使用说明和验收见 [trace-view-r01](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/neuron-explorer-multimodel-v2-2026-10-26/trace-view-r01/README.zh-CN.md)。下方远端启动与原只读服务说明为历史。

**2026-10-27 脑图实验入口：** 已将全层十点调查与五档正剂量结果直接接入原 Three.js 三维界面。打开 `http://127.0.0.1:8794/`（或双击 `open-brainmap.command`）即可旋转、缩放、点选通道；右侧“脑图实验”显示同题原版和干预回答，可换题、换剂量或展开六份回答。左侧“实验点”列出每层十点，五档点带金圈；2B/4B/9B仍由顶部切换。全景与点位定位按钮保留三维透视。

这次重新启动的三个服务均为 `EXPLORER_NO_MODEL=1`、`EXPLORER_READ_ONLY=1`：只读取原布局/连接/词表缓存及已归档的9,880条回答，不加载权重，不运行新实验，所有POST被禁用。颜色仅表示所选题目和剂量的输出形态，灰色为缺测；原连接不代表本次实验测得的激活传播。验证脚本 `check_brainmap.py`，新增补丁及验收材料见 `brainmap-r01/`。下文停止记录为此前历史状态。

当前服务状态：2026-10-27 北京时间12:07，按用户要求停止旧版4B及多模型版2B/4B/9B四个服务，显存已释放，缓存与结果保留。等待用户再次使用时再启动；`open.command` 只建立连接，不会自动重启远端模型。停止核验见 `shutdown-2026-10-27-r01.json`。

保留作者原界面，顶部新增模型选择。源提交为 `ddb144e4121fbeb16ec080077dd67247e499132d`；原4B复现v1保留。

2026-10-26 北京时间22:03:18，完整缓存与三模型实时API验收均已完成；2B覆盖147456个通道，9B覆盖393216个通道，4B复用原公开缓存。每模型15项固定API检查通过，浏览器最终验收也已通过，记录见 `browser-acceptance-r01.json`。完整状态见[收据](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/neuron-explorer-multimodel-v2-2026-10-26/receipt.json)，逐文件大小、形状和SHA-256见[最终缓存元数据](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/neuron-explorer-multimodel-v2-2026-10-26/evidence-final-r01/cache-metadata.json)，原始请求/响应、校准和运行日志见[取回清单](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/neuron-explorer-multimodel-v2-2026-10-26/evidence-final-r01/fetch-manifest.json)。完整索引与实时验收分别记录，不以某层文件生成代替全图完成。

| 模型 | 层数 | 每层MLP通道 | 本地端口 |
| --- | ---: | ---: | ---: |
| Qwen3.5-2B | 24 | 6144 | 8792 |
| Qwen3.5-4B | 32 | 9216 | 8794 |
| Qwen3.5-9B | 32 | 12288 | 8799 |

部署完成后，双击 `open.command` 连接三端口并打开4B。顶部下拉切换2B/4B/9B；切换清空当前坐标及普通对话，已有Claude历史按模型端口各自保存。`L14 N8949` 在2B不存在，系统会拒绝越界坐标；相同编号不代表跨模型功能对应。

操作与v1相同：地图点选或顶部跳转；Details看词表和连接；Chat中的reads you读激活、writes做正/零/反向三列干预；fires显示输入的全模型激活。换干预条件先clear，避免对话历史混入。

##### 来源与隔离

`models.json` 固定模型路径、官方revision与维度。三个模型的缓存、命名与会话隔离，服务进程独立。缓存身份和形状不匹配时启动失败。2B/9B不读取4B数值缓存。

`multimodel.patch` 包含对原始提交的所有修改（含v1两处修复）；`source-changes.json` 记录前后哈希。模型权重未修改，未重启旧题集。源码、缓存、依赖和下载不进入Git；较大的新缓存保存在本次远端版本目录，以逐文件哈希清单记录，原始结果不丢弃。

4B复用v1六个公开缓存，作者没有固定这些缓存的权重revision，这一边界保持不变。2B/9B的布局、连接、logit lens、steer lens及激活尺度分别从已校验的相应权重生成。

##### 全图定义

2B覆盖147456个通道，9B覆盖393216个通道。Steer lens沿用作者四个上下文、正负0.8剂量和每批96通道，保存各方向top12词与KL。2B计294912个正负条件，9B计786432个，每条件四上下文。完整层通过坐标、形状、上下文、标定尺度及有限值检查后才合并，计时部分分片不进入完整索引。

布局仍为归一化权重、完整PCA/SVD、UMAP、网格排序。2B/9B通道数不是完全平方数，适配了不足整行的最后一行。实际构建使用原NumPy完整SVD，没有改成随机近似。

激活尺度采用有来源记录的FineWeb-Edu sample-10BT前1100条固定公开文本，按seed0、buffer1000重排；每模型10240个token，512为一段，跳过各段首位置。尺度定义保留，但该固定子集不是作者原缓存的同一文本样本。文本、token IDs和哈希保留，见 `calibration/manifest.json` 及各模型校准收据。

##### 环境与验收

复用远端 `/workspace/acupuncture/.venv-bench`。UMAP等仅安装在本版本 `runtime/vendor`，未改变共享环境；官方wheel版本与哈希见 `dependency-manifest.json`、`dependency-install-check.json`。

- `test_builder_adaptations.py`：非平方网格、4B排序一致及分片边界。
- `test_cache_merge.py`：完整合并及拒绝部分层、上下文掩码或尺度不一致。
- `test_server_adaptations.py`：三模型身份、维度、坐标、命名隔离和访问边界，不加载模型。
- `live_smoke.py --profile 2b --output 新文件.json`：单模型有限验收，4b/9b同理，保留每次请求和原响应。

实时验收固定L10/N100，自然文本 `The sky is blue.`，生成问题 `Name two colors.`，add=0和0.1，每列最多12新token。这是工具链路验收，不用于宣称人格效果、能力保持或机制发现。

原作者未提供的完整回答扫描、命名库和rollout embeddings仍缺失；完整steer词表图不等于这些数据。Claude面板沿用原实现，本轮不调用外部Claude服务。

##### 远端运行

目录为 `/workspace/acupuncture/experiments/neuron-explorer-multimodel-v2-2026-10-26`。完整缓存就绪后，以现有环境运行 `python serve_model.py 2b`，4b/9b同理。仅监听远端127.0.0.1，经SSH连接本机，没有公开互联网端口。停止前核对本目录runtime中的PID和进程命令，勿终止其他任务。

新检出环境需按v1的固定归档恢复upstream，再应用本目录 `multimodel.patch`，不要先应用v1补丁后重复应用本补丁。模型和缓存按manifest恢复。原版8791服务可独立共存。

---

### 原件 3：全部已有实验的统一可视化入口

原路径：`experiments/neuron-explorer-multimodel-v2-2026-10-26/all-experiments-r01/README.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/neuron-explorer-multimodel-v2-2026-10-26/all-experiments-r01/README.zh-CN.md) · [单独阅读副本](../library/23611d54aaf28e75.md)；SHA-256：`23611d54aaf28e7598af60147d1495995940c58daa054b64a7644972e20ed777`。

---

#### 全部已有实验的统一可视化入口

本次只读取和展示已有证据，没有运行新实验、加载模型或修改原始结果。

- 三维页：`http://127.0.0.1:8794/?model=4b`。顶部切模型，左侧选层、通道、剂量和题目。
- 左下角“全部实验”打开同一工具的历史结果库；也可直接访问`http://127.0.0.1:8794/library.html`。
- 关闭服务后，双击上级目录的`open-brainmap.command`重新启动本地只读服务。

##### 前后区别

此前默认三维页只有7,632条Hook记录；另一旧调查入口是9,880条Qwen十点及正剂量回答，尚未统一全部负剂量、Llama与更早实验。

现在默认三维页读取18,272条唯一回答：2B 3,656、4B 4,872、9B 4,872、Llama 4,872。7,632条Hook是其中子集。重复导出引用合并，原始源文件不改。每层十通道只有+1，其中一个通道有正负五档，不将未测剂量补成观测值。

历史结果库覆盖首轮24题双针、早期三基准、四模型固定能力面板、同族和跨架构迁移、三问追加、拆针及随机对照、组件排序、实际修复与反向重现，以及保留下来的停止记录。未运行计划有单独状态；它们不是实验结果。不同研究有复用样本和不同计分口径，目录条目数与逐题数不作跨实验总和。

##### 展示边界

有Hook：显示同前缀下的逐token组件差分、三维分布与原版／干预后的自由回答。无Hook：显示插针位置和已有回答，清空内部颜色／数值并隐藏轨迹滑块。没有采集不等于没有变化。

旧能力或修复选择题可能只有候选得分，没有自由生成的回答；界面据实展示。组件排序预测与实际修复结果分开。旧停止记录保留状态，不视为完整实验。三维连线和色差不是已经证实的因果链。

##### 核验记录

- `receipt.json`：历史目录、逐类数量、模块和目录哈希。
- `http-acceptance.json`：四模型结果与原文配对、全部目录、HTML入口及只读边界。
- `browser-acceptance.json`：实际页面切换与渲染检查。
- `frontend-files.json`：本次实际交付页面文件哈希。

旧验收记录保留；当前本地服务身份记录在`local-server.json`。

---

### 原件 4：早层输出二维观察台

原路径：`experiments/neuron-explorer-multimodel-v2-2026-10-26/analysis-view-r01/README.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/neuron-explorer-multimodel-v2-2026-10-26/analysis-view-r01/README.zh-CN.md) · [单独阅读副本](../library/7da0ed25f5035b60.md)；SHA-256：`7da0ed25f5035b60d927a90bc78f9b323d28646a205e0a02f373b79e52fcc962`。

---

#### 早层输出二维观察台

[打开本地观察台](http://127.0.0.1:8794/analysis.html?model=4b&layer=0&channel=4146&question=Q04&dose=0.5)。若本地服务未运行，先双击上级目录的 `open-brainmap.command`，再点击三维页左侧“二维对照”。三维、二维互相跳转时保留模型、层、通道、剂量与题目。

这次仅使用已有归档：四模型18,272份唯一单针回答，其中7,632份有内部轨迹。没有模型加载、新推理、GPU运行、语义评分或原文改写。原有三维视图及未完成的三维曲面草稿保留；此目录是独立的二维交付版本。

##### 三组联动视图

1. **同点正负剂量原文**：11个固定槽位按−1至+1排列，0为同模型同题共享原版。可见正文、完整raw_text、token IDs、长度和结束原因；点击剂量查看该条件轨迹。非剂量点只有+1与原版，其余九档明确标为未测。
2. **层×预测步热图**：Attention/GatedDeltaNet、MLP、层末残差分开显示；可切相对差分、1−cosine、绝对差分、无针范数。固定颜色尺度，超范围饱和；点击格子查看五项精确读数，并联动token和曲线。步0是提示末位，预测第1个输出token；没有在最后输出token之后补画前向。
3. **token竞争曲线**：停止优势、实际输出token距无针最佳的logit差值、固定候选token在两分支的log probability。可逐步选择并展开当步所有已保存候选。未保存的候选分数断线，缺轨迹条件清空图表。

停止优势为最佳EOS logit减去最佳非停止logit，正值偏向停止。实际token与无针最佳并列时差值为0，不自动算成分歧；差分或首个不同token不等于语义失败。

图中“无针参照”从提示开始全程无针，使用自己的缓存、强制读取干预分支所选的同一文字历史。它与原版自由回答不同，也不是中途撤针。热图是组件整体差分，未证明完整语句开关或因果传播路径。固定候选曲线的纵轴随当前轨迹缩放，跨剂量比较需看数值；热图颜色尺度固定。

##### 可直接查看的已核验例子

- [4B L0 N4146 Q04 +0.5](http://127.0.0.1:8794/analysis.html?model=4b&layer=0&channel=4146&question=Q04&dose=0.5)：27 tokens。点+1会切换到仅1个EOS；停止优势由无针−17.6875变为干预+3.0625。
- [4B L2 N5063 Q04 +1](http://127.0.0.1:8794/analysis.html?model=4b&layer=2&channel=5063&question=Q04&dose=1)：128 tokens；点步2可见实际`<think>`与无针最高候选`</think>`，clean gap为−5.9375。此通道未做其余九档，不补造剂量曲线。
- [Llama L31 N832 Q04 +1](http://127.0.0.1:8794/analysis.html?model=llama31-8b-instruct&layer=31&channel=832&question=Q04&dose=1)：原文有完整剂量配对，内部轨迹未采集，图表留空。

##### 验收与实现

- [数据验收](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/neuron-explorer-multimodel-v2-2026-10-26/analysis-view-r01/data-acceptance.json)：四模型全部索引、960个完整剂量题组及8,640个稀疏题组；5个真实案例的原文/token、步位置、停止优势、零剂量、缺轨迹、缺候选及并列处理通过。
- [浏览器验收](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/neuron-explorer-multimodel-v2-2026-10-26/analysis-view-r01/browser-acceptance.json)：实际页面与点选，四模型、EOS单步、128步重复、深层缺轨迹、基线零差分、热图/曲线联动、三维双向跳转。
- [交付文件SHA清单](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/neuron-explorer-multimodel-v2-2026-10-26/analysis-view-r01/frontend-files.json)。旧归档、freeze、收据和先前前端验收文件没有重写。
- 运行本地已有服务后，可在上级目录执行 `node test_analysis_view.mjs` 复核数据与变换。服务仍是 `serve_trajectories.py`，后端未改，只通过既有只读接口按需取原文及当前选中轨迹。

页面为本地服务页面，不能单独用file://打开HTML；不需要额外安装绘图库。

---

### 原件 5：传播轨迹视图：尚未完成

原路径：`experiments/neuron-explorer-multimodel-v2-2026-10-26/propagation-view-r01/STATUS.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/neuron-explorer-multimodel-v2-2026-10-26/propagation-view-r01/STATUS.zh-CN.md) · [单独阅读副本](../library/aa2702be90581c31.md)；SHA-256：`aa2702be90581c31052927958dcd9293a917d9a709cf0d4652c8dc35b1dfcdc5`。

---

#### 传播轨迹视图：尚未完成

2026-10-28：用户反馈旧界面缺少直观轨迹，已开始把层×生成步×组件差分展开为三维曲面。随后用户要求优先确认全部实验结果上传Git，因此先保存实现中的源码。

- pending-source/propagation.js：仅语法检查通过，未完成浏览器/几何语义验收。
- pending-source/trace.js：控件/播放/布局集成草稿，尚缺配套CSS和实际验证。
- 当前服务及trace-view-r01/static保留此前已验收的全部结果版本，不加载这些草稿。
- 没有启动新模型实验，未改变原始科学结果。

恢复工作时先完成集成并检查真实token对齐、T=1/null/零剂量、固定尺度和浏览器实际可读性，不把此目录当作已交付功能。

---

### 原件 6：本地全部实验与内部轨迹三维查看

原路径：`experiments/neuron-explorer-multimodel-v2-2026-10-26/trace-view-r01/README.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/neuron-explorer-multimodel-v2-2026-10-26/trace-view-r01/README.zh-CN.md) · [单独阅读副本](../library/e5d3dcabec5e7c31.md)；SHA-256：`e5d3dcabec5e7c3119ea07105e6772466f5f2676b62b807c6492f59041db9205`。

---

#### 本地全部实验与内部轨迹三维查看

打开 `http://127.0.0.1:8794/?model=4b`，或双击上级目录的 `open-brainmap.command`。沿用原 Neuron Explorer 的 Three.js 三维界面，服务只读本地归档，不连接推理服务、不加载权重。启动要求三批归档全部核验通过。

**二维观察台已接入：** 左侧“二维对照”可打开同一点正负剂量原文、层×预测步热图、token竞争曲线，跳转保留所选条件。见[新视图说明与独立验收](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/neuron-explorer-multimodel-v2-2026-10-26/analysis-view-r01/README.zh-CN.md)；本目录下旧前端源码快照与SHA仍保留原验收版本。

**本次扩展：** 默认三维页现覆盖四模型全层十点与单点正负剂量的18,272条唯一回答，其中7,632条具有内部轨迹。左下角“全部实验”还可查首轮双针、能力面板、同族及跨架构迁移、拆针、候选排序、实际修复和已停止记录；历史实验保留各自分母及复用说明，不与单针结果重复相加。新入口是[全部实验库](http://127.0.0.1:8794/library.html)，代码与导入记录位于上级`all-experiments-r01/`。

**此前轨迹归档验收：** 7,632条正式唯一记录、56条预检单列；15,496文件/2.538GiB全量本地归档，缺失/额外/重复为0。四模型页面、深层与正负剂量、原版零差分、时间轴和组件点选已实际检查；[原浏览器验收](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/neuron-explorer-multimodel-v2-2026-10-26/trace-view-r01/browser-acceptance.json)。

##### 怎么看

1. 顶部选模型；左侧选**范围、注入层、通道、正负剂量、题目**。窄窗口点左上角 `›` 展开筛选。“全部回答”下2B可选L0–L23，4B、9B与Llama可选L0–L31；“含内部轨迹”仅显示已采集hook的条件。每层10个通道有+1，其中1个通道有正负五档，不把缺测条件补成结果。
2. 拖动旋转、滚轮缩放，也可点“全景3D”或“定位注入层”。三维板表示Attention和MLP，底部梁表示层末残差；点击查看该层组件的无针范数、干预范数、差分、相对差分和cosine。
3. 拖动右侧token位置滑块，看变化怎样随输入位置和生成推进。默认提示末位，即第一次输出预测；提示内部位置没有采集的logits不显示。最后一个输出token之后没有新增前向，不补画。
4. 右侧下方并排显示同题**原版自由回答／干预后回答**，可展开raw_text或打开原始回答、采集记录和压缩轨迹。原版对照选项可检查零差分。
5. 没有内部轨迹的条件只显示插针位置、剂量和原版／干预回答；组件颜色、时间轴和内部数值清除并明确写“未采集”。这不表示内部没有变化。左下角“全部实验”可逐页读取更早各轮的回答或评分；候选似然评分没有自由回答，不补造文本。

图中颜色比较**相同输入前缀下**干预与无针参照的组件整体读数。原版自由回答是另一个对照，不把分叉后的不同前缀直接相减。固定色标在超上限时饱和；精确数值仍完整显示，灰色表示零范数造成的未定义值。

本图不是逐通道激活图，也没有建立因果路径。三维位置沿用原布局；不同模型同层号或相邻位置不代表同功能。Llama无原工具的权重布局和连接缓存，明确按通道编号排列。Qwen可从左侧链接回旧十点回答调查，原布局、词表搜索和连接缓存仍可读取；离线版没有导出的连接词汇聚合摘要会标为不可用。

##### 覆盖与证据

| 模型 | 全层回答范围 | 唯一回答 | 其中有内部轨迹 |
|---|---|---:|---:|
| Qwen3.5-2B | L0–L23 | 3,656 | 920 |
| Qwen3.5-4B | L0–L31 | 4,872 | 4,872 |
| Qwen3.5-9B | L0–L31 | 4,872 | 920 |
| Llama-3.1-8B-Instruct | L0–L31 | 4,872 | 920 |

下面是7,632条轨迹子集的采集范围，不能再加到18,272条回答总数上：

| 模型 | 注入范围 | 观察范围 | 唯一正式记录 |
|---|---|---|---:|
| Qwen3.5-2B | L0–L5 | 全24层×3组件 | 920 |
| Qwen3.5-4B | L0–L31 | 全32层×3组件 | 4,872 |
| Qwen3.5-9B | L0–L5 | 全32层×3组件 | 920 |
| Llama-3.1-8B-Instruct | L0–L5 | 全32层×3组件 | 920 |

每个模型包含8份共享原版；合计7,632条。预检及追加批次的16份校准引用不计入正式数量。

- [全量归档核验](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/layer-trace-extension-v1-2026-10-28/archive-r01/combined-verification.json)：原始数据位于各实验的`archive-r01/execution-r01/`；旧快照、远端结果及冻结代码保持原样。
- [后端验收](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/neuron-explorer-multimodel-v2-2026-10-26/trace-view-r01/backend-acceptance.json)：覆盖、同题原版配对、模型隔离、原始证据和只读边界。
- [缓存核验](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/neuron-explorer-multimodel-v2-2026-10-26/trace-view-r01/cache-verification.json)：原三模型21份缓存逐文件SHA与原清单一致。
- [前端源码覆盖包](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/neuron-explorer-multimodel-v2-2026-10-26/trace-view-r01/static)及[SHA清单](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/neuron-explorer-multimodel-v2-2026-10-26/trace-view-r01/frontend-files.json)，[固定Three.js依赖清单](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/neuron-explorer-multimodel-v2-2026-10-26/trace-view-r01/vendor-manifest.json)。

实现是一个本地HTTP服务及原界面上的轨迹覆盖。压缩轨迹按需读取，没有将全部轨迹一次性载入浏览器。若默认Python路径不可用，给`EXPLORER_PYTHON`指定已有的带NumPy的Python即可；没有安装新模型依赖。

---


## 时间、运行与停止收据索引

下面是所收集JSON的原有时间字段与状态，不把预计结束时间当实际完成时间。未列时间的文件仍有原件链接。完整JSON全部保存在原文归档，不能以此索引中的标量代替完整嵌套内容。

| 原件 | 原记录状态/阶段 | 原时间字段（原时区） |
|---|---|---|
| [all-experiments-r01/cpu-all-results-acceptance.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/neuron-explorer-multimodel-v2-2026-10-26/all-experiments-r01/cpu-all-results-acceptance.json) | {"status": "passed"} | {} |
| [all-experiments-r01/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/neuron-explorer-multimodel-v2-2026-10-26/all-experiments-r01/receipt.json) | {"status": "verified"} | {"created_at": "2026-10-28T09:25:34.373022+00:00"} |
| [brainmap-r01/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/neuron-explorer-multimodel-v2-2026-10-26/brainmap-r01/receipt.json) | {"status": "completed"} | {"verified_at": "2026-10-27T14:34:28.118030+00:00"} |
| [deployment-content-audit.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/neuron-explorer-multimodel-v2-2026-10-26/deployment-content-audit.json) | {} | {} |
| [evidence-final-r01/data/2b/calibration-receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/neuron-explorer-multimodel-v2-2026-10-26/evidence-final-r01/data/2b/calibration-receipt.json) | {} | {} |
| [evidence-final-r01/data/2b/steer-cache-receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/neuron-explorer-multimodel-v2-2026-10-26/evidence-final-r01/data/2b/steer-cache-receipt.json) | {"status": "complete"} | {} |
| [evidence-final-r01/data/9b/calibration-receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/neuron-explorer-multimodel-v2-2026-10-26/evidence-final-r01/data/9b/calibration-receipt.json) | {} | {} |
| [evidence-final-r01/data/9b/steer-cache-receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/neuron-explorer-multimodel-v2-2026-10-26/evidence-final-r01/data/9b/steer-cache-receipt.json) | {"status": "complete"} | {} |
| [evidence-final-r01/runtime/postbuild-receipt-r01.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/neuron-explorer-multimodel-v2-2026-10-26/evidence-final-r01/runtime/postbuild-receipt-r01.json) | {"status": "passed"} | {"started_at": "2026-10-26T11:02:36.125681+00:00"} |
| [evidence-partial-r01/data/2b/calibration-receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/neuron-explorer-multimodel-v2-2026-10-26/evidence-partial-r01/data/2b/calibration-receipt.json) | {} | {} |
| [evidence-partial-r01/data/2b/steer-cache-receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/neuron-explorer-multimodel-v2-2026-10-26/evidence-partial-r01/data/2b/steer-cache-receipt.json) | {"status": "complete"} | {} |
| [evidence-partial-r01/data/9b/calibration-receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/neuron-explorer-multimodel-v2-2026-10-26/evidence-partial-r01/data/9b/calibration-receipt.json) | {} | {} |
| [evidence-partial-r01/runtime/postbuild-receipt-r01.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/neuron-explorer-multimodel-v2-2026-10-26/evidence-partial-r01/runtime/postbuild-receipt-r01.json) | {"status": "running"} | {"started_at": "2026-10-26T11:02:36.125681+00:00"} |
| [model-assets-verification.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/neuron-explorer-multimodel-v2-2026-10-26/model-assets-verification.json) | {"scope": "Read-only current file existence/size, config inspection and fresh SHA-256 of two configs and all five weight shards; tokenizers and auxiliary files were not rehashed in this check."} | {"recorded_at": "2026-10-26T10:37:19.325184+00:00"} |
| [receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/neuron-explorer-multimodel-v2-2026-10-26/receipt.json) | {"status": "complete"} | {"updated_at": "2026-10-26T14:06:32.787426+00:00"} |
| [trace-view-r01/cache-verification.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/neuron-explorer-multimodel-v2-2026-10-26/trace-view-r01/cache-verification.json) | {"status": "verified", "new_model_inference": false} | {} |

## 全部原始资产入口

本目录在固定提交下共有161个跟踪文件，包含代码、原回答、失败、收据和压缩证据；文件数不是样本数。[逐文件完整账本](../assets/011-neuron-explorer-multimodel-v2-2026-10-26.tsv) · [原目录](https://github.com/yuxiexiong/acupuncture/tree/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/neuron-explorer-multimodel-v2-2026-10-26)。未复制模型权重、环境或凭据。
