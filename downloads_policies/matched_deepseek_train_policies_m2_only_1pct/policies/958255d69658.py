# policy_hash: 958255d69658029fa60d1c0b2b5dffcc9b3c56900ebc2e599301cf821ca0b862
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_5
# matched_train_cells: 11
# source_prompt_files: 1
# best_target_performance: 1316.06
# best_prompt_performance: 1316.06
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_084144.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 408.8781824300625  # OPT_PARAM: {"initial": 408.8781824300625, "min": 400, "max": 650, "type": "float"}
    demand_forecast = 91.57860323891309  # OPT_PARAM: {"initial": 91.57860323891309, "min": 90, "max": 110, "type": "float"}
    smoothing_factor = 0.05117802359395592  # OPT_PARAM: {"initial": 0.05117802359395592, "min": 0.01, "max": 0.2, "type": "float"}
    safety_stock_multiplier = 0.9644774790824421  # OPT_PARAM: {"initial": 0.9644774790824421, "min": 0.8, "max": 2.0, "type": "float"}
    pipeline_coverage = 2.160577987685989  # OPT_PARAM: {"initial": 2.160577987685989, "min": 2.0, "max": 4.0, "type": "float"}

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
