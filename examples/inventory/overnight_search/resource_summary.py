"""Summarize incurred resources, preserving incomplete and failed attempts."""
from __future__ import annotations

import csv
import argparse
import hashlib
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
import tempfile

from ..correlated_benchmark.api_client import atomic_json

ROOT = Path(__file__).resolve().parents[3] / "output/overnight_search/20260917"


def read(path):
    return json.loads(path.read_text())


# Outcomes are deliberately discarded before metadata records leave the reader.
# None of this accounting code evaluates a policy or examines a score value.
OUTCOME_FIELDS = frozenset({"cost", "path_costs", "metrics", "mean_cost", "mean_components",
                            "path_components", "validation", "train_score", "score"})
EVALUATION_COLUMNS = (
    "profile", "stage", "job_id", "request_sha256", "code_sha256", "policy_aliases",
    "source_labels", "artifact_paths", "representations", "coverage", "scenario_names",
    "scenario_records", "saved_execution_records", "optimizer_nfev", "optimizer_seconds",
    "transitions", "worker_wall_seconds", "cache_status", "cache_hits", "cache_misses",
    "cache_peak_entries", "cache_scenarios_measured", "cache_scenario_records",
    "artifact_cache_hits", "artifact_cache_misses", "excluded_checkpoint_paths", "notes")


def read_metadata(path):
    return json.loads(path.read_text(), object_hook=lambda row: {
        key: value for key, value in row.items() if key not in OUTCOME_FIELDS})


def digest(code):
    return hashlib.sha256(code.encode()).hexdigest()


