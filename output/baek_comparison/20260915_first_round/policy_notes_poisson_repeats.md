# Poisson 后续重复的源码审阅

审阅范围：`l1_poisson_r2`、`l2_poisson_r2`、`l1_poisson_r3`、`l2_poisson_r3`。这里只读取冻结的 `result.json` 和 `policy.py`，说明数学结构、到货时序、备货行为和确定性 stationary 性质；未读取评分结果，未运行生成程序，未修改任何提交策略。源码结论不替代统一执行器的实际有效性检查。

## 1. `l2_poisson_r2`：精确单步 Poisson 余量函数与两参数截断投影规则

- 冻结源码：[policy.py](/Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/sessions/l2_poisson_r2/policy.py:1)。
- 原始生成记录：[result.json](/Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/sessions/l2_poisson_r2/result.json)。
- SHA-256：`cfdd9b12ea25e0ddec4600382c025ba0ff282ca74392ba5e18d9615e50bbcbe4`。文件字节的哈希与生成记录一致，源码文本也与记录中的 `final_code` 完全一致。

### 决策公式

令 `D~Poisson(μ)`，`F(n)=P(D≤n)`，`F(−1)=0`。对于确定的非负实库存 x，程序使用：

`g(x) = E[(x−D)⁺] = x·F(floor(x)) − μ·F(floor(x)−1)`。

它先预存 CDF 表，再计算单步预计剩余库存。这一公式对整数需求和实数库存都成立；不是把实数库存四舍五入后计算。对于远超表上界 `K=ceil(μ+12√μ+20)` 的库存，使用 `g(x)≈x−μ` 的极小尾部近似。[CDF 表及向量函数](/Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/sessions/l2_poisson_r2/policy.py:15)。

给定本期到货后的库存 I 和旧在途订单 P_1,…,P_(L−1)，压缩预测为：

`y_0=g(I)`；

`y_j=g(y_(j−1)+P_j), j=1,…,L−1`；

`q = min(C, max(0, S−y_(L−1)))`。

S 是目标水平，C 是策略自行选择的订货上限，二者都由 `design(params)` 固定。环境本身没有 C 这个容量约束。常规计算量为 O(L)，只需标量查表与算术运算。[返回动作函数](/Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/sessions/l2_poisson_r2/policy.py:146)。

### 设计阶段和备货

设计器读取固定的 L、μ、持有费 h、缺货费 p 和销售长度 T。固定随机种子 104729 生成 9000 条 T 期 Poisson 需求路径，所有候选共享这些路径。先用正态分位数近似 `μ+√μ·Φ⁻¹(p/(p+h))` 初始化 S；再进行一维有界搜索，最后用固定种子 130363 的 differential evolution 联合优化 S 和 C。[搜索过程](/Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/sessions/l2_poisson_r2/policy.py:83)。

搜索区间为 `S∈[max(0,μ−5√μ), μ+7√μ]`，`C∈[max(10⁻⁹,μ−5√μ), μ+8√μ]`。本批 μ=100 时分别是 `[50,170]` 和 `[50,180]`。这些是搜索约束，不能从源码推断最终选中的参数值。

每个候选从全零库存和 L 个空到货槽开始，模拟 L 个零需求、无费用的备货期，再模拟 T 个收费销售期。备货期和销售期使用完全相同的动作公式，没有独立的备货序列或阶段识别分支。从全零状态的第一个动作为 `min(C,S)`，此后的备货动作由逐步建立的在途状态决定。[完整初始过程](/Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/sessions/l2_poisson_r2/policy.py:43)。

### 时序、stationary 性质与近似

