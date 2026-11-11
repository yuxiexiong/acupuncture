# 142．VLM数据v4：真实处理器验收

[返回总时间线](../README.zh-CN.md)

**时间定位**：版本/记录日期 2026-11-05；未从所选收据确定完整运行起止，不据目录名补写时刻。

**当时的目的与设计**

固定Qwen3-VL-4B模型/处理器来源，按真实缩放检查P0、B、C图像可辨认性。

**实际过程、结果与后来更正**

474张完成原图/处理器图对照，0因缩放排除；下载12文件并校验。未实例化模型、未前向，仍是输入工程验收。

**来源身份**：`wsp-vlm-processor-prep-v4-2026-11-05`；本章主体来源提交 `2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274`。下方原文中的状态是各文件写作时的状态，不能把早期“尚未运行”覆盖后期正式收据，也不能将后期结果倒填进早期设计。


## 原设计、执行过程、结果与更正全文

以下按“设计与题目 → 工程/执行记录 → 结果/更正 → 其他历史说明”组织；同类内没有可靠时间时保留路径顺序，不冒充严格先后。正文未删段；仅为本章节重排标题层级、把相对链接指向固定提交。原始字节另外完整保存。

### 原件 1：v4 准备工作自查

原路径：`experiments/wsp-vlm-processor-prep-v4-2026-11-05/SELF_CHECK.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-processor-prep-v4-2026-11-05/SELF_CHECK.zh-CN.md) · [单独阅读副本](../library/17612ec2e2f237d2.md)；SHA-256：`17612ec2e2f237d21c64203aa0ce13d3aa54351dd3fbc460b111a8db8c4f9066`。

---

#### v4 准备工作自查

使用 `docs/experiment-design-self-check.zh-CN.md` v1。同一助手自查，非独立审查。本轮是已批准方案的工程准备，不新增科学设计。

##### 设计卡与版本差异

- 主线：研究者 AI 依据目标 VLM 的具体失效反馈，定位并搜索稀疏权重修补；先确认 B/C 行为失效。
- 本轮：固定模型资产是否完整，实际处理器是否保留可审核的视觉输入，P0 还有何工程阻碍。
- 增量：v3 只有离线输入包/运行器；v4 增加真实固定处理器 CPU 结果、474 张缩放图审核、64 条真实序列化以及资产哈希验收。没有新增模型行为认识。
- 依据：v3 冻结运行器/队列、v2 通过组、官方固定模型元数据、实际文件与 CPU 日志；不以截图或旧“已准备”口头描述替代当前回执。
- 操作：下载固定 revision 文件；仅实例化 processor/tokenizer，调用 CPU resize/图像处理与 chat template。无模型、层、hook、剂量或权重编辑。
- 估计对象：文件完整性、图像处理一致性、源图到缩放图的可辨认性变化；不估计准确率或因果机制。
- 判读：哈希或网格失败则工程失败；缩放导致关键对象/关系不可辨认则标记并停止该输入使用，不凑组；本次未观察到该失败。源数据原有质量限制继续记录。
- 成本/退出：12 文件约 8.89 GB 下载、CPU 处理和本地视觉审核；0 次模型调用、0 GPU 计算。完成回执即止，不自动进入 P0。

##### C01–C14

| 项 | 判定及理由 |
|---|---|
| C01 | 通过：WSP 问题和 B/C 任务未更换；准备只服务后续行为筛查。 |
| C02 | 通过（工程）：消除真实处理器与模拟输入不一致风险；不包装为科学发现。 |
| C03 | 通过：复用 v3 处理器路径，官方固定元数据与逐文件校验，来源见 README。 |
| C04 | 通过：面对暗图、遮挡、水印、源裁切等反例；可辨认不推出模型会答对。 |
| C05 | 通过：只处理输入图片/文本，禁止权重加载入口；没有干预模型内部。 |
| C06 | 通过：模型 revision、像素预算、队列/划分均不改；处理器实际尺寸取整如实记录。 |
| C07 | 不适用：未构造模型内部混合反事实或共享状态操作。 |
| C08 | 通过：不由图像/哈希成功推断信息存量、因果位置或稀疏可修复性。 |
| C09 | 不适用科学假设比较：这是输入验收，不用工程成功选择 WSP 机制。 |
| C10 | 通过：64 条“输入序列化通过”和“推理预检通过”严格区分，后者仍未运行。 |
| C11 | 通过：网络、目录、GPU 环境问题归工程；不会算成任务失败或 WSP 阴性。 |
| C12 | 通过：CPU 与文件流式校验足够，未新增 GPU 测量。 |
| C13 | 通过：474 图清单/79 页索引/逐图记录/最终回执绑定哈希；同一助手审核；数据未重新抽样。 |
| C14 | 通过：资产与可辨认性准备完成，但 GPU 软件兼容与硬超时缺口决定下一步工程工作；不跳入修补。 |

相关历史错误：E02（不预选两层）；E10/E11（输入正确不等于回答正确/信息已被使用）；E16（工程失败不冒充科学阴性）；E22（474 图不称 474 个独立科学组；B146/C160 保持）；E23（自查不称独立，下载不称加载）；E25（不加额外模型实验）。其他内部缓存干预错误不适用于本轮无模型准备。

##### 反方检查与修正

1. **拼图看起来清楚，真实模型看到的未必相同。** 预览使用 v3 真处理器 resize，另做图像处理核对网格；64 条输入还核对了真实 image token 数；另对全部 474 张预览重新进行真实归一化/分块，得到与原图处理结果完全相同的像素张量。此证据不保证视觉编码器提取成功，不把预览作为推理结果。
2. **源图本来模糊，审核全部通过会掩盖问题。** 回执的通过只表示未观察到缩放新增的任务相关可辨认性损伤。保留原图质量限制，不重写前轮标签审查为“完美”。
3. **镜像提供了错误版本。** 使用独立从官方站获取的固定 revision 元数据，逐文件检查 Git blob/LFS 哈希与大小；同名/同 revision 字符串本身不够。仅校验字节，不读取权重张量。
4. **处理器能运行就称 GPU 环境好了。** 已修正为 CPU 通过；CUDA13/535 组合列为明确待解决兼容问题，未通过 CUDA 实测，也未宣称实测报错。
5. **新环境可能改变预览，旧回执仍会被复用。** README 要求软件栈变化后复核处理器输出/哈希；v3 执行器已有 processor SHA 比较，不能跳过。
6. **max_time 会卡在一次 forward，预算不是硬限制。** 保留为 P0 前未完成工程项；本轮没有因下载完成而声称可直接开跑。

结论：准备工作逻辑与 CPU 输入/视觉验收通过；不新增科学设计结论。模型文件完整性以 download_manifest 为证，实际 GPU 运行验收未完成，P0 未授权也未执行。新增材料不足以证明候选痛点存在或 WSP 有效。

---

### 原件 2：WSP VLM 固定资产与真实处理器验收 v4

原路径：`experiments/wsp-vlm-processor-prep-v4-2026-11-05/README.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-processor-prep-v4-2026-11-05/README.zh-CN.md) · [单独阅读副本](../library/cb6ef3a639bbc1e7.md)；SHA-256：`cb6ef3a639bbc1e7a62c6865699f4c37644bbb088b3784572b88e9cee51cd082`。

