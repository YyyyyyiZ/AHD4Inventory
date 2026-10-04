# policy_hash: 36a808b80787abd5f5b40231d756b256a46f447a3a36579083af4786523cb907
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_5
# matched_train_cells: 2
# source_prompt_files: 1
# best_target_performance: 1347.53
# best_prompt_performance: 1347.53
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_231809.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 311.5192843129855  # OPT_PARAM: {"initial": 311.5192843129855, "min": 200, "max": 500, "type": "float"}
    safety_stock = 33.830364847598275  # OPT_PARAM: {"initial": 33.830364847598275, "min": 10, "max": 100, "type": "float"}
    demand_forecast_factor = 1.05  # OPT_PARAM: {"initial": 1.05, "min": 0.8, "max": 1.3, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate demand using recent arrivals
    if len(pipeline_orders) >= 2 and pipeline_orders[0] > 0:
        recent_demand_estimate = pipeline_orders[0] * demand_forecast_factor
    else:
        recent_demand_estimate = 100.0

    # Dynamic base stock adjustment
    adjusted_base_stock = base_stock + safety_stock

    # More aggressive adjustment based on demand estimate
    if recent_demand_estimate > 115:
        adjusted_base_stock += 35.0  # OPT_PARAM: {"initial": 35.0, "min": 10, "max": 80, "type": "float"}
    elif recent_demand_estimate < 85:
        adjusted_base_stock -= 25.0  # OPT_PARAM: {"initial": 25.0, "min": 10, "max": 60, "type": "float"}

    # Calculate order amount
    raw_order = max(0, adjusted_base_stock - inventory_position)

    # Apply different smoothing based on order size
    smoothing_factor_large = 0.6383036484759828  # OPT_PARAM: {"initial": 0.6383036484759828, "min": 0.3, "max": 1.0, "type": "float"}
    smoothing_factor_small = 0.7383036484759828  # OPT_PARAM: {"initial": 0.7383036484759828, "min": 0.5, "max": 1.0, "type": "float"}

    if raw_order > 150:
        order_amount = raw_order * smoothing_factor_large
    elif raw_order > 50:
        order_amount = raw_order * smoothing_factor_small
    else:
        order_amount = raw_order

    # Round to nearest integer
    return order_amount
