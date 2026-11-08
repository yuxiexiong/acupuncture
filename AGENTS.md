# Acupuncture project instructions

- Project name: **Acupuncture**.
- Canonical repository: `https://github.com/yuxiexiong/acupuncture.git`.
- Canonical local root: `/Users/ruizhixu/Documents/ChatGPT/acupuncture`.
- All future project code, protocols, notes, analyses, and deliverable results belong in this repository. Do not create new Acupuncture work under `stealthiness`; that location is a preserved historical source.
- Use `experiments/` for versioned runs and their code/evidence, and `docs/` for project-wide research notes. Reuse the existing structure; do not add speculative infrastructure.
- Keep raw responses, failed attempts, fixed questions, source hashes, settings, and historical receipts intact. Corrected implementations and new experiments need separate versioned runs.
- Distinguish observed results, author-reported evidence, hypotheses, and unrun plans. Do not label these channels as established morality or safety neurons.
- Preserve the Q24 user-stop boundary for the first corpus. Repository migration is not authorization to restart Q25–Q40, run an old pilot, run static weight edits, or begin new model experiments. Respect the applicable user authorization for each subsequent run.
- Existing remote jobs may finish at their recorded historical paths. Do not interrupt them solely for a rename; bring their completed evidence into this repository with provenance.
- Keep model weights, upstream bulk downloads, virtual environments, caches, and credentials out of Git. Commit source/revision/URL/hash manifests for external assets; preserve project-produced raw evidence unless there is a concrete size or privacy issue.
- Inspect the exact staged files before a push. Do not stage unrelated material from other projects. This user has designated this repository for project delivery.
- Think before coding: state consequential assumptions and distinguish competing interpretations. Prefer the smallest correct implementation, make surgical changes, and verify the requested outcome.

Read `README.md`, `docs/RESEARCH_STATUS.zh-CN.md`, and the relevant experiment's protocol and receipt before continuing work.

## Mandatory experiment-design self-check (user instruction, 2026-10-31)

- Before delivering any new experiment design or substantive revision, read and apply `docs/experiment-design-self-check.zh-CN.md`. This applies to both research lines, including exploratory analyses and supplementary experiments.
- Record the design card, C01–C14 decisions with reasons, relevant historical errors, comparison with the previous design, and a substantive adversarial self-check. Revise failed designs and recheck before presenting a proposed experiment to the user; do not outsource known logical flaws to user review.
- Keep the main research question stable and require a useful, bounded increment. Do not demand complete mechanism identification in each round, add controls merely for completeness, or lower claims until a scientifically empty experiment passes.
- Separate logical design review, implementation/numerical acceptance, execution authorization, and actual results. Self-review is not independent review. If missing evidence genuinely prevents a valid design, report the specific blocker rather than inventing a pass.
- This is a standing quality requirement, not a new permission workflow. Existing user authorization remains effective; a passed checklist itself grants no GPU or model-run authorization.

- Cache-line main question: explain how the needle changes internal computation, writing, old-state processing and reading to produce large answer effects. Withdrawal is a diagnostic condition, not the overall objective.

## 项目文档及时交付（用户指示，2026-11-01）

完成本项目的方案、必要自查记录或其他交付文档后，及时提交并推送到已确认的 GitHub 仓库，核对远端可读并向用户提供链接与提交号；不能仅交付本地路径。检查准确的暂存范围，保留远端和工作区其他改动，必要附件与索引一并交付。推送文档不构成 GPU 或模型运行授权。

## 缓存机制线现行目标（用户确认，2026-11-08）

- 继续缓存机制线前，读取 [现行核心目标与任务口径](docs/cache-mechanism-current-goal.zh-CN.md)。它是当前目标入口；旧路线图、To-do、论文及补证方案中的“下一步”按历史版本阅读，用户后续指示优先。
- 主线 A 保持：解释针怎样改变历史形成、写入、旧状态处理和后续读取，最终影响完整回答。下一阶段先解释一项重要历史信号的写入或利用及其答案后果；允许有价值的部分解释，不把统一所有针／任务／成功失败设为贡献前提。
- 每项任务说明具体差异、认识增量、已有依据与结束条件。不把已知公式或更多阳性当新认识，不默认围绕 N4146 继续细拆，不因未知而自动扩模型；已有局部因果证据也不因尚未解释完整原生机制而被否定。
- 本次授权是目标文档与仓库口径同步、提交推送，不包含改被审正文、设计或运行新实验。后续新设计仍适用完整自查；旧方案、设计通过及文档发布均不构成新的模型／GPU授权。
