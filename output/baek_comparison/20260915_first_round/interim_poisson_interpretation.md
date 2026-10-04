# Poisson L2 第一份策略：阶段性解读

**范围仅为 `l2_poisson_r1`：一次 LLM 生成的设计器，用于六个 Poisson 场景。** 它不是六次独立生成，也不是全部三次重复的最终成绩。以下数值来自已经冻结的评分记录；本次核查没有新增模型调用、仿真、调参或策略筛选。

## 核心场景：有小幅、可检出的成本改善

在 `poisson_L6_c1_2` 的 1000 条新需求路径上：

| 指标 | 数值 |
|---|---:|
| Baek 第一份 L2 策略的 50 期成本 | 743.5681 |
| 已选历史 AHD 策略的 50 期成本 | 747.0960 |
| 训练选定 capped-base-stock 的 50 期成本 | 747.1035 |
| 相对 AHD 的绝对成本降低 | 3.5279 / 50 期，即 0.07056 / 期 |
| 相对 AHD 的改进率 | **0.4722%** |
| 已保存的配对 95% bootstrap 改进率区间 | **0.2626%–0.6762%** |

逐路径原始成本的均值、改进率及需求哈希与报告一致。对应候选减对照的成本差区间为 −5.0421 至 −1.9615，方向与改进率一致。该区间描述需求路径抽样误差，不能说明不同 LLM 生成之间的稳定性。[Baek 评分](</Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/scores/poisson_L6_c1_2/baek_l2_poisson_r1.json>)；[历史 AHD 评分](</Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/scores/poisson_L6_c1_2/ahd_historical.json>)；[配对区间表](</Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/tables/paired_comparisons.csv>)。

改善伴随持有成本增加 15.9977、缺货成本减少 19.5255；需求满足率增加约 0.1953 个百分点。因此这份策略主要通过多持有一些库存降低缺货，获得净成本收益。

## 六场景平均：2.57% 的 AHD 差距需要结合经典对照理解

以下均为新需求上的相对成本改善，先逐场景计算，再等权平均。

| 场景 | 相对历史 AHD | 相对训练选定经典基线 |
|---|---:|---:|
| Poisson，L=2，p=2 | 5.9241% | 0.7591% |
| Poisson，L=2，p=5 | 0.3610% | 0.7279% |
| Poisson，L=4，p=2 | 2.2425% | 1.1015% |
| Poisson，L=4，p=5 | 5.1166% | 0.8760% |
| Poisson，L=6，p=2 | 0.4722% | 0.4732% |
| Poisson，L=6，p=5 | 1.2916% | 1.2854% |
| **六场景等权平均** | **2.5680%** | **0.8705%** |

六场景相对两种对照的已保存配对区间均支持成本降低，但它们共用一个设计器，不能当作六个独立生成重复。较大的 AHD 差距集中在 L=2、p=2 和 L=4、p=5：这两个场景中，经典基线本身已分别比历史 AHD 低约 5.20% 和 4.28%。因此，“比这批历史 AHD 平均好 2.57%”不等于“比强经典对照好 2.57%”。[逐场景配对表](</Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/tables/paired_comparisons.csv>)。

## 历史对照与策略结构的具体限制

六个 Poisson 场景最终选中的历史策略都来自 `deepseek-chat`，但搜索宽度和可用运行数不同；每场景候选运行数分别为 3、3、1、5、13、8。选择范围固定为非 old 目录、SciPy、m2、generation 10 的记录，不能将它称为全部历史版本、全部搜索配置上的最优 AHD。六个选中策略的训练重评分均与保存记录吻合，没有发现重评分口径不一致。[冻结的历史清单](</Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/historical_inventory.json>)。

核心场景的历史 AHD 策略，在当前整数库存轨迹上等价于目标库存位置约 689、订单上限 96 的 capped-base-stock；新训练经典基线的参数为 S=688.9879、cap=96.0007。两者测试成本几乎相同。因此核心场景的 0.47% 是相对于一个接近该经典策略族的强参考的细小改善。[经典训练参数](</Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/baselines/poisson_L6_c1_2.json>)。

这份 Baek 设计器投影订单到达前库存的均值和方差，并用固定随机种子的 **6000 条模拟路径**在初始化阶段选择参数；经典基线仅用 50 条既有训练路径。这是明确的信息与样本量差异，不能单独归因于搜索框架。代码还专门优化免费备货阶段的初始订单，采用仅依赖库存状态的识别规则，不使用时间计数器；50 期结果因此包含对启动状态的优化，当前结果不能分离这部分贡献。[冻结的 Baek 源码](</Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/sessions/l2_poisson_r1/policy.py>)。

## 长期与整数检查

核心场景的现有测试集改进为 0.3884%，统一整数动作改进为 0.4460%，方向与新需求一致。

固定长期检查中，20 条各 10000 期轨迹丢弃前 2000 期后：Baek 每期成本为 **14.95997**，AHD 为 **15.00799**，相对改善 **0.31996%**；已保存配对区间为 0.21254%–0.42500%。其原始总成本 119679.74 与 120063.90 对应各条轨迹保留的 **8000 期**，不能直接与 50 期成本比较。这仍是有限长轨迹敏感性检查，没有证明达到稳态。[长期原始评分](</Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/scores/poisson_L6_c1_2/baek_l2_poisson_r1.json>)。

**当前可支持的结论：第一份 Poisson L2 设计器在六个已评分场景都获得了小幅、可检出的经典基线改善；核心场景相对历史 AHD 改善约 0.47%。** 生成稳定性、其他需求类别和 L1 表现仍须等待其余预先计划的结果。报告中的 6/30 是场景覆盖，6/90 是 L2 场景策略覆盖，Poisson 独立生成仍只有 1/3；“三次均值”栏当前只有一份有效输出，不能解释为三次已完成的平均。
