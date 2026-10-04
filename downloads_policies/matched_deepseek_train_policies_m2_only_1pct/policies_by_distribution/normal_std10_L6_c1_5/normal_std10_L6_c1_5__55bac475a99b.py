# policy_hash: 55bac475a99be1dfb373ad14c95ce463f6a5a0d4ea05e00a6bdb25d810f5440b
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L6_c1_5
# matched_train_cells: 18
# source_prompt_files: 1
# best_target_performance: 1284.96
# best_prompt_performance: 1284.96
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260129_193635.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 652.2544139460238  # OPT_PARAM: {"initial": 652.2544139460238, "min": 400, "max": 900, "type": "float"}
    safety_stock = 80.1  # OPT_PARAM: {"initial": 80.1, "min": 30, "max": 150, "type": "float"}
    demand_forecast = 98.36101600180123  # OPT_PARAM: {"initial": 98.36101600180123, "min": 80, "max": 120, "type": "float"}
    smoothing_factor = 0.01253395757449696  # OPT_PARAM: {"initial": 0.01253395757449696, "min": 0.0, "max": 0.8, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    expected_lead_time_demand = demand_forecast * len(pipeline_orders)

    # Calculate order-up-to level using both base stock and safety stock
    order_up_to = max(base_stock, expected_lead_time_demand + safety_stock)

    # Calculate order quantity
    order_amount = max(0, order_up_to - inventory_position)

    # Apply smoothing only when order is positive
    if order_amount > 0 and smoothing_factor > 0:
        order_amount = smoothing_factor * order_amount + (1 - smoothing_factor) * demand_forecast

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
