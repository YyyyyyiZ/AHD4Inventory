# policy_hash: 0ff76f3361b5ec96c7152ccc29a7cd11c195a9d5db471678a5cf85d4070591ba
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_5
# matched_train_cells: 3
# source_prompt_files: 1
# best_target_performance: 1345.58
# best_prompt_performance: 1345.58
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_071521.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 310.32656632199144  # OPT_PARAM: {"initial": 310.32656632199144, "min": 200, "max": 400, "type": "float"}
    safety_stock = 29.96931192824858  # OPT_PARAM: {"initial": 29.96931192824858, "min": 10, "max": 80, "type": "float"}
    adjustment_factor = 0.6785365008200204  # OPT_PARAM: {"initial": 0.6785365008200204, "min": 0.5, "max": 1.2, "type": "float"}
    demand_buffer = 12.98835379641835  # OPT_PARAM: {"initial": 12.98835379641835, "min": 5, "max": 40, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand from pipeline pattern
    if len(pipeline_orders) >= 2:
        recent_orders = pipeline_orders[-2:]  # Look at most recent orders placed
        estimated_demand = sum(recent_orders) / len(recent_orders) if recent_orders else 0
    else:
        estimated_demand = 0

    # Dynamic target based on estimated demand
    dynamic_target = base_stock + safety_stock + max(0, estimated_demand - 100) * 0.3

    # Add buffer for upcoming periods
    target_inventory = dynamic_target + demand_buffer

    # Calculate order amount with adjustment
    raw_order = max(0, target_inventory - inventory_position)
    adjusted_order = raw_order * adjustment_factor

    # Round to nearest integer
    order_amount = int(round(adjusted_order))

    return order_amount
