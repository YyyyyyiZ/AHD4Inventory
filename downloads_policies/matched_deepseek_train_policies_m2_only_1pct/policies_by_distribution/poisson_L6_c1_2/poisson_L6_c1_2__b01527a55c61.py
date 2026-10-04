# policy_hash: b01527a55c610fa0bb87de29176317265d252c920b0f8a2ce0120036003ba13e
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_2
# matched_train_cells: 3
# source_prompt_files: 1
# best_target_performance: 2580.56
# best_prompt_performance: 2589.95
# best_rel_error_pct: 0.363875
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251222_015846.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 600.0022022536668  # OPT_PARAM: {"initial": 600.0022022536668, "min": 400, "max": 700, "type": "float"}
    safety_stock = 60.0  # OPT_PARAM: {"initial": 60.0, "min": 20, "max": 60, "type": "float"}
    pipeline_adjustment = 0.9  # OPT_PARAM: {"initial": 0.9, "min": 0.9, "max": 1.1, "type": "float"}
    smoothing_factor = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.0, "type": "float"}
    demand_buffer = 40.0  # OPT_PARAM: {"initial": 40.0, "min": 10, "max": 40, "type": "float"}

    # Calculate effective pipeline with adjustment
    effective_pipeline = sum(pipeline_orders) * pipeline_adjustment

    # Calculate target inventory position with demand buffer
    target_inventory = base_stock + safety_stock + demand_buffer

    # Calculate current inventory position
    inventory_position = on_hand_inventory + effective_pipeline

    # Calculate desired order with smoothing
    desired_order = max(0, target_inventory - inventory_position)
    order_amount = smoothing_factor * desired_order

    # Round to nearest integer
    return order_amount
