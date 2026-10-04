# policy_hash: abb096d5de56642507b7e8960c8d897fa4da2a06cda573e9f7defa63f987f17b
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L2_c1_2
# matched_train_cells: 34
# source_prompt_files: 1
# best_target_performance: 974.18
# best_prompt_performance: 974.18
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L2_c1_2_50_plain_processed_scipy_15_default_m2_2_r9/prompt_for_code/m2_20260129_213345.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 249.76267260083466  # OPT_PARAM: {"initial": 249.76267260083466, "min": 100, "max": 400, "type": "float"}
    demand_forecast = 95.48563174787796  # OPT_PARAM: {"initial": 95.48563174787796, "min": 80, "max": 120, "type": "float"}
    safety_factor = 1.1104154308518628  # OPT_PARAM: {"initial": 1.1104154308518628, "min": 0.5, "max": 3.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time plus one period
    lead_time = len(pipeline_orders)
    lead_time_demand = demand_forecast * (lead_time + 1)

    # Calculate safety stock based on demand variability
    safety_stock = safety_factor * demand_forecast

    # Calculate target inventory level
    target_inventory = lead_time_demand + safety_stock

    # Calculate order amount
    order_amount = max(0, target_inventory - inventory_position)

    # Apply base stock as upper bound
    if order_amount > base_stock:
        order_amount = base_stock

    return order_amount
