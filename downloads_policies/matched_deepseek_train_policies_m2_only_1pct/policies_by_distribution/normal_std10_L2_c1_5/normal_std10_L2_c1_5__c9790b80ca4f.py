# policy_hash: c9790b80ca4fb403997d27dfc2ae131dadd97a9798a5477351263053f333418d
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L2_c1_5
# matched_train_cells: 17
# source_prompt_files: 1
# best_target_performance: 1227.32
# best_prompt_performance: 1227.86
# best_rel_error_pct: 0.043998
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L2_c1_5_50_plain_processed_scipy_15_default_m2_2_r8/prompt_for_code/m2_20260130_095012.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 438.27524350839866  # OPT_PARAM: {"initial": 438.27524350839866, "min": 350, "max": 500, "type": "float"}
    pipeline_weight = 0.7834829506185816  # OPT_PARAM: {"initial": 0.7834829506185816, "min": 0.75, "max": 0.95, "type": "float"}
    smoothing_factor = 0.35  # OPT_PARAM: {"initial": 0.35, "min": 0.15, "max": 0.35, "type": "float"}
    min_order = 0  # OPT_PARAM: {"initial": 0, "min": 0, "max": 5, "type": "int"}
    safety_stock = 31.539807583144842  # OPT_PARAM: {"initial": 31.539807583144842, "min": 15, "max": 40, "type": "float"}
    demand_anticipation = 0.21430012424253667  # OPT_PARAM: {"initial": 0.21430012424253667, "min": 0.1, "max": 0.5, "type": "float"}

    # Calculate effective inventory position with weighted pipeline
    effective_pipeline = pipeline_weight * sum(pipeline_orders)
    inventory_position = on_hand_inventory + effective_pipeline

    # Adjust base stock based on pipeline variability
    pipeline_variance = max(0, sum(pipeline_orders) - effective_pipeline)
    adjusted_base = base_stock + safety_stock - demand_anticipation * pipeline_variance

    # Base stock policy with smoothing
    raw_order = adjusted_base - inventory_position
    order_amount = max(min_order, raw_order)

    # Apply exponential smoothing to reduce order volatility
    if order_amount > 0:
        smoothed_order = smoothing_factor * order_amount + (1 - smoothing_factor) * min_order
        order_amount = max(min_order, smoothed_order)

    return order_amount
