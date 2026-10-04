# policy_hash: 4b2d3f504d37bfbd9368237919753ef5a2540e6a7030f7870c7a58cfbab92a45
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_5
# matched_train_cells: 16
# source_prompt_files: 1
# best_target_performance: 1301.24
# best_prompt_performance: 1301.24
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_084623.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 400.16572231105283  # OPT_PARAM: {"initial": 400.16572231105283, "min": 300, "max": 600, "type": "float"}
    demand_forecast = 92.52329548008333  # OPT_PARAM: {"initial": 92.52329548008333, "min": 90, "max": 110, "type": "float"}
    smoothing_factor = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.3, "type": "float"}
    safety_stock_multiplier = 1.020654248865138  # OPT_PARAM: {"initial": 1.020654248865138, "min": 1.0, "max": 2.5, "type": "float"}
    pipeline_coverage = 2.1975630816548763  # OPT_PARAM: {"initial": 2.1975630816548763, "min": 2.0, "max": 4.0, "type": "float"}
    lost_sales_weight = 0.8866802969369267  # OPT_PARAM: {"initial": 0.8866802969369267, "min": 0.5, "max": 0.9, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Dynamic safety stock based on forecast and pipeline coverage
    safety_stock = safety_stock_multiplier * demand_forecast * pipeline_coverage

    # Adjust base stock based on cost ratio (p=5, h=1)
    # Higher weight on avoiding lost sales
    adjusted_base_stock = base_stock + safety_stock * lost_sales_weight

    # Calculate order-up-to quantity
    order_up_to = max(0, adjusted_base_stock - inventory_position)

    # Apply smoothing with moderate response
    smoothed_order = smoothing_factor * order_up_to + (1 - smoothing_factor) * demand_forecast

    # Ensure non-negative integer order
    order_amount = max(0, round(smoothed_order))

    return order_amount
