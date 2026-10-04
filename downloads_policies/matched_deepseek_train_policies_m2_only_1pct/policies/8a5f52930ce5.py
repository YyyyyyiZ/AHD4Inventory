# policy_hash: 8a5f52930ce5c1551527afbee24a715826bf132452e8f395fe356d4b7473b08d
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std30_L4_c1_5
# matched_train_cells: 10
# source_prompt_files: 1
# best_target_performance: 4186.92
# best_prompt_performance: 4184.72
# best_rel_error_pct: 0.052545
# example_source_txt: examples/inventory/deepseek-chat_normal_std30_L4_c1_5_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260128_043828.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 510.7725789298141  # OPT_PARAM: {"initial": 510.7725789298141, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 50.0  # OPT_PARAM: {"initial": 50.0, "min": 0, "max": 200, "type": "float"}
    demand_adj_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 2.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand from recent pipeline arrivals
    recent_arrivals = pipeline_orders[:2] if len(pipeline_orders) >= 2 else pipeline_orders
    avg_recent_demand = sum(recent_arrivals) / len(recent_arrivals) if recent_arrivals else 0

    # Adjust base stock based on recent demand pattern
    adjusted_base = base_stock + demand_adj_factor * (avg_recent_demand - base_stock / (len(pipeline_orders) + 1))

    # Calculate order-up-to level with safety stock
    order_up_to = max(safety_stock, adjusted_base)

    # Place order to reach order-up-to level
    order_amount = max(0, order_up_to - inventory_position)

    # Smooth ordering by limiting large changes
    max_order_change = 117.98048188340864  # OPT_PARAM: {"initial": 117.98048188340864, "min": 10, "max": 300, "type": "float"}
    if len(pipeline_orders) > 0:
        last_order = pipeline_orders[-1]
        if abs(order_amount - last_order) > max_order_change:
            if order_amount > last_order:
                order_amount = last_order + max_order_change
            else:
                order_amount = max(0, last_order - max_order_change)

    return order_amount
