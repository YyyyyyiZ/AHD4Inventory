# policy_hash: c7aa6672b1593c3c94c2a7acd5f31faea8047b1df6436070839a9ef2674b1ddd
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_5
# matched_train_cells: 6
# source_prompt_files: 1
# best_target_performance: 12845.0
# best_prompt_performance: 12838.9
# best_rel_error_pct: 0.047489
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_060507.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 449.0787162687127  # OPT_PARAM: {"initial": 449.0787162687127, "min": 100, "max": 800, "type": "float"}
    safety_factor = 1.726275893457961  # OPT_PARAM: {"initial": 1.726275893457961, "min": 0.5, "max": 3.0, "type": "float"}
    demand_smoothing = 0.237785401809561  # OPT_PARAM: {"initial": 0.237785401809561, "min": 0.1, "max": 0.8, "type": "float"}
    order_smoothing = 0.9899083771787107  # OPT_PARAM: {"initial": 0.9899083771787107, "min": 0.1, "max": 1.0, "type": "float"}

    lead_time = len(pipeline_orders)

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate demand using exponential smoothing of pipeline arrivals
    # Pipeline orders reflect recent demand patterns
    if len(pipeline_orders) > 0:
        # Use weighted average with more weight on recent periods
        weights = [0.5**i for i in range(len(pipeline_orders))]
        weights = [w/sum(weights) for w in weights]
        weighted_demand = sum(w * q for w, q in zip(weights, pipeline_orders))

        # Apply exponential smoothing
        if 'prev_demand_est' not in compute_order_amount.__dict__:
            compute_order_amount.prev_demand_est = weighted_demand
        smoothed_demand = (demand_smoothing * weighted_demand +
                          (1 - demand_smoothing) * compute_order_amount.prev_demand_est)
        compute_order_amount.prev_demand_est = smoothed_demand
    else:
        smoothed_demand = base_stock / (lead_time + 1)

    # Calculate safety stock based on demand variability
    safety_stock = safety_factor * smoothed_demand

    # Calculate order-up-to level
    order_up_to = base_stock + safety_stock

    # Calculate raw order amount
    raw_order = max(0, order_up_to - inventory_position)

    # Apply order smoothing to reduce volatility
    if 'prev_order' not in compute_order_amount.__dict__:
        compute_order_amount.prev_order = raw_order
    smoothed_order = (order_smoothing * raw_order +
                     (1 - order_smoothing) * compute_order_amount.prev_order)
    compute_order_amount.prev_order = smoothed_order

    # Round to nearest integer
    order_amount = int(round(smoothed_order))

    return order_amount
