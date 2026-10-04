# Nested-logit 方向核查：旧版 hard tail 不再成立

2026-09-16 夜间诊断。没有付费 LLM 调用，API 花费为 **$0**。

**结论：不要把 Baek 的 arXiv v1 nested-logit hard tail 当作反例。** 最新公开代码已修正每个 nest 的容量取整错误，原先的表现差距随之消失。本文核查没有发现可支持 AIPS 优势的 nested-logit instance。

## 为什么与 arXiv v1 不同

arXiv v1 将 nested logit 描述为主要例外，其 L2 平均收入低于最佳已知方法约 1.24%。[原论文](https://arxiv.org/html/2608.27296v1)

公开仓库的 2026 年 9 月修正说明指出：原 loader 使用 `round(n * cap_rate)`，而来源 benchmark 使用 `ceil(n * cap_rate)`。当 `n=25`、比例为 `0.1` 或 `0.5` 时，原实验分别只允许 2 或 12 个产品，正确限制是 3 或 13 个。这影响 971 个公开 instance 中的 233 个。L2 算法代码没有修改，只修正了输入容量与评分结果。[作者修正记录](https://anonymous.4open.science/r/llm-or-algorithms-F9F2/assortment/results/nl_cap_correction/README.md)

## 独立核查结果

比较口径为作者提供的 `best_existing.json`，不是把它称为精确最优值。公开日志有三个有效 Sol L2 draw；主重放预先按作者规则选择第一个有效 draw，没有按得分择优。

| 核查对象 | 数量 | 平均收入 / 最佳已知 | 最低比值 | 0.1% 内或更好 |
|---|---:|---:|---:|---:|
| 公开修正日志：第一个 draw | 971 | 1.0000060295 | 0.9999998703 | 971/971 |
| 公开修正日志：第二个 draw | 971 | 1.0000060295 | 0.9999998703 | 971/971 |
| 公开修正日志：第三个 draw | 971 | 1.0000060295 | 0.9999998703 | 971/971 |
| 本地完整重放：第一个 draw | 971 | 1.0000060295 | 0.9999998703 | 971/971 |

保存的 233 份修正决策全部通过独立的容量、二元决策与逐项标量收入检查；收入最大绝对误差为 `3.55e-15`。大于 1 的极小收入比值涉及最佳已知 comparator 与其记录精度，不能解释成超过精确最优值。

**完整本地重放已完成：971/971 决策均可行，全部与保存收入一致，最大绝对误差为 `3.55e-15`。** `replay.jsonl` 保留逐实例决策、收入与耗时；`replay_summary.json` 保留全部 48 个配置的结果。两名 worker 的逐实例计时合计约 609.5 秒，这不是并行运行的实际墙钟总时长。

## 新生成的 80 个 instance

另外固定四个生成器：独立 lognormal、吸引力与价格负相关、产品分簇、nest 间异质性。每类 20 个种子，提前把前 10 个设为 discovery、后 10 个设为 holdout；没有根据 discovery 表现调整生成器或筛掉失败结果。

所有实例均为 2 个 nests、每 nest 20 个产品、每 nest 最多选择 10 个产品，`gamma` 从 `[0.15, 0.99]` 均匀抽样。每 nest 共 616,666 个可行子集，超过原始算法 400,000 个子集的穷举阈值，实际走其启发式分支。独立 oracle 枚举每 nest 的全部可行子集，通过有限集合的分式优化获得最优收入，并检查残差与标量收入。

| 生成器 | Discovery 数量 | Holdout 数量 | 达到精确最优（数值精度内） |
|---|---:|---:|---:|
| 独立 lognormal | 10 | 10 | 20/20 |
| 负相关 | 10 | 10 | 20/20 |
| 产品分簇 | 10 | 10 | 20/20 |
| Nest 间异质性 | 10 | 10 | 20/20 |

这 80 个实例也没有产生有效反例。这只排除了本轮四个生成器，不能推断所有 nested-logit instance 都容易。

## 文件与复现

所有文件位于 `examples/inventory/overnight_search/nested_diagnostic/`。

- `audit.py`：核查全部保存记录，并可完整重放原作者第一个有效 L2 程序。
- `saved_audit.json`：日志统计、233 份决策检查、运行环境与全部下载文件 SHA-256。
- `replay.jsonl`、`replay_summary.json`：全部本地重放结果及按配置汇总。
- `synthetic_probe.py`：固定的四类新实例生成器和精确 oracle。
- `synthetic_results.jsonl`、`synthetic_summary.json`：80 个新实例全部结果，包括每个实例的算法和 oracle 决策。
- `source/`：未修改的公开输入、日志、原始算法、许可文件和修正说明。

在仓库根目录运行：

```bash
.venv/bin/python examples/inventory/overnight_search/nested_diagnostic/audit.py --replay --workers 2
.venv/bin/python examples/inventory/overnight_search/nested_diagnostic/synthetic_probe.py
```

脚本可恢复已经完成的结果。数据固定到公开 [Assortment-Benchmark commit 06107bf](https://github.com/wch444/Assortment-Benchmark/tree/06107bffaed2d5faef30c73e36688deb67c4923e)。本地运行环境为 Python 3.14.3、NumPy 2.4.3；作者的修正重放环境不同，因此额外保留了逐实例收入重放误差，不能默认运行时间直接可比。

**归因边界：** 本目录没有训练、修改或评测 AIPS。精确 oracle 是诊断工具，其结果不能被标为“我们的方法成功”。本次有价值的结果是及时排除了一个由旧版本评测错误造成的方向，把预算留给库存扩展与 optimizer 的实际消融实验。
