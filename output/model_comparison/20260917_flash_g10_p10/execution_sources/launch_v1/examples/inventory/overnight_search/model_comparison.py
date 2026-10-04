"""Same-workflow backbone comparison; all paid operations are explicit CLI steps.

prepare and baselines never call a model. run-model requires a confirmed endpoint
configuration. Final testing is blocked until all model/repetition artifacts are
frozen. Old experimental sources/results are read-only references.
"""
from __future__ import annotations

import argparse
import ast
from dataclasses import asdict
from datetime import datetime, timezone
import fcntl
import hashlib
import json
from pathlib import Path

import numpy as np

from .model_comparison_client import atomic_json
from .model_comparison_numeric import evaluate_comparison
from .perishable import Scenario
from .search import PROBLEM, extract, seed_codes


DEFAULT_RUN = Path(__file__).resolve().parents[3] / "output/model_comparison/20260917"


def read(path):
    return json.loads(Path(path).read_text())


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def immutable(path, value):
    path = Path(path)
    if path.exists():
        if read(path) != value:
            raise ValueError(f"Frozen record mismatch: {path}")
    else:
        atomic_json(path, value)
    return value


def specifications():
    return [asdict(Scenario(f"perish_m{m}_L2_cv{cv:g}_f{f:g}", m=m, L=2, cv=cv, f=f))
            for m in (3, 4, 5, 7, 8) for cv in (1.5, 2.) for f in (0., .5)]


def common_codes():
    codes = seed_codes()
    codes["flexible_age_weights"] = '''def compute_order_amount(age, pipeline, mu, cv, f, L):
    S = 14.0 # OPT_PARAM: {"type":"float","initial":14.0,"min":0.0,"max":60.0}
    C = 8.0 # OPT_PARAM: {"type":"float","initial":8.0,"min":0.0,"max":30.0}
    P = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":3.0}
    W_old = 0.1 # OPT_PARAM: {"type":"float","initial":0.1,"min":0.0,"max":4.0}
    W_mid = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":4.0}
    W_new = 1.0 # OPT_PARAM: {"type":"float","initial":1.0,"min":0.0,"max":4.0}
    effective = P * sum(pipeline)
    for i in range(len(age)):
        z = i / max(1, len(age)-1)
        if z <= 0.5:
            weight = W_old + 2*z*(W_mid-W_old)
        else:
            weight = W_mid + (2*z-1)*(W_new-W_mid)
        effective = effective + weight*age[i]
    return max(0.0, min(C, S-effective))
'''
    return codes


def prepare(root):
    root.mkdir(parents=True, exist_ok=True)
    draft = read(root / "protocol_draft.json")
    settings = {key: value for key, value in draft.items()
                if key not in {"status", "paid_requests_sent", "created_utc"}}
    settings["common_seeds"] = {
        "code_sha256": {k: hashlib.sha256(v.encode()).hexdigest() for k, v in common_codes().items()},
        "provenance": "Four standard seeds plus flexible age weights based on prior source/training inspection; common to every backbone, not LLM discoveries in this run."}
    immutable(root / "protocol.json", settings)
    immutable(root / "scenarios.json", specifications())
    immutable(root / "common_seed_codes.json", common_codes())
    return settings


def seed_for(phase, repeat, scenario=""):
    raw = f"model_comparison_v1:{phase}:{repeat}:{scenario}".encode()
    return int.from_bytes(hashlib.sha256(raw).digest()[:4], "big") % (2**31 - 1)


def make_job(root, code, phase, repeat, *, specs=None, warm_starts=None, theta=None):
    config = read(root / "protocol.json")
    stage = {k: v for k, v in config["stages"][phase].items() if k != "top_k"}
    if specs is None:
        specs = [s for s in specifications() if s["m"] in config["discovery_m"]]
    job = dict(op="fit" if phase in {"train", "promote", "refit"} else "evaluate",
               code=code, scenarios=specs, seed=seed_for(phase, repeat),
               scenario_seeds={s["name"]: seed_for(phase, repeat, s["name"]) for s in specs},
               optimizer_seed=seed_for("optimizer", repeat), cache_actions=True, **stage)
    if warm_starts is not None:
        job["warm_starts"] = warm_starts
    if theta is not None:
        job["theta"] = theta
    return job


