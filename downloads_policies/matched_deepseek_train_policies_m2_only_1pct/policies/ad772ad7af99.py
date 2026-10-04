# policy_hash: ad772ad7af9900ead0b4524e7a19207957dcb3763ac9cfa6f31b08ce46036926
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_2
# matched_train_cells: 1
# source_prompt_files: 1
# best_target_performance: 962.22
# best_prompt_performance: 962.21
# best_rel_error_pct: 0.001039
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_023450.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 239.98035060530455  # OPT_PARAM: {"initial": 239.98035060530455, "min": 150, "max": 300, "type": "float"}
    safety_stock = 54.980350605303535  # OPT_PARAM: {"initial": 54.980350605303535, "min": 20, "max": 100, "type": "float"}
    demand_forecast = 104.64671280876759  # OPT_PARAM: {"initial": 104.64671280876759, "min": 80, "max": 120, "type": "float"}
    pipeline_weight = 0.0  # OPT_PARAM: {"initial": 0.0, "min": 0.0, "max": 0.5, "type": "float"}
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

    # Apply demand-based smoothing
    if order_amount > 1.5 * demand_forecast:
        order_amount = smoothing_factor * order_amount + (1 - smoothing_factor) * 1.5 * demand_forecast

    return order_amount
