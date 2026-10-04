# policy_hash: 424b849e669f5aaa7d2aa5cbd2464a8ea3cb3b1888940b0ca684d6fa3e7f3bc8
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_2
# matched_train_cells: 1
# source_prompt_files: 1
# best_target_performance: 7759.18
# best_prompt_performance: 7759.18
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_091210.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 307.2097401669807  # OPT_PARAM: {"initial": 307.2097401669807, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 0.0  # OPT_PARAM: {"initial": 0.0, "min": 0, "max": 300, "type": "float"}
    lead_time = len(pipeline_orders)

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    # Use average of recent pipeline arrivals as demand proxy
    if lead_time >= 2:
        recent_arrivals = pipeline_orders[-min(lead_time, 3):]
        avg_recent_demand = sum(recent_arrivals) / len(recent_arrivals)
    else:
        avg_recent_demand = 0

    # Adjust base stock based on recent demand pattern
    adjusted_base = base_stock + safety_stock * (avg_recent_demand / 100)

    # Calculate order amount
    order_amount = max(0, adjusted_base - inventory_position)

    # Round to nearest integer since order amounts should be integers
    order_amount = int(round(order_amount))

    return order_amount