def saved_job(path, job, timeout=3600):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.with_suffix(".lock").open("a+") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        return _saved_job_locked(path, job, timeout)


def _saved_job_locked(path, job, timeout):
    request_hash = fingerprint(job)
    if path.exists():
        result = read(path)
        if result.get("request_sha256") != request_hash:
            raise ValueError(f"Numerical cache collision: {path}")
        return result
    immutable(path.with_suffix(".request.json"), job)
    result = evaluate_comparison(job, timeout=timeout, log_path=path.with_suffix(".worker.json"))
    atomic_json(path, result)
    return result


def mean_score(record, denominators):
    if not record.get("valid"):
        return float("inf")
    return float(np.mean([r["cost"] / denominators[name]
                          for name, r in record["results"].items()]))


def fitted_theta(record):
    return {s: r["theta"] for s, r in record["results"].items()}


def make_baselines(root, repeat):
    prepare(root)
    results = {}
    for name, code in common_codes().items():
        folder = root / "common" / f"r{repeat}" / name
        immutable(folder / "source.json", {"code": code})
        record = saved_job(folder / "train.json", make_job(root, code, "train", repeat))
        if not record["valid"]:
            raise ValueError(f"Shared baseline did not finish: {name}")
        results[name] = {"origin": "common:" + name, "code": code, "train": record}
        print("BASELINE", repeat, name, flush=True)
    denominators = {s: min(row["train"]["results"][s]["cost"] for row in results.values())
                    for s in next(iter(results.values()))["train"]["results"]}
    immutable(root / "common" / f"r{repeat}" / "denominators.json", denominators)
    for row in results.values():
        row["score"] = mean_score(row["train"], denominators)
    return results, denominators


def parameters_from_code(code):
    output = {}
    for line in code.splitlines():
        if "OPT_PARAM:" in line:
            metadata = json.loads(line.split("OPT_PARAM:", 1)[1].strip())
            assignment = ast.parse(line.split("#", 1)[0].strip()).body[0]
            if not isinstance(assignment, ast.Assign) or len(assignment.targets) != 1:
                raise ValueError("Invalid parameter declaration")
            output[assignment.targets[0].id] = (float(ast.literal_eval(assignment.value)), metadata)
    return output


def mapped_warm_starts(code, parents):
    """Same-name coefficients are suggestions only, re-evaluated within budget."""
    declared = parameters_from_code(code)
    output = {}
    for parent in parents[:2]:
        previous = parent["train"]
        old_names = list(previous["parameters"])
        for scenario, row in previous["results"].items():
            old = dict(zip(old_names, row["theta"]))
            values = [min(meta["max"], max(meta["min"], old.get(name, literal)))
                      for name, (literal, meta) in declared.items()]
            output.setdefault(scenario, []).append(values)
    return output


