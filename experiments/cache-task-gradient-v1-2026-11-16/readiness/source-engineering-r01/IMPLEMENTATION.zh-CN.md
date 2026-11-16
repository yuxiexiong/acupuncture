# TGA-01 / A023 实现合同与作者自查

2026-11-16。来源提交9a0bc01db；承接[已审最小任务梯度卡](../cache-numerator-gate-use-v1-2026-11-16/analysis/asymmetry-r01/MINIMAL_MEASUREMENT.zh-CN.md)。最新用户已明确授权实现、测试后GPU工程/正式、按设计修复bug和结果Advisor讨论；如果一阶预测失败不自动追加。原方案“未授权”是当时身份，不覆盖本轮新授权。

## 实现及不改变的科学合同

- 复用WSB/DWB形成、C/H混合、原ΔH与t1实际J；复用NGU正式48接收者/168 AL/BD冲突对、原输出映射/完整t2 logits、RCS原生11 norm端点与NGU native/patch原件。工程仍六场景首接收者20对。
- `tg_hooks.py`仅在G14 gated norm输出添加FP64叶子控制，再cast原输出dtype。native.double不detach；后续所有原生算子及更新保持。零控制必须逐位桥接原11；冻结P=patch_X−native_X必须逐位桥接原X的每层native/patch和最终完整logits。
- `tg_run.py`绕过原V.fwd的inference_mode包装，仅t2调用同一V.L.forward并打开图；形成/t1继续旧路径。权重requires_grad=False、无优化器。历史cache在inference_mode外deepcopy转普通独立张量；原件/兄弟分支hash检查。
- 源码检查发现cache.copy_可能覆盖backward保存的输入。采用PyTorch已安装的`allow_mutation_on_saved_tensors`同时覆盖forward/backward：仅在保存值遭修改时留副本，不改forward算子、cache更新、dtype或图依赖。CPU需对同一冻结kernel在有/无cache.copy_条件验证输出及梯度相等。若真实kernel不支持backward、仍断图或端点不同则工程停止；不替换kernel或模型精度。本项是待Advisor核对的实现处理，不冒称旧模型实验已验收。
- 同一t2 logits的D−Y对14控制求VJP，保存原FP64梯度；每个后续norm检查native.requires_grad，autograd.grad拒绝unused梯度，梯度有限，权重grad始终None。
- `tg_analysis.py`固定原P符号、receiver等权、全部误差及sign资格覆盖；C/H各自通过MAE≤.25、≤零预测50%、|bias|≤.10、80%receiver MAE≤.5、合格sign≥.8才允许解释cross。不拟合、不加样、不按结果选层，完整回答结果沿原NGU不新增。

## 记录、失败与预算

每pair背景保存实际t1 snapshot、原生/frozen候选与停止logits、完整logits SHA、flow、源record引用、逐层内积和原FP64梯度。桥接失败前先保存已获得的raw端点；失败现场保存当前norm native/patch、flow、t1记录/状态及已获梯度，原始失败不覆盖。

所有本轮代码、设计、旧输入文件/包与环境代码绑定SHA；复用上轮NGU冻结来源，但重新核当前文件与环境。原始权重不入Git；新梯度按hash/size清单留服务器，JSON原值/回执/源快照交付。

复用NGU已审授权/历史尝试/来源检查函数，在本进程明确设置本轮HERE/CAP/TOTAL_CAP/STORAGE；不会改写旧模块文件。监督器独立计时/存储硬停、单worker锁、指定空闲GPU；不占用已有任务、不排队。每次前向执行前检查本stage模型调用上限，backward前检查上限；所有失败尝试计费。

固定上限：工程最多2次，各900秒；正式最多1次5400秒；总7200秒、新输出2GiB。正式96形成＋48前缀、336 t1、336 native t2/backward、336 frozen t2；含两工程≤4668 forward/416 backward、0自然回答。计数与原ledger核对。预算外推按最慢前缀token/形成token、形成开销、完整pair时间（含forward/backward/桥接/IO）等×正式单位数×1.25；不得以工程校准是否阳性决定正式启动，正式只依赖数值/来源/图/预算验收。

## 作者C01–C14及反方检查

|项|复查结论|
|---|---|
|C01|通过：原换门不对称的一阶任务预测，未换题。|
|C02|通过：能无拟合预测或撤回近似，非仅梯度存在。|
|C03|通过：旧代码/包/端点/评分全复用；来源重新核。|
|C04|通过：保留舍入/非线性/小C效果的失败可能。|
|C05|通过：G14/t2/FP64控制、P原件、固定面板与原dtype不变。|
|C06|通过：native不detach；缓存副本与保存张量副本不截断t2图。真实梯度待工程。|
|C07|通过：人工加数端点路径，非NGU自适应政策导数。|
|C08|通过：surrogate及条件cross，无层份额/自然中介/完整回答恢复主张。|
|C09|通过：幅度/方向/任务映射区分沿原卡，任一背景失败不拿cross作解释。|
|C10|通过：D−Y signed误差主检验，非范数或相关性替代。|
|C11|通过：实现桥接/图失败与科学预测失败独立；后者不视bug自动修假设。|
|C12|通过：参考桥接/形成/失败计费，无新答案/模型/剂量。|
|C13|通过：逐pair/receiver/场景保留，SHA/旧面板身份明确。|
|C14|通过：近似失败退出，不自动积分或扩大；当前用户授权仅本轮。|

相关历史错误E03/04/09/17/18/22/23/25沿原卡处理；实现重点防多tap detach、总漂移重复计数、梯度与score错位、失败不留现场及source版本漂移。其余历史项无新增科学操作，沿已审卡边界。

反方：保存张量副本可能被误称换模型。对策：同kernel有/无原位覆盖的CPU梯度对照、GPU逐位端点桥接、全部原源码hash不变；若端点/梯度图无法保持则停止，不以“数值差小”放宽。另反例为两均值接近而逐样本错：固定MAE、receiver/sign和零预测比较不变。

作者逻辑/代码自查完成；初步本地小张量5项通过、1项真实上游待服务器。CPU完整验收及GPU端点/图/预算尚未完成。独立Advisor实现审查随后记录。
