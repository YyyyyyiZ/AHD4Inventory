# policy_hash: e683fc88c3ac3dee8532453ff4c34e1f2bdc24b2d83c736aeb065abe18d31359
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std30_L4_c1_5
# matched_train_cells: 11
# source_prompt_files: 1
# best_target_performance: 3698.33
# best_prompt_performance: 3701.98
# best_rel_error_pct: 0.098693
# example_source_txt: examples/inventory/deepseek-chat_normal_std30_L4_c1_5_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260128_052355.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 565.4480421605462  # OPT_PARAM: {"initial": 565.4480421605462, "min": 400, "max": 600, "type": "float"}
    safety_stock = 75.0  # OPT_PARAM: {"initial": 75.0, "min": 50, "max": 120, "type": "float"}
    demand_adj_factor = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.3, "type": "float"}
    max_order_change = 97.46322868507833  # OPT_PARAM: {"initial": 97.46322868507833, "min": 30, "max": 100, "type": "float"}
    pipeline_weight = 0.6  # OPT_PARAM: {"initial": 0.6, "min": 0.3, "max": 0.9, "type": "float"}
    lost_sales_weight = 1.3  # OPT_PARAM: {"initial": 1.3, "min": 1.0, "max": 1.8, "type": "float"}
    holding_weight = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.1, "max": 0.5, "type": "float"}
    demand_window = 3  # OPT_PARAM: {"initial": 3, "min": 2, "max": 6, "type": "int"}
    pipeline_cap_factor = 0.8  # OPT_PARAM: {"initial": 0.8, "min": 0.5, "max": 0.9, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand from recent pipeline arrivals
    if len(pipeline_orders) >= demand_window:
        recent_arrivals = pipeline_orders[:demand_window]
    else:
        recent_arrivals = pipeline_orders

    avg_recent_demand = sum(recent_arrivals) / len(recent_arrivals) if recent_arrivals else 0

    # Adjust base stock based on recent demand pattern
    # Stronger adjustment for lost sales prevention
    if avg_recent_demand > base_stock / 4:
        adjustment = demand_adj_factor * lost_sales_weight * (avg_recent_demand - base_stock / 4)
    else:
        adjustment = demand_adj_factor * holding_weight * (avg_recent_demand - base_stock / 4)

    adjusted_base = base_stock + adjustment

    # Calculate order-up-to level with safety stock
    order_up_to = max(safety_stock, adjusted_base)

    # Place order to reach order-up-to level
    order_amount = max(0, order_up_to - inventory_position)

    # Apply pipeline smoothing with cap on pipeline influence
    if len(pipeline_orders) > 0:
        future_arrivals = sum(pipeline_orders[1:]) if len(pipeline_orders) > 1 else 0
        if future_arrivals > 0:
            # Cap the pipeline influence to avoid over-reduction
            pipeline_ratio = min(future_arrivals / (order_up_to * pipeline_cap_factor), 1.0)
            reduction_factor = max(pipeline_weight * 0.5, 1.0 - pipeline_ratio)
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
