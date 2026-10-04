# Baek 方法在 AHD4Inventory 的第一轮比较

报告生成时间：2026-09-16T03:24:33.242685+00:00。

## 结果状态与比较口径

计划 18 个独立首试会话；当前日志中 18 个会话已提交代码。已保存 99 个 Baek 场景策略的评测记录。生成完成不等于策略通过有效性检查。

整组首试合成验证：通过 18、确认无效 0、待完成或核查 0，计划分母为 18 个独立生成组。计入允许的补跑后，目前 18/18 组已有统一选定的合格尝试。

主要指标为 L 个零需求备货期之后的 50 期销售总成本；越低越好。L1 对三个核心场景分别生成策略，L2 的固定设计器用于同类别的全部场景。首次独立生成（draw 1）与全部三个独立生成的均值和离散程度分别报告；不按测试成绩挑选代表策略。

如果某组独立生成触发无效补跑，该组统一采用按尝试顺序首次通过全部所需场景合成验证的输出。L2 的一次尝试只要在所需网格任一场景无效，原尝试就不能与补跑结果逐场景拼接；完整合成验证缺失时暂不进入主结果。原始失败与每次尝试保留，repeat_summary.csv 的 n_first_attempt_invalid 单列首试无效数；补跑不增加独立生成的计划分母。

经典对照先在前 50 条训练路径上分别拟合 base-stock、constant-order、capped base-stock，再仅按训练成本选定每场景的对照。历史 AHD 也是按保存的训练分数选择，保留不同模型及搜索预算身份。改进率 = 100 ×（对照成本 − 候选成本）/ 对照成本；正值表示 Baek 成本更低。

## 三个核心场景：与我们的历史 AHD 直接比较

以下均为同一数据批次上的 50 期销售总成本，越低越好。经典成本来自训练选定的基线；历史 AHD 也按训练记录选择，可能来自不同模型和搜索预算。r1 是第一组独立生成，三次均值只包含整组资格通过且该场景有效的策略，括号列出有效数/计划数。相对 AHD 的改进率只使用通过相同需求路径核验的配对，括号列出配对数/计划数；缺失记为 —。

### 独立新需求测试集

| 场景 | 经典成本 | 我们的历史 AHD 成本 | L1 r1 | L1 三次均值 | L2 r1 | L2 三次均值 | L1 相对 AHD 改进 | L2 相对 AHD 改进 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| exponential_L6_c1_2 | 6127.97 | 6121.21 | 6109.18 | 6109.36 (3/3) | 6122.64 | 6113.89 (3/3) | 0.19% (3/3) | 0.12% (3/3) |
| normal_std30_L6_c1_2 | 2249.56 | 2243.11 | 2236.65 | 2237.68 (3/3) | 2235.72 | 2235.98 (3/3) | 0.24% (3/3) | 0.32% (3/3) |
| poisson_L6_c1_2 | 747.10 | 747.10 | 742.76 | 742.74 (3/3) | 743.57 | 743.36 (3/3) | 0.58% (3/3) | 0.50% (3/3) |

![核心场景独立新需求比较](/Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/figures/core_fresh_test_comparison.png)

圆点表示各次独立生成；线段表示对需求路径计算的配对 95% 区间；菱形表示三次生成的平均值。区间不包含生成之间的变异。

### 现有基准测试集

| 场景 | 经典成本 | 我们的历史 AHD 成本 | L1 r1 | L1 三次均值 | L2 r1 | L2 三次均值 | L1 相对 AHD 改进 | L2 相对 AHD 改进 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| exponential_L6_c1_2 | 6146.71 | 6148.78 | 6124.83 | 6124.90 (3/3) | 6135.79 | 6130.19 (3/3) | 0.39% (3/3) | 0.30% (3/3) |
| normal_std30_L6_c1_2 | 2234.64 | 2226.47 | 2220.92 | 2221.80 (3/3) | 2219.75 | 2219.78 (3/3) | 0.21% (3/3) | 0.30% (3/3) |
| poisson_L6_c1_2 | 745.98 | 745.97 | 742.40 | 742.38 (3/3) | 743.08 | 742.78 (3/3) | 0.48% (3/3) | 0.43% (3/3) |

## 跨场景概况

下表先求每场景的改进率，再对已有结果的场景等权计算均值与中位数；两者都是描述指标，不构成额外的显著性检验。“三次均值”只对有效生成求均值，缺失或失败不填入虚构成本；覆盖不足时不能视为完整实验结论。

