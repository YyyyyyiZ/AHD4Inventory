# policy_hash: d13b15b97c1fd92af3550eb80ec7b529369c1fb65772a0a2c1d0bca4b9687f20
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_5
# matched_train_cells: 12
# source_prompt_files: 2
# best_target_performance: 11167.0
# best_prompt_performance: 11167.0
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_044500.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 397.1903966943214  # OPT_PARAM: {"initial": 397.1903966943214, "min": 200, "max": 600, "type": "float"}
    safety_stock = 101.89039669432618  # OPT_PARAM: {"initial": 101.89039669432618, "min": 20, "max": 200, "type": "float"}
    demand_smoothing = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.3, "max": 1.0, "type": "float"}
    order_smoothing = 0.30000000000000004  # OPT_PARAM: {"initial": 0.30000000000000004, "min": 0.2, "max": 0.8, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Simple demand forecast using recent pipeline arrivals
    if len(pipeline_orders) > 0:
        # Use weighted average with more weight on recent orders
        weights = [0.6, 0.3, 0.1][:len(pipeline_orders)]
        weights = [w/sum(weights) for w in weights]  # Normalize
        forecast = sum(w * d for w, d in zip(weights, pipeline_orders))
        forecast = forecast * demand_smoothing
    else:
        forecast = 0

    # Target inventory level with forecast adjustment
    target_inventory = base_stock + safety_stock + forecast

    # Calculate order needed
    order_needed = max(0, target_inventory - inventory_position)

    # Apply order smoothing
    if order_needed > 0:
        order_amount = order_needed * order_smoothing
    else:
        order_amount = 0

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
