# policy_hash: d1169f1af070779bc0a8ffee3960bdd6906686326663fddbe78f44c9d1608356
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L6_c1_5
# matched_train_cells: 34
# source_prompt_files: 1
# best_target_performance: 1264.81
# best_prompt_performance: 1264.81
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260129_071622.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 854.0927830715955  # OPT_PARAM: {"initial": 854.0927830715955, "min": 800, "max": 950, "type": "float"}
    safety_stock = 40.99595470111844  # OPT_PARAM: {"initial": 40.99595470111844, "min": 30, "max": 70, "type": "float"}
    demand_forecast = 98.29263646577793  # OPT_PARAM: {"initial": 98.29263646577793, "min": 95, "max": 105, "type": "float"}
    smoothing_factor = 0.0  # OPT_PARAM: {"initial": 0.0, "min": 0.0, "max": 0.5, "type": "float"}
    pipeline_weight = 0.5380011143144084  # OPT_PARAM: {"initial": 0.5380011143144084, "min": 0.4, "max": 0.8, "type": "float"}
    order_threshold = 0.8676141679270764  # OPT_PARAM: {"initial": 0.8676141679270764, "min": 0.5, "max": 1.0, "type": "float"}

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
