# L2 Exponential r1：冻结策略的源码审查

## 来源与审查范围

- 最终源码：[policy.py](/Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/sessions/l2_exponential_r1/policy.py:1)。
- SHA-256：`b8211a44683af33150d35e8129f93f7434fd63a6fb5a866f00fa07cb30077191`，已与 `result.json` 的冻结代码哈希核对一致。
- 必要接口：[环境模拟器](/Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/examples/inventory/baek_comparison/environment.py:262)、[需求分布定义](/Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/examples/inventory/baek_comparison/prompts.py:55)。

本审查仅阅读冻结源码及接口，没有读取评分、执行生成策略、重新调参或调用模型。它解释算法结构，不对实测成绩作结论。

**概括：按实例模拟调参的、带订货上限的加权线性规则，另加入一个确定性剩余库存预测项。** 初始化从 capped base-stock 候选出发，优化在途位置权重，最后尝试增加预测库存惩罚；它不是精确动态规划。

## 1. 最终动作

设 I 为当前到货后的库存，Pⱼ 为 j 期后到货的既有订单。程序先用每期固定需求 d̄ 预测：

\[
r_0=(I-\bar d)^+,\qquad
r_j=(r_{j-1}+P_j-\bar d)^+,\quad j=1,\ldots,L-1.
\]

最终订货规则为

\[
q(I,P)=\min\left\{C,\left[A-\alpha I-
\sum_{j=1}^{L-1}\beta_jP_j-\kappa r_{L-1}\right]^+\right\}.
\]

A、C、α、所有 βⱼ 和 κ 在 `design(params)` 内固定；权重非负。κ 可以为零，从而退回纯加权线性规则。L≥2 时有 L+3 个标量参数（包括 κ）。动作计算只需 O(L) 加减乘及截零，不进行模拟或优化。[参数冻结与最终函数](/Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/sessions/l2_exponential_r1/policy.py:379)

规则使用有到货顺序的整个在途向量，不只是总库存位置。对固定参数，增加 I 或任一个 Pⱼ 都不会提高动作：直接惩罚与预测库存惩罚都单调。C 是模型自行选择的策略参数，不是环境的订货容量；最终搜索通常限制 C 在 `[0.2μ,3μ]`。环境仍允许任意非负有限实数动作。

## 2. Rounded Exponential 与预测近似

程序生成 `D=rint(−μ·log(1−U))`，正确对应指数分布均值/scale 为 μ，然后四舍五入。它未将 μ 误作 rate。[样本生成](/Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/sessions/l2_exponential_r1/policy.py:16)

其均值公式也是正确的：整数 k≥1 时，`P(D≥k)=exp(−(k−0.5)/μ)`，故

\[
\bar d=E[D]=\frac{e^{-0.5/\mu}}{1-e^{-1/\mu}}
=\frac{1}{2\sinh(1/(2\mu))}.
\]

实际实现用 `expm1` 稳定计算分母。名义 μ 与舍入后的均值略有区别；预测项使用 d̄，截距和订货上限则用 μ 作尺度化参数，这不改变模拟需求的定义。

**r 并不是真实的期望剩余库存。** 它将每次随机需求替换为均值，再逐期计算 `(库存−需求)⁺`。例如 I=d̄、无在途时，一期预测为零，但随机需求有低于 I 的概率，真实期望剩余量为正。最终剩余库存是未来需求向量的凸函数，因此在各未来期都按销售需求分布运行时，Jensen 不等式给出这个确定性预测不高于真实期望的关系。

因此 κ 项只是一种额外的状态特征；参数通过随机需求模拟拟合，不能将该项称作精确的多期库存预测。相比纯加权规则，它允许对“已有库存足以覆盖若干期平均需求”的状态施加额外惩罚。它不会在空库存、空在途中凭空产生正的预测库存。

## 3. 初始化优化与数据使用

| 阶段 | 源码中的实现 |
|---|---|
| 合成路径 | 训练：4,096 条 scrambled Sobol 路径，seed=910+L；开发验证：2,048 条，seed=1910+L；每条 H 维 |
| Capped base-stock | 优化 `min(C,[S−I−ΣP]⁺)` 的 S、C；差分进化最多 10 代，`popsize=5`，seed=33+L |
| 平滑位置权重 | L=2 时直接优化单个在途权重；L>2 时用 `β(x)=u·exp(vx+w·x(1−x))` 表达位置权重；差分进化最多 12 代，seed=73+L |
| 多起点局部优化 | 全局候选、base-stock 候选和两个启发式候选分别做有界 Powell；第一个最多 4 次迭代，其余最多 2 次 |
| 全部在途权重 | 放开各 βⱼ，做最多 3 次 Powell 迭代；与初始候选比较后择优 |
| 增加预测项 | 从 κ=0 开始，再做最多 3 次 Powell 迭代；与 κ=0 候选比较后择优 |

