# sub_b：物体幻觉评测——饱和度与"评测产物"证据（草稿，2026-11-06）

状态：**终稿**（16:5x 先落过一版中间稿，之后补了 6 条查询、9 篇正文与一次被引扫描；补充内容已并入各节，另有 §2.4 汇总新增的关键证据）。
阅读层级：F = 取到正文并核对了对应表或段落（本稿的 F 绝大多数是**定点阅读**：只读了相关表与相邻段，没有通读方法与局限）；A = 只读摘要；S = 只见检索片段或别人表里的转引。逐字引文全部在下载的 .txt 里 grep 核对过；没核对的不加引号。

---

## 0. 最不利的几条先说

1. **"POPE 饱和"是多篇论文的明文结论，但"物体幻觉已解决"没有一篇这样写**；找到的原话方向相反（DASH："Contrary to the belief that object hallucinations are no longer an issue…"）。查询 1 条专搜 "largely solved / no longer the bottleneck / nearly solved"，0 命中（结论层，1 条查询，不能写成"没人说过"）。
2. **CHAIR 在新模型上没有饱和，但数字几乎完全由 max_new_tokens 决定**：同一个 Qwen3-VL-8B，64 token 时 CHAIR_S 8.0–8.4，512 时 45.0，1024 时 51.4，另一篇（未注明 token 上限）58.8。跨论文比较 CHAIR 基线没有意义，除非口径对齐。
3. 你提到的 **Qwen3-VL-8B CHAIR_S 51.6 我没找到出处**。最接近的是 GIFT（2510.22067）Table 2 的 51.4（greedy，max_new_tokens=1024，500 张 COCO 图）。缓存全库 grep "51.6" 无 Qwen3 行。
4. **OpenReview 审稿意见一条也没取到**：Mirage 的论坛号查到了（wGeQr5cARm，NeurIPS 2025 poster），但论坛接口与页面都返回人机验证（403 ChallengeRequired），我没有绕。DASH、VCD 未查到公开审稿。
5. "修法在新模型上收益消失"的**独立复核型**证据不多但有：Mirage、2609.01888（你已读）之外，**2607.25196（Rethinking the Effectiveness of Contrastive Decoding）在 Qwen2.5-VL-7B 与 InternVL3-8B 上直接做了**——greedy 的 CHAIR 全面优于 VCD/SID，把对比项换成高斯噪声分数不变或更好（见 §2.4）。这是与你们可能想写的"对比解码收益是解码行为变化"**结论层重合**的一篇。其余多是新方法论文里顺带的基线表（作者有动机让基线难看）；HQH、POPE token 审计用的是旧模型。
6. 属性/关系/计数在新模型上的逐类数字只拿到零散几条 F 级：CRPE relation、MIHBench count、VAW 颜色探针 FPR（Qwen2.5-VL-3B 33.8%、InternVL3.5-4B 31.6%）、VLMBias 计数 17.05%（摘要）。AMBER 判别式逐类表没找到含 Qwen2.5-VL/InternVL3 的。
7. 被引扫描只做成一篇：Semantic Scholar 接口限流，RePOPE 与 DASH 的被引没拿到；Mirage 只返回 7 条被引（接口收录显然不全）。

---

## 问题 1：新一代模型上是否饱和，剩余空间在哪

### 1.1 模型 × 基准数字表（全部 F，除非另注；空格 = 没找到）

**(A) POPE（存在性，yes/no）**

| 模型 | 数字 | 口径 | 出处 |
|---|---|---|---|
| 17 个开源模型（InternVL2.5 8B–78B、LLaVA-NeXT×3、LLaVA-OV、Ovis2 1B–8B、PaliGemma/2） | POPE 三 split 平均 F1 **85.7–90.1**，Acc 87.1–90.5 | 原始标签 | RePOPE 2504.15707 Tab.2 |
| 同上 | random F1 86.9–94.7；popular 85.6–90.1；adversarial 83.5–88.3 | 原始标签 | 同上 Tab.3–5 |
| 同上 | **RePOPE** 平均 F1 88.2–94.2，Acc 88.2–94.9；random F1 92.1–95.9；popular 88.2–94.1；adversarial 83.5–93.1 | 改正标签、去掉歧义题 | 同上 Tab.6–9 |
| InternVL3-1B / 2B / 8B / 14B / 38B / 78B | POPE avg 90.7 / 89.6 / 91.1 / 90.2 / 90.6 / 90.3 | 官方表，"avg" | InternVL3 2504.10479 Tab.5 |
| InternVL2.5-8B；Qwen2-VL-7B；MiniCPM-V2.6；GPT-4o-20240513 | 90.6；88.1；87.3；**86.9** | 同上（部分转引自 OpenCompass，原文注明） | 同上 |
| Qwen2-VL 7B / Qwen2.5-VL 7B / InternVL2.5 8B / InternVL3 8B / LLaVA-OV 7B | POPE-adversarial(COCO) F1 87.20 / 87.08 / 89.88 / 90.50 / 89.48；precision 93.11 / 93.98 / 89.76 / 88.08 / 90.52 | 该文自测 | HOPE 2508.06530 Tab.2 |
| Qwen2-VL 7B / Qwen2.5-VL 7B / Qwen3-VL 8B | POPE COCO adversarial Acc 85.3 / 85.6 / 86.2，F1 84.5 / 85.1 / 85.8 | vanilla | SHIELD 2510.16596（ICLR 2026）Tab.15 |
| Qwen3-VL 8B；Qwen2-VL 7B；LLaVA-1.5 7B | F1 88.9 / 86.0 / 82.4；Acc 88.5 / 86.5 / 79.5 | 9 个 split（COCO、A-OKVQA、GQA ×3）宏平均，greedy，max_new_tokens=10 | GIFT 2510.22067 Tab.2 |
| Qwen3-VL（尺寸未核） | Acc 89.05，Recall 85.00，F1 88.62 | "averaged metrics" | REVIS 2602.11824 Tab.14 |
| InternVL3 / InternVL3.5（尺寸未核） | Acc ≈90.2–90.5 / 88.14 | 正文叙述 | REVIS App.F.4 |
| GPT-4o-mini | POPE 上只对 77.5% 的图给出有效回答，其中 TNR 92.7% | | DASH 2503.23573 Tab.3 脚注 |

读法：POPE 平均 F1/Acc 在 2024 年末以后的开源模型上集中在 **85–91**，InternVL3 从 1B 到 78B 基本持平（89.6–91.1）——参数量放大 78 倍没有带来 POPE 增益（推导：直接读表）。

**(B) POPE 与标注噪声上限**

