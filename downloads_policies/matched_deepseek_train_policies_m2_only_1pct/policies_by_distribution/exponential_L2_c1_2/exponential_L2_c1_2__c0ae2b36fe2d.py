# policy_hash: c0ae2b36fe2dd3edb4e2db528634dcfc9dae979df27afc1769adf76e50634d64
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_2
# matched_train_cells: 7
# source_prompt_files: 1
# best_target_performance: 6298.07
# best_prompt_performance: 6298.07
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_064013.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 195.44277843872442  # OPT_PARAM: {"initial": 195.44277843872442, "min": 100, "max": 500, "type": "float"}
    safety_stock = 25.442778611563373  # OPT_PARAM: {"initial": 25.442778611563373, "min": 20, "max": 200, "type": "float"}
    pipeline_factor = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Adjust base stock based on incoming pipeline orders
    incoming_next = pipeline_orders[0] if len(pipeline_orders) > 0 else 0
    incoming_after = pipeline_orders[1] if len(pipeline_orders) > 1 else 0

    # Dynamic adjustment: reduce order when large shipments are arriving soon
    pipeline_adjustment = pipeline_factor * (incoming_next + 0.5 * incoming_after)

    # Target inventory position with safety stock
    target = base_stock + safety_stock - pipeline_adjustment

    # Order amount
    order_amount = max(0, target - inventory_position)

    # Round to nearest integer (since demand is integer)
    return order_amount
