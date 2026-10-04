# policy_hash: 914e9f982aec3100fb55fd36869c15265a1d100543209396c378fce21fd5cc6e
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_5
# matched_train_cells: 24
# source_prompt_files: 1
# best_target_performance: 11174.22
# best_prompt_performance: 11174.22
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_010909.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 402.8191025150848  # OPT_PARAM: {"initial": 402.8191025150848, "min": 300, "max": 700, "type": "float"}
    safety_stock = 30.05470511303909  # OPT_PARAM: {"initial": 30.05470511303909, "min": 30, "max": 200, "type": "float"}
    demand_forecast_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 1.5, "type": "float"}
    smoothing_factor = 0.11743518743269722  # OPT_PARAM: {"initial": 0.11743518743269722, "min": 0.05, "max": 0.5, "type": "float"}
    lead_time_factor = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 2.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Improved demand forecast using weighted average of pipeline orders
    if pipeline_orders:
        # Give more weight to recent orders
        weights = [0.3, 0.4, 0.2, 0.1][-len(pipeline_orders):]
        weighted_sum = sum(w * o for w, o in zip(weights, pipeline_orders))
        avg_recent_demand = weighted_sum / sum(weights[:len(pipeline_orders)])
    else:
        avg_recent_demand = 0

    # Adjust base stock based on demand forecast and lead time
    adjusted_base_stock = base_stock + demand_forecast_factor * avg_recent_demand * lead_time_factor

    # Add safety stock with lead time consideration
    order_up_to = adjusted_base_stock + safety_stock * (1 + 0.1 * len(pipeline_orders))

    # Calculate raw order quantity
    raw_order = max(0, order_up_to - inventory_position)

    # Apply smoothing with stronger emphasis on recent demand
    if pipeline_orders and len(pipeline_orders) >= 2:
        last_order = pipeline_orders[-1]
        second_last = pipeline_orders[-2]
        recent_avg = (last_order + second_last) / 2
        smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * recent_avg
    elif pipeline_orders:
        smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * pipeline_orders[-1]
    else:
        smoothed_order = raw_order

    # Dynamic order limit based on forecast
    max_order_limit = 750.0  # OPT_PARAM: {"initial": 750.0, "min": 300, "max": 1000, "type": "float"}
    smoothed_order = min(smoothed_order, max_order_limit)

    # Smarter minimum order quantity
    min_order_quantity = 30.1  # OPT_PARAM: {"initial": 30.1, "min": 0, "max": 50, "type": "float"}
    if smoothed_order > 0 and smoothed_order < min_order_quantity:
        # Only enforce minimum if inventory position is low
        if inventory_position < order_up_to * 0.7:
            smoothed_order = min_order_quantity

    # Round to nearest integer
    order_amount = int(round(smoothed_order))

    return order_amount
