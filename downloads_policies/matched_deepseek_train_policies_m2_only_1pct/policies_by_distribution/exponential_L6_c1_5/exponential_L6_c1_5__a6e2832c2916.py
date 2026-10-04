# policy_hash: a6e2832c2916bbbe77ea262f584155890a0b7af2c554fd21a140452fa35cd56e
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_5
# matched_train_cells: 27
# source_prompt_files: 1
# best_target_performance: 11007.47
# best_prompt_performance: 11007.47
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260129_101507.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 450.0016463994671  # OPT_PARAM: {"initial": 450.0016463994671, "min": 200, "max": 800, "type": "float"}
    safety_stock = 109.45463498759725  # OPT_PARAM: {"initial": 109.45463498759725, "min": 50, "max": 300, "type": "float"}
    demand_forecast = 51.25504570348364  # OPT_PARAM: {"initial": 51.25504570348364, "min": 50, "max": 150, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.5, "type": "float"}
    pipeline_weight = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 1.0, "type": "float"}
    lost_sales_weight = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 1.0, "max": 2.0, "type": "float"}

    # Calculate inventory position with weighted pipeline
    weighted_pipeline = sum(p * pipeline_weight**(i+1) for i, p in enumerate(pipeline_orders))
    inventory_position = on_hand_inventory + weighted_pipeline

    # Calculate expected demand during lead time with safety buffer
    lead_time = len(pipeline_orders)
    expected_demand_during_lead_time = demand_forecast * lead_time * lost_sales_weight

    # Calculate target inventory level
    target_inventory = expected_demand_during_lead_time + safety_stock

    # Use the maximum of base_stock and target_inventory
    order_up_to_level = max(base_stock, target_inventory)

    # Calculate order amount
    order_amount = max(0, order_up_to_level - inventory_position)

    # Apply smoothing to order amount
    if order_amount > 0:
        order_amount = smoothing_factor * order_amount + (1 - smoothing_factor) * demand_forecast

    return order_amount
