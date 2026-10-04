"""Phase-2 adapter. Run only in a fresh process; never changes primary files.

Commands: prepare, prepare-initial, search, evaluate [--freeze-only], score-baek, report.
Search is the only command here that may make paid requests. Its client always
uses the ORIGINAL framework USD35 ledger. Baek generation lives separately at
the original Baek root / extended and shares the ORIGINAL USD12 ledger.
"""
from __future__ import annotations

import argparse
import ast
from concurrent.futures import ThreadPoolExecutor, as_completed
from copy import deepcopy
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import numpy as np

from ..correlated_benchmark.api_client import atomic_json
from .client import SearchClient as OriginalSearchClient
from .perishable import Scenario, inventory_cap, sample_demands


PRIMARY = Path(__file__).resolve().parents[3] / "output/overnight_search/20260917"
RUN = PRIMARY / "extended"
BAEK_RUN = PRIMARY / "baek/extended"
FRAMEWORK_LEDGER = PRIMARY / "framework_budget"
REVISION = "extended_m7_m8_equal_candidate_budget_v1"


def scenarios():
    return [Scenario(f"perish_m{m}_L2_cv{cv:g}_f{f:g}", m=m, L=2, cv=cv, f=f)
            for m in (7, 8) for cv in (1.5, 2.0) for f in (0.0, 0.5)]


def scenario_list(discovery=True):
    return [asdict(s) for s in scenarios() if (s.m == 7) == discovery]


def scenario_grid():
    return [dict(name=s.name, m=s.m, L=s.L, cv=s.cv, f=s.f,
                 split="discovery" if s.m == 7 else "transfer") for s in scenarios()]


class SharedSearchClient(OriginalSearchClient):
    def __init__(self, ignored_run_dir=None):
        # Deliberately ignore search.run_arm's extended/framework_budget path.
        super().__init__(FRAMEWORK_LEDGER)

    def chat(self, messages, max_tokens=32768, metadata=None):
        return super().chat(messages, max_tokens=max_tokens,
                            metadata={**(metadata or {}), "profile": "extended", "revision": REVISION})


def configure():
    """Override imported module globals in THIS process, never source files."""
    from . import search, evaluate_search, evaluator
    from .memory_guard import MemoryGuardMixin
    class ExtendedNumericalSandbox(MemoryGuardMixin, evaluator.NumericalSandbox):
        memory_limit_bytes = 1024 ** 3
    evaluator.NumericalSandbox = ExtendedNumericalSandbox
    config = deepcopy(search.CONFIG)
    config.update(profile="extended", amendment_revision=REVISION,
                  discovery_m=[7], transfer_m=[8], one_query_candidates=8,
                  feedback_details=True,
                  worker_rss_limit_bytes=1024 ** 3,
                  shared_framework_budget_dir=str(FRAMEWORK_LEDGER),
                  shared_baek_budget_file=str(PRIMARY / "baek/budget.json"),
                  initial_information="All three arms receive the same selected common seed code and training costs.",
                  phase2_selection="Full fixed grid of 8 scenarios; amended after primary diagnostic, new test seed sealed.")
    for phase, seed in (("train", 18091001), ("validation", 18092001),
                        ("refit", 18093001), ("test", 18094001)):
        config[phase]["seed"] = seed
    config["train"].update(paths=32, burnin=500, horizon=1000, budget=1024)
    config["refit"].update(paths=64, burnin=500, horizon=1500, budget=2048)
    problem = search.PROBLEM.replace("shelf life m in {3,4,5}", "shelf life m in {7,8}")
    if "shelf life m in {7,8}" not in problem:
        raise ValueError("Primary problem wording changed; review the phase-2 prompt explicitly")
    problem += ("\nThis machine has 8 GiB total RAM. Every phase-2 numerical worker, including the "
                "unrestricted Baek comparison, has the SAME 1 GiB resident-memory watchdog limit. "
                "Avoid full-state tables that exceed this disclosed resource limit. "
                "This is a machine-memory constraint, not a limit on the number of policy parameters.\n")
    search.RUN, search.CONFIG, search.PROBLEM = RUN, config, problem
    search.scenario_list, search.SearchClient = scenario_list, SharedSearchClient
    search.evaluate = lambda request, timeout=900: evaluator.evaluate(request, timeout=timeout)
    evaluate_search.RUN, evaluate_search.CONFIG = RUN, config
    evaluate_search.scenarios = scenarios
    # Existing imported job/score functions resolve the patched search globals.
    return search, evaluate_search, config