首次生成的均值与中位数使用相同的 r1 配对场景。三次有效生成的中位数先在每场景内平均有效生成的改进率，再对这些场景均值取中位数，保持每场景等权，不把全部场景和重复次数混合后计算。

场景分母保留该方法的完整计划范围：L1 为 3、L2 为 30。历史 AHD 对照只在有可核验策略且完成评分的场景可用，因此历史对照行的覆盖分子通常低于分母；不能把覆盖缺失解释为 Baek 失败。首次生成列的 n 单独标明实际配对场景数。

最后一列“有效策略/计划策略”表示 Baek 策略本身的有效性覆盖，不是与该行对照的配对数。AHD 与经典基线的汇总均值可能来自不同场景子集，不能将两个汇总改进百分比直接相减并归因于方法差异。

| 数据 | 方法 | 对照 | 有配对结果场景/计划场景 | 首次生成平均改进 | 首次生成改进中位数 | 三次有效生成平均改进 | 三次有效生成改进中位数 | 有效策略/计划策略 |
|---|---|---|---:|---:|---:|---:|---:|---:|
| 现有基准测试集 | Baek-L1 | 训练选定经典基线 | 3/3 | 0.48% (n=3) | 0.48% | 0.47% | 0.48% | 9/9 |
| 现有基准测试集 | Baek-L1 | 历史 AHD（可用场景） | 3/3 | 0.37% (n=3) | 0.39% | 0.36% | 0.39% | 9/9 |
| 现有基准测试集 | Baek-L2 | 训练选定经典基线 | 30/30 | 0.84% (n=30) | 0.75% | 0.87% | 0.77% | 90/90 |
| 现有基准测试集 | Baek-L2 | 历史 AHD（可用场景） | 20/30 | 3.04% (n=20) | 0.74% | 3.08% | 0.90% | 90/90 |
| 独立新需求测试集 | Baek-L1 | 训练选定经典基线 | 3/3 | 0.49% (n=3) | 0.57% | 0.47% | 0.53% | 9/9 |
| 独立新需求测试集 | Baek-L1 | 历史 AHD（可用场景） | 3/3 | 0.35% (n=3) | 0.29% | 0.34% | 0.24% | 9/9 |
| 独立新需求测试集 | Baek-L2 | 训练选定经典基线 | 30/30 | 0.82% (n=30) | 0.75% | 0.85% | 0.76% | 90/90 |
| 独立新需求测试集 | Baek-L2 | 历史 AHD（可用场景） | 20/30 | 2.96% (n=20) | 0.73% | 3.01% | 0.88% | 90/90 |
| 统一整数动作检查 | Baek-L1 | 训练选定经典基线 | 3/3 | 0.47% (n=3) | 0.46% | 0.46% | 0.47% | 9/9 |
| 统一整数动作检查 | Baek-L1 | 历史 AHD（可用场景） | 3/3 | 0.36% (n=3) | 0.39% | 0.35% | 0.39% | 9/9 |
| 统一整数动作检查 | Baek-L2 | 训练选定经典基线 | 30/30 | 0.86% (n=30) | 0.76% | 0.89% | 0.75% | 90/90 |
| 统一整数动作检查 | Baek-L2 | 历史 AHD（可用场景） | 20/30 | 3.06% (n=20) | 0.76% | 3.09% | 0.92% | 90/90 |
| 长期运行检查 | Baek-L1 | 训练选定经典基线 | 3/3 | 0.21% (n=3) | 0.19% | 0.20% | 0.14% | 9/9 |
| 长期运行检查 | Baek-L1 | 历史 AHD（可用场景） | 3/3 | 0.30% (n=3) | 0.31% | 0.29% | 0.30% | 9/9 |
| 长期运行检查 | Baek-L2 | 训练选定经典基线 | 3/3 | 0.19% (n=3) | 0.24% | 0.20% | 0.24% | 9/9 |
| 长期运行检查 | Baek-L2 | 历史 AHD（可用场景） | 3/3 | 0.28% (n=3) | 0.28% | 0.29% | 0.28% | 9/9 |

### 显著性与小差距比例

显著胜/负按每个独立生成、每个场景的配对 95% 区间判断；相同生成跨场景不当作统计独立样本。0.1% / 1% 比例为场景层面的描述指标，含成本更低的场景：改进率分别 ≥ −0.1% / −1%。分母为相应列已配对且对照均值大于零的场景数。三次均值一列先在场景内平均有效生成的改进率。

