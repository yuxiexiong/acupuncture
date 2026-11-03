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

## Cache-mechanism planning rule (user correction, 2026-10-31)

- Before every next-stage plan for this line, reread its current purpose: explain how the model responds to a sparse activation intervention, how writing, old-state processing and subsequent reading change, and why these changes produce large answer effects. Withdrawal is a diagnostic condition, not the overall objective. Do not silently turn this into a new attack, EOS repair, or unrestricted cache survey.
- Read `docs/cache-mechanism-known-basics-audit-2026-10-31.zh-CN.md`. Separate architecture/implementation facts, conditional mathematical deductions, prior authors' results, our observed evidence, and untested hypotheses. Do not spend scientific experiment budget rediscovering what source or formulas already determine; retain necessary bounded engineering checks.
- Keep the research purpose stable. The user's subsequent clarification rejects repeatedly narrowing or redefining the core question: each experiment needs a clear purpose that directly advances the main question, and findings must accumulate toward the broader mechanism. A bounded experiment does not shrink the topic; do not default to making first-token EOS the research objective.
- State this experiment's purpose, the relation it tests, what outcomes would change our understanding, and how the result connects to existing assets and the broader mechanism. Use distinguishable predictions where appropriate; do not impose a single-unknown or two-hypothesis format on every useful experiment. Repeated localization is insufficient without a direct contribution; a cheaper experiment is not automatically useful.
- Reuse existing data and CPU/theoretical analysis first. Any proposed GPU budget must explain exactly what missing measurements justify it, including rebuilds and reference replays. Current instruction is no new GPU work; old plans are not authorization.
- Keep negative results and allow a branch to stop. Do not automatically expand layers, models, doses, or questions when results are weak or still ambiguous.

## 项目文档及时交付（用户指示，2026-11-01）

完成本项目的方案、必要自查记录或其他交付文档后，及时提交并推送到已确认的 GitHub 仓库，核对远端可读并向用户提供链接与提交号；不能仅交付本地路径。检查准确的暂存范围，保留远端和工作区其他改动，必要附件与索引一并交付。推送文档不构成 GPU 或模型运行授权。
