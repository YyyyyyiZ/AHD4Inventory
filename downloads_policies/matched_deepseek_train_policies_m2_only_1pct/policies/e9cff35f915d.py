# policy_hash: e9cff35f915dc8966987ddbfc63400a925c889bd9fb5be1eea9c1eceb6e60154
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L4_c1_2
# matched_train_cells: 21
# source_prompt_files: 1
# best_target_performance: 744.55
# best_prompt_performance: 744.55
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L4_c1_2_50_plain_processed_scipy_15_default_m2_2_r8/prompt_for_code/m2_20260128_080013.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 420.1  # OPT_PARAM: {"initial": 420.1, "min": 350, "max": 500, "type": "float"}
    safety_stock = 52.09750570843611  # OPT_PARAM: {"initial": 52.09750570843611, "min": 30, "max": 100, "type": "float"}
    demand_forecast = 95.99997760412222  # OPT_PARAM: {"initial": 95.99997760412222, "min": 90, "max": 110, "type": "float"}
    smoothing_factor = 0.0  # OPT_PARAM: {"initial": 0.0, "min": 0.0, "max": 0.5, "type": "float"}
    pipeline_weight = 0.6317145701092172  # OPT_PARAM: {"initial": 0.6317145701092172, "min": 0.6, "max": 1.0, "type": "float"}

    # Calculate inventory position with discounted pipeline
    inventory_position = on_hand_inventory
    for i, p in enumerate(pipeline_orders):
        inventory_position += p * (pipeline_weight ** (i + 1))

    # Calculate expected demand during lead time
    expected_lead_time_demand = demand_forecast * len(pipeline_orders)

    # Dynamic safety stock adjustment
    pipeline_sum = sum(pipeline_orders)
    if pipeline_sum > 0:
        pipeline_ratio = sum(p * (pipeline_weight ** (i + 1)) for i, p in enumerate(pipeline_orders)) / pipeline_sum
        adjusted_safety = safety_stock * (0.8 + 0.4 * pipeline_ratio)
    else:
        adjusted_safety = safety_stock

    # Calculate target inventory level
    target_inventory = expected_lead_time_demand + adjusted_safety

    # Use the minimum of base_stock and target_inventory for tighter control
    order_up_to = min(base_stock, target_inventory)

    # Calculate order quantity
    order_amount = max(0, order_up_to - inventory_position)

    # Apply smoothing to reduce order volatility
    if order_amount > 0:
        smoothed_order = smoothing_factor * order_amount + (1 - smoothing_factor) * demand_forecast
        order_amount = min(order_amount, smoothed_order)

    return order_amount
