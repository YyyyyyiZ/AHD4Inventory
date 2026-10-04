# policy_hash: 6d6175c195361ab8c59526471e383d3c231b4832a0fd7787f08c09a88c047d96
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_2
# matched_train_cells: 21
# source_prompt_files: 1
# best_target_performance: 3997.4
# best_prompt_performance: 3997.4
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_2_50_plain_processed_scipy_15_default_m2_2_r8/prompt_for_code/m2_20260128_212224.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 534.0521701419602  # OPT_PARAM: {"initial": 534.0521701419602, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 49.3442975495877  # OPT_PARAM: {"initial": 49.3442975495877, "min": 0, "max": 200, "type": "float"}
    pipeline_lead_time = 6  # fixed lead time

    # Calculate net inventory position
    net_inventory = on_hand_inventory + sum(pipeline_orders)

    # Calculate forecast based on recent pipeline arrivals
    # Use average of recent pipeline orders as demand forecast
    if len(pipeline_orders) >= 3:
        recent_orders = pipeline_orders[:3]  # oldest 3 orders (most recent arrivals)
        forecast = 96.77594110355973  # Optimized
    else:
        forecast = 100.0  # OPT_PARAM: {"initial": 100.0, "min": 50, "max": 200, "type": "float"}

    # Adjust base stock based on forecast
    adjusted_base = base_stock * (forecast / 100.0)  # scale by forecast

    # Calculate order-up-to level with safety stock
    order_up_to = max(adjusted_base, safety_stock + forecast * pipeline_lead_time)

    # Calculate order amount
    order_amount = max(0, order_up_to - net_inventory)

    # Smooth ordering with maximum order limit
    max_order = 100.0  # OPT_PARAM: {"initial": 100.0, "min": 100, "max": 500, "type": "float"}
    order_amount = min(order_amount, max_order)

    return order_amount