| 数据 | 方法 | 对照 | 逐次配对显著胜 / 负 / 全部 | r1：0.1% / 1% 以内或更好 | 三次均值：0.1% / 1% 以内或更好 |
|---|---|---|---:|---:|---:|
| 现有基准测试集 | Baek-L1 | 训练选定经典基线 | 9 / 0 / 9 | 3/3 (100.0%) / 3/3 (100.0%) | 3/3 (100.0%) / 3/3 (100.0%) |
| 现有基准测试集 | Baek-L1 | 历史 AHD | 9 / 0 / 9 | 3/3 (100.0%) / 3/3 (100.0%) | 3/3 (100.0%) / 3/3 (100.0%) |
| 现有基准测试集 | Baek-L2 | 训练选定经典基线 | 89 / 0 / 90 | 30/30 (100.0%) / 30/30 (100.0%) | 30/30 (100.0%) / 30/30 (100.0%) |
| 现有基准测试集 | Baek-L2 | 历史 AHD | 59 / 0 / 60 | 20/20 (100.0%) / 20/20 (100.0%) | 20/20 (100.0%) / 20/20 (100.0%) |
| 独立新需求测试集 | Baek-L1 | 训练选定经典基线 | 9 / 0 / 9 | 3/3 (100.0%) / 3/3 (100.0%) | 3/3 (100.0%) / 3/3 (100.0%) |
| 独立新需求测试集 | Baek-L1 | 历史 AHD | 9 / 0 / 9 | 3/3 (100.0%) / 3/3 (100.0%) | 3/3 (100.0%) / 3/3 (100.0%) |
| 独立新需求测试集 | Baek-L2 | 训练选定经典基线 | 88 / 0 / 90 | 30/30 (100.0%) / 30/30 (100.0%) | 30/30 (100.0%) / 30/30 (100.0%) |
| 独立新需求测试集 | Baek-L2 | 历史 AHD | 58 / 0 / 60 | 20/20 (100.0%) / 20/20 (100.0%) | 20/20 (100.0%) / 20/20 (100.0%) |
| 统一整数动作检查 | Baek-L1 | 训练选定经典基线 | 9 / 0 / 9 | 3/3 (100.0%) / 3/3 (100.0%) | 3/3 (100.0%) / 3/3 (100.0%) |
| 统一整数动作检查 | Baek-L1 | 历史 AHD | 9 / 0 / 9 | 3/3 (100.0%) / 3/3 (100.0%) | 3/3 (100.0%) / 3/3 (100.0%) |
| 统一整数动作检查 | Baek-L2 | 训练选定经典基线 | 89 / 0 / 90 | 30/30 (100.0%) / 30/30 (100.0%) | 30/30 (100.0%) / 30/30 (100.0%) |
| 统一整数动作检查 | Baek-L2 | 历史 AHD | 59 / 0 / 60 | 20/20 (100.0%) / 20/20 (100.0%) | 20/20 (100.0%) / 20/20 (100.0%) |
| 长期运行检查 | Baek-L1 | 训练选定经典基线 | 7 / 0 / 9 | 3/3 (100.0%) / 3/3 (100.0%) | 3/3 (100.0%) / 3/3 (100.0%) |
| 长期运行检查 | Baek-L1 | 历史 AHD | 9 / 0 / 9 | 3/3 (100.0%) / 3/3 (100.0%) | 3/3 (100.0%) / 3/3 (100.0%) |
| 长期运行检查 | Baek-L2 | 训练选定经典基线 | 8 / 0 / 9 | 3/3 (100.0%) / 3/3 (100.0%) | 3/3 (100.0%) / 3/3 (100.0%) |
| 长期运行检查 | Baek-L2 | 历史 AHD | 9 / 0 / 9 | 3/3 (100.0%) / 3/3 (100.0%) | 3/3 (100.0%) / 3/3 (100.0%) |

## 独立新需求：逐场景结果

三次成本按 r1 / r2 / r3 顺序列出；无效或尚未评分记为 —。标准差描述生成变异，不是置信区间。逐次配对 95% bootstrap 区间见 paired_comparisons.csv，抽样单位为完整需求路径。

