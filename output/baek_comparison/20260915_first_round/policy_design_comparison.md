# Baek 方法在我们的环境里设计出了什么 policy？

**六份 r1 输出的共同结构是：把现货和有到货顺序的在途订单转成库存特征，再据此订货。** Poisson 和 Normal 主要使用“新订单到货前还会剩多少库存”的预测；Exponential L1 使用分段线性状态反馈，L2 使用带上限的加权库存规则并增加一个预测项。LLM 产出了可执行规则和调参程序，部署后的每期动作由这些程序直接计算。

本文依据冻结源码与审查笔记，归纳 **Poisson、Normal、Exponential 各族 L1/L2 的完整第一组生成，共六份 r1**。六份源码均已与生成记录中的 SHA256 核对；这里仍不包含三次独立重复的完整结论。

## 1. L1 与 L2 分别交付什么？

| | L1：针对一个实例 | L2：针对一个分布族 |
|---|---|---|
| 输出 | 已写定参数的订货函数 | `design(params)`，接收提前期、需求与成本参数，返回订货函数 |
| 本轮适用范围 | 各族的 L=6、持有/缺货成本=1/2 核心场景 | 同一份设计程序覆盖该族的网格：Poisson 6 格、Normal 18 格、Exponential 6 格 |
| 实例初始化 | 最终文件只加载常量 | 根据已知分布生成合成路径，做数值搜索，再冻结参数 |
| 每期执行 | 输入当前状态，计算一次订单 | 使用初始化得到的固定参数计算订单；没有每期重新优化 |

统一记号：I 为本期到货后的现货；Pⱼ 为再过 j 期到货的旧订单，j = 1, …, L−1；q 为现在下单、L 期后到货的数量；[x]⁺ = max(x, 0)。以下规则都使用完整的有序在途向量，不能简单概括成只看 I + Σⱼ Pⱼ。

## 2. 六份已交付规则

### Poisson L1：预测库存的固定线性反馈

常规动作是 **q = clip(99.5 − 0.78 m₆, 0, 99.5)**。从当前状态预测未来六次需求后的剩余库存均值 m₆，期间依次接入五个旧订单。预测同时传播均值和方差，每步把“库存减需求”近似为正态，再计算其正部的前两阶矩。

这里每步加入的**有效需求方差为 80**，真实 Poisson(100) 方差是 100；80 是固定的启发式参数。方差通过预测间接影响动作，没有单独的风险加项。初始化备货序列为 **(101,96,96,96,96,96)**，所以 99.5 只是常规分支的上限。部署时没有调参，动作计算只需六步递推。

来源：[冻结源码](/Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/sessions/l1_poisson_r1/policy.py)、[审查笔记 §2](/Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/policy_notes_first_draws.md)。

### Poisson L2：均值反馈，加预测不确定性修正

常规动作是 **q = [μ + a√μ − b m_L + c√v_L]⁺**，另有很大的数值保护上限。m_L、v_L 仍来自正态正部的矩递推，此处需求方差增量使用真实的 μ。b 抑制预测库存较多时的订货；c 可正可负，由搜索决定如何修正预测不确定性。

初始化生成 **6,000 条固定种子的 Poisson 合成路径**，每条 50 期。三轮小规模差分进化依次搜索三个常规参数、两个备货参数，再细调常规参数。两个备货参数决定首个销售期现货与后续等量在途订单；这些值与常规参数一并冻结。每期只做 O(L) 递推。

这是对缺货截断过程的矩近似。另有一个设计模拟与部署的条件性差别：模拟在销售期使用常规公式，实际函数若重新遇到备货匹配状态，会再次执行备货分支；是否实际出现及其影响未量化。

来源：[冻结源码](/Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/sessions/l2_poisson_r1/policy.py)、[审查笔记 §1](/Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/policy_notes_first_draws.md)。

### Normal L1：确定性库存投影，加分段线性订货表

