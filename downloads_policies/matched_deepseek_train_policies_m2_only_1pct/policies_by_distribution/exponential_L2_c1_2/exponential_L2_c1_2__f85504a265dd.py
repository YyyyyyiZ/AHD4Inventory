# policy_hash: f85504a265dd0ac4ea2cefca3180e4f89b919d9d57b6dfc85c158b90e8bdbe97
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_2
# matched_train_cells: 9
# source_prompt_files: 1
# best_target_performance: 6025.24
# best_prompt_performance: 6025.24
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_064327.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 179.28494944708524  # OPT_PARAM: {"initial": 179.28494944708524, "min": 50, "max": 400, "type": "float"}
    safety_stock = 29.284949447085303  # OPT_PARAM: {"initial": 29.284949447085303, "min": 0, "max": 100, "type": "float"}
    demand_forecast_factor = 0.6886538873441784  # OPT_PARAM: {"initial": 0.6886538873441784, "min": 0.0, "max": 2.0, "type": "float"}
    pipeline_weight = 0.6  # OPT_PARAM: {"initial": 0.6, "min": 0.0, "max": 1.0, "type": "float"}
    order_smoothing = 0.5067623662514281  # OPT_PARAM: {"initial": 0.5067623662514281, "min": 0.0, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate demand forecast using weighted average of pipeline arrivals
    if len(pipeline_orders) > 0:
        # Give more weight to recent pipeline orders
        weights = [pipeline_weight ** i for i in range(len(pipeline_orders))]
        weighted_sum = sum(p * w for p, w in zip(reversed(pipeline_orders), weights))
        total_weight = sum(weights)
        recent_demand_estimate = weighted_sum / total_weight if total_weight > 0 else 0
    else:
        recent_demand_estimate = 0

    # Adjust base stock dynamically based on demand forecast
    adjusted_base_stock = base_stock + safety_stock + demand_forecast_factor * recent_demand_estimate

    # Calculate raw order with smoothing
    raw_order = max(0, adjusted_base_stock - inventory_position)

    # Apply order smoothing to reduce volatility
    smoothed_order = order_smoothing * raw_order + (1 - order_smoothing) * max(0, adjusted_base_stock - inventory_position - raw_order)

    # Round to nearest integer
    order_amount = int(round(smoothed_order))

    return order_amount
