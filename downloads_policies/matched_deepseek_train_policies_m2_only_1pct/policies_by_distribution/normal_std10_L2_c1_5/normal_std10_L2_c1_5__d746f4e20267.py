# policy_hash: d746f4e202678c7c33c9a62049872bad6cc7140be98b52c008fd70d68c0f11d0
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L2_c1_5
# matched_train_cells: 11
# source_prompt_files: 1
# best_target_performance: 1235.44
# best_prompt_performance: 1236.84
# best_rel_error_pct: 0.113320
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L2_c1_5_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260129_232105.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 275.00034838610037  # OPT_PARAM: {"initial": 275.00034838610037, "min": 200, "max": 350, "type": "float"}
    safety_stock = 40.00034838610035  # OPT_PARAM: {"initial": 40.00034838610035, "min": 20, "max": 80, "type": "float"}
    smoothing_factor = 0.35773893709955473  # OPT_PARAM: {"initial": 0.35773893709955473, "min": 0.3, "max": 0.9, "type": "float"}
    lead_time = 2  # OPT_PARAM: {"initial": 2, "min": 1, "max": 3, "type": "int"}
    avg_demand = 83.10657110869744  # OPT_PARAM: {"initial": 83.10657110869744, "min": 80, "max": 120, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    expected_lead_time_demand = lead_time * avg_demand

    # Target inventory position
    target_position = base_stock + safety_stock + expected_lead_time_demand

    # Calculate raw order needed
    raw_order = target_position - inventory_position

    # Apply smoothing only for positive orders
    if raw_order > 0:
        smoothed_order = smoothing_factor * raw_order
    else:
        smoothed_order = raw_order

    # Ensure non-negative integer order
    order_amount = max(0, int(round(smoothed_order)))

    return order_amount