- RePOPE Tab.1：POPE 标 "Yes" 的题里 **9.3% 标错、13.8% 歧义**；标 "No" 的题里 1.7% 标错、4.3% 歧义（random 0.3%/1.3%，popular 2.6%/4.4%，adversarial 2.2%/7.3%）。
- 推导（我的算术，非原文）：正例占一半、正例错标 9.3% → 即使模型全对，原始 POPE 的 recall 上限约 90.7%（不计歧义题）；若歧义题按一半算错则约 84%。所以原始 POPE 上 F1 ≈ 90 已贴近或进入标注噪声带。这条是推导档，原文没有给出"上限"这个数。
- RePOPE 原话（§4.2）："This questions how reliable this kind of error can be measured on this split and suggests that the negative set is saturated on POPE random."
- RePOPE 原话（结论）："Note that this re-labeling has only a limited effect on the saturation of the benchmark (many models acchieve true positive rates as well as true negative rates of more than 90%. To overcome this, other benchmarks need to be evaluated complimentary, e.g. DASH-B [1] which follows a similar design as POPE with a “harder” negative set."（原文拼写与括号如此）
- RePOPE 原话："Some models that achieve some of the best F1 scores in the POPE ranking, e.g. InternVL2.5-8B or -26B, drop to the bottom of the ranking after evaluating on the RePOPE labels."——即改标签后**排名大变**（InternVL2.5-26B：POPE 平均第 1 → RePOPE 平均第 10；Ovis2-4B：第 3 → 第 1）。
- DASH App.H：PaliGemma 在 POPE 4500 道负例上只答了 137 次 "Yes"；重标后其中 35 个（25.5%）图里其实有该物体，31 个（22.6%）歧义。原话："This large amount of label noise among the remaining false positives indicates that the POPE benchmark is saturated."
- DASH §4.3 原话："Given the label noise (see App. H), the high true negative rates (TNR) on POPE (96.0%±1.2%) suggest that the benchmark is saturated and provides limited insight regarding FP-hallucinations. In contrast, the models exhibit a significantly lower TNR on DASH-B (48.6%±10.1%)."（数字取自 arXiv HTML 的公式 alttext）

**(C) 更难的存在性集合（同样是 yes/no，但负例更难）——存在性本身并未解决**

| 基准 | 模型与数字 | 出处 |
|---|---|---|
| DASH-B（2642 张，ReLAION 真实图，70 类） | Acc：LLaVA-OV 75.1，Ovis2-8B 71.4，PaliGemma2-3B 68.9，InternVL2.5-8B/26B/38B/78B 71.7/77.5/76.2/74.1，GPT-4o-mini **86.3**；TNR：44.8–60.2（开源），GPT-4o-mini 77.0（Tab.6；Tab.3 写 76.7，原文两处不一致） | DASH Tab.3、Tab.6 |
| HOPE（COCO，描述式干扰项） | precision：LLaVA-Next 66.51，LLaVA-OV 67.93，Qwen2-VL 76.00，Qwen2.5-VL 7B 81.35，InternVL2.5 8B 80.72，InternVL3 8B 75.35（同一批模型 POPE-adv precision 88–94） | HOPE 2508.06530 Tab.2 |
| HOPE（Objects365，"All" 策略，二元提示） | precision：Qwen2.5-VL 7B 67.83，InternVL3 8B 60.86，InternVL2.5 8B 62.81 | 同上 Tab.1 |

注意：DASH-B 的负例是"对 Qwen2-VL-72B 与 Llama-3.2-11B 都成功诱发幻觉的图"筛出来的，HOPE 是对抗搜索出来的——它们量的是**最坏情况**，不是自然分布上的错误率。这条轴和 POPE 的平均情况不能互推。

**(D) CHAIR（COCO 描述，生成式）——同一模型随 token 上限相差 6 倍**

| 模型 | CHAIR_S / CHAIR_I | max_new_tokens；解码；图数 | 出处 |
|---|---|---|---|
| Qwen3-VL-8B-Instruct | 8.40 / 4.62 | 64；—；500 | HIME 2602.18711 Tab.2 |
| Qwen3-VL（尺寸未核） | 8.00 / 3.35；17.00 / 5.79；45.00 / 9.06 | 64；128；512（数值全为整数，样本量可能很小，未核） | REVIS 2602.11824 Tab.14 |
| Qwen3-VL 8B | **51.4** / 10.6 | 1024；greedy；500 | GIFT 2510.22067 Tab.2 + App. |
| Qwen3-VL-8B | **58.80** / 10.57（F1 75.29） | 正文未检到 token 上限；提示 "Describe the image." | SAVAA 2602.13600 Tab.1 |
| Qwen2.5-VL（尺寸未核） | 14.0 / 6.42；28.0 / 8.18；31.0 / 8.13 | 64；128；512 | REVIS Tab.16 |
| Qwen2.5-VL（尺寸未核） | 47.4 / 10 | 512；greedy | 2602.21704（ICLR 2026）App. 表 |
| Qwen2.5-VL-32B | 9.00 / 5.26；22.00 / 6.72；52.00 / 11.05 | 64；128；512 | REVIS Tab.12 |
| Qwen2-VL 7B | 24.8 / 9.1 | 1024；greedy | GIFT Tab.2 |
| Qwen2-VL-8B-Instruct（原文如此） | 20.8 / 5.36 | 64 | HIME Tab.2 |
| InternVL3 | 28.4 / 7.6；29.0 / — | 512 greedy；（REVIS 口径未核） | 2602.21704；REVIS App.F.4 |
| InternVL3.5(-8B) | 30.0 / —；41.40 / 10.80 | REVIS；SAVAA | REVIS App.F.4；SAVAA Tab.1 |
| LLaVA-NeXT-7B | 33.80 / 8.46 | SAVAA | SAVAA Tab.1 |
| LLaVA-1.5 7B（对照） | 50.2 / 15.4 | 1024 greedy | GIFT Tab.2 |
| Qwen2.5-VL-7B-Instruct | greedy **22.8 / 7.3**；采样 31.2 / 10.4 | token 上限正文未检到；500 张 | 2607.25196 Tab.3 |
| InternVL3-8B | greedy **29.4 / 8.1**；采样 33.5 / 9.1 | 同上 | 同上 |
| LLaVA-v1.5-7B（对照） | greedy 50.0 / 13.9；采样 57.4 / 17.3 | 同上 | 同上 |

读法（推导）：
- Qwen3-VL-8B 的 CHAIR_S 51.4（1024 token）与 LLaVA-1.5-7B 的 50.2 持平，尽管前者 POPE 与 MMHal 都更好。GIFT 作者原话："We observe that Qwen3-VL 8B, despite achieving the best performance on POPE and MMHal-Bench, shows higher CHAIR scores than other models. We attribute this to its tendency to generate detailed, reasoning-based descriptions that may be penalized by CHAIR’s string-matching approach against predefined objects, suggesting the metric may need refinement for modern models producing nuanced outputs."——作者把它归给**度量问题**（"we attribute"，未做实验区分是真幻觉还是字符串匹配误判；这是一个开口）。
- CHAIR_I（每个提到的物体里幻觉占比）在新模型上是 3–11，比 CHAIR_S 稳定得多；CHAIR_S 高主要因为"描述越长，至少出现一个幻觉物体的概率越大"（推导；与 LeHaCE 的线性关系一致，见问题 2）。

**(E) 其他基准**

