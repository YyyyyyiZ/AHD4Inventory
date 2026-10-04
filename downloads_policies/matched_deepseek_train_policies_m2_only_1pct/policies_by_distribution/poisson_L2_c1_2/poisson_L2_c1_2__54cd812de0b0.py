# policy_hash: 54cd812de0b011dca47f3bd437614d401703f86e39f9dc11f54ad4f0c5ade4b4
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_2
# matched_train_cells: 2
# source_prompt_files: 1
# best_target_performance: 718.4
# best_prompt_performance: 718.4
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_224959.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 280.0  # OPT_PARAM: {"initial": 280.0, "min": 280, "max": 340, "type": "float"}
    safety_stock = 20.0  # OPT_PARAM: {"initial": 20.0, "min": 20, "max": 35, "type": "float"}
    demand_forecast = 96.0  # OPT_PARAM: {"initial": 96.0, "min": 96, "max": 102, "type": "float"}
    smoothing_factor = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.3, "type": "float"}
    pipeline_weight = 0.9  # OPT_PARAM: {"initial": 0.9, "min": 0.5, "max": 1.0, "type": "float"}

    # Calculate total pipeline inventory (unweighted)
    total_pipeline = sum(pipeline_orders)

    # Calculate inventory position (traditional: on-hand + all pipeline)
    inventory_position = on_hand_inventory + total_pipeline

    # Calculate order-up-to level with simpler adjustment
    # Base adjustment based on pipeline coverage
    pipeline_coverage = total_pipeline / (2 * demand_forecast + 1e-6)
    if pipeline_coverage < 0.8:
        adjustment = safety_stock * 1.2
    elif pipeline_coverage > 1.2:
        adjustment = safety_stock * 0.8
    else:
        adjustment = safety_stock

    order_up_to = base_stock + adjustment

    # Calculate raw order amount
    raw_order = max(0, order_up_to - inventory_position)

    # Apply smoothing with simpler logic
    if raw_order > demand_forecast * 2.0:
        # Large orders: smooth more aggressively
        smoothed_order = smoothing_factor * 0.5 * raw_order + (1 - smoothing_factor * 0.5) * demand_forecast
    else:
        smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * demand_forecast

    # Ensure minimum order is at least forecast * 0.5
    if smoothed_order < demand_forecast * 0.5:
        smoothed_order = demand_forecast * 0.5

    # Round to nearest integer
    order_amount = int(round(smoothed_order))

    return order_amount
