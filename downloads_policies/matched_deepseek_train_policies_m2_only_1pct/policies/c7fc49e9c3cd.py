# policy_hash: c7fc49e9c3cd5947fb744de73fd84d3afefe5aa4120eeb1f7c7f11ee800eb3d0
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_5
# matched_train_cells: 4
# source_prompt_files: 1
# best_target_performance: 11326.49
# best_prompt_performance: 11326.49
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_022653.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 412.86986225529364  # OPT_PARAM: {"initial": 412.86986225529364, "min": 300, "max": 450, "type": "float"}
    safety_stock = 152.86986225312867  # OPT_PARAM: {"initial": 152.86986225312867, "min": 80, "max": 180, "type": "float"}
    pipeline_coverage = 0.7999999999999999  # OPT_PARAM: {"initial": 0.7999999999999999, "min": 0.7, "max": 1.0, "type": "float"}
    demand_estimate = 90.0  # OPT_PARAM: {"initial": 90.0, "min": 90, "max": 140, "type": "float"}
    order_multiplier = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 1.0, "max": 1.8, "type": "float"}
    min_order_threshold = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.5, "type": "float"}

    # Calculate effective pipeline coverage
    effective_pipeline = sum(pipeline_orders) * pipeline_coverage

    # Current inventory position
    inventory_position = on_hand_inventory + effective_pipeline

    # Target inventory level
    target_inventory = base_stock + safety_stock

    # Order up to target
    order_amount = max(0, target_inventory - inventory_position)

    # Apply reasonable order size based on demand estimate
    if order_amount > 0:
        # Only place orders when significant gap exists
        if order_amount < demand_estimate * min_order_threshold:
            order_amount = 0
        else:
            order_amount = min(order_amount, demand_estimate * order_multiplier)

    # Round to nearest integer
    return order_amount
