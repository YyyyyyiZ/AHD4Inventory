# policy_hash: 1c35f4a94e826d60882d47d49b048cfd129126c6688e91aef2c1726f6d0d1d1d
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std30_L4_c1_5
# matched_train_cells: 15
# source_prompt_files: 1
# best_target_performance: 4173.5
# best_prompt_performance: 4174.19
# best_rel_error_pct: 0.016533
# example_source_txt: examples/inventory/deepseek-chat_normal_std30_L4_c1_5_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260128_045632.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 508.1397357287865  # OPT_PARAM: {"initial": 508.1397357287865, "min": 300, "max": 600, "type": "float"}
    safety_stock = 90.1  # OPT_PARAM: {"initial": 90.1, "min": 30, "max": 150, "type": "float"}
    demand_adj_factor = 0.01  # OPT_PARAM: {"initial": 0.01, "min": 0.01, "max": 0.2, "type": "float"}
    max_order_change = 119.79464084378351  # OPT_PARAM: {"initial": 119.79464084378351, "min": 40, "max": 150, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand from recent pipeline arrivals (last 2 periods)
    if len(pipeline_orders) >= 2:
        recent_arrivals = pipeline_orders[:2]
    else:
        recent_arrivals = pipeline_orders

    avg_recent_demand = sum(recent_arrivals) / len(recent_arrivals) if recent_arrivals else 0

    # Adjust base stock based on recent demand pattern
    # More responsive adjustment with higher factor
    adjusted_base = base_stock + demand_adj_factor * (avg_recent_demand - base_stock / 5)

    # Calculate order-up-to level with safety stock
    order_up_to = max(safety_stock, adjusted_base)

    # Place order to reach order-up-to level
    order_amount = max(0, order_up_to - inventory_position)

    # Smooth ordering by limiting large changes
    if len(pipeline_orders) > 0:
        last_order = pipeline_orders[-1]
        if abs(order_amount - last_order) > max_order_change:
            if order_amount > last_order:
                order_amount = last_order + max_order_change
            else:
                order_amount = max(0, last_order - max_order_change)

    return order_amount