- **到货时序符合接口。** 每期先弹出并接收最旧订单，剩余 L−1 项进入预测；动作确定并接入队列后扣当期需求。预测包括 L 次需求和 L−1 次旧到货，定位在本期新订单到货之前。备货期不扣随机需求，也不计算费用。
- **返回策略是确定性的 stationary 函数。** 它只读取当前 I、P 和固定的 S、C、μ、CDF 表；不更新数组、不保存计数器、不读取时钟。随机数和优化器仅在设计阶段使用，并显式设种子。在固定软件环境和固定 params 下，设计过程没有时间预算触发的随机停止条件，也不读取其他场景的数据。`horizon` 只决定离线调参目标，未成为在线倒计时。
- **精确的是单步 g，不是多步预计库存。** 每次把随机剩余库存替换成一个均值，再调用 g，遗漏了剩余库存分布及其不确定性。理想精确 g 是递增凸函数，因此这种逐步代入均值的代理在相同固定到货条件下会低估真实预期余量；不能把它称为精确 L 步 Poisson 预测。S、C 的模拟调参可能吸收部分偏差，但本记录未查看性能。
- **没有 r1 的销售期重新触发备货规则问题。** 本程序没有独立初始化动作分支，设计模拟和部署都调用同一投影规则。不过向量版和标量版的尾部切换边界存在细小差别：向量版在 `floor(x)>K` 时改为 `x−μ`，标量版在 `x>K` 时改用该式。因此 `(K,K+1)` 区间的实现形式略不同；K 位于均值上方约 12 个标准差以上，这不是到货时序错误。
- **动作有有限非负保护。** 固定参数范围内 S、C 有界，常规动作总在 `[0,C]`；极大库存相加溢出为正无穷时返回零。源码没有发现可以由合法普通状态触发的非法动作。
- **优化异常会静默保留当时最优候选。** 一维和联合搜索在同一个 `try/except Exception` 中，异常后继续返回已保存的参数；初始候选模拟在该异常处理之外。源码不报告是否走了回退。实际设计耗时和执行成功与否须由独立执行记录判定。

## 2. `l1_poisson_r2`：偏置需求均值的两阶矩投影

- 冻结源码：[policy.py](/Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/sessions/l1_poisson_r2/policy.py:1)。
- 原始生成记录：[result.json](/Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/sessions/l1_poisson_r2/result.json)。
- SHA-256：`ebbe0a69288d0179c5facec8fbcdaba9205850cee9b91bc5c8943abafd9697bb`。文件字节哈希与生成记录一致，源码文本与 `final_code` 完全一致。

### 决策公式与近似

常规订货为 `q=max(0,100.375−m_6)`。m_6 使用长度为六的正态正部矩递推预测：初始 m=I、v=0，每步设 `r=m−100.9`、`s=√(v+100)`、`z=r/s`，然后更新：

`m′=sφ(z)+rΦ(z)`；

`v′=max(0,(s²+r²)Φ(z)+rsφ(z)−(m′)²)`。

前五步需求之后分别把 P_1,…,P_5 加到投影均值；第六步需求后直接使用 m_6 计算订单。[矩递推与动作](/Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/sessions/l1_poisson_r2/policy.py:32)。

真实需求是 Poisson(100)，而内部预测采用**有效均值 100.9、方差 100**。尽管源码注释称为 matched normal moments，均值实际上加了 0.9 的偏置，应当把它视为启发式预测参数。与 r1 的方差 80、残余均值反馈系数 0.78 相比，本次使用真实需求方差和系数 1，并更改目标常数。它仍然把经缺货截断后的库存分布近似为只保留两阶矩的正态代理，没有显式表示零点概率质量。

在精确算术下 m_6≥0，因此常规订单不超过 100.375；这是公式的结果，不是物理订货容量。CDF 通过 `0.5*(1+erf(...))` 计算，极小尾部可能有浮点消减误差；最终仍显式截断负订单，方差也截断到非负。

### 有限初始化

六个固定备货订单为：

`(101,96.16805647,95.97646665,96,95.51355986,95.58825429)`。

当前现货绝对值≤10⁻¹⁰、五个旧在途槽与备货序列的某一前缀逐项相差≤10⁻⁸时，返回下一个备货量。从全零初态执行 L=6 个零需求期后，首个销售期现货为 101，五个旧在途量是其余五项。[备货识别](/Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/sessions/l1_poisson_r2/policy.py:20)。

这里的 k 是每次调用重新计算的状态匹配索引，不是隐藏的时间或调用次数。销售期若再次遇到同一库存/在途状态，也会触发同一分支。最终文件只有固定策略，没有设计器或调参模拟器，因此本次源码审阅不判断开发模拟与部署之间是否存在初始化分支差异。

### 时序、stationary 性质与异常动作

- **未发现到货错位。** 六次需求之间接入五个旧订单，预测到本期新订单在六期后到货之前，与统一接口相符。
- **确定且 stationary。** 全局对象仅有不可变常数和备货元组；每次函数将传入在途复制成局部元组，不修改环境输入，没有随机数、时钟、计数或跨调用更新。
- **合法普通状态下未发现非法动作。** 本期现货或任意在途量超过一百万时直接返回零，防止极大值的矩运算溢出；其余合法状态使用有限数值运算并返回非负实数。备货分支可以返回 101，高于常规动作的名义上界，这属于明确的策略分支。
- **L1 参数完全固定。** 它按既定 L=6、μ=100 的核心场景设计，没有 `design(params)`，也没有在部署时重新调参。

