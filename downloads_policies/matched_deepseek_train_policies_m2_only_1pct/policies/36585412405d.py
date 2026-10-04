# policy_hash: 36585412405d6e405c49e77200d87fff7e437306a145cb0c9a328b92c467914e
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_2
# matched_train_cells: 32
# source_prompt_files: 1
# best_target_performance: 6308.02
# best_prompt_performance: 6308.02
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_035744.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 350.0  # OPT_PARAM: {"initial": 350.0, "min": 200, "max": 600, "type": "float"}
    safety_stock = 25.0  # OPT_PARAM: {"initial": 25.0, "min": 0, "max": 100, "type": "float"}
    demand_smoothing = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.1, "max": 0.8, "type": "float"}
    order_smoothing = 0.4  # OPT_PARAM: {"initial": 0.4, "min": 0.1, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate demand estimate from pipeline arrivals (recent deliveries)
    # Use weighted average with more weight on recent periods
    if len(pipeline_orders) > 0:
        weights = [0.5, 0.3, 0.2]  # OPT_PARAM: {"initial": [0.5, 0.3, 0.2], "min": [0.1, 0.1, 0.1], "max": [0.8, 0.6, 0.4], "type": "list"}
        recent_arrivals = pipeline_orders[:min(3, len(pipeline_orders))]
        weighted_sum = 0
        total_weight = 0
        for i, arrival in enumerate(recent_arrivals):
            weight = weights[i] if i < len(weights) else 0.1
            weighted_sum += arrival * weight
            total_weight += weight
        avg_demand = weighted_sum / total_weight if total_weight > 0 else 0
    else:
        avg_demand = 0

    # Adjust base stock based on demand trend
    adjusted_base_stock = base_stock + demand_smoothing * avg_demand

    # Calculate target inventory position
    target_inventory = adjusted_base_stock + safety_stock

    # Calculate raw order amount
    raw_order = max(0, target_inventory - inventory_position)

    # Apply order smoothing
    if raw_order > 0:
        order_amount = order_smoothing * raw_order
    else:
        order_amount = 0

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