def measured(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return value if math.isfinite(value) and value >= 0 else None


def measured_sum(values):
    values = list(values)
    return sum(values) if values and all(value is not None for value in values) else None


def result_metadata(record):
    results = record.get("results", {})
    rows = list(results.values())
    cache_rows, states = [], []
    for name in sorted(results):
        # New checkpoint aggregates retain each worker's cache metadata. Older
        # whole-family jobs have one action_cache entry; old jobs have neither.
        cache = record.get("action_cache_by_scenario", {}).get(name, record.get("action_cache"))
        enabled = cache.get("enabled") if isinstance(cache, dict) else None
        states.append("enabled" if enabled is True else "disabled" if enabled is False else "unknown")
        counters = cache.get("scenarios", {}).get(name, {}) if isinstance(cache, dict) else {}
        cache_rows.append({key: measured(counters.get(key)) for key in ("hits", "misses", "peak_entries")})
    state = next(iter(set(states))) if len(set(states)) == 1 else "mixed" if states else "unknown"
    return dict(scenario_names=sorted(results), scenario_records=len(rows),
        optimizer_nfev=measured_sum(measured(row.get("nfev")) for row in rows),
        optimizer_seconds=measured_sum(measured(row.get("seconds")) for row in rows),
        transitions=measured(record.get("transitions")), worker_wall_seconds=measured(record.get("wall_seconds")),
        cache_status=state, cache_hits=measured_sum(row["hits"] for row in cache_rows),
        cache_misses=measured_sum(row["misses"] for row in cache_rows),
        cache_peak_entries=(max(row["peak_entries"] for row in cache_rows)
                            if cache_rows and all(row["peak_entries"] is not None for row in cache_rows) else None),
        cache_scenarios_measured=sum(row["hits"] is not None and row["misses"] is not None for row in cache_rows),
        cache_scenario_records=cache_rows,
        artifact_cache_hits=None, artifact_cache_misses=None)


def policy_metadata(run):
    """Map existing source/selection metadata to aliases without outcome use."""
    aliases, origins, validation, validation_source, label_source = (defaultdict(set), defaultdict(set),
                                                                  defaultdict(set), {}, {})
    def source(code, label, *, final=False):
        if not isinstance(code, str):
            return None
        key = digest(code)
        origins[key].add(label)
        if final:
            aliases[key].add(label)
            label_source[label] = key
        return key
    def validation_alias(code, theta, label):
        if isinstance(code, str) and isinstance(theta, dict):
            key = digest(code + json.dumps(theta, sort_keys=True))[:20]
            validation[key].add(label)
            validation_source[key] = digest(code)
    for path in sorted((run / "baselines").glob("*/fit.json")):
        row = read_metadata(path)
        label = "baseline_" + path.parent.name
        source(row.get("code"), label, final=True)
        results = row.get("results", {})
        if results and all("theta" in value for value in results.values()):
            validation_alias(row.get("code"), {name: value["theta"] for name, value in results.items()}, label)
    for path in sorted((run / "search").glob("*/candidate_*/policy.py")):
        source(path.read_text(), path.parent.parent.name + ":" + path.parent.name)
    for path in sorted((run / "selected").glob("*.json")):
        row = read_metadata(path)
        label = path.stem
        source(row.get("selected", {}).get("code"), label, final=True)
        for choice in row.get("choices", []):
            validation_alias(choice.get("code"), choice.get("train_theta"), label + ":" + choice.get("origin", "unknown"))
    freeze_path = run / "numeric_policies_freeze.json"
    if freeze_path.exists():
        for label, artifact in read_metadata(freeze_path).get("artifacts", {}).items():
            source(artifact.get("code"), label, final=True)
    return dict(aliases=aliases, origins=origins, validation=validation,
                validation_source=validation_source, label_source=label_source,
                prefixes={key[:20]: key for key in origins})


def numerical_evaluation_resources(root):
    """Account once per saved job, grouping identical requests and their aliases.

    A shared cached file is visited once. Distinct scoring filenames really
    trigger separate workers in the current harness, even for identical
    requests; they share one row but their recorded work is summed. Refit
    aggregate/checkpoint representations are the sole intentional duplicate.
    """
    output = []
    for profile in ("primary", "extended"):
        run = root if profile == "primary" else root / "extended"
        metadata = policy_metadata(run)
        expected = {f"perish_m{m}_L2_cv{cv:g}_f{f:g}" for m in ((3, 4, 5) if profile == "primary" else (7, 8))
                    for cv in (1.5, 2.) for f in (0., .5)}
        jobs = []
        def add(path, stage, *, aliases=(), representation="saved_job", coverage="saved_record",
                code_sha=None, excluded=(), record=None):
            record = read_metadata(path) if record is None else record
            code_sha = record.get("code_sha256") or (digest(record["code"]) if isinstance(record.get("code"), str) else code_sha)
            request_sha = record.get("request_sha256")
            # Without a full request hash, do not assume different parameter
            # vectors or different historical settings were the same request.
            identity = request_sha or str(path.relative_to(root))
            aliases = set(aliases)
            if stage == "final_refit":
                aliases.update(metadata["aliases"].get(code_sha, ()))
            values = result_metadata(record)
            notes = []
            if not request_sha:
                notes.append("No saved request hash; artifact path is the conservative identity.")
            if values["cache_status"] in ("unknown", "mixed"):
                notes.append("Missing action-cache counters remain null; partial coverage is reported separately.")
            jobs.append(dict(profile=profile, stage=stage, identity=identity, request_sha256=request_sha,
                code_sha256=code_sha, policy_aliases=sorted(aliases), source_labels=sorted(metadata["origins"].get(code_sha, ())),
                artifact_paths=[str(path.relative_to(root))], representations=[representation], coverage=coverage,
                saved_execution_records=1, excluded_checkpoint_paths=[str(p.relative_to(root)) for p in excluded],
                notes=notes, **values))
        for path in sorted((run / "baselines").glob("*/fit.json")):
            add(path, "initial_baseline_fit", aliases=["baseline_" + path.parent.name])
        for path in sorted((run / "validation").glob("*.json")):
            add(path, "validation", aliases=metadata["validation"].get(path.stem, ()),
                code_sha=metadata["validation_source"].get(path.stem))
        aggregates = {path.stem: path for path in (run / "refit").glob("*.json")}
        parts = {path.name: sorted(path.glob("*.json")) for path in (run / "refit_parts").glob("*") if path.is_dir()}
        for key in sorted(set(aggregates) | set(parts)):
            aggregate = read_metadata(aggregates[key]) if key in aggregates else None
            checkpoints = parts.get(key, [])
            code_sha = metadata["prefixes"].get(key)
            if aggregate and set(aggregate.get("results", {})) == expected:
                add(aggregates[key], "final_refit", code_sha=code_sha, excluded=checkpoints,
                    representation="complete_refit_aggregate", coverage="complete", record=aggregate)
            elif checkpoints:
                for path in checkpoints:
                    add(path, "final_refit", code_sha=code_sha, representation="refit_checkpoint_part", coverage="partial")
            elif aggregate:
                add(aggregates[key], "final_refit", code_sha=code_sha,
                    representation="incomplete_refit_aggregate", coverage="partial", record=aggregate)
        for path in sorted((run / "test").glob("*.json")):
            # Baek's combined test file is a view over baek_scores, not an
            # optimizer worker record; it is not charged again here.
            if path.stem.startswith("baek_"):
                continue
            raw = path.stem.endswith("_without_tuning")
            label = path.stem.removesuffix("_without_tuning")
            add(path, "final_scoring_defaults" if raw else "final_scoring_tuned", aliases=[label],
                code_sha=metadata["label_source"].get(label))
        grouped = defaultdict(list)
        for job in jobs:
            grouped[job["stage"], job["identity"]].append(job)
        for (stage, identity), entries in sorted(grouped.items()):
            codes = {entry["code_sha256"] for entry in entries if entry["code_sha256"]}
            if len(codes) > 1:
                raise ValueError("One request identity has inconsistent source hashes")
            row = dict(profile=profile, stage=stage, job_id=digest(profile + "/" + stage + "/" + identity),
                       request_sha256=entries[0]["request_sha256"], code_sha256=next(iter(codes), None))
            for key in ("policy_aliases", "source_labels", "artifact_paths", "representations", "scenario_names", "excluded_checkpoint_paths", "notes"):
                row[key] = sorted({value for entry in entries for value in entry[key]})
            coverage = {entry["coverage"] for entry in entries}
            row["coverage"] = next(iter(coverage)) if len(coverage) == 1 else "mixed"
            for key in ("scenario_records", "saved_execution_records", "optimizer_nfev", "optimizer_seconds",
                        "transitions", "worker_wall_seconds", "cache_hits", "cache_misses", "cache_scenarios_measured",
                        "artifact_cache_hits", "artifact_cache_misses"):
                row[key] = measured_sum(entry[key] for entry in entries)
            peaks = [entry["cache_peak_entries"] for entry in entries]
            row["cache_peak_entries"] = max(peaks) if peaks and all(value is not None for value in peaks) else None
            states = {entry["cache_status"] for entry in entries}
            row["cache_status"] = next(iter(states)) if len(states) == 1 else "mixed"
            row["cache_scenario_records"] = [dict(artifact=entry["artifact_paths"][0], scenario=name, **counters)
                for entry in entries for name, counters in zip(entry["scenario_names"], entry["cache_scenario_records"])]
            if len(entries) > 1:
                row["notes"].append("One shared request row; distinct saved worker executions are summed, not charged once per alias.")
            output.append({key: row[key] for key in EVALUATION_COLUMNS})
    return output


def summarize(root=ROOT):
    framework = read(root / "framework_budget/api_budget.json")
    baek = read(root / "baek/budget.json")
    rows = {}
    for profile in ("primary", "extended"):
        for arm in ("one_query", "best_of_n", "evolution"):
            for repeat in (1, 2, 3):
                rows[profile, arm, repeat] = dict(
                    profile=profile, arm=arm, repeat=repeat, api_requests=0,
                    api_known_usd=0., api_held_usd=0., input_tokens=0, output_tokens=0,
                    api_elapsed_seconds=0., candidates=0, valid_candidates=0,
                    invalid_candidates=0, fit_objective_calls=0,
                    fit_worker_wall_seconds=0., fit_transitions=0,
                )
    for req in framework["requests"].values():
        meta = req.get("metadata", {})
        key = (meta.get("profile", "primary"), meta.get("arm"), meta.get("repeat"))
        if key not in rows:
            raise ValueError(f"Unattributed framework request: {meta}")
        row = rows[key]
        row["api_requests"] += 1
        row["api_known_usd"] += req.get("actual_cost_usd") or 0.
        if req.get("state") != "complete":
            row["api_held_usd"] += req.get("reserved_usd", 0.)
        usage = req.get("usage", {})
        row["input_tokens"] += usage.get("prompt_tokens", 0)
        row["output_tokens"] += usage.get("completion_tokens", 0)
        row["api_elapsed_seconds"] += req.get("elapsed_seconds", 0.)
    for (profile, arm, repeat), row in rows.items():
        run = root if profile == "primary" else root / "extended"
        folder = run / "search" / f"{arm}_r{repeat}"
        row["completed"] = (folder / "completed.json").exists()
        for path in sorted(folder.glob("candidate_*/fit.json")):
            fitted = read(path)
            row["candidates"] += 1
            valid = bool(fitted.get("valid"))
            row["valid_candidates"] += int(valid)
            row["invalid_candidates"] += int(not valid)
            row["fit_worker_wall_seconds"] += fitted.get("wall_seconds", 0.)
            row["fit_transitions"] += fitted.get("transitions", 0)
            row["fit_objective_calls"] += sum(x.get("nfev", 0) for x in fitted.get("results", {}).values())
    numeric = list(rows.values())
    tool_rows = []
    for profile, run in (("primary", root / "baek"), ("extended", root / "baek/extended")):
        for repeat in (1, 2, 3):
            path = run / "sessions" / f"l2_r{repeat}" / "result.json"
            result = read(path) if path.exists() else {}
            usage = result.get("usage", {})
            tool_rows.append(dict(profile=profile, arm="baek", repeat=repeat,
                completed=result.get("status") == "completed", status=result.get("status", "pending"),
                api_requests=result.get("requests"), api_known_usd=result.get("cost_usd"),
                api_held_usd=result.get("uncertain_cost_usd"), input_tokens=usage.get("input_tokens"),
                output_tokens=usage.get("output_tokens"), tool_calls=result.get("tool_calls"),
                python_seconds=result.get("python_seconds")))
    fees = {}
    for name, ledger, settled, held_key in (("framework", framework, "complete", "reserved_usd"),
                                             ("baek", baek, "known", "upper_usd")):
        requests = list(ledger["requests"].values())
        fees[name] = dict(states=dict(Counter(x.get("state") for x in requests)),
            known_usd=sum(x.get("actual_cost_usd") or 0. for x in requests),
            held_usd=sum(x.get(held_key, 0.) for x in requests if x.get("state") != settled),
            allocated_usd=ledger["limit_usd"])
    total = sum(x["known_usd"] + x["held_usd"] for x in fees.values())
    if total > 50.000001:
        raise ValueError(f"Known plus held charges exceed user budget: {total}")
    evaluation_resources = numerical_evaluation_resources(root)
    result = dict(created_utc=datetime.now(timezone.utc).isoformat(), budget=fees,
        total_known_usd=sum(x["known_usd"] for x in fees.values()),
        total_held_usd=sum(x["held_usd"] for x in fees.values()),
        numeric=numeric, baek=tool_rows, numerical_evaluation_resources=evaluation_resources,
        notes=["Monetary ledgers cover both phases and retain truncated/failed API responses.",
               "Numerical fit counts exclude common baselines, validation, final refit and final test.",
               "Invalid fits do not return objective counts or worker timings; their compute is missing, not zero.",
               "Archived repaired attempts remain on disk but cannot be included in fit counters if no timings were saved.",
               "Baek's reported Python seconds are tool execution wall time; they are not matched simulator transitions.",
               "Parallel task times are summed work durations, not elapsed overnight duration.",
               "Unfinished Baek sessions appear pending here; all their settled requests are already in budget totals.",
               "The separate numerical_evaluation_resources list adds initial baseline fits, validation, final refits and tuned/default scoring to the existing search-only numeric rows.",
               "Complete refit aggregates replace their checkpoint parts; partial refits count available checkpoint jobs only. These are recorded finished worker executions, not a complete CPU audit of failed unsaved workers.",
               "Shared cache artifacts are attributed once with all known policy aliases. Separate scoring filenames execute independent workers even for an identical request; those executions are summed in one request row.",
               "Action-cache hit/miss counters are distinct from artifact-cache reuse; the latter was not instrumented and remains null. Missing old resource metadata remains null, never zero.",
               "The separate numerical list covers optimizer-pipeline workers and common baselines. Baek tool/setup/scoring and exact-DP diagnostic work have different accounting scopes and are not silently added to these optimizer totals."])
    atomic_json(root / "resource_summary.json", result)
    for filename, records in (("numeric_resources.csv", numeric), ("baek_resources.csv", tool_rows)):
        path = root / "tables" / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(records[0]))
            writer.writeheader()
            writer.writerows(records)
    path = root / "tables/numerical_evaluation_resources.csv"
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=EVALUATION_COLUMNS)
        writer.writeheader()
        for row in evaluation_resources:
            writer.writerow({key: json.dumps(value, ensure_ascii=False, sort_keys=True)
                             if isinstance(value, (list, dict)) else value for key, value in row.items()})
    return result