先递推 y₀ = [I − d₀]⁺、yⱼ = [yⱼ₋₁ + Pⱼ − dⱼ]⁺，其中六个有效需求量约为 **(75.47,93.33,98.74,98.75,98.75,98.75)**。它们是预测参数，并非环境的真实均值；索引表示距本期订单到货的相对位置。

若最终投影接近零，订货 **87.991**；否则根据投影量，在结点 **0、5、10、20、40、80、160** 上线性插值，订单从约 **86.076** 逐渐降到 **0**。因此原点附近存在约 1.915 单位的跳跃，整条规则不是单一线性函数。

备货序列约为 **(103.37,89.84,88.11,87.21,87.33,86.01)**。全部参数已写定，每期只需六步截零递推和一次插值。它不传播方差；不确定性的作用通过这些固定参数和动作曲线间接体现。

来源：[冻结源码](/Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/sessions/l1_normal_r1/policy.py)、[审查笔记 §3](/Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/policy_notes_first_draws.md)。

### Normal L2：混合两种库存预测的四参数规则

动作家族是

> q = [A − b{w C(I, P) + (1 − w) M(I, P)} − c P̄]⁺

C 使用截零、舍入 Normal 的离散概率表，先计算一期函数 f(x) = E[(x − D)⁺]，再按 f(I)、f(f(I) + P₁)、… 递推；M 使用正态正部的均值/方差递推；P̄ 是平均在途量。

初始化用 **2,048 条 scrambled Sobol 合成路径**搜索四个参数，并用另一组 **4,096 条**进一步调整目标量 A 和选择候选；还比较简化规则及恒定订货候选。方法包括差分进化、Nelder–Mead 和一维优化。两套路径都参与开发；Sobol 路径具有准蒙特卡洛结构，不应称为普通独立随机样本。每期执行只需 O(L) 递推。

一期 f 除极小尾部截断外是精确的，**把随机库存替换成均值后的多期递推仍是近似**；M 同样依赖正态近似，甚至可能在空系统中预测出正的剩余量。混合和调参可补偿部分误差，但没有精确性保证。

来源：[冻结源码](/Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/sessions/l2_normal_r1/policy.py)、[详细审查](/Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/policy_notes_l2_normal_r1.md)。

### Exponential L1：分段线性的库存与在途反馈

令 x₀ = I/100、xⱼ = Pⱼ/100、T = x₀ + Σⱼ xⱼ。规则可写为：

> q = 100 [0.85993599 + 0.07725468 x₀ − Σⱼ wⱼ xⱼ + G(x₀) + H(T)]⁺

五个在途惩罚权重约为 **(0.00545,0.02922,0.05609,0.13157,0.30589)**，较晚到货的权重更大。G 使用现货阈值 **0.25、0.5、1、2** 的正部项，H 使用总库存阈值 **1 至 6** 的正部项；例如 [x₀ − 0.25]⁺ 在越过阈值后才改变斜率。参数已全部写定，每期只做固定数量的加减乘与截零。

它没有显式的多期库存预测或部署时调参，也没有专用备货表；零状态首单为 **85.993599**。低库存区间的现货系数为正，现货从 0 增至 10、在途保持为零时，订单会增至约 **86.7661**，因此不能把它解释成“库存越多，订货必越少”。虽然没有显式上限参数 C，这些固定系数在非负状态域内隐含约 **95.1935** 的动作上界，详见源码审查的静态推导。最终文件没有开发模拟器，不能仅凭它核实生成阶段的调参目标。

来源：[冻结源码](/Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/sessions/l1_exponential_r1/policy.py)、[详细审查](/Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/policy_notes_l1_exponential_r1.md)。

### Exponential L2：带上限的加权库存规则，加均值需求投影

最终动作家族是

> q = min{C, [A − α I − Σⱼ βⱼ Pⱼ − κ r]⁺}

