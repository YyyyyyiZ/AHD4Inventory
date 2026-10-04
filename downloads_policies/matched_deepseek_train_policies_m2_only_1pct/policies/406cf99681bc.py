# policy_hash: 406cf99681bc8ccaad82b553b15b7ceb4ed0086fdbb92f2d3f2933b27bbd3be1
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_2
# matched_train_cells: 2
# source_prompt_files: 1
# best_target_performance: 6109.96
# best_prompt_performance: 6110.26
# best_rel_error_pct: 0.004910
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_014451.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 472.542631567924  # OPT_PARAM: {"initial": 472.542631567924, "min": 300, "max": 700, "type": "float"}
    pipeline_weight = 0.9062305567838728  # OPT_PARAM: {"initial": 0.9062305567838728, "min": 0.6, "max": 1.0, "type": "float"}
    smoothing_factor = 0.16680980629175343  # OPT_PARAM: {"initial": 0.16680980629175343, "min": 0.1, "max": 0.8, "type": "float"}
    safety_stock = 107.54263156792055  # OPT_PARAM: {"initial": 107.54263156792055, "min": 50, "max": 250, "type": "float"}
    demand_adjustment = 0.09876950290782197  # OPT_PARAM: {"initial": 0.09876950290782197, "min": 0.05, "max": 0.3, "type": "float"}

    # Calculate weighted pipeline inventory
    weighted_pipeline = sum(pipeline_orders) * pipeline_weight

    # Calculate inventory position
    inventory_position = on_hand_inventory + weighted_pipeline

    # Estimate upcoming demand from recent pipeline orders
    recent_orders = pipeline_orders[-3:] if len(pipeline_orders) >= 3 else pipeline_orders
    estimated_demand = sum(recent_orders) / len(recent_orders) if recent_orders else 0

    # Adjust base stock based on demand estimate
    adjusted_base_stock = base_stock + safety_stock + (estimated_demand * demand_adjustment)

    # Calculate desired order
    desired_order = max(0, adjusted_base_stock - inventory_position)

    # Apply smoothing to reduce order volatility
    if desired_order > 0:
        order_amount = int(desired_order * smoothing_factor)
    else:
        order_amount = 0

    return order_amount
