# policy_hash: 8dabbe12a2887421a085832bf2c2008950e16c3c9941acea819536292cb4cb11
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_2
# matched_train_cells: 8
# source_prompt_files: 1
# best_target_performance: 6111.18
# best_prompt_performance: 6111.18
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_094048.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 432.7996707300752  # OPT_PARAM: {"initial": 432.7996707300752, "min": 350, "max": 550, "type": "float"}
    pipeline_weight = 0.8  # OPT_PARAM: {"initial": 0.8, "min": 0.8, "max": 1.0, "type": "float"}
    smoothing_factor = 0.2  # OPT_PARAM: {"initial": 0.2, "min": 0.2, "max": 0.8, "type": "float"}
    safety_stock = 30.0  # OPT_PARAM: {"initial": 30.0, "min": 30, "max": 80, "type": "float"}
    demand_anticipation_factor = 1.2  # OPT_PARAM: {"initial": 1.2, "min": 1.0, "max": 1.2, "type": "float"}

    # Calculate total pipeline (simple sum)
    total_pipeline = sum(pipeline_orders)

    # Effective pipeline with weight
    effective_pipeline = total_pipeline * pipeline_weight

    # Inventory position
    inventory_position = on_hand_inventory + effective_pipeline

    # Adjusted base stock
    adjusted_base_stock = (base_stock + safety_stock) * demand_anticipation_factor

    # Order quantity
    raw_order = max(0, adjusted_base_stock - inventory_position)

    # Apply smoothing
    if raw_order > 0:
        order_amount = int(raw_order * smoothing_factor + 0.5)
    else:
        order_amount = 0

    return order_amount
