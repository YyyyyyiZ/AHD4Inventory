# policy_hash: da31a785bbbad239975e39e36fe8d5220ae5d2d7f3ebe3903e17bbc2bbac5d97
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_2
# matched_train_cells: 3
# source_prompt_files: 1
# best_target_performance: 984.46
# best_prompt_performance: 984.46
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_022915.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 263.3107337672818  # OPT_PARAM: {"initial": 263.3107337672818, "min": 200, "max": 350, "type": "float"}
    safety_stock = 23.410733767278256  # OPT_PARAM: {"initial": 23.410733767278256, "min": 20, "max": 100, "type": "float"}
    demand_forecast = 90.33891553723416  # OPT_PARAM: {"initial": 90.33891553723416, "min": 90, "max": 110, "type": "float"}
    pipeline_weight = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.5, "type": "float"}
    smoothing_factor = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected pipeline coverage
    expected_pipeline = demand_forecast * len(pipeline_orders)
    pipeline_adjustment = max(0, expected_pipeline - sum(pipeline_orders)) * pipeline_weight

    # Dynamic order-up-to level
    order_up_to = base_stock + safety_stock + pipeline_adjustment

    # Calculate order amount
    order_amount = max(0, order_up_to - inventory_position)

    # Apply demand-based smoothing with tighter bounds
    if order_amount > 1.2 * demand_forecast:
        order_amount = smoothing_factor * order_amount + (1 - smoothing_factor) * 1.2 * demand_forecast

    # Round to nearest integer (since order amounts should be integers)
    order_amount = int(round(order_amount))

    return order_amount
