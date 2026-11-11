# 127．VLM运行通道v5

[返回总时间线](../README.zh-CN.md)

**时间定位**：版本/记录日期 2026-11-05；未从所选收据确定完整运行起止，不据目录名补写时刻。

**当时的目的与设计**

准备本地研究者到服务器的持久通道、隔离工具和请求回执。

**实际过程、结果与后来更正**

本章完整保存CPU/通道验收与实际启动边界；该准备版本本身不提供行为修复分数，真实筛查在下一章。

**来源身份**：`wsp-vlm-channel-prep-v5-2026-11-05`；本章主体来源提交 `2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274`。下方原文中的状态是各文件写作时的状态，不能把早期“尚未运行”覆盖后期正式收据，也不能将后期结果倒填进早期设计。


## 原设计、执行过程、结果与更正全文

以下按“设计与题目 → 工程/执行记录 → 结果/更正 → 其他历史说明”组织；同类内没有可靠时间时保留路径顺序，不冒充严格先后。正文未删段；仅为本章节重排标题层级、把相对链接指向固定提交。原始字节另外完整保存。

### 原件 1：v5 工程准备自查

原路径：`experiments/wsp-vlm-channel-prep-v5-2026-11-05/SELF_CHECK.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-channel-prep-v5-2026-11-05/SELF_CHECK.zh-CN.md) · [单独阅读副本](../library/884452f1834f83bf.md)；SHA-256：`884452f1834f83bf5f0bd5777bc67647e153f019434a9fb329cff38557434193`。

---

#### v5 工程准备自查

依据 `docs/experiment-design-self-check.zh-CN.md`。同一助手自查，不是独立审查。本轮不新增科学设计；不涉及GPU/模型运行授权。

设计卡：主问题仍是研究者AI能否依据具体VLM失败定位并进行稀疏权重修补。当前仅准备B/C行为筛查的运行通道。v4已验证资产和处理器但遗留CUDA主版本冲突、软超时；v5改用现有CUDA12.4栈并重新验证输入，增加进程级期限及写前尝试记账。评价对象是输入一致性、异常退出、预算记录；不估计准确率、信息可读性或WSP效果。沿用B146/C160、固定revision和队列。CPU检查失败就修复并保留日志，未知GPU行为留给未来P0，不用追加实验掩盖。

| 项 | 判定和理由 |
|---|---|
| C01 | 通过：主线及候选任务稳定，工程准备服务既有筛查。 |
| C02 | 通过（工程）：消除已有运行障碍，不把模拟测试包装为科学增量。 |
| C03 | 通过：使用当前环境元数据、实际CPU张量与官方驱动兼容表；类导入不等于模型执行。 |
| C04 | 通过：允许GPU运行仍失败；明确兼容表PTX限制与源图原有质量问题。 |
| C05 | 通过：不实例化模型、不读入权重张量；CPU处理器与模拟子进程有边界。 |
| C06 | 通过：只变工程软件栈；固定模型、图片、提示、划分与生成设置不变；新旧输入逐字节核对。 |
| C07 | 不适用：没有内部状态或反事实激活拼接。 |
| C08 | 通过：输入等价不推出模型输出等价；没有宣称GPU或WSP有效。 |
| C09 | 不适用科学竞争假设：工程接受标准是精确一致及失败路径正确，不据此选择机制。 |
| C10 | 通过：明确64条输入预检与64条真实推理预检之别；后者0/64。 |
| C11 | 通过：进程异常不计答错；写前日志把中断的在途调用计入尝试；旧running记录阻止继续。 |
| C12 | 通过：复用现有环境，无重复下载或新GPU工作，原预算不扩大。 |
| C13 | 通过：保留初次路径错误日志、成功回执与历史v4；测试均标合成/离线；自查不称独立。 |
| C14 | 通过：CPU准备结束后停在P0执行边界；资源窗口及真实GPU表现仍待核验。 |

相关历史错误：E02不预选两层；E10/E11不把可辨认/可序列化当作已调用内部信息；E16工程失败不算科学阴性；E22图像条数不当独立组数；E23同一助手自查不称独立；E25不因通道准备自动开始模型实验。

反方检查：
1. **只是绕开版本报错，没有验证新栈。** 已做CPU类导入、474图处理器/预览像素核对、64条模板/token一致性；GPU模型行为仍标未验收，不称全面兼容。
2. **共享环境被其他任务改了，回执仍会放行。** 不修改该环境；记录真实Python来源及8个关键包；运行器加载前检查版本和CUDA构建，变化即停。未做容器级不可变封装，因此不称完全隔离环境。
3. **生成内卡住，max_time无效。** 外部进程监督器终止工作进程组；模拟忽略TERM验证KILL路径，写前日志记录在途尝试。用户态进程不提供对机器断电/内核挂死的实时保证。
4. **父进程失联后模型仍跑。** Linux添加父进程死亡信号；异常未闭合receipt仍禁止后续自动运行。此保护不替代异常耗时核账。
5. **数据集、统计接口被顺手改动。** v5仍调用v3冻结队列；5个队列校验，原12项回归通过。科学方案、评分统计不改。
6. **审核只看resize，不是实际模型输入。** 新栈所有474图实际像素张量与对应预览处理结果完全相同；同时新旧manifest和64输入相同。这只支持输入工程验收。

结论：本轮无模型工程准备通过。GPU实测、64条P0输出/吞吐和后续正式实验仍未完成。没有新科学设计或科学结果，也不以本自查授权开跑。

---

### 原件 2：B/C 运行通道准备 v5

原路径：`experiments/wsp-vlm-channel-prep-v5-2026-11-05/README.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-channel-prep-v5-2026-11-05/README.zh-CN.md) · [单独阅读副本](../library/6a24fc8715f930e7.md)；SHA-256：`6a24fc8715f930e741f451b337931e244dfadb7bdcdc06078153c7694951ddb8`。

