# policy_hash: b2d08417db71f9e2271397ef935a25f42f9e179c3a37b4595c32e88745bcba3e
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_5
# matched_train_cells: 6
# source_prompt_files: 1
# best_target_performance: 1432.82
# best_prompt_performance: 1432.82
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_025753.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 264.19509134364534  # OPT_PARAM: {"initial": 264.19509134364534, "min": 100, "max": 400, "type": "float"}
    safety_stock = 44.29509134364446  # OPT_PARAM: {"initial": 44.29509134364446, "min": 0, "max": 100, "type": "float"}
    demand_estimate = 100.17848124598335  # OPT_PARAM: {"initial": 100.17848124598335, "min": 80, "max": 130, "type": "float"}
    pipeline_threshold = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.6, "max": 1.0, "type": "float"}
    pipeline_adjustment = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.3, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate target inventory level
    target_level = base_stock + safety_stock

    # Base order amount
    order_amount = max(0, target_level - inventory_position)

    # Add demand anticipation for pipeline smoothing
    if len(pipeline_orders) > 0:
        # Check if pipeline is below expected level
        expected_pipeline = demand_estimate * len(pipeline_orders)
        current_pipeline = sum(pipeline_orders)
        if current_pipeline < expected_pipeline * pipeline_threshold:
            order_amount += pipeline_adjustment * (expected_pipeline - current_pipeline)

    # Round to nearest integer (orders must be integer quantities)
    order_amount = int(round(order_amount))

    return order_amount
