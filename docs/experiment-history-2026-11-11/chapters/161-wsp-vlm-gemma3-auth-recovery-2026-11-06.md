# 161．Gemma v8认证中断与原线程恢复

[返回总时间线](../README.zh-CN.md)

**时间定位**：版本/记录日期 2026-11-06；未从所选收据确定完整运行起止，不据目录名补写时刻。

**当时的目的与设计**

11月6日08:33 B24/30、C11/30时研究者因401 token_revoked退出；用户重新登录后按原配置接续。

**实际过程、结果与后来更正**

保留无usage的失败回合，不填零。B候选25已暂存未提交，C候选12已提交未评，分别处理；08:46启动恢复器、08:48仍等空卡，不把启动等同恢复完成。随后共享GPU接续另列。

**来源身份**：`wsp-vlm-gemma3-auth-recovery-2026-11-06`；本章主体来源提交 `2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274`。下方原文中的状态是各文件写作时的状态，不能把早期“尚未运行”覆盖后期正式收据，也不能将后期结果倒填进早期设计。


## 原设计、执行过程、结果与更正全文

以下按“设计与题目 → 工程/执行记录 → 结果/更正 → 其他历史说明”组织；同类内没有可靠时间时保留路径顺序，不冒充严格先后。正文未删段；仅为本章节重排标题层级、把相对链接指向固定提交。原始字节另外完整保存。

### 原件 1：Gemma 09:10巡检：B认证恢复成功，C继续等卡

原路径：`experiments/wsp-vlm-gemma3-auth-recovery-2026-11-06/heartbeat-0910/REPORT.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-gemma3-auth-recovery-2026-11-06/heartbeat-0910/REPORT.zh-CN.md) · [单独阅读副本](../library/ffbd247a3b227fe5.md)；SHA-256：`ffbd247a3b227fe51e4de122ab2c9d4c8004dcadb47b805ec18632e3785e3f3b`。

---

#### Gemma 09:10巡检：B认证恢复成功，C继续等卡

2026-11-06 09:10，B原线程turn111已成功并取得工具响应。远端B2171235于09:09取得GPU1，本机控制器80318继续同Astra线程；C2171236/80319仍等待空卡。GPU0为其他任务2166726使用，不抢占。v9等待器2125523/2125524及本机57718/57720均存活，正常waiting_gemma_v8。没有新增工程故障或重复启动。

| 组别 | 完整轮次/目标及增量 | 所选主分数/W0 | 所选全体正确率/W0 | 修对/改错 |
|---|---|---|---|---|
| v8 B | 24/30，+0 | 21.5517%/16.3793% | 46.3362%/43.5345% | 20/7 |
| v8 C | 11/30，+0 | 33.9844%/33.9844% | 79.1406%/79.1406% | 0/0，仍W0 |
| v9 B/C | 各0/30 | 未运行 | 未运行 | 等待v8 |

轮次未增长的主要原因是此前等卡，B09:09才进入恢复回合，当前重建Python工作变量。turn111为status动作，新增目标样本0、测量0、完整评价0；ready时实际模型加载0，不能把取得GPU锁或研究者恢复当成目标模型已装载。B/C累计measure仍为5/3，诊断不计修补轮，也不直接证明机制。所选补丁/保护结果与上一报告相同，均未冻结，v9机制报告尚未开始；开发结果不构成独立泛化。

##### 身份、工程和用量核验

四个服务/等待器及四个本地控制器实际PID/命令核对；两版source-manifest逐文件无差异，v8工程收据均存在并通过，完整评价缓存逐SHA一致，无未决/不完整远端动作。C最后失败仍是旧turn64，尚未发生新的认证尝试，不误报再次失败。

B turn111保持线程01a1adde-e3b8-7421-ad03-de7238ef0db4，研究者回执与工具回执成功。累计15914989 tokens，承接原已知15766109，差额148880包含缓存输入；累计计账已接续，但不能据此单独分离失败turn110的用量，原失败无usage事实保持。C已知累计6500783，失败64用量仍未知。实际费用未知。

B搜索累计11675样本、3596404目标token、149.944 CPU秒；C30723样本、8108464目标token、37.749 CPU秒。工程各另计2212生成/2218前向，其中2080吞吐校准，不计30轮。本次没重放W0或历史动作。

##### 耗时、GPU、磁盘与ETA

B turn111 Astra整回合23.861秒（含API排队/上下文/输出，不是纯思考），远端status约0.000009秒，按同Mac请求/响应mtime差扣远端elapsed计工具往返5.653秒。恢复等待器从08:46到09:09等待空卡约23分钟；不把这段时间当模型推理变慢。新完整候选尚未完成，B待恢复后首个完整评价再校准完工ETA；C仍等卡，暂停完工ETA，v9同理。

09:10GPU0/1采样27%/0%，计算进程仅其他任务2166726；B虽持GPU1锁但目标模型尚未加载，处于研究者/CPU阶段。磁盘余134.266GiB，较08:48减少1.748GiB；B目录3.012GiB仅增约0.152MiB，C3.266GiB无增量，不能把全盘下降算作本实验增长。各分支12GiB和全盘20GiB门禁均有余量，无清理。

证据：remote.json保存实时状态、工程收据、源码核对、逐题比较计数和资源；B-turn-0111保存完整首个成功回合；verification.json核对线程、用量差、工具成功与耗时。半小时巡检已更新B在线恢复成功及C仍等待身份。本次没有修改实验条件或运行代码。

---

### 原件 2：Gemma v8认证失败后接续（2026-11-06 08:40巡检）

原路径：`experiments/wsp-vlm-gemma3-auth-recovery-2026-11-06/README.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-gemma3-auth-recovery-2026-11-06/README.zh-CN.md) · [单独阅读副本](../library/5e0e6c53715b8bb4.md)；SHA-256：`5e0e6c53715b8bb44398768835a380ceb8d46fec7a7a9d8d1241ed767b361bac`。

