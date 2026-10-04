# 易腐库存：今晚筛查的可执行定义与来源核对

## 定位

今晚主实验采用用户附件建议的 12 个因子组合：寿命 m∈{3,4,5}、提前期 L=2、实际总需求 CV∈{1.5,2}、FIFO 平均需求比例 f∈{0,0.5}。这是一项预定小网格筛查，不是先测 Baek 后只保留其失利的实例。完整网格都须保留在结果表。

**该网格沿用论文文字的实际 CV 定义，但不能声称精确复现 Temizöz 等人的发表数值。** 核对发现论文文字和目前公开源代码的两处实质差异，下文分别保留，避免把不同需求难度的结果混在一起。

## 论文与源代码的可核事实

[Temizöz 等人的公开稿 §6.1 与 Appendix B](https://arxiv.org/html/2011.15122v6) 给出 μ=4、h=0、p=w=100，需求以 Adan–van Eenige–Resing 的前两矩拟合法产生，并采用 FIFO/LIFO 两路需求。论文把 cvr 称为变异系数，库存位置上限为 m+L 期总需求的 newsvendor 分位数。寿命是到货后可销售的期数，不包括在途等待；状态含年龄库存和在途订单。

本次代码核对固定在公开 DynaPlex-legacy 提交 `087b3f2fc07b8a9dd57b76bbf7d393be0141e1ec`。这证明当前公开实现，不证明它与论文原始运行二进制逐字相同。

- [模型头文件](https://github.com/DynaPlex/DynaPlex-legacy/blob/087b3f2fc07b8a9dd57b76bbf7d393be0141e1ec/src/lib/models/models/perishable_systems/mdp.h) 将 `cvr` 注释为方差除以均值的平方根。
- [模型实现](https://github.com/DynaPlex/DynaPlex-legacy/blob/087b3f2fc07b8a9dd57b76bbf7d393be0141e1ec/src/lib/models/models/perishable_systems/mdp.cpp) 设置 SD=`cvr*sqrt(mu)`。两路均值按 f 与 1−f 分配，方差也按这两个比例分配。因此总需求 SD/μ=`cvr/sqrt(mu)`；当 μ=4 时，配置 1.5 和 2 实际对应 CV=0.75 和 1。该文件计算库存上限时循环包含端点，累计的是 m+L+1 期需求。其事件实现等价于：先 FIFO，再 LIFO，再移除最老剩余库存，年龄下降一格，并让下期在途订单到达。
- [论文实验可执行文件](https://github.com/DynaPlex/DynaPlex-legacy/blob/087b3f2fc07b8a9dd57b76bbf7d393be0141e1ec/src/executables/perishables_paper_results/perishables_paper_results.cpp) 确实把 1、1.5、2 直接作为 `cvr` 配置传入，而非先乘以 √μ。
- [联合分布实现](https://github.com/DynaPlex/DynaPlex-legacy/blob/087b3f2fc07b8a9dd57b76bbf7d393be0141e1ec/src/lib/models/modelling/jointdiscretedist.cpp) 使用两个边际概率的乘积，即两路需求独立。它不是先抽取总需求再做二项分流。
- [离散分布实现](https://github.com/DynaPlex/DynaPlex-legacy/blob/087b3f2fc07b8a9dd57b76bbf7d393be0141e1ec/src/lib/models/modelling/discretedist.cpp) 给出 Adan 拟合的 Poisson、二项混合、负二项混合与几何混合分支。此次高 CV 主网格全部落在两个几何分布混合分支。

## 主实验定义

每期从已经收到本期到货的状态作决策。`age[j]` 表示剩余寿命 j+1 期的库存；`pipeline[k]` 表示 k+1 期后到货的订单。因此 L=2 时 `pipeline` 只有一个元素。今天订货在 t+2 期需求前到货；到货时剩余寿命为 m，可以参加 t+2 至 t+m+1 共 m 次需求满足。

本期流程：决策订货 → FIFO 需求从最老库存开始取货 → LIFO 需求从最新库存开始取货 → 缺口记作 lost sales → 最老未售库存报废 → 其余库存剩余寿命减一 → 接收下期到货，进入下一个决策状态。没有 backorder、采购费、固定订货费或最小订货量。

计分为每期 `100*lost + 100*waste`；h 默认为 0，但实现包含报废后幸存库存的持有成本。没有终端残值或终端强制报废。初态全零，丢弃 burn-in 后计算每期平均费用；warm-up 本身也执行策略。长度与训练/测试种子由运行器保存，不属于 simulator 隐藏常量。

FIFO 与 LIFO 需求分别独立且跨期 IID。给定总 SD=μ·CV，两路矩为：

- FIFO: mean=f·μ, variance=f·(μ·CV)²。
- LIFO: mean=(1−f)·μ, variance=(1−f)·(μ·CV)²。

给定某一路均值 ν>0、方差 v，令 a=(v−ν)/ν²。主网格 a≥1，定义 b±=1+a±√(a²−1)。以权重 1/b+ 抽取第一个几何分布，否则抽第二个；对应成功概率是 2/(2+νb+) 和 2/(2+νb−)，均在 {0,1,…} 上计数。零均值一路恒为零。

统一动作语义为：实数建议先限制到非负及剩余库存位置容量，再用 `np.rint` 取整（半整数舍入到偶数）。所有方法共享此投影。库存位置为全部年龄库存加全部在途量，上限是 m+L 期总需求的 p/(p+w)=0.5 分位数。因此这不是外加的参数个数限制，而是来自模型文字的有限动作域。`cap_mode="none"` 可以用于事后容量敏感性检查，不能混进主实验。

| instance | m | L | 实际 CV | f | 库存位置上限 |
|---|---:|---:|---:|---:|---:|
| perish_m3_L2_cv1.5_f0 | 3 | 2 | 1.5 | 0 | 17 |
| perish_m3_L2_cv1.5_f0.5 | 3 | 2 | 1.5 | 0.5 | 16 |
| perish_m3_L2_cv2_f0 | 3 | 2 | 2 | 0 | 14 |
| perish_m3_L2_cv2_f0.5 | 3 | 2 | 2 | 0.5 | 14 |
| perish_m4_L2_cv1.5_f0 | 4 | 2 | 1.5 | 0 | 21 |
| perish_m4_L2_cv1.5_f0.5 | 4 | 2 | 1.5 | 0.5 | 20 |
| perish_m4_L2_cv2_f0 | 4 | 2 | 2 | 0 | 18 |
| perish_m4_L2_cv2_f0.5 | 4 | 2 | 2 | 0.5 | 17 |
| perish_m5_L2_cv1.5_f0 | 5 | 2 | 1.5 | 0 | 25 |
| perish_m5_L2_cv1.5_f0.5 | 5 | 2 | 1.5 | 0.5 | 24 |
| perish_m5_L2_cv2_f0 | 5 | 2 | 2 | 0 | 22 |
| perish_m5_L2_cv2_f0.5 | 5 | 2 | 2 | 0.5 | 21 |

## 独立保留的公开代码口径

`scenarios(demand_mode="legacy_code", cap_mode="legacy_code")` 使用 SD=cvr√μ 和 m+L+1 期分位数。这是对公开代码的单独敏感性网格，不是主实验数值的替代标签。

| instance 配置名 | 实际 CV | 公开代码口径上限 |
|---|---:|---:|
| perish_m3_L2_cv1.5_f0 | 0.75 | 23 |
| perish_m3_L2_cv1.5_f0.5 | 0.75 | 23 |
| perish_m3_L2_cv2_f0 | 1 | 23 |
| perish_m3_L2_cv2_f0.5 | 1 | 23 |
| perish_m4_L2_cv1.5_f0 | 0.75 | 27 |
| perish_m4_L2_cv1.5_f0.5 | 0.75 | 27 |
| perish_m4_L2_cv2_f0 | 1 | 27 |
| perish_m4_L2_cv2_f0.5 | 1 | 27 |
| perish_m5_L2_cv1.5_f0 | 0.75 | 31 |
| perish_m5_L2_cv1.5_f0.5 | 0.75 | 31 |
| perish_m5_L2_cv2_f0 | 1 | 31 |
| perish_m5_L2_cv2_f0.5 | 1 | 31 |

本 Python 实现直接抽样未截断的拟合需求分布。公开 C++ 则把边际概率尾部截断到约 1e−16，并删除极小联合概率。计算库存容量时 Python 为避免无限数组，用约 1e−13 的边际尾部截断并归一化；主网格分位数远离该数值误差。随机数算法也不同，因此不能声称逐路径重现 C++，但概率矩和事件转换已经检验。

## 本地接口与验证

实现位于 `examples/inventory/overnight_search/perishable.py`，不调用付费 API。

- `scenarios()` 返回 12 个不可变 `Scenario`；`to_dict()` 保存实际 CV 与库存上限，避免仅依赖含混配置名。
- `sample_demands(scenario,npaths,periods,seed)` 返回 `[paths,periods,2]`，最后一维按 FIFO、LIFO 排列。
- `evaluate(scenario,demands,policy,theta,burnin)` 用 Numba callback `policy(age,pipeline,theta,mu,cv,f,L)`。
- `evaluate_python(scenario,demands,policy,burnin)` 使用任意确定性 callback `policy(age,pipeline)`，其目标和转移完全相同。
- 两个 evaluator 都返回 `(各路径每期费用, 各路径每期[waste,lost,order])`，并拒绝非有限动作。

`handcheck()` 已通过 4500 个随机状态和事件案例，与公开 C++ 累积库存坐标转移的直接转写逐一比较；覆盖 m=3/4/5 与 L=1/2/3、混合发货和需求超过库存。单独手算检查了 FIFO/LIFO 造成的不同报废量、L=2 到货时点以及到货后的 m 次销售机会。24 个主网格与代码口径分布的最大均值误差小于 6.2e−12，最大方差误差小于 3.3e−9。

## 可支持的研究结论边界

本次筛查可以回答在明确模型、统一样本、统一动作域及给定预算下，反馈搜索是否比实际生成的 Baek-style 策略更好。它不能独自证明原 Baek 论文方法一般失败，也不能替代 BSP-low-EW、适用的 PIL/APIL、DCL 和小实例 DP 的强基线。训练、候选选择与最终测试必须用独立种子；完整 12 场景和不利结果都要保留。若只获得数值优化收益，应把 optimizer 与结构搜索贡献分开。

## 已补充的文献规则：BSP-low-EW

`literature_baselines.py` 提供 `policy_codes()["bsp_low_ew_mixed_l2"]`，可直接交给共同 numerical optimizer。采用 [De Moor、Gijsbrechts、Boute 的作者稿第 7 页](https://ciencia.ucp.pt/ws/portalfiles/portal/91570599/39282916.pdf) 所列、归因于 Haijema–Minner 的公式：IP<b 时 q=[S1−αIP+EW]+，否则 q=[S2−IP+EW]+，其中 α=1−(S2−S1)/b。三个参数均由训练数据优化。

EW 在本模型中按两期确定性均值需求、FIFO 后 LIFO 的顺序计算，包含中间一期的 pipeline 到货。因此该名称明确标为混合 issuing 的 L=2 适配；不声称是 PIL/APIL。实现将该两期递推写为闭式表达式，避免策略调用内的数组修改。2400 个随机连续库存、需求均值与 issuing 比例案例与独立 fluid-stock 递推一致，最大误差 7.2e−15；已通过共同 AST 规则及隔离数值评分的 smoke test。
