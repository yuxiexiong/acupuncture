# sub_a：VLM 物体幻觉已有修法六组整理（草稿，供主查重者当输入）

日期 2026-11-06。检索截至 2026-11。阅读层级：F = 取到正文并核对了对应表或段；A = 只读摘要；S = 只在别人表里或检索片段里见到。
关键数字与逐字引文只来自 F。逐字引文都在 pdftotext/HTML 文本里核对过（文本来自 /tmp/a4_audit/papers 与 /tmp/vl03/papers）。
不给等级、分数、"值得做/不值得做"。跨论文不直接比涨幅：同一基线（LLaVA-1.5 CHAIR_S）在不同论文里从约 20 到约 55，各自口径逐条写明。

"组内最强"只按四条轴之一陈述（模型族最多 / 同表涨幅最大 / 对照最严 / 开销最低），每条都写明是哪条轴，不是总评。

本文件不覆盖（主查重者已读）：Dual-Pathway 2605.13156、SSL 2505.16146、Mirage 2504.10020、"Does Playing it Safe" 2609.01888、Role-Break 2607.29412。下文引用这几篇时只引我在正文里核对过的句子，并标"主查已读"。

---

## 第 1 组 解码类

组内按轴最强者：
- 模型族最多：VCD（LLaVA-1.5 / InstructBLIP / Qwen-VL，三个语言骨干里两种：Vicuna-7B、Qwen-7B）与 DeCo（InstructBLIP / MiniGPT-4 / LLaVA-1.5 / Qwen-VL）。新一代模型上有数字的只有 NoLan（Qwen2-VL、Qwen2.5-VL，仅 POPE-random）。
- 对照最严（统计）：VCD 报 5 次运行的均值与标准差；SID 报 3 次。组内没有任何一篇做"随机对比分支"式的对照，DeCo 有"随机扰动所选层"对照（Table 5）。
- 开销最低：DeCo 自报约 1.2×；SID 在 V100 上 POPE 全集 494 s → 668–704 s（约 1.35–1.43×）。
- 同表涨幅最大：不同论文口径不一，不排序；逐条见下。

### 1.1 VCD（Visual Contrastive Decoding）— F
- arXiv 2311.16922 / 2023 / CVPR 2024。推理时；对比原图与加高斯噪声图的 logits，加 adaptive plausibility constraint（APC）。
- 模型族：LLaVA-1.5（Vicuna-7B）、InstructBLIP（Vicuna-7B）、Qwen-VL（Qwen-7B）；附录 Table 8 有 13B 版。
- 口径：POPE 三数据源（MSCOCO / A-OKVQA / GQA）× random / popular / adversarial，各 500 图 × 6 问，共 27,000 条；报 Acc / Prec / Rec / F1；**基线是 direct sampling（"Regular decoding denotes direct sampling"）**；5 次运行均值±标准差。MME 幻觉子集。CHAIR：正文没有 CHAIR 主表（未找到 max new tokens）。LLaVA-Bench 用 GPT-4V 打分。
- 效果（Table 1，GQA 段我核对的行）：LLaVA-1.5 GQA-random Acc 83.73→86.65、F1 82.95→86.99；Qwen-VL GQA-random Acc 80.97→85.59。MME 幻觉子集总分（Table 2）：LLaVA-1.5 565.33→604.66、Qwen-VL 587.33→596.67、InstructBLIP 380.33→447.67。
- 换解码（Table 7，LLaVA-1.5，POPE-random）：Top-P 无 VCD 84.91 → 有 87.82；**Greedy 无 VCD 87.10 → 有 88.49**；Top-K+temp1.5 79.28→86.97。即涨幅随基线解码的随机性变大，greedy 下只剩 +1.39 Acc。
- 开销：作者未给数字（只说 "minimal computational overhead"）；别人实测：DeCo 报 1.8×（Fig. 6 文字）；SID Table 6 报 494 s→904 s；NoLan Table 22 报 0.4579→0.7537 s/token。
- 一般能力：作者 MME 全表（Table 9/10）称有益；别人实测：SID Table 5（LLaVA-1.5 7B，greedy）MME 1510.8 → VCD 1488.5，MMBench 64.4→63.8。
- 对照：无随机对照分支；无换问法；5 次种子。
- 失败条件（别人实测）：
  - DeCo Table 2（max tokens 未在该表注明，500 图）：nucleus 下 VCD 的 CHAIR_S 反而升高——InstructBLIP 54.6→58.0、MiniGPT-4 32.6→33.8、LLaVA-1.5 48.8→54.0；只有 Qwen-VL 49.2→46.4 下降。
  - SID Table 1（LLaVA-1.5 7B，POPE MSCOCO）：greedy 下 random Acc Normal 88.8 → VCD 87.8（下降），adversarial 79.3→80.9；去掉 APC（Eq. 3）后 sampling 下 VCD 83.3 < Normal 84.9。SID Table 11：去掉 APC 后 VCD 的 CHAIR_S 51.9（Sampling 基线 51.3）、MME 1457.1（基线 1471.5）。
  - Mirage 2504.10020（主查已读；摘要逐字）："The performance improvements observed on POPE Benchmark are largely driven by two misleading factors: (1) crude, unidirectional adjustments to the model's output distribution and (2) the adaptive plausibility constraint, which reduces the sampling strategy to greedy search."
- 作者自认局限（逐字）："While this study employs a basic Gaussian noise approach to introduce visual uncertainty, more fine-grained techniques, like object-level blurring, hold the potential for improved outcomes."
- 代码：https://github.com/DAMO-NLP-SG/VCD

### 1.2 OPERA — F
- arXiv 2311.17911 / 2023 / CVPR 2024。推理时；beam search 里加 over-trust penalty（对"汇总 token"的列式注意力聚集加罚）+ retrospection-allocation 回滚。
- 模型族：InstructBLIP、MiniGPT-4、LLaVA-1.5、Shikra（全是 Vicuna 一代）。
- 口径：CHAIR：COCO val2014 随机 500 图，提示 "Please describe this image in detail."，**max new tokens 512（Table 1）与 64（Table 2）两档**；未报种子数、未报 recall；另有 GPT-4V 打分（correctness / detailedness）、PPL 与流畅度（Table 5）。POPE：三 split 的平均 F1（Table 4）。MME / MMBench（Table 6，LLaVA-1.5）。
- 效果（Table 1，512 tokens，CS/CI）：InstructBLIP Greedy 58.8/23.7、Beam 55.6/15.8 → OPERA 46.4/14.2；MiniGPT-4 Greedy 31.8/9.9、Beam 30.6/9.5 → 26.2/9.5；LLaVA-1.5 Greedy 45.0/14.7、Beam 48.8/13.9 → 44.6/12.8；Shikra Greedy 55.8/15.4、Beam 50.4/13.3 → 36.2/12.1。POPE 平均 F1（Table 4）：LLaVA-1.5 Greedy 82.2、Beam 84.9 → 85.4；InstructBLIP 80.0 / 84.4 → 84.8（相对 beam 只 +0.4 到 +0.5）。
- 开销：作者正文未给倍数（未找到）；别人实测：DeCo 报 5.1×；SID Table 6 报 494 s→2643 s、显存 15673→21943 MB。
- 一般能力（Table 6）：MME Greedy 1510.7 / Beam 1504.3 → 1515.4；MMBench 64.3 / 64.4 → 64.4。SID 正文称 "OPERA generates text with fewer words and sentences due to penalization of the over-trust mechanism"（SID §5，F）。
- 对照：无随机对照；无换问法。
- 失败条件：作者自认短回答上增益很小；LLaVA-1.5 上相对 greedy 的 CHAIR_S 只有 45.0→44.6。
- 作者自认局限（逐字）："OPERA demonstrates marginal gains when addressing hallucinations in short answers (< 10 tokens), primarily due to the hysteresis of knowledge aggregation patterns." 以及 "The first limitation lies in it can not address all kinds of the hallucinations of MLLMs."
- 代码：正文文本未抓到 URL（公开仓库 shikiw/OPERA 是我的记忆，未在文本核对，标 S）。

### 1.3 DeCo（Dynamic Correction Decoding）— F
- arXiv 2410.11779 / 2024 / ICLR 2025。推理时；把前面某层（动态选）的 logits 加到末层 logits 上（依据：前层对真实物体概率更高，末层被语言先验压低）。
- 模型族：InstructBLIP、MiniGPT-4、LLaVA-1.5（Vicuna-7B）、Qwen-VL（Qwen-7B）。
- 口径：CHAIR 500 张 COCO 图（max new tokens 在正文未检到，标"未找到"）；三种解码（greedy / beam / nucleus）各自配对比较；POPE 只报 F1（500 图 × 6 问）；AMBER 生成（附录 Table 7，仅 LLaVA-1.5）；MM-Vet（Table 9）；GPT-4o 打分。未报种子数。
- 效果（Table 2，CS/CI）：LLaVA-1.5 Greedy 45.0/14.7 → 37.8/11.1；Beam 48.8/13.9 → 33.0/9.7；Nucleus 48.8/14.2 → 42.8/13.2。Qwen-VL Greedy 46.0/12.5 → 42.2/10.7。POPE F1（Table 3）：LLaVA-1.5 Greedy 82.2→86.7；Qwen-VL Greedy 85.2→86.3；Beam 下 InstructBLIP 84.4→84.9。AMBER（Table 7，LLaVA-1.5 greedy）：CHAIR 8.2→6.6，Hal 34.3→28.1，**Cover 48.9→47.5（下降）**。
- 开销：自报 "approximately 1.2 times"（延迟），同段给 VCD 1.8×、OPERA 5.1×。
- 一般能力：MM-Vet（Table 9）LLaVA-1.5 总分 23.6→27.9；Qwen-VL 45.7→46.3，但 Rec 51.8→50.5、Know 41.0→38.8、Gen 35.6→33.8 下降。GPT-4o detailedness：MiniGPT-4 6.20→6.08、LLaVA-1.5 6.31→6.25 下降（Table 4）。
- 对照：有"随机扰动所选前层"对照（Table 5，"perturbed DeCo"），无随机方向类对照；无换问法。
- 失败条件：覆盖率 / 细节度下降（自认）；模型只到 Qwen-VL 一代。
- 作者自认局限（逐字）："Due to the GPU cost consideration, we conduct experiments solely on limited MLLMs, without exploring additional MLLMs or those with larger parameter sizes." 与 "The results shown in Table 4 indicate that our method has a little negative impact on the level of detailedness metric."
- 代码：https://github.com/zjunlp/DeCo

### 1.4 SID（Self-Introspective Decoding）— F
- arXiv 2408.02032 / 2024 / ICLR 2025。推理时；在早层只保留注意力最低的视觉 token 造"放大幻觉"的分支，再做对比解码。
- 模型族：LLaVA-1.5、InstructBLIP、Shikra、LLaVA-NeXT（7B；附录 Table 14 有更大骨干）。
- 口径：POPE（三 split，Acc 与 F1，sampling 与 greedy 两种都报，Table 4）；CHAIR 500 图、max new tokens 512、三次运行平均（Table 3）；GPT-4 SHR（VG 200 图）；MME / MMBench（Table 5）；附录有 MathVista / MM-Vet / LLaVA-Bench / MMMU。
- 效果（Table 3，CS/CI）：LLaVA-1.5 Sampling 51.3/16.8 → 45.0/11.7；Greedy 49.6/14.4 → 44.2/12.2；LLaVA-NeXT Greedy 42.9/13.2 → 38.1/11.3；Shikra Greedy 47.1/13.9 → 44.8/12.8。POPE（Table 1，LLaVA-1.5 MSCOCO，greedy）：random Acc 88.8→89.3、adversarial 79.3→83.3。
- 开销（Table 6，V100，POPE adversarial 全集秒数）：Normal 494；VCD 904；ICD 974；OPERA 2643；SID 668–704。
- 一般能力（Table 5，LLaVA-1.5 7B）：MME Greedy 1510.8 → SID 1520.4；MMBench 64.4→65.0；同表 DoLa 1480.7、ICD 1473.2、VCD 1488.5（低于 greedy）。
- 对照：有 token 选择策略对照（Table 13）；无随机方向类对照。
- 失败条件：greedy 下 POPE-random 只 +0.5 Acc；作者称 1-gram 流畅度与 WPI 略低于 sampling。
- 作者自认局限（逐字，Future Work）："As the pruning ratios and layer are set manually, we consider training the external network to automatically determine optimal hyperparameters"。正文无独立 Limitation 节。
- 代码：https://github.com/huofushuo/SID

