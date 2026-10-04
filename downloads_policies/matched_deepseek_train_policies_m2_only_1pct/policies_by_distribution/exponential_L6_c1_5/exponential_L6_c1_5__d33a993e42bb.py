# policy_hash: d33a993e42bbc4df3054172c876ae81f59311163f66d354c9e0b4cd49fa1ed57
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_5
# matched_train_cells: 7
# source_prompt_files: 1
# best_target_performance: 12461.91
# best_prompt_performance: 12461.21
# best_rel_error_pct: 0.005617
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_101605.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 375.0830338097578  # OPT_PARAM: {"initial": 375.0830338097578, "min": 100, "max": 800, "type": "float"}
    safety_stock = 65.08303380975555  # OPT_PARAM: {"initial": 65.08303380975555, "min": 20, "max": 200, "type": "float"}
    demand_estimate = 94.86916630713249  # OPT_PARAM: {"initial": 94.86916630713249, "min": 50, "max": 300, "type": "float"}
    pipeline_weight = 0.0  # OPT_PARAM: {"initial": 0.0, "min": 0.0, "max": 0.8, "type": "float"}
    recent_weight = 0.28401810197258776  # OPT_PARAM: {"initial": 0.28401810197258776, "min": 0.0, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate effective pipeline coverage
    total_pipeline = sum(pipeline_orders)
    recent_pipeline = sum(pipeline_orders[:3])  # Next 3 periods' arrivals

    # Dynamic adjustment based on pipeline
    pipeline_adjustment = pipeline_weight * total_pipeline
    recent_adjustment = recent_weight * recent_pipeline

    # Calculate target inventory position
    target_position = base_stock + safety_stock - pipeline_adjustment + recent_adjustment

    # Calculate order amount
    order_amount = max(0, target_position - inventory_position)

    # Apply demand-based minimum order
    min_order = max(0, demand_estimate - pipeline_orders[-1] if pipeline_orders else demand_estimate)
    order_amount = max(order_amount, min_order)

    return order_amount
