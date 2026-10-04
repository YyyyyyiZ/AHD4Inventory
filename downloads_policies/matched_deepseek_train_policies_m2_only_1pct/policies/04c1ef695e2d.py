# policy_hash: 04c1ef695e2d20f6e1a48005453e1baa8d5063b5870f2c3d720913d218749bc4
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_2
# matched_train_cells: 4
# source_prompt_files: 1
# best_target_performance: 1425.92
# best_prompt_performance: 1425.92
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r4/prompt_for_code/m2_20251218_100008.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 290.786121085696  # OPT_PARAM: {"initial": 290.786121085696, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 17.828983868125768  # OPT_PARAM: {"initial": 17.828983868125768, "min": 0, "max": 100, "type": "float"}
    demand_adj_factor = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.5, "type": "float"}

    # Calculate net inventory position
    net_inventory = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand based on pipeline arrivals
    # Use average of recent pipeline orders as demand proxy
    if len(pipeline_orders) > 0:
        recent_orders = pipeline_orders[-2:] if len(pipeline_orders) >= 2 else pipeline_orders
        avg_recent_demand = sum(recent_orders) / len(recent_orders)
    else:
        avg_recent_demand = 100.0  # default estimate

    # Adjust base stock based on recent demand pattern
    adjusted_base = base_stock + (avg_recent_demand - 100) * demand_adj_factor

    # Calculate target inventory position
    target_inventory = adjusted_base + safety_stock

    # Calculate order amount
    order_amount = max(0, target_inventory - net_inventory)

    # Round to nearest integer (since order amounts should be integers)
    order_amount = int(round(order_amount))

    return order_amount