### 1.5 其余（定点读，字段不全）
- HALC 2403.00425（ICML 2024）— F（定点）：MiniGPT-4 / LLaVA-1.5 / mPLUG-Owl2；依赖外部检测器取 FOV，再做 focal-contrast + beam；CHAIR 报 BLEU（Table 1），自建 OPOPE；Fig. 4 画了 CHAIR_I 随 max tokens 变化。开销未在正文检到。代码 https://github.com/BillChan226/HALC 。
- M3ID 2403.14003（CVPR 2024）— F（定点）：LLaVA-1.5 7B/13B、InstructBLIP；有/无图两次前向对比。自认局限（逐字）："A limitation of M3ID is that it requires two forward passes at inference time" 与 "sometimes M3ID may prevent the generation of objects that are highly likely under the unprompted language prior (due to context clues)"（附录 Table 7 称 overcompensation）。
- ICD 2403.18715（ACL Findings 2024）— F（定点）：指令扰动对比；SID Table 1 实测 greedy 下 POPE-random Acc 88.8→87.9（下降），SID Table 5 MME 1510.8→1473.2。
- AGLA 2406.12718（CVPR 2025）— F（定点）：LLaVA-1.5、InstructBLIP，另 MiniCPM-V 2.4B（ROPE）；需外部图文匹配模型造局部遮罩图。自认局限（逐字）："we conducted experiments on the most widely used LVLMs due to resource constraints. It will be useful to evaluate our model on larger LVLMs such as LLaVA 34B and Flamingo 70B"。代码 https://github.com/Lackel/AGLA 。
- NoLan 2602.22144（2026）— F（定点）：有图 / 纯文本对比，动态压语言先验；LLaVA-1.5 7B/13B、InstructBLIP、Qwen-VL，附录 Table 21 有 Qwen2-VL 2B/7B 与 Qwen2.5-VL 3B/7B（**只有 POPE MSCOCO random，基线是 direct sampling**）：Qwen2.5-VL-7B Acc 83.70→88.63、F1 80.65→88.04（recall 67.93→83.67，precision 99.22→92.89）；Qwen2.5-VL-3B Acc 87.27→90.67。开销（Table 22）：0.4579→0.6075–0.6277 s/token。代码 https://github.com/lingfengren/NoLan 。
- Delve into VCD 2412.06775 — A：摘要称不同对比样本在不同基准上增益不一。
- DoLa：只在别人表里见（S）：OPERA Table 1 LLaVA-1.5 CHAIR_S Greedy 45.0 → DoLa 47.8（升高）；SID Table 5 MME 1510.8→1480.7。

补注（1.3）：DeCo Table 2 的 Greedy / Beam / OPERA 行与 OPERA Table 1（max new tokens 512）逐数相同，推断 DeCo 的 CHAIR 也是 512 口径（推导档；DeCo 正文未检到该参数）。

---

## 第 2 组 注意力重分配类

组内按轴最强者：
- 模型族最多：VAR（LLaVA-1.5 7B/13B、LLaVA-1.5-HD-13B、VILA-13B、Qwen2-VL-7B、InternVL2-8B）与 ILVAD（LLaVA-1.5-7B、LLaVA-NeXT-7B、Qwen2-VL-7B、Qwen3-VL-8B、InternVL3-8B，附录 Qwen2.5-VL-7B、Qwen3.5-9B、GLM-4.1V-9B）。ILVAD 是本组唯一在 Qwen3 / InternVL3 一代报 CHAIR 的。
- 同表涨幅最大（LLaVA-1.5，CHAIR_S，512 tokens，各自口径）：PAI 46.6→24.8（greedy）；Devils 53.0→25.0；ILVAD 48.6→32.6；TARAC 45.4→30.0。四者都伴随 recall / F1 / 长度变化，见各条。
- 对照最严：VAR 有随机头消融对照（Fig. 9）；SPARC 把 recall 与 precision 分开报并对别人方法做了同口径复测（Table 2/13）；CAAC 报两档 max tokens。
- 开销最低：SPARC 自测 30.37→31.21 ms/token（+2.8%）；ILVAD 自称 "almost no additional inference overhead"（只有图 Fig. 5，无数字）。

### 2.1 PAI（Paying More Attention to Image）— F
- arXiv 2407.21771 / 2024 / ECCV 2024（发表处为记忆，未在文本核对）。推理时；放大对图像 token 的注意力（系数 α，层先验 L），再减去无图分支的 logits（系数 γ）。
- 模型族：LLaVA-1.5、MiniGPT-4、Shikra（全 Vicuna 一代）；附录 LLaVA-1.5-13B。
- 口径：CHAIR：max_new_tokens 512、随机 500 张；POPE 报 Acc 与 F1，含 single-turn 与 multi-turn；MMHal-Bench；GPT-4V（50 图）。未报种子、未在主表报 recall（Table 4 的消融里有 F1 列）。
- 效果（Table 1，CS/CI）：LLaVA Greedy 46.6/13.4 → 24.8/6.9；Beam 46.4/14.3 → 21.8/5.6；Nucleus 58.2/18.2 → 43.4/14.7；MiniGPT-4 Greedy 32.8/11.1 → 26.3/8.8；Shikra Greedy 51.2/14.4 → 37.6/10.0。POPE（Table 2，LLaVA greedy single-turn）Acc 84.76→85.82、F1 85.51→85.97。
- 开销：作者未给（未找到）；别人实测：SPARC Table 6 报 30.37→57.75 ms/token（+90.2%）。
- 一般能力 / 损伤（别人实测）：
  - SPARC Table 13（LLaVA-1.5，CHAIR 口径，带 recall）：Baseline CHAIR_S 53.96、Recall 79.46、F1 81.99 → PAI CHAIR_S 34.92、**Recall 72.44、F1 80.52（低于基线）**。
  - Devils Table 2（LLaVA-1.5-7B）：Greedy F1 76.7 → PAI 75.2。
- 对照：无随机对照；有与 Prompt Highlighter 的比较（附录 C）。
- 失败条件：作者自述 γ 敏感（逐字）："When γ is too large, it can lead to uncontrollable model behavior."；Table 4 里 α 过大时 "resulting in an unbalanced response, we terminate the experiment"。
- 作者自认局限：标题为 "Conclusion and Limitation" 的一节里我没检到具体的局限陈述句（未找到）。
- 代码：正文文本未抓到 URL（未找到）。

### 2.2 VAR（Visual Attention Redistribution，"visual attention sink"）— F
- arXiv 2503.03321 / 2025 / ICLR 2025（发表处为记忆）。推理时；找 image-centric heads，把 sink token 上的注意力预算重分给其余视觉 token。
- 模型族：LLaVA-1.5-7B/13B、LLaVA-1.5-HD-13B、VILA-13B、Qwen2-VL-7B、InternVL2-8B。
- 口径：CHAIR（max tokens 未检到）；POPE(all) F1 与 Acc；MMHal；另 10 个通用基准、MMVP、CV-Bench。ρ 按任务类型各设一个值（通用 0.8、幻觉 0.5、视觉中心 0.9）。
- 效果（Table 2，CS/CI）：LLaVA-1.5-7B 45.0/14.7 → 43.2/13.8；LLaVA-1.5-13B 20.6/6.2 → 17.3/5.1；**Qwen2-VL-7B 30.5/8.4 → 30.1/8.2；InternVL2-8B 32.4/9.7 → 31.8/9.3**。POPE Acc：LLaVA-1.5-7B 84.76→85.87；Qwen2-VL-7B 87.5→88.2；InternVL2-8B 87.8→88.6。
- 开销：未找到。
- 一般能力（Table 1）：LLaVA-1.5-7B MME 1495.5→1513.8、MMBench 64.3→65.1；Qwen2-VL-7B MME 1672.3→1688.5；InternVL2-8B 1648.1→1655.4（作者报全部为正）。
- 对照：随机头消融对照（Fig. 9，POPE，LLaVA-1.5-7B）："The performance drops more significantly when ablating the image-centric heads than when ablating the random heads."
- 失败条件（别人实测）：ILVAD Table 1（LLaVA-1.5-7B，greedy，512 tokens，3 组 500 图）：Greedy CHAIR_S 48.6 → **VAR 52.5（升高）**，CHAIR_I 13.52→14.17，MMHal Hal 67.0→62.2。新一代模型上自报 CHAIR_S 只降 0.4–0.6。
- 作者自认局限（逐字）："the raw attention map may not be perfect for grounding the object because the model may have seen the object incorrectly (Guan et al., 2024) or the visual encoder may misinterpret the image (Tong et al., 2024b)." 与 "it is still worth exploring our methodology on different and larger LMMs"。
- 代码：文本未抓到 URL（未找到）。

### 2.3 ILVAD（Inter-Layer Visual Attention Discrepancy）— F
- arXiv 2605.20965 / 2026 / 发表处未核对（模板关键词写 ICML）。推理时；用层间视觉注意力差构造 saliency map，生成全程增强对"视觉证据 token"的注意力并增强文本。
- 模型族：LLaVA-1.5-7B、LLaVA-NeXT-7B、Qwen2-VL-7B、Qwen3-VL-8B、InternVL3-8B；附录 Qwen2.5-VL-7B、Qwen3.5-9B、GLM-4.1V-9B。
- 口径：CHAIR：max new tokens 512；**"we sampled three different sets of images using different random seeds. Each set includes 500 images"**；报 Len.；基线 greedy。POPE 报 Acc / F1（模型先生成 10 个 token 造 saliency map 再重答）。MMHal-Bench（GPT-4o 打分）、MME 子集（LLaVA-1.5）、LLaVA-Bench、CapMAS。
- 效果（Table 1，CS / CI / Len）：LLaVA-1.5-7B 48.6/13.52/82.66 → 32.6/9.42/81.82；LLaVA-NeXT-7B 29.2/7.91/158.13 → 25.8/6.52/152.87；Qwen2-VL-7B 20.8/7.58/87.41 → 17.8/5.14/82.51；Qwen3-VL-8B 51.6/9.84/316.58 → 45.2/8.52/310.59；InternVL3-8B 21.2/7.07/99.97 → 16.8/4.94/104.04。POPE Acc：Qwen3-VL-8B 89.19→89.80；InternVL3-8B 88.16→88.31。附录 Table 6：Qwen2.5-VL-7B CS 24.6→21.6（Len 144.48→137.09）、POPE-A 83.34→83.91；Qwen3.5-9B CS 54.1→50.6；GLM-4.1V-9B 26.2→17.6。
- 开销：自称（逐字）"it incurs almost no additional inference overhead"；只有图，无数字。POPE 上要先生成 10 个 token 再重答（额外一次短生成）。
- 一般能力：MME 子集（Table 2，LLaVA-1.5）631.66→641.66，其中 Count 158.33→153.33 下降。
- 对照：无随机部件对照（检索 "random" 只命中抽图）；有 τ、T 消融。
- 失败条件：新一代模型上 POPE 涨幅 0.15–0.6 Acc；Qwen3-VL-8B 的 CHAIR_S 仍在 45（基线 51.6，caption 长 316 词）。
- 作者自认局限：正文未检到 Limitation 节（未找到）。
- 代码：https://github.com/ytx-ML/ILVAD
- **同文对别人方法的复测（Table 1，LLaVA-1.5-7B，greedy，CS）**：Greedy 48.6；VCD 48.4；CODE 48.2；AGLA 46.4；VAF 49.8；VAR 52.5；SPARC 48.9；ONLY 47.8；VHR 34.5；ILVAD 32.6。即同一口径下 VCD / CODE / SPARC / ONLY 与 greedy 相差不到 1 点，VAF 与 VAR 高于 greedy。

### 2.4 SPARC — F
- arXiv 2502.01419 / 2025 / ICML 2025（发表处为记忆）。推理时；按步间注意力增量选择性放大视觉 token，逐步累积。
- 模型族：LLaVA-1.5、LLaVA-NeXT、Qwen2-VL。
- 口径：主指标是 CLAIR（IIW-400、DOCCI，长描述）；CHAIR 口径把 precision / recall / F1 分开报（Table 2/13）；POPE 只在附录（Table 11，Acc）。
- 效果：CLAIR（Table 3，IIW-400）LLaVA-1.5 56.36→61.49；LLaVA-NeXT 58.86→64.94；**Qwen2-VL 78.34→79.70（+1.36）**。CHAIR（Table 13，LLaVA-1.5）CHAIR_S 53.96→51.52、CHAIR_I 15.30→12.28、Recall 79.46→79.98。POPE Acc（Table 11）82.01→83.13。
- 开销（Table 6，ms/token）：Baseline 30.37；OPERA 322.28（+961.3%）；VCD 59.44（+95.7%）；Volcano 109.98；PAI 57.75（+90.2%）；SPARC 31.21（+2.8%）。
- 对照：有 "Naive Attn. Scaling" 对照（POPE 82.01→81.45，下降）。
- 同文对别人方法的复测（Table 13，LLaVA-1.5）：OPERA CHAIR_S 55.68（基线 53.96，升高）、Recall 78.82；VCD 57.92（升高）、Recall 77.50；PAI 34.92、Recall 72.44。作者逐字："our analysis reveals a previously overlooked limitation: these methods significantly reduce model recall (Figure 1)."
- 失败条件（别人实测）：ILVAD Table 1 里 SPARC 的 CHAIR_S 48.9（greedy 48.6）。
- 作者自认局限：未检到 Limitation 节（未找到）。
- 代码：https://github.com/mingi000508/SPARC

