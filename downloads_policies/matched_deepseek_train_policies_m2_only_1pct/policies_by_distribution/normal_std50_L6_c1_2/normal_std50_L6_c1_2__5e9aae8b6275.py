# policy_hash: 5e9aae8b6275f0aaadc749ea1d11d40a1e703ddacafc72ed5f089581924a446d
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_2
# matched_train_cells: 8
# source_prompt_files: 1
# best_target_performance: 5568.79
# best_prompt_performance: 5571.4
# best_rel_error_pct: 0.046868
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251217_002234.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 476.455010814047  # OPT_PARAM: {"initial": 476.455010814047, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 0.0  # OPT_PARAM: {"initial": 0.0, "min": 0, "max": 200, "type": "float"}
    demand_forecast = 50.0  # OPT_PARAM: {"initial": 50.0, "min": 50, "max": 200, "type": "float"}
    pipeline_weight = 0.9507255676941221  # OPT_PARAM: {"initial": 0.9507255676941221, "min": 0.1, "max": 1.5, "type": "float"}

    # Calculate effective inventory position
    effective_inventory = on_hand_inventory + pipeline_weight * sum(pipeline_orders)

    # Calculate target inventory level
    target_inventory = base_stock + safety_stock

    # Calculate order amount
    order_amount = max(0, target_inventory - effective_inventory + demand_forecast)

    return order_amount
