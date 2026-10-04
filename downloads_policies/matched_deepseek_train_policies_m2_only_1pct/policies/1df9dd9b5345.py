# policy_hash: 1df9dd9b53455a890e9edd32a351d2cf80d0249c1dacc4146a99274a32127a76
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_5
# matched_train_cells: 4
# source_prompt_files: 1
# best_target_performance: 1295.1
# best_prompt_performance: 1295.1
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_005102.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 439.610087727406  # OPT_PARAM: {"initial": 439.610087727406, "min": 400, "max": 500, "type": "float"}
    safety_stock = 20.144822696923768  # OPT_PARAM: {"initial": 20.144822696923768, "min": 15, "max": 40, "type": "float"}
    demand_forecast = 97.56720906093777  # OPT_PARAM: {"initial": 97.56720906093777, "min": 95, "max": 105, "type": "float"}
    smoothing_factor = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.3, "type": "float"}
    pipeline_weight = 0.7164651231370672  # OPT_PARAM: {"initial": 0.7164651231370672, "min": 0.5, "max": 0.9, "type": "float"}

    # Calculate total pipeline with weighted emphasis on near-term arrivals
    total_pipeline = sum(pipeline_orders)
    weighted_pipeline = pipeline_weight * total_pipeline + (1 - pipeline_weight) * sum(pipeline_orders[:2])

    # Calculate inventory position
    inventory_position = on_hand_inventory + weighted_pipeline

    # Dynamic order-up-to level that adjusts based on pipeline composition
    order_up_to = base_stock + safety_stock

    # Calculate order quantity with more aggressive adjustment
    raw_order = max(0, order_up_to - inventory_position)

    # Apply smoothing with emphasis on meeting the gap
    smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * demand_forecast

    # Ensure minimum order when inventory position is significantly below target
    if inventory_position < 0.8 * order_up_to:
        smoothed_order = max(smoothed_order, demand_forecast)

    # Round to nearest integer
    order_amount = max(0, int(round(smoothed_order)))

    return order_amount