### 2.5 其余（定点读）
- Devils in Middle Layers 2411.16724（CVPR 2025，发表处为记忆）— F（定点）：LLaVA-1.5-7B/13B、Shikra-7B、MiniGPT-4-7B；中间层按多头平均放大视觉注意力。Table 2（512 tokens，greedy，CS/CI/F1）：LLaVA-1.5-7B 53.0/15.6/76.7 → 25.0/6.7/76.1；同表 **VCD 58.6/18.2/72.8（差于 greedy）**、PAI 24.2/7.1/75.2、OPERA 45.6/13.1/79.1。Table 12 的 α 敏感性：α=0.5 → 25.0/6.7/76.1，**α=0.6 → CS 1.0、F1 49.3**（描述塌缩）。自认局限（逐字）："the SVAR metric, used to detect hallucinated object tokens, is limited by the inherent attention behavior of LVLMs. When LVLM consistently exhibits extremely high visual attention ratios at nearly all layers, such as the case of Shikra illustrated in Fig. 13 (a), this may weaken the effectiveness of the SVAR metric."；"identifying the specific range of these stages remains somewhat subjective."。代码 https://github.com/ZhangqiJiang07/middle_layers_indicating_hallucinations
- TARAC 2504.04099（2025，IEEE 版式，发表处未核对）— F（定点）：LLaVA-1.5-7B、Qwen2-VL-7B、InternVL2-8B；跨步累积视觉注意力再注入。TABLE I（LLaVA-1.5，CS/CI/Recall/Len）：Greedy 45.4/13.4/77.5/89.09 → 30.0/8.1/**72.0**/83.24；同表 VCD 55.2/16.8、DoLa(high) 58.2/16.9（均差于 greedy）。TABLE VII（AMBER 生成）：**Qwen2VL CHAIR 5.2→4.1 但 Cover 67.0→53.3**；**InternVL2 CHAIR 8.5→8.5（不变）、Cover 73.4→70.4**。自认局限（逐字）："A current limitation is the reliance on fixed hyperparameters."。代码：未找到。
- CAAC 2505.21472（2025，发表处未核对）— F（定点）：InstructBLIP、LLaVA-1.5、LLaVA-NeXT（7B）。Table 1（CHAIR，CS/CI）：LLaVA-1.5 55.2/17.6 → 39.2/10.4；LLaVA-NeXT 33/9.4 → 30.6/8.1；同表 **VCD 57.8、AvisC 60.4、M3ID 56.2（LLaVA-1.5，都高于基线 55.2）；InstructBLIP 上 VCD 60.8、AvisC 71.0、M3ID 72.8（基线 55.6）；LLaVA-NeXT 上 VCD 41.6、M3ID 42（基线 33）**。AMBER 按 max tokens 64 / 512 两档报（Table 2）。作者逐字提到 "failure of proposed hallucination mitigation methods under Max New Tokens of 512"。代码 https://github.com/mehrdadfazli/CAAC
- FarSight 2505.16652（CVPR 2025，发表处为记忆）— F（定点）：LLaVA-1.5、InstructBLIP、Video-LLaVA、Chat-UniVi；改 causal mask（衰减式掩码）。Table 2：LLaVA-1.5 CHAIR_S 48.0→41.6、CHAIR_I 13.9→13.2；同表 ICD 47.7、VCD 46.8、OPERA 45.2；一般能力 MMBench 64.3→66.0，而 **ICD 63.1、VCD 63.9（低于基线）；VizWiz 上 VCD 48.5→43.4**。max tokens 未检到。Limitation 节未检到。

---

## 第 3 组 头消融或缩放类

组内按轴最强者：
- 模型族最多：Yang et al.（LLaVA-1.5-7B、MiniGPT-4 为主；附录 Table 9 有 Llama-3.2-11B-Vision、LLaVA-v1.5-13B、Chameleon-30B、LLaVA-v1.6-34B）与 SPIN（LLaVA-1.5 7B/13B、MiniGPT-4、Shikra、Qwen-VL，附录 LLaVA-NeXT-7B(Mistral)、Qwen2.5-VL-7B）。
- 对照最严：VHR 报 5 个随机划分的均值±标准差并报 caption 长度；Yang 有"微调随机头 / 全参数微调"对照（Table 5）与 Nocaps 域外；AllPath 报 MME 3 次运行标准差并换了问法（MCQ-POPE）。
- 同表涨幅最大（LLaVA-1.5-7B，CHAIR_S）：SPIN 44.4→16.6（F1 77.8→74.6）或 →26.4（F1 77.6）；HAVAE 48.2→18.2（F1 76.4→76.7）；AllPath 52.2→26.6；AD-HH 51.8→29.6（128 tokens）；VHR 49.68→33.32。
- 开销最低：都自称接近零额外开销；有数字的只有 SPIN 的 "improving throughput by 1.8× compared to existing alternatives"（相对别的方法，不是相对基线）。

### 3.1 Yang et al.（AD-HH / TF-HH）— F（修复部分）
- "Understanding and Mitigating Hallucination in Large Vision-Language Models via Modular Attribution and Intervention" / ICLR 2025 / arXiv 号未核对（缓存文件 yang_iclr25.txt）。AD-HH：推理时按条件下调"幻觉头"的文本注意力（top-k 头，LLaVA k=20、MiniGPT-4 k=10）；TF-HH：只微调这些头（训练）。
- 模型族：LLaVA-1.5-7B、MiniGPT-4；附录更大 / 更新模型只测了 AD-HH。
- 口径：CHAIR：COCO val 与 Nocaps（out-of-domain）各随机 500 张，提示 "Please describe this image in detail"，**"The maximum token limit is set to 128 by default"**，greedy；MM-Vet；BLEU / ROUGE / METEOR；人工评测（500 条/方法）；MME。未报种子。无 POPE。
- 效果（Table 1，CS/CI）：COCO LLaVA-7B Greedy 51.8/13.3 → AD-HH 29.6/8.0、TF-HH 35.0/8.7；MiniGPT-4 40.6/13.7 → 35.2/11.7、32.0/11.4。Nocaps LLaVA-7B 43.2/14.3 → 35.6/9.4、35.4/11.1；MiniGPT-4 57.4/20.0 → 46.8/16.2、45.2/16.8。附录 Table 9（AD-HH）：**Llama-3.2-11B-Vision 28.4/7.4 → 22.6/4.9**；LLaVA-v1.5-13B 48.6/12.4 → 38.8/9.4；Chameleon-30B 38.0/12.6 → 34.8/12.5；LLaVA-v1.6-34B 23.2/6.4 → 20.4/5.6。
- 同表别人方法（Table 1，COCO LLaVA-7B，128 tokens）：DoLA 53.8、VCD 55.4（均高于 greedy 51.8）；OPERA 50.2；HALC 50.2；LURE 51.2。
- 开销：未给数字；称 AD-HH "runs faster in practice compared to these baselines"。
- 一般能力：MM-Vet 总分 LLaVA-7B 31.4 → AD-HH 34.3、TF-HH 32.5（同表 VCD 29.4）；MME 1791.64 → 1812.36 / 1813.06；BLEU（Table 4）COCO 17.9 → AD-HH 17.8、TF-HH 18.8；Nocaps 24.6 → AD-HH 23.1（下降）。人工评测 generation quality：Greedy 3.99 → AD-HH 3.85（下降）、TF-HH 4.01。
- 对照：Table 5（LLaVA-1.5，CS/CI）：Original 51.8/13.3；Fine-tune Full Parameters 56.3/15.6；**Fine-tune Random Heads 54.4/15.7**；Fine-tune Hallucination Heads 35.0/8.7。Fig. 6 有随机头缩放对照。头在 COCO train 上识别、COCO val 与 Nocaps 上评。无换问法。
- 失败条件：
  - 别人实测（AllPath Table 1 / Table 6，LLaVA-1.5-7B，POPE 用 nucleus sampling temperature 1）：POPE-random Acc Vanilla 85.1 → AD-HH 85.0；A-OKVQA / GQA 各 split 与 Vanilla 相差 ≤0.1。即 AD-HH 在是非题格式上无增益（同文 CHAIR 上 AD-HH 52.2→33.2 有效）。
  - 作者自述 Chameleon-30B 上 CHAIR_I 12.6→12.5（基本不变）；全零下调文本注意力会掉 BLEU（Fig. 6c）。
- 作者自认局限（逐字）："a key limitation of Algorithm 1 is that it requires the explicit calculation of attention weights, making it incompatible with memory-efficient mechanisms like FlashAttention (Dao, 2023)."
- 代码：https://github.com/TianyunYoung/Hallucination-Attribution

### 3.2 SPIN — F
- arXiv 2505.16411 / 2025 / 发表处未核对（ACL 版式）。推理时；按每个样本的图像注意力，把图像注意力最低的一部分头（比例 r）乘 α 压低（α 可为 0，即剪掉）。
- 模型族：LLaVA-1.5 7B/13B、MiniGPT-4、Shikra、Qwen-VL；附录 LLaVA-NeXT-7B（Mistral-7B）、Qwen2.5-VL-7B。每个模型的层范围、r、α 各自设定（Table 1 每个模型给两组）。
- 口径：CHAIR：COCO val2014 随机 500 张，提示 "Please help me describe the image in detail."，greedy 为主，另 beam / nucleus；**报 F1**；max tokens 在正文未检到。POPE：multi-turn 口径，500 图 × 6 问。MME、MMMU（val）、GPT-4o 打分。未报种子。
- 效果（Table 1，greedy，CS/CI/F1）：LLaVA-1.5-7B 44.4/12.3/77.8 → 26.4/7.6/77.6（α=0.08）或 16.6/5.6/**74.6**（α=0.01）；LLaVA-1.5-13B 41.4/10.9/78.9 → 30.6/8.3/79.6；Qwen-VL 46.2/11.7/76.5 → 29.6/8.5/78.0；Shikra 55.2/14.0/75.39 → 30.6/8.0/75.41。附录 Table 12：LLaVA-NeXT-7B 35.6/8.6/71.7 → 32.6/8.1/72.3；**Qwen2.5-VL-7B 34.8/7.9/75.7 → 28.6/7.0/74.0**（F1 下降）。Table 13（multi-turn POPE）：Qwen2.5-VL-7B Acc 81.64→83.02、F1 77.75→79.80。
- 开销：摘要 "improving throughput by 1.8× compared to existing alternatives"；相对基线的数字未检到。
- 一般能力：MME（Table 5）LLaVA-1.5-7B 感知 1266.8→1294.0、认知 261.1→273.6；**Qwen2.5-VL-7B 感知 1521.9→1537.3，认知 590.7→552.5（下降，Numerical 155.0→125.0）**。MMMU（Table 6）Qwen2.5-VL-7B 49.9→49.9。GPT-4o 打分（Table 7）LLaVA-1.5-7B Accuracy 6.50→7.19，**Detailedness 6.83→6.12（下降）**。
- 对照：Table 9 比较了选头策略（Query / Key / Attention / Image Attention）；没有"随机头"对照（检索 random head 无命中）。同表 PAI 44.4→27.2、DAMRO 45.2（高于基线）、VTI 35.8。
- 失败条件：
  - 采样解码（Table 11）：MiniGPT-4 nucleus 基线 31.8/11.8/66.4 → SPIN 23.6/**12.5**/**62.9**（CHAIR_I 升高、F1 下降）；Shikra nucleus F1 72.8→71.5。
  - 新一代模型上 CHAIR F1 下降、MME 认知下降（见上）。
  - MiniGPT-4 上偶发重复输出（正文："SPIN occasionally leads to repetitive outputs for MiniGPT-4"）。
- 作者自认局限（逐字）："Our method's effectiveness is somewhat reduced when paired with sampling-based decoding strategies (e.g., nucleus sampling). We attribute this to the greater token selection variability inherent in these stochastic approaches"；"Our method requires access to the model weights, which limits its applicability to open-source models."
- 代码：摘要写 "Code is available here"（超链接，文本未抓到 URL；未找到）。

### 3.3 VHR（Vision-aware Head Divergence / Reinforcement）— F
- arXiv 2412.13949 / 2024 / 发表处未核对（ACL 版式）。推理时；按 VHD 分数逐样本选"视觉敏感头"并放大其输出。
- 模型族：InstructBLIP、LLaVA-1.5、LLaVA-NeXT。
- 口径：CHAIR：**5 个随机划分的均值±标准差，报 Len**，max_new_token 512，beam 数 5；POPE 三 split 平均 F1；LLaVA-Bench（GPT-4V）。
- 效果（Table 1，CS/CI/Len）：LLaVA-1.5 Greedy 49.68±1.47/14.32/83.06 → 33.32±1.31/9.71/81.33；InstructBLIP 45.32±2.24/12.98/91.06 → 37.76±2.76/9.75/106.49；LLaVA-NeXT 29.08±2.09/8.08/157.06 → 24.96±2.09/6.80/156.92。POPE F1（Table 2）：InstructBLIP 85.36→85.52；LLaVA-1.5 84.98→85.47；LLaVA-NeXT 88.51→88.87。
- 同表别人方法（Table 1）：**VCD 在三个模型上都高于 greedy**（InstructBLIP 50.72 vs 45.32；LLaVA-1.5 51.92 vs 49.68；LLaVA-NeXT 30.80 vs 29.08）；DoLa 46.00 / 50.88 / 28.76（≈greedy）；OPERA LLaVA-1.5 44.28、Len 75.88（变短）；CODE InstructBLIP 50.76。POPE F1：VCD 84.67 / 84.41 / 88.11（均低于 greedy）。
- 开销：摘要 "negligible additional time overhead"；只有图（Fig. 6）。
- 对照：Table 4 有 "fixed VHR"（不逐样本选头）对照：LLaVA-1.5 44.72（逐样本 33.32）。无随机头对照。
- 失败条件：别人实测一致有效（ILVAD Table 1：LLaVA-1.5 48.6→34.5）。作者自述继续加强会 "degrades the model's generation quality and fails to effectively mitigate hallucinations"。POPE 涨幅 ≤0.5 F1。没有 Qwen2 之后的模型。
- 作者自认局限（逐字）："there may be other architectural factors—such as those in the vision encoder and the FFN module in the LLMs—that contribute to hallucinations but were not directly addressed in this study."
- 代码：https://github.com/jinghan1he/VHR