| 场景 | 方法 | 首次成本 | 全部有效生成均值 ± 标准差 | 三次成本 r1 / r2 / r3 | 相对经典基线平均改进 | 有效/计划 | 失败/待完成或核查 |
|---|---|---:|---:|---:|---:|---:|---:|
| exponential_L2_c1_2 | Baek-L2 | 6082.98 | 6079.38 ± 3.12 | 6082.98 / 6077.63 / 6077.53 | 0.55% | 3/3 | 0/0 |
| exponential_L2_c1_5 | Baek-L2 | 10515.94 | 10510.18 ± 4.99 | 10515.94 / 10507.47 / 10507.13 | 0.87% | 3/3 | 0/0 |
| exponential_L4_c1_2 | Baek-L2 | 6092.40 | 6088.12 ± 3.72 | 6092.40 / 6086.24 / 6085.71 | 0.34% | 3/3 | 0/0 |
| exponential_L4_c1_5 | Baek-L2 | 11174.55 | 11144.99 ± 25.60 | 11174.55 / 11130.82 / 11129.62 | 1.05% | 3/3 | 0/0 |
| exponential_L6_c1_2 | Baek-L1 | 6109.18 | 6109.36 ± 0.17 | 6109.18 / 6109.39 / 6109.52 | 0.30% | 3/3 | 0/0 |
| exponential_L6_c1_2 | Baek-L2 | 6122.64 | 6113.89 ± 7.58 | 6122.64 / 6109.77 / 6109.26 | 0.23% | 3/3 | 0/0 |
| exponential_L6_c1_5 | Baek-L2 | 11246.76 | 11218.89 ± 24.16 | 11246.76 / 11206.11 / 11203.81 | 1.40% | 3/3 | 0/0 |
| normal_std10_L2_c1_2 | Baek-L2 | 702.74 | 702.82 ± 0.09 | 702.74 / 702.91 / 702.80 | 0.70% | 3/3 | 0/0 |
| normal_std10_L2_c1_5 | Baek-L2 | 1061.78 | 1061.74 ± 0.22 | 1061.78 / 1061.94 / 1061.50 | 0.82% | 3/3 | 0/0 |
| normal_std10_L4_c1_2 | Baek-L2 | 734.56 | 734.80 ± 0.22 | 734.56 / 734.99 / 734.86 | 0.45% | 3/3 | 0/0 |
| normal_std10_L4_c1_5 | Baek-L2 | 1177.76 | 1177.51 ± 0.55 | 1177.76 / 1177.89 / 1176.89 | 1.25% | 3/3 | 0/0 |
| normal_std10_L6_c1_2 | Baek-L2 | 751.12 | 750.19 ± 0.82 | 751.12 / 749.55 / 749.91 | 0.52% | 3/3 | 0/0 |
| normal_std10_L6_c1_5 | Baek-L2 | 1220.74 | 1220.81 ± 0.51 | 1220.74 / 1221.35 / 1220.33 | 1.36% | 3/3 | 0/0 |
| normal_std30_L2_c1_2 | Baek-L2 | 2109.22 | 2108.91 ± 0.30 | 2109.22 / 2108.62 / 2108.89 | 0.64% | 3/3 | 0/0 |
| normal_std30_L2_c1_5 | Baek-L2 | 3209.64 | 3209.67 ± 0.93 | 3209.64 / 3210.62 / 3208.76 | 0.76% | 3/3 | 0/0 |
| normal_std30_L4_c1_2 | Baek-L2 | 2198.70 | 2198.23 ± 0.44 | 2198.70 / 2198.18 / 2197.82 | 0.50% | 3/3 | 0/0 |
| normal_std30_L4_c1_5 | Baek-L2 | 3501.54 | 3500.81 ± 0.90 | 3501.54 / 3501.10 / 3499.80 | 1.33% | 3/3 | 0/0 |
| normal_std30_L6_c1_2 | Baek-L1 | 2236.65 | 2237.68 ± 1.61 | 2236.65 / 2236.86 / 2239.53 | 0.53% | 3/3 | 0/0 |
| normal_std30_L6_c1_2 | Baek-L2 | 2235.72 | 2235.98 ± 0.25 | 2235.72 / 2235.99 / 2236.22 | 0.60% | 3/3 | 0/0 |
| normal_std30_L6_c1_5 | Baek-L2 | 3653.66 | 3653.64 ± 1.15 | 3653.66 / 3654.78 / 3652.48 | 1.67% | 3/3 | 0/0 |
| normal_std50_L2_c1_2 | Baek-L2 | 3435.93 | 3435.78 ± 0.17 | 3435.93 / 3435.82 / 3435.60 | 0.63% | 3/3 | 0/0 |
| normal_std50_L2_c1_5 | Baek-L2 | 5240.33 | 5240.47 ± 1.77 | 5240.33 / 5242.30 / 5238.77 | 0.71% | 3/3 | 0/0 |
| normal_std50_L4_c1_2 | Baek-L2 | 3578.68 | 3578.06 ± 0.56 | 3578.68 / 3577.59 / 3577.91 | 0.75% | 3/3 | 0/0 |
| normal_std50_L4_c1_5 | Baek-L2 | 5746.59 | 5746.70 ± 2.27 | 5746.59 / 5749.02 / 5744.48 | 1.10% | 3/3 | 0/0 |
| normal_std50_L6_c1_2 | Baek-L2 | 3630.97 | 3630.82 ± 0.22 | 3630.97 / 3630.92 / 3630.57 | 0.59% | 3/3 | 0/0 |
| normal_std50_L6_c1_5 | Baek-L2 | 6019.31 | 6019.59 ± 0.51 | 6019.31 / 6020.18 / 6019.28 | 1.50% | 3/3 | 0/0 |
| poisson_L2_c1_2 | Baek-L2 | 697.76 | 697.57 ± 0.18 | 697.76 / 697.56 / 697.40 | 0.79% | 3/3 | 0/0 |
| poisson_L2_c1_5 | Baek-L2 | 1064.79 | 1066.32 ± 3.30 | 1064.79 / 1070.11 / 1064.07 | 0.59% | 3/3 | 0/0 |
| poisson_L4_c1_2 | Baek-L2 | 729.37 | 729.21 ± 0.28 | 729.37 / 729.39 / 728.88 | 1.12% | 3/3 | 0/0 |
| poisson_L4_c1_5 | Baek-L2 | 1169.57 | 1169.74 ± 2.44 | 1169.57 / 1172.26 / 1167.39 | 0.86% | 3/3 | 0/0 |
| poisson_L6_c1_2 | Baek-L1 | 742.76 | 742.74 ± 0.03 | 742.76 / 742.71 / 742.75 | 0.58% | 3/3 | 0/0 |
| poisson_L6_c1_2 | Baek-L2 | 743.57 | 743.36 ± 0.56 | 743.57 / 743.78 / 742.73 | 0.50% | 3/3 | 0/0 |
| poisson_L6_c1_5 | Baek-L2 | 1220.29 | 1219.21 ± 1.55 | 1220.29 / 1219.90 / 1217.42 | 1.37% | 3/3 | 0/0 |

