# policy_hash: 67cb7d969072e614d422180e029bc4eac6af4580e77dcc3e69abe634f4f3d675
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_2
# matched_train_cells: 8
# source_prompt_files: 1
# best_target_performance: 6312.54
# best_prompt_performance: 6312.54
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_023523.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 207.00001640733515  # OPT_PARAM: {"initial": 207.00001640733515, "min": 100, "max": 500, "type": "float"}
    safety_stock = 20.0  # OPT_PARAM: {"initial": 20.0, "min": 20, "max": 200, "type": "float"}
    pipeline_weight = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.3, "max": 1.0, "type": "float"}

    # Calculate effective inventory position
    effective_pipeline = pipeline_weight * sum(pipeline_orders)
    inventory_position = on_hand_inventory + effective_pipeline

    # Adjust base stock based on pipeline status
    if pipeline_orders[0] > 0:  # Arriving order this period
        adjusted_base = base_stock
    else:
        adjusted_base = base_stock + safety_stock

    # Calculate order amount
    order_amount = max(0, adjusted_base - inventory_position)

    # Round to integer for practical ordering
    return order_amount
