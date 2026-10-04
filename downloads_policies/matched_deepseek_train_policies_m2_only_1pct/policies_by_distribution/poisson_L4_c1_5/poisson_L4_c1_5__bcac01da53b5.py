# policy_hash: bcac01da53b5dd5cdbee32b7fd06d46f4c14ac15b78a351f2a23af28b10b9a22
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_5
# matched_train_cells: 12
# source_prompt_files: 1
# best_target_performance: 1273.68
# best_prompt_performance: 1273.68
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_084449.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 467.2401038493759  # OPT_PARAM: {"initial": 467.2401038493759, "min": 450, "max": 650, "type": "float"}
    demand_forecast = 95.1  # OPT_PARAM: {"initial": 95.1, "min": 95, "max": 105, "type": "float"}
    smoothing_factor = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.3, "type": "float"}
    safety_stock = 10.750729061551002  # OPT_PARAM: {"initial": 10.750729061551002, "min": 10, "max": 60, "type": "float"}
    shortfall_multiplier = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 1.0, "max": 2.5, "type": "float"}
    pipeline_weight = 0.8  # OPT_PARAM: {"initial": 0.8, "min": 0.8, "max": 1.0, "type": "float"}

    # Calculate effective pipeline inventory
    effective_pipeline = sum(p * pipeline_weight for p in pipeline_orders)
    inventory_position = on_hand_inventory + effective_pipeline

    # Calculate target inventory level
    target_inventory = base_stock + safety_stock

    # Calculate shortfall with multiplier
    shortfall = max(0, target_inventory - inventory_position)
    adjusted_shortfall = shortfall_multiplier * shortfall

    # Order calculation: blend of forecast and adjusted shortfall
    order_amount = smoothing_factor * adjusted_shortfall + (1 - smoothing_factor) * demand_forecast

    # Round to nearest integer and ensure non-negative
    order_amount = max(0, round(order_amount))

    return order_amount
