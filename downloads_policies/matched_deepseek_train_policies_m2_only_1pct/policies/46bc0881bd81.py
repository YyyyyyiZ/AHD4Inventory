# policy_hash: 46bc0881bd8108191421d772ef9a889809d43a71a495f51ca260d31e8bce0e15
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std30_L4_c1_5
# matched_train_cells: 65
# source_prompt_files: 1
# best_target_performance: 3673.9
# best_prompt_performance: 3674.08
# best_rel_error_pct: 0.004899
# example_source_txt: examples/inventory/deepseek-chat_normal_std30_L4_c1_5_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260129_225538.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 490.09862324244915  # OPT_PARAM: {"initial": 490.09862324244915, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 50.0  # OPT_PARAM: {"initial": 50.0, "min": 0, "max": 200, "type": "float"}
    demand_forecast = 91.55814509214328  # OPT_PARAM: {"initial": 91.55814509214328, "min": 50, "max": 200, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.9, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    expected_lead_time_demand = demand_forecast * len(pipeline_orders)

    # Calculate target inventory level
    target_inventory = expected_lead_time_demand + safety_stock

    # Calculate order-up-to level
    order_up_to = max(base_stock, target_inventory)

    # Calculate order amount with smoothing
    raw_order = max(0, order_up_to - inventory_position)
    order_amount = smoothing_factor * raw_order + (1 - smoothing_factor) * demand_forecast

    # Round to nearest integer (since order amount must be integer)
    order_amount = int(round(order_amount))

    return order_amount
