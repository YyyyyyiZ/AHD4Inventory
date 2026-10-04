# policy_hash: cfdbb04c17cc3f3a79b13b2549ca29645b30ddc78a26bdce08857a7f6944d692
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_5
# matched_train_cells: 10
# source_prompt_files: 1
# best_target_performance: 10982.31
# best_prompt_performance: 10977.8
# best_rel_error_pct: 0.041066
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_051331.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 420.0  # OPT_PARAM: {"initial": 420.0, "min": 300, "max": 550, "type": "float"}
    demand_estimate = 130.0  # OPT_PARAM: {"initial": 130.0, "min": 100, "max": 180, "type": "float"}
    safety_multiplier = 0.9145906369536355  # OPT_PARAM: {"initial": 0.9145906369536355, "min": 0.8, "max": 1.8, "type": "float"}
    order_smoothing = 0.2606642673584208  # OPT_PARAM: {"initial": 0.2606642673584208, "min": 0.2, "max": 0.8, "type": "float"}
    min_order_fraction = 0.44883831367968846  # OPT_PARAM: {"initial": 0.44883831367968846, "min": 0.4, "max": 0.9, "type": "float"}
    lost_sales_weight = 0.841495559266685  # OPT_PARAM: {"initial": 0.841495559266685, "min": 0.5, "max": 0.9, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate safety stock
    lead_time = len(pipeline_orders)
    safety_stock = safety_multiplier * demand_estimate * (lead_time ** 0.5)

    # Adjust base stock based on lost sales weight (higher weight → higher base stock)
    adjusted_base_stock = base_stock * (1.0 + (1.0 - lost_sales_weight) * 0.3)

    # Calculate target inventory position
    target_position = adjusted_base_stock + safety_stock

    # Calculate order needed
    order_needed = target_position - inventory_position

    # Apply order smoothing with more aggressive ordering when below target
    if order_needed > 0:
        # Use stronger smoothing when significantly below target
        if inventory_position < target_position * min_order_fraction:
            order_amount = max(demand_estimate, order_smoothing * order_needed)
        else:
            order_amount = order_smoothing * order_needed
    else:
        order_amount = 0

    # Ensure integer order amount
    order_amount = max(0, int(round(order_amount)))

    return order_amount
