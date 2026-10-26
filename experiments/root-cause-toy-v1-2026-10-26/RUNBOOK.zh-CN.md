# 执行入口与交接

主定义见[执行合同](CONTRACT.zh-CN.md)，机器设置见[contract.json](contract.json)。没有启动授权文件，入口会在加载模型前退出。

## 准备阶段

在本目录运行 CPU 检查和冻结核验：

```sh
python -m unittest discover -p 'test_*.py' -v
python freeze.py verify
```

需要已有 PyTorch 的解释器。纯Python检查可以单独运行，但缺PyTorch而跳过的张量测试不算完整验收。本次本地CPU运行库为PyTorch 2.7.1；目标服务器为已固定的2.6.0+cu124，不能将本地通过冒充目标环境验证。

`check_ready.py --output <新收据路径>`只清点目标环境、权重哈希、分词对齐和GPU状态，不加载模型。它需要在已部署的新目录中运行；输出仅表示检查时刻可用，不占用或预留GPU。

## 获准后的运行顺序

每阶段使用新输出目录。`--prior`可重复。启动授权文件必须记录用户真实指令、授权时间、本实验名称和`status=authorized`；准备阶段不伪造该文件。

| 阶段 | 入口参数 | 必需的已完成收据 |
|---|---|---|
| 实际模型预检 | `--stage preflight` | 无；验证真实模型评分、梯度和修复钩子 |
| 拆针 | `--stage decompose` | preflight |
| 排名 | `--stage rank` | preflight、decompose |
| 有限候选真替换 | `--stage validate` | preflight、rank |
| 功能开发 | `--stage function-dev --explanations proposal.json` | preflight、validate |
| 新题确认 | `--stage confirm --explanations final.json` | preflight、validate、function-dev |

各模型阶段共同需要：

```sh
python run_root.py --stage <阶段> --execute \
  --launch-authorization <实际用户启动授权.json> \
  --model /data/models/Qwen3.5-4B-851bf6e --device cuda:0 \
  --output <新的阶段目录> --prior <前置阶段receipt.json>
```

这是参数说明，不是自动启动脚本。模型预检失败时不进入采集；失败目录完整保留。代码修复需另行冻结并从受影响的阶段重新开始，不能修改旧输出。

## 两处有意保留的研究决策

开发结果出来以前不能知道哪个候选有用、负责什么功能，所以程序不会自动编造结论。

`proposal.json`需包含：`family`（reading/comparison/reporting中选1），`validation_receipt_sha256`，以及1—2项`explanations`。每项写入已测试的`candidate_id`与`candidate_sha256`、`hypothesis`、`task_relation`、`expected_direction`、`falsifier`，以及未替换下游`reader`的组件和`positions=prompt_last`。开发提案不得预填投影。

功能开发只用clean开发输入学习预定内容分组`[1,1,-1,-1]`的均值差读数，记录来源哈希。这是内容相关读数，不自动命名功能；真实供体替换、任务终点、标签排列对照仍须一起看。

`function-dev`产生`explanations.frozen.json`。收据完成后，使用`freeze.py seal`将其绑定到该收据，生成新的最终确认输入。确认程序检查它与开发输出完全一致；不能在确认后修改位置、投影或任务族。

若没有候选通过或无法写出可检验的功能预测，本轮可以在开发验证结束，不需要凑足两条解释。只在答案尾部有效或没有下游读取位置的候选，按合同保留能力干预线索。

## 如何看结果

逐题JSON保留完整选项得分、实际来源针偏移、局部替换范数、输入哈希和钩子范围。`summary.json`报告配对效应；功能结果另按计算要求、两种答案标签排列和内容读数分别报告。汇总不会自动把“分数好看”标为找到根因。

确认集仅64题、功能确认仅16个基础对，区间可能较宽；这是允许的失败结论，不是继续加样本或筛除失败题的理由。真实模型预检和正式结果均不在准备完成收据内冒充已通过。
