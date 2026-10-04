# policy_hash: 8165f3b13eb1dc901d45f5d45863c7aa929f5890967e5445b0ee5910a44638f8
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_5
# matched_train_cells: 9
# source_prompt_files: 1
# best_target_performance: 1223.22
# best_prompt_performance: 1223.22
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_083603.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 481.84371658458474  # OPT_PARAM: {"initial": 481.84371658458474, "min": 400, "max": 650, "type": "float"}
    demand_forecast = 96.01889824843279  # OPT_PARAM: {"initial": 96.01889824843279, "min": 90, "max": 110, "type": "float"}
    smoothing_factor = 0.01379542093502565  # OPT_PARAM: {"initial": 0.01379542093502565, "min": 0.01, "max": 0.2, "type": "float"}
    safety_stock_multiplier = 1.1994487361760604  # OPT_PARAM: {"initial": 1.1994487361760604, "min": 0.8, "max": 2.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Dynamic safety stock based on lead time and demand variability
    safety_stock = safety_stock_multiplier * demand_forecast

    # Adjusted base stock level
    adjusted_base_stock = base_stock + safety_stock

    # Calculate order-up-to level
    order_up_to = max(0, adjusted_base_stock - inventory_position)

    # Apply smoothing to reduce order volatility
    smoothed_order = smoothing_factor * order_up_to + (1 - smoothing_factor) * demand_forecast

    # Round to nearest integer and ensure non-negative
    order_amount = max(0, round(smoothed_order))

    return order_amount