![fresh_test_improvement](/Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/figures/fresh_test_improvement.svg)

[下载独立 SVG 图](</Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/figures/fresh_test_improvement.svg>)

![fresh_test_vs_ahd_improvement](/Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/figures/fresh_test_vs_ahd_improvement.svg)

[下载独立 SVG 图](</Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/figures/fresh_test_vs_ahd_improvement.svg>)

![existing_test_improvement](/Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/figures/existing_test_improvement.svg)

[下载独立 SVG 图](</Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/figures/existing_test_improvement.svg>)

![existing_test_vs_ahd_improvement](/Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/figures/existing_test_vs_ahd_improvement.svg)

[下载独立 SVG 图](</Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/figures/existing_test_vs_ahd_improvement.svg>)

## 稳健性与有效性

独立新需求每场景 1000 条路径；整数检查对所有方法统一使用 ties-to-even 取整。长期检查仅覆盖三个核心场景：20 条 × 10000 期，丢弃前 2000 期。各检查均使用已经冻结的策略，不据此调参。长期结果的总成本对应保留期数，横向阅读应使用每期成本列。这项有限长轨迹敏感性检查没有证明系统已经达到稳态；当前未预先登记分段稳定性判据，不事后宣称收敛。

配对统计要求相同的需求路径与计分协议；有需求哈希时核对哈希，同时核对逐路径需求总量、路径数及计分期数。逐对 95% 区间描述需求抽样误差，不包含生成之间的差异，且没有进行多重比较校正。

明确无效输出、非法策略或策略执行超时计为失败；尚未评分、需要人工核查、来源哈希不一致或执行基础设施故障列入待完成或核查，不擅自认定为模型策略失败。

初始化超过原文 30 秒目标的 Baek 场景策略：0/99。600 秒为防止初始化卡死的执行上限；超过 30 秒的记录保留并标明，不宣称满足原文的初始化时间目标。

经典基线的向量化评分器没有测量逐动作耗时；其计时占位值不解释为零运行时间。

## 模型费用与运行资源

模型：`openai/gpt-5.6-sol`，推理强度 `high`。已知实际计费 **$5.439324**，其中接口预检 $0.000664；含未决请求保守预留的账本金额 **$7.212040**，全局上限 $30.00。仍有 2 条费用未决记录，上界合计 $1.772716。其中 $1.772716 已明确保留全额上界并允许原会话恢复，实际费用仍未知。Python 模拟用时不折算成 API token 费用。

