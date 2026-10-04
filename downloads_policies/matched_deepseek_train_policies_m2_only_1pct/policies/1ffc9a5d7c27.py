# policy_hash: 1ffc9a5d7c272f187428ee7021941325e61a0ba82ed75079337076f3917a4f08
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L4_c1_2
# matched_train_cells: 11
# source_prompt_files: 1
# best_target_performance: 1005.02
# best_prompt_performance: 1005.02
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L4_c1_2_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260129_235344.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 475.93540254784693  # OPT_PARAM: {"initial": 475.93540254784693, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 50.0  # OPT_PARAM: {"initial": 50.0, "min": 0, "max": 200, "type": "float"}
    demand_forecast = 93.01632100542933  # OPT_PARAM: {"initial": 93.01632100542933, "min": 50, "max": 150, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.9, "type": "float"}

    # Calculate current inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    expected_lead_time_demand = demand_forecast * len(pipeline_orders)

    # Calculate target inventory level
    target_inventory = expected_lead_time_demand + safety_stock

    # Calculate order-up-to level
    order_up_to = max(base_stock, target_inventory)

    # Calculate order amount with smoothing
    raw_order = max(0, order_up_to - inventory_position)
    smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * demand_forecast

    # Round to nearest integer (as order amount should be integer)
    order_amount = int(round(smoothed_order))

    return order_amount
