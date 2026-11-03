# WSP 双模型过程复现：工程准备与验收

2026-11-03，准备阶段检查点。用户已要求依次推进代办，并选择等现有任务结束后使用空闲 GPU。正式自主搜索、最终评测均未启动。

实验设计沿用 [v1 完整计划](../../docs/wsp-process-reproduction-v1-2026-11-03.zh-CN.md)、[v1 自查](../../docs/wsp-process-reproduction-self-check-v1-2026-11-03.zh-CN.md)及 [0.8B＋4B v2 增补](../../docs/wsp-process-reproduction-0p8b-4b-v2-2026-11-03.zh-CN.md)。本目录记录实现与工程证据，不把接口测试当科学结果。

## 已完成并有收据的项目

| 项目 | 实测结果 | 证据 |
|---|---|---|
| 原作者编辑器可用性 | 当前 ChatGPT 登录下，`gpt-6-astra`、`max` 返回指定标记；输入 6448 tokens、输出 29 tokens | [编辑器事件](receipts/editor-probe.events.jsonl)、[stderr](receipts/editor-probe.stderr.txt) |
| 4B 原始资源完整性 | 12 个正式文件重新计算 SHA256，与历史固定 revision 清单一致 | [当前哈希复验](receipts/4b-current-hash-receipt.json) |
| 4B 文本导出 | 426 个文本张量保持原名、形状、dtype，导出后逐张量字节哈希全部一致；排除视觉及 MTP 权重 | [逐张量收据](receipts/text_export_receipt.json) |
| CPU 沙箱基本接口 | 无网络、无 GPU、模型只读、观察端不可见；变量持久；冻结张量与整张量倍乘拒绝；编辑保存/撤销通过 | [成功收据](receipts/sandbox-probe.json) |
| 沙箱失败历史 | 旧 bubblewrap 不支持 `--clearenv`；随后发现旧虚拟环境实际 Python 位于 `amic-q3`，修正环境清理与挂载后通过 | [第一次](receipts/sandbox-probe.attempt1.json)、[第二次](receipts/sandbox-probe.attempt2.json) |

编辑器测试仅证明当前模型标识和档位可调用，不证明剩余额度、作者认证方式、40 轮续接或完整上下文隔离。stderr 中的实验特性提示、Code Mode 禁用提示及本地索引警告保留，不隐去。

CPU 沙箱通过的是所列四组有限测试，不是完整安全/超时/恢复验收。所用 CPU 环境是只读复用的 `.venv-bench`；独立 WSP 推理环境完成后仍需对应版本验收。`sandbox_kernel.py` 是待集成原型，不能直接当成完整运行器启动搜索。

## 正在推进与剩余代办

1. **0.8B 原始资产**：固定 revision `2fc06364715b967f1860aea9cf38778875588b17`；模型文件下载进行中，尚不能声称完整权重核验或导出完成。练习集已经通过固定 Git blob SHA1 校验，经本机中转解除服务器访问 GitHub 的低速问题。
2. **独立环境**：`/workspace/acupuncture/.venv-wsp`；数学评分依赖已装。固定 `vllm==0.33.0` 安装尚未完成；`llguidance` 在当前系统没有可用 wheel，第一次构建因 Rust 下载超时失败，专用 Rust 工具链安装后正在处理依赖构建。旧实验环境及系统驱动未升级。
3. **GPU 兼容性**：服务器 Debian 10 / glibc 2.28、驱动 535.161.08。仅在 WSP 目录解包 NVIDIA `cuda-compat-13-4_615.71.10-1`；`cuInit=0`、CUDA driver API version 13040。此为初始化通过，尚不是 vLLM/Qwen 数值验收。
4. **双模型提示**：`freeze_prompts.py` 在任何新搜索前冻结原作者 0.8B 提示；4B 仅替换架构段落及两处 residual 索引上界，生成 diff 与 SHA256，不加入已知补丁、候选层号或本次结果。
5. **评分**：`scorer_probe.py` 测试原作者 `extract/score/math-verify` 的 5 个确定性案例。仅排除未公开 `mcqa` 的导入；该缺失函数保持不可用，不伪造循环诊断结果。完整评测导入、IFEval、多选数据和授权仍待准备。
6. **完整运行器**：仍需实现/验收编辑器续接、外部预算账本、硬超时与进程回收、候选快照及前向前复验、generation/teacher-forced/内部张量返回、原版与空编辑一致性、完整失败日志与断点恢复。原作者未公开这些服务，本项目自建部分必须单列。
7. **资源与正式执行**：等其他任务结束再使用空闲卡。按 v2 每模型至多 0.5 GPUh 做工程验收与吞吐测量；正式两轮搜索和终验的时长、存储、编辑器消耗仍需据实冻结。没有因初始化 CUDA 就开始科学搜索。

## 实现与资产位置

冻结提示来自 [RikiyaT/lm_understand-logs](https://github.com/RikiyaT/lm_understand-logs/tree/4d09ba6d6a7e891dd8063974dfe81b3d78e3494f/exp8_math)，遵循作者 [CC BY 4.0 声明](https://github.com/RikiyaT/lm_understand-logs/blob/4d09ba6d6a7e891dd8063974dfe81b3d78e3494f/LICENSE)。0.8B 初始提示原样复制；4B 改动见 `frozen-prompts/4b-prompt.diff`。原作者 Python 脚本为 MIT；第三方题目保留各自许可。来源、改动与本项目新代码分列。

- `upstream_manifest.json`：固定作者提交与 25 个公开文件的 Git blob SHA1；不含最终补丁。
- `model_manifest.json`：此前实际读取的 0.8B 固定版本文件大小和哈希。镜像元数据随后返回 403，下载器改用此冻结清单；镜像 `master` 只有在文件与固定哈希一致时才被接受。
- `prepare_assets.py`：下载、总时限/低速退出、镜像回退及逐文件校验。可复用 4B 中字节完全相同的词表文件，不把 4B 模板或 config 覆盖给 0.8B。
- `export_text.py`：只提取原始文本张量并复验，无权重编辑；不会覆盖已经存在的导出目录。
- `sandbox_kernel.py` / `sandbox_probe.py`：持久 CPU 接口及有限隔离/编辑测试。
- `scorer_probe.py` / `freeze_prompts.py`：数学评分验收与双模型输入冻结。
- 服务器外部资产根：`/workspace/acupuncture/external/wsp/`。模型、环境、第三方大文件及编译缓存不提交 Git。

`save_edit` 对整张量倍乘使用 `rtol=1e-5, atol=1e-7` 的显式检测；作者没有公开该校验器的数值容差。必须将此标为重建实现差异，前向服务还需对直接写入的 `.npy` 再做独立校验，不能依靠搜索者自觉调用 `save_edit`。

## 未发生的事项

没有复制或应用作者最终 MLP 修正；没有把 0.8B 的搜索轨迹传给 4B；没有生成新的 Qwen 数学回答；没有形成 WSP 效果或机制结论。当前只有资产、CPU 工程及一次编辑器可用性证据。
