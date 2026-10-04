# policy_hash: 272f87876f5085d32ee7fa88beaeea0136f2723b45c18c31e7976ae30ade2859
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_2
# matched_train_cells: 6
# source_prompt_files: 1
# best_target_performance: 6038.08
# best_prompt_performance: 6038.08
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260129_034723.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 280.0293122586163  # OPT_PARAM: {"initial": 280.0293122586163, "min": 150, "max": 400, "type": "float"}
    pipeline_weight = 0.9908799707055449  # OPT_PARAM: {"initial": 0.9908799707055449, "min": 0.8, "max": 1.0, "type": "float"}
    demand_buffer = 1.2862442036719062  # OPT_PARAM: {"initial": 1.2862442036719062, "min": 1.1, "max": 1.6, "type": "float"}
    smoothing_factor = 0.14013118021009505  # OPT_PARAM: {"initial": 0.14013118021009505, "min": 0.1, "max": 0.4, "type": "float"}
    safety_stock = 46.319476066930655  # OPT_PARAM: {"initial": 46.319476066930655, "min": 20, "max": 100, "type": "float"}

    # Calculate effective inventory position
    weighted_pipeline = sum(pipeline_orders) * pipeline_weight
    inventory_position = on_hand_inventory + weighted_pipeline

    # Calculate target inventory level with safety stock
    target_inventory = base_stock * demand_buffer + safety_stock

    # Base order amount
    order_amount = max(0, target_inventory - inventory_position)

    # Apply moderate smoothing
    if len(pipeline_orders) > 0:
        avg_pipeline = sum(pipeline_orders) / len(pipeline_orders)
        smoothed_order = smoothing_factor * order_amount + (1 - smoothing_factor) * avg_pipeline
        order_amount = max(0, smoothed_order)

    # Round to nearest integer
    return order_amount
