# policy_hash: 7af440baca6dad730d801ba4ea6ecdbe632ae4bb01b0119a67ac6dde210a92ee
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_2
# matched_train_cells: 8
# source_prompt_files: 2
# best_target_performance: 5886.04
# best_prompt_performance: 5886.04
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_225014.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 184.74667716602306  # OPT_PARAM: {"initial": 184.74667716602306, "min": 100, "max": 300, "type": "float"}
    safety_factor = 3.247022518402694  # OPT_PARAM: {"initial": 3.247022518402694, "min": 1.5, "max": 4.0, "type": "float"}
    pipeline_weight = 0.9058820717235917  # OPT_PARAM: {"initial": 0.9058820717235917, "min": 0.5, "max": 1.0, "type": "float"}
    smoothing_factor = 0.34308896619119045  # OPT_PARAM: {"initial": 0.34308896619119045, "min": 0.1, "max": 0.5, "type": "float"}
    demand_adj_factor = 0.2058939091288646  # OPT_PARAM: {"initial": 0.2058939091288646, "min": 0.05, "max": 0.3, "type": "float"}

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
