# policy_hash: 50c5586cbfba9fc02b3320d64320bbf49bf914ad166d0f0622c8284d1e38afc4
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_5
# matched_train_cells: 15
# source_prompt_files: 1
# best_target_performance: 1234.84
# best_prompt_performance: 1234.84
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_083957.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 400.0  # OPT_PARAM: {"initial": 400.0, "min": 400, "max": 650, "type": "float"}
    demand_forecast = 93.30369189639265  # OPT_PARAM: {"initial": 93.30369189639265, "min": 90, "max": 110, "type": "float"}
    smoothing_factor = 0.026797510507657083  # OPT_PARAM: {"initial": 0.026797510507657083, "min": 0.01, "max": 0.2, "type": "float"}
    safety_stock_multiplier = 1.1003710417345827  # OPT_PARAM: {"initial": 1.1003710417345827, "min": 0.8, "max": 2.0, "type": "float"}
    pipeline_coverage = 2.3317241875867505  # OPT_PARAM: {"initial": 2.3317241875867505, "min": 2.0, "max": 4.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Dynamic safety stock
    safety_stock = safety_stock_multiplier * demand_forecast * pipeline_coverage

    # Adjusted base stock level
    adjusted_base_stock = base_stock + safety_stock

    # Calculate order-up-to quantity
    order_up_to = max(0, adjusted_base_stock - inventory_position)

    # Apply smoothing with more aggressive response
    smoothed_order = smoothing_factor * order_up_to + (1 - smoothing_factor) * demand_forecast

    # Ensure non-negative integer order
    order_amount = max(0, round(smoothed_order))

    return order_amount
