# B/C 运行通道准备 v5

日期：2026-11-05。结论：**不涉及模型执行的准备已完成；还差真实 GPU/模型的 64 条 P0 工程预检，不能称已完成端到端验收。** 本轮没有加载模型权重，没有 forward/generate，没有 GPU 计算，也没有开始 B/C 行为实验或 WSP 修补。

## 距离开跑还差什么

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

## 本轮具体变更

v5的 `runner.py` 是v3运行器的版本化副本，只修改环境锁、调用前attempt日志、原子receipt写入和受监督启动要求。数据仍读v3冻结队列。没有改模型、dtype、SDPA、greedy、128输出上限、像素预算或科学统计判据。

`launch.py` 是后续唯一推荐执行入口。默认只做CPU输入校验；显式 `--execute` 才能进入模型工作进程。监督器先检查累计时间，保留5秒退出余量，对整个工作进程组施加期限，TERM后2秒仍不退出则KILL；中断的在途请求仍计一次尝试。加载与异常耗时记入receipt，不把基础设施错误算答错。已有running回执会阻止继续，不悄悄抹掉或重新跑。Linux监督器死亡会杀死其模型子进程，未闭合回执仍须显式核账后恢复；断电/内核不可中断状态不能靠用户态脚本提供实时保证。

环境没有安装/卸载任何包，也没有改共享环境。`.venv-bench`实际Python路径和8个关键包版本见 `audit/environment_lock.json`；执行前逐项检查，变化即停止。复用现有环境避免修改正在服务其他任务的软件。新栈的GPU数值结果尚不存在，不能声称与旧CUDA13栈的模型输出等价。

CPU验收首次在最后附加审核文件时发现远端v4的审核文件实际位于external目录，保留 `audit/processor.log` 的原始失败日志；修正为从真实位置读取并以manifest SHA绑定，另存 `audit/equivalence.log` 成功回执。该错误发生在CPU图片和序列化完成之后，未产生任何模型调用。

## 使用位置与边界

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

## 证据与限制

- [v3固定输入与评分](../wsp-vlm-screen-ready-v3-2026-11-05/README.zh-CN.md)、[v4资产与可辨认性审核](../wsp-vlm-processor-prep-v4-2026-11-05/README.zh-CN.md)。
- `audit/processor_receipt.json`、`processor_manifest.json`、`equivalence.json`、`pixel_equivalence.json`：真实CPU结果。
- `audit/channel_tests.json`、`channel_tests.log`、`offline_regression.json`、`P0_dry.json`：离线/合成验收；不代表64条模型回答通过。
- `audit/environment_lock.json`、`gpu_inventory.txt`、`source_hashes.json`：环境、瞬时资源和代码来源。
- [NVIDIA兼容文档](https://docs.nvidia.com/deploy/cuda-compatibility/minor-version-compatibility.html)：CUDA12最低驱动525、CUDA13最低580；兼容表仍有PTX/新特性限制。因此535+CUDA12符合基础条件，但GPU验收必须实际做。
- 没有重新下载权重或增加大型依赖，新增仅代码/JSON/处理器预览；模型、图像库、环境、缓存均不进Git。
