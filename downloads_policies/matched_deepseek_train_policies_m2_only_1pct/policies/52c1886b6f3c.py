# policy_hash: 52c1886b6f3c9b636d62b795be4f5bb1ffe9962cbdbb4829ba56ea62053bac98
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_5
# matched_train_cells: 25
# source_prompt_files: 1
# best_target_performance: 10995.78
# best_prompt_performance: 10995.78
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_090545.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 481.06011399255783  # OPT_PARAM: {"initial": 481.06011399255783, "min": 300, "max": 700, "type": "float"}
    pipeline_weight = 0.8223637244626237  # OPT_PARAM: {"initial": 0.8223637244626237, "min": 0.6, "max": 1.0, "type": "float"}
    smoothing_factor = 0.23341823467757422  # OPT_PARAM: {"initial": 0.23341823467757422, "min": 0.1, "max": 0.4, "type": "float"}
    safety_stock = 121.06011399255814  # OPT_PARAM: {"initial": 121.06011399255814, "min": 50, "max": 250, "type": "float"}
    demand_anticipation = 0.23341823467757422  # OPT_PARAM: {"initial": 0.23341823467757422, "min": 0.0, "max": 0.5, "type": "float"}
    pipeline_threshold = 0.41989084773461527  # OPT_PARAM: {"initial": 0.41989084773461527, "min": 0.2, "max": 0.6, "type": "float"}

    # Calculate effective inventory position with weighted pipeline
    effective_pipeline = pipeline_weight * sum(pipeline_orders)
    inventory_position = on_hand_inventory + effective_pipeline

    # Add safety stock to base stock level
    adjusted_base_stock = base_stock + safety_stock

    # Calculate order-up-to amount
    order_up_to = max(0, adjusted_base_stock - inventory_position)

    # Apply demand anticipation: increase orders when pipeline is low
    if sum(pipeline_orders) < pipeline_threshold * adjusted_base_stock:
        order_up_to *= (1 + demand_anticipation)

    # Apply smoothing with consistent factor
    order_amount = smoothing_factor * order_up_to

    # Round to nearest integer (as order amounts should be integers)
    order_amount = int(round(order_amount))

    return order_amount
