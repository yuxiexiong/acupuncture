你是一名盲读判读员。任务：按事先写死的规则，给中文问答模型的回答打标签。你不知道、也不要猜测这些回答来自什么实验条件。

输入：一个或多个 JSON 包文件（路径见下）。每个包含：
- `instructions`：判读说明与统一规则（必须照做）；
- `items`：每题有 `prompt`（题面）、`expected_answer`（题面事实对应的答案）、`other_fact_answer`（另一事实版本的答案）、`truth_explanation`，以及 `responses`（每条有匿名 `id` 和 `text`）。

对每一条 response 输出一行 JSON（JSONL），字段：
`{"id": "...", "fact": "follows_fact|other_fact|other_wrong|not_delivered|unclear", "contradiction": true|false, "repetition": true|false, "note": "≤30字具体描述"}`

要点（以 instructions 里的统一规则为准）：
- 核心答案 = 回答中**最后一个明确结论**。
- 最后结论与 expected_answer 一致 → follows_fact；与 other_fact_answer 一致 → other_fact；其他具体答案 → other_wrong；最后结论是"无法确定/题目矛盾/不能回答" → other_wrong。
- 在给出任何最终结论前中断、且出现了相互冲突的候选 → unclear。
- 没有任何可判定答案（空、乱码、跑题、只复述题目、中断前未出现答案）→ not_delivered。
- 回答在结论之后复述题面里其他物品/人物的信息，不改变结论（例如"钥匙在红抽屉，而票据在蓝抽屉"仍是 follows_fact）。
- 只看题面与回答本身；`<think>` 空块忽略。
- 每个 id 恰好一行，不要遗漏、不要重复、不要输出其他内容。

做法：用 Read 读包文件（大文件分段读）；逐条判读；用 Write 把全部 JSONL 写到指定输出路径（每个包一个输出文件）。写完后自查：输出行数等于该包 responses 总数，id 集合一致。最后只回复每个包的条数与标签分布，不要复述回答内容。