| 基准（量什么） | 模型与数字 | 出处 |
|---|---|---|
| HallusionBench（图像上下文推理 + 视觉错觉；不是纯物体存在） | InternVL3-8B 49.9，-78B 59.1；Qwen2.5-VL-7B 52.9，-72B 55.2；GPT-4o-20240513 55.0；Claude-3.5-Sonnet 55.5；Gemini-1.5-Pro 45.6 | InternVL3 Tab.5（部分转引） |
| HallusionBench | Qwen3-VL-235B thinking/instruct 66.7/63.2；Gemini 2.5 Pro 63.7/60.9；GPT-5 high/minimal 65.7/53.7；Claude Opus 4.1 60.4/55.1；Qwen3-VL-8B 65.4/61.1，-4B 64.1/57.6，-2B 54.9/51.4；GPT-5 nano 58.4/39.3 | Qwen3-VL 技术报告 2511.21631 Tab.2–4 |
| MMHal-Bench（score 0–6 ↑ / Hal 率 ↓） | InternVL3-8B 3.61，-78B 3.85，InternVL2.5-78B 3.89，GPT-4o 4.00 | InternVL3 Tab.5 |
| MMHal-Bench | Qwen3-VL 8B：Hal 28.3%，score 4.80；Qwen2-VL 7B：32.7%，3.53；LLaVA-1.5 7B：65.2%，2.22（GPT-4.1 打分） | GIFT Tab.2 |
| CRPE relation（关系） | InternVL3-8B 76.3，-78B 79.2；Qwen2.5-VL-7B 76.4，-72B 79.2；GPT-4o 76.6 | InternVL3 Tab.5 |
| AMBER 生成式（CHAIR ↓ / Cover ↑ / Hal ↓ / Cog ↓） | Qwen3-VL-8B 7.66 / 73.59 / **59.24** / 3.75；InternVL3.5-8B 7.49 / 74.24 / **62.20** / 5.95；LLaVA-NeXT-7B 7.83 / 63.87 / 49.20 / 4.33 | SAVAA Tab.3 |
| AMBER 判别式逐类（existence / attribute / relation） | **未找到含新模型的 F 级逐类表**（2 条查询）。AMBER 原文称 existence 不是主要弱点、relation 最差——S | — |
| MIHBench（多图：存在 / 计数 / 身份一致，yes/no） | 存在 Acc：Qwen2.5-VL 71.59，InternVL2.5 74.00，LLaVA-NeXT-Interleave 75.75，Mantis 63.67；计数 Acc：57.75 / 53.13 / 55.13 / 52.38（recall 仅 18.25 / 9.25 / 16.00 / 10.75）；身份一致 Acc：68.75 / 71.38 / 51.88 / 62.63 | MIHBench 2508.00726（ACM MM 2025）Tab.2 |
| HAVEN（视频幻觉） | 总准确率最好 Valley-Eagle-7B 61.29；GPT-4o-mini 56.80；Qwen2.5-VL-7B 50.19 | HAVEN 2503.19622 表 |
| MM-Snowball（多轮、带诱导的 6 轮对话；Turn-5 准确率 / VFR ↓） | Qwen3-VL-8B 5.05 / 91.81；Qwen3-VL-32B 9.35 / 84.40；Qwen2.5-VL-7B 3.15 / 93.86；Gemini 2.5 Flash 10.60 / 82.97；GPT-5 49.35 / 27.37；Kimi K2.5 65.15 / −0.15；Seed-1.6 62.55 / 4.65 | MM-Snowball 2606.00622（ICML 2026）Tab.2 |
| DOCCI-Critique（100 张 DOCCI 图的段落描述，人工逐句标事实性；"% Correct Sentence"） | LLaVA-1.5-7B 60.0；LLaVA-OV-7B 81.8；Molmo-7B-D 82.7；Qwen2-VL-7B 87.6；Gemini-1.5-Pro 95.1；Gemini-1.5-Flash 96.1；GPT-4o(2024-08-06) **97.1**；14 模型合计 76.5。平均 4–12 句/段 | 2506.07631 Tab.2（只有 2024 年及以前的模型） |
| DeCapBench（DCScore ↑，兼顾幻觉与全面性） | GPT-4o 53.44；Claude-3.5-Sonnet 52.37；InternVL-2-26B 49.59；Gemini-1.5-Pro 46.34；LLaVA-OV-7B 43.49 | 2503.07906 Tab.7（取末列；列头未逐一核对） |
| VAW 颜色属性 yes/no 探针（假阳性率 FPR ↓） | Qwen2.5-VL-3B 33.8%；InternVL3.5-4B 31.6%；LLaVA-1.5-7B 47.2% | 2608.11024 Tab.（预印本，6 千词；样本 2,992） |
| VLMBias（反事实图上的计数/识别，Gemini-2.5 Pro、o3、o4-mini、Sonnet-3.7、GPT-4.1） | 计数平均准确率 **17.05%**；去掉背景后 +21.09 点 | 2505.23941（ICLR 2026）摘要——**A** |
| VideoHallu（合成视频） | Gemini-2.5-Pro ≈49.8，GPT-4o ≈45.5，Qwen2.5-VL-32B ≈51.4 | **S**（检索片段，2505.01481） |
| VidHal（时序幻觉） | Gemini-2.5 Pro 0.814，Qwen2.5-VL-7B 0.760；InternVL3-8B 80.9（聚合站） | **S** |
| DetailVerifyBench（长描述幻觉定位，2604.05623） | DOCCI 自然图幻觉率约 26%，图表/GUI/电影/海报 41–90% | **S** |
| ELV-Halluc（长视频语义聚合） | Gemini-2.5 Flash ≈53%，GPT-4o ≈8.7%，Qwen2.5-VL-72B ≈32% | **S** |
| MIOH（多图细粒度，CVPR 2026） | Qwen2.5-VL-3B 44.3 | **S** |
| Common-O（跨场景共同物体） | GPT-4o 35% | **S** |
| THRONE、HaloQuest、RePOPE 之外的 DASH 系、DOCCI/IIW/CAPTURE 上的新模型数字 | **未找到**（THRONE 原文只有 2023 年的 11 个模型） | — |

### 1.2 各类幻觉的剩余空间（"多少"轴逐条分开，不互推）

