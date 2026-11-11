# 163．Gemma v8两组共享GPU的执行调整

[返回总时间线](../README.zh-CN.md)

**时间定位**：版本/记录日期 2026-11-06；未从所选收据确定完整运行起止，不据目录名补写时刻。

**当时的目的与设计**

按用户要求，确认显存足够后让B与C共用GPU0，保留其他任务；数据、batch32、评分和30轮预算不变。

**实际过程、结果与后来更正**

09:23实际B/C合计约29.9GiB，卡上剩65.3GiB。B24→25轮、C11→12轮；B新增恰464个样本，无基线重放。第25候选主20.6897%，未超过R24的21.5517%，不能用全体正确率代替主指标。完整调度和边界证据保留。

**来源身份**：`wsp-vlm-gemma3-shared-gpu-2026-11-06`；本章主体来源提交 `2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274`。下方原文中的状态是各文件写作时的状态，不能把早期“尚未运行”覆盖后期正式收据，也不能将后期结果倒填进早期设计。

## 逐轮候选完整账目

- [Gemma-v8-B逐轮目的、改动和结果](../rounds/Gemma-v8-B.md)


## 原设计、执行过程、结果与更正全文

以下按“设计与题目 → 工程/执行记录 → 结果/更正 → 其他历史说明”组织；同类内没有可靠时间时保留路径顺序，不冒充严格先后。正文未删段；仅为本章节重排标题层级、把相对链接指向固定提交。原始字节另外完整保存。

### 原件 1：Gemma四组巡检：2026-11-06 09:40–09:43

