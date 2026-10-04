# policy_hash: aa4896dc94849d5376b68b144e02d3aa82b4e432e7302fcbe2f458c1166a446b
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_2
# matched_train_cells: 1
# source_prompt_files: 1
# best_target_performance: 6165.14
# best_prompt_performance: 6165.14
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_023853.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 201.09149510408108  # OPT_PARAM: {"initial": 201.09149510408108, "min": 50, "max": 500, "type": "float"}
    safety_stock = 75.0  # OPT_PARAM: {"initial": 75.0, "min": 20, "max": 200, "type": "float"}
    demand_smoothing = 0.0  # OPT_PARAM: {"initial": 0.0, "min": 0.0, "max": 1.0, "type": "float"}
    pipeline_weight = 0.6  # OPT_PARAM: {"initial": 0.6, "min": 0.0, "max": 1.0, "type": "float"}
    min_order = 49.65652661553391  # OPT_PARAM: {"initial": 49.65652661553391, "min": 0, "max": 50, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate demand using pipeline arrivals with smoothing
    if pipeline_orders and pipeline_orders[0] > 0:
        # Weighted average of recent pipeline arrivals
        recent_arrivals = [p for p in pipeline_orders if p > 0]
        if recent_arrivals:
            # Give more weight to most recent arrivals
            weights = [pipeline_weight ** i for i in range(len(recent_arrivals))]
            weights = [w/sum(weights) for w in weights]
            estimated_demand = sum(r * w for r, w in zip(recent_arrivals, weights))
        else:
            estimated_demand = 100.0
    else:
        estimated_demand = 100.0

    # Adjust base stock dynamically based on demand estimate
    # Higher demand -> higher base stock, but with diminishing returns
    demand_adjustment = demand_smoothing * (estimated_demand - 100.0)
    adjusted_base_stock = base_stock + demand_adjustment

    # Ensure minimum safety stock
    target_inventory = max(adjusted_base_stock, safety_stock)

    # Calculate order amount
    order_amount = max(0, target_inventory - inventory_position)

    # Apply minimum order quantity if ordering
    if order_amount > 0:
        order_amount = max(order_amount, min_order)

    # Round to nearest integer
    return order_amount
