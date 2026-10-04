# policy_hash: d7c928fd42a55b237ebcaa54bfcf7d12ddffac39a0901da210530cc48ff12ef9
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_2
# matched_train_cells: 3
# source_prompt_files: 1
# best_target_performance: 5373.86
# best_prompt_performance: 5375.27
# best_rel_error_pct: 0.026238
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251217_003229.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 449.5223550789041  # OPT_PARAM: {"initial": 449.5223550789041, "min": 300, "max": 600, "type": "float"}
    safety_stock = 14.522355078904045  # OPT_PARAM: {"initial": 14.522355078904045, "min": 0, "max": 50, "type": "float"}
    demand_forecast_factor = 0.7289318105396334  # OPT_PARAM: {"initial": 0.7289318105396334, "min": 0.5, "max": 1.5, "type": "float"}
    pipeline_weight = 0.48155301756605995  # OPT_PARAM: {"initial": 0.48155301756605995, "min": 0.1, "max": 1.0, "type": "float"}
    recent_window = 4  # OPT_PARAM: {"initial": 4, "min": 1, "max": 10, "type": "int"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Use weighted average of pipeline orders as demand forecast
    # More weight to recent orders
    if len(pipeline_orders) > 0:
        recent_arrivals = pipeline_orders[:recent_window]
        weights = [pipeline_weight ** i for i in range(len(recent_arrivals))]
        weighted_sum = sum(w * d for w, d in zip(weights, recent_arrivals))
        weight_sum = sum(weights)
        avg_recent_demand = weighted_sum / weight_sum if weight_sum > 0 else 0
    else:
        avg_recent_demand = 0

    # Adjust base stock based on demand forecast
    adjusted_base = base_stock + demand_forecast_factor * avg_recent_demand

    # Calculate target inventory position
    target_position = adjusted_base + safety_stock

    # Calculate order amount
    order_amount = max(0, target_position - inventory_position)

    # Round to nearest integer
    return order_amount