原路径：`experiments/wsp-vlm-gemma3-shared-gpu-2026-11-06/heartbeat-0940/REPORT.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-gemma3-shared-gpu-2026-11-06/heartbeat-0940/REPORT.zh-CN.md) · [单独阅读副本](../library/a3ad0b37790762ce.md)；SHA-256：`a3ad0b37790762ce7b531dbbf8538e05d7f80237cfeee97f0aa367b7a9f4e077`。

---

#### Gemma四组巡检：2026-11-06 09:40–09:43

同卡并行健康，无新工程失败。本次保持运行条件和进程，未重启或重放任何实验动作。

| 组别 | 完整候选 | 较09:10 | 较09:23 | 状态 |
|---|---:|---:|---:|---|
| v8 B | 28/30 | +4 | +3 | 第29候选已提交、正在完整评价 |
| v8 C | 14/30 | +3 | +2 | 第15候选已提交、正在完整评价 |
| v9 B | 0/30 | 0 | 0 | 等待两组v8科学评价完成 |
| v9 C | 0/30 | 0 | 0 | 等待两组v8科学评价完成 |

计数以remote.json的完整评分快照和state为准；进行中的29/15不计完成。B的29份、C的15份评价缓存（各含W0）逐SHA核对通过。v8/v9各24个清单文件无哈希漂移；原工程验收通过，执行batch32。原始验收和本次复核见engineering-verification.json。

B所选仍R24：主分数21.5517% vs W0 16.3793%（+5.1724个百分点），全体46.3362% vs43.5345%，修对20、改错7。新增候选未替代当前选择。C仍选W0：主分数33.9844%、全体79.1406%，所选相对W0修对/改错0/0。C早段post-attention norm gain1.05曾提高普通joint但未过三个保护条件；其余深度段未形成通过保护的改善，现在评价早段1.025半步。B继续数字0输出/embedding与视觉桥剂量敏感性比较。measure累计B5/C3，本窗无新增measure；这些调用不等于细致MLP机制成立。两组均未冻结、未完成最终报告；v9尚无正式研究者或模型调用。所有分数都是开发集结果，不是独立泛化。

##### 资源和实际耗时

真实远端B2191786/C2171236，同驻GPU0；本地B85511/C80319存活。v9远端2125523/2125524、本地57718/57720继续正常等待。GPU0采样100%，总用30,612 MiB（29.9 GiB）、剩66,895 MiB（65.3 GiB）。GPU1其他任务PID已变为2200956、采样100%、约83.3 GiB，不属于本实验，本次未干预。显存余量充足，无OOM；一次100%采样不代表全程满载。

工作盘剩133.188 GiB，比09:23快照131.399 GiB增加1.789 GiB，属于全盘净变化，不能称本实验回收。B目录3.080 GiB（约+0.048），C3.495 GiB（约+0.152）；满足每组12 GiB及全盘至少20 GiB预算，无清理。

| 搜索累计计账 | B | C |
|---|---:|---:|
| 目标样本/前向 | 13,531 | 39,267 |
| 目标token | 4,168,878 | 10,354,628 |
| CPU Python秒 | 242.136 | 48.953 |
| 最近成功研究者turn | 129 | 78 |
| 研究者累计token（含缓存输入） | 19,476,360 | 9,468,159 |

C本次目标样本包含正在评价中的部分样本，不能按样本数反推完整轮数。工程另计各2212生成、2218前向，其中2080校准，不混入30轮。401失败110/64没有单次usage收据，恢复后的线程累计持续对账，但失败单次成本不能单独分离；不填0，不把tokens当已知账单金额。

已完成动作窗口B118–128：Astra整回合合计435.1秒（该统计包含已完成研究者129，工具动作129仍进行中），评价373.3秒、Python129.8秒、提交99.1秒、工具等待45.7秒。C68–78：Astra611.8秒、完整评价554.8秒、Python4.0秒、提交0.08秒、工具等待44.5秒；正在执行的评价78未计入完整评价耗时。Astra耗时包含API排队、上下文处理、输出，不称纯思考；工具等待由同Mac请求/响应mtime差减远端执行时间计算。窗口不严格同长，不能把这些列比较成速度排行榜。原始timing.json列明边界。

最近同卡B完整评价约84–159秒；C约231–285秒，长于此前约217秒。存在共享计算竞争的可能，但未经配对性能试验，不能唯一归因于同卡。查看最近4–8候选循环时保留原间隔并排除显式认证/GPU等待段（B约3199秒、C约2857秒），不把它们算计算速度：恢复后B循环约3.3–5.9分钟，C约7.3–9.8分钟，样本仍少。预计B剩余科学评价约5–15分钟，C约2–3小时；最终报告耗时另计、不承诺。v9仍有依赖等待及自身工程验收，暂不给四组总完工时间。

B先完成30后应正常冻结/退出并释放服务；若仅收尾失败，保存结果和停止回执后释放GPU，不让收尾卡住后续。C尚未完成30，v9等待它是科学依赖，并非收尾阻塞。保持每30分钟巡检及工程故障及时处理。

---

### 原件 2：Gemma巡检与v8 B30交付：2026-11-06 10:10

原路径：`experiments/wsp-vlm-gemma3-shared-gpu-2026-11-06/heartbeat-1010/REPORT.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-gemma3-shared-gpu-2026-11-06/heartbeat-1010/REPORT.zh-CN.md) · [单独阅读副本](../library/babbc147a6b8f013.md)；SHA-256：`babbc147a6b8f013b0e49d266dce14756f35c52424a38095a2ccc8ce2d59db8a`。

---

#### Gemma巡检与v8 B30交付：2026-11-06 10:10

B已于09:47:00左右完成30/30，自动冻结R24并正常退出；服务2191786及控制器85511均已消失，GPU已释放。C18/30，较09:40增加4轮，正在评价第19候选；首次出现通过保护条件的小幅改善。本次未重启或改变任何运行实验。v9 B/C各0/30，正常等待尚未完成的C，未被B收尾阻塞。

| 组别 | 完整轮次（较09:40） | W0→所选主分数 | W0→所选全体正确率 | 修对/改错 |
|---|---|---|---|---|
| v8 B | 30/30（+2），已冻结退出 | 16.3793%→21.5517% | 43.5345%→46.3362% | 20/7 |
| v8 C | 18/30（+4），继续 | 33.9844%→34.7656% | 79.1406%→79.2969% | 24/20 |
| v9 B/C | 各0/30 | 未运行 | 未运行 | 等待v8依赖 |

