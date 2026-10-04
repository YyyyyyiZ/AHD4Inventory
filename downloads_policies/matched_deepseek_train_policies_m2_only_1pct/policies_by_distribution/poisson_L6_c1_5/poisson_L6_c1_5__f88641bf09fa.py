# policy_hash: f88641bf09fa07c716ac498e579debaa09c9eca6429e1b583d9fc4dbab029955
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_5
# matched_train_cells: 4
# source_prompt_files: 2
# best_target_performance: 3061.61
# best_prompt_performance: 3065.41
# best_rel_error_pct: 0.124118
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_095133.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 850.0  # OPT_PARAM: {"initial": 850.0, "min": 500, "max": 1200, "type": "float"}
    safety_stock = 200.0  # OPT_PARAM: {"initial": 200.0, "min": 50, "max": 200, "type": "float"}
    demand_estimate = 120.0  # OPT_PARAM: {"initial": 120.0, "min": 80, "max": 120, "type": "float"}
    adjustment_factor = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.0, "type": "float"}
    pipeline_weight = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.1, "max": 1.0, "type": "float"}
    min_order = 20  # OPT_PARAM: {"initial": 20, "min": 0, "max": 50, "type": "int"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time with weighted pipeline consideration
    expected_lead_time_demand = demand_estimate * len(pipeline_orders)

    # Adjust target based on pipeline composition
    weighted_pipeline = sum(p * (pipeline_weight ** i) for i, p in enumerate(reversed(pipeline_orders)))
    pipeline_adjustment = weighted_pipeline / (sum(pipeline_orders) + 1e-6)

    # Calculate target inventory position
    target_position = expected_lead_time_demand + safety_stock
    target_position = target_position * (0.8 + 0.2 * pipeline_adjustment)

    # Calculate order amount
    order_amount = max(0, target_position - inventory_position)

    # Apply adjustment factor
    order_amount = order_amount * adjustment_factor

    # Apply base stock as upper bound
    max_order = max(0, base_stock - inventory_position)
    order_amount = min(order_amount, max_order)

    # Apply minimum order quantity
    if order_amount > 0 and order_amount < min_order:
        order_amount = min_order

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
