# policy_hash: d6ced09ffc807b811ebe10947c09d4053511747064448556028dc0fc2a173606
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_2
# matched_train_cells: 1
# source_prompt_files: 1
# best_target_performance: 1646.41
# best_prompt_performance: 1646.41
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_074007.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 421.9380363419706  # OPT_PARAM: {"initial": 421.9380363419706, "min": 350, "max": 500, "type": "float"}
    safety_stock = 76.55175995392845  # OPT_PARAM: {"initial": 76.55175995392845, "min": 40, "max": 120, "type": "float"}
    pipeline_coef = 0.7  # OPT_PARAM: {"initial": 0.7, "min": 0.7, "max": 1.0, "type": "float"}
    demand_buffer = 1.3  # OPT_PARAM: {"initial": 1.3, "min": 1.0, "max": 1.3, "type": "float"}
    pipeline_weight = 0.4  # OPT_PARAM: {"initial": 0.4, "min": 0.4, "max": 0.8, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate weighted pipeline to avoid over-ordering
    weighted_pipeline = pipeline_weight * sum(pipeline_orders)

    # Adjust base stock based on demand buffer
    adjusted_base = base_stock * demand_buffer

    # Calculate target with safety stock and pipeline consideration
    target_level = adjusted_base + safety_stock - weighted_pipeline

    # Calculate order amount
    order_amount = max(0, target_level - inventory_position)

    # Apply smoothing coefficient
    order_amount = pipeline_coef * order_amount

    # Round to nearest integer
    return order_amount
