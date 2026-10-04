# 首批三个策略的源码审阅

审阅对象：`l1_poisson_r1`、`l1_normal_r1`、`l2_poisson_r1`。本记录说明冻结程序的数学结构、时序和 stationary 性质；性能数字由统一评分报告提供。三个冻结程序的源码审阅均已完成；未修改提交算法。

## 1. `l2_poisson_r1`：投影库存矩与有限初始化的联合设计

- 冻结源码：[policy.py](/Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/sessions/l2_poisson_r1/policy.py:1)。
- 原始生成记录：[result.json](/Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/sessions/l2_poisson_r1/result.json)。
- SHA-256：`3e2c0c91ebd5da94da4691cbcae33d10933c8b2ba9a0c12794ccd9689548220b`；与生成记录一致。

### 决策公式

先预测本期订单在 L 期后到货前，系统剩余库存的均值 m_L 和方差 v_L，再订购：

`q = min(q_max, max(0, μ + a√μ − b·m_L + c√v_L))`。

其中 a、b、c 是初始化时选定的三个常数；q_max 是程序自身设置的很大保护上限，约为百万数量级。m_L 的反馈减少已有库存较多时的订货，v_L 项修正预测不确定性。每期计算量与 L 成正比。

投影用正态近似逐期传播库存正部的前两阶矩。若当前投影库存的均值、方差为 m、v，需求为 Poisson(μ)，则令 r=m−μ、s=√(v+μ)、z=r/s，近似更新为：

`m′ = s φ(z) + r Φ(z)`；

`v′ = (s²+r²) Φ(z) + r s φ(z) − (m′)²`。

每次需求扣减后，再把下一期确定到货的在途订单加到均值。循环 L 次，前 L−1 次接入旧订单，最后一次之后才轮到本期新订单。这是对包含缺货截断的库存分布的近似，未把它声明为精确 Poisson 动态规划。[投影实现](/Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/sessions/l2_poisson_r1/policy.py:203)。

### 初始化和搜索

`design(params)` 使用 6000 条固定种子的真实 Poisson 需求路径，每条 50 期，运行三轮小规模 differential evolution：先调三个常规订货参数，再调两个备货参数，最后局部细调三个常规参数。共五个独立可调常数。[模拟及搜索](/Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/sessions/l2_poisson_r1/policy.py:28)。

两个备货参数决定首个销售期的现货，以及之后 L−1 个在途到货量。策略在现货接近零、在途恰好匹配初始备货序列时，返回该序列的下一个订单。这能从全零初始状态构造所选销售初态。[初始化状态识别](/Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/sessions/l2_poisson_r1/policy.py:180)。

这段初始化规则仍然是 stationary：它只比较当前库存和在途订单，不读取时点、阶段标记或调用计数器；相同状态始终得到相同动作。优化器和模拟器的随机数仅用于设计阶段，返回的动作函数不保留可变随机状态。

### 时序核查与局限

- **未发现到货时点错位。** 设计阶段的模拟先按本期到货后的库存订货，再扣本期需求并计算费用，随后接入下一期到货；这与统一环境相符。初始化模拟直接从所设计的首个销售状态开始，与 L 个零需求备货期能够建立的状态一致。
- **设计目标与部署规则存在一个条件性差别。** 设计模拟在销售期始终使用常规投影公式；实际提交函数会在销售期重新遇到某个备货匹配状态时再次执行备货分支。因此，如果这种状态重现，调参模拟与完整提交策略的行为不同。是否发生及频率尚未量化；它不构成非平稳行为。
- **设计阶段异常会触发默认参数回退。** 整个优化过程包在 `except Exception` 中，异常时同时恢复三个常规参数和两个备货参数。源码未单独报告是否触发了回退；初始化耗时和结果需结合统一执行记录判断。

## 2. `l1_poisson_r1`：固定投影库存均值反馈

- 冻结源码：[policy.py](/Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/sessions/l1_poisson_r1/policy.py:1)。
- 原始生成记录：[result.json](/Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/sessions/l1_poisson_r1/result.json)。
- SHA-256：`0426285529394c174fbc083480ff83a6775f12a147278cbe711d760c38d49bf5`；与生成记录一致。

### 决策公式

常规订货为：

`q = clip(99.5 − 0.78·m_6, 0, 99.5)`。

m_6 是从当前到货后的状态出发，经过六次需求、依次接入五个旧在途订单后，预测的剩余库存均值。预测仍采用上一节的正态正部两阶矩递推，不过每步加入的**有效需求方差设为 80**。真实 Poisson(100) 的方差为 100；80 是该启发式内部的近似参数，不代表环境分布发生了变化。[常规投影和动作](/Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/sessions/l1_poisson_r1/policy.py:46)。

它对预测库存均值施加固定的 0.78 倍负反馈，没有 L2 Poisson 策略中直接增加 `c√v_L` 的项；方差仍通过正部矩递推间接影响 m_6。99.5 的订货上限由该策略自行选择，环境没有给它这个容量约束。

### 有限初始化

六个备货订单固定为 `(101, 96, 96, 96, 96, 96)`。从全零状态执行后，首个销售期到货后的现货为 101，未来五期到货量各为 96。策略通过当前现货为零、在途匹配已建立的前缀来识别这些状态；备货分支可返回 101，因此 99.5 仅是常规分支上限。[状态识别](/Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/sessions/l1_poisson_r1/policy.py:17)。

