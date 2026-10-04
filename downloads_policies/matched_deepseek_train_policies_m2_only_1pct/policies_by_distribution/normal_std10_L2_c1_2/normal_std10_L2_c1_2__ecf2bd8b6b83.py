# policy_hash: ecf2bd8b6b836f239c346f63aae8e04f56ba7f6dbd2d897cd40287071d2d299e
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L2_c1_2
# matched_train_cells: 49
# source_prompt_files: 1
# best_target_performance: 695.13
# best_prompt_performance: 695.13
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L2_c1_2_50_plain_processed_scipy_15_default_m2_2_r8/prompt_for_code/m2_20260129_210302.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 304.70354089078864  # OPT_PARAM: {"initial": 304.70354089078864, "min": 290, "max": 330, "type": "float"}
    safety_stock = 45.0  # OPT_PARAM: {"initial": 45.0, "min": 30, "max": 55, "type": "float"}
    demand_buffer = 13.65840642154521  # OPT_PARAM: {"initial": 13.65840642154521, "min": 10, "max": 25, "type": "float"}
    smoothing_min = 5.0  # OPT_PARAM: {"initial": 5.0, "min": 5, "max": 15, "type": "float"}
    smoothing_max = 98.40992183598254  # OPT_PARAM: {"initial": 98.40992183598254, "min": 90, "max": 140, "type": "float"}
    pipeline_weight = 0.9  # OPT_PARAM: {"initial": 0.9, "min": 0.5, "max": 1.2, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected incoming inventory (weighted by pipeline age)
    weighted_pipeline = sum(p * (pipeline_weight ** i) for i, p in enumerate(pipeline_orders))

    # Dynamic adjustment based on pipeline and current inventory
    if on_hand_inventory < safety_stock:
        # Low on-hand inventory requires more aggressive ordering
        adjusted_base = base_stock + demand_buffer * 1.2
    elif weighted_pipeline < base_stock * 0.25:
        # Low pipeline coverage requires higher base stock
        adjusted_base = base_stock + safety_stock * 0.6
    else:
        # Normal operation with moderate adjustment
        adjusted_base = base_stock - demand_buffer * 0.3

    # Calculate order amount
    order_amount = max(0, adjusted_base - inventory_position)

    # Apply smoothing with refined bounds
    if order_amount > 0:
        order_amount = max(smoothing_min, min(order_amount, smoothing_max))

    return order_amount