def immutable_json(path, record):
    if path.exists():
        existing = json.loads(path.read_text())
        if existing != record:
            raise ValueError(f"Existing phase-2 artifact differs: {path}")
        return existing
    atomic_json(path, record)
    return record


def prepare(config):
    RUN.mkdir(parents=True, exist_ok=True)
    target = RUN / "amendment.json"
    if not target.exists() and any((RUN / "test").glob("*.json")):
        raise ValueError("Cannot create a prospective amendment after phase-2 test files exist")
    amendment = dict(
        revision=REVISION,
        rationale="Primary small inventory-position caps allow an unrestricted tool agent to enumerate exact states. "
                  "This follow-up increases shelf-life/state dimension while keeping mean, costs, demand fitting and lead time unchanged. "
                  "It tests scalable policy design; greater state dimension does not guarantee worse Baek performance or more economic headroom.",
        status="Protocol amendment after primary/scaling diagnostics, not an originally preregistered confirmatory test.",
        grid=[s.to_dict() for s in scenarios()], discovery_shelf_life=7, transfer_shelf_life=8,
        disclosure="All 8 outcomes will be retained. m8 parameters are public but excluded from structure-search feedback.",
        parity="One-query now returns 8 candidates in one response; independent sampling and evolution each return 8. "
               "Each candidate gets the same optimizer ceiling. All arms see the same initial seed source/costs. "
               "Initial fitted parameters/metrics are also common; subsequent feedback is available only to evolution. "
               "Train fitting uses32 paths and1024 evaluations; final refit uses64 paths and2048 evaluations. "
               "All phase-2 numerical workers, including Baek, share a1GiB RSS watchdog limit on the8GiB host. "
               "Token and wall-clock costs can still differ.",
        monetary_budget="Shares the original USD35 framework ledger and original USD12 Baek ledger; no additional allocation. "
                        "The overall user authorization remains USD50, including the USD3 unallocated reserve.",
        test_gate="No phase-2 final-test tape is generated until numeric structures/parameters and all three Baek sources are sealed.",
        settings=config,
    )
    immutable_json(target, amendment)
    immutable_json(RUN / "protocol.json", config)
    text = """# 第二阶段协议修订：寿命 7/8 的易腐库存

第一阶段较小的库存容量允许通用工具 agent 使用精确状态枚举。本阶段增加年龄状态维度，检验有限计算预算下的可扩展策略设计；保持均值 4、L=2、实际 CV=1.5/2、FIFO 比例 0/0.5 及原有需求、费用和容量口径。

固定全部 8 个场景：m=7 的 4 个用于结构发现，m=8 的 4 个仅用于未提供搜索反馈的迁移检查。更长寿命可能使经济问题更简单，不预设 Baek 表现较差。本阶段由前期诊断促成，必须标为协议修订和探索性检验，不能声称是最初预登记的确认性结果。

单次查询现在一次返回 8 个候选；独立生成和演化各产生 8 个，每候选使用同一数值优化上限。三组均先看到同一初始基线源码、训练成绩、拟合参数和费用分项，之后仅演化组获得逐轮反馈。模型调用次数、token、美元和运行时间仍须分别报告。

训练、验证、重新拟合和测试使用新种子 18091001、18092001、18093001、18094001。训练使用 32 条路径、500 期 warm-up、1000 期计分及 1024 次 objective 上限；重新拟合使用 64 条路径、500 期 warm-up、1500 期计分及 2048 次 objective 上限。验证和测试路径数、时域沿用第一阶段设置。先冻结全部数值结构/参数及三份 Baek 源码，再生成测试需求。没有参数个数限制，全部场景和失败结果均保留。

本机物理内存为 8 GiB。第二阶段所有数值工作进程（含 Baek）统一执行 1 GiB 常驻内存监测上限，超限必须明确标记。该机器资源条件不会被解释为某类算法原则上不能使用动态规划。

费用复用第一阶段同一本 $35 框架账和同一本 $12 Baek 账；没有新增 $35 或 $12 预算。用户总授权仍为 $50，另有 $3 未分配。
"""
    markdown = RUN / "amendment.md"
    if markdown.exists() and markdown.read_text() != text:
        raise ValueError("Existing amendment markdown changed")
    if not markdown.exists():
        markdown.write_text(text)
    return amendment


