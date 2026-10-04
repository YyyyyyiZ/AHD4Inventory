# policy_hash: d4689d26270a4488f6f9403865850450b7b681c05859ad98db0f6758c95231b9
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_2
# matched_train_cells: 2
# source_prompt_files: 1
# best_target_performance: 6282.44
# best_prompt_performance: 6282.5
# best_rel_error_pct: 0.000955
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r4/prompt_for_code/m2_20251218_104353.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 188.6075391031234  # OPT_PARAM: {"initial": 188.6075391031234, "min": 150, "max": 300, "type": "float"}
    safety_stock = 29.18062731851089  # OPT_PARAM: {"initial": 29.18062731851089, "min": 20, "max": 80, "type": "float"}
    demand_forecast_factor = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.5, "type": "float"}
    pipeline_weight = 0.4  # OPT_PARAM: {"initial": 0.4, "min": 0.3, "max": 0.9, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Simple demand forecast based on recent arrivals
    recent_demand_estimate = 0
    if len(pipeline_orders) > 0:
        # Weight recent arrivals more heavily
        weights = [0.5, 0.3, 0.2]  # Fixed weights for up to 3 periods
        for i, arrival in enumerate(pipeline_orders[:3]):
            recent_demand_estimate += arrival * weights[i]

    # Adjust target based on demand forecast
    forecast_adjustment = recent_demand_estimate * demand_forecast_factor
    adjusted_target = base_stock + safety_stock + forecast_adjustment

    # Consider pipeline coverage in ordering decision
    pipeline_coverage = sum(pipeline_orders) * pipeline_weight
    final_target = max(base_stock, adjusted_target - pipeline_coverage)

    # Calculate order amount
    order_amount = max(0, final_target - inventory_position)

    # Round to nearest integer
    return order_amount
