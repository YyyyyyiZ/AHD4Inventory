# policy_hash: fa4ae61761b951585e888027ff18dd330cfb3c0a5ee9bace2084d596c70f506b
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std30_L4_c1_5
# matched_train_cells: 29
# source_prompt_files: 1
# best_target_performance: 3914.32
# best_prompt_performance: 3914.86
# best_rel_error_pct: 0.013795
# example_source_txt: examples/inventory/deepseek-chat_normal_std30_L4_c1_5_50_plain_processed_scipy_15_default_m2_2_r8/prompt_for_code/m2_20260128_105913.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 52.3810479401248  # OPT_PARAM: {"initial": 52.3810479401248, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 50.0  # OPT_PARAM: {"initial": 50.0, "min": 0, "max": 200, "type": "float"}
    demand_ratio = 0.8  # OPT_PARAM: {"initial": 0.8, "min": 0.1, "max": 2.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Adjust base stock based on pipeline variability
    pipeline_variance = sum((q - sum(pipeline_orders)/len(pipeline_orders))**2 for q in pipeline_orders) / max(len(pipeline_orders), 1)
    pipeline_factor = 1775.0453368424721  # OPT_PARAM: {"initial": 1775.0453368424721, "min": 1000, "max": 50000, "type": "float"}

    # Dynamic base stock adjustment
    adjusted_base = base_stock * pipeline_factor

    # Calculate order-up-to level with safety stock
    order_up_to = max(adjusted_base, safety_stock + demand_ratio * base_stock)

    # Smooth ordering to avoid large fluctuations
    order_amount = 0.11795686272994815  # Optimized

    # Apply smoothing factor to reduce order volatility
    smoothing = 0.9901711410850595  # OPT_PARAM: {"initial": 0.9901711410850595, "min": 0.1, "max": 1.0, "type": "float"}
    if order_amount > 0:
        order_amount = smoothing * order_amount + (1 - smoothing) * max(0, order_up_to * 0.1)  # OPT_PARAM: {"initial": 0.1, "min": 0.01, "max": 0.5, "type": "float"}

    return order_amount
