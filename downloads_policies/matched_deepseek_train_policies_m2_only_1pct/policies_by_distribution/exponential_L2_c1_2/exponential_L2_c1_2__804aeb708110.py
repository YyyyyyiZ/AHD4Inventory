# policy_hash: 804aeb7081100b53101915706c3f736a4481a6e13a420a4ebb3ba529e0b6e3f4
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_2
# matched_train_cells: 26
# source_prompt_files: 1
# best_target_performance: 5881.95
# best_prompt_performance: 5882.0
# best_rel_error_pct: 0.000850
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_225505.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 210.8037827560155  # OPT_PARAM: {"initial": 210.8037827560155, "min": 150, "max": 300, "type": "float"}
    safety_factor = 2.891134826804754  # OPT_PARAM: {"initial": 2.891134826804754, "min": 1.5, "max": 4.0, "type": "float"}
    pipeline_weight = 0.953797284450267  # OPT_PARAM: {"initial": 0.953797284450267, "min": 0.8, "max": 1.0, "type": "float"}
    smoothing_factor = 0.2689864222503652  # OPT_PARAM: {"initial": 0.2689864222503652, "min": 0.1, "max": 0.5, "type": "float"}
    demand_adj_factor = 0.16139185335078168  # OPT_PARAM: {"initial": 0.16139185335078168, "min": 0.05, "max": 0.3, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate demand variability from recent pipeline orders
    if len(pipeline_orders) >= 2:
        recent_orders = pipeline_orders[-2:]  # Focus on most recent orders
        avg_recent = sum(recent_orders) / len(recent_orders)
        variance = sum((p - avg_recent) ** 2 for p in recent_orders) / len(recent_orders)
        std_dev = max(variance ** 0.5, avg_recent * 0.2)
    else:
        std_dev = base_stock * 0.2

    # Safety stock calculation
    safety_stock = safety_factor * std_dev

    # Pipeline adjustment - more aggressive when pipeline is low
    total_pipeline = sum(pipeline_orders)
    expected_pipeline = base_stock * len(pipeline_orders) * pipeline_weight
    pipeline_adjustment = max(0, expected_pipeline - total_pipeline) * demand_adj_factor

    # Target inventory position
    target_inventory = base_stock + safety_stock + pipeline_adjustment

    # Order calculation
    order_needed = target_inventory - inventory_position

    # Apply smoothing to large orders
    if abs(order_needed) > base_stock * 0.3:
        smoothed_order = order_needed * smoothing_factor
    else:
        smoothed_order = order_needed

    # Ensure non-negative integer order
    order_amount = max(0, int(round(smoothed_order)))

    return order_amount