def prompt_for(index, pool, baseline_rows, failures, *, independent_initial_candidates=4):
    text = PROBLEM.replace("shelf life m in {3,4,5}", "shelf life m in {3,4,5,7,8}")
    text = text.replace("No exact test instances are disclosed.",
                        "The full parameter grid is public. Performance on m=4 and m=8 is withheld from structural-search feedback.")
    text = text.replace("Actions are rounded half-to-even, then clipped to [0,max(0,cap-sum(age)-sum(pipeline))].",
                        "Actions are first clipped to [0,max(0,cap-sum(age)-sum(pipeline))], then rounded half-to-even.")
    text = text.replace("Avoid scipy in the per-period policy: this numerical subset is shared by all three structure arms.\nThe separate unrestricted tool-enabled Baek baseline can use arbitrary NumPy/SciPy designs.",
                        "Avoid scipy in the per-period policy: this numerical subset is shared by all compared backbones.")
    text += '''
EXPERIMENT CONTRACT
You are one backbone in a common evolve-and-optimize workflow. All backbones
receive identical initial information and numerical budgets; do not assume a
desired winner. Propose ONE self-contained policy function in a Python fence.
The host numerically tunes constants separately by instance, so focus on useful
state dependence, plausible initialization, and sensible coefficient ranges.
There is no parameter-count limit. Keep each decision lightweight: do not run
simulation, dynamic programming, or an optimizer inside the per-period action.
The host uses derivative-free optimization and returns its actual coefficients,
cost components and execution diagnostics. Structural complexity alone is not
a benefit. A simple rule is acceptable when its validation is competitive.
Use the feedback to distinguish poor structure from incompletely tuned parameters.
Explore a different representation when repeated refinements stop helping.
Runtime/memory failures are real experimental outcomes; simplify an expensive
implementation rather than silently changing the problem or information set.
Return executable policy code only, with OPT_PARAM declarations for constants.
'''
    initial = index < independent_initial_candidates
    selected = sorted(baseline_rows if initial else pool, key=lambda r: r["score"])[:3]
    text += ("\nIndependently propose a strong initial structure.\n" if initial else
             "\nImprove an existing structure or propose a distinct alternative using the feedback below.\n")
    for parent in selected:
        detail = {s: {"cost": row["cost"], "theta": dict(zip(parent["train"]["parameters"], row["theta"])),
                      "waste_lost_order": row["metrics"], "objective_calls": row["nfev"],
                      "optimizer_seconds": row.get("seconds"), "simulated_transitions": row.get("transitions")}
                  for s, row in parent["train"]["results"].items()}
        text += "\nCandidate " + parent["origin"] + "; normalized mean cost " + str(parent["score"]) + "\n"
        text += json.dumps(detail) + "\n" + parent["code"] + "\n"
    if failures and not initial:
        text += "\nRecent execution failures:\n" + json.dumps(failures[-3:])
    return text


def generation_plan(config):
    """Absent generation fields retain the original sequential search protocol."""
    if not any(key in config for key in ("generations", "proposals_per_generation")):
        return None
    generations = config.get("generations")
    width = config.get("proposals_per_generation")
    if any(type(value) is not int or value <= 0 for value in (generations, width)):
        raise ValueError("Generations and proposals_per_generation must both be positive integers")
    total = generations * width
    if config.get("generated_candidates_per_repetition") != total or config.get("total", total) != total:
        raise ValueError("Generation dimensions must equal the declared candidate total")
    if config.get("independent_initial_candidates") != width:
        raise ValueError("The full first generation must be independent")
    return generations, width


PROPOSAL_STYLES = (
    "Start with a compact, interpretable rule and improve its useful state dependence.",
    "Explore how age-dependent inventory weights should vary with remaining shelf life.",
    "Explore lightweight predictions of depletion or expiry before replenishment arrives.",
    "Explore smooth interactions between on-hand age composition and pipeline inventory.",
    "Explore a small number of meaningful hinges or thresholds in inventory state.",
    "Explore how order caps or replenishment targets should depend on age composition.",
    "Explore a complementary structure that combines useful features of the supplied rules.",
    "Explore simplification or reparameterization that makes numerical tuning easier.",
    "Explore a distinct nonlinear representation with sensible scales and initialization.",
    "Use your own judgment to propose a different promising lightweight policy structure.",
)


def generation_prompt(generation, proposal, snapshot, baseline_rows, width):
    text = prompt_for(0 if generation == 0 else width, snapshot["pool"], baseline_rows,
                      snapshot["failures"], independent_initial_candidates=width)
    text += (f"\nGENERATION CONTRACT\nGeneration {generation + 1}, proposal {proposal + 1} of {width}.\n"
             "Every proposal in this generation receives the same parent and failure snapshot, frozen before any proposal in this generation.\n"
             "No sibling proposal, training result, or failure from this generation is available.\n"
             + ("This is an independent initial proposal using only the common seed information.\n" if generation == 0 else
                "Only candidates from completed earlier generations and the common seeds may inform this proposal.\n")
             + "Proposal emphasis (guidance, not a restriction): " + PROPOSAL_STYLES[proposal % len(PROPOSAL_STYLES)] + "\n")
    return text


