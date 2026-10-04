# policy_hash: e92e52e5c629910d14fc9ebe848ea9467e78bbe95f95ca9ca802385e7da413b0
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_2
# matched_train_cells: 43
# source_prompt_files: 1
# best_target_performance: 6372.58
# best_prompt_performance: 6371.94
# best_rel_error_pct: 0.010043
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_235426.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 299.7413401728866  # OPT_PARAM: {"initial": 299.7413401728866, "min": 100, "max": 600, "type": "float"}
    safety_stock = 35.27241588627878  # OPT_PARAM: {"initial": 35.27241588627878, "min": 0, "max": 150, "type": "float"}
    demand_smoothing_factor = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.05, "max": 0.5, "type": "float"}
    pipeline_coverage_factor = 0.8457793457046842  # OPT_PARAM: {"initial": 0.8457793457046842, "min": 0.0, "max": 1.5, "type": "float"}
    max_order_increase = 75.70785742285531  # OPT_PARAM: {"initial": 75.70785742285531, "min": 50, "max": 300, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand based on pipeline arrivals (as proxy for recent demand)
    if pipeline_orders:
        # Use weighted average with more weight on recent periods
        weights = [0.6, 0.3, 0.1][:len(pipeline_orders)]
        weights = [w/sum(weights) for w in weights]
        weighted_demand_estimate = sum(w * d for w, d in zip(weights, pipeline_orders))
    else:
        weighted_demand_estimate = 0

    # Smooth demand estimate
    smoothed_demand = demand_smoothing_factor * weighted_demand_estimate + (1 - demand_smoothing_factor) * (base_stock / 4)

    # Adjust base stock based on demand variability
    adjusted_base_stock = base_stock + 2.0 * smoothed_demand

    # Calculate order-up-to level
    order_up_to = adjusted_base_stock + safety_stock

    # Account for pipeline coverage
    pipeline_cover = pipeline_coverage_factor * sum(pipeline_orders)
    target_inventory = order_up_to - pipeline_cover

    # Calculate order amount
    order_amount = max(0, target_inventory - inventory_position)

    # Apply smoothing to avoid extreme fluctuations
    if order_amount > max_order_increase:
        order_amount = max_order_increase + (order_amount - max_order_increase) * 0.3

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
