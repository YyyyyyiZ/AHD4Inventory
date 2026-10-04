# policy_hash: 9b7eec6f951fd4e11fa71e5e3b4049851d031674d9321dcbca1a64a565f08121
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L6_c1_2
# matched_train_cells: 12
# source_prompt_files: 1
# best_target_performance: 712.28
# best_prompt_performance: 712.28
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L6_c1_2_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260128_040318.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 612.7662029715867  # OPT_PARAM: {"initial": 612.7662029715867, "min": 450, "max": 650, "type": "float"}
    safety_stock = 40.0  # OPT_PARAM: {"initial": 40.0, "min": 15, "max": 40, "type": "float"}
    demand_forecast = 96.50683339336582  # OPT_PARAM: {"initial": 96.50683339336582, "min": 95, "max": 105, "type": "float"}
    pipeline_weight = 0.95  # OPT_PARAM: {"initial": 0.95, "min": 0.95, "max": 1.05, "type": "float"}
    order_multiplier = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 1.0, "max": 1.5, "type": "float"}
    smoothing_factor = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 0.9, "type": "float"}

    # Calculate total pipeline inventory
    total_pipeline = sum(pipeline_orders) * pipeline_weight

    # Calculate inventory position
    inventory_position = on_hand_inventory + total_pipeline

    # Calculate target inventory position
    target_position = base_stock + safety_stock

    # Calculate order needed to reach target
    order_needed = max(0, target_position - inventory_position)

    # Apply smoothing and forecast adjustment
    if order_needed > 0:
        # Blend between order_needed and forecast-based order
        smoothed_order = order_needed * smoothing_factor + demand_forecast * (1 - smoothing_factor)
        # Apply multiplier to forecast component
        order_amount = min(smoothed_order, demand_forecast * order_multiplier)
    else:
        order_amount = 0

    # Ensure integer output
    return order_amount
