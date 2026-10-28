# Neuron Explorer：Qwen3.5 2B / 4B / 9B

**2026-10-28 本地内部轨迹已接入：** 7,632条正式记录（2B920、4B4,872、9B920、Llama920）及56条单列预检已完整回传，逐文件与逐条轨迹核验通过，缺失/额外/重复均为0。双击 `open-brainmap.command` 现在打开**本地** `http://127.0.0.1:8794/?model=4b`；四模型共用此端口，按注入层、通道、正负剂量和题目选择，逐token查看全部层的Attention/MLP/残差差分，点板查看数值，右侧对比原版与干预回答。原Three.js界面、三Qwen布局/词表/连接缓存保留；Llama明确使用编号布局。窄窗口点左上角 `›` 展开筛选，“定位注入层”可放大观察。无模型加载、无新实验、无需SSH；完整使用说明和验收见 [trace-view-r01](trace-view-r01/README.zh-CN.md)。下方远端启动与原只读服务说明为历史。

**2026-10-27 脑图实验入口：** 已将全层十点调查与五档正剂量结果直接接入原 Three.js 三维界面。打开 `http://127.0.0.1:8794/`（或双击 `open-brainmap.command`）即可旋转、缩放、点选通道；右侧“脑图实验”显示同题原版和干预回答，可换题、换剂量或展开六份回答。左侧“实验点”列出每层十点，五档点带金圈；2B/4B/9B仍由顶部切换。全景与点位定位按钮保留三维透视。

这次重新启动的三个服务均为 `EXPLORER_NO_MODEL=1`、`EXPLORER_READ_ONLY=1`：只读取原布局/连接/词表缓存及已归档的9,880条回答，不加载权重，不运行新实验，所有POST被禁用。颜色仅表示所选题目和剂量的输出形态，灰色为缺测；原连接不代表本次实验测得的激活传播。验证脚本 `check_brainmap.py`，新增补丁及验收材料见 `brainmap-r01/`。下文停止记录为此前历史状态。

当前服务状态：2026-10-27 北京时间12:07，按用户要求停止旧版4B及多模型版2B/4B/9B四个服务，显存已释放，缓存与结果保留。等待用户再次使用时再启动；`open.command` 只建立连接，不会自动重启远端模型。停止核验见 `shutdown-2026-10-27-r01.json`。

保留作者原界面，顶部新增模型选择。源提交为 `ddb144e4121fbeb16ec080077dd67247e499132d`；原4B复现v1保留。

2026-10-26 北京时间22:03:18，完整缓存与三模型实时API验收均已完成；2B覆盖147456个通道，9B覆盖393216个通道，4B复用原公开缓存。每模型15项固定API检查通过，浏览器最终验收也已通过，记录见 `browser-acceptance-r01.json`。完整状态见[收据](receipt.json)，逐文件大小、形状和SHA-256见[最终缓存元数据](evidence-final-r01/cache-metadata.json)，原始请求/响应、校准和运行日志见[取回清单](evidence-final-r01/fetch-manifest.json)。完整索引与实时验收分别记录，不以某层文件生成代替全图完成。

| 模型 | 层数 | 每层MLP通道 | 本地端口 |
| --- | ---: | ---: | ---: |
| Qwen3.5-2B | 24 | 6144 | 8792 |
| Qwen3.5-4B | 32 | 9216 | 8794 |
| Qwen3.5-9B | 32 | 12288 | 8799 |

部署完成后，双击 `open.command` 连接三端口并打开4B。顶部下拉切换2B/4B/9B；切换清空当前坐标及普通对话，已有Claude历史按模型端口各自保存。`L14 N8949` 在2B不存在，系统会拒绝越界坐标；相同编号不代表跨模型功能对应。

操作与v1相同：地图点选或顶部跳转；Details看词表和连接；Chat中的reads you读激活、writes做正/零/反向三列干预；fires显示输入的全模型激活。换干预条件先clear，避免对话历史混入。

## 来源与隔离

`models.json` 固定模型路径、官方revision与维度。三个模型的缓存、命名与会话隔离，服务进程独立。缓存身份和形状不匹配时启动失败。2B/9B不读取4B数值缓存。

`multimodel.patch` 包含对原始提交的所有修改（含v1两处修复）；`source-changes.json` 记录前后哈希。模型权重未修改，未重启旧题集。源码、缓存、依赖和下载不进入Git；较大的新缓存保存在本次远端版本目录，以逐文件哈希清单记录，原始结果不丢弃。

4B复用v1六个公开缓存，作者没有固定这些缓存的权重revision，这一边界保持不变。2B/9B的布局、连接、logit lens、steer lens及激活尺度分别从已校验的相应权重生成。

## 全图定义

2B覆盖147456个通道，9B覆盖393216个通道。Steer lens沿用作者四个上下文、正负0.8剂量和每批96通道，保存各方向top12词与KL。2B计294912个正负条件，9B计786432个，每条件四上下文。完整层通过坐标、形状、上下文、标定尺度及有限值检查后才合并，计时部分分片不进入完整索引。

布局仍为归一化权重、完整PCA/SVD、UMAP、网格排序。2B/9B通道数不是完全平方数，适配了不足整行的最后一行。实际构建使用原NumPy完整SVD，没有改成随机近似。

激活尺度采用有来源记录的FineWeb-Edu sample-10BT前1100条固定公开文本，按seed0、buffer1000重排；每模型10240个token，512为一段，跳过各段首位置。尺度定义保留，但该固定子集不是作者原缓存的同一文本样本。文本、token IDs和哈希保留，见 `calibration/manifest.json` 及各模型校准收据。

## 环境与验收

复用远端 `/workspace/acupuncture/.venv-bench`。UMAP等仅安装在本版本 `runtime/vendor`，未改变共享环境；官方wheel版本与哈希见 `dependency-manifest.json`、`dependency-install-check.json`。

- `test_builder_adaptations.py`：非平方网格、4B排序一致及分片边界。
- `test_cache_merge.py`：完整合并及拒绝部分层、上下文掩码或尺度不一致。
- `test_server_adaptations.py`：三模型身份、维度、坐标、命名隔离和访问边界，不加载模型。
- `live_smoke.py --profile 2b --output 新文件.json`：单模型有限验收，4b/9b同理，保留每次请求和原响应。

实时验收固定L10/N100，自然文本 `The sky is blue.`，生成问题 `Name two colors.`，add=0和0.1，每列最多12新token。这是工具链路验收，不用于宣称人格效果、能力保持或机制发现。

原作者未提供的完整回答扫描、命名库和rollout embeddings仍缺失；完整steer词表图不等于这些数据。Claude面板沿用原实现，本轮不调用外部Claude服务。

## 远端运行

目录为 `/workspace/acupuncture/experiments/neuron-explorer-multimodel-v2-2026-10-26`。完整缓存就绪后，以现有环境运行 `python serve_model.py 2b`，4b/9b同理。仅监听远端127.0.0.1，经SSH连接本机，没有公开互联网端口。停止前核对本目录runtime中的PID和进程命令，勿终止其他任务。

新检出环境需按v1的固定归档恢复upstream，再应用本目录 `multimodel.patch`，不要先应用v1补丁后重复应用本补丁。模型和缓存按manifest恢复。原版8791服务可独立共存。
