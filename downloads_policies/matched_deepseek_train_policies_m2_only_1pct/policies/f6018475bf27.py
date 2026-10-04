# policy_hash: f6018475bf273f95245b07ad0cfe0213777fa52cce4e72a3a9bce87cfdb2a145
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_5
# matched_train_cells: 25
# source_prompt_files: 1
# best_target_performance: 1351.88
# best_prompt_performance: 1351.88
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_065841.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 316.3231238155782  # OPT_PARAM: {"initial": 316.3231238155782, "min": 200, "max": 400, "type": "float"}
    safety_stock = 31.323123815577464  # OPT_PARAM: {"initial": 31.323123815577464, "min": 0, "max": 100, "type": "float"}
    adjustment_factor = 0.7060848093755946  # OPT_PARAM: {"initial": 0.7060848093755946, "min": 0.5, "max": 1.0, "type": "float"}
    demand_buffer = 15.1  # OPT_PARAM: {"initial": 15.1, "min": 0, "max": 50, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand from pipeline pattern
    if len(pipeline_orders) >= 2:
        recent_orders = pipeline_orders[-2:]  # Last two orders placed
        avg_recent_order = sum(recent_orders) / len(recent_orders) if recent_orders else 0
    else:
        avg_recent_order = 0

    # Dynamic target based on recent ordering pattern
    dynamic_target = base_stock + safety_stock + demand_buffer * (avg_recent_order / 100)

    # Calculate order amount
    raw_order = max(0, dynamic_target - inventory_position)
    adjusted_order = raw_order * adjustment_factor

    # Round to nearest integer
    order_amount = int(round(adjusted_order))

    return order_amount