Python 用时按单调时钟统计子进程墙钟时间，包含启动开销，不是 CPU 秒数。每个 worker 的 BLAS 设置为单线程；耗时仍受硬件和其他并发任务影响。时间预算是在本次机器与调度配置下的执行限制，不能作为跨硬件严格相等的计算量。

| 会话 | 状态 | 实际已知费用 | 输入 token | 输出 token（含推理） | Python 墙钟秒数 | 工具调用 | 冻结代码 |
|---|---|---:|---:|---:|---:|---:|---|
| l1_exponential_r1 | completed | $0.360177 | 380383 | 20333 | 1549.09 | 20 | [源码](</Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/sessions/l1_exponential_r1/policy.py>) |
| l1_exponential_r2 | completed | $0.299753 | 314149 | 18448 | 2491.63 | 25 | [源码](</Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/sessions/l1_exponential_r2/policy.py>) |
| l1_exponential_r3 | completed | $0.255966 | 125408 | 17847 | 1866.05 | 12 | [源码](</Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/sessions/l1_exponential_r3/policy.py>) |
| l1_normal_r1 | completed | $0.311223 | 227117 | 15255 | 3473.38 | 17 | [源码](</Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/sessions/l1_normal_r1/policy.py>) |
| l1_normal_r2 | completed | $0.378964 | 530033 | 19872 | 1542.44 | 29 | [源码](</Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/sessions/l1_normal_r2/policy.py>) |
| l1_normal_r3 | completed | $0.241269 | 153936 | 12516 | 3600.02 | 13 | [源码](</Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/sessions/l1_normal_r3/policy.py>) |
| l1_poisson_r1 | completed | $0.352632 | 266964 | 15252 | 2744.18 | 21 | [源码](</Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/sessions/l1_poisson_r1/policy.py>) |
| l1_poisson_r2 | completed | $0.273581 | 274989 | 16093 | 2982.31 | 20 | [源码](</Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/sessions/l1_poisson_r2/policy.py>) |
| l1_poisson_r3 | completed | $0.223346 | 190798 | 13822 | 2995.22 | 16 | [源码](</Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/sessions/l1_poisson_r3/policy.py>) |
| l2_exponential_r1 | completed | $0.345252 | 219026 | 23632 | 711.22 | 14 | [源码](</Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/sessions/l2_exponential_r1/policy.py>) |
| l2_exponential_r2 | completed | $0.288824 | 185429 | 19672 | 771.60 | 12 | [源码](</Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/sessions/l2_exponential_r2/policy.py>) |
| l2_exponential_r3 | completed | $0.285007 | 195306 | 19091 | 450.44 | 14 | [源码](</Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/sessions/l2_exponential_r3/policy.py>) |
| l2_normal_r1 | completed | $0.412934 | 153779 | 24495 | 862.59 | 9 | [源码](</Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/sessions/l2_normal_r1/policy.py>) |
| l2_normal_r2 | completed | $0.304634 | 133663 | 22265 | 1051.88 | 9 | [源码](</Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/sessions/l2_normal_r2/policy.py>) |
| l2_normal_r3 | completed | $0.302058 | 128385 | 22335 | 982.85 | 8 | [源码](</Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/sessions/l2_normal_r3/policy.py>) |
| l2_poisson_r1 | completed | $0.237310 | 108116 | 17458 | 1399.06 | 10 | [源码](</Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/sessions/l2_poisson_r1/policy.py>) |
| l2_poisson_r2 | completed | $0.225290 | 96206 | 16682 | 1970.06 | 9 | [源码](</Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/sessions/l2_poisson_r2/policy.py>) |
| l2_poisson_r3 | completed | $0.340440 | 255363 | 22490 | 1269.35 | 15 | [源码](</Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/sessions/l2_poisson_r3/policy.py>) |

基础设施记录：18 个计划请求在模型推理开始前被路由层拒绝，另有 1 个诊断拒绝请求。已核对这部分计费为 $0.000000。它们没有生成策略，不计入独立生成次数或策略失败率。[费用核对记录](</Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/billing_reconciliation.json>)

本轮已记录的实际调度为生成端至多 3 个 worker，与自动评分端至多 2 个 worker 同时运行。manifest 记录了操作系统和逻辑 CPU 数；这里补充实际并发配置，以便解释墙钟预算。

