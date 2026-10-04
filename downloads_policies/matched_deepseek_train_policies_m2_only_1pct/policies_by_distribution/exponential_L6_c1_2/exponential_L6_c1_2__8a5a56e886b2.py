# policy_hash: 8a5a56e886b2652055da8926866fe85ec7dae2ad38e8d73b26b7c52d538a6887
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_2
# matched_train_cells: 5
# source_prompt_files: 2
# best_target_performance: 6263.7
# best_prompt_performance: 6263.7
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_013645.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 383.64353233083136  # OPT_PARAM: {"initial": 383.64353233083136, "min": 200, "max": 600, "type": "float"}
    pipeline_weight = 0.7783956452817509  # OPT_PARAM: {"initial": 0.7783956452817509, "min": 0.7, "max": 1.0, "type": "float"}
    demand_buffer = 63.64353233083218  # OPT_PARAM: {"initial": 63.64353233083218, "min": 30, "max": 120, "type": "float"}

    # Calculate effective inventory position
    effective_pipeline = sum(pipeline_orders) * pipeline_weight
    inventory_position = on_hand_inventory + effective_pipeline

    # Calculate target inventory level
    target_inventory = base_stock + demand_buffer

    # Calculate order amount
    order_amount = max(0, target_inventory - inventory_position)

    # Apply order smoothing with dynamic factor
    smoothing = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 0.8, "type": "float"}
    order_amount = order_amount * smoothing

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
