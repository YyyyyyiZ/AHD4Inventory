# policy_hash: 14e150bbb4eb41bd80d71d1473f5119f42eddb12b340a2c51834344db6337099
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_2
# matched_train_cells: 5
# source_prompt_files: 1
# best_target_performance: 5937.18
# best_prompt_performance: 5937.02
# best_rel_error_pct: 0.002695
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_025025.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 184.9918549757947  # OPT_PARAM: {"initial": 184.9918549757947, "min": 100, "max": 400, "type": "float"}
    safety_factor = 1.4909206114986728  # OPT_PARAM: {"initial": 1.4909206114986728, "min": 1.0, "max": 3.0, "type": "float"}
    demand_estimate = 109.99685716155614  # OPT_PARAM: {"initial": 109.99685716155614, "min": 50, "max": 300, "type": "float"}
    pipeline_weight = 0.6945144235308484  # OPT_PARAM: {"initial": 0.6945144235308484, "min": 0.1, "max": 0.8, "type": "float"}
    smoothing = 0.5509150421790453  # OPT_PARAM: {"initial": 0.5509150421790453, "min": 0.1, "max": 0.9, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    lead_time_demand = demand_estimate * len(pipeline_orders)

    # Adjust base stock with safety factor
    safety_stock = safety_factor * (lead_time_demand ** 0.5)
    target_inventory = base_stock + safety_stock

    # Account for pipeline more aggressively
    pipeline_adjustment = pipeline_weight * sum(pipeline_orders)
    adjusted_target = max(target_inventory - pipeline_adjustment, lead_time_demand)

    # Calculate raw order
    raw_order = max(0, adjusted_target - inventory_position)

    # Apply smoothing with demand-based floor
    smoothed_order = smoothing * raw_order + (1 - smoothing) * demand_estimate

    # Ensure order covers at least expected demand
    min_order = max(0, demand_estimate - on_hand_inventory - pipeline_orders[0])
    final_order = max(smoothed_order, min_order)

    # Round to nearest integer
    order_amount = int(round(final_order))

    return order_amount
