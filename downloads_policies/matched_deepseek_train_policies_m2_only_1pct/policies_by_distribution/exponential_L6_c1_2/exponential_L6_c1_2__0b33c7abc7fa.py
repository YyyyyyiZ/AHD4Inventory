# policy_hash: 0b33c7abc7faef420ef5c39f18c2020de4cfa63487652855f8646a4067439e87
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_2
# matched_train_cells: 2
# source_prompt_files: 1
# best_target_performance: 6112.22
# best_prompt_performance: 6112.22
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_093106.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 452.95892093109654  # OPT_PARAM: {"initial": 452.95892093109654, "min": 300, "max": 600, "type": "float"}
    pipeline_weight = 0.6472464706774573  # OPT_PARAM: {"initial": 0.6472464706774573, "min": 0.5, "max": 1.0, "type": "float"}
    smoothing_factor = 0.2  # OPT_PARAM: {"initial": 0.2, "min": 0.1, "max": 0.5, "type": "float"}
    safety_stock = 82.95892093109805  # OPT_PARAM: {"initial": 82.95892093109805, "min": 50, "max": 150, "type": "float"}

    # Calculate inventory position with full pipeline consideration
    effective_pipeline = sum(pipeline_orders) * pipeline_weight
    inventory_position = on_hand_inventory + effective_pipeline

    # Calculate target inventory level
    target_inventory = base_stock + safety_stock

    # Calculate order amount
    raw_order = max(0, target_inventory - inventory_position)

    # Apply smoothing
    if raw_order > 0:
        order_amount = int(raw_order * smoothing_factor + 0.5)
    else:
        order_amount = 0

    return order_amount
