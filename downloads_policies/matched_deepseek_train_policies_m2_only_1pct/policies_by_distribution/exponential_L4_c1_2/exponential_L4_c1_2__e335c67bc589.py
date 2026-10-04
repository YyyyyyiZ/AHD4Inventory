# policy_hash: e335c67bc589985e93009d201334ca9cfde73b6acca975f9bbf48124371fce77
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_2
# matched_train_cells: 15
# source_prompt_files: 1
# best_target_performance: 6161.54
# best_prompt_performance: 6161.54
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_080854.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 188.1026848137871  # OPT_PARAM: {"initial": 188.1026848137871, "min": 100, "max": 300, "type": "float"}
    safety_stock = 45.2  # OPT_PARAM: {"initial": 45.2, "min": 20, "max": 80, "type": "float"}
    demand_forecast_factor = 0.8914775364436464  # OPT_PARAM: {"initial": 0.8914775364436464, "min": 0.5, "max": 1.2, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.5, "type": "float"}
    pipeline_weight = 0.38449324961165027  # OPT_PARAM: {"initial": 0.38449324961165027, "min": 0.3, "max": 1.0, "type": "float"}
    lost_sales_weight = 2.4258050580350177  # OPT_PARAM: {"initial": 2.4258050580350177, "min": 1.0, "max": 3.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate demand using weighted average of pipeline orders
    if len(pipeline_orders) > 0:
        weights = [pipeline_weight ** i for i in range(len(pipeline_orders))]
        weighted_sum = sum(w * q for w, q in zip(weights, pipeline_orders))
        total_weight = sum(weights)
        demand_estimate = (weighted_sum / total_weight) * demand_forecast_factor
    else:
        demand_estimate = 0

    # Dynamic base stock adjustment with lost-sales emphasis
    adjusted_base_stock = base_stock + (demand_estimate * lost_sales_weight)

    # Calculate order-up-to level with safety stock
    order_up_to = max(adjusted_base_stock, safety_stock)

    # Calculate raw order amount
    raw_order = max(0, order_up_to - inventory_position)

    # Apply smoothing with previous orders
    if len(pipeline_orders) > 0:
        last_order = pipeline_orders[-1]
        smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * last_order
        order_amount = max(0, smoothed_order)
    else:
        order_amount = raw_order

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
