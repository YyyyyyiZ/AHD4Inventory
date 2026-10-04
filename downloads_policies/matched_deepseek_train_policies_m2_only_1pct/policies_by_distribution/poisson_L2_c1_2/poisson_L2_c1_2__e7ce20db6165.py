# policy_hash: e7ce20db61657eb35272bf0fe08de7c61311ac5f369d540b2cd301400baf0043
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_2
# matched_train_cells: 2
# source_prompt_files: 1
# best_target_performance: 983.13
# best_prompt_performance: 983.12
# best_rel_error_pct: 0.001017
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_023029.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 241.8047494878228  # OPT_PARAM: {"initial": 241.8047494878228, "min": 200, "max": 400, "type": "float"}
    safety_stock = 52.1129641601368  # OPT_PARAM: {"initial": 52.1129641601368, "min": 50, "max": 200, "type": "float"}
    demand_forecast = 80.0  # OPT_PARAM: {"initial": 80.0, "min": 80, "max": 120, "type": "float"}
    pipeline_weight = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected pipeline coverage
    expected_pipeline = demand_forecast * len(pipeline_orders)
    pipeline_adjustment = max(0, expected_pipeline - sum(pipeline_orders)) * pipeline_weight

    # Dynamic order-up-to level
    order_up_to = base_stock + safety_stock + pipeline_adjustment

    # Calculate order amount
    order_amount = max(0, order_up_to - inventory_position)

    # Apply demand-based smoothing
    smoothing_factor = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.0, "type": "float"}
    if order_amount > 1.5 * demand_forecast:
        order_amount = smoothing_factor * order_amount + (1 - smoothing_factor) * 1.5 * demand_forecast

    return order_amount
