# L0 跨通道验证｜CFM-CROSS-CHANNEL v1｜效应是否超出一般扰动，V 关系与 V 变化是否跨通道相似

- 设计：[跨通道验证方案 v2](../../docs/cache-cross-channel-validation-plan-v2-2026-10-31.zh-CN.md)（取代 v1）
- 合同：[CONTRACT.zh-CN.md](CONTRACT.zh-CN.md)
- 实现与决策日志：[IMPLEMENTATION.zh-CN.md](IMPLEMENTATION.zh-CN.md)
- 承接：[CFM-FORM-READ-BRIDGE v1](../cache-formation-readout-bridge-v1-2026-10-31/)（N4146 −1 每输入逐位锚定）

**结果与解释更新（2026-11-01）：** formal-r01全部闸门与每输入锚点通过。−1下十个原生通道及四条随机方向都复现V搬入强、换回只削弱部分的关系；量级和ΔV几何相似，说明当前现象不是N4146孤例，不是统计等效、任意方向有效或通道完全无特殊性的证明。SF组合机制尚未跨针检验。−0.5下通道分化但缺随机参照，作为边界保留，当前不默认转向剂量扫描。

[当前进展与推进计划](../../docs/cache-mechanism-progress-and-next-stage-plan-2026-11-01.zh-CN.md)：机制拆解为主，关键预测形成后用少量其他针眼和随机方向作阶段性检查。[固定结果](analysis/xchan-readouts-r01.json) · [完成核验](runs/formal-r01/verification.json)。实现日志保留执行时原表述，以本入口及当前计划作为最新解释。
