"""Read-only statistical analysis plus final, reproducible delivery artifacts.

Never sends model requests or changes any frozen policy or evaluation result.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import shutil
import time

import numpy as np

from .environment import summarize
from .experiment import RUN, specs
from examples.inventory.baek_comparison.runner import atomic_json, recover_spend


def pair(a, b):
    return summarize(np.asarray(a["path_costs"]) - np.asarray(b["path_costs"]))


def interval(x):
    return f"[{x['ci95_low']:.2f}, {x['ci95_high']:.2f}]"


def collect():
    rows = []
    for spec in specs():
        d = RUN / "sessions" / spec["id"]
        row = dict(spec)
        for file, key in [("result.json", "generation"), ("scores.json", "scoring")]:
            if (d / file).exists():
                row[key] = json.loads((d / file).read_text())
        if (d / "frozen.json").exists():
            expected = json.loads((d / "frozen.json").read_text())["sha256"]
            actual = hashlib.sha256((d / "policy.py").read_bytes()).hexdigest()
            assert actual == expected, spec["id"]
            row["policy_sha256"] = actual
        rows.append(row)
    return rows


def build(allow_partial=False):
    rows = collect()
    complete = all("generation" in r for r in rows)
    if not complete and not allow_partial:
        raise RuntimeError("Planned generation sessions are not all finished")
    unscored = [r["id"] for r in rows if r.get("generation", {}).get("final_code")
                and (not r.get("policy_sha256") or "scoring" not in r)]
    if unscored and not allow_partial:
        raise RuntimeError(f"Frozen policies awaiting scoring: {unscored}")
    valid = [r for r in rows if r.get("scoring", {}).get("status") == "valid"]
    for r in valid:
        for x in r["scoring"]["datasets"].values():
            recomputed = summarize(x["path_costs"])
            for k in recomputed:
                assert np.isclose(recomputed[k], x[k], rtol=1e-12, atol=1e-10)
    by_id = {r["id"]: r for r in valid}
    l2 = [r for r in valid if r["level"] == "L2"]
    selected = min(valid, key=lambda r: r["scoring"]["datasets"]["validation"]["mean"]) if valid else None
    selected_l2 = min(l2, key=lambda r: r["scoring"]["datasets"]["validation"]["mean"]) if l2 else None
    lowest_excel = min(valid, key=lambda r: r["scoring"]["datasets"]["excel"]["mean"]) if valid else None
    repeats = [r for r in valid if r["role"] == "stability"]
    refs = json.loads((RUN / "baselines.json").read_text())
    actual_cost = sum(r.get("generation", {}).get("cost_usd", 0) for r in rows)
    generations = [r["generation"] for r in rows if "generation" in r]
    analysis = dict(
        complete=complete and not unscored,
        completed_sessions=len(generations), planned_sessions=len(rows),
        valid_policies=len(valid),
        actual_cost_completed_sessions_usd=actual_cost,
        selected_by_validation=selected["id"] if selected else None,
        selected_L2_by_validation=selected_l2["id"] if selected_l2 else None,
        lowest_excel_observed=lowest_excel["id"] if lowest_excel else None,
        lowest_excel_is_post_hoc=True,
        actual_models=sorted({m for g in generations for m in g.get("actual_models", [])}),
        total_python_seconds=sum(g.get("python_seconds", 0) for g in generations),
        total_tool_calls=sum(g.get("tool_calls", 0) for g in generations),
        total_api_requests=sum(g.get("requests", 0) for g in generations),
        total_input_tokens=sum(g.get("usage", {}).get("input_tokens", 0) for g in generations),
        total_output_tokens=sum(g.get("usage", {}).get("output_tokens", 0) for g in generations),
        policy_hashes={r["id"]: r["policy_sha256"] for r in rows if "policy_sha256" in r},
        paired_comparisons={}, repeat_distribution={},
    )
    for dataset in ["excel", "validation", "fresh"]:
        pairs = {}
        if "l1_main" in by_id and "l2_main" in by_id:
            pairs["main_L2_minus_L1"] = pair(by_id["l2_main"]["scoring"]["datasets"][dataset], by_id["l1_main"]["scoring"]["datasets"][dataset])
        if "l1_main" in by_id and selected_l2:
            pairs["validation_selected_L2_minus_L1"] = pair(selected_l2["scoring"]["datasets"][dataset], by_id["l1_main"]["scoring"]["datasets"][dataset])
        if selected:
            for ref in refs["datasets"][dataset]:
                pairs["validation_selected_minus_" + ref["family"]] = pair(selected["scoring"]["datasets"][dataset], ref)
        analysis["paired_comparisons"][dataset] = pairs
        if repeats:
            a = np.array([r["scoring"]["datasets"][dataset]["mean"] for r in repeats])
            analysis["repeat_distribution"][dataset] = dict(
                valid=len(a), planned=10, mean=float(a.mean()), median=float(np.median(a)),
                between_generation_sd=float(a.std(ddof=1)) if len(a) > 1 else None,
                minimum=float(a.min()), maximum=float(a.max()))
    # Resolve token charges from provider responses independently of result totals.
    response_cost = 0.0
    first, last = [], []
    for r in rows:
        journal = RUN / "sessions" / r["id"] / "events.jsonl"
        if not journal.exists():
            continue
        events = []
        for line in journal.read_text().splitlines():
            try:
                events.append(json.loads(line))
            except ValueError:
                if complete:
                    raise
        if events:
            first.append(events[0]["timestamp"])
            last.append(events[-1]["timestamp"])
        for e in events:
            if e["event"] == "response":
                response_cost += e["response"].get("usage", {}).get("cost", 0)
    analysis["actual_returned_response_cost_usd"] = response_cost
    analysis["generation_wall_seconds"] = max(last) - min(first) if first else 0
    _, unresolved = recover_spend(RUN)
    incident_charges = [x for x in unresolved if x["reason"] != "pending"]
    analysis["unconfirmed_failure_charges"] = incident_charges
    analysis["unconfirmed_failure_cost_upper_usd"] = sum(x["reserved_usd"] for x in incident_charges)
    analysis["confirmed_plus_failure_upper_usd"] = response_cost + analysis["unconfirmed_failure_cost_upper_usd"]
    if complete:
        assert np.isclose(actual_cost, response_cost, atol=1e-8), (actual_cost, response_cost)
    atomic_json(RUN / "final_analysis.json", analysis)

    lines = [
        "# Instance 13：Level 1 / Level 2 实验结果", "",
        ("已完成全部 12 次生成会话及可用策略评估。" if analysis["complete"] else "阶段性结果：实验仍在运行。"),
        "采用用户 Excel 的设定；平均折现成本越低越好。主实验各生成一次 L1、L2；另做十次 L2，单独衡量生成结果的稳定性。", "",
        "## 主结果与独立验证集选出的候选", "",
        "| 策略 | Excel 平均成本 | 标准误 | 95% Student-t 区间 | 独立测试平均成本 | 初始化秒数 |",
        "|---|---:|---:|---|---:|---:|",
    ]
    featured = [by_id[k] for k in ["l1_main", "l2_main"] if k in by_id]
    if selected_l2 and selected_l2 not in featured:
        featured.append(selected_l2)
    for r in featured:
        sc = r["scoring"]; x = sc["datasets"]["excel"]
        lines.append(f"| {r['id']} | {x['mean']:.2f} | {x['standard_error']:.2f} | {interval(x)} | {sc['datasets']['fresh']['mean']:.2f} | {sc['setup_seconds']:.3f} |")
    lines += ["", f"全体策略中，独立验证集选择 **{analysis['selected_by_validation']}**；L2 内选择 **{analysis['selected_L2_by_validation']}**。选择不使用 Excel 或独立测试成绩。候选集合中挑选一次是额外的比较，不替代只生成一次的主实验。", ""]
    if lowest_excel:
        lowest_x = lowest_excel["scoring"]["datasets"]["excel"]
        lines += [f"全部已评估产物中，Excel 成本的事后最小值为 **{lowest_x['mean']:.2f}**（{lowest_excel['id']}）。此数只描述这批产物，不作为未经选择偏差影响的代表成绩。", ""]
    for dataset, label in [("excel", "Excel 固定路径"), ("fresh", "独立测试路径")]:
        pairs = analysis["paired_comparisons"][dataset]
        for name, label2 in [("main_L2_minus_L1", "主 L2 − 主 L1"), ("validation_selected_L2_minus_L1", "验证集选出的 L2 − 主 L1")]:
            if name in pairs:
                x = pairs[name]
                conclusion = "区间包含零，尚不能清楚区分二者" if x["ci95_low"] <= 0 <= x["ci95_high"] else "区间完全高于零，前者成本较高" if x["ci95_low"] > 0 else "区间完全低于零，前者成本较低"
                lines.append(f"- {label}，{label2}：配对差 {x['mean']:.2f}，95% 区间 {interval(x)}；{conclusion}。")
    lines += ["", "区间按同一组 200 条路径的成本差计算，仅反映需求路径抽样误差；候选筛选及多重比较应结合独立测试理解。没有认证最优值，因此不将这些差异称为最优性差距。", "", "## 十次额外 L2 的稳定性", ""]
    for dataset, label in [("excel", "Excel"), ("fresh", "独立测试")]:
        x = analysis["repeat_distribution"].get(dataset)
        if x:
            sd = f"{x['between_generation_sd']:.2f}" if x["between_generation_sd"] is not None else "尚不可计算"
            lines.append(f"{label}：{x['valid']}/10 份有效；各次平均成本的均值 {x['mean']:.2f}，中位数 {x['median']:.2f}，范围 [{x['minimum']:.2f}, {x['maximum']:.2f}]，生成之间的标准差 {sd}。")
    lines += ["", "此处生成间标准差与单份策略基于 200 条需求路径的标准误是不同统计量。无效产物保留并计数，不通过重跑剔除失败。", "", "| 会话 | 状态 | Excel 均值 | SE | 95% 区间 | 验证均值 | 独立测试均值 | 初始化秒 | Python 调用 | Python 秒 | API 美元 |", "|---|---|---:|---:|---|---:|---:|---:|---:|---:|---:|"]
    for r in rows:
        g, sc = r.get("generation", {}), r.get("scoring", {})
        x = sc.get("datasets", {}).get("excel")
        status = sc.get("status", g.get("status", "pending"))
        if x:
            lines.append(f"| {r['id']} | {status} | {x['mean']:.2f} | {x['standard_error']:.2f} | {interval(x)} | {sc['datasets']['validation']['mean']:.2f} | {sc['datasets']['fresh']['mean']:.2f} | {sc['setup_seconds']:.3f} | {g['tool_calls']} | {g['python_seconds']:.1f} | {g['cost_usd']:.6f} |")
        else:
            lines.append(f"| {r['id']} | {status} | — | — | — | — | — | — | {g.get('tool_calls', '—')} | {g.get('python_seconds', '—')} | {g.get('cost_usd', '—')} |")
    lines += ["", "## 主策略的内容", "",
        "主 L1 为本实例生成近似动态规划：对 307461 个舍入观测状态建立动作表，使用 45 次折现值迭代。对观测格子内不可见的连续状态采用均匀近似和数值积分；这不是连续状态问题的精确最优解。",
        "主 L2 为问题类生成模拟调参程序。在本实例上选出 target=34、gain=0.65、alpha=0.5，规则为 q=clip(rint(0.65 × (34 − sum(state) + 0.5 × W)), 0, 10)。W 是从当前观测状态、以需求均值向前预测得到的报废量，初始状态订货 6。", "",
        "| 主策略 | 采购 | 持有 | 积压 | 报废 | 流失罚损 |", "|---|---:|---:|---:|---:|---:|"]
    for name in ["l1_main", "l2_main"]:
        if name in by_id:
            parts = by_id[name]["scoring"]["datasets"]["excel"]["component_means"]
            lines.append("| " + name + " | " + " | ".join(f"{v:.2f}" for v in parts) + " |")
    if selected_l2 and selected_l2["id"] == "l2_repeat_07":
        lines += ["", "验证集选中的额外 L2（第 7 次）为线性反馈：q 约等于 clip(rint(23.915060 − 0.578988 x0 − 0.701312 x1 − 0.746418(x2+x3+x4)), 0, 10)。这是用于说明结构的舍入系数，冻结源码保留完整精度。系数由 design(params) 内的独立模拟和差分进化搜索产生，初始状态订货 6。"]
    lines += ["", "上表为各成本项的路径平均折现值；两位小数相加可能有舍入差。", "", "## 简单参考策略", "", "固定订货量和 base-stock 的参数在独立训练路径上选择，均未使用 Excel 测试数据。", "", "| 参考策略 | 参数 | Excel 均值 | SE | 95% 区间 |", "|---|---:|---:|---:|---|"]
    for x in refs["datasets"]["excel"]:
        lines.append(f"| {x['family']} | {x['parameter']} | {x['mean']:.2f} | {x['standard_error']:.2f} | {interval(x)} |")
    if selected:
        reference = next(x for x in refs["datasets"]["excel"] if x["family"] == "base_stock")
        selected_x = selected["scoring"]["datasets"]["excel"]
        difference = analysis["paired_comparisons"]["excel"]["validation_selected_minus_base_stock"]
        reduction = 100 * (reference["mean"] - selected_x["mean"]) / reference["mean"]
        lines += ["", f"验证集选出的策略相对 base-stock 的 Excel 成本降低 {reduction:.2f}%；配对成本差 {difference['mean']:.2f}，95% 区间 {interval(difference)}。"]
    lines += ["", "base-stock 的订货量为 clip(S − 所有舍入后状态分量之和, 0, 10)。这些是简单参考，不能代表最优策略。", "", "## 设置、预算与适配", "",
        "- 模型：openai/gpt-5.6-sol，high 推理强度；所有调用保留服务端模型标识。",
        "- 每个生成会话最多 50 次 Python 调用、累计 3600 秒；L1/L2 每次模型请求输出上限分别为 16384/32768 token。模型可提前结束，无需耗尽预算。",
        "- 一次主 L1、一次主 L2，另外十次 L2。次数按 Jackie 论文 §6.3 的 ten additional 解释；原始仓库对总次数的描述差异已写入冻结协议。",
        "- 每个工具进程使用单个数值线程，两个生成会话可同时运行。工具不保留跨调用状态，仅提供标准库、NumPy、SciPy；不能读取 Excel 测试矩阵或仓库、不能联网。",
        "- 策略初始化目标 30 秒，600 秒防卡死上限。实际机器为 Apple M1 / 8 GB，论文机器为 M2 Pro / 16 GB；因此不能声称硬件完全一致。",
        "- 用户批准扩展 L2 范围以覆盖 instance 13：提前期 2–12、寿命 2–5、需求母均值 0.1–50、母标准差 2–5、持有 1–5、报废 2–10、积压 2–10、流失罚损 0–1000、采购 0–20、最大订货量 10–50、折现率 0.95–0.99。需求始终为条件化到 [0,10] 的正态分布，最大积压等于最大订货量。本次只检验 instance 13，不宣称覆盖整个参数范围的表现。",
        "- Excel：初态 (5,5,5,5,5)，观测状态先 np.rint；连续真实状态用于需求满足、成本和转移。采购系数 9.025，h=1、积压=2、报废=8、流失=1000，动作 0–10，积压上限 10，折现率 0.95。每条路径 1000 期，无预热、无终端成本。",
        "- Excel 种子 111–310；独立验证 41001–41200；独立测试 51001–51200；参考策略训练 61001–61200。每组 200 条路径。随机策略种子固定并记录。",
        "- 核验了 Excel 全部 200000 个需求值和矩阵哈希；评估器通过手算边界、随机源代码对照与统计量检查。",
        "- PIC 论文采用无限期目标和 500 条评估路径，采购项为 gamma^J c_o；本次按 Excel 使用 1000 期、200 条路径和采购系数 9.025。因此这是 Excel instance 上的 Level 1/2 适配实验，不是原论文数值表的原样复现。", "",
        "对当前有界状态、需求和动作，1000 期之后的折现成本可用 1.09×10^(-17) 统一上界控制，因此截断本身数值影响极小；采购系数与评估路径数量的差异仍需保留。", "",
        f"已完成会话 API 已确认费用：**${actual_cost:.6f}**；已返回响应核账总额：${response_cost:.6f}。",
        (f"另有连接失败请求的费用无法确认，完整保留上限 **${analysis['unconfirmed_failure_cost_upper_usd']:.6f}**；已确认费用加该上限为 ${analysis['confirmed_plus_failure_upper_usd']:.6f}。上限不是观测到的实际收费。第 5 次额外 L2 因一次 SSL/TLS 连接错误从原有对话继续；已完成的 5 次模拟、177.78 秒用量和失败请求均保留，没有重置预算或从头另抽策略。核对证据保存在 recovery_evidence/。" if incident_charges else "没有未确认收费的失败请求。"),
        f"生成期间累计 Python 工具时间 {analysis['total_python_seconds']:.1f} 秒、{analysis['total_tool_calls']} 次工具调用、{analysis['total_api_requests']} 次 API 请求；生成墙钟跨度 {analysis['generation_wall_seconds']/60:.1f} 分钟。最终评估使用本地计算，另外记录。", "",
        "## 文件与复核", "",
        f"- [逐策略逐数据集统计]({RUN / 'results.csv'})",
        f"- [逐路径成本]({RUN / 'path_costs.csv'})",
        f"- [完整分析与配对比较]({RUN / 'final_analysis.json'})",
        f"- [冻结实验协议]({RUN / 'protocol.json'})",
        f"- [输入和评估器核验记录]({RUN / 'verification.json'})",
        f"- [最终可复核性核验]({RUN / 'reproducibility_audit.json'})",
    ]
    for r in featured:
        lines.append(f"- [{r['id']} 原始冻结策略]({RUN / 'sessions' / r['id'] / 'policy.py'})")
    lines += ["", "来源：[Jackie Baek 的 Level 1/2 论文](https://arxiv.org/html/2608.27296v1)；[PIC 问题论文](https://arxiv.org/pdf/2001.02798v2)。外部 PIC 代码固定在提交 992d43d61f22317df2532cf67fb5547685bf394a，源码快照及哈希随结果保存。", ""]
    (RUN / "实验报告.md").write_text("\n".join(lines))
    with (RUN / "path_costs.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["run", "level", "role", "dataset", "trajectory_id", "demand_seed", "discounted_cost"])
        for r in valid:
            for dataset, x in r["scoring"]["datasets"].items():
                for i, cost in enumerate(x["path_costs"]):
                    w.writerow([r["id"], r["level"], r["role"], dataset, i + 1, {"excel":111,"validation":41001,"fresh":51001}[dataset] + i, cost])
        for dataset, items in refs["datasets"].items():
            for ref in items:
                for i, cost in enumerate(ref["path_costs"]):
                    w.writerow([ref["family"], "reference", "reference", dataset, i + 1, {"excel":111,"validation":41001,"fresh":51001}[dataset] + i, cost])
    if analysis["complete"]:
        # Retain the initial frozen snapshot. Save reporting-stage code separately.
        dest = RUN / "final_implementation"
        dest.mkdir(exist_ok=True)
        for p in Path(__file__).parent.glob("*.py"):
            shutil.copy2(p, dest / p.name)
        atomic_json(dest / "manifest.json", dict(created_at=time.time(),
            hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in dest.glob("*.py")}))
    print(json.dumps({k:analysis[k] for k in ["complete", "completed_sessions", "valid_policies", "actual_cost_completed_sessions_usd", "selected_by_validation", "selected_L2_by_validation"]}, ensure_ascii=False))
    print(RUN / "实验报告.md")
    return analysis


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--partial", action="store_true")
    args = parser.parse_args()
    build(args.partial)
