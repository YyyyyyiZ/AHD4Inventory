# policy_hash: b216381da017b66c3838f4691b055eb33deece7fafb50351da224d9911b2dd71
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_5
# matched_train_cells: 9
# source_prompt_files: 1
# best_target_performance: 2218.0
# best_prompt_performance: 2218.74
# best_rel_error_pct: 0.033363
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_095459.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 300.0  # OPT_PARAM: {"initial": 300.0, "min": 300, "max": 600, "type": "float"}
    safety_stock = 178.0157284856364  # OPT_PARAM: {"initial": 178.0157284856364, "min": 50, "max": 200, "type": "float"}
    demand_forecast = 104.19643639036876  # OPT_PARAM: {"initial": 104.19643639036876, "min": 90, "max": 120, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.5, "type": "float"}
    lead_time = len(pipeline_orders)

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    expected_lead_time_demand = demand_forecast * lead_time

    # Calculate target inventory position
    target_inventory = expected_lead_time_demand + safety_stock

    # Calculate raw order amount
    order_amount_raw = max(0, target_inventory - inventory_position)

    # Apply smoothing with base_stock cap
    order_amount = smoothing_factor * order_amount_raw + (1 - smoothing_factor) * min(order_amount_raw, base_stock)

    # Round to nearest integer
    return order_amount
