# policy_hash: 451fc0a9ef702980db29776caada2afe6ec97e0dfb15ccde011faffe13a307e4
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_2
# matched_train_cells: 14
# source_prompt_files: 1
# best_target_performance: 6043.52
# best_prompt_performance: 6043.52
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260129_034103.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 352.1138452642395  # OPT_PARAM: {"initial": 352.1138452642395, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 45.1536878216066  # OPT_PARAM: {"initial": 45.1536878216066, "min": 0, "max": 200, "type": "float"}
    pipeline_weight = 0.9660007903822264  # OPT_PARAM: {"initial": 0.9660007903822264, "min": 0.1, "max": 1.5, "type": "float"}

    # Calculate effective inventory position
    effective_pipeline = sum(pipeline_orders) * pipeline_weight
    inventory_position = on_hand_inventory + effective_pipeline

    # Adjust base stock based on safety stock
    adjusted_base_stock = base_stock + safety_stock

    # Calculate order amount
    order_amount = max(0, adjusted_base_stock - inventory_position)

    # Apply smoothing to avoid extreme fluctuations
    smoothing_factor = 0.11346705157152136  # OPT_PARAM: {"initial": 0.11346705157152136, "min": 0.1, "max": 1.0, "type": "float"}
    if len(pipeline_orders) > 0:
        avg_past_order = sum(pipeline_orders) / len(pipeline_orders)
        smoothed_order = smoothing_factor * order_amount + (1 - smoothing_factor) * avg_past_order
        order_amount = max(0, smoothed_order)

    # Round to integer (as required by output type)
    return order_amount
