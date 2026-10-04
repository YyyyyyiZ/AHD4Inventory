# policy_hash: aacc96f62544cd07aab61c073aa79c9758a00c1c5df30716811016f3d50ae7ae
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_5
# matched_train_cells: 8
# source_prompt_files: 1
# best_target_performance: 3228.9
# best_prompt_performance: 3228.9
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_025230.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 308.9814814814807  # OPT_PARAM: {"initial": 308.9814814814807, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 50.0  # OPT_PARAM: {"initial": 50.0, "min": 0, "max": 200, "type": "float"}
    demand_estimate = 100.0  # OPT_PARAM: {"initial": 100.0, "min": 50, "max": 150, "type": "float"}

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
        if current_pipeline < expected_pipeline * 0.8:  # OPT_PARAM: {"initial": 0.8, "min": 0.5, "max": 1.0, "type": "float"}
            pipeline_adjustment = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.1, "max": 0.5, "type": "float"}
            order_amount += pipeline_adjustment

    # Round to nearest integer (orders must be integer quantities)
    order_amount = int(round(order_amount))

    return order_amount
