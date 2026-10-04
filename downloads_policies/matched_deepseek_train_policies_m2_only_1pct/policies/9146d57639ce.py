# policy_hash: 9146d57639ce420b08d0905cac39739312a5bd5b0f377a201697e873b1403963
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L6_c1_5
# matched_train_cells: 17
# source_prompt_files: 1
# best_target_performance: 1475.29
# best_prompt_performance: 1472.92
# best_rel_error_pct: 0.160646
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260129_205012.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 561.3975684787923  # OPT_PARAM: {"initial": 561.3975684787923, "min": 550, "max": 700, "type": "float"}
    safety_stock = 15.0  # OPT_PARAM: {"initial": 15.0, "min": 15, "max": 40, "type": "float"}
    demand_forecast = 96.26318123858812  # OPT_PARAM: {"initial": 96.26318123858812, "min": 95, "max": 105, "type": "float"}
    smoothing_factor = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.3, "type": "float"}
    pipeline_weight = 0.7582811575034395  # OPT_PARAM: {"initial": 0.7582811575034395, "min": 0.5, "max": 1.0, "type": "float"}
    lost_sales_weight = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 1.0, "max": 1.5, "type": "float"}

    # Calculate inventory position with full pipeline consideration
    weighted_pipeline = sum(pipeline_orders) * pipeline_weight
    inventory_position = on_hand_inventory + weighted_pipeline

    # Adjust base stock based on lost sales risk
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