B最终选择R24（数字0绑定embedding/输出行gain1.45、视觉桥norm有效gain0.90，3707个有效BF16标量改变）；最后6个候选没有替代它。C当前R18对第5–8层post_attention_layernorm有效gain作1.05倍修改，普通joint净增2/256、主分数+0.78125个百分点，且通过保护门槛；全体净增4/2560，仍有20条原对改错，不能说全面改善。正在评价相同层gain1.10剂量。B内部measure累计5、C3，本窗无新增measure；这不是定向MLP写入机制证明，也不是独立泛化。

##### B完成与归档核验

31份完整评价（W0+30）逐SHA复核通过；完成计数30，research_done=true，frozen和best同为c-c20a52e0a986df9c0cccdc5aec965480f0edd044aee46b5243074bf4a6c5ae59。冻结清单与实际两个补丁文件SHA一致。冻结文件明确标记development_selection_only_pending_reload_and_new_confirmation，本次未新加载模型，不冒充独立重载验证或确认实验。

B-remote-evidence.tar.gz取回原始回答/评分、actions/inbox、候选JSON清单、协议、工程/历史收据、自动result/trajectory报告及冻结记录；B-researcher-trace.tar.gz取回全部本地研究者原始事件、输入、回答、工具结果和usage，含失败turn110及最终turn132。压缩件SHA见archive-sha256.json，内部完整评分核验见archive-verification.json。候选NPZ和work/staged权重留在原远端路径，不进Git；冻结补丁文件清单及哈希在B-frozen-candidate.json。原件未删除。B-continuation-receipt和status是本次实际结束收据，旧认证恢复B的running是历史，不应误判仍运行。v8自动结果报告已完成，不伪造额外研究者机制报告。

##### 实际资源与用量

GPU0仅剩C2171236：整卡用15,491 MiB（约15.13 GiB）、剩82,017 MiB（约80.1 GiB），采样0%发生在研究者/提交阶段；C随后评价在进行。GPU1是其他训练2200956，未修改。v9等待器2125523/2125524及控制器57718/57720存活；C本地80319存活，无新认证/容量/OOM故障。

工作盘剩125.062 GiB，较09:40下降8.125 GiB；B目录3.111 GiB（+0.031）、C3.789 GiB（+0.294），不能把全盘下降都归因本实验。每组12 GiB和全盘至少20 GiB仍满足，不清理。

| 计账 | B最终 | C快照（含第19评价部分样本） |
|---|---:|---:|
| 搜索目标样本/前向 | 14,459 | 48,899 |
| 实际目标tokens | 4,454,864 | 12,896,323 |
| Python CPU秒 | 256.757 | 50.552 |
| 研究者累计tokens，含缓存输入 | 19,956,144（turn132） | 12,146,313（turn94） |

工程每组另计2212生成、2218前向，其中2080吞吐校准，不计修补轮。401失败110/64缺单独用量回执，恢复后线程累计已承接，不能将失败单次用量填0；金额未知。模型加载历史在各工程/恢复收据中保留，ready不等于实际加载。本窗未新加载模型。

本窗B剩两次评价共228.4秒、Python30.7秒、提交24.9秒、工具等待17.8秒，Astra130–132整回合65.6秒。C完整评价78/82/86/90共923.9秒、Python1.64秒、提交0.10秒、工具等待86.6秒；研究者79–94整回合858.9秒。窗口起止不完全对齐，不能相加当严格墙钟总时长。Astra含API排队/上下文/输出，非纯思考；工具等待由同Mac request/response mtime差减远端elapsed得到。新measure耗时0。原始timing及researcher-usage分别列明。

C最近4个完整候选循环约6.4–9.7分钟，按剩12轮并结合第19评价正在进行，预计科学评价还需约1.3–2小时；最终收尾另计。B科学评价已完成，无剩余ETA。v9有依赖等待和自身工程验收，暂无可信四组总完工时间。C未到30前不绕过科学依赖；到30后若仅报告/冻结/归档失败，按用户授权保存证据及停止收据、释放服务，避免收尾卡后序。

---

### 原件 3：Gemma半小时巡检：2026-11-06 10:40

