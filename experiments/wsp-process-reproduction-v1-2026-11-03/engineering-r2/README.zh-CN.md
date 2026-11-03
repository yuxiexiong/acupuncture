# WSP 工程收尾 r2：已验收，正式搜索未启动

**已授权清理完成｜2026-11-03：** [执行收据与环境复核](cleanup-r1/README.zh-CN.md)：指定缓存清理释放约 44.11 GB，当前空闲约 270 GB；161,321 个保留文件无缺失或变化，构建资料已归档，环境检查通过。正式预算模板已同步为 8/20 GPU 小时、100/150 GB 启动空闲门槛、50 GB 保留线；两端 authorized=false，**仍未启动搜索**。本条及最新启动清单覆盖下方旧预算/缺口说明，旧检查点按其历史时间理解。


> **同日资源核算纠正（后续结论优先）：** [只读清理清单与预算复算](resource-audit/REPORT.zh-CN.md)已撤回把 400/600 GB、额外 1 TB 和 24/60 GPU 小时当作默认需要的解释。当前约 226 GB 空闲，优先候选可回收约 44.07 GB，含旧 4B 导出约 52.51 GB；作者同量级负载的参考工作额度为新增 50/100 GB、粗估 4–8/10–20 GPU 小时。全部属于未执行的规划，运行配置仍关闭且本轮未改，服务器未删任何文件、未启动搜索。下文保留上一轮预算与验收历史，旧门槛须在将来正式启用前修订。


日期：2026-11-03。接续 FA-01 交接 `a47d3d8a08045a86cfca5ac0b707fab1c2c3dd4f`。本目录只完成用户授权的接口修正、编辑器接入、调度和有限工程验收；**0.8B 与 4B 的正式搜索均为 0/50**。下一阶段预算和启动条件见 [STARTUP.zh-CN.md](STARTUP.zh-CN.md)。

## 完成内容与证据

|范围|实际结果|收据|
|---|---|---|
|0.8B 接口/编辑装载/生成激活|通过；2 次短 TF + 1 次 both 短生成；194.704 GPU 设备秒|[0.8B](receipts/engineering-r2-0p8b-r1-receipt.json)|
|4B 同项验收|通过；2 次短 TF + 1 次 both 短生成；238.708 GPU 设备秒|[4B](receipts/engineering-r2-4b-r1-receipt.json)|
|Astra 完整工具链|4 回合；CPU 持久变量、原始 tokenizer API、一次短 TF、正常结束；6.773 GPU 设备秒|[集成](receipts/editor-integrated/receipt.json)|
|Astra 明确会话 ID 续接|两回合 marker 记忆通过；无 native tool 事件|[续接](receipts/editor-resume/receipt.json)|
|调度器超时/恢复|外部限时终止本内核；重启明确告知变量丢失；最终空编辑提交验证通过；0 GPU|[调度](receipts/engineering-r2-scheduler-r1-receipt.json)|
|派生 checkpoint 生命周期|CPU 从两模型保存快照重建，SHA256 与已验收 checkpoint 完全一致；自身缓存可清理，快照保留|[重建](receipts/checkpoint-rebuild.json)|
|CPU 回归|原 FA-01 3 个测试函数 + r2 8 个 unittest 通过|`test_forward_service.py`、`test_engineering.py`|

本轮记录的新增 GPU 总量 **440.184 设备秒 = 0.1223 GPU 小时**；包含模型加载、短生成及激活重放，both 按两张卡计。本轮冻结上限为 3,600 设备秒，未触及。这里的 7 次成功前向均为隔离的工程验收，不计入未来两场 50-pass 研究预算。

保留了首次注意力检查阈值错误、首次短暂 GPU_BUSY、CPU 测试文件数算错的历史：[失败清单](receipts/failed-checks.json)。没有修改 FA-01 的 F2/F3/F6/F8 容差，没有加载作者的最终 MLP 输出列补丁；合成编辑仅将第一层 `mlp.up_proj.weight[0,0]` 加 1，随后清空，独立于任何科学候选。

## 修正的接口