## 3. `l2_poisson_r3`：三参数矩投影与局部样本均值优化

- 冻结源码：[policy.py](/Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/sessions/l2_poisson_r3/policy.py:1)。
- 原始生成记录：[result.json](/Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/sessions/l2_poisson_r3/result.json)。
- SHA-256：`bdda953037fd1cdea85815c414e244b744b93657fc61675f2f49c32bc87807b8`。文件哈希与生成记录一致，源码文本与 `final_code` 完全一致。

### 决策公式

三个固定参数分别为缓冲目标 B、反馈系数 k 和预测偏移 s。令 `d̃=μ+s√μ`，对当前到货后的 I 和 L−1 个旧在途订单进行 L 步正态正部矩递推，得到新订单到货之前的预计余量 m_L。最终动作是：

`q=max(0, μ+k(B−m_L))`。

投影初值为 m=I、v=0；每步取 `r=m−d̃`、`σ=√(v+d̃)`，利用正态正部的前两阶矩更新 m、v，并在前 L−1 步之后加入相应旧订单。[在线递推与订单](/Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/sessions/l2_poisson_r3/policy.py:147)。

偏移 s 同时改变预测需求的均值和方差增量；真实环境的需求均值与方差仍均为 μ。这个模型通过偏移需求矩和反馈系数修正库存预测，而不是精确计算多步 Poisson 库存分布。等价的线性截距是 `μ+kB`，不是固定 μ，也没有 r1 中独立的 `c√v_L` 加项；v_L 只通过矩递推间接影响 m_L。

### 设计和备货

`design(params)` 用固定种子 731291 生成 10000 条 T 期真实 Poisson 需求路径。它从全零现货和空在途开始，对每个候选模拟 L 个零需求备货期和 T 个销售期；备货期与销售期都使用同一动作公式。[候选模拟](/Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/sessions/l2_poisson_r3/policy.py:16)。

初始参数为 `B=0.75√μ·Φ⁻¹(p/(p+h))`、k=0.9、s=0.2。L-BFGS-B 从这一个初值局部优化，设置 maxiter=18、maxfun=88、maxls=10，参数区间为：

- `B∈[−2√μ,5√μ]`；
- `k∈[0.1,1.6]`；
- `s∈[−0.5,1]`。

只有返回参数有限、目标有限且样本均值成本不高于初值时才采用优化结果；优化异常则退回初值。接受条件没有要求优化器报告收敛成功。固定搜索设置并不等于源码保证初始化必在 30 秒内完成；本审阅未执行设计器或读取其计时。[初值、边界和搜索](/Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/sessions/l2_poisson_r3/policy.py:90)。

它不单独储存备货序列，也不识别备货阶段。全零状态下的初始订单大致为 `max(0,μ+kB)`，极小正态尾部余量可能带来微小修正；后续备货由当前在途状态决定。T 只用于固定场景的设计目标，在线函数没有剩余销售期计数。

### 时序、stationary 性质与近似

- **`pipeline` 加 `last_order` 的模拟写法时序正确。** 模拟内部用 L−1 列保存旧在途，另存上期动作。进入下一期时，先接收原在途第一列，再左移并把上期动作接在末尾。因此 t 期新下的订单在 t+L 期到货；动作看到的仍是本期到货后的库存和 L−1 个未来到货槽。预测中的 L 次需求、L−1 次旧到货与此一致。
- **确定且 stationary。** 设计只使用固定 params 和显式固定种子的本地样本；返回前把三个参数转成固定浮点数。在线函数将输入在途转为局部列表，不修改传入状态，不使用随机数、调用历史、时钟或计数器。
- **模拟和部署的尾部处理略有区别。** 向量调参函数始终使用 `scipy.special.ndtr` 和完整正部矩公式；标量部署函数在标准化净库存 `z≤−8` 时直接设均值、方差为零，在 `z≥8` 时直接使用未截断净库存的矩。尾部截断改善标量计算的数值稳定性，但两份代码不是逐位相同的计算；这不是到货顺序差异。
- **合法场景范围内未发现异常动作来源。** 本轮及公开设计范围的 L≥2，符合模拟对在途第一列的索引要求；d̃ 始终大于 1。现货或任意旧订单达到 10¹⁰⁰ 时在线函数直接返回零，最终动作还检查有限性和非负性。它不限制环境库存，也没有引入物理订货容量。
- **优化仍是有限样本上的局部搜索。** 公共随机数使相同参数的设计目标可重复，但有限样本、单初值和非光滑缺货费用仍限制优化精度；本记录不据此推断评分优劣或全局最优性。

