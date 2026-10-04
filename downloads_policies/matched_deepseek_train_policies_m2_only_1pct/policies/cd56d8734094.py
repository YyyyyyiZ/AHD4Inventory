# policy_hash: cd56d8734094b40431e898c806a597af3939302a4f72d8348aa037daab38d6ca
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_2
# matched_train_cells: 7
# source_prompt_files: 1
# best_target_performance: 6186.47
# best_prompt_performance: 6186.6
# best_rel_error_pct: 0.002101
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_040141.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 266.48082838364166  # OPT_PARAM: {"initial": 266.48082838364166, "min": 100, "max": 500, "type": "float"}
    safety_stock = 31.4808283836388  # OPT_PARAM: {"initial": 31.4808283836388, "min": 10, "max": 150, "type": "float"}
    demand_sensitivity = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.5, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.8, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate demand from recent arrivals (last 3 periods)
    recent_arrivals = pipeline_orders[:3] if len(pipeline_orders) >= 3 else pipeline_orders
    if recent_arrivals:
        avg_recent_demand = sum(recent_arrivals) / len(recent_arrivals)
    else:
        avg_recent_demand = 0

    # Adjust base stock based on demand trend
    adjusted_base_stock = base_stock + demand_sensitivity * avg_recent_demand

    # Calculate target inventory position
    target_position = adjusted_base_stock + safety_stock

    # Calculate raw order amount
    raw_order = max(0, target_position - inventory_position)

    # Apply smoothing using last order if available
    if pipeline_orders:
        last_order = pipeline_orders[-1]
        smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * last_order
        order_amount = max(0, smoothed_order)
    else:
        order_amount = raw_order

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
