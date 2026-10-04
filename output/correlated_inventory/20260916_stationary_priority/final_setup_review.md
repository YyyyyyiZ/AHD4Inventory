# 正式实验基础设施独立审查

审查时间：2026-09-16T04:41:08.944415+00:00

## 结论

核心预算、数据和测试门禁检查通过。审查发现的 HTTP 失败错误释放预算、Python 调用绕过 test 门禁、baseline 参数未绑定冻结清单三项问题，已由主任务修正并复查。未调用任何真实 API、未运行生成策略、未修改被审代码，未重复正在执行的 validation 任务。

## 实际验证

- 预算：现有 2 个本地单元测试通过；额外 4 进程/16 次并发预留的 $0.01 fixture 只成功 1 次，未知费用 $0.0054502 在重启后仍全额计入预算。
- 模拟 HTTP 400/401/402/403/404/422/429/500：每种只调用一次 mock transport，均保留 reservation；无自动重试。
- 模拟有效 usage.cost 与错误模型 ID：返回被拒绝，但已知费用保留。模拟缺失 usage.cost：全额 reservation 保留。
- 18 份真实数据文件 SHA256 与 manifest 一致；train/validation/test 的 seed 集合无交集，每 split 4 条独立需求流，另两格是预注册的 fixed/random 共享需求对。两对训练 demand 与 D_prev 数组逐项完全一致。
- 直接 Python evaluate_scenario(test) 在主实验未冻结时失败，mock 证明 load_tapes 从未被调用。
- 合成完整 18 个训练 completion 与 6 组基线：freeze 绑定 48 份文件（18 策略、18 completion、6 records、6 baseline completion），重复冻结幂等，修改基线参数后被拒绝。
- 合成随机交货期轨迹：steady B500 与 cold B0 各 H50/100/200/500，共八窗口的成本、销售、失销量、需求和订单数量与分别执行参考环境一致。所有比较使用同一冻结规则及对应日历路径。
- write_windows → NPZ/JSON → report 的合成八行 roundtrip 通过，成本分解、aggregate fill rate、来源与文件哈希兼容。空或不完整的已有评价记录会被拒绝。

## 源码审查

- ledger 用跨进程 flock 包围读取、预留和结算，原子替换并 fsync 文件；pending/unknown_charge/missing_cost 全额保留上限，authoritative usage.cost 单独计入已知费用。
- 请求价格上限与最大输出同时约束，输入上限用 UTF-8 字节加 framing 余量；没有自动 HTTP 重试。实际 model ID 在保存响应和结算后校验。
- 数据 latent 从不变分布开始；日历报价独立于动作；连续指数边际、AR latent 参数及 regime 构造在 protocol 与数据模块一致。
- pilot 写入 pilots，正式 10×10 搜索写入 training；报告还要求 full_protocol=true、正确 H200 与 r1/r2/r3 ID 才纳入 18 主组。
- test gate 现在位于公开评估函数内，并绑定真实策略与全七族 baseline records；refit CLI 也要求主实验冻结。
- 评价按完整 1000 期真实需求轨迹取嵌套窗口，cold_start 使用从空状态开始的前缀，steady 使用运行前 500 期后的窗口；没有免费备货期。

## 尚待真实运行确认

- 正式 18 组训练及所有测试评价尚未完成；这里不证明政策性能、训练收敛、API 全流程实际吞吐或最终费用。
- 有限 500 期预热只近似受控库存稳态；需求本身从第一期严格平稳。
- adapter 正在进行 optimizer 轻量反馈优化；其改动后的 mock 等价性和最终源码快照由主任务另行确认，不属于本次已测代码。
- 已提醒 adapter 在从已落盘 provider response 恢复时再次核对模型 ID，防止极窄崩溃窗口绕过初次模型校验；普通错误路径已有 blocked_transport 禁止自动恢复。

## 被审源码哈希

| 文件 | SHA256 |
|---|---|
| api_client.py | 862f95092d064a7448504dbb4c15464fee574c4459066c7ee33fa2e731dc510b |
| protocol.py | dbb4fa73c34bf7d6d9bca0b967fe424b906c68e61dc4f51905f71b8717872212 |
| prepare_data.py | 22f8844e73dd84a4be5ce8d39be697e7354aa9a733cec8381818396f475f64fd |
| orchestrator.py | 529d25b8cd4eff4f86815a9bdc0ac7878ad936f87dbfc76455211e4ce4b7a246 |
| evaluation.py | b9230daecdd8dbf1f35849fa4d1a823784f55c228e433a77cb82331544e1d8b0 |
