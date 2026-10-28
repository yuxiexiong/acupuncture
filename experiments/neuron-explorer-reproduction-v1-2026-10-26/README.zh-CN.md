# Neuron Explorer 原工具复现 v1

2026-10-26：原版界面已运行，接通 `Qwen/Qwen3.5-4B`。这是软件功能复现与有限实时验收；截图中的人格配方、两篇论文的实验结论尚未复现。

## 打开

- 当前地址：<http://127.0.0.1:8791/#L15/N3920>
- 断开后，在本机双击本目录的 `open.command`，会重连 SSH 隧道并打开页面；该入口不负责重启远端服务。
- 原版面板占用较多宽度，建议用宽窗口。左边 `›` 打开列表，右边 `‹ N3920` 打开详情；顶部可输入 `L15 N3920` 跳转，滚轮缩放，拖动旋转。
- `Details` 查看词表读出和连接；`Chat` 使用原版正向、原模型、反向三列。此处手动运行会实际调用远端模型。

服务在 `gqa-h20` 的 `127.0.0.1:8791`，经 SSH 转到本机；没有开放公网端口。2026-10-26 18:19 的进程为 `1599626`，占用 GPU 0 约 `9574 MiB`，保留运行供交互。其他已有任务未中断。当前页面截图为 `live-ui.png`，详情截图为 `live-details.png`。

## 固定来源与改动

作者仓库：[lyramakesmusic/neuron-explorer](https://github.com/lyramakesmusic/neuron-explorer/tree/ddb144e4121fbeb16ec080077dd67247e499132d)。固定提交 `ddb144e4121fbeb16ec080077dd67247e499132d`。原始归档 URL、SHA-256 和全部 43 个文件的哈希见 `source-manifest.json`。公开的六个缓存直接复用，没有重新扫描语料或重建缓存。

模型使用项目已有的官方权重：`Qwen/Qwen3.5-4B`，revision `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`，远端目录 `/data/models/Qwen3.5-4B-851bf6e`。12 个文件均重新校验大小和 SHA-256，见 `model-verification.json`。该文件中的 `model_loaded: false` 描述校验步骤本身；随后实时服务已经加载并完成推理。

仅有两处补丁：

1. `local-model-config.patch`：让服务配置读取遵循原有 `EXPLORER_MODEL`，使用固定本地权重路径。
2. `panel-collapse.patch`：将标签页按钮绑定限定为 `[data-tab]`。原版绑定覆盖了收起按钮，浏览器实际报 `setTab(undefined)` 的空值错误；修复后收起、重新打开和 Details 切换通过。

模型以 BF16 在 CUDA 运行；使用现有 Python 3.11.16 环境及依赖，精确版本见 `remote-state.json`。未升级共享环境。缺少 `causal_conv1d` 和 `flash-linear-attention`，Transformers 使用自身参考实现，日志保留在 `server-live-r01.log`；不能据此报告作者原环境的速度。

## 已验证的范围

| 检查 | 实际结果 | 证据 |
| --- | --- | --- |
| 原缓存页面、架构、布局、lens、连接、搜索 | 6 项通过，32 层、每层 9216 个 MLP 通道 | `cache-smoke-r02.json` |
| 自然文本读取 | `The sky is blue.` 返回 5 个 token 的有限激活值 | `live-smoke-r01.json` |
| 激活地图 | `32×9216` FP16，全部有限，375 个非零值 | 同上及 `verification.json` |
| 零剂量三列生成 | L14/N8949，add=0，三列相同 | `live-smoke-r01.json` |
| 非零剂量三列生成 | add=0.1 正向列首个颜色为 Red；原模型和反向列为 Blue | 同上 |
| 浏览器交互 | 三维地图渲染、缩放、通道跳转、Details、连接、面板收起及重新打开 | `ui-verification.json`、两张实时截图 |

生成提示固定为 `Name two colors.`，每列上限 12 个新 token，贪心解码。六条输出均到达该上限，只是短生成链路验收，并未完成整个“两种颜色”回答。不能把 Blue/Red 的一次变化解释成已定位某种人格或功能神经元。

保留了首次本机网络权限失败的 `cache-smoke-r01.json`；随后在允许访问本机端口的执行环境中重试成功。远端直接下载太慢，中止了本轮对应下载并保留残片；改从本机传输完整官方归档，校验一致后解压。

## 尚未复现

- 作者没有公开完整 `runs/`、`stats/`、采样输出、命名库和嵌入数据。因此历史 Examples、扫描排行与 embeddings 没有相应原始记录。
- 作者未固定公开缓存所用权重 revision，不能证明这些缓存与本次固定权重逐字节对应。
- Claude 命令行存在，但本轮未调用，认证状态和该面板未验收。
- 多轮对话、乘法干预、截图中的动态反馈控制器及人格配方未测试；未运行两篇论文的实验。
- 布局和连接沿用作者实现，是权重关系的可视化，不是已验证的因果通路。

## 重启和恢复

远端运行目录是 `/workspace/acupuncture/experiments/neuron-explorer-reproduction-v1-2026-10-26`。确认本次服务已经退出后，在该目录运行 `bash serve.sh` 即可前台启动；本机再打开 `open.command`。没有安装系统常驻服务或开机自启。

新检出仓库时，`upstream/` 和模型权重不在 Git 中：按 `source-manifest.json` 下载固定归档并核对哈希，解压至 `upstream/`，在其中依次执行 `patch -p1 < ../local-model-config.patch` 和 `patch -p1 < ../panel-collapse.patch`。使用已有模型和环境；其他机器可通过 `EXPLORER_MODEL`、`EXPLORER_PYTHON` 指定路径。`serve.sh` 会检查六个原始缓存，缺失时停止，避免误触发大规模重建。

本机只关闭隧道可执行 `ssh -S /tmp/acupuncture-neuron-explorer-8791.sock -O exit gqa-h20`。如需释放模型显存，应先检查 `runtime/live-server.pid` 对应命令确为本目录服务，再终止该进程。不要终止其他任务。

本目录的协议、启动文件、补丁、来源清单和验收证据可版本管理；第三方源码/缓存、下载、模型、环境不进入 Git。本轮没有提交或推送，也没有重新启动旧题集或修改模型权重。
