# policy_hash: 9e76df7535dd4330282217def0803d8c3b49f5c126d879a72c18fd632c3cf650
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std30_L4_c1_5
# matched_train_cells: 28
# source_prompt_files: 1
# best_target_performance: 3773.08
# best_prompt_performance: 3776.0
# best_rel_error_pct: 0.077390
# example_source_txt: examples/inventory/deepseek-chat_normal_std30_L4_c1_5_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260128_051735.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 550.0  # OPT_PARAM: {"initial": 550.0, "min": 400, "max": 550, "type": "float"}
    safety_stock = 90.0  # OPT_PARAM: {"initial": 90.0, "min": 50, "max": 120, "type": "float"}
    demand_adj_factor = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.3, "type": "float"}
    max_order_change = 87.78773606657549  # OPT_PARAM: {"initial": 87.78773606657549, "min": 50, "max": 120, "type": "float"}
    pipeline_weight = 0.4  # OPT_PARAM: {"initial": 0.4, "min": 0.4, "max": 0.9, "type": "float"}
    lost_sales_weight = 1.1  # OPT_PARAM: {"initial": 1.1, "min": 1.0, "max": 1.5, "type": "float"}
    holding_weight = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand from recent pipeline arrivals
    if len(pipeline_orders) >= 4:
        recent_arrivals = pipeline_orders[:4]
    else:
        recent_arrivals = pipeline_orders

    avg_recent_demand = sum(recent_arrivals) / len(recent_arrivals) if recent_arrivals else 0

    # Adjust base stock based on recent demand pattern
    # Use asymmetric adjustment: stronger for lost sales prevention
    if avg_recent_demand > base_stock / 4:
        adjustment = demand_adj_factor * lost_sales_weight * (avg_recent_demand - base_stock / 4)
    else:
        adjustment = demand_adj_factor * holding_weight * (avg_recent_demand - base_stock / 4)

    adjusted_base = base_stock + adjustment

    # Calculate order-up-to level with safety stock
    order_up_to = max(safety_stock, adjusted_base)

    # Place order to reach order-up-to level
    order_amount = max(0, order_up_to - inventory_position)

    # Apply pipeline smoothing with stronger consideration for future arrivals
    if len(pipeline_orders) > 0:
        future_arrivals = sum(pipeline_orders[1:]) if len(pipeline_orders) > 1 else 0
        if future_arrivals > 0:
            # More aggressive reduction when pipeline is full
            reduction_factor = max(pipeline_weight, 1.0 - (future_arrivals / (order_up_to * 0.8)))
            order_amount = order_amount * reduction_factor

    # Smooth ordering by limiting large changes
    if len(pipeline_orders) > 0:
        last_order = pipeline_orders[-1]
        if abs(order_amount - last_order) > max_order_change:
            if order_amount > last_order:
                order_amount = last_order + max_order_change
            else:
                order_amount = max(0, last_order - max_order_change)

    return order_amount
