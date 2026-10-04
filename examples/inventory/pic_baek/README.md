# PIC instance 13 的 Jackie-style 实验

用户于 2026-09-23 授权使用 Excel 的实验设置和提供的 OpenRouter 凭据运行，随后明确批准扩展 Level 2 范围以覆盖 instance 13。

本目录独立于此前的非易腐库存实验。冻结协议、提示、源码、费用和逐路径结果保存在 `output/pic_baek/20260923_instance13/`。密钥存放在仓库外，不进入模型工具进程、提示或报告。

## 固定实验

- 使用 `openai/gpt-5.6-sol`、high 推理强度；无模型回退。保留服务端实际模型标识。
- 主结果：一次 L1、一次 L2。稳定性结果：另外十次 L2，按论文 §6.3 的“ten additional”解释。公开仓库的 RUNS.md 对总次数的描述不同，协议记录了该差异。
- 每个会话最多 50 次 Python 工具调用、累计 3600 秒。L1/L2 单次模型请求输出上限分别为 16384/32768 token。工具之间没有持久状态，只提供 Python 标准库、NumPy、SciPy。
- 初始化目标 30 秒，600 秒防卡死上限；分别记录初始化和策略评估用时。每个数值进程限制为一个数值计算线程。同时最多两个生成会话。
- 本轮没有另行指定美元上限，也不继承旧实验的 30 美元上限。运行器以约定会话数、工具计算和 token 上限控制范围，并记录真实收费。协议中的价格总上界是保守核账上界，不是预计花费。

## 模型和评估

状态初始化为 `(5,5,5,5,5)`。策略收到真实状态的 `np.rint` 结果，返回 0–10 的整数动作。成本和状态转移保留连续状态与连续需求，采购系数始终为 9.025。

Excel 提供的 200×1000 条需求只进入最终评估器。其 Float64 矩阵哈希以及原文件哈希记录在协议中。论文与公开代码的采购系数、轨迹数量和无限期目标的区别也保留在实验解释中。本轮采用用户 Excel 的 1000 期折现总成本，无预热和终端成本。

数据分工：

- Excel：最终固定测试集，需求种子 111–310。
- 验证集：同一需求分布，种子 41001–41200；仅用于从冻结产物中挑选交付候选。
- 独立测试集：种子 51001–51200，作为额外复核，不用于调参或挑选。
- 简单基线训练集：种子 61001–61200。固定订货量和 base-stock 基线独立调参，其成绩不回传生成模型。

每条路径先累加折现成本，再计算路径均值、样本标准误和自由度 199 的 Student-t 区间。生成随机性与需求抽样误差分别报告。没有认证最优值时不称为最优性差距。

Level 2 的参数范围见 `prompts.RANGES`：保留原协议共享的提前期 2–12、需求母均值不超过 50；把罚损上限扩展到 1000，并补充 PIC 特有的寿命、报废、积压、折现和截断正态参数。问题分布、动态和目标都是适配，不能声称原样复现 Jackie 的 Poisson lost-sales 问题。

## 执行

在仓库根目录使用现有 `.venv/bin/python`：

```text
python -B -m examples.inventory.pic_baek.experiment prepare
python -B -m unittest examples.inventory.pic_baek.test_environment -v
python -B -m examples.inventory.pic_baek.experiment baselines
python -B -m examples.inventory.pic_baek.experiment generate
python -B -m examples.inventory.pic_baek.experiment score
python -B -m examples.inventory.pic_baek.experiment report
python -B -m examples.inventory.pic_baek.finalize_report
python -B -m examples.inventory.pic_baek.final_audit
```

`generate` 是唯一发送付费模型请求的阶段。已有完成结果会跳过；未结束的日志需要 `--resume`，未经核对的收费不明请求阻止恢复。若以完整保留费用上限的方式继续，必须先保存故障证据、绑定原始对话哈希，并在报告中单列未知费用；历史调用和计算预算不重置。评分只能使用与冻结哈希一致的策略。结果差不会触发重跑。

`finish_when_ready` 可与生成进程同时运行，在每份策略冻结后自动评分；不发送模型请求。`finalize_report` 从保存的逐路径结果重新核算统计量、配对比较和 API 费用，输出中文 `实验报告.md`、`final_analysis.json` 与 `path_costs.csv`。默认要求所有计划会话结束；`--partial` 仅生成明确标注的阶段报告。初始实现快照保留在 `implementation/`，最终整理代码另存于 `final_implementation/`。

来源：

- Jackie Baek, *LLMs Can Design Near-Optimal OR Algorithms*, https://arxiv.org/html/2608.27296v1 ，§6.3、Appendix A、Appendix H。
- Pakiman 等, *Self-guided Approximate Linear Programs*, https://arxiv.org/pdf/2001.02798v2 ，§6。
- 用户 Excel 指定的公开仓库提交 `992d43d61f22317df2532cf67fb5547685bf394a`；相关源文件快照保存在本轮 `source/`。
