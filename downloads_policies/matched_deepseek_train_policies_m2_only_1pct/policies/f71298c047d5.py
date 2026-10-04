# policy_hash: f71298c047d500f5d70fd328bab7c4dce4298a9a938b48e46fd1f2d32cddbf86
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_5
# matched_train_cells: 25
# source_prompt_files: 1
# best_target_performance: 1116.62
# best_prompt_performance: 1116.62
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_032717.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 250.0  # OPT_PARAM: {"initial": 250.0, "min": 100, "max": 400, "type": "float"}
    safety_stock = 15.0  # OPT_PARAM: {"initial": 15.0, "min": 0, "max": 50, "type": "float"}
    demand_estimate_factor = 0.95  # OPT_PARAM: {"initial": 0.95, "min": 0.7, "max": 1.3, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate demand using pipeline information
    # For L=2, use weighted average of recent orders as demand estimate
    if len(pipeline_orders) >= 2:
        # Weight recent orders more heavily
        recent_weight = 0.7  # OPT_PARAM: {"initial": 0.7, "min": 0.5, "max": 0.9, "type": "float"}
        older_weight = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.1, "max": 0.5, "type": "float"}

        if pipeline_orders[-1] > 0 and pipeline_orders[-2] > 0:
            demand_estimate = (recent_weight * pipeline_orders[-1] +
                             older_weight * pipeline_orders[-2]) * demand_estimate_factor
        elif pipeline_orders[-1] > 0:
            demand_estimate = pipeline_orders[-1] * demand_estimate_factor
        else:
            demand_estimate = 100.0  # Default estimate
    else:
        demand_estimate = 100.0  # Default estimate

    # Adjust base stock dynamically based on demand estimate
    # Higher demand -> higher base stock, but with diminishing returns
    demand_adjustment = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.5, "type": "float"}
    adjusted_base = base_stock + safety_stock + (demand_estimate * demand_adjustment)

    # Calculate order amount using base stock policy
    order_amount = max(0, adjusted_base - inventory_position)

    # Apply conservative smoothing to reduce volatility
    smoothing = 0.8  # OPT_PARAM: {"initial": 0.8, "min": 0.2, "max": 0.8, "type": "float"}
    if pipeline_orders and pipeline_orders[-1] > 0:
        previous_order = pipeline_orders[-1]
        smoothed_order = smoothing * order_amount + (1 - smoothing) * previous_order
        order_amount = max(0, smoothed_order)

    # Ensure order amount is reasonable relative to demand estimate
    max_order_multiplier = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 1.0, "max": 3.0, "type": "float"}
    order_amount = min(order_amount, demand_estimate * max_order_multiplier)

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