| 类别 | 现状 | 证据级 | 出处 |
|---|---|---|---|
| 存在性，yes/no，COCO 自然图（POPE） | F1/Acc 85–91，TNR ≈96%，剩下的假阳性约一半是标注错或歧义 → **在该分布上已量不出差别** | F | RePOPE、DASH |
| 存在性，yes/no，难负例（DASH-B、HOPE） | 开源 Acc 54–78、TNR 10–60；GPT-4o-mini 86；HOPE precision 60–81 → **剩余空间大**，但是最坏情况口径 | F | DASH、HOPE |
| 存在性，描述任务（CHAIR、AMBER 生成式） | CHAIR_I 3–11；CHAIR_S 8（64 tok）到 45–59（≥512 tok）；AMBER Hal 率 59–62%（Qwen3-VL-8B、InternVL3.5-8B） → **长输出下未饱和**；但 CHAIR 本身的可信度受质疑（见问题 2） | F | REVIS、GIFT、SAVAA、HIME |
| 关系 | CRPE relation 76–79，7B 到 78B 只涨约 3 点，GPT-4o 76.6 | F（官方表，部分转引） | InternVL3 Tab.5 |
| 属性（颜色，VAW yes/no 探针） | 小尺寸新模型 FPR 31.6–33.8%（Qwen2.5-VL-3B、InternVL3.5-4B）；该文称材质类的高 FPR 部分是标注粒度噪声（steel：45.5% → 4.5%） | F（定点；预印本） | 2608.11024 |
| 计数（多图） | MIHBench count Acc 52–58（接近随机 50），recall 9–18 | F | MIHBench |
| 计数（反事实图） | 2025 年旗舰闭源模型平均 17.05% | A | VLMBias 2505.23941 |
| 长描述 | 人工逐句口径：2024 年开源 7B 每句错 12–18%，GPT-4o / Gemini-1.5 每句错 3–5%（推导：段落 6–12 句 → 开源 7B 的多数段落至少含一处错）；CHAIR/AMBER 512–1024 token 口径见上；**2025–2026 新模型在 DOCCI/IIW/CAPTURE 上的数字未取到** | F（旧模型）/ 无（新模型） | DOCCI-Critique 2506.07631 |
| 多图 | 见 MIHBench；MIOH、Common-O 只有 S | F / S | — |
| 视频 | HAVEN 最好 61%；其余 S | F / S | — |
| 多轮 | MM-Snowball Turn-5：多数模型 3–11%，仅 GPT-5 / Kimi K2.5 / Seed-1.6 在 49–65% | F | MM-Snowball |
| 推理型/错觉（HallusionBench） | 2025 末旗舰 60–67，人类上限未核 | F | Qwen3-VL 报告 |

注意两点口径：(i) MM-Snowball 的对话里有一个"Deceptive Attacker"在第 3–5 轮施压，量的是**抗诱导**，不是自然多轮对话下的自发幻觉累积；(ii) Qwen3-VL 官方技术报告全文没有 POPE 与 CHAIR（grep "POPE" 0 命中），幻觉类只报 HallusionBench——官方评测已不再用 POPE（事实陈述，不推断动机）。

### 1.3 逐字"饱和 / 未饱和"原话汇总

说**饱和**（都限定在 POPE 或某个具体基准上）：
- DASH §4.3："As the popular POPE [24] benchmark for object hallucinations seems saturated and contains significant label noise, a novel hard object hallucination benchmark is needed to measure further progress."
- DASH §2（说的是 AMBER）："While object hallucinations saturate in their benchmark for VLMs, we demonstrate that a substantial number of systematic object hallucinations persist even in current models such as Qwen2-VL-72B [52] and Llama 3.2-VL-11B [9]."
- RePOPE 两句，见 1.1(B)。
- HOPE 引言："our study reveals that as LVLMs continue to evolve through successive iterations, the hallucination problem has been significantly mitigated. As a result, the POPE benchmark is becoming increasingly outdated and fails to precisely reflect the hallucination behavior of state-of-the-art LVLMs."
- REVIS App.F.4（InternVL3 上自家方法 POPE 不涨）："We attribute this plateau to the model reaching a capability ceiling on this specific discriminative task, where the room for marginal improvement is minimal."；同段："…even when discriminative signals are saturated."
- SAVAA §5："SAVAA brings modest gains on POPE because it requires predicting a single closed-form answer, leaving limited room for step-wise adaptive VAA."

说**没解决**：
- DASH 结论："Contrary to the belief that object hallucinations are no longer an issue, we find that they persist extensively when using VLMs in an open world scenario."
- HOPE 引言："In practice, models may appear robust not because they have overcome the hallucination problem, but because the evaluation benchmark fails to challenge them effectively."
- HOPE §实验："Notably, InternVL3, despite being the most recently released model, achieves only 77.31% and 83.24% in precision on the VG and OpenImages datasets, respectively."
- Qwen3-VL 报告："HallusionBench aims at diagnosing image-context reasoning and poses great challenges for current VLMs."
- InternVL3 §3.7："Despite these advancements, minor declines on certain benchmarks, such as MMHal, indicate that although the InternVL3 series has made overall progress, optimizing data and training strategies to achieve more consistent improvements remains an important direction for future work."

没找到：明文写 "object hallucination is largely solved / no longer the bottleneck" 的论文（1 条专门查询，结论层）。DASH 那句 "the belief that object hallucinations are no longer an issue" 说明作者认为社区里有这种看法，但没给出处。

---

## 问题 2：指出"修法收益是评测产物"的工作（Mirage 2504.10020 与 2609.01888 之外）

### 2.1 逐条证据表

