# 方法来源与 ML 项目适配

2026-11-12。这是根据用户要求写成的项目适配，不是上游原版安装，不声称上游作者认可本项目判断。来源读取身份和内容哈希见 [sources.json](sources.json)。不复制大型套件，不新增后台服务。

## 核心：Scientific Problem Selection

来源：[Anthropic scientific-problem-selection](https://github.com/anthropics/knowledge-work-plugins/blob/main/bio-research/skills/scientific-problem-selection/SKILL.md)。本次读其入口、[风险分析](https://github.com/anthropics/knowledge-work-plugins/blob/main/bio-research/skills/scientific-problem-selection/references/02-risk-assessment.md)、[价值标准](https://github.com/anthropics/knowledge-work-plugins/blob/main/bio-research/skills/scientific-problem-selection/references/03-optimization-function.md)和[决策树](https://github.com/anthropics/knowledge-work-plugins/blob/main/bio-research/skills/scientific-problem-selection/references/05-decision-tree.md)。

采用：明确区分执行与战略评价；根据新证据调整分支；把科学事实是否成立与技术能否测到分开；先面对可能使整个贡献不成立的依赖；不同研究类型采用不同价值标准。

适配：生命科学问题改成 ML 计算与经验问题；文献来源按需用论文原文、arXiv、会议官方与官方代码，不机械使用 PubMed。用户已提供背景时直接读取，不再问一遍入门问题。原版固定日程、年限、风险数字区间、固定替代方案数量和产物页数不作为项目要求。没有证据时保留不确定性，不制造概率。关注时点由用户的每次方向/设计/阶段决策触发，不创建定时自动化。

## 补充：HKUSTDial Idea Evaluator

来源：[idea-evaluator](https://github.com/HKUSTDial/Supervisor-Skills/blob/main/skills/idea-evaluator/SKILL.md)，[fatal-flaws](https://github.com/HKUSTDial/Supervisor-Skills/blob/main/skills/idea-evaluator/references/fatal-flaws.md)，入口声明 CC-BY-4.0；作者项目 HKUSTDial/Supervisor-Skills。本文件为独立改写与适配。

采用：具体致命缺陷先于宣传；用用户实际资源检查可行性；最强近邻需要原文；检验范围失控、主张无法由证据识别、方法先行而缺问题动机。

不采用机械的 Higher/Faster/Stronger/Cheaper/Broader 五维总分、固定8分门槛、论文寿命估计和“有几条缺点就自动转向”。纯机制贡献不需要性能提升或立即部署收益。基线优于某方法，只反对相应性能主张，不能自动推翻一切机制解释；单次阴性只裁决所测操作。已有工作存在不是否决理由，组合新颖也不是价值证据。不同之处必须有科学或实践后果。

## 证据与假设

本机 [hypothesis-generation](/Users/ruizhixu/.codex/skills/hypothesis-generation/SKILL.md) 2.4：观察、研究问题、候选解释、预测、因果估计对象和分析计划分开；列合理竞争解释；旧数据产生的假设保持探索身份；解释未验证与被数据否定分开。

本机 [scientific-critical-thinking](/Users/ruizhixu/.codex/skills/scientific-critical-thinking/SKILL.md) 1.5：先固定比较对象、终点与单位，再取证；核对反证、依赖和适用范围；缺报告不等于没执行；因果语言与实际干预匹配。

两者已有安装，本项目直接复用；如文件不可用，以上原则仍是本 skill 的可执行基础，披露未读取原文，不以安装缺失为虚构通过的理由。K-Dense 项目来源为 scientific-agent-skills；本地既有准备记录见 `docs/evidence-rediscovery-2026-11-12/EXECUTION.zh-CN.md`。引用：Kassis, T., Agarwal, V., He, Y., Patel, D., & Brueckner, A. M. (2026). *Scientific Agent Skills: A Library of Procedural Knowledge for Research Agents*. https://doi.org/10.48550/arXiv.2609.00065 。2026-11-12核对arXiv记录，当前v2、未见期刊引用；原始来源版本与实际文件哈希分别记录，不把hash当质量认证。

## ARS Socratic Mentor 的边界

检查了本机 ARS deep-research 的 `agents/socratic_mentor_agent.md`。可借其区分主线与表面措辞、警惕持续附和的思路，但不启用其“只提问、不给结论”和强制提问模式。用户需要明确判断与纠正，不能把责任全部交回用户；不扮演真实主编或教授，不把角色设定当资历。

## 本项目的额外要求

- 成功上限：假如预想结果全部出现，得到的认识是否足够重要？仅多一个条件依赖不自动通过。
- 证据连接：跨背景、跨终点、跨任务的连接需要依据；缺口可以保留，不一定追加实验填齐。
- 退出有动作：失败解释退出、取消相应队列或推荐；不能阴性后改名继续。成功足够时也停止细拆。
- 合理风险可接受：不要求每轮完整机制、所有干预同因或零副作用；未验证不能当否定，不能靠越缩越小使无意义实验通过。
- 不以资料更多、近邻更少、近期结果更新、用户没反驳某方向来推荐方向。
