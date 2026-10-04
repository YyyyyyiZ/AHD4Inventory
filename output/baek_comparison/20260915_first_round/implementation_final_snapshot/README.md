# Baek 方法对照实验

本目录实现已批准的第一轮：L1 为三个核心场景各三次独立生成，L2 为三个需求类别各三次独立生成，共 18 次首试。模型为 `openai/gpt-5.6-sol`，推理强度为 `high`。问题适配与比较范围见仓库中的 `docs/baek_2026_comparison_proposal.md`。

目标为 L 个零需求备货期后的 50 期销售总成本。策略看到到货后的库存与长度 L−1 的在途订单；动作允许非负有限实数，无订货容量上限。策略必须确定且 stationary，即同一状态、同一固定参数给出同一动作。

模型费用总上限为 **30 美元，包括接口预检和每组至多一次无效补跑**。预算中断属于未完成，不能自动换模型或当作策略质量失败。导入模块、评分、统计、测试均不会调用模型；`generate` 与明确执行的无效补跑会调用付费 API。

## 运行条件

以下命令从仓库根目录运行，使用已经配置的 `.venv/bin/python`。实际 Python、NumPy、SciPy 与硬件版本记入 `manifest.json`。策略工具和评测使用 macOS `sandbox-exec`：策略无法联网、读取仓库需求数据或读取凭据，工具调用之间没有持久 Python 状态。

API 凭据仅由父运行器从仓库外的 `~/.config/ahd4inventory/openrouter_credentials.json` 读取，结构为包含 `api_key` 字段的 JSON。凭据不进入提示词、策略或运行日志。

```bash
BAEK_RUN=output/baek_comparison/20260915_first_round

# 合成轨迹、模拟接口以及实际本地隔离检查；没有模型请求。
.venv/bin/python -B -m unittest discover -s examples/inventory/baek_comparison -t . -p 'test_*.py'
```

## 复现顺序

### 1. 固定协议与对照

```bash
.venv/bin/python -B -m examples.inventory.baek_comparison.runner prepare --run-dir "$BAEK_RUN"
.venv/bin/python -B -m examples.inventory.baek_comparison.pipeline baselines --run-dir "$BAEK_RUN"
```

`prepare` 固定 18 个原始提示、场景、种子与数据文件哈希。它读取测试文件原始字节用于哈希，不把测试成本传给生成过程。`baselines` 仅在前 50 条训练路径上拟合三类经典策略，同时按保存的训练分数冻结历史 AHD 来源；历史方法的模型及搜索预算分别保留。已有冻结基线文件不会自动重拟合。

### 2. 生成第一轮策略

```bash
.venv/bin/python -B -m examples.inventory.baek_comparison.runner generate --run-dir "$BAEK_RUN" --workers 2
.venv/bin/python -B -m examples.inventory.baek_comparison.runner status --run-dir "$BAEK_RUN"
```

每会话最多 50 次 Python 工具调用、3600 秒累计 Python 执行；L1 每次模型请求最多 16384 输出 token，L2 最多 32768。会话可提前提交。Python 用时、模型 token 与费用分别记录。

`generate --only l1_poisson_r1` 可限定一个原始会话。已有 `result.json` 会被跳过；有未完成请求日志时程序停止并要求核对状态，不自动重发可能已经计费的请求。`status` 只读。

确认旧运行器已退出、已发模型请求都有完整回复及费用记录，或已按下述流程逐笔批准恢复后，可从原会话继续：

```bash
.venv/bin/python -B -m examples.inventory.baek_comparison.runner generate --run-dir "$BAEK_RUN" --workers 2 --resume
```

`--resume` 沿用原始提示、完整对话、已完成工具结果及累计预算；不会重发已有完整回复的模型请求，也不会重做已记录结果的工具调用。若有保留的工具进程，运行器等待恢复监视器将真实结果写回日志并把 `recovered_tool_pending.json` 标记为完成，再继续。没有完整回复且未获明确恢复授权的请求会阻止恢复。此操作继续原独立生成组，不增加尝试次数，也不使用 `retry_1`。基础设施错误会阻止排队或等待中的会话开始；已在执行的会话仍可在共享费用上限内继续。