| # | 工作 | 模型 | 基准 | 测到什么 | 逐字原话 | 层级 |
|---|---|---|---|---|---|---|
| 1 | **Token-Set Choice Confounds POPE** 2610.25964（NeurIPS 2026 workshop，检索片段称；v3 2026-10-23） | LLaVA-1.5-7B（4-bit NF4）主实验 9000 题；另 4 个 VLM、3 个分词器族 | POPE 三 split | 读出方式本身移动 F1：两 token logit 读出（ID 3582/1217）对 adversarial 给 F1 0.761，八 token（含带空格前缀的 ‘ Yes’/‘ No’）给 0.8221，差 **6.13 点**；模型实际生成的是 3869/1939，那两个 ID 一次都没生成。把 LLaVA 的 ID 原样搬到词表不相交的模型上 F1 = 0.00 | "That 6.13-point adversarial shift exceeds the adversarial gain reported by five of the six papers we surveyed. None of them states its readout, and our reference ran under 4-bit NF4 quantization, so we cannot say how much of any reported gain a matched evaluation would keep."；自认局限："We do not claim the official POPE code mandates this readout, and we could not verify the readout of any published baseline we survey" | F（摘要、§4、局限） |
| 2 | **Measuring the Measurers / HQH** 2406.17115 | MiniGPT4、Otter、Qwen-VL-7B、InstructBLIP、XComposer 等（旧模型） | POPE、AMBER-d、AMBER-g、OpenCHAIR、MMHal、GAVIE | 平行形式信度：POPE **0.3563**、AMBER-d 0.3636、AMBER-g(CHAIR) 0.5333、OpenCHAIR 0.5510（重测信度都 >0.93）。Qwen-VL-7B 的 POPE Acc 0.791（Yes% 0.325）在平行测试下变 0.500（Yes% 0.021）。把提示从 "Describe the image." 换成 "Provide a description of the image."，InstructBLIP-Flan-T5-XXL 的平均长度 104.66 → 10.37 词，AMBER CHAIR 0.151 → 0.037 | "Such inherent bias causes great performance gap in parallel tests, making it unclear whether the evaluation result truly reflects models’ hallucination level or is simply an artifact of their own response bias." | F（Tab.I–III 与相邻段） |
| 3 | **LeHaCE**（Toward a Stable, Fair, and Comprehensive Evaluation of Object Hallucination in LVLMs，NeurIPS 2024，无 arXiv 号） | 十余个 LVLM（旧模型；具体清单未核） | CHAIR | 指令只通过描述长度间接影响幻觉；长度与 CHAIR 近似线性 | "the degree of object hallucination is primarily influenced by the length of image descriptions, with instructions only indirectly affecting hallucinations through their effect on description lengths. The longer the image description, the higher the object hallucination degree, and there is a clear linear relation between them." | F（摘要、引言） |
| 4 | **REVIS** 2602.11824（方法论文里的基线表） | Qwen2.5-VL | CHAIR @64/128/512 | 512 token 下 VCD 34.0、VTI 35.0、ONLY 33.0、AGLA 32.0、M3ID 31.0，**全部不优于 Regular 31.0**；而 64 token 下它们都优于 Regular（14.0）→ 短输出上的收益在长输出上消失 | "While baselines like VCD and VTI suffer from severe degradation, rising to 34.00% and 35.00% respectively (worse than the Regular decoding at 31.00%)" | F（Tab.16）。注意：作者有动机；数值全为整数，样本量未核 |
| 5 | **GIFT** 2510.22067 | LLaVA-1.5 7B/13B | CHAIR、POPE、MMHal | 以 greedy 为基线时，VCD 的 CHAIR_S 52.2（基线 50.2）、POPE F1 80.9（基线 82.4），**都更差**；VAF、VAR 的 CHAIR_S 也不优于 greedy（49.6 / 54.0）；13B 上同样 | 表内数字；无对应原话 | F（Tab.2）。与 Mirage "基线换成 greedy 收益消失"同向，独立来源 |
| 6 | **SAVAA** 2602.13600 | Qwen3-VL-8B、InternVL3.5-8B、LLaVA-NeXT-7B | CHAIR、AMBER | 旧一代注意力放大类基线换到新模型上常变差：InternVL3.5-8B 上 PAI 45.60、VGA 44.20、VAF 42.20 都高于 vanilla 41.40；LLaVA-NeXT 上 PAI 39.60、VAF 36.40 高于 vanilla 33.80；AMBER Hal 率 PAI 在三个模型上都高于 vanilla | 表内数字 | F（Tab.1、Tab.3）。作者有动机 |
| 7 | **MM-Snowball** 2606.00622（ICML 2026） | LLaVA-1.5、Qwen2.5-VL(-7B) | MM-Snowball 6 轮 | 单轮修法在多轮上基本无效：Qwen2.5-VL Turn-5 基线 3.15，+VCD 2.75、+OPERA 2.90、+DoLA 2.85、+DeCo 3.10、+MemVR 3.20、+RVD 3.30；LLaVA-1.5 全部在 0.40–0.60 | "Despite their success in single-turn tasks, the efficacy of these methods diminishes in multi-turn dialogues."；摘要："…reveals the inefficacy of existing mitigation methods designed for single-turn VQA" | F（Tab.2–3）。须知：作者自己的 CAVR 在 Turn-5 也只到 3.50 / 0.65，表里所有方法（含自家）都在噪声量级——这张表支持"都没用"，不支持"CAVR 有用" |
| 8 | **THRONE** 2405.05256（CVPR 2024） | 11 个 LVLM（2023 年代） | THRONE（自由生成）vs POPE | POPE（Type II）进步不传导到自由生成（Type I）：两者 Spearman 仅 0.2；POPE 只抽 ≤9 个负类，严重低估 | "we observe that a reduction in Type II hallucinations does not lead to a reduction in Type I hallucinations but rather that the two forms of hallucinations are often anti-correlated."；"THRONE and POPE, which measure Type I and Type II hallucinations, respectively, have a Spearman’s rank correlation coefficient of just 0.2" | F（摘要、§5.4） |
| 9 | **RePOPE** 2504.15707 | 17 个开源模型 | POPE → RePOPE | 标注噪声改变排名（见 1.1(B)）。没有测任何修法 | 见上 | F（全文短，表全读） |
| 10 | **DASH** 2503.23573（ICCV 2025，检索片段称） | PaliGemma、LLaVA-NeXT、Qwen2-VL-72B、Llama-3.2-11B 等 | DASH-B | COCO 之外失效（见 1.1(C)）。唯一涉及修法的是自家微调 PaliGemma（DASH-B +11.6%，AMBER existence +2.2%）；相关工作里只写了一句 "The literature on mitigation of hallucinations is limited."（未测 VCD 等） | 见上 | F（HTML；§4.3、App.H、App.J） |
| 11 | **HOPE** 2508.06530 | 6 个 2024–2025 模型 | HOPE vs POPE | POPE 的干扰项太弱；没有测任何修法 | 见 1.3 | F（引言、Tab.1–3） |
| 12 | **Delve into VCD** 2412.06775 | InstructBLIP、LLaVA-1.5、Qwen-VL（旧模型） | POPE、MME | 对比样本的效果随模型与基准变；**不是**"收益是产物"的批评，结论是提出融合方法 | "We find that the efficacy of different CDs varies across LVLMs and tasks. For example, contrastive decoding with image editing improves the InstructBLIP [5] on the POPE [15] and MME [8] benchmarks the most but has a minor improvement for LLaVA-1.5 [18] on the POPE benchmark." | F（摘要、引言；表未细读） |
| 13 | **HALLUCINOGEN** 2412.20622 | 11 个 LVLM + LLaVA-RLHF、LURE | 自建攻击提示（identification → counterfactual） | 两种修法在更难任务上错误率升 21.09% / 23.12% | "This highlights the ineffectiveness of these mitigation techniques when evaluated against HALLUCINOGEN." | F（定点）。弱：比较的是任务难度升高后的错误增量，不是"有修法 vs 无修法" |
| 14 | **Do More Details Always Introduce More Hallucinations?** 2406.12663 | LLaVA-1.5 等（旧） | CHAIR | 认为 CHAIR 在详细描述上高估幻觉（人工参考描述不详 + 规则匹配） | "our study finds technical flaws in existing metrics, leading to unreliable evaluations of models and conclusions about OH." | F（摘要、引言） |
| 15 | **HalTrapper / Why LVLMs Are More Prone to Hallucinations in Longer Responses** 2510.20229（ICCV 2025，检索片段称） | LLaVA 系、Qwen-VL | CHAIR、AMBER | 幻觉物体更常出现在输出后段；归因于对上文的依赖而非长度本身 | "we suggest that the risk of hallucinations is not caused by length itself but by the increased reliance on context for coherence and completeness in longer responses."；局限："This work primarily addresses object-level hallucinations in long-form responses generated by large LVLMs." | F（摘要、局限） |
| 16 | 多篇方法论文的实验设置 | — | CHAIR、POPE | 基线解码不统一：vanilla 与 VCD 用采样、OPERA 用 beam search（MVP 2408.17150、SHIELD 2510.16596 的设置描述）；"Following the original papers, we pair VCD with nucleus sampling, apply OPERA and DeCo on top of beam search"（某 2026 论文） | 未核 | **S** |
| 17 | 2511.05017（Refining Textual Embeddings / VisAlign） | Video-LLaVA | MME 分项 | VCD 在 MME 各子类上普遍下降或无提升（一般能力代价） | "hallucination mitigation methods like VCD cause a universal performance drop or yield no improvements across all MME subcategories" | F（定点：仅该段；Tab.7 数字未读）。作者有动机 |
| 18 | **SPARC** 2502.01419（Jung et al. 2025；缓存在 /tmp/vl03） | LLaVA-1.5、LLaVA-NeXT、Qwen2-VL；对 OPERA、VCD、PAI 等 | CHAIR（precision/recall）、CLAIR、DOCCI、IIW-400 + 人评 | 已有修法提高 precision 的代价是 recall | "Our experiments, incorporating both automated and human evaluations, demonstrate that existing methods improve the precision of MLLMs at the cost of recall." | A+（摘要与引言；结果表未读）。与 2609.01888 同向且更早 |
| 19 | **Rethinking the Effectiveness of Contrastive Decoding** 2607.25196（Mirage 的被引） | LLaVA-v1.5-7B、**Qwen2.5-VL-7B-Instruct、InternVL3-8B**；VCD、SID、ICD | CHAIR（COCO 500 图）、LLaVA-Bench、POPE（机制分析） | (i) 去掉对比项只留 adaptive plausibility constraint（APC-S）即得到大部分 CHAIR 收益；(ii) **greedy 在三个模型上 CHAIR 全面最好**（Qwen2.5-VL-7B：采样 31.2 / VCD 25.1–28.8 / SID 27.8–29.6 / APC-S 23.5 / greedy 22.8；InternVL3-8B：33.5 / 33.1–33.5 / 33.0–33.2 / 29.7 / 29.4）；(iii) 对比项放大幻觉物体 token 的次数不少于抑制；换成同幅度高斯噪声分数不降 | "Experiments across three models and standard hallucination benchmarks show that these improvements reflect a change in decoding behaviour rather than genuine hallucination mitigation."；"greedy decoding accounts for most of the improvement reported by VCD [9], SID [11] and ICD [10]."；局限："Our mechanistic analysis covers a single model on a single discriminative benchmark … so whether the same absence of a hallucination-specific signal holds in larger models or in free-form generation remains open."；"Applying the same treatment to newer methods and larger models would establish how far these conclusions generalise." | F（摘要、贡献、Tab.3、局限；机制节未细读） |
| 20 | **When Visual Signals Mislead** 2608.11024（预印本） | Qwen2.5-VL-3B、InternVL3.5-4B、LLaVA-1.5-7B | VAW 属性 yes/no 探针（颜色/材质/状态） | VCD、ICD 对颜色 FPR 的改变为 0.0 pp（三个模型皆然）；F1/Acc 不变而 yes 比例上升 | "VCD/ICD achieve 0.0 pp improvement on color."；表注："VCD/ICD Yes-Ratio increases reveal worsening yes-bias masked by stable F1/Accuracy." | F（定点）。三个模型都恰为 0.0 pp，原因我没读到；作者自家方法是对照 |
| 21 | **DASH** App.M Tab.9（提示措辞） | PaliGemma-3B、LLaVA-NeXT Vicuna/Mistral | DASH 自采图，11 种问法 | PaliGemma 的幻觉迁移率随问法从 0.861（"Can a OBJ be seen in the image?"）到 0.348（"Is OBJ in the image?"，即它预训练用的问法）；LLaVA-NeXT 两个模型标准差 0.06–0.07 | "PaliGemma was pretrained on this task using the prompt ”Is OBJ in the image?” and shows lower transfer rates on similar prompts. However, this improved robustness against systematic hallucinations does not generalize to less similar prompts." | F（HTML Tab.9） |
| 22 | **Lost in Contrast** 2610.16722（Mirage 的被引） | 9 个模型（未核清单） | VizWiz、Food-101（带"可弃答"指令的 VQA） | VCD 类对比解码把有依据的弃答变成错误回答（候选过滤先把弃答 token 排除、参考分支减掉了弃答指令的效应）；不是物体幻觉基准 | 摘要："the same contrast also turns supported abstentions into incorrect answers" | A（仅摘要） |

