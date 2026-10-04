# policy_hash: 795209d13976f2bc02f2527ab5fc4dab68588cd9e067983dfff76a2dde9ddd37
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L6_c1_5
# matched_train_cells: 10
# source_prompt_files: 1
# best_target_performance: 1524.78
# best_prompt_performance: 1524.48
# best_rel_error_pct: 0.019675
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260129_203921.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 601.3999999926606  # OPT_PARAM: {"initial": 601.3999999926606, "min": 550, "max": 700, "type": "float"}
    safety_stock = 15.0  # OPT_PARAM: {"initial": 15.0, "min": 15, "max": 40, "type": "float"}
    demand_forecast = 95.0  # OPT_PARAM: {"initial": 95.0, "min": 95, "max": 105, "type": "float"}
    smoothing_factor = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.3, "type": "float"}
    pipeline_weight = 0.9  # OPT_PARAM: {"initial": 0.9, "min": 0.5, "max": 1.0, "type": "float"}
    lost_sales_weight = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 1.0, "max": 1.5, "type": "float"}

    # Calculate inventory position with weighted pipeline
    weighted_pipeline = sum(p * (pipeline_weight ** i) for i, p in enumerate(pipeline_orders))
    inventory_position = on_hand_inventory + weighted_pipeline

    # Adjust base stock based on lost sales risk (higher p/h ratio)
    adjusted_base = base_stock * lost_sales_weight

    # Calculate order-up-to level
    order_up_to = adjusted_base + safety_stock - inventory_position

    # Apply smoothing with demand forecast adjustment
    if order_up_to > 0:
        smoothed_order = smoothing_factor * order_up_to + (1 - smoothing_factor) * demand_forecast
    else:
        smoothed_order = 0

    # Round to nearest integer and ensure non-negative
    order_amount = max(0, int(round(smoothed_order)))

    return order_amount