---

#### Gemma v8认证失败后接续（2026-11-06 08:40巡检）

B、C在08:33分别于研究者turn110、turn64因401 token_revoked退出，原服务随后释放GPU。用户收到明确故障说明后回复“已重新登录”。本次依现有四组各30轮、及时修工程的授权恢复；不重新授权或修改科学条件，不恢复旧Qwen/2B/8B/旧Gemma。

##### 当前结果

| 组别 | 完整轮次（较08:10） | W0→所选主分数 | W0→所选全体正确率 | 修对/改错 |
|---|---|---|---|---|
| v8 B | 24/30（+6） | 16.3793%→21.5517% | 43.5345%→46.3362% | 20/7 |
| v8 C | 11/30（+3） | 33.9844%→33.9844% | 79.1406%→79.1406% | 0/0，仍选W0 |
| v9 B/C | 各0/30 | 尚未运行 | 尚未运行 | 等待两组v8科学评价结束 |

B当前所选R24是数字0绑定embedding/输出行gain1.45与视觉桥gain0.90组合，主分数与R17相同，全体正确率略低，但改错从12降到7、修对26降到20；是原选优规则下的取舍，不隐去损伤。B剩6轮，C剩19轮。B此前144高/低空间均值能量通道比较已有完整评价，但未替代当前输出/视觉桥组合；measure调用不证明机制。C继续全层/分深度gain诊断，新增候选尚无通过保护的改善。均未冻结，开发结果不是独立泛化，不能称MLP机制修复。

##### 故障和恢复边界

失败事件只有thread.started、错误与turn.failed，没有agent回答或turn.completed/usage。远端B最后完整动作109、C63，无未决inbox、无缺响应action；原评分快照B25份、C12份逐SHA核验。失败用量未知，不将其填0，下次成功线程累计usage继续对账。

B109已暂存candidate25工作文件、未提交；C63已提交candidate12、未完整评价。恢复提示明确告知两处差异，禁止重放动作、重复评价计轮。相同线程B01a1adde-e3b8-7421-ad03-de7238ef0db4从111、C01a1addf-9ba6-77b2-8466-d863db04b647从65继续。Python变量重建，文件和缓存保留，目标模型按首次前向懒加载，不重跑W0。

恢复器复用此前已验收resume_C.py，新增精确认证失败边界和空卡等待，B/C共用一个脚本。2个测试覆盖两个真实合法边界，以及state变化、提前完成、冻结、未决动作、失败回执、研究者已有回答/usage等拒绝条件；本地和远端通过。原v8服务、目标模型、数据、batch32、评分、轮数预算不变。

应用自带CLI已变为0.166.0-alpha.6，二进制SHA从58a91f6e…变为508388df…，见cli-amendment.json。原目标协议和验收收据不覆盖修改；只在研究者接续配置中显式记录新CLI哈希，使用同gpt-6-astra/max、ChatGPT登录和原禁用工具/持久会话参数。实际CLI参数解析通过，不冒充在线研究者验收。v9尚未启动，既有控制器在启动时自行记录当前CLI哈希，不需修改其引擎。

