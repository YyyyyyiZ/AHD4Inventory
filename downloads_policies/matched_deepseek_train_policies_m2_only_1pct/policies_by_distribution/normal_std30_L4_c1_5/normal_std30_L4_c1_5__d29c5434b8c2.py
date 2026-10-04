# policy_hash: d29c5434b8c21f0cd53804162d9dfd73d684730228944d3e8c5af5b4a265cddb
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std30_L4_c1_5
# matched_train_cells: 3
# source_prompt_files: 1
# best_target_performance: 3905.36
# best_prompt_performance: 3903.41
# best_rel_error_pct: 0.049931
# example_source_txt: examples/inventory/deepseek-chat_normal_std30_L4_c1_5_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260128_050838.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 550.0  # OPT_PARAM: {"initial": 550.0, "min": 400, "max": 550, "type": "float"}
    safety_stock = 75.0  # OPT_PARAM: {"initial": 75.0, "min": 50, "max": 120, "type": "float"}
    demand_adj_factor = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.3, "type": "float"}
    max_order_change = 94.69412732047371  # OPT_PARAM: {"initial": 94.69412732047371, "min": 50, "max": 120, "type": "float"}
    pipeline_weight = 0.6191082629260669  # OPT_PARAM: {"initial": 0.6191082629260669, "min": 0.4, "max": 0.9, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand from recent pipeline arrivals (last 3 periods)
    if len(pipeline_orders) >= 3:
        recent_arrivals = pipeline_orders[:3]
    else:
        recent_arrivals = pipeline_orders

    avg_recent_demand = sum(recent_arrivals) / len(recent_arrivals) if recent_arrivals else 0

    # Adjust base stock based on recent demand pattern
    # Use stronger adjustment with higher factor
    adjusted_base = base_stock + demand_adj_factor * (avg_recent_demand - base_stock / 4)

    # Calculate order-up-to level with safety stock
    order_up_to = max(safety_stock, adjusted_base)

    # Place order to reach order-up-to level
    order_amount = max(0, order_up_to - inventory_position)

    # Apply pipeline smoothing: consider future arrivals in ordering decision
    if len(pipeline_orders) > 0:
        future_arrivals = sum(pipeline_orders[1:]) if len(pipeline_orders) > 1 else 0
        # Reduce order if sufficient pipeline inventory is coming
        if future_arrivals > 0:
            order_amount = order_amount * pipeline_weight

    # Smooth ordering by limiting large changes
    if len(pipeline_orders) > 0:
        last_order = pipeline_orders[-1]
        if abs(order_amount - last_order) > max_order_change:
            if order_amount > last_order:
                order_amount = last_order + max_order_change
            else:
                order_amount = max(0, last_order - max_order_change)

    return order_amount
