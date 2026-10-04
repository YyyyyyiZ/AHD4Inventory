# policy_hash: f5b71427f8dd0d34ac08b15b4ed203a7c4004736b359e102511c59f126c35cdd
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_2
# matched_train_cells: 51
# source_prompt_files: 2
# best_target_performance: 780.26
# best_prompt_performance: 780.26
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r4/prompt_for_code/m2_20251218_103607.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 293.49016407336353  # OPT_PARAM: {"initial": 293.49016407336353, "min": 200, "max": 350, "type": "float"}
    safety_stock = 15.0  # OPT_PARAM: {"initial": 15.0, "min": 5, "max": 40, "type": "float"}
    demand_sensitivity = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.01, "max": 0.2, "type": "float"}
    pipeline_weight = 0.8  # OPT_PARAM: {"initial": 0.8, "min": 0.5, "max": 1.0, "type": "float"}
    smoothing_factor = 0.2309107902568994  # OPT_PARAM: {"initial": 0.2309107902568994, "min": 0.1, "max": 0.5, "type": "float"}

    # Calculate net inventory position with weighted pipeline
    weighted_pipeline = sum(p * (pipeline_weight ** i) for i, p in enumerate(reversed(pipeline_orders)))
    net_inventory = on_hand_inventory + weighted_pipeline

    # Estimate demand from recent pipeline arrivals (more stable than using pipeline orders)
    if len(pipeline_orders) >= 2:
        # Use average of last two arrivals as demand proxy
        recent_arrivals = pipeline_orders[:2]
        avg_demand = sum(recent_arrivals) / len(recent_arrivals)
    else:
        avg_demand = 100.0  # Default to historical average

    # Adjust base stock based on demand deviation from historical mean
    demand_adjustment = demand_sensitivity * (avg_demand - 100)
    adjusted_base_stock = base_stock + demand_adjustment

    # Ensure minimum safety stock
    target_inventory = max(adjusted_base_stock, safety_stock)

    # Calculate raw order amount
    raw_order = max(0, target_inventory - net_inventory)

    # Apply smoothing to reduce order volatility
    order_amount = int(round(raw_order * smoothing_factor + pipeline_orders[-1] * (1 - smoothing_factor)))

    return order_amount
