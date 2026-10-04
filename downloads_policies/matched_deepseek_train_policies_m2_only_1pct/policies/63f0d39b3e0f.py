# policy_hash: 63f0d39b3e0f470fbad9f9ada548f3356579f4971cc8ce909eaa732c1548a33b
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_2
# matched_train_cells: 3
# source_prompt_files: 1
# best_target_performance: 2184.72
# best_prompt_performance: 2184.72
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_073721.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 481.979022078215  # OPT_PARAM: {"initial": 481.979022078215, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 50.0  # OPT_PARAM: {"initial": 50.0, "min": 0, "max": 200, "type": "float"}
    demand_forecast = 100.0  # OPT_PARAM: {"initial": 100.0, "min": 50, "max": 150, "type": "float"}
    smoothing_factor = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.01, "max": 0.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Adjust base stock based on pipeline variability
    pipeline_variance = sum((q - demand_forecast) ** 2 for q in pipeline_orders) / len(pipeline_orders) if len(pipeline_orders) > 0 else 0
    pipeline_risk_factor = max(0, 1.0 - smoothing_factor * (pipeline_variance / (demand_forecast ** 2 + 1e-6)))  # OPT_PARAM: {"initial": 0.3, "min": 0.01, "max": 0.5, "type": "float"}

    # Dynamic target inventory level
    dynamic_target = base_stock * pipeline_risk_factor + safety_stock

    # Calculate order amount with smoothing
    raw_order = max(0, dynamic_target - inventory_position)
    smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * demand_forecast  # OPT_PARAM: {"initial": 0.3, "min": 0.01, "max": 0.5, "type": "float"}

    # Round to nearest integer (as required by problem statement)
    order_amount = int(round(smoothed_order))

    return order_amount
