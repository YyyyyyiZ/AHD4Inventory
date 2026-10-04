# 参数数量上限消融：旧轮与新轮

状态：**incomplete**；完成 0/72 个比较窗口。

旧轮测试结果已经查看，本轮是随后开展的参数数量限制消融／探索比较；两轮复用同一测试集，不是新的未见留出验证，也不能仅凭差异作因果归因。

- 旧轮：/Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/correlated_inventory/20260916_stationary_priority
- 新轮：/Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/correlated_inventory/20260916_unrestricted_params

成本单位均为每期平均成本，越低越好。每轮分别在每条路径上平均全部三次独立生成，再按同一需求与交货期路径配对；不选测试最佳策略，也不把两轮 r1 当作配对的模型随机种子。

95% 区间重采样整条路径，仅反映需求路径抽样误差，不包含策略生成变异，也未作多重比较校正。生成间样本 SD 单列。改善率为 100×(对照−候选)/对照，正值有利于候选。

## 主比较：训练 H=200，评价 H=200，B=500

三次未齐时不显示部分重复的替代均值。三类 PIL 对照均要求两轮记录哈希及逐路径成本一致。

| 场景 | 旧/新重复数 | 旧成本 ± 生成 SD | 新成本 ± 生成 SD | 新比旧改善% [95% CI] | Conditional PIL 成本 | Adaptive PIL 成本 | PIL + COP 成本 |
|---|---:|---:|---:|---:|---:|---:|---:|
| exp_iid_fixed6 | 3/3 · 0/3 | 124.975 ± 1.134 | — ± — | — | — | — | — |
| exp_ar_pos08_fixed6 | 3/3 · 0/3 | 166.171 ± 2.459 | — ± — | — | — | — | — |
| exp_ar_neg06_fixed6 | 3/3 · 0/3 | 101.886 ± 3.105 | — ± — | — | — | — | — |
| exp_regime095_fixed6 | 3/3 · 0/3 | 152.560 ± 2.626 | — ± — | — | — | — | — |
| exp_iid_random3_9 | 3/3 · 0/3 | 139.946 ± 5.921 | — ± — | — | — | — | — |
| exp_regime095_random3_9 | 3/3 · 0/3 | 153.126 ± 2.323 | — ± — | — | — | — | — |

## 主窗口：分别与三类 PIL 比较

绝对成本差 = 本轮 self-evolve − PIL，单位为每期成本，负值有利于 self-evolve；相对改善率为正值时有利于 self-evolve。旧轮与新轮各自平均三次生成；所有区间仍只重采样相同的整条需求路径。

| 场景 | PIL family | 旧−PIL 成本差 [95% CI] | 旧改善% [95% CI] | 新−PIL 成本差 [95% CI] | 新改善% [95% CI] |
|---|---|---:|---:|---:|---:|
| exp_iid_fixed6 | Conditional PIL | — | — | — | — |
| exp_iid_fixed6 | Adaptive PIL | — | — | — | — |
| exp_iid_fixed6 | PIL + COP continuation | — | — | — | — |
| exp_ar_pos08_fixed6 | Conditional PIL | — | — | — | — |
| exp_ar_pos08_fixed6 | Adaptive PIL | — | — | — | — |
| exp_ar_pos08_fixed6 | PIL + COP continuation | — | — | — | — |
| exp_ar_neg06_fixed6 | Conditional PIL | — | — | — | — |
| exp_ar_neg06_fixed6 | Adaptive PIL | — | — | — | — |
| exp_ar_neg06_fixed6 | PIL + COP continuation | — | — | — | — |
| exp_regime095_fixed6 | Conditional PIL | — | — | — | — |
| exp_regime095_fixed6 | Adaptive PIL | — | — | — | — |
| exp_regime095_fixed6 | PIL + COP continuation | — | — | — | — |
| exp_iid_random3_9 | Conditional PIL | — | — | — | — |
| exp_iid_random3_9 | Adaptive PIL | — | — | — | — |
| exp_iid_random3_9 | PIL + COP continuation | — | — | — | — |
| exp_regime095_random3_9 | Conditional PIL | — | — | — | — |
| exp_regime095_random3_9 | Adaptive PIL | — | — | — | — |
| exp_regime095_random3_9 | PIL + COP continuation | — | — | — | — |

[主窗口三类 PIL 完整比较表](main_pil_comparisons.csv)。


## 全时域与冷暖启动

[全部窗口](all_windows.csv) 包括固定 H=200 策略在 H=50/100/200/500 的评价，以及 AR+ 的 H=50/100/500 单独重训扩展；source_training_horizon 明确区分两者。cold_start 为 B=0，steady 为 B=500。

[跨场景汇总](scenario_aggregates.csv) 同时报等权均值、中位数和完成/计划场景数，属于描述指标；未完成时只汇总完整配对场景，不外推至全部场景。[全部配对区间](paired_comparisons.csv) 使用相同路径。

## OPT_PARAM 数量

只数 OPT_PARAM 注释绑定的独立标量赋值；四个策略输入是观测状态，不算可优化参数。原始生成阶段按每个已保存的模型最终回复计数（包括同一候选的第二次请求），最终阶段每条链仅统计按训练目标选定的 policy.py。种子策略不混入模型生成分母。无法解析与未返回的回复单列，不能当作零参数。

| 轮次 | 范围 | 阶段 | 可计数/已观察 | 未返回 | 无法解析 | 最小/中位/最大 | >4 | 数量分布 |
|---|---|---|---:|---:|---:|---:|---:|---|
| old | primary | generated_response | 1853/1858 | 1 | 4 | 2/4.0/4 | 0 | {"2": 59, "3": 461, "4": 1333} |
| old | primary | final_training_selected | 18/18 | 0 | 0 | 3/4.0/4 | 0 | {"3": 2, "4": 16} |
| old | horizon_extension | generated_response | 909/913 | 4 | 0 | 2/4.0/4 | 0 | {"2": 1, "3": 412, "4": 496} |
| old | horizon_extension | final_training_selected | 9/9 | 0 | 0 | 4/4.0/4 | 0 | {"4": 9} |
| new | primary | generated_response | 1104/1110 | 4 | 2 | 1/3.0/7 | 160 | {"1": 1, "2": 57, "3": 663, "4": 223, "5": 108, "6": 49, "7": 3} |
| new | primary | final_training_selected | 9/9 | 0 | 0 | 3/3.0/6 | 2 | {"3": 5, "4": 2, "5": 1, "6": 1} |
| new | horizon_extension | generated_response | 0/0 | 0 | 0 | —/—/— | 0 | {} |
| new | horizon_extension | final_training_selected | 0/0 | 0 | 0 | —/—/— | 0 | {} |

完整明细：[参数计数](parameter_counts.csv)、[数据配对](dataset_pairing.csv)、[基线记录配对](baseline_pairing.csv)、[机器可读报告](parameter_comparison.json)。

除参数上限外，已观察搜索设置差异 0 条；读取或配对问题 0 条，详见 JSON。不完整或不一致的窗口不会生成比较区间。