---

#### B/C 运行通道准备 v5

日期：2026-11-05。结论：**不涉及模型执行的准备已完成；还差真实 GPU/模型的 64 条 P0 工程预检，不能称已完成端到端验收。** 本轮没有加载模型权重，没有 forward/generate，没有 GPU 计算，也没有开始 B/C 行为实验或 WSP 修补。

##### 距离开跑还差什么

| 项目 | 当前状态 | 仍需完成 / 工作量 |
|---|---|---|
| 固定模型与处理器资产 | v4 已下载并按官方哈希核对，revision `ebb281ec70b05090aa6165b016eac8ec08e71b17`；约 8.89 GB | 无需重下；执行时再次核对文件和版本 |
| B/C 数据、输入包、评分与统计 | B146 独立组、C160 独立组；沿用 v3 固定划分、改写、队列及标签 | 无需补题；不改研究方案 |
| 缩放图可辨认性 | v4 已审474图；v5生成结果、网格、processor SHA和PNG哈希逐字节一致 | 已继承精确绑定的审核；不是重新宣称独立审核 |
| 可用软件栈 | 改为只读复用 `.venv-bench`：torch 2.6.0+cu124 / torchvision 0.21.0+cu124 / transformers 5.20.2；类导入成功 | CUDA12.4符合当前535驱动的最低版本范围；实际GPU执行仍未测 |
| 处理器/模板等价性 | 474图像素张量核对全相同，64条输入序列化与v4一致 | CPU验收完成 |
| 超时与中断记账 | 新增进程监督、进程组终止、Linux父进程死亡保护、调用前持久化attempts日志 | 模拟测试通过；真实GPU挂起未测试 |
| 离线回归 | 6项新通道测试＋12项既有测试；全部5个队列哈希/图像核验通过 | 已完成；均为合成/CPU结果 |
| GPU资源窗口 | 开始核查时两卡各占约9–10GB；交付前快照均仅3MiB，见inventory；资源未预留 | P0前只读复查，并选定一张卡；数分钟，不承诺资源立即可用 |
| 真实端到端P0 | **0/64执行**，不存在P0_acceptance.json | 后续明确授权后，1次加载＋64条工程输入；检查BF16/SDPA、显存、EOS/截断、输出与评分接口、实际吞吐 |
| 正式B/C筛查 | 未执行 | P0通过、吞吐预算可行并确认执行范围后才开展；本轮不展开科学计划 |

工程准备已消除已知CUDA主版本不匹配和软超时两项代码缺口。**没有依据给出“再过几分钟一定能跑完”的模型运行时间**：64条预检就是用来实测吞吐、检验余下7568条正式请求能否落入总预算。保留累计12 GPU小时、7888次尝试上限（含64预检及256恢复预留）；不追加额度，不自动重试。

##### 本轮具体变更

v5的 `runner.py` 是v3运行器的版本化副本，只修改环境锁、调用前attempt日志、原子receipt写入和受监督启动要求。数据仍读v3冻结队列。没有改模型、dtype、SDPA、greedy、128输出上限、像素预算或科学统计判据。

