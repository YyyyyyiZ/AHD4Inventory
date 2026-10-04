# policy_hash: de054f6e35d55cd7222eab58e1cb49ff0b9b042dcf8e3484d8352301fe20448b
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_5
# matched_train_cells: 26
# source_prompt_files: 1
# best_target_performance: 11444.73
# best_prompt_performance: 11444.73
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_062024.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 591.4958860497374  # OPT_PARAM: {"initial": 591.4958860497374, "min": 300, "max": 600, "type": "float"}
    safety_stock = 295.95328156521373  # OPT_PARAM: {"initial": 295.95328156521373, "min": 100, "max": 300, "type": "float"}
    pipeline_weight = 0.6  # OPT_PARAM: {"initial": 0.6, "min": 0.6, "max": 1.0, "type": "float"}
    smoothing = 0.2  # OPT_PARAM: {"initial": 0.2, "min": 0.2, "max": 0.8, "type": "float"}
    demand_buffer = 1.5  # OPT_PARAM: {"initial": 1.5, "min": 1.0, "max": 1.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand from recent pipeline arrivals
    # Use average of recent pipeline orders as demand proxy
    recent_pipeline = pipeline_orders[:3] if len(pipeline_orders) >= 3 else pipeline_orders
    avg_recent_demand = sum(recent_pipeline) / len(recent_pipeline) if recent_pipeline else 0

    # Dynamic target adjustment based on demand pattern
    dynamic_target = base_stock + safety_stock * demand_buffer

    # Adjust for pipeline coverage with weighted approach
    pipeline_total = sum(pipeline_orders)
    adjusted_target = dynamic_target - pipeline_weight * pipeline_total

    # Calculate raw order with demand consideration
    raw_order = max(0, adjusted_target - inventory_position + avg_recent_demand * 0.3)

    # Apply smoothing with threshold
    if raw_order > avg_recent_demand * 0.5:
        order_amount = raw_order * smoothing
    else:
        order_amount = 0

    # Ensure integer order amount
    return order_amount
