# policy_hash: f13c39bb15ab74e9cac6905039129da9f9e9ef681aa73d4944d9f7a21c1b2316
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_2
# matched_train_cells: 10
# source_prompt_files: 1
# best_target_performance: 2499.66
# best_prompt_performance: 2501.78
# best_rel_error_pct: 0.084812
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251222_014051.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 740.8119048344868  # OPT_PARAM: {"initial": 740.8119048344868, "min": 500, "max": 750, "type": "float"}
    safety_stock = 80.0  # OPT_PARAM: {"initial": 80.0, "min": 20, "max": 150, "type": "float"}
    smoothing_factor = 0.4454171659874425  # OPT_PARAM: {"initial": 0.4454171659874425, "min": 0.1, "max": 0.8, "type": "float"}

    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate desired order with smoothing
    desired_order = base_stock - inventory_position

    # Apply smoothing to reduce order volatility
    if desired_order > 0:
        order_amount = max(0, smoothing_factor * desired_order)
    else:
        order_amount = 0

    # Add safety stock consideration for low inventory situations
    if inventory_position < safety_stock:
        additional_order = safety_stock - inventory_position
        order_amount = max(order_amount, additional_order)

    return order_amount
