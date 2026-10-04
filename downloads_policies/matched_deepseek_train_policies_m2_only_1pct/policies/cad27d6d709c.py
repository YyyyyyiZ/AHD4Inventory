# policy_hash: cad27d6d709c7f6f64ce16c261b77aac0a52e436e200a4b9f5284a805439069b
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_5
# matched_train_cells: 3
# source_prompt_files: 1
# best_target_performance: 11845.83
# best_prompt_performance: 11845.83
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_021129.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 431.7200375903465  # OPT_PARAM: {"initial": 431.7200375903465, "min": 300, "max": 700, "type": "float"}
    pipeline_weight = 0.9642302989134763  # OPT_PARAM: {"initial": 0.9642302989134763, "min": 0.5, "max": 1.0, "type": "float"}
    smoothing_factor = 0.15000000000000002  # OPT_PARAM: {"initial": 0.15000000000000002, "min": 0.05, "max": 0.5, "type": "float"}
    safety_stock = 108.42671483507314  # OPT_PARAM: {"initial": 108.42671483507314, "min": 50, "max": 250, "type": "float"}
    demand_buffer = 1.0123669705031182  # OPT_PARAM: {"initial": 1.0123669705031182, "min": 1.0, "max": 2.0, "type": "float"}
    lost_sales_weight = 0.3463375269627311  # OPT_PARAM: {"initial": 0.3463375269627311, "min": 0.1, "max": 1.0, "type": "float"}
    holding_weight = 0.1901889555248558  # OPT_PARAM: {"initial": 0.1901889555248558, "min": 0.1, "max": 0.5, "type": "float"}

    # Calculate total pipeline
    total_pipeline = sum(pipeline_orders)

    # Calculate inventory position with weighted pipeline
    weighted_pipeline = total_pipeline * pipeline_weight
    inventory_position = on_hand_inventory + weighted_pipeline

    # Estimate expected demand from recent pipeline arrivals
    if len(pipeline_orders) >= 4:
        # Use more recent orders for better demand estimation
        recent_orders = pipeline_orders[1:4]
        avg_recent_demand = sum(recent_orders) / len(recent_orders)
        expected_demand = avg_recent_demand * demand_buffer
    else:
        expected_demand = 0

    # Adjust base stock considering cost ratio (p=5, h=1)
    # Weight safety stock more toward preventing lost sales
    cost_adjusted_safety = safety_stock * (lost_sales_weight * 5 + holding_weight * 1) / 6

    # Dynamic base stock adjustment based on expected demand
    adjusted_base_stock = base_stock + cost_adjusted_safety + expected_demand

    # Base-stock policy
    order_amount = max(0, adjusted_base_stock - inventory_position)

    # Smooth ordering with adaptive smoothing
    if len(pipeline_orders) >= 2:
        avg_recent = sum(pipeline_orders[-2:]) / 2
        # Reduce smoothing when inventory is very low
        if inventory_position < adjusted_base_stock * 0.3:
            effective_smoothing = smoothing_factor * 0.5
        else:
            effective_smoothing = smoothing_factor

        order_amount = effective_smoothing * order_amount + (1 - effective_smoothing) * avg_recent

    # Ensure integer order amount
    return order_amount