原路径：`experiments/wsp-vlm-gemma3-shared-gpu-2026-11-06/heartbeat-1040/REPORT.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-gemma3-shared-gpu-2026-11-06/heartbeat-1040/REPORT.zh-CN.md) · [单独阅读副本](../library/4974340fbe5e0cc9.md)；SHA-256：`4974340fbe5e0cc9cab1552b43f0865ed29e7d494d478348758913ba7def8e70`。

---

#### Gemma半小时巡检：2026-11-06 10:40

C22/30（较10:10增加4轮），最佳主分数升至36.71875%；B保持30/30已冻结退出；v9 B/C各0/30等待C科学评价完成。未发现新工程、认证或容量失败。本次没有修改、重启或重放运行实验。

| 组别 | 完整轮次 | W0→所选主分数 | W0→所选全体正确率 | 修对/改错 |
|---|---:|---|---|---|
| v8 B | 30/30，完成 | 16.3793%→21.5517% | 43.5345%→46.3362% | 20/7 |
| v8 C | 22/30，继续 | 33.9844%→36.7188% | 79.1406%→79.4922% | 28/19 |
| v9 B/C | 各0/30 | 未运行 | 未运行 | 等待v8完成 |

C较W0主分数增加2.734375个百分点，普通joint从87/256到94/256；全体净增9/2560，仍有19条原对改错。与10:10所选R18相比，主分数再增加1.953125个百分点。当前R22仅第7、8层post_attention_layernorm有效gain1.075，共5097个有效BF16标量改变，其余恢复W0。逐保护格复算最差下降3.125个百分点，在3.5个百分点门槛内；格式错误率0.46875%，截断0，保护通过。通过不代表所有格子无损伤。

更宽的第5–8层gain1.075曾有更高开发主分数37.8906%，但无图保护格下降6.25个百分点，不能作为合格最优。现在通过拆层将修改缩至7、8层；下一候选单独第7层同剂量，检验第8层是否必要。此为已授权研究者的开发反馈驱动搜索，不是新增外部指定实验。本轮没有新增measure，累计仍B5/C3；拆层及剂量控制是有用行为证据，但norm增益调整不等于选中了特定MLP输出方向，也未证明内部方向写入机制。开发结果不是独立泛化。

##### 实测状态与计账

B原服务/控制器已退出、冻结及原始证据在heartbeat-1010交付，不恢复；本次完整31份评分哈希再次通过。C远端2171236、本地80319存活，23份完整评分（W0+22）哈希通过；快照时第23候选正在准备，随后研究者已到turn109。v9远端2125523/2125524和本地57718/57720正常waiting_gemma_v8。v8/v9源码清单各24文件无漂移，历史工程batch32验收不变。C未冻结、最终报告未完成。

GPU0由C占用约15.13 GiB，空余约80.10 GiB，采样0%时处于研究者阶段；GPU1另一个项目进程2218292约14.44 GiB、79%利用率，不属于Gemma，不修改。一次采样不代表整个窗口利用率。工作盘剩124.155 GiB，较10:10净减0.908 GiB；B目录3.111 GiB不变、C4.084 GiB（增加0.295 GiB），全盘变化不能全归本实验。每组12 GiB和全盘至少20 GiB门槛满足，无需清理。

C搜索累计58,883样本/前向，15,540,628目标tokens，52.222 Python CPU秒；研究者最新成功turn109累计15,213,690 tokens（含缓存输入），与远端快照不是同一瞬间。B最终14,459样本、4,454,864目标tokens、256.757 CPU秒、19,956,144研究者tokens不变。工程每组另计2212生成/2218前向含2080校准，不计30轮。历史401失败无单次usage仍不能填0；恢复后线程累计继续承接，金额未知。

C研究者95–109整回合累计827.2秒，包含API排队/上下文/输出，非纯思考。快照内95以后已完成工具：完整评价20–22共649.4秒、Python1.70秒、提交0.07秒、工具等待68.2秒；第19评价属于此前已派发94，不混入这个工具窗口。时间窗不完全相同，不相加当严格墙钟总耗时。新测量耗时0；工具等待按同Mac请求/响应mtime差减远端elapsed。最近8完整候选的7个间隔约5.75–9.69分钟，近4个约5.75–7.62分钟；剩8轮预计约50–80分钟，最终收尾另计，不承诺结束时刻。B无需ETA；v9等待C完成及自身验收，四组总ETA仍待v9实测。

本次remote.json保存四组状态、候选摘要、评分hash与资源；C-turn-0105保存当前最优完整评价原始工具响应（gzip无损），106/107保留审计和下一步原始回答；C-protection-recheck为本次CPU保护复算；timing含原始耗时和最新研究者usage。持续每30分钟巡检，若仅30轮后的收尾故障，按授权保存证据、退出服务并安全交接后序，不让其无限阻塞。

---

### 原件 4：Gemma v8 B/C 同卡并行调度修复

原路径：`experiments/wsp-vlm-gemma3-shared-gpu-2026-11-06/README.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-gemma3-shared-gpu-2026-11-06/README.zh-CN.md) · [单独阅读副本](../library/bb9c9190143ba94c.md)；SHA-256：`bb9c9190143ba94c84e7bda6e9445dc7ead3a06daec942d3ed7db6a031e255e4`。