### 2.2 按你列的子项对账

| 子项 | 找到什么 | 没找到什么 |
|---|---|---|
| POPE yes/no 偏置 | HQH（#2）：平行形式信度 0.36，偏置使结果不可解释 | 在**新模型**上重做的 yes 率 × 修法分析（Mirage 之外） |
| 读出 token 选择 | #1（6.13 点） | 任何已发表修法的收益被证实来自读出差异——#1 自己说核不了 |
| 提示后缀 / 问法 | #21（DASH Tab.9：同一模型的存在性幻觉率随问法从 0.86 到 0.35）；HQH（#2）换一句等价描述指令，输出长度变 10 倍。DASH 全程加后缀 "Please answer only with yes or no." | 专门研究"Please answer with one word"这类**后缀**对修法结论影响的工作（2 条查询，对象层） |
| CHAIR 长度混淆 / max_new_tokens | #2、#3、#4 + 1.1(D) 的 token 上限表 | 在等长条件下重评多种修法的独立研究（2609.01888 用 recall/Cover 配对，不是等长截断） |
| recall 下降 | 2609.01888（你已读）；#18 SPARC（更早，2025-02） | — |
| 同义词表与 COCO 80 类覆盖 | GIFT 作者把 Qwen3-VL 的高 CHAIR 归给字符串匹配（"we attribute"，无实验）；THRONE 图注："CHAIR relies on exact text matching to a fixed set of objects and synonyms"；OpenCHAIR、ALOHa、VALOR-Eval 只有 S | 量化"新模型的 CHAIR 幻觉里有多少是匹配误判"的工作 |
| 单轮 → 多轮 | #7；先例 MMHalSnowball 2407.00569（S） | 自然（无诱导）多轮下修法是否失效 |
| 长描述后段 | #4（512 token 下收益消失）、#15 | — |
| 标注噪声 | #9、DASH App.H | 用 RePOPE 重评修法收益的工作（未检到） |
| 自然图之外 | #10、#11、#13 | 在 DASH-B / HOPE 上评 VCD/OPERA/转向类修法（未检到） |
| 换解码后收益消失 | **#19（三模型含两个新模型，greedy 全面最好，独立重评）**；#5（greedy 基线下 VCD 变差）；#16（S） | 对比解码之外的修法（注意力放大、转向向量、权重编辑）在 greedy 基线下的独立重评 |
| 换模型后收益消失 | #19（Qwen2.5-VL-7B、InternVL3-8B，仅对比解码类）；#20（属性探针，VCD/ICD 0 pp）；#4、#6（方法论文里的基线表）；#12 | 独立第三方在 Qwen3-VL / InternVL3.5 上、或对**非对比解码类**修法做的专门重评（3 条查询未命中，对象层） |
| 幻觉基准与一般能力背离 | 2609.01888（你已读）；InternVL3 Tab.5：POPE 在 1B–78B 持平而 MMBench、MMVet 等随规模上升（推导：读表）；#17（S） | 排行榜层面的秩相关分析（1 条查询未命中） |

### 2.4 中间稿之后新增的关键证据（单列，方便你对照）

