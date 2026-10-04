# policy_hash: a232071da71e88a98cc44346bd87e05f3e75b34498ffffc699d95446c498838f
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_5
# matched_train_cells: 8
# source_prompt_files: 1
# best_target_performance: 1218.22
# best_prompt_performance: 1218.22
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_083510.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 412.9705355509506  # OPT_PARAM: {"initial": 412.9705355509506, "min": 400, "max": 650, "type": "float"}
    demand_forecast = 94.47578943354189  # OPT_PARAM: {"initial": 94.47578943354189, "min": 90, "max": 110, "type": "float"}
    smoothing_factor = 0.017253427100944605  # OPT_PARAM: {"initial": 0.017253427100944605, "min": 0.01, "max": 0.2, "type": "float"}
    safety_stock_multiplier = 1.0854484933574706  # OPT_PARAM: {"initial": 1.0854484933574706, "min": 0.8, "max": 2.0, "type": "float"}
    pipeline_coverage = 2.556312331048841  # OPT_PARAM: {"initial": 2.556312331048841, "min": 2.0, "max": 4.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Dynamic safety stock based on demand forecast and pipeline coverage
    safety_stock = safety_stock_multiplier * demand_forecast * pipeline_coverage

    # Adjusted base stock level
    adjusted_base_stock = base_stock + safety_stock

    # Calculate expected shortfall
    expected_shortfall = max(0, adjusted_base_stock - inventory_position)

    # More aggressive smoothing for faster response
    smoothed_order = smoothing_factor * expected_shortfall + (1 - smoothing_factor) * demand_forecast

    # Ensure non-negative order
    order_amount = max(0, round(smoothed_order))

    return order_amount
