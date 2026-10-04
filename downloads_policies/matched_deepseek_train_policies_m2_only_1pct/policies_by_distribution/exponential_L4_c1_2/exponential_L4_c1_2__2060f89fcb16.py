# policy_hash: 2060f89fcb169904d55ab85e5cd1094fe6e7d10e63930c23755724e2ad3a074a
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_2
# matched_train_cells: 7
# source_prompt_files: 1
# best_target_performance: 6156.36
# best_prompt_performance: 6155.44
# best_rel_error_pct: 0.014944
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_082906.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 211.70962921913787  # OPT_PARAM: {"initial": 211.70962921913787, "min": 150, "max": 300, "type": "float"}
    safety_stock = 38.7  # OPT_PARAM: {"initial": 38.7, "min": 20, "max": 60, "type": "float"}
    demand_forecast_factor = 1.042904139299252  # OPT_PARAM: {"initial": 1.042904139299252, "min": 0.8, "max": 1.3, "type": "float"}
    smoothing_factor = 0.07013236105907825  # OPT_PARAM: {"initial": 0.07013236105907825, "min": 0.05, "max": 0.3, "type": "float"}
    pipeline_weight = 0.27884712264161216  # OPT_PARAM: {"initial": 0.27884712264161216, "min": 0.1, "max": 0.8, "type": "float"}
    lost_sales_weight = 1.930880157106048  # OPT_PARAM: {"initial": 1.930880157106048, "min": 1.0, "max": 2.5, "type": "float"}
    holding_weight = 0.4790413570653473  # OPT_PARAM: {"initial": 0.4790413570653473, "min": 0.1, "max": 1.0, "type": "float"}

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

    # Dynamic base stock adjustment with cost-aware balancing
    cost_ratio = lost_sales_weight / (lost_sales_weight + holding_weight)
    adjusted_base_stock = base_stock + demand_estimate * (2.0 * cost_ratio)

    # Calculate order-up-to level with safety stock
    order_up_to = max(adjusted_base_stock, safety_stock + demand_estimate)

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