r 用舍入 Exponential 的真实均值 d̄ 代替每期随机需求：先算 [I − d̄]⁺，再依次加入 Pⱼ、扣除 d̄ 并截零。不同到货位置有不同权重 βⱼ；κ 可以为零，退回纯加权规则。C 是策略自己选的订货上限，环境没有容量限制。

初始化使用 **4,096 条训练和 2,048 条开发验证 Sobol 路径**：从 capped base-stock 开始，搜索平滑的位置权重，再放开各位置权重，最后尝试加入投影项。采用差分进化和多起点 Powell；候选按 **0.6×训练成本+0.4×开发验证成本**选择。“验证”路径反复参与选择，仍属开发数据。每期只需 O(L) 加减乘及截断。

r 是均值需求下的确定性预测，通常低估真正的期望剩余库存，不能当作精确条件期望。这份规则与 Normal L2 都在备货期继续使用同一个公式，初始化模拟显式包含 L 个零需求备货期。

来源：[冻结源码](/Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/sessions/l2_exponential_r1/policy.py)、[详细审查](/Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/policy_notes_l2_exponential_r1.md)。

## 3. 备货识别为什么仍符合 stationary？

这里 stationary 指：**相同的当前库存和在途向量，始终给出相同动作**。Poisson 两份策略和 Normal L1 在现货接近零、在途恰好匹配备货序列前缀时返回下一笔固定订单；它们没有保存调用次数、读取时点或切换隐藏阶段。因此识别来自可见状态，符合本轮契约。若销售期重现同一状态，也必须触发同一分支。

Normal L2 与 Exponential 两份策略没有专门的备货表。所有 L2 程序的模拟随机数只用于初始化，随后参数固定；50 期目标可以影响初始化参数，但每期动作不读取剩余期限。源码审查未发现这六份程序存在提前一期到货或读取未来实际需求的错误。L2 各实例最终选择的具体参数没有单独导出参数表，本文也没有通过重新执行设计器获取参数，因而不推断每个实例最终使用了哪个简化分支。

## 4. 这些规则目前做到了多好？

下表只举三个核心场景：同一场景各方法使用相同的 **1,000 条新需求路径**，报告 **50 期总成本**；成本越低越好。改善率的分母是历史 AHD 成本。

| 核心场景 | 历史 AHD | L1 r1 | L2 r1 | L1 / L2 相对 AHD 改善 |
|---|---:|---:|---:|---:|
| Poisson，L=6，成本1/2 | 747.096 | 742.761 | 743.568 | +0.5802% / +0.4722% |
| Normal，std=30，L=6，成本1/2 | 2243.106 | 2236.650 | 2235.716 | +0.2878% / +0.3295% |
| Exponential，L=6，成本1/2 | 6121.213 | 6109.184 | 6122.638 | +0.1965% / −0.0233% |

Poisson/Normal 四项对 AHD 的配对 95% 改善区间均为正；Exponential L1 的区间为 **[+0.0704%,+0.3244%]**，也支持其成本较低。Exponential L2 的区间为 **[−0.1885%,+0.1455%]**，尚不能判定优劣。这里只报告完整的第一组生成。三次独立重复现已全部完成，其均值和变异见[主报告](/Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/report.md)，全部规则结构见[三次生成详解](/Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/policy_design_all_draws.md)；r1 单独不能判断生成稳定性，本轮也没有证明任何策略接近最优。

比较时需保留信息与计算条件：Baek 得到真实分布参数，L2 还能自行模拟大量开发路径；历史 AHD 来自不同模型和既有搜索预算，主要依据训练样本。结果支持“这些已交付规则在统一测试上的表现”，不能单独归因于设计框架。初始化数值搜索也只是受限参数族内的有限搜索，没有全局收敛或最优性保证。

结果来源：[持续更新的主报告](/Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/report.md)、[配对统计](/Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/tables/paired_comparisons.csv)、[前四份策略的统计验收记录](/Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/interim_report_audit.md)。
