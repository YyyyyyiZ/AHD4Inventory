# 三次独立生成：Baek 方法交付了哪些订货规则？

本轮每个分布族分别运行 L1、L2 各三次，共 18 份源码，均已完成生成与评测。本文归纳冻结代码的结构，性能与覆盖状态以[主报告](/Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/report.md)为准。第一组六份规则的逐项解释见[第一组详解](/Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/policy_design_comparison.md)。

**L1 交付一个实例的固定订货函数；L2 交付 `design(params)`，在实例初始化时模拟已知分布并调参，再返回固定订货函数。** 执行每期订单时使用已生成的程序，不再请求 LLM。这里的“分布族设计器”只在本轮规定的参数网格上经过评测，不代表所有参数范围都已验证。

记 I 为本期到货后的现货，Pⱼ 为再过 j 期到货的旧订单，q 为当前订单；q 在 L 期后到货。[x]⁺ 表示 max(x,0)。m_L、v_L 表示各策略自己预测的剩余库存均值和方差；不同代码的预测模型不同，不能把这些符号默认当成真实条件矩。

## 1. 各次生成的结构

表中每个已完成条目链接对应的冻结源码。性能比较使用预定的三次独立生成，没有按测试成本挑选一份代表整个方法。

| 分布与层次 | 第一次 r1 | 第二次 r2 | 第三次 r3 |
|---|---|---|---|
| Poisson L1 | [q=clip(99.5−0.78m₆,0,99.5)](/Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/sessions/l1_poisson_r1/policy.py)。正态正部矩预测，需求方差取80；有状态匹配备货分支。 | [q=[100.375−m₆]⁺](/Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/sessions/l1_poisson_r2/policy.py)。预测需求均值100.9、方差100；有状态匹配备货分支。 | [q=[101.18+0.075√v₆−m₆]⁺](/Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/sessions/l1_poisson_r3/policy.py)。预测需求均值101.35、方差143；统一使用同一个规则。 |
| Poisson L2 | [均值反馈加方差修正](/Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/sessions/l2_poisson_r1/policy.py)：[μ+a√μ−bm_L+c√v_L]⁺，并搜索备货参数；6,000条开发路径。 | [带上限的投影补货](/Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/sessions/l2_poisson_r2/policy.py)：min(C,[S−y]⁺)。用 Poisson 一期精确期望反复代入均值，9,000条开发路径调 S、C。 | [q=[μ+k(B−m_L)]⁺](/Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/sessions/l2_poisson_r3/policy.py)。预测中的需求均值、方差都取 μ+s√μ；10,000条开发路径联合调 B、k、s。 |
| Normal L1 | [确定性库存投影加分段线性订货表](/Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/sessions/l1_normal_r1/policy.py)，并有状态匹配备货分支。 | [加权在途库存的分段响应](/Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/sessions/l1_normal_r2/policy.py)：W=I+1.14P₁+1.06P₂+1.17P₃+1.20P₄+1.65P₅，依 W 分段订货；有备货分支。 | [六步确定性库存投影再补货](/Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/sessions/l1_normal_r3/policy.py)：每步预测需求98.92710131，q=[1.00220586(87.3074014−y)]⁺；有状态匹配的103/90/88/87/87/86备货表。 |
| Normal L2 | [混合两种库存预测](/Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/sessions/l2_normal_r1/policy.py)，再加入平均在途量修正；2,048和4,096条 Sobol 开发路径，搜索四个参数。 | [预测均值加最新在途订单修正](/Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/sessions/l2_normal_r2/policy.py)：[A−g m_L−s(P_{L−1}−d̄)]⁺；4,096条 Latin-hypercube 开发路径，搜索三个参数。 | [两点分布库存预测加均值/波动反馈](/Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/sessions/l2_normal_r3/policy.py)：clip(b d̄−g m_L+r√v_L,0,4d̄)，搜索四参数 b、g、r、λ。L≤3使用4,096条 Sobol 开发路径，否则2,048条。 |
| Exponential L1 | [现货、各在途量与总库存的分段线性反馈](/Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/sessions/l1_exponential_r1/policy.py)，参数全部写定。 | [指数加权矩的解析预测加分段订货函数](/Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/sessions/l1_exponential_r2/policy.py)，订单上限82.83732902；连续指数预测与环境的取整需求仍有差异。 | [固定6→12→1神经网络](/Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/sessions/l1_exponential_r3/policy.py)：库存状态除以200，12个 tanh 隐层单元，120×sigmoid 输出；另有状态匹配的备货订单表。 |
| Exponential L2 | [带上限的加权库存反馈加均值需求投影](/Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/sessions/l2_exponential_r1/policy.py)；4,096和2,048条 Sobol 开发路径，分阶段数值搜索。 | [q=[A−c m_L]⁺](/Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/sessions/l2_exponential_r2/policy.py)。用可调尺度 gμ 做取整指数的一期期望，再代入均值递推；4,096条 Sobol 开发路径搜索三个参数。 | [全零状态订 Q，其余 q=[A−cR]⁺](/Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/sessions/l2_exponential_r3/policy.py)。连续指数的一期期望做均值递推；16,384条 Sobol 开发路径、两个起点搜索 Q、A、c。 |

