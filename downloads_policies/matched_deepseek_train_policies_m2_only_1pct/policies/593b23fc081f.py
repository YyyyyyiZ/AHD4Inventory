# policy_hash: 593b23fc081f0781deefcedd5015f1ec3448a8989d350d8b339f01b5bb650798
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_5
# matched_train_cells: 8
# source_prompt_files: 1
# best_target_performance: 1973.84
# best_prompt_performance: 1973.84
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_082704.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 509.0311864287618  # OPT_PARAM: {"initial": 509.0311864287618, "min": 400, "max": 650, "type": "float"}
    demand_forecast = 91.67092631868249  # OPT_PARAM: {"initial": 91.67092631868249, "min": 90, "max": 110, "type": "float"}
    smoothing_factor = 0.2  # OPT_PARAM: {"initial": 0.2, "min": 0.2, "max": 0.5, "type": "float"}
    safety_stock_multiplier = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 1.0, "max": 2.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected shortfall
    expected_shortfall = max(0, base_stock - inventory_position)

    # Calculate safety stock adjustment based on pipeline variability
    pipeline_std = 0.0
    if len(pipeline_orders) > 1:
        mean_pipeline = sum(pipeline_orders) / len(pipeline_orders)
        pipeline_std = (sum((q - mean_pipeline) ** 2 for q in pipeline_orders) / len(pipeline_orders)) ** 0.5

    safety_adjustment = safety_stock_multiplier * pipeline_std

    # Smooth adjustment with safety stock consideration
    smoothed_order = smoothing_factor * (expected_shortfall + safety_adjustment) + (1 - smoothing_factor) * demand_forecast

    # Ensure non-negative order
    order_amount = max(0, round(smoothed_order))

    return order_amount
