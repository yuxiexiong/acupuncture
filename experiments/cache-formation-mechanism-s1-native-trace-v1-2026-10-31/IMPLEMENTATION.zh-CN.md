# CFM-S1 实现说明与决策日志

日期：2026-10-30（UTC）。计划 `CFM-S1-v1-20261031`；合同 [CONTRACT.zh-CN.md](CONTRACT.zh-CN.md) r01。

## 文件

| 文件 | 作用 |
|---|---|
| `cfm_trace.py` | 透传记录器、单条轨迹（C/T 原路径）、复现与惰性闸门、冻结 / 授权 / worker / 控制器 / 核验 |
| `account.py` | float64 离线重建与工程门、三项对称记账与两种端点记账、区段拆分、自身来源分量、局部读出、§6 判读规则；`selftest` 为合成预演 |
| `build_reference.py` | 从 II-B 归档 `b_validate-r01.tar.zst` 取 36 条参考记录、6 份校准、缓存清单，生成 `data/reference-r01.json` |
| `test_cfm_trace.py` | 在 8 层随机初始化 Qwen3.5（层 4–6 线性 + 7 全注意力，代替 L16–18 + L19）上的 CPU 测试，不加载权重 |
| `data/reference-r01.json` | 每条轨迹必须逐值复现的 II-B 值 |
| `data/segments-r01.json` | 按文本规则生成的区段标签（只用分词器，在看任何内部量前生成并冻结） |

代码来源：直接 import 阶段二 `stage2.py`（缓存清单、管理状态、条件表）及其引入的阶段一 `localize.py`（`forward`、`_build_T`、`_clean_cache`、`score`、`decode`）和 `control_engine.py`（注入、校准）。递推公式与 transformers 5.20.2 `torch_recurrent_gated_delta_rule` 逐行对照；记账结构借 WriteSAE v4 附录 A 的写入—传播—读取顺序，不训练 SAE。

## 决策日志（偏离计划或计划未覆盖的判断）

1. **计划 §2 引用的 `cache-complement-analysis-v1-2026-10-31/` 与 `docs/cache-mechanism-path-audit-2026-10-31.zh-CN.md` 不在 main（f17da0a）上，服务器上也没有。** 本实现不依赖它们；36 条原参考直接从 II-B 归档（`/workspace/stage2-ops/archive/b_validate-r01.tar.zst`，sha `f56663e1…`，与 `b_validate-r01.verify.json` 一致）重建，每条记录逐值复现（合同 R1）。影响：计划 §2 表里来自那两份文件的数字（如 L0 四格 24 输入）本实验没有复核。
2. **旧轨迹复用检查**（计划 §2"先按旧清单检查是否有同身份归档"）：II-B 归档只有缓存哈希清单与 `gate_decay` 摘要，没有 `.pt/.npy` 张量；服务器 `/workspace/stage2-ops/` 也没有。确无可复用轨迹，按计划新采集。
3. **中间状态**：prefix 是一次分块调用，内核只暴露 prefix 末状态；事实段末、问题段末状态标为离线重建（计划 §4 允许），不拆分 prefix。
4. **候选分支末状态**：与 II-B `score` 完全相同，只喂候选前 m−1 个 token（最后一个 token 只作为被评分目标）。"评分分支末"指喂完第 m−1 个 token 之后的状态。
5. **末提示 token 单列为 `last` 段**，不并入 L（计划 §7 的 L 定义为"事实后到撤针边界"）；判读规则里的 R_late 用 L+last，在合同 §6 写明。
6. **worker 数**：preflight 是一个不可拆的门槛任务（同一输入的三条件），只占一张卡；formal 双卡各 1 个 worker（36 条前缀很短，每卡多 worker 没有收益）。
7. **"旧 D"** 取阶段二定义：D = 首步停止优势，S_fact = 两事实候选对数似然差之差（`analyze_stage2.py` 的 `D_by_base` / `S_by_base`）。
8. **判读阈值**：计划 §7 只给出分支的定性描述；合同 §6 的数值切点（0.5/0.3/0.3/ρ0.5/抵消 2、4/6 情景）是我定的描述性切点，同时预注册两套敏感性设定。计划对这些数字没有规定，它们不来自任何已看过的数据。
9. **合成预演**的 "coupled" 世界第一版（大幅改 key，后改为强后段衰减）都没造出抵消，判据阈值未改；改成 delta rule 的冗余重写（同一 (k,v) 反复写入，β 不同，ΔB 与 ΔA S̄ 逐步抵消）后 5/5 判到 coupled。这是合成世界构造的修正，不是判据修改。

10. **合同外探索分析（运行后，看过主判读之后）**：主判读两锚点都是 coupled，触发条件是抵消比 ≥ 2。为判断这个标签是否特异，在 `analysis/explore_natural_pair.py` 中对同一情景两个事实版本的 C 轨迹（token 位置一致，无针）跑同一套记账。结果：抵消比 1.95–2.19，主设定下 5/6 判 coupled。只读已核验的张量，零 GPU；不改合同判读。影响：报告第 0、3、6、7 节中凡涉及"原针与自然差异比较"的内容都标为探索档。
11. **合同设计错误（我的错误）**：§6 的分支切点只用数值底标定"非零"，没有用对照条件标定零分布（研究准则 6.3）。抵消比切点 2.0 恰好落在本模型 delta rule 记账的常态上，coupled 判读信息量低。修正建议写在报告第 7 节（第二阶段先建零分布），需新合同。
12. **记录格式**：`gate_decay` 继续记录（与 II-B 相同的汇总），没有用于分析。

## 运行记录

| 运行 | 时间（UTC） | 结果 |
|---|---|---|
| preflight-r01 | 2026-10-30 19:54 | passed；1 worker（GPU 0）；29 s |
| formal-r01 | 2026-10-30 19:57 | passed；2 worker（每卡 1 个）；36 条；52 s |
| account r01 | 2026-10-30 ~20:00 | analyzed；CPU float64；重建与恒等式全过；主判读两锚点 coupled，三套设定一致 |

## 测试与预演

- `test_cfm_trace.py` 22 项全部通过（`readiness/cpu-tests-r01.log`、`readiness/cpu-receipt-r01.json`；gqa-h20 `.venv-bench`，torch 2.6.0+cu124 / transformers 5.20.2，CPU，仓库外副本 `/workspace/cfm-s1-ops/cputest`）。覆盖：记录器在 fp32 小模型上逐字节惰性（缓存清单、首步 logits、候选分数）；分支评分与阶段一 `score` 相同；调用计数；全局名与钩子恢复；捕获的 q/k/v/g/β 与 forward 内推导逐位相同；注入层及以前缓存 T=C；针只在 prefix；复现检查对任一处 1e-12 的差都报错；fp32 与 bf16 小模型上重建闸门通过；三项恒等式、Z^W+Z^R=ΔS、区段份额和为 1、自身来源份额和为 1、读出恒等式、收缩界；C 对 C 全零且判 unresolved；计划面板（12 输入、3 条件、36 键、EOS 12/0/0）；区段规则。
- `account.py selftest`：五个合成世界（early_write / late_processing / coupled / readout_disconnect / null）各 5 种子全部判到预期分支，且 early_write 世界从不判入 coupled/readout_disconnect；重建闸门对精确状态通过、对 1e-2 状态扰动和 5% 输出扰动失败；锚点规则 4/6 支持、3/6+2/6 判 unstable；α>1 被收缩检查发现。判据可满足与不可满足两面都演示到。
