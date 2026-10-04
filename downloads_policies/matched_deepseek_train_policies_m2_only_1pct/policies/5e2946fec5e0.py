# policy_hash: 5e2946fec5e0df5668d87b546a538d9c3530097963f2e7e7f7ab52a580b571fe
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std30_L4_c1_5
# matched_train_cells: 56
# source_prompt_files: 1
# best_target_performance: 3532.72
# best_prompt_performance: 3532.72
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std30_L4_c1_5_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260130_062010.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 427.59237499583514  # OPT_PARAM: {"initial": 427.59237499583514, "min": 200, "max": 600, "type": "float"}
    safety_stock = 80.0  # OPT_PARAM: {"initial": 80.0, "min": 20, "max": 150, "type": "float"}
    demand_multiplier = 1.2  # OPT_PARAM: {"initial": 1.2, "min": 0.3, "max": 1.2, "type": "float"}
    pipeline_weight = 0.4  # OPT_PARAM: {"initial": 0.4, "min": 0.1, "max": 0.8, "type": "float"}
    max_order = 97.39306810671411  # OPT_PARAM: {"initial": 97.39306810671411, "min": 80, "max": 200, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand using weighted pipeline information
    # Give more weight to recent pipeline orders
    if len(pipeline_orders) >= 2:
        weighted_demand = (pipeline_orders[0] * 0.6 + pipeline_orders[1] * 0.4)
    elif pipeline_orders:
        weighted_demand = pipeline_orders[0]
    else:
        weighted_demand = 0

    # Adjust base stock based on demand pattern
    adjusted_base = base_stock + demand_multiplier * weighted_demand

    # Incorporate pipeline coverage into safety stock adjustment
    pipeline_coverage = sum(pipeline_orders) * pipeline_weight
    effective_safety = safety_stock + pipeline_coverage / 4

    # Calculate order-up-to level
    order_up_to = max(adjusted_base, effective_safety * 3)

    # Calculate order amount
    order_amount = max(0, order_up_to - inventory_position)

    # Apply smoothing with dynamic cap
    order_amount = min(order_amount, max_order)

    # Ensure integer order amount
    return order_amount