暂停与恢复：本次运行记录了用户要求的暂停。日志起止时间包含暂停时段；恢复后的 Python 执行秒数排除了暂停。2 个已有 Python 进程保留内存后继续执行，没有重跑；暂停前的有效执行时长含记录注明的亚秒级估计误差。暂停时尚未返回的 HTTP 响应被接收并保存，没有重新发送该请求。这些恢复操作不增加独立生成或无效补跑次数。 [暂停记录](</Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/pause_history/20260915T234434.json>)；[原请求响应恢复记录](</Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/resume_http_drain.json>)；[l1_normal_r1 进程恢复记录](</Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/sessions/l1_normal_r1/recovered_tool_pending.json>)；[l1_poisson_r1 进程恢复记录](</Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/sessions/l1_poisson_r1/recovered_tool_pending.json>)

### 传输故障后的原会话恢复

日志中有 2 条通过原日志、请求、上下文及证据哈希核验的恢复记录。其中未知费用的保守上界合计 **$1.772716**，继续占用全局预算；上界不当作已确认实际费用。恢复限定在原会话、原提示和原上下文内，保留已完成工具结果及累计调用次数、执行时长，工具预算不重置。这些传输恢复本身不增加独立生成次数，也不属于无效策略补跑或按测试成绩重抽。

丢失的响应可能已在服务端执行；保留费用上界不代表原请求未执行或已确认零收费。从已保存上下文继续也不能称为找回丢失的原响应。下表区分恢复核准与已经开始续接，策略是否完成仍以上方会话状态为准；恢复记录不证明 TLS 故障根因已修复。

| 会话 | 原传输请求（从 1 开始） | 恢复状态 | 原请求实际费用 | 保留上界 | 核账记录 |
|---|---:|---|---:|---:|---|
| l1_normal_r2 | 29 | 已记录从原上下文开始续接 | 未知 | $0.952908 | [证据](</Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/transport_recovery_ssl_20260916/recovery_decision.json>)；[证据](</Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/transport_recovery_ssl_20260916/key_usage_snapshot.json>)；[证据](</Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/transport_recovery_ssl_20260916/key_usage_snapshot_2.json>)；[证据](</Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/transport_recovery_ssl_20260916/offline_native_checkpoint_check.json>)；[证据](</Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/transport_recovery_ssl_20260916/original_failures/l1_normal_r2/result.json>)；[证据](</Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/transport_recovery_ssl_20260916/original_failures/l1_normal_r2/events.jsonl>) |
| l1_poisson_r2 | 21 | 已记录从原上下文开始续接 | 未知 | $0.819808 | [证据](</Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/transport_recovery_ssl_20260916/recovery_decision.json>)；[证据](</Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/transport_recovery_ssl_20260916/key_usage_snapshot.json>)；[证据](</Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/transport_recovery_ssl_20260916/key_usage_snapshot_2.json>)；[证据](</Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/transport_recovery_ssl_20260916/offline_native_checkpoint_check.json>)；[证据](</Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/transport_recovery_ssl_20260916/original_failures/l1_poisson_r2/result.json>)；[证据](</Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/transport_recovery_ssl_20260916/original_failures/l1_poisson_r2/events.jsonl>) |

账户汇总快照只反映各查询时已经入账的费用。核对中已观察到账户汇总落后于成功响应日志，因此一次金额对齐不能证明故障请求永久零收费。 [key_usage_snapshot.json](</Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/transport_recovery_ssl_20260916/key_usage_snapshot.json>)；[key_usage_snapshot_2.json](</Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/transport_recovery_ssl_20260916/key_usage_snapshot_2.json>)

## 适配范围与结论限制

本实验比较 Baek 的单任务工具调用策略设计流程在我们的环境中的表现。目标为 50 期销售成本、动作允许非负有限实数且没有订货容量上限；固定提前期、确定性 stationary 策略，以及 Poisson、取整 Exponential、截零取整 Normal 是本轮具体设定。

历史 AHD 和 Baek 可能使用不同模型、计算预算及信息条件：Baek 知道真实需求分布，历史 AHD 主要依据训练样本。因此结果不能单独归因于搜索框架。现有基准测试集曾用于历史评测，独立新需求结果单独列出。没有可靠最优解的场景仅报告相对对照的成本差，不称最优性差距。

提示描述也有差异：仓库现有 v2 提示的到货/决策时序描述与实际模拟器不一致，本轮问题描述已按实际动态修正；历史 AHD 保留既有策略，没有使用本轮相同提示重新生成。这不表示全部历史运行均使用该 v2 提示，也不据此推断这一差异对成绩的影响。见[已批准方案 §3](</Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/docs/baek_2026_comparison_proposal.md>)。

