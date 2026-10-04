# policy_hash: 3556667ac517965afa5dd370333df782589658a5ca7d80dfc1fc30cdebbb4c8a
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_5
# matched_train_cells: 33
# source_prompt_files: 1
# best_target_performance: 1313.9
# best_prompt_performance: 1313.9
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_083942.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 457.87589526072935  # OPT_PARAM: {"initial": 457.87589526072935, "min": 400, "max": 550, "type": "float"}
    demand_forecast = 98.26717283074773  # OPT_PARAM: {"initial": 98.26717283074773, "min": 95, "max": 105, "type": "float"}
    smoothing_factor = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.3, "type": "float"}
    safety_stock = 15.0  # OPT_PARAM: {"initial": 15.0, "min": 15, "max": 60, "type": "float"}
    pipeline_weight = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.8, "max": 1.0, "type": "float"}
    reorder_point = 450.0  # OPT_PARAM: {"initial": 450.0, "min": 350, "max": 500, "type": "float"}

    # Calculate total pipeline inventory (unweighted)
    total_pipeline = sum(pipeline_orders)

    # Calculate inventory position
    inventory_position = on_hand_inventory + total_pipeline

    # Calculate target inventory level
    target_inventory = base_stock + safety_stock

    # Calculate order-up-to level
    order_up_to = max(target_inventory, reorder_point)

    # Calculate required order to reach order-up-to level
    required_order = max(0, order_up_to - inventory_position)

    # Apply smoothing with demand forecast
    if required_order > 0:
        smoothed_order = smoothing_factor * required_order + (1 - smoothing_factor) * demand_forecast
    else:
        smoothed_order = 0

    # Round to nearest integer and ensure non-negative
    order_amount = max(0, round(smoothed_order))

    return order_amount
