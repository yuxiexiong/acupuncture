# 准备与运行说明

本轮目前只允许准备与CPU验收。未给出正式运行授权；以下运行命令是供之后使用的说明，**本次不执行**。

## CPU准备

在本目录执行，均不加载成品模型：

```sh
python3 task_data.py verify
python3 -m unittest discover -s . -p 'test_*.py' -v
python3 experiment.py freeze
python3 experiment.py check
```

freeze只能在全部代码审查完成后生成一次，已有freeze不可覆盖。CPU测试中的微型合成网络用于检验真实钩子，不能称成品模型预检。

服务器现成解释器为`/workspace/acupuncture/.venv-bench/bin/python`。在相同仓库相对目录使用它执行测试及：

```sh
/workspace/acupuncture/.venv-bench/bin/python experiment.py check --tokenizer
```

该命令只读分词器、不读成品模型权重、不调用模型前向。前序`validate-parallel`通过原扩展核验；旧冻结依赖不得覆盖。如有哈希差异，先报告准确文件，再处理。

## 以后获得正式授权时

另存`launch-authorization-r01.json`，记录实际用户指令与时间，不预填授权。必要字段：`status=authorized`、本轮`experiment`、当前`freeze_sha256`、`candidate_ids=[C05,C01]`、`maximum_model_workers=2`、`user_instruction`、`granted_at`。准备授权或旧实验授权会在加载模型前拒绝。

确认两张卡空闲后，从两个独立终端启动；日志放在输出目录外，记录真实退出码。不启动别的实验或抢占其他作业。

```sh
/workspace/acupuncture/.venv-bench/bin/python experiment.py run --candidate C05 --device cuda:0 --output runs/r01-C05 --authorization launch-authorization-r01.json --execute
/workspace/acupuncture/.venv-bench/bin/python experiment.py run --candidate C01 --device cuda:1 --output runs/r01-C01 --authorization launch-authorization-r01.json --execute
```

输出目录必须不存在；没有resume。每卡开始时做一次恒等替换检验，然后完整跑256个变体。每个变体保存六条件、参考/当前输入身份、实际干预审计；失败留下原目录。

完成后分别核验：

```sh
/workspace/acupuncture/.venv-bench/bin/python experiment.py verify-run --output runs/r01-C05
/workspace/acupuncture/.venv-bench/bin/python experiment.py verify-run --output runs/r01-C01
```

要求两个进程正常退出、两个receipt completed、各256个逐题文件、各summary有效、模型权重与钩子检查通过。不要将本轮收据作为旧function-dev/confirm收据输入。后续解释、独立确认和其他模型实验另讨论。
