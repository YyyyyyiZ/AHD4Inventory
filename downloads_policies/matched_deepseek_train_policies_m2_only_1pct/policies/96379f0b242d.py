# policy_hash: 96379f0b242db8c02c8cb120ce3d3f9f631a6b0dd028e968a60dc7103e1a8012
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_5
# matched_train_cells: 25
# source_prompt_files: 1
# best_target_performance: 11255.94
# best_prompt_performance: 11255.94
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_084752.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 457.1853528412109  # OPT_PARAM: {"initial": 457.1853528412109, "min": 100, "max": 800, "type": "float"}
    pipeline_weight = 0.595183775181743  # OPT_PARAM: {"initial": 0.595183775181743, "min": 0.5, "max": 1.0, "type": "float"}
    smoothing_factor = 0.3497240151993954  # OPT_PARAM: {"initial": 0.3497240151993954, "min": 0.1, "max": 0.5, "type": "float"}

    # Calculate effective inventory position
    effective_pipeline = pipeline_weight * sum(pipeline_orders)
    inventory_position = on_hand_inventory + effective_pipeline

    # Calculate order amount
    order_amount = max(0, base_stock - inventory_position)

    # Apply smoothing
    order_amount = smoothing_factor * order_amount

    return order_amount