1. **2607.25196**：对比解码在 Qwen2.5-VL-7B、InternVL3-8B 上的 CHAIR 收益被 greedy 与"只留约束、去掉对比项"的对照完全解释。这是目前找到的**唯一一篇在新一代模型上做的独立重评**，且把 Mirage 的 POPE 结论推到了生成任务。它自己留的开口：机制分析只做了一个模型一个判别式基准；"newer methods and larger models"没做。**结论层占位情况**：若我们要写的那句话是"对比解码的收益来自解码行为而非幻觉抑制"，这句已被 Mirage + 2607.25196 写出（原话见 #19）；对比解码以外的修法家族未见同类重评（3 条查询，对象层）。
2. **SPARC 2502.01419**：precision 换 recall 的结论比 2609.01888 早一年半，且有人评。
3. **2608.11024**：属性（颜色）探针上 VCD/ICD 0 pp，且 yes 比例上升被稳定的 F1/Acc 掩盖——与 Mirage 的 yes 偏置机制同向，换到了属性与新模型上。
4. **DASH Tab.9**：存在性幻觉率对问法高度敏感（PaliGemma 0.86 ↔ 0.35），"鲁棒性"只在训练见过的问法附近成立。
5. **DOCCI-Critique**：长描述逐句事实性，GPT-4o 97.1%、Qwen2-VL-7B 87.6%——是"长描述剩余空间"唯一的人工标注口径数字，但没有 2025 年以后的模型。

### 2.3 公开审稿意见

- **Mirage（NeurIPS 2025）**：论坛 ID wGeQr5cARm 已定位（OpenReview 搜索接口返回，venue "NeurIPS 2025 poster"）。取论坛内容时接口返回 403 ChallengeRequiredError，网页版只显示人机验证。**没取到任何审稿文字**，没有绕验证。
- **DASH**：未检到 OpenReview 页面（未专门发查询；ICCV 通常不公开审稿——这句是常识性判断，未核）。
- **VCD（CVPR 2024）**：按指示跳过。

---

## 检索日志

### 查询清单（WebSearch 23 条 + 接口查询 4 条）

1. POPE benchmark saturated newer VLMs Qwen2.5-VL InternVL3 object hallucination "saturated" 2025 2026 arXiv
2. Qwen3-VL-8B CHAIR_S 51.6 hallucination mitigation CHAIR Qwen3-VL InternVL3.5 arXiv 2026
3. hallucination mitigation LVLM evaluation flawed CHAIR caption length confound shorter captions recall "max_new_tokens" re-evaluation decoding methods
4. POPE prompt sensitivity "Please answer" yes/no bias hallucination mitigation methods gains disappear prompt format evaluation artifact LVLM
5. hallucination mitigation methods LVLM re-evaluation "fail to generalize" OR "do not transfer" newer models Qwen2.5-VL InternVL3 training-free decoding benchmark study 2025 2026
6. AMBER attribute relation hallucination Qwen2.5-VL InternVL3 GPT-4o results "relation" hallucination remains challenging benchmark 2025
7. MM-Snowball multimodal hallucination snowballing multi-turn mitigation methods fail arXiv 2606.00622
8. detailed image caption hallucination benchmark modern VLMs GPT-4o Qwen2.5-VL long caption hallucination rate DOCCI CAPTURE DeCapBench 2025
9. "hallucination" mitigation LVLM "fair comparison" OR "standardized evaluation" OR "unified benchmark" decoding methods VCD OPERA re-implementation gains inconsistent across models benchmarks 2025 2026 arXiv
10. VCD baseline nucleus sampling vs greedy decoding hallucination gains vanish "greedy" baseline stronger contrastive decoding LVLM POPE CHAIR critique sampling baseline weak
11. video hallucination benchmark results Qwen2.5-VL Gemini 2.5 GPT-4o accuracy human gap VideoHallucer EventHallusion 2025 2026 new benchmark
12. multi-image hallucination benchmark MLLM Qwen2.5-VL InternVL3 GPT-4o existence count attribute hallucination multiple images 2025
13. openreview "The Mirage of Performance Gains" contrastive decoding NeurIPS 2025 reviews
14. "object hallucination" "largely solved" OR "no longer the bottleneck" OR "nearly solved" OR "has been largely addressed" modern vision-language models 2025 2026
15. CHAIR metric limitation COCO 80 categories synonym list open-vocabulary hallucination evaluation ALOHa OpenCHAIR recall trade-off "CHAIR" unreliable modern captions
16. "hallucination" LVLM mitigation "caption length" controlled CHAIR "same length" OR "length-controlled" OR "truncate" shorter outputs explain CHAIR reduction recall drop pitfalls evaluation 2025
17. "Toward a Stable, Fair, and Comprehensive Evaluation of Object Hallucination in Large Vision-Language Models" arXiv instruction length LeHaCE
18. hallucination mitigation methods "stronger models" OR "advanced LVLMs" VCD OPERA "limited improvement" OR "diminish" OR "no improvement" Qwen2.5-VL InternVL3 LLaVA-OneVision "even degrade" POPE CHAIR
19. POPE evaluation "first token" OR "logit" yes no probability readout vs generated text answer parsing sensitivity prompt template "answer the question using a single word" hallucination benchmark VLM bias study
20. Jung 2025 hallucination mitigation methods trade precision for recall CHAIR "recall" caption object coverage LVLM mitigation methods reduce recall evaluation
21. AMBER discriminative existence attribute relation F1 table Qwen2.5-VL-7B InternVL3-8B Qwen3-VL "Relation" "Attribute" "Existence" hallucination 2026 arXiv
22. hallucination benchmark performance does not correlate with general VLM capability MMBench "hallucination" leaderboard trade-off mitigation degrades general performance MME MMMU study 2025 2026
23. counting hallucination OR "number hallucination" VLM benchmark 2025 2026 Qwen2.5-VL GPT-4o Gemini accuracy object counting hallucination remains

24. "Mirage of Performance Gains" OR "RePOPE" cited hallucination mitigation evaluation 2026 "re-evaluate" existing methods RePOPE DASH-B results VCD OPERA steering "DASH-B" mitigation
25. attribute hallucination benchmark 2025 2026 state-of-the-art VLMs GPT-4o Qwen2.5-VL InternVL3 "attribute" hallucination accuracy fine-grained still struggle color count state benchmark results
26. POPE GPT-4o Gemini Claude accuracy F1 closed-source "POPE" results table 2025 Gemini 2.0 Claude 3.5 Sonnet object hallucination yes/no
27. hallucination mitigation "no method" consistently improves benchmark of mitigation methods LVLM 2026 "HalluBench" OR "reproducibility" OR "sanity check" OR "pitfalls" OR "rethinking" training-free hallucination mitigation evaluation protocol
28. VideoHallucer EventHallusion results table Qwen2.5-VL-7B InternVL3 LLaVA-Video Gemini 2.5 video hallucination mitigation 2026 "EventHallusion" "VideoHallucer" accuracy
29. long detailed caption hallucination rate modern VLMs "DOCCI" OR "IIW" OR "CAPTURE" Qwen2.5-VL InternVL3 GPT-4o hallucination increases with caption length benchmark 2025 2026 "CapMAS" OR "DetailCaps" OR "CompreCap"

