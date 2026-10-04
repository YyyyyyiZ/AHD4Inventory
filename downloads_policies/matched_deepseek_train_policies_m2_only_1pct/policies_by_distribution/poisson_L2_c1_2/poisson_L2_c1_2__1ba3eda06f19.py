# policy_hash: 1ba3eda06f195d00d5ae99779062738ab85f62a44adb3321e4c3487de0101e7e
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_2
# matched_train_cells: 10
# source_prompt_files: 1
# best_target_performance: 719.66
# best_prompt_performance: 719.66
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_224737.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 283.40000000000435  # OPT_PARAM: {"initial": 283.40000000000435, "min": 280, "max": 340, "type": "float"}
    safety_stock = 20.0  # OPT_PARAM: {"initial": 20.0, "min": 20, "max": 35, "type": "float"}
    demand_forecast = 96.0  # OPT_PARAM: {"initial": 96.0, "min": 96, "max": 102, "type": "float"}
    smoothing_factor = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.3, "type": "float"}
    pipeline_weight = 0.8  # OPT_PARAM: {"initial": 0.8, "min": 0.5, "max": 1.0, "type": "float"}

    # Calculate effective inventory position with weighted pipeline
    weighted_pipeline = sum(p * (pipeline_weight ** i) for i, p in enumerate(pipeline_orders))
    inventory_position = on_hand_inventory + weighted_pipeline

    # Dynamic order-up-to level based on pipeline composition
    pipeline_ratio = sum(pipeline_orders) / (len(pipeline_orders) * demand_forecast + 1e-6)
    dynamic_adjustment = safety_stock * (1.0 + 0.5 * (1.0 - pipeline_ratio))
    order_up_to = base_stock + dynamic_adjustment

    # Calculate raw order amount
    raw_order = max(0, order_up_to - inventory_position)

    # Apply smoothing with demand forecast consideration
    if raw_order > demand_forecast * 1.5:
        smoothing_factor_adjusted = smoothing_factor * 0.7
    else:
        smoothing_factor_adjusted = smoothing_factor

    smoothed_order = smoothing_factor_adjusted * raw_order + (1 - smoothing_factor_adjusted) * demand_forecast

    # Ensure order doesn't drop below minimum forecast
    if smoothed_order < demand_forecast * 0.7:
        smoothed_order = demand_forecast * 0.7

    # Round to nearest integer
    order_amount = int(round(smoothed_order))

    return order_amount