---

#### WSP VLM 固定资产与真实处理器验收 v4

日期：2026-11-05。性质：下载、CPU 输入处理和图片审核；不是模型实验。承接 [v3 输入包与运行器](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-screen-ready-v3-2026-11-05/README.zh-CN.md)。

##### 本轮边界

用户授权下载固定版本模型和处理器、生成真实缩放图、完成可辨认性审核。没有实例化模型、反序列化权重、执行 forward/generate 或进行 GPU 计算。64 条 P0 仅完成输入序列化，**没有 64 条模型回答，也没有 P0 推理验收通过结论**。

WSP 的位置不变：先用 B/C 行为筛查确认具体失效，再由研究者 AI 根据反馈定位并搜索稀疏权重修补。当前下载和图像验收只是保证输入可信，不提供失效机制或可修补性的证据，不预先指定两个层。

##### 固定资产

- 模型与处理器：`Qwen/Qwen3-VL-4B-Instruct`。
- 固定 revision：`ebb281ec70b05090aa6165b016eac8ec08e71b17`。
- 官方元数据：[固定 revision API](https://huggingface.co/api/models/Qwen/Qwen3-VL-4B-Instruct/revision/ebb281ec70b05090aa6165b016eac8ec08e71b17?blobs=true)，原件见 [upstream_model_info.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-processor-prep-v4-2026-11-05/audit/upstream_model_info.json)。
- 远端官方站连接失败后，改用 `hf-mirror.com` 获取同 revision 文件；镜像文件的大小、LFS SHA256 或 Git blob SHA1 必须匹配从官方站取得的元数据。下载脚本流式读取文件字节校验，不反序列化权重。
- 所需 12 个文件共 **8,887,284,080 字节**，包括两个 safetensors 分片和完整配置、分词器、模板与处理器文件。逐文件完成状态和哈希以 [download_manifest.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-processor-prep-v4-2026-11-05/audit/download_manifest.json) 为准；README 与 `.gitattributes` 不属于运行依赖。
- 资产放在 `gqa-h20:/workspace/acupuncture/external/wsp-vlm-model-cache/hub/models--Qwen--Qwen3-VL-4B-Instruct/snapshots/ebb281ec70b05090aa6165b016eac8ec08e71b17`，权重没有复制到本地 Mac，也不进 Git。

##### 真实处理器和可辨认性审核

使用原 v3 `runner.processor_audit` 和 `AutoProcessor`，`local_files_only=True`，像素范围仍为 65,536–1,048,576，patch=16、merge=2。预览调用真实图像处理器的 resize；并对每张原图实际执行图像处理，核对输出 `image_grid_thw` 与预览尺寸。拼图仅用于查看，不替代模型输入。

| 范围 | 图片数 | 审核结果 |
|---|---:|---|
| P0 独立工程夹具 | 8 | 缩放后颜色、对象和相对位置保留 |
| B：146 个冻结合格组 | 146 | 未观察到缩放新增的对象丢失、裁切或关系不可辨认 |
| C：160 个冻结组，原图/反事实图 | 320 | 两个对象和大小关系仍可辨认，关系翻转保留 |
| 合计 | **474** | **474 张完成对照；0 张因本轮缩放排除** |

同一助手用 `view_image` 逐页检查全部 79 页原图/处理器图对照。不是独立人工复核。407 张尺寸发生变化；C 全部从 350×300 调整为 352×288。图像视觉 token 范围为 80–768。原图与预览的 SHA256、尺寸、网格和像素预算全部离线核对通过。另用真实处理器比较“原图正常预处理”与“预览跳过缩放后预处理”：**474/474 个像素张量逐项完全一致，最大绝对差为 0**，见 [像素一致性回执](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-processor-prep-v4-2026-11-05/audit/pixel_equivalence.json) 和 [日志](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-processor-prep-v4-2026-11-05/audit/pixel_equivalence.log)。

B 部分原图偏暗、遮挡或目标较小；C 存在抠图、源图裁切、水印和合成风格。这些源数据限制仍在，不是本轮缩放新增的问题。本次审核不重判已冻结标签，不保证模型能识别，更不证明 WSP 能修复。

- [真实处理器原始清单](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-processor-prep-v4-2026-11-05/audit/processor_manifest.json)：保留生成时的“尚需视觉审核”状态，完成状态由后续审核回执承接。
- [逐图审核](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-processor-prep-v4-2026-11-05/audit/visual_review.jsonl)、[79 页索引与哈希](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-processor-prep-v4-2026-11-05/audit/review_pages.json)、[最终审核回执](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-processor-prep-v4-2026-11-05/audit/processor_review.json)。
- [CPU 输入检查回执](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-processor-prep-v4-2026-11-05/audit/processor_receipt.json)：64 条 P0 全部通过真实模板、分词与图像占位符检查，48 条带图、16 条无图；输入长度 31–843 token。CPU 处理阶段约 20.61 秒，不含下载和视觉审核。
- [处理日志](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-processor-prep-v4-2026-11-05/audit/processor.log)、[环境元数据](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-processor-prep-v4-2026-11-05/audit/environment_receipt.json)。

预览文件约 83 MB（传输压缩包），保存在远端和本地仓库的 `external/wsp-vlm-processor-prep-v4-2026-11-05/processor_audit/`。本地 `review_sheets/` 保存全部对照页。批量第三方图片不进 Git；清单、哈希和生成代码入库。审核回执也已放入远端该 external 目录，且核对了它与 `processor_audit/manifest.json` 的绑定。

##### 64 条 P0 还缺什么

**数据、固定模型文件、处理器输入与缩放图审核完成后，P0 尚不能直接执行。**

1. **GPU 软件栈兼容性未解决。** 本次 CPU 导入记录为 `torch 2.14.0+cu130`，CUDA 构建 13.0；`nvidia-smi` 驱动为 535.161.08。按 [NVIDIA 兼容性表](https://docs.nvidia.com/deploy/cuda-compatibility/minor-version-compatibility.html)，CUDA 13.x 的通常最低驱动是 580。本次未发现 `/usr/local/cuda*/compat` 或 CUDA 的 `LD_LIBRARY_PATH` 配置。未做 CUDA 初始化/运行测试，不能声称已实测 GPU 报错；但当前配置不能签为可运行。下一步应准备与现有驱动适配的隔离运行环境，或协调驱动升级；本轮未改变它们。若软件包变化，需要重新核对处理器输出/哈希，不能直接继承此回执。
2. **外部硬超时保护尚未落地。** v3 内部有累计预算和生成时间检查，但一次阻塞的 forward 不能靠内部检查强制结束。P0 启动前需补齐进程级硬超时、停止后的状态与成本对账。不得把“有 max_time”当成硬上限保障。
3. **模型加载与 P0 推理尚未授权。** 本轮授权到准备和处理器审核为止；没有启动命令被执行。届时也需刷新显存/设备占用。此次只读快照显示两张 H20 各 97,871 MiB、已用 3 MiB，不代表未来资源预留。

BF16 模型能否正确加载、真实生成格式、EOS/截断、显存峰值、吞吐和评分链路，是未来 P0 要测的项目，目前均未验收。它们不是要求先跑另一套模型实验的额外前置条件。P0 简单夹具的吞吐也不能保证正式图像任务全程耗时，原累计预算仍须执行。

本轮没有新增科学样本、改变 B=146/C=160、开发/留出划分、统计规则或 GPU 预算；没有生成 P0_acceptance.json。WSP 搜索尚未开始。

##### 复用方式与工程记录

`download_assets.py` 负责固定下载与字节校验；`prepare_processor.py` 负责 CPU 真实处理器调用，显式禁止常见权重加载入口；`make_review_sheets.py` 在本地从原图和真实预览生成对照页；`verify_preview_pixels.py` 在 CPU 核对实际像素张量一致性。[源码哈希](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-processor-prep-v4-2026-11-05/audit/source_hashes.json) 固定实际使用的脚本。未来执行需显式使用上述专用 `HF_HUB_CACHE`，不能误用默认空缓存。

首次远端官方站网络不可达；切换镜像后，因空 audit 目录未传输曾有一次日志输出目录缺失，建目录后重新启动。两者均发生于模型加载前，属于准备过程失败，不算科学阴性。最终下载和处理日志保留；没有用重试结果冒充模型实验重复性。

[本轮自查](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-processor-prep-v4-2026-11-05/SELF_CHECK.zh-CN.md)。

---


## 时间、运行与停止收据索引

下面是所收集JSON的原有时间字段与状态，不把预计结束时间当实际完成时间。未列时间的文件仍有原件链接。完整JSON全部保存在原文归档，不能以此索引中的标量代替完整嵌套内容。

| 原件 | 原记录状态/阶段 | 原时间字段（原时区） |
|---|---|---|
| [audit/environment_receipt.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-processor-prep-v4-2026-11-05/audit/environment_receipt.json) | {"model_calls": 0} | {"recorded_at_utc": "2026-11-04T22:20:03.647616+00:00"} |
| [audit/processor_receipt.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-processor-prep-v4-2026-11-05/audit/processor_receipt.json) | {"status": "processor_only_not_inference", "model_calls": 0} | {} |
| [audit/visual_review_progress.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-processor-prep-v4-2026-11-05/audit/visual_review_progress.json) | {} | {} |

## 全部原始资产入口

本目录在固定提交下共有20个跟踪文件，包含代码、原回答、失败、收据和压缩证据；文件数不是样本数。[逐文件完整账本](../assets/142-wsp-vlm-processor-prep-v4-2026-11-05.tsv) · [原目录](https://github.com/yuxiexiong/acupuncture/tree/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-processor-prep-v4-2026-11-05)。未复制模型权重、环境或凭据。
