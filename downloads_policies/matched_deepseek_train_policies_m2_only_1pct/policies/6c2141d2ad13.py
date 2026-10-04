# policy_hash: 6c2141d2ad130234b4e68e97f61847da2d17c2fd25d2333f45dd6ef7894de557
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L6_c1_5
# matched_train_cells: 4
# source_prompt_files: 1
# best_target_performance: 3076.3
# best_prompt_performance: 3070.57
# best_rel_error_pct: 0.186263
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260128_033111.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 677.8607545926457  # OPT_PARAM: {"initial": 677.8607545926457, "min": 500, "max": 800, "type": "float"}
    safety_stock = 127.86075459265352  # OPT_PARAM: {"initial": 127.86075459265352, "min": 50, "max": 150, "type": "float"}
    smoothing_factor = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.0, "type": "float"}
    demand_buffer = 0.9  # OPT_PARAM: {"initial": 0.9, "min": 0.9, "max": 1.2, "type": "float"}
    min_order = 5  # OPT_PARAM: {"initial": 5, "min": 0, "max": 20, "type": "int"}
    lead_time = 6  # OPT_PARAM: {"initial": 6, "min": 1, "max": 10, "type": "int"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate target inventory position with lead-time adjustment
    target_position = base_stock + safety_stock * (lead_time / 6.0)

    # Calculate order amount with smoothing
    raw_order = smoothing_factor * (target_position - inventory_position)

    # Apply demand buffer
    buffered_order = raw_order * demand_buffer

    # Ensure non-negative order with minimum order quantity
    order_amount = max(min_order, buffered_order)

    # Round to nearest integer
    return order_amount
