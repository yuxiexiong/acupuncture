# E03：卷积状态清理方案

历史原件；不是本次提出的假设、论证或运行要求。

原路径：`experiments/cache-behavior-validation-v1-2026-10-30/e03-convolution/PLAN.zh-CN.md`。来源：[固定提交原件](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-behavior-validation-v1-2026-10-30/e03-convolution/PLAN.zh-CN.md)；SHA-256：`a9dcb32bf5b9cae58fe9be8ff915f88378322f34b7d87a024f5b2e02f5093bef`。精确字节见原文归档。

---

# E03：卷积状态清理方案

2026-10-30，draft-r01，未执行。[独立合同](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-behavior-validation-v1-2026-10-30/e03-convolution/CONTRACT.zh-CN.md) · [车队](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/cache-behavior-validation-v1-2026-10-30/PLAN.zh-CN.md)。

## 补哪个缺口

卷积清理能开口，但是否只是转为循环尚不清楚。

## 独立问题与设计

固定L0/C4146/−1，96个新基础情景、192输入。目标臂TTC/N、TTC/E，只清理全部线性层卷积状态；参照TTT/N、TTT/E及CCC/N、CCC/E。其余缓存不变。

主指标P为两个相反事实版本均正确的情景比例，D/S只辅助。H04：P(TTC/N)>P(TTT/N)；H05：P(TTC/E)>P(TTT/E)。

## 怎样结题

自然生成下改善支持行为恢复；在相同首步EOS解除后仍有实用改善，才支持超出首步停止的作用。主要减少循环/未交付时优先解释生成过程；明确事实错误转正确才支持任务层面的事实利用改善。只有D/S变化则不算能力恢复。

不论正、负或不确定均独立报告，不依赖其他实验显著。完整采集1152次生成；有确切匹配参照时新增384次；预检上限24次。当前不运行，不自动追加细层/剂量/模型扫描。