def add_literature_baseline(search):
    from .literature_baselines import policy_codes
    for name, code in policy_codes().items():
        target = RUN / "baselines" / name / "fit.json"
        if not target.exists():
            record = search.evaluate(search.job(code))
            record.update(code=code, valid=True)
            atomic_json(target, record)
            (target.parent / "policy.py").write_text(code)


def initialize_shared_information(search):
    denominators, bases = search.initialize()
    # Same source and identical training information appear in ALL arm prompts.
    name = min(bases, key=lambda key: bases[key]["score"])
    seed = bases[name]
    common = dict(name=name, code=seed["code"], training_score=seed["score"],
                  costs={s: row["cost"] for s, row in seed["results"].items()},
                  fitted_parameters={s: row["theta"] for s, row in seed["results"].items()},
                  cost_metrics={s: row["metrics"] for s, row in seed["results"].items()})
    immutable_json(RUN / "common_seed_information.json", common)
    shared_text = ("All comparison arms receive the SAME common initial policy and training information below. "
                   "You may retain, improve or replace it. Lower cost is better.\n"
                   + json.dumps({key: value for key, value in common.items() if key != "code"})
                   + "\n" + common["code"])
    information_path = RUN / "common_seed_information.txt"
    if information_path.exists() and information_path.read_text() != shared_text:
        raise ValueError("Shared initial information changed")
    if not information_path.exists():
        information_path.write_text(shared_text)
    search.PROBLEM += "\n" + shared_text
    prompt_path = RUN / "common_problem_prompt.txt"
    if prompt_path.exists() and prompt_path.read_text() != search.PROBLEM:
        raise ValueError("Phase-2 common prompt changed")
    if not prompt_path.exists():
        prompt_path.write_text(search.PROBLEM)
    add_literature_baseline(search)
    return denominators, bases


def search_all(search, workers):
    denominators, bases = initialize_shared_information(search)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(search.run_arm, arm, repeat, denominators, bases): (arm, repeat)
                   for repeat in (1, 2, 3) for arm in ("one_query", "best_of_n", "evolution")}
        for future in as_completed(futures):
            arm, repeat = futures[future]
            try:
                result = future.result()
                print("EXTENDED COMPLETED", arm, repeat, result["best_training"]["score"], flush=True)
            except Exception as error:
                atomic_json(RUN / "errors" / f"{arm}_r{repeat}.json", dict(error=str(error)))
                print("EXTENDED ARM ERROR", arm, repeat, str(error), flush=True)
    atomic_json(RUN / "framework_budget_summary.json", SharedSearchClient().summary())


def freeze_numeric(search, evaluation, workers):
    completed = [json.loads(path.read_text()) for path in sorted((RUN / "search").glob("*/completed.json"))]
    expected = {(arm, repeat) for arm in ("one_query", "best_of_n", "evolution") for repeat in (1, 2, 3)}
    if {(row["arm"], row["repeat"]) for row in completed} != expected or len(completed) != 9:
        raise ValueError("Need exactly all nine phase-2 search repetitions before selecting final structures")
    bases = {}
    for path in sorted((RUN / "baselines").glob("*/fit.json")):
        row = json.loads(path.read_text())
        theta = {name: value["theta"] for name, value in row["results"].items()}
        validation = evaluation.validate(row["code"], theta, path.parent.name)
        bases[path.parent.name] = dict(code=row["code"], validation=validation)
    denominators = {s["name"]: min(row["validation"]["results"][s["name"]]["cost"]
                    for name, row in bases.items() if name in search.seed_codes()) for s in scenario_list()}
    with ThreadPoolExecutor(max_workers=workers) as pool:
        selected = list(pool.map(lambda row: evaluation.select_one(row, denominators), completed))
    codes = {f"{row['arm']}_r{row['repeat']}": row["selected"]["code"] for row in selected}
    codes.update({f"baseline_{name}": row["code"] for name, row in bases.items()})
    fits = {}
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(evaluation.refit, code): name for name, code in codes.items()}
        for future in as_completed(futures):
            name = futures[future]
            fits[name] = future.result()
            print("EXTENDED REFIT", name, flush=True)
    artifacts = {name: dict(code=code, code_sha256=hashlib.sha256(code.encode()).hexdigest(),
                           theta={s: row["theta"] for s, row in fits[name]["results"].items()})
                 for name, code in codes.items()}
    seal = RUN / "numeric_policies_freeze.json"
    if seal.exists():
        existing = json.loads(seal.read_text())
        if existing["artifacts"] != artifacts:
            raise ValueError("Phase-2 numeric frozen artifacts changed")
        return existing
    freeze = dict(created_utc=datetime.now(timezone.utc).isoformat(), profile="extended", artifacts=artifacts)
    atomic_json(seal, freeze)
    return freeze


