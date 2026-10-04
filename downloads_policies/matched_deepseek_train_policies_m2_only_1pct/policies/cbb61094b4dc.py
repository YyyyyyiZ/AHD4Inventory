# policy_hash: cbb61094b4dc86077c8cbf1bd03f102bbfcb56c7200a2ec3f2a064071846d8c0
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_2
# matched_train_cells: 17
# source_prompt_files: 1
# best_target_performance: 1173.49
# best_prompt_performance: 1173.42
# best_rel_error_pct: 0.005965
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_2_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260130_024501.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 485.3641994817895  # OPT_PARAM: {"initial": 485.3641994817895, "min": 400, "max": 600, "type": "float"}
    safety_stock = 25.0  # OPT_PARAM: {"initial": 25.0, "min": 10, "max": 50, "type": "float"}
    demand_adjustment = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.5, "type": "float"}
    lead_time = 4

    # Calculate net inventory position
    net_inventory = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand using all pipeline orders
    if len(pipeline_orders) > 0:
        avg_pipeline_demand = sum(pipeline_orders) / len(pipeline_orders)
    else:
        avg_pipeline_demand = 100.0  # default estimate

    # Adjust base stock based on demand pattern
    adjusted_base = base_stock + demand_adjustment * (avg_pipeline_demand - 100)

    # Calculate order-up-to level with safety stock
    order_up_to = max(adjusted_base, safety_stock + avg_pipeline_demand * lead_time)

    # Order amount
    order_amount = max(0, order_up_to - net_inventory)

    # Smooth ordering with tighter limits
    max_order_change = 38.3143803412377  # OPT_PARAM: {"initial": 38.3143803412377, "min": 20, "max": 60, "type": "float"}
    if len(pipeline_orders) > 0:
        last_order = pipeline_orders[-1]
        if abs(order_amount - last_order) > max_order_change:
            if order_amount > last_order:
                order_amount = last_order + max_order_change
            else:
                order_amount = max(0, last_order - max_order_change)

    # Round to integer for practical ordering
    return order_amount