源码没有设计器或部署时参数搜索。所有参数均已固定；每次调用只执行长度为六的预测循环及少量状态比较。

### 时序核查与局限

- **未发现到货时点错位。** 六次扣需求之间只接入五个旧订单，最后得到本期新订单到货之前的剩余库存，符合 L=6 的接口。
- **为确定性的 stationary 规则。** 它没有在线随机数、调用计数或可变全局状态。备货分支仅依赖当前状态；若销售期再次出现同一状态，也会给出同一备货动作。
- **预测方差与真实需求方差不同。** 这是明确的近似参数，可能补偿矩闭合和反馈公式的偏差；单看源码不能断言这一调整改善了多少成本。
- **极大库存状态有独立保护分支。** 当前现货或任一在途量超过一百万时返回零订单。这是该策略的数值保护决策，环境仍保留全部库存。
- 最终源码没有附带调参模拟器，因此这里未对其开发阶段模拟与最终策略之间的一致性作额外断言。

## 3. `l1_normal_r1`：分阶段库存投影与分段线性反馈

- 冻结源码：[policy.py](/Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/sessions/l1_normal_r1/policy.py:1)。
- 原始生成记录：[result.json](/Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/sessions/l1_normal_r1/result.json)。
- SHA-256：`483a2a4913e3e2c705e062fd5af57a151de3ed057db799d53f594bde03c86136`；与生成记录一致。

### 状态压缩与决策公式

先把当前现货 I 和五个在途订单 P_1,…,P_5 压缩成一个投影剩余量 y：

`y_0 = max(I − d_0, 0)`；

`y_(j+1) = max(y_j + P_(j+1) − d_(j+1), 0), j=0,…,4`。

六个有效需求扣减量为：

`d = (75.4734, 93.3260, 98.7350, 98.7496, 98.7497, 98.7469)`。

这些数是预测公式里的固定启发式参数，不是环境每期需求的真实均值。不同位置对应的是距本期订单到货的相对距离；每一期都使用同一组 d，因此它没有引入时间依赖。逐步取正部保留了到货先后的影响，不能简单合并成“现货加所有在途”。[投影实现](/Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/sessions/l1_normal_r1/policy.py:73)。

若最终 `y≤1e−10`，订货 `q=87.991`；否则按下表做线性插值，`y≥160` 时订货为零：

| y 的结点 | 0 | 5 | 10 | 20 | 40 | 80 | 160 |
|---|---:|---:|---:|---:|---:|---:|---:|
| 正投影分支的 q | 86.0756 | 85.0058 | 84.2788 | 82.3808 | 77.5007 | 53.6510 | 0 |

常规分支随投影库存增加而减少订货，包含约 1.9154 的近零跳跃：完全耗尽投影库存时订购 87.991，刚超过零阈值时约为 86.0756。这是提交规则中的明确分支；不能把整段规则概括成单一线性反馈。[插值与零点分支](/Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/sessions/l1_normal_r1/policy.py:48)。

### 有限初始化

六个备货订单为：

`(103.36740662, 89.84154688, 88.11440108, 87.20817980, 87.33351561, 86.01063776)`。

首个销售期的现货为第一项，后续五个在途到货量为其余五项。当前现货接近零且在途匹配这些前缀时，策略返回下一项。前三个备货量可超过常规分支的 87.991 上限；该上限并不是环境容量。[初始化识别](/Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/sessions/l1_normal_r1/policy.py:36)。

### 时序核查与局限

- **未发现到货时点错位。** 对本期现货先扣一次需求，再依次加五个旧订单、分别扣后续需求；总计六次需求后预测本期新订单到货前的余量，符合 L=6 的环境。
- **为确定性的 stationary 规则。** 全局数据都是固定常量或元组；没有在线随机数或跨次调用更新。初始化分支的局部变量 `stage` 用来匹配当前状态，不是保存下来的时间计数器。
- **原点附近不连续。** `y≤1e−10` 的额外订单量使浮点误差或轻微状态变化在阈值附近可能改变约 1.9154 个订单单位。这是需要解释的策略结构，源码本身没有显示其导致非法动作。
- **这是确定性投影代理。** 它没有像两个 Poisson 程序那样传播库存方差；需求不确定性通过 d 的取值及分段反馈间接体现。最终文件也未附带调参模拟器，因此没有据此推断开发模拟的精确一致性。

## 4. 三份源码的共同特征

三者都利用当前在途订单的到货顺序预测新订单到货前的库存，并为全零初始状态设置了一组固定备货动作。它们的备货识别均由当前状态决定，所以仍是 stationary 策略。三者的常规决策表达分别是：

| 冻结程序 | 常规库存预测 | 从预测量到订单的映射 | 部署时设计搜索 |
|---|---|---|---|
| L1 Poisson | 两阶矩递推，有效方差 80 | 投影均值的固定线性负反馈 | 无 |
| L2 Poisson | 两阶矩递推，方差增量 μ | 均值负反馈加方差平方根项 | 有，场景初始化时 |
| L1 Normal | 六个有效需求量的逐期确定性投影 | 带零点跳跃的分段线性反馈 | 无 |

这些是已提交程序的源码归纳。任何优劣判断应以相同需求路径上的统一评分为依据；这里的时序核查没有发现上述三份提交存在 L 与 L−1 的接口错配。
