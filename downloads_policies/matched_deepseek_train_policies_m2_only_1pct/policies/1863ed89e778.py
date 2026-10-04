# policy_hash: 1863ed89e778507dd479e7354dff123197d178dd66c10610d5e225c6c22488bf
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L6_c1_5
# matched_train_cells: 20
# source_prompt_files: 1
# best_target_performance: 1272.55
# best_prompt_performance: 1272.55
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260129_070520.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 843.9320804498155  # OPT_PARAM: {"initial": 843.9320804498155, "min": 700, "max": 1000, "type": "float"}
    safety_stock = 57.05332838936518  # OPT_PARAM: {"initial": 57.05332838936518, "min": 30, "max": 100, "type": "float"}
    demand_forecast = 98.38504801329276  # OPT_PARAM: {"initial": 98.38504801329276, "min": 90, "max": 110, "type": "float"}
    smoothing_factor = 0.0  # OPT_PARAM: {"initial": 0.0, "min": 0.0, "max": 0.5, "type": "float"}
    pipeline_weight = 0.520162823803309  # OPT_PARAM: {"initial": 0.520162823803309, "min": 0.5, "max": 1.0, "type": "float"}
    order_threshold = 0.8690361291856622  # OPT_PARAM: {"initial": 0.8690361291856622, "min": 0.3, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    expected_lead_time_demand = demand_forecast * len(pipeline_orders)

    # Calculate target inventory level
    target_inventory = expected_lead_time_demand + safety_stock

    # Blend base_stock and target_inventory based on pipeline status
    effective_base = base_stock * pipeline_weight + target_inventory * (1 - pipeline_weight)

    # Calculate order-up-to level
    order_up_to_level = max(effective_base, target_inventory)

    # Calculate raw order amount
    raw_order = max(0, order_up_to_level - inventory_position)

    # Apply smoothing based on threshold
    if raw_order > demand_forecast * order_threshold:
        order_amount = raw_order * smoothing_factor + demand_forecast * (1 - smoothing_factor)
    else:
        order_amount = raw_order

    return order_amount
