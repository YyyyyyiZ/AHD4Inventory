# policy_hash: c041a1256ae0c0c7e8f1932da8e7bc44107eca96d502d72207bdd216bc46eef6
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_2
# matched_train_cells: 3
# source_prompt_files: 1
# best_target_performance: 4252.28
# best_prompt_performance: 4248.32
# best_rel_error_pct: 0.093127
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251217_004532.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 387.177591661996  # OPT_PARAM: {"initial": 387.177591661996, "min": 300, "max": 450, "type": "float"}
    safety_stock = 47.177591661997546  # OPT_PARAM: {"initial": 47.177591661997546, "min": 20, "max": 100, "type": "float"}
    demand_forecast = 117.17759166199805  # OPT_PARAM: {"initial": 117.17759166199805, "min": 90, "max": 130, "type": "float"}
    pipeline_weight = 0.6  # OPT_PARAM: {"initial": 0.6, "min": 0.6, "max": 1.0, "type": "float"}
    adjustment_factor = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 0.8, "type": "float"}

    # Calculate effective inventory position
    effective_inventory = on_hand_inventory + pipeline_weight * sum(pipeline_orders)

    # Calculate target inventory level
    target_inventory = base_stock + safety_stock

    # Calculate base order amount
    base_order = max(0, target_inventory - effective_inventory + demand_forecast)

    # Apply adjustment to smooth ordering
    order_amount = int(round(base_order * adjustment_factor))

    return order_amount
