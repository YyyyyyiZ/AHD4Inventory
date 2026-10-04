# policy_hash: c9d48c7fcbc5449b2bbaf3d6045fa793e4acfd2e7d796e231f02253d3edd2c6f
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_5
# matched_train_cells: 19
# source_prompt_files: 1
# best_target_performance: 10171.43
# best_prompt_performance: 10171.41
# best_rel_error_pct: 0.000197
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_233050.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 331.65961788653823  # OPT_PARAM: {"initial": 331.65961788653823, "min": 200, "max": 600, "type": "float"}
    safety_stock = 101.65961788653303  # OPT_PARAM: {"initial": 101.65961788653303, "min": 50, "max": 250, "type": "float"}
    smoothing_factor = 0.3079912842908638  # OPT_PARAM: {"initial": 0.3079912842908638, "min": 0.1, "max": 1.0, "type": "float"}
    demand_forecast_factor = 0.683317442395383  # OPT_PARAM: {"initial": 0.683317442395383, "min": 0.5, "max": 1.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand based on pipeline arrivals
    # Use a weighted average of recent pipeline orders as demand forecast
    if len(pipeline_orders) >= 2:
        recent_demand_estimate = (pipeline_orders[0] + pipeline_orders[1]) / 2.0
    else:
        recent_demand_estimate = pipeline_orders[0] if pipeline_orders else 0

    # Adjust target based on demand forecast
    adjusted_target = base_stock + safety_stock + demand_forecast_factor * recent_demand_estimate

    # Calculate raw order amount
    raw_order = max(0, adjusted_target - inventory_position)

    # Apply smoothing with threshold
    if raw_order > 0:
        order_amount = smoothing_factor * raw_order
    else:
        order_amount = 0

    # Round to nearest integer
    return order_amount