def save_generation_summary(folder, snapshot, rows, pool, *, status=None):
    def best(items):
        if not items:
            return None
        row = min(items, key=lambda item: item["score"])
        return {"origin": row["origin"], "score": row["score"],
                "source_kind": "common_seed" if row["origin"].startswith("common:") else "generated"}
    expected = snapshot["proposals_expected"]
    output = {
        "schema_version": 1, "generation_index": snapshot["generation_index"],
        "generation_number": snapshot["generation_index"] + 1,
        "status": status or ("complete" if len(rows) == expected else "running"),
        "proposals_expected": expected, "proposals_recorded": len(rows),
        "valid": sum(bool(row["valid"]) for row in rows),
        "invalid": sum(not row["valid"] for row in rows),
        "input_sha256": fingerprint(snapshot),
        "metric": "mean_training_cost_ratio_to_common_baseline",
        "best_before": best(snapshot["pool"]), "best_after": best(pool),
        "best_generated_so_far": best([row for row in pool if not row["origin"].startswith("common:")]),
        "candidates": [{"index": row["index"], "origin": row["origin"], "valid": row["valid"],
                        "score": row.get("score"), "error": row.get("error"),
                        "code_sha256": hashlib.sha256(row["code"].encode()).hexdigest() if row.get("code") else None,
                        "generation_provenance": row.get("generation_provenance")}
                       for row in rows],
    }
    atomic_json(folder / "summary.json", output)
    return output


def configured_models(root):
    catalog = read(root / "models.json")
    models = catalog["models"]
    if len({m["slug"] for m in models}) != len(models):
        raise ValueError("Duplicate model slug")
    protocol = read(root / "protocol.json")
    if protocol.get("comparison_mode") == "standalone_flash":
        if (len(models) != 1 or models[0].get("role") != "candidate"
                or models[0].get("client", {}).get("model") != "deepseek-flash"):
            raise ValueError("Standalone Flash mode requires exactly one deepseek-flash candidate and no control")
    elif sum(m["role"] == "control" for m in models) != 1:
        raise ValueError("Exactly one same-workflow control is required")
    immutable(root / "models_frozen.json", catalog)
    return models


def make_client(root, model, repeat):
    from .model_comparison_client import ClientConfig, FrozenPricing, ModelComparisonClient
    data = dict(model["client"])
    data["client_id"] = data["client_id"] + f"_r{repeat}"
    data["pricing"] = FrozenPricing(**data["pricing"])
    if not data.get("endpoint_confirmed"):
        raise ValueError("Provider endpoint/model must be confirmed before model requests")
    config = ClientConfig(**data)
    credentials_path = Path(model["credentials_path"]).expanduser()
    return ModelComparisonClient(config, budget_directory=root / "api_budget",
        limit_usd=read(root / "protocol.json")["new_experiment_limit_usd"],
        credentials_path=credentials_path,
        credential_index=model.get("credential_indices", [0, 0, 0])[repeat-1],
        allow_network=True)


