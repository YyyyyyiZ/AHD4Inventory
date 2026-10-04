# policy_hash: a66001e34119f0809891d39036649011b0643e984221e700cb1f038bec75baf1
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_2
# matched_train_cells: 7
# source_prompt_files: 1
# best_target_performance: 2624.28
# best_prompt_performance: 2623.02
# best_rel_error_pct: 0.048013
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251222_015840.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 621.5767275851837  # OPT_PARAM: {"initial": 621.5767275851837, "min": 550, "max": 700, "type": "float"}
    safety_stock = 48.5485942167385  # OPT_PARAM: {"initial": 48.5485942167385, "min": 30, "max": 60, "type": "float"}
    pipeline_adjustment = 1.073704002351719  # OPT_PARAM: {"initial": 1.073704002351719, "min": 0.95, "max": 1.15, "type": "float"}
    smoothing_factor = 0.8471682322201138  # OPT_PARAM: {"initial": 0.8471682322201138, "min": 0.6, "max": 1.0, "type": "float"}
    demand_buffer = 18.5485942167385  # OPT_PARAM: {"initial": 18.5485942167385, "min": 5, "max": 30, "type": "float"}

    # Calculate effective pipeline with adjustment
    effective_pipeline = sum(pipeline_orders) * pipeline_adjustment

    # Calculate target inventory position with demand buffer
    target_inventory = base_stock + safety_stock + demand_buffer

    # Calculate inventory position
    inventory_position = on_hand_inventory + effective_pipeline

    # Calculate raw order amount
    raw_order = max(0, target_inventory - inventory_position)

    # Apply smoothing with higher factor for more responsiveness
    order_amount = int(round(smoothing_factor * raw_order))

    return order_amount
