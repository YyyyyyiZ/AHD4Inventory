# policy_hash: 8f008f8aad256a781575b9d7f43eb05131827123b74b07c0996396400b4fb42a
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_5
# matched_train_cells: 10
# source_prompt_files: 1
# best_target_performance: 11397.07
# best_prompt_performance: 11396.78
# best_rel_error_pct: 0.002545
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260129_095931.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 554.5851702816196  # OPT_PARAM: {"initial": 554.5851702816196, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 50.0  # OPT_PARAM: {"initial": 50.0, "min": 0, "max": 200, "type": "float"}
    demand_forecast = 69.71904169441764  # OPT_PARAM: {"initial": 69.71904169441764, "min": 10, "max": 300, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.9, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    lead_time = len(pipeline_orders)
    expected_demand_during_lead_time = demand_forecast * lead_time

    # Calculate target inventory level
    target_inventory = expected_demand_during_lead_time + safety_stock

    # Calculate order-up-to level
    order_up_to_level = max(base_stock, target_inventory)

    # Calculate order amount
    order_amount = max(0, order_up_to_level - inventory_position)

    # Smooth the order amount to avoid extreme fluctuations
    if order_amount > 0:
        order_amount = smoothing_factor * order_amount + (1 - smoothing_factor) * demand_forecast

    return order_amount
