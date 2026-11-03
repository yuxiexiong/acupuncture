# 2026-11-04 已有证据归档收据

## 范围与快照

用户要求把资产盘点和理论／实验骨干之后的材料补齐、如实整理并交付GitHub。本次以远端main `9b83017a281dc4d4b54b27d5cafec483dcae66f4` 建立隔离Git工作树；提交前合入远端`2d2b728d`的并行WSP工程交付。其两份文件与较早本地捕获版本不同，已将早版本改存`local-variants`、主路径保留远端版本；导入清单记录此次转移。保留主工作区的旧分支和所有未提交内容，未把主工作区旧版本覆盖到远端。

来源主目录：`/Users/ruizhixu/Documents/ChatGPT/acupuncture`，其HEAD为`3d00273b`。本地文件捕获时间为北京时间 **2026-11-04 01:13:22–01:13:25**，逐文件UTC时间在[local-import.json](local-import.json)。WSP文件来自活动队列，是分文件快照，非原子备份；本次没有调用编辑器、运行模型、启动GPU、重试或中断队列。

扫描覆盖最新远端交付树、主工作区未跟踪／修改文件、全部已登记工作树的Git状态，以及本地被Git忽略的实验资产。另一处早期交付工作树的13个未提交文件全部与主目录逐字节相同，见[对账](other-worktree-check.json)。其他登记工作树在检查时均干净。Git分支指针保存在[refs快照](git-refs-at-start.txt)，不是把未合并方案当结果。

没有宣称扫描了未知机器、所有历史聊天或服务器的全部目录。历史Stealthiness来源不改动；已迁移证据沿用[此前迁移清单](../2026-10-28-full-results-git-r01/README.zh-CN.md)。本次新材料都属于Acupuncture仓库。

## 导入结果

| 处理 | 文件数 | 解释 |
|---|---:|---|
| 补入原路径 | 4,491 | 双针联合测量、CPU分析、历史协议、阅读原文等原件 |
| 运行快照 | 5,161 | 原`external/`迁入WSP实验的[local-runtime-archive-r01](../../experiments/wsp-process-reproduction-v1-2026-11-03/local-runtime-archive-r01/README.zh-CN.md)，保留原子路径；含验收夹具，不都是正式实验 |
| 历史不同版本 | 45 | 放在[local-variants](local-variants/)，不覆盖最新同名文件 |
| 已完全相同 | 772 | 不重复复制 |
| 仅登记哈希 | 23 | 2份private-key盲评映射、1份上游MBPP原下载、20份瞬时进程锁；原文件保留本地 |
| CFM-S3缺位原记录 | 26 | 从本次导入的来源副本补回原实验路径，原收据哈希全部一致；见[补位映射](restored-records.json) |

前三行共9,697个文件、215,210,239字节；CFM-S3补位另外26个路径、53,380,605字节，是相同原记录的第二个位置，不增加样本或采集成本。Git可按相同内容去重。原件中的历史建议、已撤回解释与失败状态不重写；当前结论见[理论与实验总览](../../docs/RESEARCH_ARCHIVE_2026-11-04.zh-CN.md)。

## 大文件、私有映射和上游数据

- [本地外置资产清单](local-external-assets.json)列出本地实验目录中被忽略的9,063个非临时文件，共5,142,448,296字节及SHA-256。包括已有轨迹、张量和私有映射等；它们**没有上传Git**。清单是位置／身份登记，不是删除许可。
- [缓存核验](verification.json)另收集2,232个tensor哈希引用，实际张量仍按各receipt的服务器路径保存。引用可能重复；本轮未登录服务器逐字节重验全部张量，不能称为完整独立备份或全计算复现。
- 模型权重、虚拟环境、凭据、缓存和上游大批下载不提交。MBPP来源沿用[WCP来源清单](../../experiments/wsp-coding-painpoint-v1-2026-11-03/receipts/sources-manifest.json)。本次只提交项目产生的选择／审查记录，单份上游原下载以本地哈希登记。
- 两份`private-key.json`是盲评映射，不是API密钥；为保持其private身份，仅登记哈希。`.lock`是运行锁，不作为可执行恢复状态导入。

## 验证与明确限制

1. **9,697个导入文件**逐字节SHA-256一致，未修改原始内容。
2. 缓存实验目录的worker收据中，**2,271份record_hashes全部匹配**，当前预期路径缺失0、哈希不符0。这只覆盖脚本列明的`cache-*/runs/*/worker-*/receipt.json`，不冒充每个项目文件都重跑验收。
3. **NCC、NSR、NQK、NPC各48输入**从原记录标签重新加总完整正确数，与新总览表一致。标签本身没有重作语义判断；这不是独立人工评审。
4. 新导入JSON中有**1份空的历史草稿**`joint-behavior-capability-v1-2026-10-28/readiness/tokenizer-draft-r01.json`无法解析，原样保留并登记，不把它当有效收据。9份工程SQLite快照的只读`quick_check`均为ok；见[格式审计](format-audit.json)。这不保证活动队列多个文件的事务一致。
5. 新报告区分架构事实、条件推导、历史作者报告、我们的干预／观察结果与未测假设；保留失败预测、更正与反例。未增加文献新颖性主张、实验设计或执行授权。
6. 本次为同一助手的资料与算术核对：`ANALYZED_NO_MODEL_RERUN`。工程passed不等于科学阳性，来源哈希匹配不等于完整理论已证实。

## 文件级清单与复查

[assets.jsonl](assets.jsonl)逐行记录交付树内`experiments/`、`docs/`及历史`migration/`资产的路径、大小、SHA-256，包含本轮历史不同版本；[inventory-summary.json](inventory-summary.json)记精确总数。为避免自引用，清单排除本次派生目录表和本次migration下的清单／核验文件本身；这部分由Git提交固定。

[全目录表](../../docs/RESEARCH_ASSET_CATALOG_2026-11-04.zh-CN.md)覆盖116个一级实验／设计／审计／工程目录。文件及目录数不能相加成独立实验数；同源CPU复算、参照重放、来源副本都不增加独立样本。

在交付Git工作树根目录，可只读核验已导入文件和收据，并重算四轮Y计数：

```sh
python3 migration/2026-11-04-evidence-archive-r01/verify_archive.py
```

脚本只读已有证据、写本次核验JSON，不导入模型包。`import_local.py`是一轮导入工具，有已存在快照保护；不要把它当同步器反复运行。`build_inventory.py`只计算哈希和生成目录，重建外置清单需要本地原资产路径可用。