def seal_baek():
    policies = {}
    for repeat in (1, 2, 3):
        source = BAEK_RUN / "sessions" / f"l2_r{repeat}" / "policy.py"
        if not source.exists():
            raise ValueError(f"Phase-2 test remains sealed: missing Baek draw {repeat}: {source}")
        code = source.read_text()
        ast.parse(code)
        if not code.strip():
            raise ValueError("Empty Baek source")
        policies[repeat] = code
    hashes = {str(repeat): hashlib.sha256(code.encode()).hexdigest() for repeat, code in policies.items()}
    seal = RUN / "baek_policies_freeze.json"
    if seal.exists():
        if json.loads(seal.read_text())["sha256"] != hashes:
            raise ValueError("Phase-2 Baek frozen artifacts changed")
    else:
        atomic_json(seal, dict(sha256=hashes, source_root=str(BAEK_RUN), profile="extended",
                               created_utc=datetime.now(timezone.utc).isoformat()))
    return policies


def evaluate_numeric(search, evaluation, freeze, workers):
    # This call checks all Baek artifacts before any final-test job is built.
    seal_baek()
    def test_one(item):
        name, artifact = item
        evaluation.saved_evaluate(RUN / "test" / f"{name}.json",
            search.job(artifact["code"], "test", specs=[asdict(s) for s in scenarios()], theta=artifact["theta"]))
        initials = []
        for line in artifact["code"].splitlines():
            if "OPT_PARAM:" in line:
                assignment = ast.parse(line.split("#", 1)[0].strip()).body[0]
                initials.append(float(ast.literal_eval(assignment.value)))
        evaluation.saved_evaluate(RUN / "test" / f"{name}_without_tuning.json",
            search.job(artifact["code"], "test", specs=[asdict(s) for s in scenarios()],
                       theta={s.name: initials for s in scenarios()}))
        print("EXTENDED TEST", name, flush=True)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        list(pool.map(test_one, freeze["artifacts"].items()))
    atomic_json(RUN / "numeric_evaluation_completed.json", dict(policy_count=len(freeze["artifacts"]),
                test_settings=search.CONFIG["test"], discovery_instances=4, transfer_instances=4))


def score_baek(config, workers):
    from .baek_perishable import score_code
    if not (RUN / "numeric_policies_freeze.json").exists():
        raise ValueError("Freeze all phase-2 numerical artifacts before any final-test demand")
    policies = seal_baek()
    settings = config["test"]
    results = {repeat: {} for repeat in policies}
    def one(repeat, scenario):
        target = RUN / "baek_scores" / f"r{repeat}" / f"{scenario.name}.json"
        digest = hashlib.sha256(policies[repeat].encode()).hexdigest()
        if target.exists():
            row = json.loads(target.read_text())
            if row.get("code_sha256") != digest or row.get("test_settings") != settings:
                raise ValueError("Immutable Baek score changed")
            return repeat, scenario.name, row
        demands = sample_demands(scenario, settings["paths"], settings["burnin"] + settings["horizon"], settings["seed"])
        scored = score_code(policies[repeat], asdict(scenario), demands, burnin=settings["burnin"], run_dir=BAEK_RUN)
        row = dict(cost=scored["mean_cost"], path_costs=scored["path_costs"],
                   metrics=np.mean(scored["components"], axis=0).tolist(), theta=[],
                   setup_seconds=scored["setup_seconds"], score_seconds=scored["score_seconds"],
                   backend=scored["backend"], code_sha256=digest, test_settings=settings)
        atomic_json(target, row)
        print("EXTENDED BAEK TEST", repeat, scenario.name, row["cost"], flush=True)
        return repeat, scenario.name, row
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(one, repeat, scenario): (repeat, scenario.name)
                   for repeat in policies for scenario in scenarios()}
        for future in as_completed(futures):
            try:
                repeat, name, row = future.result()
                results[repeat][name] = row
            except Exception as error:
                repeat, name = futures[future]
                atomic_json(RUN / "baek_score_errors" / f"r{repeat}_{name}.json", dict(error=str(error)))
    for repeat, rows in results.items():
        atomic_json(RUN / "test" / f"baek_r{repeat}.json", dict(results=rows, complete=len(rows) == 8))


