# policy_hash: 761bc123397269aac144da4a50326ae26efa7f738640bef4f216fdfec2a0874a
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_2
# matched_train_cells: 16
# source_prompt_files: 1
# best_target_performance: 6282.29
# best_prompt_performance: 6282.29
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_064326.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 196.91436193227224  # OPT_PARAM: {"initial": 196.91436193227224, "min": 100, "max": 500, "type": "float"}
    safety_stock = 20.0  # OPT_PARAM: {"initial": 20.0, "min": 20, "max": 200, "type": "float"}
    pipeline_factor = 0.16785532430224687  # OPT_PARAM: {"initial": 0.16785532430224687, "min": 0.0, "max": 0.5, "type": "float"}
    demand_buffer = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 1.0, "max": 3.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand based on pipeline arrivals
    incoming_next = pipeline_orders[0] if len(pipeline_orders) > 0 else 0
    incoming_after = pipeline_orders[1] if len(pipeline_orders) > 1 else 0

    # More conservative pipeline adjustment
    pipeline_adjustment = pipeline_factor * (incoming_next + incoming_after)

    # Dynamic target with demand buffer
    target = base_stock + safety_stock * demand_buffer - pipeline_adjustment

    # Order amount with smoother adjustment
    order_amount = max(0, target - inventory_position)

    # Round to nearest integer
    return order_amount