### 3.4 AllPath（Intervene-All-Paths）— F（修复表）
- arXiv 2511.17254 / 2025 / 发表处未核对。推理时；按问题-答案对齐格式分别识别 image-to-input-text、image-to-output-text、text-to-text 三类通路的头并干预。
- 模型族：LLaVA-v1.5-7b、Qwen-VL-Chat；附录 Qwen2.5-VL-7B / 72B（**只有 POPE COCO**）。
- 口径：POPE（COCO 三 split，另 A-OKVQA、GQA）、自建 MCQ-POPE（四选一换问法）、MME：**"utilized nucleus sampling with a temperature of 1"**；CHAIR：500 张、greedy、"a maximum length of 512 tokens"。头用 adversarial 样本识别、三 split 上评；CHAIR 的头用 500 张 COCO val 图识别。MME 报 3 次运行的标准差。
- 效果（Table 1，LLaVA-1.5-7B）：POPE-random Acc 85.1→87.2、adversarial 80.9→82.8；MCQ-POPE random 72.8→80.5；CHAIR 52.2/14.6 → 26.6/7.2。Table 5（Qwen-VL-Chat）：CHAIR 43.4/13.5、F1 76.4、Len 98.1 → 34.2/9.0、77.2、91.0。Table 7：**Qwen2.5-VL-7B POPE-random Acc 87.6→90.6、adversarial 85.5→86.6；Qwen2.5-VL-72B adversarial Acc 85.6→85.7**。
- 一般能力：MME 幻觉子集（Table 2）540.0±39.69 → 600.0±8.66。
- 对照：无随机头对照（检索无命中）；有组件消融（Table 3）。
- 同文对别人方法的复测：
  - LLaVA-1.5-7B CHAIR：VCD 58.2/16.1（基线 52.2/14.6，升高）；ICD 51.4/14.7；PAI 28.8/7.9；AD-HH 33.2/7.5。
  - Qwen-VL-Chat（Table 5）：**PAI CHAIR 43.4→17.2 但 F1 76.4→70.1、Len 98.1→36.8；MCQ-POPE random Acc 61.8→57.9**；作者逐字："PAI compromises generative capability, resulting in a substantial reduction in generation length."；ICD CHAIR_S 50.4（升高）。
  - POPE 上 AD-HH 与 Vanilla 持平（见 3.1）。
- 失败条件：Qwen2.5-VL-72B adversarial 只 +0.1 Acc；新模型没有 CHAIR / 生成类数字。
- 作者自认局限（逐字）："we do not investigate what causal pathways are most effective for different types of questions, nor do we explore training strategies that could systematically improve the use of such pathways. Additionally, our analysis is constrained by the scope of existing hallucination benchmarks"。
- 代码：https://github.com/SooLab/AllPath

