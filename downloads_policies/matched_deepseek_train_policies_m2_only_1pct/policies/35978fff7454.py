# policy_hash: 35978fff74547900160ea2a4d22d3c58693a191af3a273f6a8ea7e07f8ef2e09
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L6_c1_5
# matched_train_cells: 41
# source_prompt_files: 1
# best_target_performance: 1257.13
# best_prompt_performance: 1257.13
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260129_073015.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 908.8358397080203  # OPT_PARAM: {"initial": 908.8358397080203, "min": 850, "max": 1000, "type": "float"}
    safety_stock = 49.121172994904214  # OPT_PARAM: {"initial": 49.121172994904214, "min": 40, "max": 80, "type": "float"}
    demand_forecast = 98.71598687520105  # OPT_PARAM: {"initial": 98.71598687520105, "min": 95, "max": 105, "type": "float"}
    smoothing_factor = 0.0  # OPT_PARAM: {"initial": 0.0, "min": 0.0, "max": 0.5, "type": "float"}
    pipeline_weight = 0.46300784187901667  # OPT_PARAM: {"initial": 0.46300784187901667, "min": 0.4, "max": 0.8, "type": "float"}
    order_threshold = 0.9844868667060206  # OPT_PARAM: {"initial": 0.9844868667060206, "min": 0.5, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    expected_lead_time_demand = demand_forecast * len(pipeline_orders)

    # Calculate target inventory level
    target_inventory = expected_lead_time_demand + safety_stock

    # Use base_stock as primary target, adjusted by pipeline status
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
