# policy_hash: 8929cd6cf0ae28bf4090cc1ea747e4861618e8eac9b18632eaebfa71f439161e
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_2
# matched_train_cells: 13
# source_prompt_files: 1
# best_target_performance: 1005.56
# best_prompt_performance: 1004.28
# best_rel_error_pct: 0.127292
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_001931.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 512.5325718909365  # OPT_PARAM: {"initial": 512.5325718909365, "min": 450, "max": 600, "type": "float"}
    safety_stock = 30.838684817175107  # OPT_PARAM: {"initial": 30.838684817175107, "min": 20, "max": 50, "type": "float"}
    demand_forecast = 96.24142779328663  # OPT_PARAM: {"initial": 96.24142779328663, "min": 95, "max": 105, "type": "float"}
    pipeline_weight = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.5, "max": 1.0, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.5, "type": "float"}
    lost_sales_weight = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 1.0, "max": 2.0, "type": "float"}
    threshold_factor = 0.6910010205080951  # OPT_PARAM: {"initial": 0.6910010205080951, "min": 0.5, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate target inventory with pipeline adjustment
    pipeline_adjustment = pipeline_weight * pipeline_orders[-1]
    target_inventory = base_stock + safety_stock - pipeline_adjustment

    # Calculate order-up-to quantity
    order_needed = target_inventory - inventory_position

    # Apply smoothing with demand forecast
    if order_needed > 0:
        smoothed_order = smoothing_factor * order_needed + (1 - smoothing_factor) * demand_forecast
    else:
        smoothed_order = 0

    # More aggressive adjustment for low inventory with threshold
    if on_hand_inventory < threshold_factor * demand_forecast:
        smoothed_order = smoothed_order * lost_sales_weight

    # Ensure non-negative integer order
    order_amount = max(0, int(round(smoothed_order)))

    return order_amount