def run_model(root, slug, repeat):
    config = prepare(root)
    plan = generation_plan(config)
    llm_max_tokens = config.get("llm_max_output_tokens", 32768)
    if type(llm_max_tokens) is not int or llm_max_tokens <= 0:
        raise ValueError("llm_max_output_tokens must be a positive integer")
    model = next(m for m in configured_models(root) if m["slug"] == slug)
    folder = root / "runs" / slug / f"r{repeat}"
    immutable(folder / "model_config.json", model)
    if (folder / "api_incomplete.json").exists():
        raise RuntimeError(f"Repetition {slug}/r{repeat} has an unresolved API opportunity; no automatic retry")
    if (folder / "completed.json").exists():
        return read(folder / "completed.json")
    baselines, denominators = make_baselines(root, repeat)
    pool = list(baselines.values())
    failures = []
    client = make_client(root, model, repeat)
    generation_rows = []
    for index in range(config["generated_candidates_per_repetition"]):
        provenance = None
        if plan is not None:
            generation, proposal = divmod(index, plan[1])
            generation_folder = folder / "generations" / f"{generation:02d}"
            if proposal == 0:
                # A deep copy ensures appending a fitted sibling cannot mutate
                # this immutable parent/feedback snapshot in memory or on disk.
                snapshot = immutable(generation_folder / "input.json", json.loads(json.dumps({
                    "schema_version": 1, "generation_index": generation,
                    "proposals_expected": plan[1], "first_candidate_index": index,
                    "independent_initial": generation == 0,
                    "protocol_sha256": fingerprint(config), "denominators_sha256": fingerprint(denominators),
                    "pool": pool, "failures": failures})))
                generation_rows = []
                save_generation_summary(generation_folder, snapshot, generation_rows, pool)
            feedback_pool, feedback_failures = snapshot["pool"], snapshot["failures"]
            parents = sorted(feedback_pool, key=lambda row: row["score"])[:2] if generation > 0 else []
            provenance = {"generation_index": generation, "proposal_index": proposal,
                          "input_sha256": fingerprint(snapshot), "warm_start_parent_origins": [row["origin"] for row in parents],
                          "feedback_parent_origins": [row["origin"] for row in sorted(feedback_pool, key=lambda row: row["score"])[:3]],
                          "proposal_style": PROPOSAL_STYLES[proposal % len(PROPOSAL_STYLES)]}
        else:
            feedback_pool, feedback_failures = pool, failures
            parents = sorted(pool, key=lambda row: row["score"])[:2] if index >= 4 else []
        candidate_dir = folder / "candidates" / f"{index:02d}"
        if provenance is not None:
            immutable(candidate_dir / "generation_provenance.json", provenance)
        record_path = candidate_dir / "record.json"
        if record_path.exists():
            row = read(record_path)
            if provenance is not None and row.get("generation_provenance") != provenance:
                raise ValueError("Saved candidate has different generation provenance")
        else:
            prompt = (generation_prompt(generation, proposal, snapshot, list(baselines.values()), plan[1])
                      if plan is not None else prompt_for(index, feedback_pool, list(baselines.values()), feedback_failures))
            immutable(candidate_dir / "prompt.json", {"messages": [{"role": "user", "content": prompt}]})
            response_path = candidate_dir / "response.json"
            attempt_path = candidate_dir / "api_attempt.json"
            failure_path = candidate_dir / "api_failure.json"
            opportunity = {"slug": slug, "repeat": repeat, "candidate": index}

            def ledger_attempts():
                # Older runs may have reserved/sent before this checkpoint
                # existed. Link only the exact opportunity, never inspect
                # provider response bodies, credentials or reasoning text.
                with client.ledger.locked() as ledger:
                    return [{"request_id": request_id, **{key: entry.get(key) for key in
                             ("state", "reserved_usd", "actual_cost_usd", "estimated_upper_usd",
                              "http_status", "error_type")}}
                            for request_id, entry in ledger["requests"].items()
                            if all(entry.get("metadata", {}).get(key) == value
                                   for key, value in opportunity.items())]

            def save_api_failure(reason, error_type=None, *, blocks_repetition=True):
                failure = {"opportunity": opportunity, "reason": reason, "error_type": error_type,
                           "ledger_attempts": ledger_attempts(), "automatic_retry_allowed": False,
                           "blocks_repetition": blocks_repetition,
                           "recorded_utc": datetime.now(timezone.utc).isoformat()}
                atomic_json(failure_path, failure)
                atomic_json(root / "api_summary.json", client.summary())
                if blocks_repetition:
                    atomic_json(folder / "api_incomplete.json", {"status": "incomplete_api_failure", **failure})
                return failure

            def recover_settled_receipt(attempts):
                # A usable receipt must have completed ledger settlement, not
                # merely been written just before a crash. Pending/unknown money
                # stays held and stops the repetition for explicit review.
                if (len(attempts) != 1 or attempts[0]["state"] not in {"actual", "pricing_upper_estimate"}
                        or client.summary().get("paused_reason")):
                    return None
                receipt_path = client.ledger.directory / "requests" / attempts[0]["request_id"] / "response.json"
                if not receipt_path.exists():
                    return None
                try:
                    receipt = read(receipt_path)
                    if (receipt.get("request_id") != attempts[0]["request_id"]
                            or receipt.get("model_matches") is not True
                            or receipt.get("bounds_exceeded") is not False
                            or receipt.get("accounting_error") is not None
                            or receipt.get("cost_status") != attempts[0]["state"]):
                        return None
                    parse_failure = receipt.get("response_error")
                    if parse_failure is None and (receipt.get("finish_reason") != "stop"
                                                 or not isinstance(receipt.get("content"), str)):
                        return None
                    return {"content": receipt["content"] if parse_failure is None else "",
                            "usage": {key: value for key, value in receipt.items() if key != "content"},
                            "recovered_from": str(receipt_path)}
                except (OSError, ValueError, TypeError, KeyError):
                    return None

            if response_path.exists():
                response = read(response_path)
            else:
                # The lock prevents two resumed processes from passing the
                # pre-POST check together. The durable marker survives crashes
                # at every later point, including before a ledger receipt exists.
                with (candidate_dir / ".api_request.lock").open("a+") as request_lock:
                    fcntl.flock(request_lock.fileno(), fcntl.LOCK_EX)
                    if response_path.exists():
                        response = read(response_path)
                    else:
                        attempts = ledger_attempts()
                        response = recover_settled_receipt(attempts)
                        if response is not None:
                            atomic_json(response_path, response)
                            atomic_json(root / "api_summary.json", client.summary())
                        elif attempt_path.exists() or attempts:
                            save_api_failure("A prior request opportunity has no recoverable successful response; it will not be sent again")
                        else:
                            immutable(attempt_path, {"opportunity": opportunity,
                                "prompt_sha256": fingerprint({"messages": [{"role": "user", "content": prompt}]}),
                                "started_utc": datetime.now(timezone.utc).isoformat(),
                                "automatic_retry_allowed": False})
                            try:
                                content, usage = client.chat([{"role": "user", "content": prompt}], max_tokens=llm_max_tokens,
                                                            metadata=opportunity)
                            except Exception as error:
                                # Never persist arbitrary exception text: an
                                # HTTP body/transport exception can contain keys.
                                response = recover_settled_receipt(ledger_attempts())
                                if response is None:
                                    failure = save_api_failure("Request failed; repetition is incomplete and this opportunity will not be resent",
                                                               type(error).__name__)
                                    failed_row = {"origin": f"{slug}/r{repeat}/{index:02d}", "index": index,
                                        "valid": False, "error": "Model request failed; see sanitized api_failure.json",
                                        "api_failure": failure}
                                    if provenance is not None:
                                        failed_row["generation_provenance"] = provenance
                                    atomic_json(record_path, failed_row)
                                    if plan is not None:
                                        save_generation_summary(generation_folder, snapshot, generation_rows + [failed_row], pool,
                                                                status="incomplete_api_failure")
                                    raise RuntimeError(f"Model request failed for {slug}/r{repeat}/{index:02d}; checkpoint saved; no automatic retry") from None
                            else:
                                response = {"content": content, "usage": usage}
                            atomic_json(response_path, response)
                            atomic_json(root / "api_summary.json", client.summary())
            if response is not None:
                usage = response.get("usage", {})
                if (usage.get("model_matches") is not True or usage.get("bounds_exceeded") is not False
                        or usage.get("accounting_error") is not None
                        or usage.get("cost_status") not in {"actual", "pricing_upper_estimate"}
                        or client.summary().get("paused_reason")):
                    save_api_failure("Provider identity, accounting or shared-ledger status is unresolved; repetition is incomplete")
                    response = None
                elif usage.get("response_error") is not None:
                    save_api_failure("Correctly attributed, settled response did not contain complete usable policy code",
                                     "SettledCodeResponseError", blocks_repetition=False)
            codes = extract(response["content"]) if response is not None else []
            row = {"origin": f"{slug}/r{repeat}/{index:02d}", "index": index, "valid": False}
            if provenance is not None:
                row["generation_provenance"] = provenance
            if response is None:
                row.update(error="Previously attempted model request has no recoverable response; no repeat POST",
                           api_failure=read(candidate_dir / "api_failure.json"))
            elif response.get("usage", {}).get("response_error") is not None:
                row.update(error="Settled model response contained invalid or incomplete policy code",
                           api_failure=read(candidate_dir / "api_failure.json"))
            elif len(codes) != 1:
                row["error"] = "Expected exactly one policy function"
            else:
                code = codes[0]
                immutable(candidate_dir / "source.json", {"code": code})
                try:
                    warm = mapped_warm_starts(code, parents)
                    fit = saved_job(candidate_dir / "train.json", make_job(root, code, "train", repeat, warm_starts=warm))
                    row.update(code=code, train=fit, valid=fit["valid"])
                    if fit["valid"]:
                        row["score"] = mean_score(fit, denominators)
                    else:
                        row["error"] = fit.get("error_type", "failed") + ": " + fit.get("error", "")[-1500:]
                except (ValueError, SyntaxError, KeyError, TypeError) as exc:
                    row["error"] = str(exc)[-1500:]
            atomic_json(record_path, row)
        if row.get("api_failure", {}).get("blocks_repetition", bool(row.get("api_failure"))):
            atomic_json(folder / "api_incomplete.json", {"status": "incomplete_api_failure", **row["api_failure"]})
            if plan is not None:
                save_generation_summary(generation_folder, snapshot, generation_rows + [row], pool, status="incomplete_api_failure")
            raise RuntimeError(f"Repetition {slug}/r{repeat} has an unresolved API opportunity; no automatic retry")
        if row["valid"]:
            pool.append(row)
        else:
            failures.append({"origin": row["origin"], "error": row.get("error", "failed")})
        if plan is not None:
            generation_rows.append(row)
            save_generation_summary(generation_folder, snapshot, generation_rows, pool)
        print("CANDIDATE", slug, repeat, index, row.get("score", row.get("error", "failed")), flush=True)
    completed = {"slug": slug, "repeat": repeat, "pool": pool, "failures": failures,
                 "completed_utc": datetime.now(timezone.utc).isoformat()}
    if plan is not None:
        completed["generation_protocol"] = {"generations": plan[0], "proposals_per_generation": plan[1],
                                           "generated_candidates_per_repetition": plan[0] * plan[1],
                                           "feedback": "Frozen before each generation; no within-generation feedback"}
    atomic_json(folder / "completed.json", completed)
    atomic_json(root / "api_summary.json", client.summary())
    return completed


