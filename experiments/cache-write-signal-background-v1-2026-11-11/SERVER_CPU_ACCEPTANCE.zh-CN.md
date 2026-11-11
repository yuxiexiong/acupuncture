# WSB-01 服务器 CPU 验收与真实预检就绪状态

2026-11-11，北京时间 17:50 最终核对。用户明确授权完成服务器 CPU 环境核对、发现问题先修复，仍不上卡。

**结论：CPU 环境核对通过，当前代码与服务器环境具备进入真实模型预检的条件。真实预检未启动，正式实验未启动，GPU 授权仍关闭。** 本轮加载完整模型 0 次、模型前向 0 次、GPU 小时 0；全程 `CUDA_VISIBLE_DEVICES=''`，最终 `cuda_initialized=false`。没有恢复定时巡检，没有查询或改变其他 GPU 任务。

## 1. 实际完成的核对

| 对象 | 结果与证据 |
|---|---|
| 服务器 | `gqa-h20`；操作镜像目录 `/workspace/acupuncture`，无 Git 元数据。只上传本实验文件及唯一缺失的历史文本，使用逐文件 hash 对齐，不对旧目录做 checkout 或整体覆盖 |
| 既有解释器 | `/workspace/claude-jump/qwen35-neuron-steering-20261025/.venv/bin/python`；沿用环境，未安装或升级依赖 |
| 依赖版本 | PyTorch `2.6.0+cu124`、Transformers `5.20.2`，与冻结模型合同一致。版本带 CUDA 后缀不代表本轮使用了 CUDA |
| 上游计算函数 | 真实安装的 Qwen3.5 递推 kernel 已在 CPU 合成张量上验收。采用历史 torch 路径，FLA／Hub kernels／额外 causal-conv 包均未启用；未为了性能更换 kernel |
| CPU 测试 | [cpu-server-r02.json](readiness/cpu-server-r02.json)：15 项全部通过，0 failures、0 errors，`upstream_kernel_tested=true`。完整[日志](readiness/cpu-server-r02.log)保留 |
| 仓库运行依赖 | [environment-server-r02.json](readiness/environment-server-r02.json)：386 个文件核对通过，`environment_checked=true`；包括形成、解析、材料、校准与旧 C0/OO/DO 桥接记录 |
| 模型资产 | 固定 revision `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`；12 个资产文件的大小与 SHA256 核对通过。这里是按块读取文件做 hash，不实例化模型、不把权重加载为模型张量 |
| 上游源码 | Qwen3.5 模型实现与缓存实现 hash 均与旧 NGC 环境记录一致，未修改上游文件 |
| 最后的一致性核对 | [preflight-readiness-server-r01.json](readiness/preflight-readiness-server-r01.json)：CPU 收据、环境清单、当前源文件及外部源码相互匹配；关闭的授权确实拒绝启动 |
| 空间 | 当时空闲 `59,449,982,976` 字节，约 **55.37 GiB**；高于预检所需的 8 GiB。正式空间是否够用，须待预检的实际产物外推，不在本轮提前判通过 |

本地修复回归也通过：[cpu-local-r05.json](readiness/cpu-local-r05.json)，15 项；本地仍没有对应 Qwen3.5 上游模块，因此这份本地收据不能替代服务器收据。

## 2. 发现的问题及修复

**问题一：原启动逻辑把两次资产核对的耗时也拿来判断身份相等。**

`model_assets()` 返回文件身份和 `wall_seconds`，两次文件完全一致也几乎不可能耗时相同。原先比较整份返回字典，会在真正启动时误报失败。现改成重新核对全部资产文件，然后只比较通过状态、文件数和 manifest hash；耗时保留作计费记录。新增回归证明“只有耗时不同”通过，而文件数、hash 或通过状态不同仍拒绝。没有跳过模型文件校验。

**问题二：服务器少一份方案引用的历史尺寸审计文本。**

首轮 CPU 测试有 1 个 error，环境验收也因此停止；失败并非上游数值测试失败。缺失文件为 `experiments/cache-native-write-readout-v1-2026-11-05/analysis/posthoc/output-shared-fraction-r01.txt`。从已确认仓库精确补回，SHA256 为 `a8a9a8a4d00b011c97b6fa48b071c846b4d4df6f4d52a21d3490771fa71b2553`，与原设计收据一致。没有重跑历史实验或改造一份新结果代替它。

首轮失败的[CPU 收据](readiness/cpu-server-r01.json)、[CPU 日志](readiness/cpu-server-r01.log)、[环境失败日志](readiness/environment-server-r01.log)和[当时源码](readiness/revisions/server-r01/wsb_run.py)全部保留，后续通过没有覆盖失败记录。

**问题三：原空间门槛把全包产物上限当作每个阶段都必须空出的空间。**

服务器约 55 GiB 可用，原逻辑会连小预检也拒绝。预检仅 60 份差值包，dense 差值合计约 3.281 GiB；现明确预检空间门槛与阶段产物上限为 **8 GiB**，正式启动则检查预检实测后含 1.25 余量的正式空间预测。预检／失败／正式合计 **64 GiB 总上限不变**，超限仍停止；没有删除旧文件，也没有减少科学配对、重放验收或降低保存精度。

工程自查：这项资源细化保持 C12/C13 的全部重建、重放、失败与存盘入账要求；C01/C02/C08/C14 的问题、估计对象、判读和退出不变。不是新科学设计，不将预检空间充足冒充正式资源已通过。

## 3. 现在能做与不能宣称的事情

**能做的下一步：在获得上卡授权后，开始原方案的真实预检。** 固定 NQ02 的 6 个既有输入、30 个有序配对；192 条自然轨迹，另加 12 次零差 t1 验收。单 H20，预检硬上限 **0.4 GPU 进程小时＝24 分钟**，包含模型加载、形成、来源采集、重放、自然生成和存盘。启动时重新检查 GPU 是否空闲、显存和磁盘；本次 CPU 核对没有对 GPU 可用性作判断或预约。

真实预检必须回答三件尚未验证的事：

1. 在完整模型中，新运行是否能重放旧 C0/OO/DO；同源增量重放的全部 t1 缓存、logits、自然 token 和停止方式是否一致。
2. 完整模型里的数值误差、层覆盖和状态身份是否满足协议，而非仅在人工小张量上成立。
3. 根据实测最长单价、全部续写上界和产物体积，正式实验能否放进 2.2 小时／全包 3 小时，以及当时的可用存储。

**不能宣称：** 已通过真实模型数值预检、正式四格已运行、假设得到支持、已经足以投稿、或正式卡时必定小于估计。CPU 通过不批准正式实验；没有自动转正式或自动重试。

当前授权文件仍为 [authorization.disabled.json](authorization.disabled.json)，`gpu_authorized=false`、`allowed_stages=[]`。这份报告是预检就绪判断，不是上卡授权。

## 4. 可追溯交付

- 初次上传与修复部署：[deployment-server-r01.json](readiness/deployment-server-r01.json)、[deployment-server-r02.json](readiness/deployment-server-r02.json)。覆盖前先核对旧 hash，并将本实验的首轮源码另存。
- 服务器证据回收：[server-collection-r01.json](readiness/server-collection-r01.json)，逐文件 SHA256 与原始传输包 hash。
- 服务器环境清单绑定当前三份修复源码及测试，未来任何代码修改都必须重新生成对应验收收据；不沿用首轮或本地旧收据放行。
- 原[设计](PLAN.zh-CN.md)、[作者自查](SELF_CHECK.zh-CN.md)与[本地实施记录](IMPLEMENTATION.zh-CN.md)保留各自当时身份；当前服务器工程状态以本报告为准。