比较候选的指标均为 `0.6×训练集平均总成本+0.4×开发验证集平均总成本`；优化器本身的目标主要是训练集成本。两套样本来自不同 scramble，但每套 Sobol 路径之间有准蒙特卡洛结构，不应表述为普通的独立随机路径。[搜索主体](/Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/sessions/l2_exponential_r1/policy.py:104)、[后续选择](/Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/sessions/l2_exponential_r1/policy.py:320)

源码中的 `validation_demands` 反复用于选参数，属于算法开发数据，不能将该集合上的成绩作为独立测试结果。没有读取仓库的现有训练/测试数据，也没有在动作阶段使用样本中的未来需求。

这些是固定迭代预算的启发式数值优化，没有全局最优保证。Powell 的 `maxiter` 限制迭代次数，未直接限制目标函数调用次数或秒数；代码也没有内部计时截止。因此仅凭源码不能保证每个参数实例都在 30 秒初始化目标内完成。本审查不读取外部计时结果。

## 4. 到货时序、备货期与计分

**三套内部模拟器与我们使用的事件顺序一致。** 循环开始时的 inventory 已含本期到货，pipeline 长度为 L−1；先按此状态下单，再发生销售需求及计费，最后把旧 pipeline 首单加入库存，左移并放入新订单。这是把下期决策前的到货写在本期循环末尾，没有把当前到货算两次。[完整模拟器](/Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/sessions/l2_exponential_r1/policy.py:271)

以 L=2 为例，本期 q 在下一期仍处于唯一在途位置，要到下下一期决策前才到货，新订单延迟恰为 2。一般情况下同理为 L。最后一轮循环后还会做一次队列更新，但其后没有决策或计费，对目标值没有影响。

所有模拟均从零库存/零在途开始，运行 L+H 期。前 L 期不执行销售与计费，相当于零需求备货；后 H=50 期按期末库存和当期丢失需求计费。没有订货费、销售前持有成本、额外终端惩罚或残值。

内部累计 `期末库存+(p/h)×丢失需求`，即真实总成本除以正数 h。在提示规定 h=1 时与环境成本相同；即使 h 为其他正数，这种统一缩放也不改变所比较策略的最优解。`normalized_p=clip(p/h,2,10)` 只用于构造启发式起点，模拟目标仍用未截断的 `p/h`。[成本与参数](/Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/sessions/l2_exponential_r1/policy.py:7)

备货期使用同一个规则，预测项仍每期扣除 d̄，而实际备货需求为零。这是 stationary 状态特征的近似，不是备货模拟错误；参数优化已经把真实备货过程包括在内。空状态首单为 `min(A,C)`。规则没有时间计数器，也不会在接近第 50 个销售期时根据剩余时间改变决策；H 只通过初始化目标影响参数。

## 5. 确定性与实现边界

从源码看，Sobol 和差分进化都使用固定 seed，后者 `workers=1`；Powell 不引入随机抽样。返回函数只读取固定浮点常数、不可变的在途权重 tuple 和当前输入，不改变输入、闭包或随机状态，没有跨调用记忆。固定运行库下具备确定性和所要求的 stationary 结构。

动作侧的标量公式与最终 `simulate_full(...,use_projection=True)` 的矢量公式一致；差别主要是求和/点积顺序引起的浮点舍入。动作通过零与 C 截断，极大有效状态即使使中间扣减成为负无穷，也会返回零。代码适用域是提示规定的 L≥2、μ>0、h>0；本审查不外推到不符合这些条件的参数或错误长度的在途输入。

有两项可见的优化实现限制：

- 曲线权重可能超出后续单独权重的 `[0.05,2.5]` 边界，但 `initial_full` 没有先按 `full_bounds` 截断；后续保留初始候选时，也可能保留这些边界外权重。它们仍是合法策略参数，因此不是环境契约错误；不过不能把后续边界描述为所有最终候选的统一限制，且起点越界可能影响局部优化表现。
- 程序未检查各优化结果的 `success`，也未设置优化失败的异常恢复。有限迭代时返回可用参数并不证明已经收敛；实际抛异常则可能使整个初始化失败。源码审查不能确认特定实例上是否发生这些情况。

本次未发现提前到货、少计备货期、提前看到需求、成本目标不一致或跨调用状态的直接源码错误。主要解释限制是受限参数族、流体预测近似、多阶段有限搜索及初始化计算量；这些不能直接当作任何实测差异的原因。冻结策略应保持原样，独立成绩另行报告。