`launch.py` 是后续唯一推荐执行入口。默认只做CPU输入校验；显式 `--execute` 才能进入模型工作进程。监督器先检查累计时间，保留5秒退出余量，对整个工作进程组施加期限，TERM后2秒仍不退出则KILL；中断的在途请求仍计一次尝试。加载与异常耗时记入receipt，不把基础设施错误算答错。已有running回执会阻止继续，不悄悄抹掉或重新跑。Linux监督器死亡会杀死其模型子进程，未闭合回执仍须显式核账后恢复；断电/内核不可中断状态不能靠用户态脚本提供实时保证。

环境没有安装/卸载任何包，也没有改共享环境。`.venv-bench`实际Python路径和8个关键包版本见 `audit/environment_lock.json`；执行前逐项检查，变化即停止。复用现有环境避免修改正在服务其他任务的软件。新栈的GPU数值结果尚不存在，不能声称与旧CUDA13栈的模型输出等价。

CPU验收首次在最后附加审核文件时发现远端v4的审核文件实际位于external目录，保留 `audit/processor.log` 的原始失败日志；修正为从真实位置读取并以manifest SHA绑定，另存 `audit/equivalence.log` 成功回执。该错误发生在CPU图片和序列化完成之后，未产生任何模型调用。

##### 使用位置与边界

服务器：`gqa-h20`，仓库 `/workspace/acupuncture`。处理器审查与将来的共享累计run目录：
`external/wsp-vlm-channel-prep-v5-2026-11-05/`。

已执行的离线入口（无 `--execute`）：

```bash
/workspace/acupuncture/.venv-bench/bin/python \
  /workspace/acupuncture/experiments/wsp-vlm-channel-prep-v5-2026-11-05/launch.py \
  --stage P0 --out /tmp/wsp_P0_dry.json
```

后续授权后才运行的P0入口（本轮未执行；CUDA_VISIBLE_DEVICES的编号必须按当时资源确认）：

```bash
CUDA_VISIBLE_DEVICES=0 /workspace/acupuncture/.venv-bench/bin/python \
  /workspace/acupuncture/experiments/wsp-vlm-channel-prep-v5-2026-11-05/launch.py \
  --stage P0 --out /workspace/acupuncture/external/wsp-vlm-channel-prep-v5-2026-11-05 \
  --execute
```

P0结束后审核真实raw outputs/receipt/environment，计算完整工作量＋20%余量；通过才生成绑定predictions SHA的P0_acceptance.json。该文件不能由当前模拟测试代填。其后再讨论B/C的D诊断登记与H验证安排；WSP仍出现在筛查确认具体失效之后，由研究者AI据反馈定位和搜索稀疏权重修补。本轮不预定两层，不启动任何权重编辑。

##### 证据与限制

- [v3固定输入与评分](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-screen-ready-v3-2026-11-05/README.zh-CN.md)、[v4资产与可辨认性审核](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-processor-prep-v4-2026-11-05/README.zh-CN.md)。
- `audit/processor_receipt.json`、`processor_manifest.json`、`equivalence.json`、`pixel_equivalence.json`：真实CPU结果。
- `audit/channel_tests.json`、`channel_tests.log`、`offline_regression.json`、`P0_dry.json`：离线/合成验收；不代表64条模型回答通过。
- `audit/environment_lock.json`、`gpu_inventory.txt`、`source_hashes.json`：环境、瞬时资源和代码来源。
- [NVIDIA兼容文档](https://docs.nvidia.com/deploy/cuda-compatibility/minor-version-compatibility.html)：CUDA12最低驱动525、CUDA13最低580；兼容表仍有PTX/新特性限制。因此535+CUDA12符合基础条件，但GPU验收必须实际做。
- 没有重新下载权重或增加大型依赖，新增仅代码/JSON/处理器预览；模型、图像库、环境、缓存均不进Git。

---


## 时间、运行与停止收据索引

下面是所收集JSON的原有时间字段与状态，不把预计结束时间当实际完成时间。未列时间的文件仍有原件链接。完整JSON全部保存在原文归档，不能以此索引中的标量代替完整嵌套内容。

| 原件 | 原记录状态/阶段 | 原时间字段（原时区） |
|---|---|---|
| [audit/processor_receipt.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-channel-prep-v5-2026-11-05/audit/processor_receipt.json) | {"status": "processor_only_not_inference", "model_calls": 0} | {} |

## 全部原始资产入口

本目录在固定提交下共有22个跟踪文件，包含代码、原回答、失败、收据和压缩证据；文件数不是样本数。[逐文件完整账本](../assets/127-wsp-vlm-channel-prep-v5-2026-11-05.tsv) · [原目录](https://github.com/yuxiexiong/acupuncture/tree/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-channel-prep-v5-2026-11-05)。未复制模型权重、环境或凭据。