## 4. `l1_poisson_r3`：方差增厚的矩投影和波动修正目标

- 冻结源码：[policy.py](/Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/sessions/l1_poisson_r3/policy.py:1)。
- 原始生成记录：[result.json](/Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/sessions/l1_poisson_r3/result.json)。
- SHA-256：`d0b8efaf6a42f6bb0b7cfb11dc6183be812ee656b17d5a3564d0379a567cadd7`。文件哈希与生成记录一致，源码文本与 `final_code` 完全一致。

### 决策公式与近似

本次仍逐步传播正态正部的两阶矩，但预测需求使用固定**有效均值 101.35、有效方差 143**，而真实 Poisson(100) 的均值、方差均为 100。投影初值为当前到货后的库存 I 和方差零；每步先扣有效需求、取正部矩，前五步之后依次加入五个旧在途订单，六步后得到 m_6、v_6。[矩预测](/Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/sessions/l1_poisson_r3/policy.py:53)。

目标水平随预测标准差变化，完整动作是：

`q=max(0,101.93+0.075(√v_6−10)−m_6)`，

等价于 `q=max(0,101.18+0.075√v_6−m_6)`。这包含对余量均值的单位负反馈和对余量标准差的正修正。10 是固定的标准差参照值，不是当前周期的观测需求或时间变量。[波动修正与动作](/Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/sessions/l1_poisson_r3/policy.py:67)。

正部矩函数通过 `erfc` 计算 CDF；标准化净库存 z≥8 时近似为未截断正态的矩，z≤−12 时近似为零库存；中间区间使用完整公式，并把因数值误差可能产生的负方差截断为零。143 和 101.35 应视为启发式有效矩，尾部截断也只是计算近似，不能解释成真实需求分布改变。[正部矩实现](/Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/sessions/l1_poisson_r3/policy.py:15)。

### 备货、时序与 stationary 性质

- **本次没有独立备货分支。** 从全零状态开始，L 个零需求备货期始终使用同一个投影动作；第一个订单约为 101.18，后续动作随逐步建立的在途状态变化。它不会匹配预先给定的备货序列。
- **到货顺序符合接口。** 六次需求之间依次接入五个旧订单，投影终点是本期新订单在六期后到货之前，没有额外计入当前订单或再次计入本期已到货的旧订单。
- **确定且 stationary。** 参数均为固定常量，辅助矩函数是纯计算；在途列表仅在当前调用内复制和读取。没有随机数、计数器、时钟、历史缓存或可变全局状态。
- **合法普通状态下未发现非法动作。** 现货或任意在途量超过一百万时直接返回零；其余计算中方差有非负保护，最终负订单截断为零。固定 L=6、μ=100 的适用范围与当前 L1 场景一致。
- **没有部署时搜索。** 最终文件不包含 `design(params)` 或调参模拟器；源码审查只能描述这份冻结规则，不能由此还原其开发阶段模拟或证明最优性。

## 5. 四个后续重复的结构对照

四份冻结源码均已核对哈希并完成审阅；未发现 L 与 L−1 的接口错配、隐藏的在线时间状态或明显非法动作来源。它们的差异集中在如何近似未来剩余库存、如何把余量转成订单，以及是否单独安排备货。

| 程序 | 余量预测 | 常规订单公式 | 备货方式 | 部署时设计搜索 |
|---|---|---|---|---|
| L1 Poisson r2 | 正态正部两阶矩，有效需求均值 100.9、方差 100 | `max(0,100.375−m_6)` | 固定六项序列，按当前状态识别 | 无 |
| L1 Poisson r3 | 正态正部两阶矩，有效需求均值 101.35、方差 143 | `max(0,101.18+0.075√v_6−m_6)` | 所有期共用同一公式 | 无 |
| L2 Poisson r2 | 单步精确 Poisson 余量函数，多步代入均值 | `min(C,max(0,S−y))` | 所有期共用同一公式 | 9000 条路径，一维搜索后两参数联合搜索 |
| L2 Poisson r3 | 正态正部两阶矩，有效需求均值和方差均为 `μ+s√μ` | `max(0,μ+k(B−m_L))` | 所有期共用同一公式 | 10000 条路径，三参数局部搜索 |

这些结论只来自最终程序。统一有效性验证、初始化耗时和成本比较由独立实验记录给出；本记录没有用评分来选择或修复任何策略。首轮 r1 的结构见[首批源码审阅](/Users/fenghua/Desktop/research/LLM/test/test/AHD4Inventory/output/baek_comparison/20260915_first_round/policy_notes_first_draws.md)。
