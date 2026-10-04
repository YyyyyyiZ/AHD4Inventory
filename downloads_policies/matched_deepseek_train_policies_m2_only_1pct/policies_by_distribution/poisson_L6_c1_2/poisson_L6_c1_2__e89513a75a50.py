# policy_hash: e89513a75a503c2d9b71f91c5c4b0de9a6ff5f68f5463098496dff44f4c5cfbb
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_2
# matched_train_cells: 4
# source_prompt_files: 1
# best_target_performance: 2818.52
# best_prompt_performance: 2818.52
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251222_015333.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 644.6719138363669  # OPT_PARAM: {"initial": 644.6719138363669, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 30.682364598208654  # OPT_PARAM: {"initial": 30.682364598208654, "min": 0, "max": 200, "type": "float"}
    pipeline_factor = 1.0289247075449217  # OPT_PARAM: {"initial": 1.0289247075449217, "min": 0.1, "max": 1.5, "type": "float"}

    # Calculate effective pipeline inventory with discount factor
    effective_pipeline = sum(pipeline_orders) * pipeline_factor

    # Calculate target inventory position
    target = base_stock + safety_stock

    # Calculate order amount
    order_amount = max(0, target - on_hand_inventory - effective_pipeline)

    # Round to nearest integer since order amounts should be integers
    return order_amount
