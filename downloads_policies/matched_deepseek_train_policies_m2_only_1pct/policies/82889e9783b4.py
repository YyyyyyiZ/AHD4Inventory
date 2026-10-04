# policy_hash: 82889e9783b451bb19efc2b5ff234f5f1c57e33ae3dfdfefec25be2cebd51e33
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_2
# matched_train_cells: 2
# source_prompt_files: 1
# best_target_performance: 6235.96
# best_prompt_performance: 6235.46
# best_rel_error_pct: 0.008018
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_092612.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 416.21818961796083  # OPT_PARAM: {"initial": 416.21818961796083, "min": 300, "max": 600, "type": "float"}
    pipeline_weight = 0.8891606801010999  # OPT_PARAM: {"initial": 0.8891606801010999, "min": 0.7, "max": 1.0, "type": "float"}
    smoothing_factor = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 1.0, "type": "float"}
    safety_stock = 76.21818961795988  # OPT_PARAM: {"initial": 76.21818961795988, "min": 20, "max": 150, "type": "float"}
    demand_anticipation_factor = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 1.0, "max": 1.5, "type": "float"}

    # Calculate effective pipeline with weighted approach
    effective_pipeline = sum(pipeline_orders) * pipeline_weight

    # Calculate inventory position
    inventory_position = on_hand_inventory + effective_pipeline

    # Adjust base stock based on safety stock and demand anticipation
    adjusted_base_stock = base_stock + safety_stock
    adjusted_base_stock = adjusted_base_stock * demand_anticipation_factor

    # Calculate raw order amount
    raw_order = max(0, adjusted_base_stock - inventory_position)

    # Apply smoothing to avoid extreme fluctuations
    if raw_order > 0:
        order_amount = int(raw_order * smoothing_factor + 0.5)
    else:
        order_amount = 0

    return order_amount
