# policy_hash: 6467f528941e05b024b2be64d22bd466a2df663f6d819e1c3100f8a5c99fa348
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_2
# matched_train_cells: 39
# source_prompt_files: 1
# best_target_performance: 6020.64
# best_prompt_performance: 6020.64
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_055041.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 527.7273066784117  # OPT_PARAM: {"initial": 527.7273066784117, "min": 200, "max": 600, "type": "float"}
    pipeline_weight = 0.5542814722508834  # OPT_PARAM: {"initial": 0.5542814722508834, "min": 0.5, "max": 1.2, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 1.0, "type": "float"}
    safety_stock = 241.53411285587381  # OPT_PARAM: {"initial": 241.53411285587381, "min": 50, "max": 300, "type": "float"}
    demand_anticipation = 0.0  # OPT_PARAM: {"initial": 0.0, "min": 0.0, "max": 0.5, "type": "float"}

    # Calculate effective pipeline
    effective_pipeline = sum(pipeline_orders) * pipeline_weight

    # Calculate inventory position
    inventory_position = on_hand_inventory + effective_pipeline

    # Adjust base stock with safety stock
    adjusted_base = base_stock + safety_stock

    # Calculate target order
    target = max(0, adjusted_base - inventory_position)

    # Apply smoothing
    order_amount = smoothing_factor * target

    # Round to nearest integer
    return order_amount