### 3.5 HAVAE（Vocabulary Hijacking）— F（定点）
- arXiv 2605.10622 / 2026 / 发表处未核对。推理时；排除 inert token 后选"关键头"并增强。
- 模型族：LLaVA-1.5 7B/13B、MiniGPT-4-7B、Shikra-7B；另 Qwen2-VL（Table 3）。
- 口径：CHAIR max_new_tokens 512、报 F1；POPE 与 POPE Chat；MME；AMBER（附录）。greedy 为主，附录有 beam / sample。
- 效果（Table 1，CS/CI/F1）：LLaVA-1.5-7B 48.2/14.2/76.4 → 18.2/3.8/76.7；Shikra 56.8/14.8/75.4 → 15.8/5.0/**71.8**；**MiniGPT-4 28.2/8.8/73.7 → 21.8/6.9/72.5**；Qwen2-VL（Table 3）27.6/8.8/79.2 → 22.8/6.2/79.4，POPE Acc 89.1→89.3。
- 同表别人方法（Table 1）：**VISTA 在 LLaVA-1.5-7B 上 CHAIR_S 15.6 但 F1 76.4→67.3**（作者把这类格标为 "potentially unreliable CHAIR scores"）；**Devils 在 LLaVA-1.5-13B 上 POPE Acc 82.6→71.4**；PAI 在 MiniGPT-4 上 POPE Acc 76.8→74.7。Table 4："Max Attention" 选头 CHAIR_S 7.8 但 F1 65.8、MME 感知 1399.0（基线 1472.5）。
- 开销：摘要 "no additional computational overhead"；数字未检到。
- 对照：选头策略对照（Table 4）；无随机头对照。
- 作者自认局限（逐字）："while this work uncovers the phenomenon of Vocabulary Hijacking, its mechanistic origin remains to be fully elucidated. Specifically, the precise training dynamics that precipitate this behavior remain unclear."
- 代码：https://github.com/lab-klc/HAVAE

---

## 第 4 组 子空间投影或静态权重编辑类

组内按轴最强者：
- 对照最严：QK Product Steering（同 k 的随机模式对照 + bottom-k 对照 + paired-bootstrap 95% CI，全程 greedy）。它也是本组唯一在 Qwen2.5-VL / InternVL3 / Pixtral 上成套报数的。
- 模型族最多：HIME（LLaVA-1.5、MiniGPT-4、mPLUG-Owl2、Qwen2-VL-8B、Qwen3-VL-8B）与 Nullu（LLaVA-1.5、MiniGPT-4、mPLUG-Owl2）。
- 开销最低：静态权重编辑类（Nullu、HIME、QK）推理时零额外开销（Nullu 自述 "without extra inference costs"）；Per-Instance 2608.09344 是推理时逐样本组合投影，开销数字未找到。
- 同表涨幅：Nullu 系三篇（Nullu / HIME / 2608.09344）都用 **max new tokens 64** 口径，LLaVA-1.5 greedy CHAIR_S 基线只有 20.40，与 512 口径（45–55）不可比。

### 4.1 Nullu（HalluSpace Projection）— F
- arXiv 2412.13817 / 2024 / CVPR 2025（发表处为记忆）。静态权重；用"真实 / 幻觉"配对描述的特征差做 SVD 得 HalluSpace，把 MLP 权重投到其零空间。
- 模型族：LLaVA-1.5、MiniGPT-4、mPLUG-Owl2（Vicuna / LLaMA-2 一代）。
- 口径：CHAIR：COCO val 随机 500 张，**"We use 64 as the max token number in this experiment"**，报均值±标准差（次数在正文未检到；与 HALC 协议一致推断为 3 次，推导档）与 BLEU；OPOPE（HALC 的离线 POPE，max tokens 256）；附录 POPE（"Original denotes direct sampling"）、MME、LLaVA-Bench（GPT-4V）。
- 效果（Table 1，CS/CI/BLEU）：LLaVA-1.5 Greedy 20.40±2.80/7.08/15.72 → 15.20±0.60/5.30/15.69；MiniGPT-4 32.40/12.20/14.57 → 21.40/8.99/14.81；mPLUG-Owl2 22.90/8.62/15.01 → 15.60/5.77/15.45。同表 VCD 20.30（≈greedy）、BLEU 14.53（下降）；Woodpecker 23.85（升高）。
- 开销：推理零额外（权重已改）；抽取 HalluSpace 需要配对数据（LURE 数据）。
- 一般能力：MME 全集图（Fig. 5）作者称有益；BLEU 持平。
- 对照：Table 16 / Fig. 7b 比较了差向量与随机向量在 HalluSpace 上的投影范数（约 10×）；**没有"投掉同秩随机子空间"的行为对照**（检索 random subspace / projection 无命中）。
- 失败条件：只在 64 token 短描述口径上报 CHAIR；长描述未报。别人同口径的后继（HIME、2608.09344）在其上再降 0.6–1.4 点 CHAIR_S（LLaVA-1.5），差距在其标准差量级内（Nullu ±0.60，2608.09344 ±0.35）。别人在 512 口径下的复测：MESA Table 1（LLaVA-v1.5，1000 图）Vanilla 48.80/13.40、Recall 77.70 → Nullu 44.80/13.00、Recall 75.10；MESA Table 2（Qwen-VL，POPE 一个数据源）Nullu Acc 74.73 对 Vanilla 74.76。
- 作者自认局限：正文无 Limitation 节（未找到）。
- 代码：https://github.com/Ziwei-Zheng/Nullu

### 4.2 QK Product Steering（Spectral Query-Key Product Weight Steering）— F
- arXiv 2606.20419 / 2026 / Workshop on Actionable Interpretability at COLM 2026。静态权重；对中间三分之一层的 M_h = W_q^T W_k 做 SVD，衰减 top-k 奇异模式（α=1 即清零）。
- 模型族：Qwen2.5-VL-7B、InternVL3-8B、Pixtral-12B（三种不同语言骨干）。
- 口径：CHAIR（N=1,000 或 4,946；约 200 步 greedy）、POPE F1、HallusionBench aAcc、MME total、MMMU；**"Decoding is greedy throughout"**；CHAIR 差值报 paired-bootstrap CI。注：Table 2 的 "CHAIRi" 列数值在 63–66，量纲与通常的 CHAIR_I 不同，正文我没检到解释（未找到），下文只用 CHAIRs 列。
- 效果（Table 2，CHAIRs）：
  - Qwen2.5-VL-7B：Baseline 31.44；random k=3 31.33；**top k=3 28.56**；Sym-only 29.53；Antisym-only 31.60。
  - InternVL3-8B：Baseline 33.81；random k=1 33.97；**top k=1 33.23**。
  - Pixtral-12B：Baseline 34.14；random k=3 34.00；**top k=3 33.81**。
  - CI（Table 5）：Qwen Sym top-3 ΔCHAIRs −2.17 [−2.95, −1.33]；**Pixtral top-3 ΔCHAIRs −0.36 [−0.85, +0.17]（含零）**，random −0.17 [−0.56, +0.21]。
  - 加大强度（Table 8，Qwen，N=500）：PSVD top-k=6、α=2 → 24.78。
- 一般能力：默认档 Qwen MME 2339.2→2293.3（Table 2）或 2344.4（Table 9，两表数不同，如实记）、MMMU 51.56→50.78；**加大强度（Table 9）：(k=3, α=2) MMMU 51.56→43.78、MME 2339.2→2253.5；(k=6, α=1) MMMU 47.11**。Pixtral 默认档 MMMU 45.44→43.11。
- 开销：推理零额外。
- 对照：matched random-k、bottom-k、Sym / Antisym 分解；附录 D.8 的 teacher-forced 检查显示幻觉 token 的 log-prob 基本不变（−0.004）而 grounded token 降得更多（−0.049）。
- 失败条件：InternVL3 与 Pixtral 上 CHAIRs 降幅 <1 点且与随机对照不可分；想要更大降幅就掉 MMMU / MME。
- 作者自认局限（逐字）："it does not add new visual knowledge or improve the model's underlying perception. Therefore, failures caused by poor object recognition, ambiguous images, or missing visual evidence may remain."；"Although we find that middle-layer dominant modes work well across multiple VLMs, the optimal configuration may vary across architectures."
- 代码：正文未给 URL（"Any released code is intended for research use"；未找到）。

### 4.3 HIME（Hallucination Insensitivity Model Editing）— F（定点）
- arXiv 2602.18711 / 2026 / 发表处未核对。静态权重；Nullu 式投影，但按层的"幻觉不敏感度"分数调强度。
- 模型族：LLaVA-1.5、MiniGPT-4、mPLUG-Owl2；另 Qwen2-VL-8B-Instruct、Qwen3-VL-8B-Instruct（Table 2，文中写法 "QWen3-VL-8B-Instruct"）。
- 口径：与 Nullu 相同（COCO 500 张、**max new tokens 64**、±、BLEU）；MME。无 POPE 主表。
- 效果（Table 1）：LLaVA-1.5 20.40/7.08 → 13.80±0.02/4.56（Nullu 15.20/5.30）；MiniGPT-4 32.40 → 16.80；mPLUG-Owl2 22.90 → 15.40。Table 2：Qwen2-VL 20.8/5.36/BLEU 11.16 → 17.2/4.43/11.30；**Qwen3-VL 8.40/4.62/BLEU 9.81 → 6.00/3.44/8.89（BLEU 下降）**。
- 对照：无随机对照（检索无命中）；无换问法。
- 失败条件 / 局限：正文未检到 Limitation 节（未找到）。Qwen3-VL 在 64 token 口径下基线 CHAIR_S 只有 8.40。
- 代码：未找到。

### 4.4 Per-Instance Disentangled Subspaces — F（定点）
- arXiv 2608.09344 / 2026 / 发表处未核对（BMVC 版式）。推理时（逐样本对多个幻觉子空间加权组合投影；作者称不改权重）。
- 模型族：LLaVA-1.5、MiniGPT-4、mPLUG-Owl2。口径同 Nullu（64 tokens、OPOPE）。
- 效果（Table 1）：LLaVA-1.5 15.20±0.60（Nullu）→ 14.60±0.35；MiniGPT-4 21.40 → 21.01±0.95；mPLUG-Owl2 15.60 → 15.21±1.01。相对 Nullu 的差值都在 Nullu 自己的标准差之内。
- 局限：未检到 Limitation 节；作者把 POPE 上的小增益写作 "even marginal F-score improvements"。代码：未找到。

### 4.5 ProjectAway — F（定点）
- arXiv 2410.02762 / 2024 / ICLR 2025。推理时；用 logit lens 的内部置信度检出幻觉物体，再把图像表征里该物体文本方向正交掉。
- 模型族：InstructBLIP、LLaVA-1.5；附录 LLaVA-NeXT、Cambrian-1。
- 效果（Table 2，表头列名按原文）：LLaVA Greedy 49.2 / 14.2 → 42.0 / 12.2（同表 OPERA 44.8 / 12.8）；InstructBLIP Greedy 57.0 / 23.3 → 43.8 / 12.5（基线是 beam 时 53.4 / 14.6）。附录 Table 7（500 张 COCO）：LLaVA-NeXT Beam CHAIR_S 23.8 → 17.2、Recall 63.12 不变；Cambrian-1 9.2 → 6.6。
- 作者自认局限（逐字）："The editing approach may struggle with highly abstract or longer sentences that involve attributes or interactions of objects."；"This can introduce noise to the internal confidence if certain tokens are common in multiple different words"。
- 代码：https://github.com/nickjiang2378/vl-interp

---

## 第 5 组 转向类 activation steering

（组内按轴最强者的小结见本节末 5.9。）

### 5.1 Revis（Sparse Latent Steering）— F
- arXiv 2602.11824 / 2026 / 发表处未核对（ICML 版式）。推理时；把"视觉向量"对语言先验方向做 Gram-Schmidt 正交化后，在单个深层按自适应阈值稀疏注入。转向向量用 Nullu 的 100 对样本算。
- 模型族：Qwen2.5-VL-7B（主）、Qwen2.5-VL-32B、Qwen3-VL-8B、LLaVA-1.5-7B、LLaVA-NeXT-7B（Mistral）、InternVL3-8B、InternVL3.5-8B。
- 口径：CHAIR：**COCO val2014 "randomly selecting 100 images"**（所以 CHAIR_S 都是整数），max new tokens 64 / 128 / 512 三档；基线 greedy（"Regular denotes the standard greedy decoding baseline"）。POPE 三 split 报 Acc / Recall / F1。MME、MM-Vet、MMMU-Pro。未报种子。
- 效果：
  - Qwen2.5-VL-7B（Table 3，512 tokens）：POPE-random Acc 89.27→91.90、adversarial 87.10→87.80；CHAIR 31.00/8.13 → 25.00/**8.23**（CHAIR_I 未降）。
  - LLaVA-1.5（Table 5）：CHAIR 54.00/15.78 → 30.00/14.16；POPE-random 87.67→89.37。LLaVA-NeXT：30.00/7.49 → 26.00/6.32。
  - Qwen2.5-VL-32B（Table 12）：CS 64 tokens 9.00→8.00；128 tokens 22.00→18.00；512 tokens 52.00→46.00。
  - Qwen3-VL（Table 14）：CS 64 tokens **8.00→8.00（CI 3.35→3.77 升高）**；128 tokens 17.00→14.00；512 tokens 45.00→43.00；POPE Acc 89.05→89.48。
  - InternVL3（Table 15）：POPE Acc **90.54→90.24（下降）**；CHAIR 29.00/8.44 → 24.00/7.86。InternVL3.5：POPE Acc 88.14→88.80，Recall 92.51→89.53；CHAIR 30.00/9.09 → 23.00/5.73。
- 一般能力（Table 4，Qwen2.5-VL-7B）：MME 2327.52→2345.30；MM-Vet 70.18→72.16。
- 开销：自称单层稀疏注入、无额外前向；数字未检到。
- 对照：无随机方向对照（检索 random vector / direction 无命中）；有层与 α、τ 消融。
- **同文对别人方法的复测（Qwen2.5-VL-7B，greedy，100 图）**：
  - Table 3（512 tokens，CS/CI）：Regular 31.00/8.13；**VCD 34.00/9.06；ONLY 33.00/9.75；VTI 35.00/7.49（CS 都高于基线）**；M3ID 31.00/8.88；AGLA 29.00/8.26。POPE-adversarial Acc：Regular 87.10；VCD 87.03；ONLY 86.93；AGLA 86.73；**VTI 85.27**。
  - Table 16（按 max tokens）：64 tokens 时 Regular 14.0，VCD 13.0、M3ID 11.0、ONLY 8.0、AGLA 10.0、VTI 9.0（都低于基线）；**到 512 tokens 时 VCD 34.0、ONLY 33.0、AGLA 32.0、VTI 35.0 都不低于基线 31.0**。作者逐字："While baselines like VCD and VTI suffer from severe degradation, rising to 34.00% and 35.00% respectively (worse than the Regular decoding at 31.00%)"。
  - Table 4（一般能力）：**VTI 使 MME 2327.52→2083.82、MM-Vet 70.18→56.38**（Rec 65.67→48.53、Know 58.57→39.88）；VCD MME 2258.86、MM-Vet 68.76。
  - LLaVA-1.5（Table 5）：VCD POPE-random Acc 87.67→86.97（greedy 基线下下降）、CHAIR 52.00/16.13；VTI CHAIR_S 54.00→35.00 但 CI 15.58（几乎不变）、POPE-adversarial 83.20→81.77。
- 失败条件：自述 InternVL3 的 POPE 已到天花板（"We attribute this plateau to the model reaching a capability ceiling on this specific discriminative task"）；Qwen3-VL 64 token 档无增益。
- 作者自认局限（逐字）："REVIS relies on the base model's representations, limiting its ability to rectify absolute perceptual blindness. Additionally, our evaluation focuses on 7B/8B and 32B architectures; verifying scalability on larger models (e.g., 70B+) remains for future work."（PDF 文本里方法名排成 "R EVIS"，此处合并了小型大写字母造成的空格。）
- 代码：https://github.com/antgroup/Revis

### 5.2 VTI（Visual and Textual Intervention）— F
- arXiv 2410.15778 / 2024 / ICLR 2025（发表处为记忆）。推理时；对视觉编码器与文本解码器各层加预先算好的方向（扰动图像 / 幻觉描述的特征差的主成分）。
- 模型族：LLaVA-1.5、InstructBLIP、Qwen-VL。
- 口径：POPE 三子任务平均 Acc / F1；CHAIR max new tokens 512，**报 Recall 与 Avg. Len**；MMHal-Bench（LLaVA-1.5）。α、β 在 {0.1,…,1.0} 上网格搜索。种子未报。
- 效果（Table 2，CS / CI / Recall / Len）：LLaVA-1.5 Vanilla 51.0/15.2/75.2/102.2 → VTI 35.8/11.1/76.8/93.8；InstructBLIP 54.0/18.1/71.1/115.3 → 43.4/11.8/70.1/105.8。POPE（Table 1）：LLaVA-1.5 Acc 79.8→86.5；Qwen-VL 83.5→85.2。同表 DOLA CHAIR_S 57.0（LLaVA-1.5）、60.0（InstructBLIP），VCD 51.0 / 57.0（不低于基线）。
- 对照：无随机方向对照；有 vision-only / text-only 拆分。
- 失败条件（别人实测）：见 5.1（Qwen2.5-VL-7B 上 512 tokens CHAIR_S 升到 35.0、MM-Vet 掉 13.8 点、POPE-adversarial 掉 1.8 点）。SPIN Table 1（LLaVA-1.5-7B）：VTI 44.4→35.8、F1 77.8→76.8。
- 作者自认局限：正文未检到 Limitation 节（未找到）。
- 代码：正文文本未抓到本方法的 URL（未找到）。

### 5.3 VISTA（Visual Information Steering + Self-Logits Augmentation）— F
- arXiv 2502.03628 / 2025 / ICML 2025（发表处为记忆）。推理时；逐样本算 Visual Steering Vector（有图 / 无图残差流之差）逐层注入，外加早层 logits 增强。
- 模型族：LLaVA-1.5、MiniGPT-4、Shikra、InstructBLIP（全 Vicuna 一代）。
- 口径：CHAIR max new token 512，greedy / beam / nucleus 三种解码各自配对；POPE 平均 Acc / F1；MME 全集；MMHal-Bench。种子、recall 未在主表报。
- 效果（Table 1，CS/CI）：LLaVA-1.5 Greedy 46.4/12.1 → 20.4/6.9；Beam 49.0/12.5 → 17.4/6.3；Nucleus 53.2/15.1 → 24.0/8.2；MiniGPT-4 Greedy 35.2/10.7 → 19.8/6.0；Shikra 56.8/14.8 → 31.4/9.7；InstructBLIP 38.0/10.7 → 27.4/8.1。
- 同表别人方法：**VCD LLaVA-1.5 Greedy 47.4（基线 46.4）、Nucleus 60.8（基线 53.2）；InstructBLIP Greedy 45.8（基线 38.0）、Nucleus 57.0（基线 46.6）**；DoLa Shikra 60.0（基线 56.8）；**OPERA InstructBLIP Beam 50.2（基线 37.8）**。
- 开销（Table 5，LLaVA-1.5，ms/token）：Greedy 28.54；VCD 58.34（×2.04）；PAI 57.78（×2.02）；VISTA 36.32（×1.27）。
- 一般能力（Table 3，MME 全集）：LLaVA-1.5 greedy 1752.35→1771.87；nucleus 1625.22→1738.56。
- 对照：无随机方向对照。
- 失败条件（别人实测）：HAVAE Table 1（LLaVA-1.5-7B）：VISTA CHAIR_S 15.6 但 **CHAIR 口径 F1 76.4→67.3**、POPE Acc 84.8→83.1；MiniGPT-4 F1 73.7→68.3。作者自述注入强度不当会明显劣化（"using inappropriate scale (see Fig. 6) will cause clear degradation"）。
- 作者自认局限（逐字）："optimal settings may vary across different architectures. Second, the effectiveness of VSV relies on the quality of visual cues extracted by the LVLM's vision encoder – models with weak visual encoding capabilities may see reduced benefits. Third, the current implementation focuses on addressing hallucination in single-round tasks; adaptation to interactive scenarios like visual dialogue may require additional considerations."
- 代码：https://github.com/LzVv123456/VISTA

### 5.4 DMAS（Dynamic Multimodal Activation Steering）— F
- arXiv 2602.21704 / 2026 / ICLR 2026。推理时；在"真实性头"与"视觉感知头"上加转向向量，向量按输入从聚类库里动态检索。
- 模型族：LLaVA-v1.5、Qwen-VL；附录 Table 13：Qwen2.5-VL、InternVL3、Mantis、Idefics3（只有 MME 幻觉子集与 CHAIR，greedy）。
- 口径：MME 幻觉子集；POPE（三数据源，Acc / Prec / Rec / F1）；CHAIR（max tokens 未检到；Table 3 的 Regular / VCD / OPERA / VTI 行与 VTI 论文 Table 2 逐数相同，推断沿用 512 口径，推导档）；AMBER（附录）；ScienceQA / ViQuAE。
- 效果：CHAIR（Table 3，LLaVA-v1.5）Regular 51.0/15.2 → 30.8/**11.4**（VTI 35.8/11.1，CHAIR_I 未超过 VTI）；MME 幻觉子集（Table 1）LLaVA-v1.5 565.33→659.99、Qwen-VL 587.33→633.33；POPE GQA Qwen-VL Acc 77.47→84.40。附录 Table 13（CS/CI）：**Qwen2.5-VL 47.4/10 → 43.2/9.5；InternVL3 28.4/7.6 → 26.4/6.9**；Mantis 44.6/12.7 → 34.8/9.7；Idefics3 49.9/8.8 → 45.2/8.2。
- 开销：只有图（Fig. 5）；逐字："VCD's inference latency is almost twice that of the original model, but our model achieves better hallucination mitigation effects while adding only a small amount of inference time."
- 对照：无随机方向 / 随机头对照（检索无命中）；有去掉各向量的消融（Table 4）、向量库数据规模与来源消融（Table 10/11）。
- 失败条件：新一代模型上 CHAIR_S 只降 2.0–4.2 点。
- 作者自认局限：正文未检到 Limitation 节（未找到）。代码：未找到。

### 5.5 Entangled Steering / MESA — F（定点）
- arXiv 2604.07914 / 2026 / 发表处未核对（ACM 版式）。推理时；学一个转向方向（训练转向向量，不改模型权重），损失里约束"只压幻觉、不改其余分布"。
- 模型族：LLaVA-v1.5、Qwen-VL（一代）。
- 口径：CHAIR：**随机 1000 张**、max new tokens 512、**报 Recall 与 Avg. length**；POPE 三数据源；AMBER；LLaVA-Bench。
- 效果（Table 1，CS / CI / Recall / Len）：LLaVA-v1.5 Vanilla 48.80/13.40/77.70/98.70 → MESA 31.00/8.60/75.80/93.50；Qwen-VL 38.70/14.30/72.70/82.40 → 29.00/8.20/72.70/83.70。
- **同文对别人方法的复测（Table 1，LLaVA-v1.5，512 tokens）**：VCD 56.30/16.00（升高）；ICD 59.50/15.80（升高）；VAF 51.10；ICT 51.00；**VTI 40.70/12.00、Len 98.70→80.30**；**Nullu 44.80/13.00、Recall 75.10**（Nullu 自报的 64 token 口径是 20.40→15.20）。Qwen-VL 上 VCD Recall 72.70→64.90、Len 82.40→71.30。POPE（Table 2 的一个数据源）：Qwen-VL 上 **Nullu Acc 74.73（Vanilla 74.76，无增益）**。
- 作者逐字（对 VTI / Nullu 类方法）："despite improving hallucination metrics, these methods do so at the cost of altering the generation process. Specifically, they lead to shorter outputs and systematically shifted token distributions in generative scenarios (see Figure 2)."
- 对照：无随机方向对照。局限节：未检到。代码：未找到。

### 5.6 OSGA（One-shot Optimized Steering Vector）— F（定点）
- arXiv 2601.23041 / 2026 / 发表处未核对（ICML 版式）。推理时注入；向量由一张图上的优化得到（one-shot），全任务共用。
- 模型族：LLaVA-v1.5；附录 Qwen2-VL-7B。（Qwen2.5 / Qwen3 / InternVL3.5 只出现在参考文献里。）
- 口径：CHAIR 500 张（沿用别人抽好的子集）、报 Recall；POPE 三数据源；MME-Hall；FaithScore、HalFscore、GAVIE；GOAT-Bench（安全）。
- 效果：POPE（Table 2，LLaVA-v1.5，MSCOCO 平均 Acc）79.83→86.29；附录 Table 7（Qwen2-VL-7B）：CHAIR 平均 14.91→13.27、Recall 68.4→68.6、POPE Acc 88.99→90.02。
- 对照：数据点选择策略与随机选点的比较（Table 6）；无随机方向对照。
- 作者自认局限（逐字）："For tasks that require specific answer formats, such as Yes/No questions, the gains of this method are relatively limited, and overfitting can easily occur during optimization, leading the model to consistently respond with "yes" or "no.""（引号字符按 PDF 文本可能是弯引号。）
- 代码：未找到。

### 5.7 SteerVLM — F（定点）
- arXiv 2510.26769 / 2025 / 发表处未核对。训练一个轻量转向模块（基座冻结），推理时按 target / converse 提示动态调激活；幻觉只是其应用之一。
- 模型族：LLaVA-1.5-7B。口径：OHD 数据集上的 POPE（Acc / F1）。
- 效果（Table 1，Overall Acc/F1）：LLaVA1.5-7B 84.5/85.5 → 86.4/86.8。同表：**CAA 56.2/69.5、MLLM Steering 75.9/78.6、ML-ACT 80.6/76.4（都低于不转向的基线）**；Act Add 84.7/85.7。
- 开销：Table 6 有计算量对比（未细读）。无 CHAIR、无新一代模型。

### 5.8 ASD（ACL 2025）与 SSL
- ASD：已取到正文，见 5.10。
- SSL 2505.16146：主查已读，不重复。

### 5.9 组内按轴最强者
- 模型族最多 / 新一代覆盖：Revis（Qwen2.5-VL 7B/32B、Qwen3-VL、InternVL3、InternVL3.5、LLaVA-1.5、LLaVA-NeXT）。DMAS 次之（Qwen2.5-VL、InternVL3、Mantis、Idefics3 只在附录各一行）。
- 同表涨幅最大（LLaVA-1.5，512 tokens，CHAIR_S）：VISTA 46.4→20.4；Revis 54.0→30.0（100 图）；MESA 48.8→31.0（1000 图，报 recall 与长度）；DMAS 51.0→30.8；VTI 51.0→35.8。
- 对照最严：本组没有任何一篇做随机方向对照（VTI、VISTA、DMAS、Revis、MESA、OSGA、SteerVLM 七篇里检索 random vector / direction 均无命中）。评测最细的是 MESA（1000 图 + recall + 长度）与 Revis（三档 max tokens + 对五个基线在 Qwen2.5-VL 上复测）。
- 开销最低：Revis / DMAS / VTI 用预先算好的向量，自称接近零开销但无数字；VISTA 自测 ×1.27。

补注（5.8 更正）：ASD 已取到正文（ACL Anthology 2025.acl-long.634，缓存为 asd_acl25.txt），见 5.10。

### 5.10 ASD（Activation Steering Decoding）— F（定点）
- ACL 2025（2025.acl-long.634；未找到 arXiv 版，1 条查询）。推理时；用小校准集（COCO 物体标注）抽"幻觉方向"，正向与负向转向两个分支做对比解码（两分支并成一个 batch）。
- 模型族：LLaVA1.5-7B、Qwen-VL-Chat（一代）。
- 口径：POPE 三数据源，**Greedy 与 Direct Sampling 两种基线都报**；CHAIR 500 张、报 Recall（max tokens 未检到）；MME、MMBench、MMMU、TextVQA、MMVet、LLaVABench。
- 效果：POPE MSCOCO Acc（Table 1）LLaVA1.5-7B Greedy 85.13→88.01、Sampling 81.49→87.19；Qwen-VL-Chat Greedy 86.44→88.09。CHAIR（Table 2，LLaVA-1.5，CS/CI/Recall）51.0/14.7/82.8 → 40.0/11.3/82.0。
- **同表 VCD 在 greedy 基线下的数**（Table 1）：LLaVA1.5-7B MSCOCO Acc 85.13→85.16（+0.03）、A-OKVQA 78.99→78.92、GQA 76.60→76.49；Qwen-VL-Chat MSCOCO 86.44→86.42。同一张表 Direct Sampling 基线下 VCD 是 81.49→85.41（+3.92）。即 VCD 的 POPE 增益在 greedy 下消失。
- 开销（Table 5）：20 / 50 / 100 tokens 分别 +18.6% / +12.8% / +11.6%。
- 一般能力（Table 3）：LLaVA1.5-7B MME 1810.70→1827.21、MMBench 65.46→65.38；**Qwen-VL-Chat MME 1839.55→1825.20（下降）**。同表 VCD：LLaVA1.5-7B MME −10.29、TextVQA −1.50、LLaVABench −1.70。
- 失败条件（自述）：正向转向 λ>0.3 时性能下降（"accuracy dropping by 2.71% at λ = 0.5"）；最优强度随数据集变。
- 作者自认局限（逐字）："our current approach primarily addresses object-level hallucination, as the steering vectors are extracted using only COCO object annotations."
- 对照：无随机方向对照。代码：未检到。

---

## 第 6 组 微调 / 训练类

组内按轴最强者：
- 模型族最多 / 新一代覆盖：ViPSy（LLaVA-1.5-7B/13B 主表；附录 Qwen2.5-VL-7B、mPLUG-Owl3-7B、InternVL3.5-8B、Kimi-VL-A3B）与 REVERSE（LLaVA-v1.5-7B、LLaVA-MORE-8B(Llama-3.1)、Qwen2.5-VL-3B）。
- 评测最宽 / 对一般能力查得最细：HALVA（CHAIR 带 Len、AMBER、MME-Hall、MMHal-Bench、HallusionBench、通用 VQA、语言质量）。
- 同表涨幅最大：RLHF-V（Object HalBench Resp. 50.5→12.2，基座 Muffin）；REVERSE 的激进阈值档（LLaVA-v1.5 CHAIRs 50.0→13.6，但 Cover 51.0→26.9）。
- 开销：训练类推理零额外（HA-DPO、HALVA、CCA、EOS、TF-HH、ViPSy）；REVERSE 例外（训练 + 推理时回溯重采样，token 数 1.75×–2.63×）。

### 6.1 REVERSE（Generate, but Verify）— F
- arXiv 2504.13169 / 2025 / 发表处未核对。训练（1.3M 样本、带 </CN> </UN> 置信标记的 hallucination-aware 微调）+ 推理时（P(</UN>) 超阈值 τ 就回溯，rejection sampling + query rewriting）。
- 模型族：LLaVA-v1.5-7B（LoRA）、LLaVA-MORE-8B（Llama-3.1）、Qwen2.5-VL-3B（全量微调，用 100k LLaVA 指令数据子集；表里记作 Qwen2.5-VL_FT）。
- 口径：CHAIR-MSCOCO（沿用 EOS 论文口径）、AMBER 生成子集（CHAIR / Cover / Hal / Cog）、HaloQuest、MMHal-Bench；阈值 τ 按骨干各设（LLaVA 0.003、Qwen 0.01）。
- 效果（Table 1；CHAIRi / CHAIRs｜AMBER CHAIR / Cover / Hall / Cog）：LLaVA-v1.5-7B None 15.4/50.0｜7.8/51.0/36.4/4.2 → REVERSE(τ=0.003) 10.3/37.0｜6.0/52.2/30.4/3.0。LLaVA-MORE-8B 14.4/52.0｜7.8/53.1/36.6/3.9 → 12.2/42.4｜6.5/54.8/35.5/3.9。**Qwen2.5-VL_FT-3B 12.2/45.8｜7.7/51.7/35.9/4.1 → 10.5/39.4｜7.5/51.5/34.4/3.6**。
- 同表别人方法（LLaVA-v1.5-7B，多数取自原论文）：VCD 14.9/48.6；OPERA 14.6/47.8；DoLA 14.1/**51.6**；AGLA 14.1/43.0；MEMVR 13.0/46.6；EOS 12.3/40.2（AMBER Cover 49.1）；HALVA 11.7/41.4；HA-DPO 11.0/38.2；Woodpecker 14.8/45.8。Qwen2.5-VL_FT-3B 上 DoLA 14.0/47.6、AMBER CHAIR 9.7（都差于基线）。
- 开销（Table 5，AMBER-G 1,004 条）：token 数相对 LLaVA-v1.5-7B 为 1.75× / 2.05× / 2.63×（随纠错轮数）。
- 一般能力 / 损伤：激进阈值 τ=0.0003 时 LLaVA-v1.5 CHAIRs 13.6 但 **AMBER Cover 51.0→26.9**；LLaVA-MORE Cover 53.1→38.9。
- 对照：组件消融（Table 4）；无随机对照。
- 失败条件 / 作者自认局限（逐字）："it does not improve performance on discriminative VQA tasks (see Table A.1) as the backtracking methods generally didn't help further reasoning."；"REVERSE reduces the hallucination with the cost of more generated tokens."；Qwen2.5-VL 因为官方不放指令微调数据，只能用替代数据（"it is not feasible given the current release conditions"）。
- 代码：https://github.com/tsunghan-wu/reverse_vlm

### 6.2 HALVA（Data-augmented Phrase-level Alignment）— F
- arXiv 2405.18654 / 2024 / ICLR 2025。训练；生成式数据增强造"正确 / 幻觉"短语对，短语级对齐损失 + 对参考模型的 KL 约束。
- 模型族：LLaVA-v1.5 7B / 13B、VILA-v1.5-13B（HALVA13B/384）。
- 口径：CHAIR（Ci / Cs / Len）、MME-Hall、AMBER（CHAIR / Cover）、MMHal-Bench、HallusionBench、通用 VQA、语言质量（GPT-4o-mini 评 100 条）。POPE 只放附录并说明理由。
- 效果（Table 1，Ci / Cs / Len）：LLaVA-v1.5-7B 15.4/50.0/100.6 → HALVA7B 11.7/41.4/92.2。MME-Hall（Table 2）648.3→665.0。附录：POPE 87.1（7B，换了 α=0.005）。
- **同表别人方法的一般能力（Table 2，MME-Hall，LLaVA-v1.5-7B 基线 648.3；作者把低于基线的标红）**：HA-DPO 618.3；EOS 606.7；VCD 604.7；Woodpecker 366.7；RLHF-V13B 585.0（13B 基线不同，如实记）。Table 1：**EOS Len 100.6→79.7**；HA-DPO Len 91.0。作者逐字："while EOS achieves a lower hallucination rate, it degrades the detailedness of image descriptions, performing worse than the base model."
- 作者对 POPE 的说法（逐字）："we note a few key limitations and find it to be a not well suited benchmark for evaluating MLLMs"；"the questions are formulated based on only 500 images and include a total of 79 unique objects"。
- 作者自认局限（逐字）："MLLMs also suffer from other forms of hallucinations that may occur due to modality misalignment or over-reliance on language while ignoring other input modalities, among others. While we showed some promising results on generalization to other forms of hallucination, a rigorous exploration of those directions is left for future work."
- 代码：https://github.com/pritamqu/HALVA

### 6.3 CCA（Concentric Causal Attention）— F
- arXiv 2410.15926 / 2024 / NeurIPS 2024（发表处为记忆）。训练；改视觉 token 的位置排列（同心）与因果掩码，**从头按 LLaVA 流程重训**。
- 模型族：LLaVA-1.5-7B。
- 口径：POPE 三数据源；CHAIR 两档（512 / 64），greedy 与 beam(5)，**报 recall 与 len**；MME 幻觉子集；LLaVA-Bench；多选基准（SEED、SQA、GQA、VizWiz、MMBench、MMStar、TextVQA）。
- 效果（Table 2，greedy，CS/CI/rec/len）：512 档 baseline 46.2/12.9/80.3/97.2 → CCA 43.0/11.5/80.4/96.6；64 档 21.0/6.2/66.3/54.9 → 18.2/5.4/66.7/54.5。**beam(5) 512 档 49.4/13.9 → 48.6/13.4（不到 1 点）**。POPE MSCOCO 平均 Acc 81.38→86.86（基线与 VCD 的数取自 VCD 论文，即 sampling 基线）。
- 同表 LLaVA-RLHF（S）：512 档 43.6/10.5、rec 78.0、len 117.9；POPE 平均 Acc 84.13。同文 Table 5：LLaVA w/ VCD 的 SEED_I 66.1→63.7、TextVQA 58.2→54.4。
- 作者自认局限（逐字）："our focus is only limited to handling of image-text inputs."
- 失败条件：需要重训整个模型；只在 LLaVA-1.5 一个模型上。
- 代码：https://github.com/xing0047/cca-llava

### 6.4 ViPSy（Vision-driven Preference Synthesis）— F（定点）
- arXiv 2606.28401 / 2026 / Preprint。训练；用图像变体从策略模型自己的生成里合成偏好对，再做 DPO。
- 模型族：LLaVA-1.5-7B / 13B（主表）；附录 Table 6：Qwen2.5-VL-7B、mPLUG-Owl3-7B、InternVL3.5-8B、Kimi-VL-A3B。Table 11 报 5 次推理的方差。
- 效果（Table 6；Object HalBench Resp. / Ment.｜AMBER CHAIR / Hal / Cog｜HallusionBench aAcc｜MMStar｜MMVP｜CV-Bench）：
  - Qwen2.5-VL-7B：9.0/5.3｜5.0/26.4/1.7｜57.7｜59.8｜56.6｜78.3 → 7.6/4.8｜4.1/23.3/1.0｜60.4｜61.7｜58.6｜**78.0**。
  - InternVL3.5-8B：8.3/4.6｜4.3/24.6/1.5｜64.2｜66.3｜59.3｜81.6 → 7.3/4.2｜3.9/17.3/1.2｜65.4｜67.9｜60.0｜**81.4**。
- 局限节：未检到。代码：https://github.com/yunpal/ViPSy

### 6.5 其余（定点或只在别人表里见）
- EOS-decision "Less is More" 2402.14545（ACL 2024，发表处为记忆）— F（定点）：训练（选择性 EOS 监督 / 数据过滤），LLaVA-1.5。别人表里的数：CHAIR 12.3/40.2、Len 79.7（HALVA Table 1）；MME-Hall 606.7（基线 648.3）。作者自述（逐字）："these methods are not directly transferable to addressing hallucination problems in broader Visual Question Answering (VQA) tasks"；"As shown in Table 7, our methods do not yield performance gains on these benchmarks."（指 MME 与 POPE）。
- RLHF-V 2312.00849（CVPR 2024，发表处为记忆）— F（定点）：训练（细粒度人工纠正反馈 + DDPO），基座 Muffin。Table 1：Object HalBench Resp. / Mention：Muffin 50.5/24.5 → RLHF-V 12.2/7.5；MHumanEval All 74.7→55.5；**LLaVA Bench Detail 79.7→75.3、Comp. 97.7→91.6（下降）**，Conv. 89.3→93.1。同表 LLaVA-RLHF 38.1/18.9。Limitation 节未检到。
- HA-DPO 2311.16839 — A（取到正文但只看了表目录）：数字只在别人表里见（S）：CHAIR 11.0/38.2、Len 91.0、MME-Hall 618.3（HALVA Table 1/2）；AMBER-G CHAIR 6.7、Cover 49.8（REVERSE Table 1）。
- TF-HH：见 3.1（Yang et al.）。只在 LLaVA-1.5-7B 与 MiniGPT-4 上；附录更新模型的表只有 AD-HH。
- LLaVA-RLHF 2309.14525 — S：只在 CCA Table 1/2、RLHF-V Table 1 里见。
- 只在检索摘要里见到、未取正文（S）：CHAIR-DPO（BMVC 2025）、SymMPO（NeurIPS 2025）、HSA-DPO（AAAI 2025）、TPO 2412.14487（摘要称有 Qwen2-VL-7B 扩展）、OPA-DPO（Revis 相关工作里提到）。

---

## 新一代模型上报告过数字的修法（小表）

"新一代"按任务给的名单：Qwen2.5-VL、Qwen3-VL、InternVL2.5/3/3.5、Gemma3、LLaVA-OneVision、Llama-3.2-Vision、Pixtral。Qwen2-VL、InternVL2、LLaVA-NeXT 不在名单里，另列在表后。全部 F 级，数字按原表；基线解码与图数不同，不可横比。

| 方法（组） | 模型 | 基准（口径） | 基线 → 方法 |
|---|---|---|---|
| NoLan（1） | Qwen2.5-VL-7B | POPE MSCOCO random，基线 direct sampling（Table 21） | Acc 83.70 → 88.63；F1 80.65 → 88.04 |
| NoLan（1） | Qwen2.5-VL-3B | 同上 | Acc 87.27 → 90.67 |
| ILVAD（2） | Qwen3-VL-8B | CHAIR 512、greedy、3×500 图（Table 1） | CS 51.6 → 45.2；CI 9.84 → 8.52；POPE Acc 89.19 → 89.80 |
| ILVAD（2） | InternVL3-8B | 同上 | CS 21.2 → 16.8；CI 7.07 → 4.94；POPE Acc 88.16 → 88.31 |
| ILVAD（2） | Qwen2.5-VL-7B | 附录 Table 6 | CS 24.6 → 21.6；POPE-A 83.34 → 83.91 |
| ILVAD（2） | Qwen3.5-9B / GLM-4.1V-9B | 附录 Table 6 | CS 54.1 → 50.6 / 26.2 → 17.6 |
| AD-HH，Yang（3） | Llama-3.2-11B-Vision | CHAIR 128 tokens、greedy、500 图（Table 9） | CS 28.4 → 22.6；CI 7.4 → 4.9 |
| SPIN（3） | Qwen2.5-VL-7B | CHAIR greedy 500 图（Table 12） | CS 34.8 → 28.6；CI 7.9 → 7.0；F1 75.7 → 74.0 |
| SPIN（3） | Qwen2.5-VL-7B | multi-turn POPE（Table 13）；MME（Table 5） | Acc 81.64 → 83.02；MME 认知 590.7 → 552.5 |
| AllPath（3） | Qwen2.5-VL-7B | POPE COCO，nucleus T=1（Table 7） | random Acc 87.6 → 90.6；adv 85.5 → 86.6 |
| AllPath（3） | Qwen2.5-VL-72B | 同上 | random 87.7 → 90.7；adv 85.6 → 85.7 |
| QK Product Steering（4） | Qwen2.5-VL-7B | CHAIRs greedy（Table 2） | 31.44 → 28.56（随机对照 31.33） |
| QK Product Steering（4） | InternVL3-8B | 同上 | 33.81 → 33.23（随机对照 33.97） |
| QK Product Steering（4） | Pixtral-12B | 同上 | 34.14 → 33.81（随机对照 34.00；CI 含零） |
| HIME（4） | Qwen3-VL-8B | CHAIR 64 tokens（Table 2） | CS 8.40 → 6.00；CI 4.62 → 3.44；BLEU 9.81 → 8.89 |
| Revis（5） | Qwen2.5-VL-7B | CHAIR 512、greedy、100 图；POPE（Table 3） | CS 31.00 → 25.00；CI 8.13 → 8.23；POPE-random Acc 89.27 → 91.90 |
| Revis（5） | Qwen2.5-VL-32B | CHAIR 64 / 128 / 512（Table 12） | CS 9 → 8 / 22 → 18 / 52 → 46 |
| Revis（5） | Qwen3-VL-8B | CHAIR 64 / 128 / 512；POPE（Table 14） | CS 8 → 8 / 17 → 14 / 45 → 43；POPE Acc 89.05 → 89.48 |
| Revis（5） | InternVL3-8B | CHAIR、POPE（Table 15） | CS 29 → 24；POPE Acc 90.54 → 90.24 |
| Revis（5） | InternVL3.5-8B | 同上 | CS 30 → 23；POPE Acc 88.14 → 88.80 |
| DMAS（5） | Qwen2.5-VL | CHAIR greedy；MME 幻觉子集（Table 13） | CS 47.4 → 43.2；CI 10 → 9.5；MME 698.33 → 718.33 |
| DMAS（5） | InternVL3 | 同上 | CS 28.4 → 26.4；CI 7.6 → 6.9 |
| REVERSE（6） | Qwen2.5-VL-3B（自行微调版） | CHAIR-MSCOCO；AMBER-G（Table 1） | CHAIRs 45.8 → 39.4；AMBER CHAIR 7.7 → 7.5；Cover 51.7 → 51.5 |
| ViPSy（6） | Qwen2.5-VL-7B | Object HalBench；AMBER；HallusionBench（Table 6） | Resp. 9.0 → 7.6；AMBER CHAIR 5.0 → 4.1；aAcc 57.7 → 60.4 |
| ViPSy（6） | InternVL3.5-8B | 同上 | Resp. 8.3 → 7.3；AMBER Hal 24.6 → 17.3 |
| 别人对老方法的复测（Revis Table 3/16） | Qwen2.5-VL-7B | CHAIR 512、greedy、100 图 | Regular 31.0；VCD 34.0；M3ID 31.0；ONLY 33.0；AGLA 29.0（Table 16 记 32.0，两表不一致）；VTI 35.0 |
| 别人对老方法的复测（REVERSE Table 1） | Qwen2.5-VL-3B（微调版） | CHAIR-MSCOCO；AMBER-G | DoLA：CHAIRs 45.8 → 47.6；AMBER CHAIR 7.7 → 9.7 |

主查已读、此处不重复：Dual-Pathway 2605.13156（Qwen3-VL、InternVL、Llama-3.2）、SSL 2505.16146（Llama-3.2）。

名单之外但晚于 Vicuna 一代的模型上有数字的：VAR（Qwen2-VL-7B CS 30.5→30.1；InternVL2-8B 32.4→31.8）；SPARC（Qwen2-VL CLAIR 78.34→79.70）；TARAC（Qwen2-VL、InternVL2，AMBER）；HAVAE（Qwen2-VL CS 27.6→22.8）；HIME（Qwen2-VL 20.8→17.2）；OSGA（Qwen2-VL-7B）；NoLan（Qwen2-VL 2B/7B）；ILVAD / SID / VHR / CAAC / SPIN / Revis / ProjectAway（LLaVA-NeXT）；DMAS（Mantis、Idefics3）；ViPSy（mPLUG-Owl3、Kimi-VL）；Yang（Chameleon-30B、LLaVA-v1.6-34B）。

在我读到的正文里**没有**任何修法报数字的名单内模型：Gemma3、LLaVA-OneVision、InternVL2.5（本文件 F 级 41 篇范围内；未就此单独发查询）。Pixtral 只有 QK Product Steering 一篇，Llama-3.2-Vision 只有 Yang 的 AD-HH 一行（另加主查已读的两篇）。

**只在 Vicuna / LLaMA-2 / Qwen-7B 一代（LLaVA-1.5、MiniGPT-4、InstructBLIP、Shikra、mPLUG-Owl2、Qwen-VL(-Chat)）上测过的方法**（按我读到的正文）：VCD、OPERA、DeCo、HALC、M3ID、ICD、AGLA（另 MiniCPM-V 2.4B）、PAI、Devils、FarSight（另两个视频模型）、Nullu、Per-Instance Subspaces 2608.09344、VTI、VISTA、ASD、MESA、SteerVLM、CCA、EOS、RLHF-V（Muffin）、TF-HH、HALVA（另 VILA-v1.5-13B）。HA-DPO、LLaVA-RLHF 未读正文，不下结论。

---

## "收益不稳或有损伤"的逐条证据

每条：谁测的（表号）｜对象方法｜现象。全部来自 F 级正文；跨论文基线不同，只在同一张表内比较。

### A. 换成 greedy 基线后，对比解码在 POPE 上的增益消失或变负
1. ASD Table 1（LLaVA1.5-7B，POPE MSCOCO）：VCD 在 greedy 下 85.13→85.16，在 direct sampling 下 81.49→85.41。
2. SID Table 1（LLaVA-1.5 7B，POPE random）：greedy 下 Normal 88.8 → VCD 87.8、ICD 87.9；去掉 APC 后 sampling 下 VCD 83.3 < Normal 84.9。
3. VCD 自己的 Table 7：greedy 下 87.10→88.49，Top-K+temp1.5 下 79.28→86.97。
4. Revis Table 5（LLaVA-1.5，greedy）：VCD POPE-random Acc 87.67→86.97；M3ID 与基线逐数相同。Table 3（Qwen2.5-VL-7B）：VCD 89.27→89.60，M3ID 相同。
5. VHR Table 2（POPE 平均 F1）：VCD 在 InstructBLIP / LLaVA-1.5 / LLaVA-NeXT 上 84.67 / 84.41 / 88.11，均低于 greedy 的 85.36 / 84.98 / 88.51。
6. Mirage 2504.10020（主查已读）的摘要结论与以上一致。

### B. 长描述（max new tokens 512）下，对比解码类的 CHAIR 不降反升
1. DeCo Table 2（nucleus）：VCD InstructBLIP 54.6→58.0、MiniGPT-4 32.6→33.8、LLaVA-1.5 48.8→54.0。
2. Devils Table 2（greedy）：VCD LLaVA-1.5-7B 53.0→58.6、MiniGPT-4 31.8→41.4。
3. VHR Table 1（5 个划分）：VCD 三个模型都高于 greedy（50.72 / 51.92 / 30.80 对 45.32 / 49.68 / 29.08）。
4. CAAC Table 1：LLaVA-1.5 基线 55.2 → VCD 57.8、AvisC 60.4、M3ID 56.2；InstructBLIP 55.6 → 60.8 / 71.0 / 72.8；LLaVA-NeXT 33 → VCD 41.6、M3ID 42。
5. VISTA Table 1：VCD LLaVA-1.5 greedy 46.4→47.4、nucleus 53.2→60.8；InstructBLIP greedy 38.0→45.8；OPERA InstructBLIP beam 37.8→50.2。
6. MESA Table 1（1000 图）：VCD 48.80→56.30；ICD 48.80→59.50。
7. AllPath Table 1：VCD 52.2→58.2。SPARC Table 13：VCD 53.96→57.92、OPERA 53.96→55.68。TARAC TABLE I：VCD 45.4→55.2、DoLa(high) 58.2。Yang Table 1（128 tokens）：VCD 51.8→55.4、DoLA 53.8。
8. Revis Table 16（Qwen2.5-VL-7B）：64 tokens 时 VCD / M3ID / ONLY / AGLA / VTI 都低于基线 14.0；512 tokens 时 VCD 34、ONLY 33、AGLA 32、VTI 35，都不低于基线 31。
9. ILVAD Table 1（LLaVA-1.5-7B，greedy，512）：VCD 48.4、CODE 48.2、SPARC 48.9、ONLY 47.8 与 greedy 48.6 相差不到 1 点；VAF 49.8、VAR 52.5 高于 greedy。

### C. CHAIR 降了，但 recall / coverage / 长度 / F1 同时掉
1. PAI：SPARC Table 13 Recall 79.46→72.44、F1 81.99→80.52；AllPath Table 5（Qwen-VL-Chat）CHAIR 43.4→17.2 而 F1 76.4→70.1、Len 98.1→36.8。
2. VISTA：HAVAE Table 1（LLaVA-1.5-7B）CHAIR_S 15.6 而 F1 76.4→67.3。
3. TARAC（自报）：LLaVA-1.5 Recall 77.5→72.0、Len 89.09→83.24；Qwen2-VL AMBER Cover 67.0→53.3。
4. Devils（自报 Table 12）：α 从 0.5 到 0.6，LLaVA-1.5-7B CHAIR_S 25.0→1.0、F1 76.1→49.3。
5. SPIN（自报）：α=0.01 档 F1 77.8→74.6；Qwen2.5-VL-7B F1 75.7→74.0；GPT-4o Detailedness 6.83→6.12。
6. VTI：MESA Table 1 Len 98.70→80.30；自报 Len 102.2→93.8。
7. EOS：HALVA Table 1 Len 100.6→79.7。REVERSE 激进档 Cover 51.0→26.9。DeCo（自报）AMBER Cover 48.9→47.5。OPERA：VHR Table 1 Len 83.06→75.88（LLaVA-1.5）。HIME（自报）Qwen3-VL BLEU 9.81→8.89。
8. HAVAE（自报）：Shikra F1 75.4→71.8；"Max Attention" 选头 CHAIR_S 7.8、F1 65.8。
9. MESA 作者对 VTI / Nullu 类的总评（逐字）："they lead to shorter outputs and systematically shifted token distributions in generative scenarios"。主查已读的 2609.01888 讨论同一问题。

### D. 一般能力受损
1. VTI：Revis Table 4（Qwen2.5-VL-7B）MME 2327.52→2083.82、MM-Vet 70.18→56.38。
2. VCD：SID Table 5 MME 1510.8→1488.5、MMBench 64.4→63.8；ASD Table 3 TextVQA −1.50；CCA Table 5 SEED_I 66.1→63.7、TextVQA 58.2→54.4；FarSight Table 2 VizWiz 48.5→43.4；Revis Table 4（Qwen2.5-VL-7B）MME 2327.52→2258.86；HALVA Table 2 MME-Hall 648.3→604.7；Yang Table 2 MM-Vet 31.4→29.4。
3. ICD、DoLa：SID Table 5 MME 1473.2、1480.7（greedy 1510.8）。
4. 训练类：HALVA Table 2 MME-Hall：HA-DPO 618.3、EOS 606.7（基线 648.3）。RLHF-V（自报）LLaVA Bench Comp. 97.7→91.6。
5. QK Product Steering（自报 Table 9）：加大强度后 MMMU 51.56→43.78。Pixtral 默认档 MMMU 45.44→43.11。
6. SPIN（自报）：Qwen2.5-VL-7B MME 认知 590.7→552.5。ASD（自报）：Qwen-VL-Chat MME −14.35。DeCo（自报）：Qwen-VL MM-Vet Rec / Know / Gen 下降。
7. Devils：HAVAE Table 1（LLaVA-1.5-13B）POPE Acc 82.6→71.4。
8. 朴素转向：SteerVLM Table 1 CAA 使 POPE Overall Acc 84.5→56.2。

### E. 换模型后增益缩小或消失
1. VAR（自报 Table 2）：LLaVA-1.5-7B CS −1.8，Qwen2-VL-7B −0.4，InternVL2-8B −0.6。
2. QK Product Steering（自报）：Qwen2.5-VL −2.88；InternVL3 −0.58；Pixtral −0.33（CI 含零），后两者与随机对照不可分。
3. TARAC（自报）：InternVL2 AMBER CHAIR 8.5→8.5。
4. Revis（自报）：InternVL3 POPE Acc 90.54→90.24；Qwen3-VL 64 tokens CS 8→8。
5. ILVAD（自报）：LLaVA-1.5 CS −16.0；Qwen2.5-VL −3.0；Qwen3-VL −6.4（基线 51.6）。POPE Acc 在 Qwen3-VL / InternVL3 上 +0.61 / +0.15。
6. SPARC（自报）：CLAIR LLaVA-1.5 +5.13，Qwen2-VL +1.36。
7. Nullu：MESA Table 2（Qwen-VL，POPE 一个数据源）Acc 74.73 对 Vanilla 74.76。
8. AllPath（自报）：Qwen2.5-VL-72B adversarial +0.1。Yang（自报）：Chameleon-30B CHAIR_I 12.6→12.5。
9. REVERSE（自报）：Qwen2.5-VL-3B AMBER CHAIR 7.7→7.5。

### F. 换任务格式（生成 ↔ 是非题 / 选择题）不迁移
1. AD-HH：AllPath Table 1/6，POPE 上与 Vanilla 相差 ≤0.1（CHAIR 上有效）。
2. EOS（自认）：MME / POPE 无增益。REVERSE（自认）："it does not improve performance on discriminative VQA tasks"。OSGA（自认）：Yes/No 题增益有限且易过拟合成恒答 yes 或 no。OPERA（自认）：短回答（<10 tokens）增益很小。
3. PAI：AllPath Table 5（Qwen-VL-Chat）MCQ-POPE random Acc 61.8→57.9。
4. HALVA 作者认为 POPE 不适合做主基准（见 6.2）。

### G. 采样解码下失效
1. SPIN（自认 + Table 11）：MiniGPT-4 nucleus CHAIR_I 11.8→12.5、F1 66.4→62.9。
2. 反方向：A 节的几条说明"基线用 sampling"会放大对比解码的表观增益。

### H. 多轮 / 交互
1. VISTA（自认）："the current implementation focuses on addressing hallucination in single-round tasks"。
2. PAI Table 2、SPIN Table 10/13 报了 multi-turn POPE；其余方法在我读到的正文里没有多轮评测。

### I. 超参数敏感 / 每模型每任务重调
PAI（γ）、Devils（α 0.5→0.6 塌缩）、VAR（ρ 按任务类型三个值）、SPIN（每模型两组层 / r / α）、VTI（α、β 网格搜索）、VISTA（自认 "optimal settings may vary across different architectures"）、QK（k 按模型用小规模 CHAIR 扫描选）、REVERSE（τ 按骨干设）、ASD（最优 λ 随数据集变）、TARAC（自认固定超参是局限）。

### J. 评测口径本身的差异（不是方法失败，但影响读数）
- LLaVA-1.5 greedy CHAIR_S 基线：20.40（Nullu / HIME，64 tokens）、44.4（SPIN）、45.0（OPERA / DeCo，512）、46.2（CCA）、48.6（ILVAD）、49.68±1.47（VHR，5 划分）、51.8（Yang，128 tokens）、52.2（AllPath）、53.0（Devils）、54.0（Revis，100 图）、55.2（CAAC）。
- 图数：100（Revis）、500（多数）、3×500（ILVAD）、5 划分（VHR）、1000（MESA、QK）、4,946（QK 的 Pixtral）。
- 报不报 recall / 长度：报的有 VTI、CCA、SPARC、TARAC、VHR、ILVAD、MESA、ASD、AllPath（附录）、SPIN / HAVAE / Devils（F1）；VCD、OPERA、DeCo、PAI 主表、VISTA、Nullu（只 BLEU）、DMAS、Revis 不报。
- 随机对照：有随机头 / 随机模式对照的只有 VAR（Fig. 9）、Yang（Fig. 6、Table 5）、QK Product Steering（Table 2/5）；转向类七篇都没有随机方向对照；Nullu 只比了投影范数。

---

## 检索日志

**查询（Web 检索共 2 条；上限 40 条没有用完，原因见"没做到的"）**
1. `"Activation Steering Decoding" hallucination large vision-language models ACL 2025 arXiv` → 命中 ACL Anthology 2025.acl-long.634；未见 arXiv 版。
2. `hallucination mitigation fine-tuning preference optimization Qwen2.5-VL InternVL3 LLaVA-OneVision CHAIR AMBER 2025 2026 DPO object hallucination` → 命中 ViPSy 2606.28401（已取正文）、CHAIR-DPO、SymMPO、HSA-DPO、TPO（未取正文）。

其余全部是对缓存正文的定点检索（正则 + 按表号读行），未计入查询数。

**新下载正文 15 篇**：2311.16922、2403.00425、2408.02032、2410.11779、2406.12718、2403.18715、2602.18711、2510.26769、2311.16839、2312.00849、2405.18654、2504.13169、2402.14545、2606.28401、ACL 2025.acl-long.634（存为 asd_acl25.txt）。

**F（读了方法、设定、主表、对照、局限；21 篇）**：2311.16922 VCD、2311.17911 OPERA、2410.11779 DeCo、2408.02032 SID、2407.21771 PAI、2503.03321 VAR、2605.20965 ILVAD、2502.01419 SPARC、Yang ICLR 2025（yang_iclr25）、2505.16411 SPIN、2412.13949 VHR、2511.17254 AllPath、2412.13817 Nullu、2606.20419 QK Product Steering、2602.11824 Revis、2410.15778 VTI、2502.03628 VISTA、2602.21704 DMAS、2504.13169 REVERSE、2405.18654 HALVA、2410.15926 CCA。

**F（定点：只核对了引用到的表与局限段；20 篇）**：2403.00425 HALC、2403.14003 M3ID、2403.18715 ICD、2406.12718 AGLA、2602.22144 NoLan、2411.16724 Devils、2504.04099 TARAC、2505.21472 CAAC、2505.16652 FarSight、2605.10622 HAVAE、2602.18711 HIME、2608.09344、2410.02762 ProjectAway、2604.07914 MESA、2601.23041 OSGA、2510.26769 SteerVLM、ACL 2025.acl-long.634 ASD、2606.28401 ViPSy、2402.14545 EOS、2312.00849 RLHF-V。

**A（取到正文但只读了摘要或表目录；3 篇）**：2504.10020 Mirage（主查已读，我只核了摘要引文）、2412.06775 Delve into VCD、2311.16839 HA-DPO。

**S（只在别人表里或检索摘要里见）**：DoLa、LLaVA-RLHF 2309.14525、CODE、ONLY、VAF、ICT、AvisC、MEMVR、Woodpecker、LURE、VDD、DAMRO、Volcano、OPA-DPO、CHAIR-DPO、SymMPO、HSA-DPO、TPO 2412.14487。

**没做到的 / 边界**
- 2025–2026 解码类后继只读了 NoLan 一篇；CODE、ONLY、VAF、ICT、MEMVR 等只有别人表里的数。没有为"各组 2025–2026 后继"系统发查询（只发了 2 条），这一块是缺口。
- 发表处多数凭记忆或版式推断，文中逐条标了"为记忆 / 未核对"；arXiv 号以缓存文件名为准。
- max new tokens 未检到的：VCD（无 CHAIR 主表）、DeCo、VAR、FarSight、SPIN、DMAS、ASD。种子数多数论文未报。
- 逐字引文二次核对：写完后用脚本（sub_a_scripts/qcheck.py，去空白与连字符后做子串匹配）复核了 42 条引文，36 条命中。未命中的 6 条都是双栏 PDF 里句子被另一栏或脚注文字隔断，我按栏切开后人工读出并拼接，**不是整句字符串匹配**，引用前建议对 PDF 原文再看一眼：VCD 的 Limitation 句（中间隔着脚注）、Revis 的 Limitations 句（隔着参考文献栏）、ASD 的 Limitations 句、EOS 的两句（附录左栏）、AGLA 的 "It will be useful to evaluate…" 句。其余没进复核清单的短引文（少于一句的片段）同样来自 pdftotext 文本，断行连字符已合并（如 "R EVIS" → "REVIS"），弯引号可能与原文字符不同。
- 没覆盖：在审稿件、OpenReview 评审意见、非 arXiv 的会议补充材料、代码仓库实际可用性（URL 只来自正文，未访问）、闭源模型。
- Revis Table 3 与 Table 16 对 AGLA 在 Qwen2.5-VL 512 tokens 的 CHAIR_S 分别记 29.00 与 32.0，原文自身不一致，两个数都保留。
- QK Product Steering Table 2 与 Table 9 对默认档 MME 分别记 2293.3 与 2344.4，原文自身不一致。

**环境事故（需知会）**：16:33 前后 /tmp 写入报 EDQUOT，我的两个脚本被写成 0 字节（ex2.py、tab.py，仍留在 sub_a_scripts/，改用 ex3.py、tb.py）。为腾空间，我删除了自己本次用 fetch.sh 下载的 13 个 PDF（对应 .txt 都保留）：2311.16922、2403.00425、2408.02032、2410.11779、2406.12718、2403.18715、2602.18711、2510.26769、2311.16839、2312.00849、2405.18654、2504.13169、2402.14545。没有动别人的文件。后两篇（ASD、ViPSy）的 PDF 下到 /dev/shm 转完文本即删。