def self_test():
    """Synthetic metadata only: no final data, policies or network calls."""
    with tempfile.TemporaryDirectory(prefix="nonsearch_resources_qa_") as temporary:
        root = Path(temporary)
        code = "def compute_order_amount(age, pipeline, mu, cv, f, L):\n    return 1\n"
        code_sha = digest(code)
        names = sorted(f"perish_m{m}_L2_cv{cv:g}_f{f:g}" for m in (3, 4, 5) for cv in (1.5, 2.) for f in (0., .5))
        def job(scenarios, *, request=None, cache=False, aggregate=False, nfev=2):
            value = dict(code_sha256=code_sha, wall_seconds=10. * len(scenarios), transitions=100. * len(scenarios),
                         results={name: dict(theta=[1.], nfev=nfev, seconds=2., cost=987654321.,
                                             path_costs=[987654321.], metrics=[987654321.]) for name in scenarios})
            if request:
                value["request_sha256"] = request
            if cache:
                if aggregate:
                    value["action_cache_by_scenario"] = {name: dict(enabled=True, scenarios={name: dict(hits=70, misses=30, peak_entries=9)}) for name in scenarios}
                else:
                    value["action_cache"] = dict(enabled=True, scenarios={name: dict(hits=70, misses=30, peak_entries=9) for name in scenarios})
            return value
        baseline = dict(job([names[0]], nfev=3), code=code, valid=True)
        atomic_json(root / "baselines/constant/fit.json", baseline)
        theta = {names[0]: [1.]}
        vkey = digest(code + json.dumps(theta, sort_keys=True))[:20]
        atomic_json(root / "validation" / f"{vkey}.json", job([names[0]], request="validation-request", nfev=0))
        aliases = ("one_query_r1", "best_of_n_r1")
        for label in aliases:
            atomic_json(root / "selected" / f"{label}.json", dict(selected=dict(code=code),
                        choices=[dict(code=code, train_theta=theta, origin="candidate_00_0", validation=123456789.)]))
        atomic_json(root / "numeric_policies_freeze.json", dict(artifacts={label: dict(code=code) for label in aliases}))
        aggregate_path = root / "refit" / f"{code_sha[:20]}.json"
        atomic_json(aggregate_path, job(names, request="full-refit", cache=True, aggregate=True))
        for name in names:
            atomic_json(root / "refit_parts" / code_sha[:20] / f"{name}.json", job([name], request="part-" + name, cache=True))
        for label in aliases:
            atomic_json(root / "test" / f"{label}.json", job(names, request="same-tuned-score", cache=True, nfev=0))
        atomic_json(root / "test/one_query_r1_without_tuning.json", job(names, request="raw-score", nfev=0))
        # Combined Baek outcomes are views, not optimizer executions.
        atomic_json(root / "test/baek_r1.json", dict(results={"s": dict(cost=987654321.)}))
        rows = numerical_evaluation_resources(root)
        selected = lambda stage: [row for row in rows if row["stage"] == stage]
        refits = selected("final_refit")
        assert len(refits) == 1 and refits[0]["coverage"] == "complete"
        assert refits[0]["optimizer_nfev"] == 24 and refits[0]["worker_wall_seconds"] == 120
        assert len(refits[0]["excluded_checkpoint_paths"]) == 12
        assert refits[0]["cache_hits"] == 840 and refits[0]["cache_misses"] == 360
        assert refits[0]["cache_peak_entries"] == 9 and set(aliases) <= set(refits[0]["policy_aliases"])
        validation = selected("validation")[0]
        assert len(validation["policy_aliases"]) == 3 and validation["saved_execution_records"] == 1
        assert validation["cache_hits"] is None and validation["artifact_cache_hits"] is None
        tuned = selected("final_scoring_tuned")[0]
        assert tuned["saved_execution_records"] == 2 and tuned["worker_wall_seconds"] == 240
        assert tuned["optimizer_nfev"] == 0 and tuned["policy_aliases"] == sorted(aliases)
        assert selected("final_scoring_defaults")[0]["cache_hits"] is None
        assert "987654321" not in json.dumps(rows) and "123456789" not in json.dumps(rows)
        # Incomplete aggregate cannot suppress its actual completed checkpoints.
        atomic_json(aggregate_path, job([names[0]], request="incomplete"))
        for name in names[2:]:
            (root / "refit_parts" / code_sha[:20] / f"{name}.json").unlink()
        rows = numerical_evaluation_resources(root)
        partial = [row for row in rows if row["stage"] == "final_refit"]
        assert len(partial) == 2 and sum(row["optimizer_nfev"] for row in partial) == 4
        assert sum(row["worker_wall_seconds"] for row in partial) == 20
        assert all(row["coverage"] == "partial" for row in partial)
        # Missing metadata on old files remains null even when another row has
        # new counters; scenario labels retain their own counter association.
        mixed = job([names[1], names[0]], cache=True, aggregate=True)
        mixed["action_cache_by_scenario"].pop(names[1])
        mixed["results"][names[1]].pop("nfev")
        stats = result_metadata(mixed)
        assert stats["cache_status"] == "mixed" and stats["cache_hits"] is None
        assert stats["optimizer_nfev"] is None and stats["cache_scenarios_measured"] == 1
        assert stats["cache_scenario_records"][0]["hits"] == 70 and stats["cache_scenario_records"][1]["hits"] is None
        extended = root / "extended"
        extended_names = sorted(f"perish_m{m}_L2_cv{cv:g}_f{f:g}" for m in (7, 8) for cv in (1.5, 2.) for f in (0., .5))
        atomic_json(extended / "numeric_policies_freeze.json", dict(artifacts={"evolution_r3": dict(code=code)}))
        old_aggregate = job(extended_names, request="old-extended-refit")
        old_aggregate["action_cache"] = dict(enabled=False)
        atomic_json(extended / "refit" / f"{code_sha[:20]}.json", old_aggregate)
        atomic_json(extended / "refit_parts" / code_sha[:20] / f"{extended_names[0]}.json", job([extended_names[0]]))
        extended_rows = [row for row in numerical_evaluation_resources(root) if row["profile"] == "extended"]
        assert len(extended_rows) == 1 and extended_rows[0]["coverage"] == "complete"
        assert extended_rows[0]["optimizer_nfev"] == 16 and extended_rows[0]["worker_wall_seconds"] == 80
        assert extended_rows[0]["policy_aliases"] == ["evolution_r3"]
        assert extended_rows[0]["cache_status"] == "disabled" and extended_rows[0]["cache_hits"] is None
        assert len(extended_rows[0]["excluded_checkpoint_paths"]) == 1
        # Run complete resource aggregation only against these synthetic files.
        atomic_json(root / "framework_budget/api_budget.json", dict(limit_usd=35., requests={
            "a": dict(state="complete", actual_cost_usd=1.25, metadata=dict(arm="one_query", repeat=1))}))
        atomic_json(root / "baek/budget.json", dict(limit_usd=12., requests={
            "b": dict(state="known", actual_cost_usd=.75), "c": dict(state="uncertain", upper_usd=.5)}))
        result = summarize(root)
        assert result["total_known_usd"] == 2. and result["total_held_usd"] == .5
        assert len(result["numeric"]) == 18 and len(result["baek"]) == 6
        assert result["numeric"][0]["api_known_usd"] == 1.25
        assert (root / "tables/numerical_evaluation_resources.csv").exists()
        assert "987654321" not in (root / "tables/numerical_evaluation_resources.csv").read_text()
        # Empty phases/files produce an empty table, not fabricated zero jobs.
        assert numerical_evaluation_resources(root / "empty") == []
    return dict(complete_refit="aggregate counted once", partial_refit="checkpoints only",
                shared_methods="one row with aliases", duplicate_scoring="actual worker records summed",
                old_and_new_cache_metadata="passed; missing remains null", monetary_accounting="unchanged",
                phase_attribution="primary and extended kept separate",
                outcome_values="not returned", synthetic_only=True, api_calls=0, policy_evaluations=0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        print(json.dumps(self_test(), indent=2))
    else:
        result = summarize()
        print(json.dumps({k: result[k] for k in ("total_known_usd", "total_held_usd", "budget")}, indent=2))
