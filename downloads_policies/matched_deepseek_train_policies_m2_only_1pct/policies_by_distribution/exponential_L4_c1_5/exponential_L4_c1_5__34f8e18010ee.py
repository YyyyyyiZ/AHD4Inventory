# policy_hash: 34f8e18010ee4c642fa62dfcf46fa3553d1c810ce2d77197bf8c33d8e3039bd7
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_5
# matched_train_cells: 5
# source_prompt_files: 1
# best_target_performance: 11304.4
# best_prompt_performance: 11303.9
# best_rel_error_pct: 0.004423
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_044310.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 385.89671822826386  # OPT_PARAM: {"initial": 385.89671822826386, "min": 200, "max": 600, "type": "float"}
    safety_stock = 95.89671822826406  # OPT_PARAM: {"initial": 95.89671822826406, "min": 30, "max": 200, "type": "float"}
    smoothing_factor = 0.45674391622157445  # OPT_PARAM: {"initial": 0.45674391622157445, "min": 0.3, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Use a simpler, more robust target calculation
    target_inventory = base_stock + safety_stock

    # Calculate order amount
    order_amount = max(0, target_inventory - inventory_position)

    # Apply smoothing to avoid extreme order sizes
    if order_amount > 0:
        order_amount = smoothing_factor * order_amount

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