#### 传输中断的显式恢复

传输失败且回复未知时，默认保留该请求的完整费用上界并阻止后续执行；`--resume` 本身不构成重新发送授权。需要先核对请求编号、原始完整对话、失败终态与日志前缀哈希，以及持久化的核账证据，再显式追加经验证的 `request_reconciled` 事件。工具调用次数、已消耗工具时间和模型请求编号继续累计，不能重置实验额度。

账户汇总可能延迟，不能将暂未观察到费用解释为实际零费用。`conservative_bound` 只批准继续原会话，费用仍未知，完整上界继续占用 30 美元总预算；只有具有明确实际费用证据的 `authoritative_cost` 才能替换该笔预留。其他未处理的请求继续阻止恢复和无效产物补跑。

操作前必须确认旧运行器已退出，由外部协调程序持有同一 `.runner.lock`。在证据验证后保留并归档原失败 `result.json`，再重开该会话；原日志采用追加记录，不能删除失败历史或直接覆盖终态。此流程是传输中断后的同一会话继续，不是策略无效的 `retry_1` 补跑，也不增加独立生成次数。

### 3. 合成验证与限定补跑

```bash
.venv/bin/python -B -m examples.inventory.baek_comparison.scoring validate-artifacts --run-dir "$BAEK_RUN" --source generated --workers 2
```

这一步只使用固定合成需求，检查接口、动作合法性和已实现的确定性/状态变化探针。L2 的一次尝试必须在其需求类别的**完整所需场景网格**通过验证，才能进入主结果。静态或动态核查标记本身不是确定的策略失败；这些检查也不构成数学上的 stationary 证明。

只有明确符合规则的无效产物可以使用一次同提示补跑。查询资格不调用模型：

```bash
.venv/bin/python -B -m examples.inventory.baek_comparison.retry_invalid --run-dir "$BAEK_RUN" --session-id l1_poisson_r1
```

对已经确认有资格的会话执行获批补跑，然后再次验证：

```bash
.venv/bin/python -B -m examples.inventory.baek_comparison.retry_invalid --run-dir "$BAEK_RUN" --session-id l1_poisson_r1 --execute
.venv/bin/python -B -m examples.inventory.baek_comparison.scoring validate-artifacts --run-dir "$BAEK_RUN" --source generated --session l1_poisson_r1
```

补跑使用逐字相同的冻结提示，不回传错误修复提示或测试成绩。原结果、源码、日志与验证保留；补跑写入 `sessions/<session_id>/retry_1/`。该位置无论成功失败最多使用一次。基础设施错误、待核查标记或有效但较差的成绩不触发此补跑。

**每组统一选择首次通过完整合成网格验证的尝试，选择不读取测试成本。** 如果 L2 原尝试在一个所需场景无效，不能在其他场景继续选用原尝试、只在失败场景改用补跑。未选原尝试的结果可保留为诊断，但不混入主结果。

### 4. 冻结后统一评分

```bash
.venv/bin/python -B -m examples.inventory.baek_comparison.pipeline score-classical --run-dir "$BAEK_RUN"
.venv/bin/python -B -m examples.inventory.baek_comparison.scoring score --run-dir "$BAEK_RUN" --source both --workers 2
```

评分使用相同场景顺序、需求路径、动作口径和计分定义，记录需求数组哈希。初始化目标为 30 秒，防卡死上限为 600 秒；默认每次策略调用上限为 1 秒，评测工作进程总上限为 1200 秒。超时和未通过结果单列，不静默改动作。

