# policy_hash: 9f285d5ad75cb138d07c9358791586cd6e95de09ac47cfd33553534588a74d4e
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_2
# matched_train_cells: 1
# source_prompt_files: 1
# best_target_performance: 1741.54
# best_prompt_performance: 1741.54
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_034643.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 433.7458312277472  # OPT_PARAM: {"initial": 433.7458312277472, "min": 300, "max": 600, "type": "float"}
    safety_stock = 48.02917228255418  # OPT_PARAM: {"initial": 48.02917228255418, "min": 10, "max": 80, "type": "float"}
    demand_smoothing_factor = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.3, "type": "float"}
    pipeline_weight = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.3, "max": 1.0, "type": "float"}

    # Calculate expected demand using weighted average of recent pipeline arrivals
    # More weight to recent arrivals to better track demand changes
    if len(pipeline_orders) >= 2:
        weights = [0.3, 0.7]  # More weight to most recent arrival
        weighted_sum = sum(w * d for w, d in zip(weights, pipeline_orders[:2]))
        avg_recent_demand = weighted_sum / sum(weights)
    else:
        avg_recent_demand = pipeline_orders[0] if pipeline_orders else 0

    # Smooth demand adjustment to avoid overreacting to outliers
    demand_adjustment = demand_smoothing_factor * (avg_recent_demand - 100)
    adjusted_base = base_stock + demand_adjustment

    # Calculate inventory position with weighted pipeline consideration
    # Give less weight to distant pipeline orders since they're less certain
    weighted_pipeline = sum(p * (pipeline_weight ** i)
                          for i, p in enumerate(pipeline_orders))

    # Calculate effective inventory position
    effective_inventory = on_hand_inventory + weighted_pipeline

    # Order up to adjusted base stock plus safety stock
    order_amount = max(0, adjusted_base + safety_stock - effective_inventory)

    # Round to nearest integer
    return order_amount
