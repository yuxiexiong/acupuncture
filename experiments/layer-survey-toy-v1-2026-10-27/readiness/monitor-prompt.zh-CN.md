每30分钟巡检本聊天已授权的 Acupuncture 2B/4B/9B 全层单针短回答调查。用户明确要求每次汇报当前进展、运行是否顺利、技术异常或警报、更新后的剩余ETA与北京时间预计完成点，以及磁盘空间是否足够。此自动化只服务本批调查；无须重复请求已获授权的技术bug修复许可。

先读本地 /Users/ruizhixu/Documents/ChatGPT/acupuncture/AGENTS.md、README.md、docs/RESEARCH_STATUS.zh-CN.md 和 experiments/layer-survey-toy-v1-2026-10-27/EXECUTION.zh-CN.md、readiness/active-survey.json。后者是当前运行路径、冻结身份、正式授权与128-token设置的唯一入口。若该文件状态仍为awaiting_token_length_clarification，不启动任何任务；报告等待用户澄清并保持自动化暂停。不得凭旧GPU验收记录声称正式任务已启动。

远程SSH别名gqa-h20，项目/workspace/acupuncture，Python为/workspace/acupuncture/.venv-bench/bin/python。实验目录以active-survey.json为准。正式控制器launch_survey.py按2B两卡、4B两卡、9B两卡顺序执行；每卡一个worker，实际batch1。每模型shard-0有基线八条；shard-1没有基线。固定正式总量7064条：2B 968+960，4B 1288+1280，9B 1288+1280。GPU验收66条不计入正式进度。禁止重复启动、不得恢复根因、判断/报告诊断、Q25—Q40、静态权重版或其他暂停实验。

每次读取当前controller.json、execution.json、六个worker的receipt与exit、真实PID及命令、GPU状态和必要错误日志；核验新增record_hashes对应文件与token哈希，不打印或语义阅读回答。文件可能尚未落盘或SSH瞬时失败时短暂重读；不凭旧日志、GPU显存或一次连接失败判断实验失败。分别报告每卡所在模型/分片、完整条件和逐题数量、上次以来增量、当前层与最后有效记录时间。候选回答变化、很早终止、乱码、达到128上限是待观察结果，不是技术bug。存在不活跃worker而收据running、真实非零exit、哈希或冻结不符、持续无新记录等情况，核实具体原因后报告异常。

ETA先读取readiness/gpu-readiness.json与active-survey.json的实际模式。已完成阶段用实测wall；进行中按模型、层和分片的有效记录与时间更新，以较慢卡为阶段剩余。前面层的短回答不能外推全部未观测层，未观测层/模型保留预检估计；另报全部128上限情景。正常结束与强制满128不能混用。计算、排队、故障修复、归档分开，不乘任意安全倍数；若无法可靠更新就如实说明。每次给剩余时间、北京时间预计完成点、与上次变化原因。

空间须检查/workspace/acupuncture、/data/models、/tmp各实际文件系统及本地归档盘，报告可用GiB和本轮输出大小，按实际增长估算余下输出与归档需求。不因95%使用率而忽略仍有足够绝对空间，也不把低空间风险藏起来。未经单独授权不删除旧结果、模型、缓存、其他项目或其他聊天文件。

发现真实技术bug，先保留失败日志、partial、源码身份、时间和退出码；只停止本轮必要进程。按冻结科学设计做最小修复，针对性CPU检查与受影响的必要模型验收通过后，用新身份/新输出目录继续。当前runner禁止原地续写partial；不得伪改旧receipt哈希以复用新版本。不得为了某种输出改题目、剂量、随机点、符号、精度、128结束规则、解码或模型。需要更改科学设计或外部权限时，说明阻塞并向用户请求必要决定。每次技术修复记录影响范围、原结果保留位置及更新ETA。

完成须六个worker均completed、exit全0、controller completed，本轮进程已退出；用survey.py verify逐分片核验冻结、题目、文件/token与权重恢复证据。取回全量证据及所有失败记录，运行export_survey.py导出完整并排原文和原始JSONL，核对whole_survey_complete=true、7064条含24基线，所有880单针条件各八题完整。列文件保留本地/远程且Git只留哈希。交付全部原文，不分析、评分、筛选或命名人格/功能区；仅报告完成、技术完整性与实际耗时。更新项目执行文档与active-survey为delivered，仅提交本项目文件；将本心跳PAUSED。
