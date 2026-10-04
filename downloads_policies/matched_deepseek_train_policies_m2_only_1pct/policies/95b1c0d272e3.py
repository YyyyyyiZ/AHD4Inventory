# policy_hash: 95b1c0d272e347587606b1cfbc71e63dbf44bfe5663fd910817e8a54bf2a426e
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_5
# matched_train_cells: 81
# source_prompt_files: 2
# best_target_performance: 1181.84
# best_prompt_performance: 1181.84
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_020000.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 680.0  # OPT_PARAM: {"initial": 680.0, "min": 600, "max": 900, "type": "float"}
    demand_estimate = 120.0  # OPT_PARAM: {"initial": 120.0, "min": 80, "max": 120, "type": "float"}
    safety_factor = 2.5  # OPT_PARAM: {"initial": 2.5, "min": 1.0, "max": 2.5, "type": "float"}
    max_order_cap = 100.0  # OPT_PARAM: {"initial": 100.0, "min": 100, "max": 200, "type": "float"}
    min_order_cap = 18.69249599934228  # OPT_PARAM: {"initial": 18.69249599934228, "min": 10, "max": 50, "type": "float"}
    demand_smoothing = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.9, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Dynamic demand adjustment based on recent pipeline
    recent_orders = sum(pipeline_orders[-2:]) / 2 if len(pipeline_orders) >= 2 else demand_estimate
    adjusted_demand = demand_estimate * (1 - demand_smoothing) + recent_orders * demand_smoothing

    # Calculate expected demand during lead time with safety factor
    expected_lead_time_demand = adjusted_demand * len(pipeline_orders)
    safety_stock = safety_factor * adjusted_demand

    # Calculate target inventory position
    target_inventory = expected_lead_time_demand + safety_stock

    # Calculate base order amount
    order_amount = max(0, target_inventory - inventory_position)

    # Apply order caps
    order_amount = min(order_amount, max_order_cap)

    # Apply minimum order threshold
    if order_amount > 0 and order_amount < min_order_cap:
        order_amount = min_order_cap

    # Ensure integer output
    return order_amount
