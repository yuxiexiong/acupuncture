# 收尾 CPU 复核脚本修正

2026-11-07。正式模型运行与冻结的 `dwb_analysis.py` 均已完成并通过。另写的收尾核对脚本第一次运行在 `A.row_out` 处报 `AttributeError`：`dwb_analysis` 中解析器通过其 `A` 模块引用，而非直接导出。调用改为 `A.A.row_out` 与 `A.A.bucket`。原脚本保留为 `audit-initial.py.txt`。

这是收尾作者核对脚本的引用错误；未写出 audit-r02.json，没有新增模型运行、重做冻结统计或修改科学判据。该脚本位于 postrun 子目录，不属于实验冻结输入。最终是否通过以 `audit-r02.json` 为准；此核对不是独立评审。