def report_extended(draws):
    """Reuse statistical helpers, without primary report's fixed 12-case text."""
    from . import report
    report.grid = scenario_grid
    data, _, problems = report.load_scores(RUN)
    groups = report.group_scores(data)
    complete = all(len(data.get(method, {})) == 8 for method in report.PRINCIPAL)
    complete = complete and all(len(groups[arm]) == 8 for arm in report.ARMS)
    comparisons, group_rows, per_run, robust, ablations = [], [], [], [], []
    for spec in scenario_grid():
        name = spec["name"]
        for method, rows in data.items():
            if name in rows:
                row = rows[name]
                per_run.append(dict(**spec, method=method, cost=row["cost"], paths=len(row["paths"])))
        present = [groups[arm].get(name) for arm in report.ARMS]
        if all(row is not None for row in present) and len({len(row["paths"]) for row in present}) != 1:
            complete = False
            problems.append(f"{name}: 主方法路径数不同")
        for method, rows in groups.items():
            if name in rows:
                row = rows[name]
                group_rows.append(dict(**spec, method=method, cost=row["cost"], generation_sd=row["generation_sd"],
                                       generations=row["generations"], paths=len(row["paths"]),
                                       best_generation_cost=row["best"], worst_generation_cost=row["worst"]))
        evo = groups["evolution"].get(name)
        for reference in ("one_query", "best_of_n", "baek") + report.BASELINES:
            ref = groups[reference].get(name)
            if evo is None or ref is None:
                continue
            paired = report.paired_comparison(evo, ref, key="extended:" + name + reference, draws=draws)
            if paired:
                comparisons.append(dict(**spec, candidate="evolution", reference=reference, **paired))
                if reference == "baek":
                    flag = bool(evo["worst"] < ref["best"] and paired["improvement_pct"] >= 1)
                    robust.append(dict(**spec, mean_improvement_pct=paired["improvement_pct"],
                                       evolution_worst_cost=evo["worst"], baek_best_cost=ref["best"],
                                       robust_screen_candidate=flag))
        for method, rows in data.items():
            if method.endswith("_without_tuning") and name in rows:
                tuned = method.removesuffix("_without_tuning")
                if name in data.get(tuned, {}):
                    paired = report.paired_comparison(data[tuned][name], rows[name], key="extended:" + name + method, draws=draws)
                    if paired:
                        ablations.append(dict(**spec, method=tuned, **paired))
    def csv(name, rows, fields):
        report.write_csv(RUN / "tables" / name, rows, fields)
    base = ["name", "m", "L", "cv", "f", "split"]
    pair_fields = ["candidate_cost", "reference_cost", "improvement_pct", "improvement_ci_low", "improvement_ci_high", "absolute_improvement", "absolute_ci_low", "absolute_ci_high", "paths"]
    csv("per_run.csv", per_run, base + ["method", "cost", "paths"])
    csv("group_summary.csv", group_rows, base + ["method", "cost", "generation_sd", "generations",
                                               "best_generation_cost", "worst_generation_cost", "paths"])
    csv("paired_comparisons.csv", comparisons, base + ["candidate", "reference"] + pair_fields)
    csv("robust_candidates.csv", robust, base + ["mean_improvement_pct", "evolution_worst_cost", "baek_best_cost", "robust_screen_candidate"])
    csv("optimizer_ablation.csv", ablations, base + ["method"] + pair_fields)
    budget = report.ledger_usage(PRIMARY)  # Global cumulative ledger; do not count it a second time.
    summary = dict(profile="extended", complete_primary_comparison=complete, n_scenarios=8, problems=problems,
                   robust_candidates=[row for row in robust if row["robust_screen_candidate"]] if complete else [],
                   budget_scope="Cumulative primary + extended, not additional phase-2 expenditure", budget=budget)
    atomic_json(RUN / "report_summary.json", summary)
    lines = ["# 第二阶段：寿命 7/8 的易腐库存", "",
             "全部主结果齐全。" if complete else "主比较尚未完成；缺失或无效结果不能被当作成功。",
             "", f"已确认满足固定稳健筛查条件的实例数：{len(summary['robust_candidates']) if complete else '待完成'} / 8。",
             "", "各单元为三个独立生成的平均每期成本 ± 生成间样本标准差；不按测试结果挑选最佳生成。", "",
             "| 场景 | 单次查询8候选 | 独立生成8候选 | 演化8候选 | Baek L2 | 演化对Baek改善% [95%路径区间] |",
             "|---|---:|---:|---:|---:|---:|"]
    for spec in scenario_grid():
        cells = []
        for arm in report.ARMS:
            row = groups[arm].get(spec["name"])
            cells.append("缺" if row is None else f"{row['cost']:.3f} ± {row['generation_sd']:.3f}")
        paired = next((row for row in comparisons if row["name"] == spec["name"] and row["reference"] == "baek"), None)
        cells.append("缺" if paired is None else f"{paired['improvement_pct']:.2f} [{paired['improvement_ci_low']:.2f}, {paired['improvement_ci_high']:.2f}]")
        lines.append(f"| m={spec['m']}, CV={spec['cv']:g}, f={spec['f']:g} | " + " | ".join(cells) + " |")
    lines += ["", "正改善为100×(参照−演化)/参照。配对bootstrap区间只反映固定这三份生成策略后的需求路径误差，不是生成不确定性的区间；生成标准差另列。稳健筛查条件为最差演化重复仍优于最佳Baek重复，且三重复均值改善至少1%；多个实例未做多重比较校正，仍需独立确认。",
              "", "m7用于三个数值结构搜索组的结构发现，m8不向这三个组提供搜索反馈。三组使用相同初始基线信息和8候选数值预算上限，但单次/多次LLM调用、token及实际费用仍不同。Baek保留通用工具与设计阶段计算能力。",
              "", "m=8仅对三个数值结构搜索组属于未提供搜索反馈的迁移场景。Baek L2同样预先知道完整有限参数族，可在工具会话中自行模拟m=7/8全部组合并针对实例拟合或写入系数；这符合其design(params)接口。双方共享公开模型/训练helper，但实际训练查询、工具计算和实例适配并不相同，不能称为所有方法共同的未知参数holdout。",
              "", "经典策略、各次生成、optimizer消融及全部配对结果位于 tables/，没有按测试结果筛除不利场景。未实现的PIL/APIL、DCL不被描述为已击败。",
              "", "本阶段是由第一阶段和独立规模诊断促成的协议修订，不是原始预登记确认试验。更高年龄维度不保证经济上更困难。CV和容量沿用已披露的论文文字口径，与公开DynaPlex代码口径差异仍然存在。",
              "", f"共享账本累计已知实付 ${budget['recorded_known_usd']:.4f}，未决上界 ${budget['recorded_held_usd']:.4f}；这是第一、二阶段合计，不能再次相加。全程总上限仍为$50。",
              "", report.nested_note(), "", "协议与结果： [amendment.md](amendment.md)、[report_summary.json](report_summary.json)、[tables/paired_comparisons.csv](tables/paired_comparisons.csv)。"]
    if problems:
        lines += ["", "## 缺失或无效记录", ""] + ["- " + text for text in problems]
    (RUN / "report.md").write_text("\n".join(lines) + "\n")
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["prepare", "prepare-initial", "search", "evaluate", "score-baek", "report"])
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--freeze-only", action="store_true")
    parser.add_argument("--bootstrap-draws", type=int, default=5000)
    args = parser.parse_args()
    search, evaluation, config = configure()
    prepare(config)
    if args.command == "prepare":
        print(json.dumps(dict(run=str(RUN), baek_run=str(BAEK_RUN), shared_framework_ledger=str(FRAMEWORK_LEDGER),
                              scenarios=[s.to_dict() for s in scenarios()], config=config), indent=2))
    elif args.command == "prepare-initial":
        initialize_shared_information(search)
        print("Initial common information frozen at", RUN / "common_seed_information.txt", flush=True)
    elif args.command == "search":
        search_all(search, args.workers)
    elif args.command == "evaluate":
        freeze = freeze_numeric(search, evaluation, args.workers)
        if not args.freeze_only:
            evaluate_numeric(search, evaluation, freeze, args.workers)
    elif args.command == "score-baek":
        score_baek(config, args.workers)
    else:
        print(json.dumps(report_extended(args.bootstrap_draws), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
