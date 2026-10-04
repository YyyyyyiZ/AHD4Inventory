# policy_hash: 83613403c95a4134b24518a5f68014a39ebc6cd691de69bd5b81ce8907c3f8fb
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_2
# matched_train_cells: 2
# source_prompt_files: 1
# best_target_performance: 2835.54
# best_prompt_performance: 2837.94
# best_rel_error_pct: 0.084640
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_050223.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 680.0  # OPT_PARAM: {"initial": 680.0, "min": 500, "max": 900, "type": "float"}
    safety_stock = 45.0  # OPT_PARAM: {"initial": 45.0, "min": 20, "max": 80, "type": "float"}
    demand_forecast = 120.0  # OPT_PARAM: {"initial": 120.0, "min": 80, "max": 120, "type": "float"}
    lead_time = len(pipeline_orders)

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected lead time demand with safety stock
    expected_lead_time_demand = demand_forecast * lead_time
    target_position = expected_lead_time_demand + safety_stock

    # Calculate order amount to reach target
    order_amount = max(0, target_position - inventory_position)

    # Apply base stock policy as upper bound
    max_order = max(0, base_stock - inventory_position)
    order_amount = min(order_amount, max_order)

    # Round to nearest integer since demand is integer
    order_amount = int(round(order_amount))

    return order_amount
