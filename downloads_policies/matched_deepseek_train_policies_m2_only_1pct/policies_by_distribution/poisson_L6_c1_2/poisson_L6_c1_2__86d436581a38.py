# policy_hash: 86d436581a386f5655b1096b536eefe92b79608e9867f6a17ad000f3bb094719
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_2
# matched_train_cells: 2
# source_prompt_files: 2
# best_target_performance: 2238.72
# best_prompt_performance: 2237.9
# best_rel_error_pct: 0.036628
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_091142.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 602.3114954439652  # OPT_PARAM: {"initial": 602.3114954439652, "min": 400, "max": 900, "type": "float"}
    safety_stock = 56.923699175004664  # OPT_PARAM: {"initial": 56.923699175004664, "min": 50, "max": 200, "type": "float"}
    demand_forecast = 88.38414196456553  # OPT_PARAM: {"initial": 88.38414196456553, "min": 80, "max": 120, "type": "float"}
    pipeline_weight = 0.783217856551259  # OPT_PARAM: {"initial": 0.783217856551259, "min": 0.5, "max": 1.0, "type": "float"}
    adjustment_factor = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 1.0, "type": "float"}
    reorder_threshold = 116.30957266095369  # OPT_PARAM: {"initial": 116.30957266095369, "min": 50, "max": 200, "type": "float"}

    # Calculate effective inventory position
    full_pipeline = sum(pipeline_orders)
    effective_pipeline = full_pipeline * pipeline_weight
    inventory_position = on_hand_inventory + effective_pipeline

    # Calculate target inventory level
    target_inventory = base_stock + safety_stock

    # Calculate deficit from target
    deficit = target_inventory - inventory_position

    # Determine order amount with more aggressive replenishment
    if deficit > reorder_threshold:
        # When significantly below target, order more aggressively
        order_target = max(0, deficit + demand_forecast * 1.2)
    else:
        # When close to target, maintain normal ordering
        order_target = max(0, deficit + demand_forecast)

    # Apply adjustment factor for smoothing
    order_amount = max(0, order_target * adjustment_factor)

    # Round to nearest integer
    return order_amount