- TF 文件恢复 `hidden_<l>.npy`；hidden / MLP 为 float16；`token_logprobs` 为 `[B,T-1]`，列 t 预测输入 t+1；metadata 提供文件名到 shape 的映射。
- 生成 JSONL 恢复每题一行、`samples` 数组；摘要返回作者形状的 accuracy、mean_tokens、failure counts、paired 字段。
- 生成激活恢复四个 stacked 数组；`mlp=true` 只读请求层中合法的模块索引，不再默认导出所有 MLP。
- 当前 Transformers 的 attention tuple 只含完整注意力模块，按 `config/layer.block_type` 映射回模块索引；0.8B 第 23 层、4B 第 31 层实际验收通过。
- 最终 hidden 使用 HF post-final-norm；`tok` 改为 `tokenizers.Tokenizer`，`encode` 返回 `.ids/.offsets`，`decode` 保持原 API；`eval_prompt_format.txt` 从实际冻结 chat template 渲染出精确 PREFIX/SUFFIX。
- observer 原始 token IDs、checkpoint 哈希、完整输出与 capped editor 输出分开归档。编辑快照在每个前向前重新验证，禁止直接写文件绕过约束。

## 编辑器和调度方式

编辑器是 **gpt-6-astra，reasoning effort=max**。本次通过本机 Codex CLI 0.166.0-alpha.5.1 和现有 ChatGPT 登录调用，不要求新建 API key，也没有把登录凭证复制到 H20。非交互调用与指定会话续接依据[官方说明](https://developers.openai.com/codex/noninteractive)，具体实际参数、输入、输出和 usage 在收据中。

本机 controller → SSH JSONL broker → H20 bubblewrap CPU 内核 / observer 前向服务。编辑器没有 native shell、web、apps、插件或记忆工具；初始 cwd 是新建空目录，项目说明不注入。CPU 内核没有网络和 GPU，只挂载固定模型、practice 和独立 /work；observer 的作者日志、验收结果、候选补丁和凭证不挂载。这不能排除模型已有预训练知识，也不声称隐藏系统上下文与作者环境完全一致。

按作者公开 p50c 输入记录：第 29 回合加入 EXPLAIN EVERY STEP；第 46/51 回合注入 notice 001/002；每 40 回合换新会话，只带任务、当前预算/文件清单、本人 notes 最后 8,000 字符和上一工具结果。4B 的 notice 002 仅适配完整注意力层号。003/004 未在 158 份输入中找到完整原文，不擅自注入；失败分类从开始使用修正定义。四份 notice 仅保留为 observer 来源材料。

调度器保存 action ID、输入哈希、快照、输出和状态：成功前向才扣 50-pass；失败和 timeout 仍计资源；已提交响应可幂等读取，未完成动作必须核查，不能盲目重跑。只有空闲卡才使用，不终止他人任务。CPU 外部限时、GPU 总设备秒/单次限时、磁盘余量和尝试数均可停止运行。50 次成功后仍允许 Python 做最终选择；无代码最终回复触发最后一次编辑快照验证，不自动跑隐藏 benchmark。

## 已知边界与版本覆盖

作者 server 未公开；这是一份接口重建，不是源码原封复用。已复用其公开评分代码、practice、任务和 notices。generation 激活采用精确生成 token IDs 的 HF 重读，作者是否先重分词未知；最终 hidden 的 post-norm 约定有 HF 与作者日志尺度支持，但不是其 server 源码证明。种子哈希、validator 容差、失败恢复及 GPU 调度也属于明示的重建实现。

FA-01 数值收据继续保留，特别是 4B F8=0.014622 接近 0.02 门限；本轮不把短接口验收升级为长输出数值等价、数学能力复现或 WSP 机制发现。原 tokenizer 的 regex warning 未被自动修补，以免改变冻结的模型输入协议。

GPU 测量对应 receipt 内的代码哈希。之后的最终收尾仅改变 observer 的私有缓存路径/清理、磁盘门禁和最终提交校验；由 CPU checkpoint 重建和调度测试补验，没有声称对这些新文件哈希重跑了所有 GPU 测量。0.8B 的 tokenizer 更新由后续 Astra 集成验收覆盖，4B 直接在更新后验收。

## 原始材料

[压缩原始证据](receipts/wsp-engineering-r2-evidence.tgz)约 1.01 MB，包含实际 .npy、JSONL、日志、失败、输入、状态和首版已测源码包；[逐文件清单](receipts/wsp-engineering-r2-evidence-manifest.json)含 214 项及 SHA256。约 218 MB 的合成编辑数组未放 Git，完整保留在服务器对应 snapshot 路径；生成它们的代码与所有哈希已归档，可 CPU 重建。原始模型、虚拟环境与缓存不入 Git。

验收合同及同一助手自查：[ACCEPTANCE.zh-CN.md](ACCEPTANCE.zh-CN.md)。逻辑审查、工程验收、正式授权、科学结果四者分别记录；目前只有前两项完成。
