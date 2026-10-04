# policy_hash: 2e19f0e6d6b24710e516391eaf0890f2e8ae5c74da2ce55265d8d2e3a3a1a697
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std30_L6_c1_2
# matched_train_cells: 59
# source_prompt_files: 1
# best_target_performance: 2339.98
# best_prompt_performance: 2339.98
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std30_L6_c1_2_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260128_054013.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 380.0  # OPT_PARAM: {"initial": 380.0, "min": 200, "max": 600, "type": "float"}
    safety_stock = 80.0  # OPT_PARAM: {"initial": 80.0, "min": 30, "max": 150, "type": "float"}
    demand_forecast = 92.8427603170146  # OPT_PARAM: {"initial": 92.8427603170146, "min": 80, "max": 130, "type": "float"}
    smoothing_factor = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.5, "type": "float"}

    # Calculate inventory position (standard definition)
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    expected_lead_time_demand = demand_forecast * len(pipeline_orders)

    # Calculate target inventory level
    target_inventory = expected_lead_time_demand + safety_stock

    # Cap target by base_stock for cost efficiency
    order_up_to = min(base_stock, target_inventory)

    # Calculate order amount
    order_amount = max(0, order_up_to - inventory_position)

    # Apply exponential smoothing to reduce order volatility
    order_amount = smoothing_factor * order_amount + (1 - smoothing_factor) * demand_forecast

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
