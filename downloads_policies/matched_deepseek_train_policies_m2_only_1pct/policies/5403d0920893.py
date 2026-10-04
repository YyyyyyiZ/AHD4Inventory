# policy_hash: 5403d09208933a49bcbeff3d0603397b12d2697d49129f6d79a76fb1d3018a9e
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_2
# matched_train_cells: 2
# source_prompt_files: 1
# best_target_performance: 6770.2
# best_prompt_performance: 6769.2
# best_rel_error_pct: 0.014771
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_091657.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 214.5114727151505  # OPT_PARAM: {"initial": 214.5114727151505, "min": 50, "max": 500, "type": "float"}
    pipeline_weight = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.0, "type": "float"}
    smoothing_factor = 0.4978327615140354  # OPT_PARAM: {"initial": 0.4978327615140354, "min": 0.1, "max": 1.0, "type": "float"}

    # Calculate effective inventory position
    effective_pipeline = sum(pipeline_orders) * pipeline_weight
    inventory_position = on_hand_inventory + effective_pipeline

    # Calculate order amount
    raw_order = max(0, base_stock - inventory_position)

    # Apply smoothing
    if raw_order > 0:
        order_amount = int(raw_order * smoothing_factor + 0.5)
    else:
        order_amount = 0

    return order_amount