def warm_for_all_specs(record):
    specs = {s["name"]: s for s in specifications()}
    output = {}
    for target in specs.values():
        candidates = [name for name in record["results"]
                      if specs[name]["cv"] == target["cv"] and specs[name]["f"] == target["f"]]
        source = min(candidates, key=lambda name: (abs(specs[name]["m"] - target["m"]), specs[name]["m"]))
        output[target["name"]] = [record["results"][source]["theta"]]
    return output


def select_and_freeze(root, slug, repeat):
    folder = root / "runs" / slug / f"r{repeat}"
    if (folder / "freeze.json").exists():
        return read(folder / "freeze.json")
    config = read(root / "protocol.json")
    completed = read(folder / "completed.json")
    denominators = read(root / "common" / f"r{repeat}" / "denominators.json")
    unique = {}
    for row in sorted(completed["pool"], key=lambda r: r["score"]):
        unique.setdefault(hashlib.sha256(row["code"].encode()).hexdigest(), row)
    choices = list(unique.values())[:config["stages"]["promote"]["top_k"]]
    best_seed = min((r for r in completed["pool"] if r["origin"].startswith("common:")), key=lambda r: r["score"])
    if all(r["code"] != best_seed["code"] for r in choices):
        choices.append(best_seed)
    validated = []
    selection_failures = []
    for row in choices:
        key = hashlib.sha256(row["code"].encode()).hexdigest()[:20]
        target = folder / "selection" / key
        warm = {s: [theta] for s, theta in fitted_theta(row["train"]).items()}
        promoted = saved_job(target / "promote.json", make_job(root, row["code"], "promote", repeat, warm_starts=warm))
        if not promoted["valid"]:
            selection_failures.append({"origin": row["origin"], "phase": "promote",
                                       "record": str(target / "promote.json")})
            continue
        validation = saved_job(target / "validation.json", make_job(root, row["code"], "validation", repeat, theta=fitted_theta(promoted)))
        if not validation["valid"]:
            selection_failures.append({"origin": row["origin"], "phase": "validation",
                                       "record": str(target / "validation.json")})
            continue
        validated.append({"code": row["code"], "origin": row["origin"], "promoted": promoted,
                          "validation_score": mean_score(validation, denominators)})
    if not validated:
        atomic_json(folder / "selected.json", {"selected": None, "choices": [],
                                               "failures": selection_failures})
        raise ValueError("All predeclared selection candidates failed; repetition is incomplete")
    selected = min(validated, key=lambda r: r["validation_score"])
    atomic_json(folder / "selected.json", {"selected": selected, "choices": validated,
                                           "failures": selection_failures})
    refitted = saved_job(folder / "refit.json", make_job(root, selected["code"], "refit", repeat,
                            specs=specifications(), warm_starts=warm_for_all_specs(selected["promoted"])))
    if not refitted["valid"]:
        raise ValueError("Final refit failed; final test remains sealed")
    frozen = {"slug": slug, "repeat": repeat, "code": selected["code"],
              "code_sha256": hashlib.sha256(selected["code"].encode()).hexdigest(),
              "theta": fitted_theta(refitted), "origin": selected["origin"],
              "refit_request_sha256": refitted["request_sha256"]}
    immutable(folder / "freeze.json", frozen)
    return frozen


