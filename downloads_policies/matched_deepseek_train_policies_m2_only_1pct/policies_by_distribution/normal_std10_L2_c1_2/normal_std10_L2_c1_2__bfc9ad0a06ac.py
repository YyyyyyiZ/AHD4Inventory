# policy_hash: bfc9ad0a06ac9c4a0fc301ebb9fd61948770617ad042d0d0f9d08ee4eeece7c3
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L2_c1_2
# matched_train_cells: 4
# source_prompt_files: 1
# best_target_performance: 695.33
# best_prompt_performance: 695.33
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L2_c1_2_50_plain_processed_scipy_15_default_m2_2_r8/prompt_for_code/m2_20260129_205517.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 306.562092561528  # OPT_PARAM: {"initial": 306.562092561528, "min": 290, "max": 330, "type": "float"}
    safety_stock = 42.0  # OPT_PARAM: {"initial": 42.0, "min": 30, "max": 55, "type": "float"}
    demand_buffer = 14.356068071338784  # OPT_PARAM: {"initial": 14.356068071338784, "min": 10, "max": 25, "type": "float"}
    smoothing_min = 8.0  # OPT_PARAM: {"initial": 8.0, "min": 5, "max": 15, "type": "float"}
    smoothing_max = 97.99619805333005  # OPT_PARAM: {"initial": 97.99619805333005, "min": 90, "max": 140, "type": "float"}
    pipeline_weight = 0.85  # OPT_PARAM: {"initial": 0.85, "min": 0.5, "max": 1.2, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected incoming inventory (weighted by pipeline age)
    # More weight to imminent arrivals
    weighted_pipeline = sum(p * (pipeline_weight ** i) for i, p in enumerate(pipeline_orders))

    # Dynamic adjustment based on pipeline and current inventory
    if on_hand_inventory < safety_stock:
        # Low on-hand inventory requires more aggressive ordering
        adjusted_base = base_stock + demand_buffer * 1.5
    elif weighted_pipeline < base_stock * 0.3:
        # Low pipeline coverage requires higher base stock
        adjusted_base = base_stock + safety_stock * 0.8
    else:
        # Normal operation with moderate adjustment
        adjusted_base = base_stock - demand_buffer * 0.5

    # Calculate order amount
    order_amount = max(0, adjusted_base - inventory_position)

    # Apply smoothing with refined bounds
    if order_amount > 0:
        order_amount = max(smoothing_min, min(order_amount, smoothing_max))

    return order_amount