- `existing_test`：现有基准测试路径；它们曾用于历史研究评测。
- `fresh_test`：每场景 1000 条独立新需求路径。
- `integer_test`：现有路径上所有方法统一按 `np.rint`（ties-to-even）取整动作。
- `long_run`：仅三个核心场景，20 条各 10000 期路径，固定丢弃前 2000 期。总成本对应保留的 8000 期；报告同时列每期成本。这是有限长轨迹敏感性检查，没有证明达到稳态，也没有预先登记的分段收敛判据。
- `training_audit`：历史 AHD 额外重评前 50 条训练路径，核对保存的训练分数；不据此修改或重新优化源码。

`scoring --only <scenario_id>` 可以重复给出多个场景；`--session <session_id>` 可重复限定生成组，包含其补跑；`--source generated|historical|both` 控制来源。经典评分的 `pipeline score-classical --only <scenario_id>` 限定单个场景。已有评分默认保留；不使用 `--overwrite` 掩盖失败或替换已冻结实验。

### 5. 从保存的评分生成报告

```bash
.venv/bin/python -B -m examples.inventory.baek_comparison.report --run-dir "$BAEK_RUN" --n-bootstrap 5000
```

报告命令不执行策略、调参或调用模型。它仅按训练成绩选择每场景经典对照，使用完整路径的配对 bootstrap 比较成本。首次独立生成组 r1 与三个独立组各自成绩、均值、离散程度分别列出。补跑属于原生成组，不增加计划分母。

## 产物与阅读方式

所有新产物位于 `$BAEK_RUN`：

| 路径 | 内容 |
|---|---|
| `manifest.json` | 冻结协议、模型、种子、数据和提示哈希 |
| `sessions/<id>/prompt.txt` | 原始问题提示 |
| `sessions/<id>/events.jsonl`、`result.json`、`policy.py` | 模型调用、工具执行、用量和冻结源码 |
| `sessions/<id>/retry_1/` | 获批无效补跑及资格证据；原尝试保留 |
| `budget.json`、`billing_reconciliation.json` | 已计费/保守预留金额与额外费用核对（如有） |
| `baselines/<scenario>.json` | 训练拟合参数、训练分数、搜索范围诊断 |
| `historical_inventory.json` | 历史 AHD 候选、训练选择和源码来源 |
| `validation/<scenario>/` | 每次尝试在合成需求上的验证 |
| `scores/<scenario>/` | 逐路径成本、分项成本、需求哈希、有效性及计时 |
| `report.md` | 中文结果和比较限制 |
| `policy_design_all_draws.md` | 三次独立生成的订货规则结构与冻结源码链接 |
| `policy_design_comparison.md` | 第一组六份规则的详细解释 |
| `tables/draw_selection.csv` | 整组尝试资格、完整所需验证网格与主结果选择 |
| `tables/per_draw.csv` | 每个场景、尝试、数据批次的成本分项、满足率及状态；标明主结果或诊断 |
| `tables/paired_comparisons.csv` | 对经典基线/可用历史 AHD 的逐次配对区间和改进率 |
| `tables/repeat_summary.csv` | r1、三次成本、均值/标准差、首试失败与最终有效覆盖 |
| `tables/generation.csv`、`tables/references.csv` | 每次尝试资源和对照身份/训练选择依据 |
| `figures/*_improvement.svg` | 新测试集和现有测试集的独立矢量图；线段为生成范围，不是置信区间 |
| `figures/core_fresh_test_comparison.png`、`.svg` | 三个核心场景逐次改进与配对95%区间；区间不含生成变异 |
| `final_numerical_audit.json`、`final_results_audit.md` | 完成后的数值、覆盖、来源及统计复核 |

正改进率表示候选策略成本更低。跨场景先算每场景百分比，再报告等权平均和中位数；显著胜负和 0.1% / 1% 以内或更好的场景比例也单独报告。缺失历史对照不算 Baek 失败。经典策略的向量化评分没有测量逐动作耗时，不将占位零值解释为零运行时间。

本轮比较不同模型、预算及信息条件下的实际策略质量，不能单独归因于搜索框架。Baek 获得真实分布定义，而历史 AHD 主要依赖训练样本。无可靠最优解的场景不报告“最优性差距”。