OpenAI官方[认证文档](https://developers.openai.com/codex/auth/)说明CLI可用codex login完成登录，login status查看认证方式；本机显示已登录加用户确认，不等于真实下一回合已通过。下一回合若再认证/容量失败仍停止保留，不无界重试、不换API或模型。

##### 实际启动与资源

08:46新远端B2171235/C2171236、本机B80318/C80319已启动；08:48实测waiting_gpu_auth_recovery / waiting_remote_ready。已核对真实命令。等待器使用原共享GPU锁、计算进程/显存/利用率双检和磁盘门禁，空卡后自动继续，不抢占其他任务。当前两卡被其他任务占用，不修改或停止它们；当前尚未产生新的Gemma模型/研究者调用，在线认证与首回合接续仍待验证。

v9远端2125523/2125524、本机57718/57720仍在，已随v8恢复等待从waiting_gemma_v8_review回到waiting_gemma_v8。原失败收据保持历史身份，当前看本目录新status/launch和实际进程。心跳已更新至此次恢复身份，每30分钟继续检查。

08:48磁盘剩136.014GiB，B/C目录3.012/3.266GiB，较08:10各增约0.093/0.223GiB；每组12GiB与全盘20GiB门禁有余量，不清理文件。GPU采样100%/25%属于其他作业，不能算Gemma利用率。

##### 用量、耗时和ETA

B搜索累计11675样本、3596404目标token、149.944 CPU秒；C30723样本、8108464目标token、37.749 CPU秒。研究者已知累计B15766109/C6500783 token（含缓存输入），失败110/64无usage回执，待下次累计对账；费用未知。工程各另计2212生成/2218前向，其中2080吞吐校准，不算修补轮。此次恢复截至空卡等待新增模型加载0、基线重放0。

统计B turn91–109：Astra615.49秒、完整评价421.50秒、Python122.54秒、提交97.11秒、工具等待88.26秒；C turn51–63：Astra612.54秒、完整评价651.55秒、Python1.71秒、提交0.16秒、工具等待74.03秒。本窗没有新增measure。Astra是含API排队/上下文/输出的整回合，非纯思考；工具等待用同Mac request/response mtime差减远端elapsed。见timing.json。

认证中断后且当前等待其他任务释放GPU，暂停完工ETA，不把排队时间混成计算速度。取得空卡、首个研究者回合和新完整候选成功后再按最近4–8个候选更新区间。

##### 证据入口

preflight.json.gz为原始恢复前状态、配置、身份、完整评价摘要及最后动作/回答，解压后内容与本地preflight.json相同；保留压缩件避免35MiB JSON重复入Git。B-turn-0109/0110、C-turn-0063/0064包含成功动作和认证失败原件。authorization、acceptance、cli-amendment、launch/status、live、timing分别区分授权、工程、工具版本、实际启动和资源。本报告不伪称已完成30轮或新登录已被服务端验证。

---


## 时间、运行与停止收据索引

下面是所收集JSON的原有时间字段与状态，不把预计结束时间当实际完成时间。未列时间的文件仍有原件链接。完整JSON全部保存在原文归档，不能以此索引中的标量代替完整嵌套内容。

| 原件 | 原记录状态/阶段 | 原时间字段（原时区） |
|---|---|---|
| [B-broker-launch.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-gemma3-auth-recovery-2026-11-06/B-broker-launch.json) | {} | {"time_unix": "2026-11-06T00:46:17.927438+00:00"} |
| [B-controller-launch.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-gemma3-auth-recovery-2026-11-06/B-controller-launch.json) | {} | {"time_unix": "2026-11-06T00:46:18.126174+00:00"} |
| [B-controller-once.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-gemma3-auth-recovery-2026-11-06/B-controller-once.json) | {} | {"time_unix": "2026-11-06T00:46:18.175256+00:00"} |
| [B-turn-0109/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-gemma3-auth-recovery-2026-11-06/B-turn-0109/receipt.json) | {} | {} |
| [B-turn-0109/tool_result.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-gemma3-auth-recovery-2026-11-06/B-turn-0109/tool_result.json) | {} | {} |
| [C-broker-launch.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-gemma3-auth-recovery-2026-11-06/C-broker-launch.json) | {} | {"time_unix": "2026-11-06T00:46:17.927756+00:00"} |
| [C-controller-launch.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-gemma3-auth-recovery-2026-11-06/C-controller-launch.json) | {} | {"time_unix": "2026-11-06T00:46:18.128039+00:00"} |
| [C-controller-once.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-gemma3-auth-recovery-2026-11-06/C-controller-once.json) | {} | {"time_unix": "2026-11-06T00:46:18.175256+00:00"} |
| [C-turn-0063/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-gemma3-auth-recovery-2026-11-06/C-turn-0063/receipt.json) | {} | {} |
| [C-turn-0063/tool_result.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-gemma3-auth-recovery-2026-11-06/C-turn-0063/tool_result.json) | {} | {} |
| [heartbeat-0910/B-turn-0111/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-gemma3-auth-recovery-2026-11-06/heartbeat-0910/B-turn-0111/receipt.json) | {} | {} |
| [heartbeat-0910/B-turn-0111/tool_result.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-gemma3-auth-recovery-2026-11-06/heartbeat-0910/B-turn-0111/tool_result.json) | {} | {} |
| [heartbeat-0910/verification.json](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-gemma3-auth-recovery-2026-11-06/heartbeat-0910/verification.json) | {} | {} |

## 全部原始资产入口

本目录在固定提交下共有63个跟踪文件，包含代码、原回答、失败、收据和压缩证据；文件数不是样本数。[逐文件完整账本](../assets/161-wsp-vlm-gemma3-auth-recovery-2026-11-06.tsv) · [原目录](https://github.com/yuxiexiong/acupuncture/tree/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-gemma3-auth-recovery-2026-11-06)。未复制模型权重、环境或凭据。
