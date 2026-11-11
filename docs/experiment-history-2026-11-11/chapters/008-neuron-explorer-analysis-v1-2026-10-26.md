# 008．三模型分析页与内部差分采集准备

[返回总时间线](../README.zh-CN.md)

**时间定位**：已提取运行收据的最早时间锚点（可含预检） 2026-10-26T21:49:28.922412+08:00；不能当作全部子运行起止。

**当时的目的与设计**

将十候选根因对照、迁移映射和19条件能力记录接入只读界面；准备4B clean/A/B/AB差分采集器，未采集时保持空态。

**实际过程、结果与后来更正**

此准备不等于真实轨迹采集。已有记录导出、界面和CPU检查与后续正式trace分开；原地图连接也不是本轮实测传播。详细准备收据、后续界面更新和缺项保留。

**来源身份**：`neuron-explorer-analysis-v1-2026-10-26`；本章主体来源提交 `7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8`。下方原文中的状态是各文件写作时的状态，不能把早期“尚未运行”覆盖后期正式收据，也不能将后期结果倒填进早期设计。


## 原设计、执行过程、结果与更正全文

以下按“设计与题目 → 工程/执行记录 → 结果/更正 → 其他历史说明”组织；同类内没有可靠时间时保留路径顺序，不冒充严格先后。正文未删段；仅为本章节重排标题层级、把相对链接指向固定提交。原始字节另外完整保存。

### 原件 1：三模型可视化分析：准备范围与验收