Normal L2 r3 在 m>0 时把非负库存近似成0和 y=m+λv/m，后者概率为 m/y。这个构造保持均值，把方差设为 λv；λ=1 时同时保持原方差。即使需求的一期概率表准确，多期反复重建两点分布仍是近似。Normal L2 r2/r3 式中的 d̄ 分别是各自截零、舍入需求概率表的均值，不必等于潜在正态分布的名义均值 μ。

Exponential L1 r3 的神经网络权重已写定，每期只做一次前向计算。订单取整会改变其备货分支：首单86.126…取整为86后，下一期管道不再匹配原来的浮点模板，后续转入网络。因此整数动作检查同时检验了取整对后续状态和分支的影响。

“开发路径”用于程序自己的搜索和选择，不是外部测试集；多次搜索同一套路径也不能视为独立验证。Sobol、Latin-hypercube 是构造模拟样本的方式，不能笼统称为普通独立随机采样。

## 2. 一个值得解释的结构：Exponential L1 r2

这一份代码对**连续指数需求**建立了有限期剩余库存均值的解析递推。令需求均值为 μ，需求前库存为随机变量 X，并记录 Mₖ=E[Xᵏ exp(−X/μ)]。消耗一个独立的连续指数需求后，Y=[X−D]⁺ 满足：

- E[Y]=E[X]−μ+μM₀。
- E[exp(−Y/μ)]=M₀+M₁/μ。
- 当 k>0 时，E[Yᵏ exp(−Y/μ)]=Mₖ₊₁/[μ(k+1)]。

已知到货量再通过二项式平移这些矩。因为预测只有六期，记录有限阶矩就足以递推所需均值；每一步使用当前已知的旧在途订单。以上关系已按指数密度直接积分核对，不依赖模型生成过程中的推理文本。

**精确性仅限这个连续需求预测。** 实际评测需求取整；在相同当前状态、相同旧在途管道，并将同一组连续需求样本逐次舍入的耦合下，六期预测库存的路径差不超过3单位。这不是闭环运行的成本差界，也不证明最终订货函数最优。代码仍通过一条固定的分段响应把预测库存转成订单。

## 3. 如何理解这些结构

多数规则利用“订单真正到货前，还可能剩下多少库存”来压缩当前现货与有序在途向量。另一类直接对这些库存分量加权，再使用分段响应；Exponential L1 r3 则用小型神经网络直接映射状态到订单。参数搜索允许这些近似适配本轮的50期成本目标。

确定性 stationary 在这里指相同当前状态始终返回相同动作。识别某些备货状态仍可符合这一要求；相同状态在销售期重现时也必须得到同样的动作。解释一个分支为“备货”并不意味着函数可以读取隐藏的时期计数。

预测更复杂、公式更精确，都不能单独保证整体成本更低：最终订货响应、开发样本、有限数值搜索与需求取整也会影响表现。完整成绩应同时看三次生成的成本与变异，而不是按结构复杂度判断优劣。本轮没有最优成本基准，不能将相对经典基线或历史 AHD 的差距解释为最优性差距。

L1终稿通常只保留订货函数和固定参数，不包含生成期的模拟或优化过程。因此，仅凭最终函数无法核实其内部开发目标是否完全符合环境；本文的最终源码审查与统一外部测试有各自明确的范围。

## 4. 源码审查依据

- [第一组规则详解及原始笔记链接](/Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/policy_design_comparison.md)
- [Poisson r2/r3 审查](/Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/policy_notes_poisson_repeats.md)
- [Normal r2/r3 审查](/Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/policy_notes_normal_repeats.md)
- [Exponential r2/r3 审查](/Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/policy_notes_exponential_repeats.md)
- [全部成本、有效性与资源记录](/Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/report.md)
