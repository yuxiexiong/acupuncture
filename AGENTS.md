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