合计 WebSearch 29 条（上限 35）。

接口：arXiv API 按标题查 LeHaCE（0 命中）；NeurIPS 2024 论文集索引按标题查 LeHaCE（命中）；OpenReview 搜索接口查 Mirage（命中论坛号）；OpenReview 论坛接口 + 网页取审稿（被人机验证挡住）；Semantic Scholar 被引接口查 Mirage / RePOPE / DASH（只有 Mirage 成功，返回 7 条；另两篇两次都被限流）。

未命中的查询：14（"已解决"原话）、20（Jung 2025——后来从 2606.25432 的参考文献里定位到是 SPARC 2502.01419）、21（AMBER 逐类）、22（秩相关）、18 与 27（独立第三方新模型重评——后来从 Mirage 被引里找到 2607.25196）、24（在 RePOPE / DASH-B 上重评修法）、26（闭源模型 POPE 表）、28（VideoHallucer / EventHallusion 新模型数字）。

教训一条：18、27 两条关键词查询都没搜出 2607.25196，是被引扫描搜出来的。RePOPE 与 DASH 的被引没扫成，那里可能还有同类漏网。

### 篇数

**F（取到正文并核对了对应表/段，多为定点阅读）——22 篇：**
2504.15707（RePOPE，表全读）、2503.23573（DASH，HTML）、2412.06775、2508.06530（HOPE）、2510.22067（GIFT）、2602.13600（SAVAA）、2602.11824（REVIS，仅 App.F）、2602.18711（HIME，仅 Tab.2 与设置）、2602.21704（仅新模型表与设置）、2510.16596（SHIELD，仅 Tab.15）、2504.10479（InternVL3，Tab.5 与 §3.7）、2511.21631（Qwen3-VL 报告，Tab.2–4 的 HallusionBench 行）、2606.00622（MM-Snowball）、2405.05256（THRONE）、2406.17115（HQH）、NeurIPS 2024 LeHaCE（无 arXiv 号）、2610.25964（POPE token 审计）、2412.20622（HALLUCINOGEN）、2510.20229（HalTrapper）、2406.12663、2508.00726（MIHBench，Tab.2）、2503.19622（HAVEN，仅结果表行）。
另：2609.01888 只顺带看了附录 Tab.6，不计入。

中间稿之后新增 **F（定点）5 篇**：2607.25196（摘要、贡献、Tab.3、局限）、2608.11024（方法对比表与 §V）、2506.07631（DOCCI-Critique，Tab.2）、2503.07906（DeCapBench，Tab.7 若干行，列头未逐一核）、2511.05017（仅一段）。F 合计 **27 篇**。

**A / 只读摘要或单段——4 篇：** 2505.23941（VLMs are Biased，摘要与模型清单）、2502.01419（SPARC，摘要与引言；缓存在 /tmp/vl03）、2610.16722（Lost in Contrast，摘要）、2606.25432（只读 §2.4 一段，用来定位 Jung et al.）。

**已下载、没读出可用内容——1 篇：** 2608.19075（ReWEIGH；关键词没定位到 AMBER 逐类表）。

**S（只见检索片段）：** 2505.01481（VideoHallu）、ELV-Halluc、2606.31933、2411.16771（VidHal）、MIOH（CVPR 2026）、Common-O、2408.17150（MVP）、2409.16494（Dentist）、2404.13874（VALOR-Eval）、2312.03631（OpenCHAIR）、ALOHa、2407.00569（MMHalSnowball）、2510.04401（VLMCountBench）、2603.10978（GroundCount）、2603.15253（HalDec-Bench）、CapArena、2405.15683（VDGD）、2512.18813、2510.18321、2609.01318。

### 过程备注

- 16:33 前后 /tmp（tmpfs）一度报配额用尽，两次写文件得到空文件，稍后恢复；没有删除任何别人的文件。
- 逐字引文二次核对：37 条用脚本（/tmp/a4_audit/sub_b_scripts/qcheck.py，忽略空白与断行连字符）在源文本里全部命中；另有 4 条跨栏或含省略号的（HQH 整句、THRONE 图注、2607.25196 局限句、DASH 带 ± 的那句）是肉眼对过的，其中 DASH 那句的数字取自 HTML 公式的 alttext。
- 我往 /tmp/a4_audit/papers/ 里新下了 25 篇（pdf+txt）：2508.06530、2510.22067、2602.13600、2510.20229、2606.00622、2412.20622、2406.12663、2508.00726、2405.05256、2406.17115、2504.10479、2511.21631、2503.19622、2610.25964、2510.16596、2505.23941、2608.19075、2511.05017、2606.25432、2503.07906、2608.11024、2506.07631、2607.25196、2610.16722，另加 lehace_neurips24.pdf/.txt。一次失败下载（403 的 HTML）已删。/tmp 当前约 60% 占用。
- 自写脚本在 /tmp/a4_audit/sub_b_scripts/（g.sh、h2t_math.py、or_list.py、or_forum.py、cit.py）；非版式文本副本在 /tmp/a4_audit/sub_b_txt/（含 DASH 带公式数字的 2503.23573.m.txt——papers 目录里那份 HTML 转文本把百分数都丢了，读 DASH 数字请用这份）。
- papers 目录里 2503.23573.pdf 是截断的坏文件（pdftotext 报 xref 错），不是我下的，没动。

---

## 没覆盖到的范围

- **闭源模型**：GPT-4o/Gemini/Claude 在 POPE、CHAIR、AMBER 上的 F 级数字只有 InternVL3 表里转引的 GPT-4o POPE 86.9 与 DASH 的 GPT-4o-mini；Claude 只有 HallusionBench。
- **指定但没查到数字的模型**：Gemma3、Llama-3.2-Vision（除 DASH-B 的构造用途）、Pixtral；Ovis2 只有 RePOPE/DASH。
- **指定但没查到新模型数字的基准**：THRONE、HaloQuest、DOCCI、IIW、DetailCaps/CAPTURE、MIRAGE/MMIU/Mantis-Eval、VideoHallucer、EventHallusion；AMBER 判别式逐类。
- **审稿意见**：见 2.3，全部未取到。
- 在审稿件、非 arXiv（除 LeHaCE）、非英文、并行未公开工作未覆盖；我的知识截止在 2026-06，之后的论文（26xx 的后半）完全依赖本次检索，漏检风险高于之前的年份。
- 引用链挖掘（第 5 步）只做成 Mirage 一篇（7 条被引，接口收录不全）；RePOPE、DASH、2609.01888 的被引与各篇参考文献没有系统扫。
- 本稿只接受了 **1 轮、29 条查询 + 1 次被引扫描**的检验；"未找到"都只是这个量级下的未找到。
- F 级多为定点阅读（表 + 相邻段），没有通读方法与对照设置；尤其 #4、#6、#17、#20 这几条来自"自家方法论文里的基线表"，基线的超参是否按原论文调过我没核。
- 2607.25196 的机制分析节、Tab.4–5 没细读；它与 Mirage 的重合程度、对 ICD 的具体数字需要你们通读后再定。
