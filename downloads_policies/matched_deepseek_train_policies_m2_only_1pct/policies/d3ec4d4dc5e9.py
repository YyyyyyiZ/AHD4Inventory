# policy_hash: d3ec4d4dc5e931122005e8809b57e0b036ca3fbbab058c72dcd688afb336e12e
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_2
# matched_train_cells: 4
# source_prompt_files: 1
# best_target_performance: 6508.66
# best_prompt_performance: 6508.66
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_012633.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 450.0000465117967  # OPT_PARAM: {"initial": 450.0000465117967, "min": 100, "max": 800, "type": "float"}
    pipeline_coverage = 1.2  # OPT_PARAM: {"initial": 1.2, "min": 0.8, "max": 1.2, "type": "float"}
    smoothing_factor = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.0, "type": "float"}

    # Calculate inventory position including all pipeline orders
    inventory_position = on_hand_inventory + sum(pipeline_orders) * pipeline_coverage

    # Calculate order amount based on base stock policy
    order_amount = max(0, base_stock - inventory_position)

    # Apply smoothing to avoid extreme fluctuations
    order_amount = order_amount * smoothing_factor

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