---

#### Gemma v8 B/C 同卡并行调度修复

用户于2026-11-06明确要求先检查显存，显存足够时允许并行，不必独占两张卡。本次只调整已授权的Gemma v8 B设备分配；C保持运行，其他训练任务保持原状。

##### 实测结论

两张H20各97,871 MiB（约95.6 GiB）。固定batch32的工程校准峰值reserved为B约14.084 GiB、C约14.682 GiB。旧门禁要求整卡空闲，确实过于保守。09:23左右的实时验收确认B进程2191786、C进程2171236同时驻留GPU0，B约15,118 MiB、C约15,484 MiB；整卡合计30,612 MiB（29.9 GiB），剩余66,895 MiB（65.3 GiB）。GPU1的另一训练进程2187740占约83.3 GiB，未被修改或中断。完整原始快照见verification.json；此处数值是瞬时实测，不是未来峰值保证。

B迁移后首次完整评价成功，24→25/30；C继续运行，11→12/30。B第25候选主分数20.6897%、全体46.7672%，相对W0修对30、改错15；主指标未超越当前选中R24的21.5517%，不能将全体正确率提升当作主指标改善。B第25评价远端用时102.394秒，包含本次首次加载，不能据此宣称同卡加速倍数。Astra请求阶段GPU仍可为0%，显存足够不等于计算持续满载。

##### 恢复边界与证据

迁移前B只有CPU工作，目标模型尚未加载。第116动作已提交候选25；第117研究者原生事件已完成，但评价请求尚未派发，远端无inbox或动作117。保留原始事件、回答、累计用量16,957,571 tokens，停止旧控制器80318和CPU服务2171235，在同W0、协议、25份评分缓存及同Astra线程上接续。第117动作在新服务首次派发，原动作不重放，W0不重算；新增样本恰为464个，即一份完整B开发评价。下一研究者回合从118继续。

B-reconciled-receipt.json是观察者从原生turn.completed事件核对的收据，不冒充原CLI完整receipt。B-turn-0117-undispatched保存原始输入和事件。Python内存因服务重建清空，工作文件保留，已通知研究者重建变量。B新控制器85511，C原控制器80319及服务2171236均未重启。实时PID以进程和新收据为准。

准入要求GPU0至少36 GiB空闲（B按24 GiB估计加12 GiB余量），且现有计算进程仅允许已核实C；两次检查间隔2秒，并使用本组共享锁和原队列锁防重入。原先C独占租约未被破坏；本次明确授权下增加B的共享租约。该规则是当前两组的有界调度，不是允许任意任务无条件共卡。数据、batch32、模型、评分、候选定义、Astra/max均未改变。旧失败及原验收完整保留。

##### 验收与后续

本地和远端单元验证通过，实际双进程GPU驻留和第117完整评价通过。磁盘实测剩余131.40 GiB，B约3.032 GiB、C约3.343 GiB，低于各12 GiB预算，满足全盘至少20 GiB要求。未删除证据。

