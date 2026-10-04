# policy_hash: 5278d8b10822509e54ef53b6ee10bc0099bc6aff1e86c3bdfd84c4425dec1e14
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_2
# matched_train_cells: 37
# source_prompt_files: 1
# best_target_performance: 736.05
# best_prompt_performance: 736.05
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_2_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260130_041742.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 485.4441701688114  # OPT_PARAM: {"initial": 485.4441701688114, "min": 450, "max": 520, "type": "float"}
    safety_stock = 35.04935148506265  # OPT_PARAM: {"initial": 35.04935148506265, "min": 20, "max": 50, "type": "float"}
    demand_forecast = 96.86378949393448  # OPT_PARAM: {"initial": 96.86378949393448, "min": 95, "max": 105, "type": "float"}
    smoothing_factor = 0.25  # OPT_PARAM: {"initial": 0.25, "min": 0.05, "max": 0.25, "type": "float"}
    pipeline_weight = 0.95  # OPT_PARAM: {"initial": 0.95, "min": 0.7, "max": 0.95, "type": "float"}
    order_threshold = 0.25  # OPT_PARAM: {"initial": 0.25, "min": 0.1, "max": 0.4, "type": "float"}
    max_order_multiplier = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 1.0, "max": 1.5, "type": "float"}

    # Calculate total pipeline inventory (simpler weighted sum)
    weighted_pipeline = sum(p * (pipeline_weight ** i) for i, p in enumerate(pipeline_orders))

    # Calculate inventory position
    inventory_position = on_hand_inventory + weighted_pipeline

    # Calculate target inventory level
    expected_lead_time_demand = demand_forecast * len(pipeline_orders)
    target_inventory = expected_lead_time_demand + safety_stock

    # Use base_stock as primary target
    order_up_to = 0.9 * base_stock + 0.1 * target_inventory

    # Calculate raw order amount
    raw_order = max(0, order_up_to - inventory_position)

    # Apply maximum order cap
    capped_order = min(raw_order, max_order_multiplier * demand_forecast)

    # Apply smoothing for all orders above threshold
    if capped_order > demand_forecast * order_threshold:
        order_amount = smoothing_factor * capped_order + (1 - smoothing_factor) * demand_forecast
    else:
        order_amount = capped_order

    # Ensure non-negative integer order
    return order_amount
