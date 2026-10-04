# policy_hash: 216bb00480791e23246323b94d4f5caa0df0b3d0d2d9e8e80f9ff3d2a7abe20f
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_5
# matched_train_cells: 9
# source_prompt_files: 1
# best_target_performance: 1760.34
# best_prompt_performance: 1767.18
# best_rel_error_pct: 0.388561
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_003652.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 409.56113907768616  # OPT_PARAM: {"initial": 409.56113907768616, "min": 400, "max": 550, "type": "float"}
    safety_stock = 25.000112321896243  # OPT_PARAM: {"initial": 25.000112321896243, "min": 10, "max": 60, "type": "float"}
    demand_forecast = 91.2082993815649  # OPT_PARAM: {"initial": 91.2082993815649, "min": 90, "max": 110, "type": "float"}
    smoothing_factor = 0.2  # OPT_PARAM: {"initial": 0.2, "min": 0.2, "max": 0.5, "type": "float"}
    pipeline_weight = 0.6111916377448575  # OPT_PARAM: {"initial": 0.6111916377448575, "min": 0.5, "max": 0.9, "type": "float"}

    # Calculate inventory position with weighted pipeline
    weighted_pipeline = sum(p * (pipeline_weight ** i) for i, p in enumerate(pipeline_orders))
    inventory_position = on_hand_inventory + weighted_pipeline

    # Dynamic order-up-to level based on pipeline composition
    pipeline_ratio = sum(pipeline_orders) / (len(pipeline_orders) * demand_forecast + 1e-6)
    adjustment = safety_stock * (1.0 - min(1.0, pipeline_ratio))
    order_up_to = base_stock + adjustment

    # Calculate order quantity
    raw_order = max(0, order_up_to - inventory_position)

    # Apply smoothing with demand forecast
    smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * demand_forecast

    # Round to nearest integer
    order_amount = max(0, int(round(smoothed_order)))

    return order_amount
