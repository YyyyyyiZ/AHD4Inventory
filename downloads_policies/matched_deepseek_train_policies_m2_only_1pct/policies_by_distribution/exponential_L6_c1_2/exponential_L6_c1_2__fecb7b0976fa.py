# policy_hash: fecb7b0976fa93afe95fd672d74bcfee901e51613cadb6fb666de7ae25b0afbb
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_2
# matched_train_cells: 6
# source_prompt_files: 1
# best_target_performance: 6287.7
# best_prompt_performance: 6287.7
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_052752.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 358.72455946132413  # OPT_PARAM: {"initial": 358.72455946132413, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 49.61031318423847  # OPT_PARAM: {"initial": 49.61031318423847, "min": 0, "max": 200, "type": "float"}
    pipeline_weight = 0.4318148726308386  # OPT_PARAM: {"initial": 0.4318148726308386, "min": 0.1, "max": 1.5, "type": "float"}

    # Calculate effective inventory position
    effective_pipeline = pipeline_weight * sum(pipeline_orders)
    inventory_position = on_hand_inventory + effective_pipeline

    # Adjust base stock based on pipeline composition
    oldest_order_ratio = pipeline_orders[0] / (sum(pipeline_orders) + 1e-6) if sum(pipeline_orders) > 0 else 0
    adjusted_base = 0.11912185729619842  # OPT_PARAM: {"initial": 0.11912185729619842, "min": 0, "max": 0.5, "type": "float"}

    # Calculate order amount with safety stock buffer
    target_inventory = adjusted_base + safety_stock
    order_amount = max(0, target_inventory - inventory_position)

    # Apply smoothing to avoid extreme order sizes
    smoothing_factor = 0.6921885123890188  # OPT_PARAM: {"initial": 0.6921885123890188, "min": 0.3, "max": 1.0, "type": "float"}
    order_amount = smoothing_factor * order_amount + (1 - smoothing_factor) * max(0, base_stock - inventory_position)

    # Round to nearest integer (as required by output type)
    return order_amount
