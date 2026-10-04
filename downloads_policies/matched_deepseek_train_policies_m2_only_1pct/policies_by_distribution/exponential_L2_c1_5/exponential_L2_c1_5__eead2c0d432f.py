# policy_hash: eead2c0d432fa83beebb48a34c462acd3f910252c8c98241a826999f68c4f04e
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_5
# matched_train_cells: 16
# source_prompt_files: 1
# best_target_performance: 10191.99
# best_prompt_performance: 10191.99
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_232146.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 363.6255873301382  # OPT_PARAM: {"initial": 363.6255873301382, "min": 200, "max": 600, "type": "float"}
    safety_stock = 28.625587330134717  # OPT_PARAM: {"initial": 28.625587330134717, "min": 0, "max": 100, "type": "float"}
    smoothing_factor = 0.3444601504444024  # OPT_PARAM: {"initial": 0.3444601504444024, "min": 0.3, "max": 1.0, "type": "float"}
    demand_anticipation_factor = 0.8378125912950449  # OPT_PARAM: {"initial": 0.8378125912950449, "min": 0.0, "max": 1.0, "type": "float"}
    pipeline_weight = 0.7  # OPT_PARAM: {"initial": 0.7, "min": 0.0, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand using weighted combination of pipeline arrivals
    if len(pipeline_orders) > 0:
        # Give more weight to recent pipeline orders
        weighted_sum = 0
        total_weight = 0
        for i, order in enumerate(pipeline_orders):
            weight = pipeline_weight ** (len(pipeline_orders) - i - 1)
            weighted_sum += order * weight
            total_weight += weight
        avg_pipeline = weighted_sum / total_weight if total_weight > 0 else 0
        demand_estimate = demand_anticipation_factor * avg_pipeline
    else:
        demand_estimate = 0

    # Dynamic target calculation
    target_inventory = base_stock + safety_stock + demand_estimate

    # Calculate order amount with smoothing
    raw_order = max(0, target_inventory - inventory_position)
    order_amount = smoothing_factor * raw_order

    # Round to nearest integer
    return order_amount