继续B、C各累计30轮，每30分钟核验实际显存、进度和异常。v9仍按既定科学依赖等待两组v8完成；同卡授权不改研究顺序。已完成30轮的报告/冻结/归档故障不得无限阻塞资源交接，应保存失败和停止收据后释放GPU。已有终止边界（Qwen及旧队列）保持。运行中用时受计算竞争和Astra请求影响，需后续实测；本次不声称科学效果改善或独立泛化。

---


## 时间、运行与停止收据索引

下面是所收集JSON的原有时间字段与状态，不把预计结束时间当实际完成时间。未列时间的文件仍有原件链接。完整JSON全部保存在原文归档，不能以此索引中的标量代替完整嵌套内容。

| 原件 | 原记录状态/阶段 | 原时间字段（原时区） |
|---|---|---|
| [B-broker-launch.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-gemma3-shared-gpu-2026-11-06/B-broker-launch.json) | {} | {"time_unix": "2026-11-06T01:20:48.736050+00:00"} |
| [B-controller-launch.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-gemma3-shared-gpu-2026-11-06/B-controller-launch.json) | {} | {"time_unix": "2026-11-06T01:20:48.952675+00:00"} |
| [B-controller-once.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-gemma3-shared-gpu-2026-11-06/B-controller-once.json) | {} | {"time_unix": "2026-11-06T01:20:49.180134+00:00"} |
| [B-controller-paused.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-gemma3-shared-gpu-2026-11-06/B-controller-paused.json) | {} | {"time_unix": "2026-11-06T01:17:27.860969+00:00"} |
| [B-old-broker-stop.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-gemma3-shared-gpu-2026-11-06/B-old-broker-stop.json) | {} | {"time_unix": "2026-11-06T01:20:47.447619+00:00"} |
| [B-old-controller-stop.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-gemma3-shared-gpu-2026-11-06/B-old-controller-stop.json) | {} | {"time_unix": "2026-11-06T01:20:47.662221+00:00"} |
| [B-reconciled-receipt.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-gemma3-shared-gpu-2026-11-06/B-reconciled-receipt.json) | {} | {} |
| [heartbeat-0940/engineering-verification.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-gemma3-shared-gpu-2026-11-06/heartbeat-0940/engineering-verification.json) | {} | {} |
| [heartbeat-1010/B-continuation-receipt.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-gemma3-shared-gpu-2026-11-06/heartbeat-1010/B-continuation-receipt.json) | {"status": "stopped_or_frozen"} | {} |
| [heartbeat-1010/B-patch-verification.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-gemma3-shared-gpu-2026-11-06/heartbeat-1010/B-patch-verification.json) | {} | {} |
| [heartbeat-1010/B-result.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-gemma3-shared-gpu-2026-11-06/heartbeat-1010/B-result.json) | {} | {} |
| [heartbeat-1010/archive-verification.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-gemma3-shared-gpu-2026-11-06/heartbeat-1010/archive-verification.json) | {} | {} |
| [heartbeat-1040/C-turn-0105/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-gemma3-shared-gpu-2026-11-06/heartbeat-1040/C-turn-0105/receipt.json) | {} | {} |
| [heartbeat-1040/C-turn-0106/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-gemma3-shared-gpu-2026-11-06/heartbeat-1040/C-turn-0106/receipt.json) | {} | {} |
| [heartbeat-1040/C-turn-0106/tool_result.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-gemma3-shared-gpu-2026-11-06/heartbeat-1040/C-turn-0106/tool_result.json) | {} | {} |
| [heartbeat-1040/C-turn-0107/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-gemma3-shared-gpu-2026-11-06/heartbeat-1040/C-turn-0107/receipt.json) | {} | {} |
| [verification.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-gemma3-shared-gpu-2026-11-06/verification.json) | {} | {"time_unix": "2026-11-06T01:23:55.652365+00:00"} |

## 全部原始资产入口

本目录在固定提交下共有58个跟踪文件，包含代码、原回答、失败、收据和压缩证据；文件数不是样本数。[逐文件完整账本](../assets/163-wsp-vlm-gemma3-shared-gpu-2026-11-06.tsv) · [原目录](https://github.com/yuxiexiong/acupuncture/tree/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-gemma3-shared-gpu-2026-11-06)。未复制模型权重、环境或凭据。
