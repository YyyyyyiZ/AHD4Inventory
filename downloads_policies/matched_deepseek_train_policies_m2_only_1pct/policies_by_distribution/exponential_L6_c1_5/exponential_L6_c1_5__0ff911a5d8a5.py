# policy_hash: 0ff911a5d8a510c98220ffe129b3deb53cbd7a1795ea16a68dbcde93ccb74abd
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_5
# matched_train_cells: 38
# source_prompt_files: 2
# best_target_performance: 11790.2
# best_prompt_performance: 11790.2
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_020140.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 360.94020818597033  # OPT_PARAM: {"initial": 360.94020818597033, "min": 200, "max": 800, "type": "float"}
    pipeline_weight = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.5, "max": 1.0, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.5, "type": "float"}
    safety_stock = 90.94020818595367  # OPT_PARAM: {"initial": 90.94020818595367, "min": 50, "max": 300, "type": "float"}
    demand_buffer = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 1.0, "max": 2.0, "type": "float"}

    # Calculate total pipeline (all upcoming orders)
    total_pipeline = sum(pipeline_orders)

    # Calculate inventory position with weighted pipeline
    weighted_pipeline = total_pipeline * pipeline_weight
    inventory_position = on_hand_inventory + weighted_pipeline

    # Calculate expected demand based on recent pipeline arrivals
    # (pipeline_orders[0] is arriving now, pipeline_orders[1] arrived L-1 periods ago)
    if len(pipeline_orders) >= 3:
        # Look at orders that were placed to meet recent demand
        recent_orders = pipeline_orders[1:4]  # Skip current arrival
        avg_recent_demand = sum(recent_orders) / len(recent_orders)
        expected_demand = avg_recent_demand * demand_buffer
    else:
        expected_demand = 0

    # Adjust base stock with safety stock and expected demand
    adjusted_base_stock = base_stock + safety_stock + expected_demand

    # Base-stock policy
    order_amount = max(0, adjusted_base_stock - inventory_position)

    # Smooth ordering to avoid extreme fluctuations
    if len(pipeline_orders) >= 2:
        avg_recent = sum(pipeline_orders[-2:]) / 2
        order_amount = smoothing_factor * order_amount + (1 - smoothing_factor) * avg_recent

    # Round to nearest integer and ensure non-negative
    return order_amount
