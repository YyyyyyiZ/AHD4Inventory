# policy_hash: f549f511306862fd6e5d3d4b57f104a781d9285032939f318582267e53f94e3d
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_5
# matched_train_cells: 5
# source_prompt_files: 1
# best_target_performance: 10556.76
# best_prompt_performance: 10556.76
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_072455.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 308.19999845400264  # OPT_PARAM: {"initial": 308.19999845400264, "min": 200, "max": 500, "type": "float"}
    safety_stock = 30.0  # OPT_PARAM: {"initial": 30.0, "min": 30, "max": 150, "type": "float"}
    adjustment_factor = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.0, "type": "float"}
    demand_buffer = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 1.0, "max": 2.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand based on pipeline orders
    if len(pipeline_orders) > 0:
        recent_orders = pipeline_orders[-min(3, len(pipeline_orders)):]
        avg_recent_order = sum(recent_orders) / len(recent_orders)
        demand_estimate = avg_recent_order * demand_buffer
    else:
        demand_estimate = 0

    # Dynamic target inventory based on demand estimate
    dynamic_target = max(base_stock, demand_estimate * 2.5)
    target_inventory = dynamic_target + safety_stock

    # Calculate order amount with adjustment factor
    order_amount = max(0, (target_inventory - inventory_position) * adjustment_factor)

    # Round to nearest integer since order amount should be integer
    order_amount = int(round(order_amount))

    return order_amount
