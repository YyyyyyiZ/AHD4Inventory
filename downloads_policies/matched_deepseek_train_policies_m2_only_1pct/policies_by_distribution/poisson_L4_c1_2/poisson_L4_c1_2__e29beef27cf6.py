# policy_hash: e29beef27cf6e771b089da62712a6ac051ca5d5248223da5185351b77f9c2a4a
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_2
# matched_train_cells: 4
# source_prompt_files: 1
# best_target_performance: 780.26
# best_prompt_performance: 780.26
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_075854.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 307.404910532378  # OPT_PARAM: {"initial": 307.404910532378, "min": 250, "max": 400, "type": "float"}
    safety_stock = 29.522704109022623  # OPT_PARAM: {"initial": 29.522704109022623, "min": 20, "max": 80, "type": "float"}
    demand_forecast = 92.2551857323948  # OPT_PARAM: {"initial": 92.2551857323948, "min": 85, "max": 115, "type": "float"}
    smoothing_factor = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.3, "type": "float"}
    pipeline_weight = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.3, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Weighted pipeline consideration: give more weight to imminent arrivals
    weighted_pipeline = pipeline_orders[0] * pipeline_weight + sum(pipeline_orders[1:]) * (1 - pipeline_weight)
    effective_position = on_hand_inventory + weighted_pipeline

    # Dynamic target based on pipeline composition
    target_inventory = base_stock + safety_stock

    # Order calculation with pipeline-aware adjustment
    raw_order = max(0, target_inventory - effective_position)

    # Apply smoothing with demand forecast
    smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * demand_forecast

    # Ensure order is integer and non-negative
    order_amount = max(0, int(round(smoothed_order)))

    return order_amount