def test_all(root):
    models = configured_models(root)
    seals = {}
    for model in models:
        for repeat in (1, 2, 3):
            path = root / "runs" / model["slug"] / f"r{repeat}" / "freeze.json"
            frozen = read(path)  # All must exist before any testing starts.
            if hashlib.sha256(frozen["code"].encode()).hexdigest() != frozen["code_sha256"]:
                raise ValueError("Frozen source mismatch")
            if set(frozen["theta"]) != {s["name"] for s in specifications()}:
                raise ValueError("Incomplete frozen parameters")
            seals[f"{model['slug']}/r{repeat}"] = fingerprint(frozen)
    immutable(root / "all_models_frozen.json", seals)
    for model in models:
        for repeat in (1, 2, 3):
            folder = root / "runs" / model["slug"] / f"r{repeat}"
            frozen = read(folder / "freeze.json")
            if fingerprint(frozen) != seals[f"{model['slug']}/r{repeat}"]:
                raise ValueError("Freeze changed after gate")
            literal = [value[0] for value in parameters_from_code(frozen["code"]).values()]
            for label, theta in [("test", frozen["theta"]), ("test_raw", {s["name"]: literal for s in specifications()})]:
                record = saved_job(folder / f"{label}.json", make_job(root, frozen["code"], "test", repeat,
                                            specs=specifications(), theta=theta))
                if not record["valid"]:
                    raise ValueError("Final scoring failed; report must remain incomplete")
            print("TESTED", model["slug"], repeat, flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["prepare", "baselines", "run-model", "freeze", "test", "report"])
    parser.add_argument("--run", type=Path, default=DEFAULT_RUN)
    parser.add_argument("--model")
    parser.add_argument("--repeat", type=int, choices=(1, 2, 3))
    args = parser.parse_args()
    root = args.run.resolve()
    if args.command == "prepare":
        prepare(root)
    elif args.command == "baselines":
        for repeat in ([args.repeat] if args.repeat else [1, 2, 3]):
            make_baselines(root, repeat)
    elif args.command in {"run-model", "freeze"}:
        if not args.model or not args.repeat:
            parser.error("--model and --repeat required")
        function = run_model if args.command == "run-model" else select_and_freeze
        function(root, args.model, args.repeat)
    elif args.command == "test":
        test_all(root)
    else:
        from .model_comparison_reporting import build_report
        build_report(root)


if __name__ == "__main__":
    main()
