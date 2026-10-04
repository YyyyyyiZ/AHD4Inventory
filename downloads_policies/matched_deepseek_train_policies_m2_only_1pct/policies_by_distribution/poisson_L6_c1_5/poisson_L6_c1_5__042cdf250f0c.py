# policy_hash: 042cdf250f0cdcd8ce703402bb9b6ed45808d4be298d4acf6e4caef38e4d911b
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_5
# matched_train_cells: 17
# source_prompt_files: 1
# best_target_performance: 1602.92
# best_prompt_performance: 1602.92
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_021146.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 850.0  # OPT_PARAM: {"initial": 850.0, "min": 700, "max": 1000, "type": "float"}
    demand_estimate = 120.0  # OPT_PARAM: {"initial": 120.0, "min": 80, "max": 120, "type": "float"}
    safety_factor = 3.0  # OPT_PARAM: {"initial": 3.0, "min": 1.0, "max": 3.0, "type": "float"}
    max_order_cap = 100.0  # OPT_PARAM: {"initial": 100.0, "min": 100, "max": 250, "type": "float"}
    min_order_cap = 21.98444728935228  # OPT_PARAM: {"initial": 21.98444728935228, "min": 10, "max": 50, "type": "float"}
    demand_smoothing = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.9, "type": "float"}
    pipeline_weight = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.01, "max": 0.3, "type": "float"}
    lead_time = len(pipeline_orders)

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate recent pipeline average (last 2 periods)
    if len(pipeline_orders) >= 2:
        recent_orders = sum(pipeline_orders[-2:]) / 2
    else:
        recent_orders = demand_estimate

    # Smooth demand estimate with recent pipeline activity
    adjusted_demand = demand_estimate * (1 - demand_smoothing) + recent_orders * demand_smoothing

    # Calculate expected lead time demand
    expected_lead_time_demand = adjusted_demand * lead_time

    # Calculate safety stock
    safety_stock = safety_factor * adjusted_demand

    # Calculate target inventory position
    target_inventory = expected_lead_time_demand + safety_stock

    # Base order-up-to amount
    order_amount = max(0, target_inventory - inventory_position)

    # Apply pipeline adjustment only if we're ordering
    if order_amount > 0 and len(pipeline_orders) >= 2:
        pipeline_ratio = sum(pipeline_orders[-2:]) / (2 * adjusted_demand)
        pipeline_ratio = max(0.5, min(2.0, pipeline_ratio))  # Bound the ratio
        order_amount *= (1 - pipeline_weight) + pipeline_weight * pipeline_ratio

    # Apply caps
    order_amount = min(order_amount, max_order_cap)

    # Apply minimum order threshold
    if order_amount > 0 and order_amount < min_order_cap:
        order_amount = min_order_cap

    # Round to nearest integer
    return order_amount
