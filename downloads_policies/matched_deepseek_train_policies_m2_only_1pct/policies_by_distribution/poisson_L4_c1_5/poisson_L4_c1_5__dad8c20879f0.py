# policy_hash: dad8c20879f06d634b388a461ae29b2c0f4697f8b756fdeef27b7d71b19077a6
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_5
# matched_train_cells: 24
# source_prompt_files: 1
# best_target_performance: 1212.4
# best_prompt_performance: 1212.4
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_083131.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 513.0571984434707  # OPT_PARAM: {"initial": 513.0571984434707, "min": 400, "max": 650, "type": "float"}
    demand_forecast = 96.46008277298097  # OPT_PARAM: {"initial": 96.46008277298097, "min": 90, "max": 110, "type": "float"}
    smoothing_factor = 0.01  # OPT_PARAM: {"initial": 0.01, "min": 0.01, "max": 0.2, "type": "float"}
    safety_stock = 43.15719844346902  # OPT_PARAM: {"initial": 43.15719844346902, "min": 20, "max": 100, "type": "float"}
    pipeline_weight = 0.8329902327967246  # OPT_PARAM: {"initial": 0.8329902327967246, "min": 0.5, "max": 1.0, "type": "float"}

    # Calculate effective inventory position with pipeline weighting
    weighted_pipeline = sum(p * pipeline_weight ** i for i, p in enumerate(reversed(pipeline_orders)))
    inventory_position = on_hand_inventory + weighted_pipeline

    # Calculate target with safety stock
    target_inventory = base_stock + safety_stock

    # Calculate expected shortfall
    expected_shortfall = max(0, target_inventory - inventory_position)

    # Smooth adjustment with stronger emphasis on shortfall
    smoothed_order = smoothing_factor * expected_shortfall + (1 - smoothing_factor) * demand_forecast

    # Ensure non-negative order
    order_amount = max(0, round(smoothed_order))

    return order_amount