历史 AHD 可用性及模型身份见下表；所有训练候选来源、索引、哈希和审计结果见 references.csv。

冻结的历史清单包含 64 个运行、20 个有来源策略的场景；当前已保存历史评测记录 20 个场景。

| 场景 | 历史模型 | 历史运行 | 训练记录成本 | 评测状态 |
|---|---|---|---:|---|
| exponential_L2_c1_2 | deepseek-chat | deepseek-chat_exponential_L2_c1_2_50_plain_processed_scipy_15_default_m2_10_r2 | 5879.34 | ok |
| exponential_L2_c1_5 | deepseek-chat | deepseek-chat_exponential_L2_c1_5_50_plain_processed_scipy_15_default_m2_10_r1 | 10145.32 | ok |
| exponential_L4_c1_2 | deepseek-chat | deepseek-chat_exponential_L4_c1_2_50_plain_processed_scipy_15_default_m2_10_r1 | 6094.36 | ok |
| exponential_L4_c1_5 | deepseek-chat | deepseek-chat_exponential_L4_c1_5_50_plain_processed_scipy_15_default_m2_2_r6 | 10982.31 | ok |
| exponential_L6_c1_2 | deepseek-chat | deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2_2_r6 | 5997.98 | ok |
| exponential_L6_c1_5 | deepseek-chat | deepseek-chat_exponential_L6_c1_5_50_plain_processed_scipy_15_default_m2_10_r1 | 11038.29 | ok |
| normal_std10_L2_c1_5 | deepseek-chat | deepseek-chat_normal_std10_L2_c1_5_50_plain_processed_scipy_15_default_m2_2_r6 | 1387.45 | ok |
| normal_std10_L6_c1_2 | deepseek-chat | deepseek-chat_normal_std10_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r8 | 713.64 | ok |
| normal_std10_L6_c1_5 | deepseek-chat | deepseek-chat_normal_std10_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r6 | 1273.44 | ok |
| normal_std30_L6_c1_2 | x-ai/grok-4.1-fast | grok-4.1-fast_normal_std30_L6_c1_2_50_plain_processed_scipy_15_default_m2_2_r1 | 2234.28 | ok |
| normal_std30_L6_c1_5 | deepseek-chat | deepseek-chat_normal_std30_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r8 | 3807.04 | ok |
| normal_std50_L4_c1_5 | deepseek-chat | deepseek-chat_normal_std50_L4_c1_5_50_plain_processed_scipy_15_default_m2_10_r1 | 6096.96 | ok |
| normal_std50_L6_c1_2 | deepseek-chat | deepseek-chat_normal_std50_L6_c1_2_50_plain_processed_scipy_15_default_m2_10_r1 | 3715.01 | ok |
| normal_std50_L6_c1_5 | deepseek-chat | deepseek-chat_normal_std50_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r6 | 6336.84 | ok |
| poisson_L2_c1_2 | deepseek-chat | deepseek-chat_poisson_L2_c1_2_50_plain_processed_scipy_15_default_m2_10_r1 | 737.48 | ok |
| poisson_L2_c1_5 | deepseek-chat | deepseek-chat_poisson_L2_c1_5_50_plain_processed_scipy_15_default_m2_10_r1 | 1092.20 | ok |
| poisson_L4_c1_2 | deepseek-chat | deepseek-chat_poisson_L4_c1_2_50_plain_processed_scipy_15_default_m2_10_r1 | 745.56 | ok |
| poisson_L4_c1_5 | deepseek-chat | deepseek-chat_poisson_L4_c1_5_50_plain_processed_scipy_15_default_m2_10_r1 | 1188.42 | ok |
| poisson_L6_c1_2 | deepseek-chat | deepseek-chat_poisson_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r8 | 760.86 | ok |
| poisson_L6_c1_5 | deepseek-chat | deepseek-chat_poisson_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r6 | 1165.30 | ok |

## 完整表格与记录

- [三次独立生成的订货规则解释](</Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/policy_design_all_draws.md>)
- [第一组规则详解](</Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/policy_design_comparison.md>)
- [per_draw.csv](</Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/tables/per_draw.csv>)
- [paired_comparisons.csv](</Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/tables/paired_comparisons.csv>)
- [repeat_summary.csv](</Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/tables/repeat_summary.csv>)
- [generation.csv](</Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/tables/generation.csv>)
- [references.csv](</Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/tables/references.csv>)
- [draw_selection.csv](</Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/tables/draw_selection.csv>)
- [冻结的实验定义与数据哈希](</Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/manifest.json>)
