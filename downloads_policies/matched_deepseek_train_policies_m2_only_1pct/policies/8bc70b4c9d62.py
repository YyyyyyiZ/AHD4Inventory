# policy_hash: 8bc70b4c9d627aa94db37dd5032ea40f78977e5af7c922f90b673fd706d4d4d7
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L6_c1_5
# matched_train_cells: 20
# source_prompt_files: 1
# best_target_performance: 1265.62
# best_prompt_performance: 1265.62
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260129_070851.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 845.4902974665813  # OPT_PARAM: {"initial": 845.4902974665813, "min": 700, "max": 1000, "type": "float"}
    safety_stock = 36.99376350516456  # OPT_PARAM: {"initial": 36.99376350516456, "min": 20, "max": 80, "type": "float"}
    demand_forecast = 98.4666391941237  # OPT_PARAM: {"initial": 98.4666391941237, "min": 95, "max": 105, "type": "float"}
    smoothing_factor = 0.0  # OPT_PARAM: {"initial": 0.0, "min": 0.0, "max": 0.5, "type": "float"}
    pipeline_weight = 0.564959216408414  # OPT_PARAM: {"initial": 0.564959216408414, "min": 0.4, "max": 0.8, "type": "float"}
    order_threshold = 0.8706310074948068  # OPT_PARAM: {"initial": 0.8706310074948068, "min": 0.3, "max": 1.0, "type": "float"}

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
