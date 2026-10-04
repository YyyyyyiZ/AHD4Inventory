# policy_hash: 6bd59b9781fe66f8695fdf70e5584c2db311a296434cfa4e30b94f32f9b9673d
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_2
# matched_train_cells: 6
# source_prompt_files: 1
# best_target_performance: 803.7
# best_prompt_performance: 803.7
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_041021.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 394.2578371783297  # OPT_PARAM: {"initial": 394.2578371783297, "min": 380, "max": 460, "type": "float"}
    safety_stock = 50.0  # OPT_PARAM: {"initial": 50.0, "min": 50, "max": 100, "type": "float"}
    demand_estimate = 93.17166112620474  # OPT_PARAM: {"initial": 93.17166112620474, "min": 90, "max": 110, "type": "float"}
    smoothing_factor = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.25, "type": "float"}
    pipeline_weight = 0.8  # OPT_PARAM: {"initial": 0.8, "min": 0.8, "max": 1.0, "type": "float"}
    lost_sales_weight = 1.2915061044326857  # OPT_PARAM: {"initial": 1.2915061044326857, "min": 1.0, "max": 1.4, "type": "float"}
    cost_ratio_adjust = 0.8  # OPT_PARAM: {"initial": 0.8, "min": 0.4, "max": 0.8, "type": "float"}
    threshold_factor = 0.6  # OPT_PARAM: {"initial": 0.6, "min": 0.5, "max": 0.9, "type": "float"}

    # Calculate inventory position with weighted pipeline
    inventory_position = on_hand_inventory + sum(pipeline_orders) * pipeline_weight

    # Adjust safety stock based on cost ratio (p=2, h=1)
    adjusted_safety = safety_stock * lost_sales_weight

    # Calculate target inventory position
    target_inventory = base_stock + adjusted_safety * cost_ratio_adjust

    # Calculate order amount
    order_amount = max(0, target_inventory - inventory_position)

    # Apply smoothing
    smoothed_order = smoothing_factor * order_amount + (1 - smoothing_factor) * demand_estimate

    # Ensure minimum order when inventory is low
    if inventory_position < target_inventory * threshold_factor:
        smoothed_order = max(smoothed_order, demand_estimate)

    # Round to nearest integer
    order_amount = int(round(smoothed_order))

    return order_amount
