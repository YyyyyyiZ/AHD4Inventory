# policy_hash: d9ba4d313233962ef00133d9f97c2b78ece1ba32946853f2bee88f9c95601c9c
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_2
# matched_train_cells: 3
# source_prompt_files: 1
# best_target_performance: 812.94
# best_prompt_performance: 812.94
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_2_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260130_033655.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 474.22089514804765  # OPT_PARAM: {"initial": 474.22089514804765, "min": 400, "max": 600, "type": "float"}
    safety_stock = 40.0  # OPT_PARAM: {"initial": 40.0, "min": 20, "max": 80, "type": "float"}
    demand_forecast = 95.99375585849604  # OPT_PARAM: {"initial": 95.99375585849604, "min": 80, "max": 120, "type": "float"}
    smoothing_factor = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.5, "type": "float"}
    pipeline_weight = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.5, "max": 1.0, "type": "float"}

    # Calculate inventory position with weighted pipeline
    weighted_pipeline = sum(p * pipeline_weight**(i+1) for i, p in enumerate(pipeline_orders))
    inventory_position = on_hand_inventory + weighted_pipeline

    # Calculate expected demand during lead time
    expected_lead_time_demand = demand_forecast * len(pipeline_orders)

    # Calculate target inventory level
    target_inventory = expected_lead_time_demand + safety_stock

    # Use the maximum of base_stock and target_inventory
    order_up_to = max(base_stock, target_inventory)

    # Calculate raw order amount
    raw_order = max(0, order_up_to - inventory_position)

    # Apply smoothing only if order is significant
    if raw_order > demand_forecast * 0.5:
        order_amount = smoothing_factor * raw_order + (1 - smoothing_factor) * demand_forecast
    else:
        order_amount = raw_order

    # Round to nearest integer for practical implementation
    return order_amount
