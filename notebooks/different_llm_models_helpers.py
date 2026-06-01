from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


ALL_MODEL_ORDER = [
    "deepseek-chat",
    "gemini-2.5-flash-lite",
    "gemini-3-flash-preview",
    "gpt-5-mini",
    "gpt-5-nano",
    "grok-4-1-fast-non-reasoning",
]

SMARTNESS_ORDER = [
    "gpt-5-nano",
    "gemini-2.5-flash-lite",
    "grok-4-1-fast-non-reasoning",
    "gpt-5-mini",
    "deepseek-chat",
    "gemini-3-flash-preview",
]

OPTIMIZER_MODEL_ORDER = [model for model in ALL_MODEL_ORDER if model != "deepseek-chat"]

MODEL_LABELS = {
    "deepseek-chat": "DeepSeek",
    "gemini-2.5-flash-lite": "Gemini 2.5 Flash Lite",
    "gemini-3-flash-preview": "Gemini 3 Flash Preview",
    "gpt-5-mini": "GPT-5 mini",
    "gpt-5-nano": "GPT-5 nano",
    "grok-4-1-fast-non-reasoning": "Grok 4.1 fast",
}

MODEL_COLORS = {
    "deepseek-chat": "#4C78A8",
    "gemini-2.5-flash-lite": "#F58518",
    "gemini-3-flash-preview": "#54A24B",
    "gpt-5-mini": "#E45756",
    "gpt-5-nano": "#72B7B2",
    "grok-4-1-fast-non-reasoning": "#B279A2",
}

SOURCE_SHEETS = [
    {
        "sheet": "S 4.1",
        "table_label": "S 4.1",
        "scenario": "deepseek without optimizer",
        "llm_family": "deepseek",
        "optimizer_status": "without optimizer",
        "with_optimizer": False,
        "base_stock_mode": "standard",
    },
    {
        "sheet": "S 3",
        "table_label": "S 3",
        "scenario": "deepseek with optimizer",
        "llm_family": "deepseek",
        "optimizer_status": "with optimizer",
        "with_optimizer": True,
        "base_stock_mode": "standard",
    },
    {
        "sheet": "S 4.4",
        "table_label": "S 4.4",
        "scenario": "other LLMs with optimizer",
        "llm_family": "other_llms",
        "optimizer_status": "with optimizer",
        "with_optimizer": True,
        "base_stock_mode": "standard",
    },
    {
        "sheet": "S 4.4 no opt",
        "table_label": "S 4.4 no opt",
        "scenario": "other LLMs without optimizer",
        "llm_family": "other_llms",
        "optimizer_status": "without optimizer",
        "with_optimizer": False,
        "base_stock_mode": "standard",
    },
    {
        "sheet": "S 4.4 no opt extension",
        "table_label": "S 4.4 no opt extension",
        "scenario": "other LLMs without optimizer and starting from different base stock level",
        "llm_family": "other_llms",
        "optimizer_status": "without optimizer",
        "with_optimizer": False,
        "base_stock_mode": "different_base_stock",
    },
]

WORKBOOK_FRONT_COLUMNS = [
    "source_sheet",
    "table_label",
    "scenario",
    "llm_family",
    "optimizer_status",
    "with_optimizer",
    "base_stock_mode",
    "initial_basestock",
]