原路径：`experiments/neuron-explorer-analysis-v1-2026-10-26/PREPARATION.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/neuron-explorer-analysis-v1-2026-10-26/PREPARATION.zh-CN.md) · [单独阅读副本](../library/e9f908e03e0a4bb4.md)；SHA-256：`e9f908e03e0a4bb4e64c7a26dde4ab9f35daa25091acb0bd1421413aaa2ea08a`。

---

#### 三模型可视化分析：准备范围与验收

##### Material Passport

- Origin Skill / Mode：academic-research-suite / experiment-agent plan；ponytail用于最小实现，Sites用于本地页面验收。
- 日期：2026-10-26；版本：analysis-preparation-v1。
- 当前任务：用户同意现在开始准备，无需等待2B/9B全图。新增工作限于已有证据导出、只读界面、差分采集器及CPU检查。
- 新模型采集、根因追加诊断与跨模型机制确认均未启动；本准备不改变其他实验的暂停边界。

##### 三项交付

1. **已有根因对照。** 展示全部十候选、逐题六条件和已计算统计；正确率与连续分数分开。C01/C05是attention组件贡献，不标成MLP通道。修复线索与反向证据不足同时展示。
2. **跨模型比较。** 导入原迁移的映射、原生通道近似、19条件及四项能力面板。几何保留比例不是保留的功能比例；随机条件和缺失项保持可见。
3. **内部差分准备。** 4B固定输入的clean/A/B/AB采集器和真实trace导入视图。未采集时保持空态，不以示例数值或旧排名汇总伪造轨迹。AB−A−B+clean仅为同输入下的代数交互差分。

原Neuron Explorer三模型地图保留不动。分析页使用现有文件，运行在本地，浏览不会调用模型。来源路径、SHA-256、导出时间随数据保存；导出不是独立重跑原实验。

##### 实现与执行分界

现有RootEngine的干预、校准和组件采集为4B专用。新采集器首先复用该实现，并明确记录观察点、实际token、参考尺度和代码身份。无执行开关时只做准备校验，不加载模型；真实采集需要绑定当前输入、模型及新输出目录的后续授权记录，代码哈希随收据保存。本轮不生成执行授权。

新采集器不修改旧冻结源，不覆盖旧收据或原始回答。采集上限用于控制单次记录体积；超出上限明确拒绝，不能静默截断。记录前后需验证权重未改变、钩子移除、状态隔离与有限值。

2B/9B的机制采集和局部修复适配属于后续工作；已有三模型地图和映射不意味着这些检查已经完成。跨模型不同编号、坐标、层深和颜色不直接构成功能对应。新方法若使用旧测试结果开发，应另留确认材料。

##### 准备验收标准

- 导出值与已有机器记录一致，十候选和19条件完整，缺失/未操作不填成零。
- 页面可选择模型、任务、候选和条件；原始证据链接可用，未采集轨迹清楚标识。
- 无GPU的检查覆盖输入/身份校验、差分方向、零差分、条件一致性与失败保全；合成网络检查不称为Qwen实测。
- 只读服务仅开放页面和清单引用的原始记录，无模型执行按钮。
- 最终准备状态及未完成检查写入prepare-receipt.json；三模型原版完成状态仍以其独立收据为准。

##### 后续真实采集前需要固定

实际输入、观察位置、剂量、模型身份和执行资源；先完成真实模型的零干预/采集无影响/输入对齐检查，再记录耗时。这里不规定新的科学样本数、不改变旧判据，也不根据界面效果挑选成功题。

---

### 原件 2：Acupuncture 可视化探索

原路径：`experiments/neuron-explorer-analysis-v1-2026-10-26/README.zh-CN.md`。 [固定提交原文](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/neuron-explorer-analysis-v1-2026-10-26/README.zh-CN.md) · [单独阅读副本](../library/cbed72115e7f91e8.md)；SHA-256：`cbed72115e7f91e868f117524f0ab4702e5538400cb504f70944003b6f2d22b8`。

---

#### Acupuncture 可视化探索

双击本目录 `open.command`，或运行 `python3 serve.py` 后打开 http://127.0.0.1:8800/ 。首页为可点击的模型图，浏览不调用模型。原三维地图可从图中位置链接打开，也可用前一版本的 `open.command`。

- **全层调查（默认入口）**：切换2B/4B/9B和八道题，点击每层的实测通道，直接并排阅读原版与干预回答。金色标记表示该点有五档正剂量，可切换剂量或展开六栏；未测剂量留空。图色只表示空正文、自然结束和长度上限，不表示能力或功能区。上/下一层按钮方便沿深度浏览。
- **根因候选图**：4B 的32层 attention/MLP 图标出两针和十个候选；颜色取真实梯度修复预测，可按任务、题目和位置切换。点击候选查看实际修复/重现证据。颜色不是实时激活，图中不绘制未经验证的因果传播线。
- **跨规模对应图**：三模型按各自实际层数展示，虚线连接已有真实/随机源映射；显示原生通道投影的能量保留比例。几何对应不是功能等价。
- **已有根因对照**（证据详情页）：切换任务和十个候选，查看六条件正确率、连续分数、配对区间和逐题原始记录。未操作的答案位置单独标注。
- **跨模型比较**：切换2B/9B及真实/随机源，查看映射位置、几何误差、全部19条件诊断和独立的正式能力面板。随机源选择不会改变只对真实配方测过的正式面板。
- **内部差分**：尚无新采集数据。以后导入采集器生成的trace.json；文件只在当前浏览器解析，不上传。原地图缓存和修复排名不是激活轨迹。

`evidence.json`由既有记录导出，`evidence-manifest.json`保存793份来源及SHA-256。页面不是独立复现实验，也不把修复线索或跨模型损伤称为共同根因。

`survey-evidence.json`复用已完成的全层调查与五档正剂量结果：880个点、88个五档点、9,880份唯一回答（24份原版、7,040份+1、2,816份低剂量）。`survey-manifest.json`保存来源哈希及原文路径；不包含预检或尚未完成的负剂量实验。原始文字、特殊标记、token数和终止原因均保留。重新导出和核验只需运行 `python3 export_survey.py`、`python3 test_survey.py`，均不加载模型。

##### 差分采集准备

`capture_differences.py`先支持固定版本4B。它复用旧校准和两针实现，比较相同文本的clean/A/B/AB，记录每层attention、MLP贡献、层末残差的逐token差分摘要，以及选定通道的注入后读数。有限位置可另存完整向量。

仅准备、不加载模型：

```sh
python3 capture_differences.py --input capture-example.json --output runtime/example-prepared
```

输出目录必须不存在。示例文本只用于验证准备流程，不是新研究题集。真实采集需要另外明确输入和执行授权；本轮未运行。2B/9B的机制采集和修复适配也未执行。

准备范围与边界见`PREPARATION.zh-CN.md`；历史准备检查以`prepare-receipt.json`为准。关闭本地服务窗口会关闭此分析页连接；本页的静态浏览不依赖远程模型服务。

---


## 时间、运行与停止收据索引

下面是所收集JSON的原有时间字段与状态，不把预计结束时间当实际完成时间。未列时间的文件仍有原件链接。完整JSON全部保存在原文归档，不能以此索引中的标量代替完整嵌套内容。

| 原件 | 原记录状态/阶段 | 原时间字段（原时区） |
|---|---|---|
| [capture-cpu-receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/neuron-explorer-analysis-v1-2026-10-26/capture-cpu-receipt.json) | {"status": "passed"} | {"recorded_at": "2026-10-26T13:49:10.252414+00:00", "finished_at": "2026-10-26T13:51:17.036220+00:00"} |
| [graph-receipt-r01.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/neuron-explorer-analysis-v1-2026-10-26/graph-receipt-r01.json) | {"status": "passed", "scope": "Graph-first view of existing evidence; no new model runs"} | {"created_at": "2026-10-26T14:06:32.787426+00:00"} |
| [prepare-receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/neuron-explorer-analysis-v1-2026-10-26/prepare-receipt.json) | {"status": "preparation_passed", "scope": "existing-evidence viewer and 4B fixed-input trace collector preparation"} | {"created_at_utc": "2026-10-26T13:51:34.599411+00:00"} |
| [runtime/example-prepared/receipt.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/neuron-explorer-analysis-v1-2026-10-26/runtime/example-prepared/receipt.json) | {"status": "prepared"} | {"started_at": "2026-10-26T13:49:28.922412+00:00", "finished_at": "2026-10-26T13:49:28.922518+00:00"} |
| [survey-ui-receipt-r01.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/neuron-explorer-analysis-v1-2026-10-26/survey-ui-receipt-r01.json) | {"status": "completed", "scope": "Existing full-layer survey and positive five-dose answers displayed in the local evidence map", "new_model_inference": false} | {"verified_at": "2026-10-27T14:18:39.739497+00:00"} |
| [ui-verification.json](https://github.com/yuxiexiong/acupuncture/blob/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/neuron-explorer-analysis-v1-2026-10-26/ui-verification.json) | {"status": "passed"} | {"checked_at_utc": "2026-10-26T13:51:34.598634+00:00"} |

## 全部原始资产入口

本目录在固定提交下共有37个跟踪文件，包含代码、原回答、失败、收据和压缩证据；文件数不是样本数。[逐文件完整账本](../assets/008-neuron-explorer-analysis-v1-2026-10-26.tsv) · [原目录](https://github.com/yuxiexiong/acupuncture/tree/7d6bdf84ab74062ac9ab55bc8201b5a6586b92c8/experiments/neuron-explorer-analysis-v1-2026-10-26)。未复制模型权重、环境或凭据。
