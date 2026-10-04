# policy_hash: 65f167e525192463f2395db2d6e43186ae4ffe9eaadf42805f8847f6804f015b
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_5
# matched_train_cells: 10
# source_prompt_files: 1
# best_target_performance: 1378.91
# best_prompt_performance: 1378.91
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260128_203525.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 667.0987975667878  # OPT_PARAM: {"initial": 667.0987975667878, "min": 400, "max": 700, "type": "float"}
    safety_stock = 0.0  # OPT_PARAM: {"initial": 0.0, "min": 0, "max": 50, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Simple demand estimation using average of recent pipeline arrivals
    if len(pipeline_orders) >= 2:
        recent_orders = pipeline_orders[:2]
        estimated_demand = sum(recent_orders) / len(recent_orders)
    else:
        estimated_demand = 100.0

    # Adjust base stock based on estimated demand
    demand_adjustment = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.2, "type": "float"}
    adjusted_base = base_stock + estimated_demand * demand_adjustment

    # Calculate target inventory level
    target_inventory = adjusted_base + safety_stock

    # Order amount calculation
    order_amount = max(0, target_inventory - inventory_position)

    # Smooth ordering with reasonable limits
    max_order = 100.0  # OPT_PARAM: {"initial": 100.0, "min": 100, "max": 250, "type": "float"}
    min_order = 0.0  # OPT_PARAM: {"initial": 0.0, "min": 0, "max": 50, "type": "float"}

    if len(pipeline_orders) > 0:
        last_order = pipeline_orders[-1]
        # Limit order increase/decrease for stability
        max_increase = 55.70202727159251  # OPT_PARAM: {"initial": 55.70202727159251, "min": 20, "max": 100, "type": "float"}
        order_amount = min(order_amount, last_order + max_increase)

    order_amount = max(min_order, min(order_amount, max_order))

    return order_amount