def build_different_llm_workbook(
    source_path="data/final results.xlsx",
    output_path="data/different_llm_models.xlsx",
):
    source_path = Path(source_path)
    output_path = Path(output_path)

    frames = []
    for spec in SOURCE_SHEETS:
        frame = pd.read_excel(source_path, sheet_name=spec["sheet"])
        if spec["sheet"] == "S 3" and "n_pop.1" in frame.columns:
            frame = frame.copy()
            frame["mode"] = frame["n_pop.1"]
        if spec["base_stock_mode"] == "different_base_stock":
            if "initial_basestock" not in frame.columns:
                raise ValueError(f"{spec['sheet']} must include initial_basestock")
        else:
            frame = frame.copy()
            frame["initial_basestock"] = 100
        frame.insert(0, "source_sheet", spec["sheet"])
        frame.insert(1, "table_label", spec["table_label"])
        frame.insert(2, "scenario", spec["scenario"])
        frame.insert(3, "llm_family", spec["llm_family"])
        frame.insert(4, "optimizer_status", spec["optimizer_status"])
        frame.insert(5, "with_optimizer", spec["with_optimizer"])
        frame.insert(6, "base_stock_mode", spec["base_stock_mode"])
        frames.append(frame)

    combined = pd.concat(frames, ignore_index=True, sort=False)
    combined.loc[combined["LLM"].eq("deepseek-chat"), "llm_family"] = "deepseek"
    combined = combined[
        WORKBOOK_FRONT_COLUMNS + [col for col in combined.columns if col not in WORKBOOK_FRONT_COLUMNS]
    ]

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        combined.to_excel(writer, index=False, sheet_name="different_llm_models")

    return combined


def load_different_llm_data(path="data/different_llm_models.xlsx", rebuild=False, source_path="data/final results.xlsx"):
    path = Path(path)
    if rebuild or not path.exists():
        build_different_llm_workbook(source_path=source_path, output_path=path)
    return pd.read_excel(path)


def prepare_matched_optimizer_convergence_slice(frame, optimizer_status, max_n_pop=None):
    test_mask = frame["mode"].astype(str).str.lower() == "test"
    if optimizer_status == "with optimizer":
        subset = frame[
            ((frame["source_sheet"] == "S 3") | (frame["source_sheet"] == "S 4.4"))
            & (frame["optimizer_status"] == optimizer_status)
            & test_mask
        ].copy()
    else:
        subset = frame[
            (
                (frame["source_sheet"] == "S 4.1")
                | (frame["source_sheet"] == "S 4.4 no opt")
            )
            & (frame["optimizer_status"] == optimizer_status)
            & test_mask
        ].copy()

    if max_n_pop is None:
        max_n_pop = 20 if optimizer_status == "with optimizer" else 10

    if max_n_pop is not None:
        subset = subset[subset["n_pop"] <= max_n_pop].copy()

    return subset


def compute_best_cost_reach_iteration(frame, tolerance=1e-9):
    """
    Compute the first n_pop at which each LLM reaches the best observed cost
    for the same instance slice.

    The best cost is defined across all LLMs and all n_pop values within the
    supplied slice, grouped by the shared instance columns.
    """
    subset = frame.copy()
    if subset.empty:
        return pd.DataFrame()

    instance_cols = ["optimizer_status", "dist"]
    if "initial_basestock" in subset.columns and subset["initial_basestock"].notna().any():
        instance_cols.append("initial_basestock")

    best_by_instance = (
        subset.groupby(instance_cols, dropna=False)["avg_top1"]
        .min()
        .rename("best_observed_avg_top1")
        .reset_index()
    )
    subset = subset.merge(best_by_instance, on=instance_cols, how="left")

    rows = []
    group_cols = instance_cols + ["LLM"]
    for group_key, group in subset.groupby(group_cols, dropna=False):
        if not isinstance(group_key, tuple):
            group_key = (group_key,)
        key_map = dict(zip(group_cols, group_key))

        ordered = group.sort_values("n_pop").copy()
        best_observed = ordered["best_observed_avg_top1"].iloc[0]
        reached = ordered.loc[
            ordered["avg_top1"] <= (best_observed + tolerance),
            "n_pop",
        ]
        n_pop_to_best_cost = reached.iloc[0] if not reached.empty else np.nan

        rows.append(
            {
                **key_map,
                "best_observed_avg_top1": best_observed,
                "n_pop_to_best_cost": n_pop_to_best_cost,
                "reached_best_cost": pd.notna(n_pop_to_best_cost),
            }
        )

    return pd.DataFrame(rows)


