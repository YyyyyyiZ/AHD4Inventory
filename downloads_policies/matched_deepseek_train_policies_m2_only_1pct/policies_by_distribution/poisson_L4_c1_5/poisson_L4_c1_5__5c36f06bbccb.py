# policy_hash: 5c36f06bbccbb4a6e91d74b043174f97009a43e6316ef1a434591e9b3df25080
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_5
# matched_train_cells: 41
# source_prompt_files: 1
# best_target_performance: 1422.29
# best_prompt_performance: 1422.29
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_5_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260128_190724.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 493.6989159248647  # OPT_PARAM: {"initial": 493.6989159248647, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 50.1  # OPT_PARAM: {"initial": 50.1, "min": 0, "max": 200, "type": "float"}
    demand_forecast = 99.03984148957005  # OPT_PARAM: {"initial": 99.03984148957005, "min": 50, "max": 150, "type": "float"}
    smoothing_factor = 0.13122311280115487  # OPT_PARAM: {"initial": 0.13122311280115487, "min": 0.1, "max": 0.9, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    expected_lead_time_demand = demand_forecast * len(pipeline_orders)

    # Calculate target inventory position
    target_position = expected_lead_time_demand + safety_stock

    # Calculate order-up-to level
    order_up_to = max(base_stock, target_position)

    # Calculate order amount
    order_amount = max(0, order_up_to - inventory_position)

    # Apply smoothing to avoid large order fluctuations
    if order_amount > 0:
        order_amount = smoothing_factor * order_amount + (1 - smoothing_factor) * demand_forecast

    return order_amount
