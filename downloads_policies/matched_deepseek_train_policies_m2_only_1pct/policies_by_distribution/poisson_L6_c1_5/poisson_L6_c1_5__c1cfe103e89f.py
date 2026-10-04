# policy_hash: c1cfe103e89fc5f5b18944f6caf44e69027045db89393a95fac6517f75509e07
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_5
# matched_train_cells: 43
# source_prompt_files: 1
# best_target_performance: 1165.54
# best_prompt_performance: 1165.47
# best_rel_error_pct: 0.006006
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260128_210344.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 616.8292742749949  # OPT_PARAM: {"initial": 616.8292742749949, "min": 450, "max": 650, "type": "float"}
    safety_stock = 36.96267159416835  # OPT_PARAM: {"initial": 36.96267159416835, "min": 0, "max": 40, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Simple demand estimation using average of recent pipeline orders
    if len(pipeline_orders) > 0:
        # Use last 3 periods for demand estimation
        recent_periods = min(3, len(pipeline_orders))
        estimated_demand = sum(pipeline_orders[-recent_periods:]) / recent_periods
    else:
        estimated_demand = 100.0

    # Adjust base stock based on estimated demand
    demand_adjustment = 0.5759871052136337  # OPT_PARAM: {"initial": 0.5759871052136337, "min": 0.3, "max": 1.5, "type": "float"}
    adjusted_base = base_stock + estimated_demand * demand_adjustment

    # Calculate target inventory level
    target_inventory = adjusted_base + safety_stock

    # Order amount calculation
    order_amount = max(0, target_inventory - inventory_position)

    # Apply smoothing to avoid extreme fluctuations
    smoothing_factor = 0.8235951877068544  # OPT_PARAM: {"initial": 0.8235951877068544, "min": 0.3, "max": 1.0, "type": "float"}
    if len(pipeline_orders) > 0:
        recent_avg = sum(pipeline_orders[-2:]) / min(2, len(pipeline_orders))
        order_amount = smoothing_factor * order_amount + (1 - smoothing_factor) * recent_avg

    # Order limits
    max_order = 99.02371901703317  # OPT_PARAM: {"initial": 99.02371901703317, "min": 80, "max": 200, "type": "float"}
    min_order = 0.0  # OPT_PARAM: {"initial": 0.0, "min": 0, "max": 20, "type": "float"}

    # Round to nearest integer for practical ordering
    order_amount = int(round(order_amount))

    order_amount = max(min_order, min(order_amount, max_order))

    return order_amount