def compute_normalized_convergence_auc(frame):
    """
    Compute normalized regret AUC for avg_top1 over n_pop.

    For each optimizer status and instance, the reference best is the best
    avg_top1 achieved by any LLM at any n_pop in the supplied slice. Smaller
    AUC means avg_top1 drops faster toward the shared best observed value.
    """
    subset = frame.copy()
    if subset.empty:
        return pd.DataFrame()

    instance_cols = ["optimizer_status", "dist"]
    if "initial_basestock" in subset.columns and subset["initial_basestock"].notna().any():
        instance_cols.append("initial_basestock")

    best_by_instance = (
        subset.groupby(instance_cols, dropna=False)["avg_top1"]
        .min()
        .rename("best_observed_avg_top1")
        .reset_index()
    )
    subset = subset.merge(best_by_instance, on=instance_cols, how="left")

    rows = []
    group_cols = instance_cols + ["LLM"]
    for group_key, group in subset.groupby(group_cols, dropna=False):
        if not isinstance(group_key, tuple):
            group_key = (group_key,)
        key_map = dict(zip(group_cols, group_key))

        ordered = group.sort_values("n_pop").copy()
        baseline = ordered.loc[ordered["n_pop"].eq(ordered["n_pop"].min()), "avg_top1"].iloc[0]
        best_observed = ordered["best_observed_avg_top1"].iloc[0]
        denominator = baseline - best_observed

        if pd.isna(denominator):
            continue

        if abs(denominator) < 1e-12:
            ordered["normalized_regret"] = 0.0
        else:
            ordered["normalized_regret"] = (ordered["avg_top1"] - best_observed) / denominator

        rows.append(
            {
                **key_map,
                "baseline_avg_top1": baseline,
                "best_observed_avg_top1": best_observed,
                "final_avg_top1": ordered["avg_top1"].iloc[-1],
                "normalized_convergence_auc": ordered["normalized_regret"].mean(),
                "final_normalized_regret": ordered["normalized_regret"].iloc[-1],
                "n_points": len(ordered),
            }
        )

    return pd.DataFrame(rows)


def compute_run_variance(frame, n_pop=20):
    subset = frame[
        (frame["source_sheet"] == "S 4.4 no opt extension")
        & (frame["mode"].astype(str).str.lower() == "test")
    ].copy()
    subset = subset[subset["n_pop"] == n_pop].copy()

    top1_cols = [f"repeat_{repeat_idx}" for repeat_idx in range(1, 11)]
    subset["top1_run_std"] = subset[top1_cols].std(axis=1)
    subset["top1_run_cv_pct"] = 100 * subset["top1_run_std"] / subset["avg_top1"]
    return subset


def compute_optimizer_impact(frame):
    """
    Compare matched standard-slice rows with and without optimizer.

    Positive `optimizer_gain_pct` means the optimizer reduced avg_top1 cost.
    """
    subset = frame[
        (frame["base_stock_mode"] == "standard")
        & (frame["mode"].astype(str).str.lower() == "test")
    ].copy()

    key_cols = ["LLM", "dist", "n_pop"]

    with_opt = subset.loc[subset["optimizer_status"] == "with optimizer", key_cols + ["avg_top1"]].rename(
        columns={"avg_top1": "avg_top1_with_optimizer"}
    )
    without_opt = subset.loc[
        subset["optimizer_status"] == "without optimizer", key_cols + ["avg_top1"]
    ].rename(columns={"avg_top1": "avg_top1_without_optimizer"})

    merged = with_opt.merge(without_opt, on=key_cols, how="inner")
    merged["optimizer_gain"] = (
        merged["avg_top1_without_optimizer"] - merged["avg_top1_with_optimizer"]
    )
    merged["optimizer_gain_pct"] = (
        100
        * merged["optimizer_gain"]
        / merged["avg_top1_without_optimizer"]
    )
    return merged


def build_metric_summary(frame, value_col):
    return (
        frame.groupby("LLM")[value_col]
        .agg(["mean", "median", "min", "max", "count"])
        .round(2)
        .reset_index()
    )


def llm_labels(order):
    return [MODEL_LABELS.get(model, model) for model in order]


def llm_colors(order):
    return [MODEL_COLORS[model] for model in order]
