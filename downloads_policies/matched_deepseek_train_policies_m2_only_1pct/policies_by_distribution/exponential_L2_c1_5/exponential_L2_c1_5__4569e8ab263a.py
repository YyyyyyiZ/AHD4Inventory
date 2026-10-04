# policy_hash: 4569e8ab263a7544dec812565f8cca188de896e251eb09f32a2bf3d5becd79cb
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_5
# matched_train_cells: 14
# source_prompt_files: 1
# best_target_performance: 10636.72
# best_prompt_performance: 10636.72
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_032338.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 279.59999999999445  # OPT_PARAM: {"initial": 279.59999999999445, "min": 150, "max": 400, "type": "float"}
    safety_stock = 39.599999999998424  # OPT_PARAM: {"initial": 39.599999999998424, "min": 20, "max": 80, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Use pipeline information for demand forecasting
    if len(pipeline_orders) >= 2:
        # Weight recent arrivals more heavily for demand signal
        recent_weight = 0.7  # OPT_PARAM: {"initial": 0.7, "min": 0.4, "max": 0.9, "type": "float"}
        older_weight = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.1, "max": 0.6, "type": "float"}

        recent_demand_signal = pipeline_orders[0] * recent_weight
        if pipeline_orders[1] > 0:
            older_demand_signal = pipeline_orders[1] * older_weight
        else:
            older_demand_signal = 0

        demand_adjustment = recent_demand_signal + older_demand_signal
    else:
        demand_adjustment = 0

    # Dynamic adjustment factor based on demand signal
    adjustment_factor = 0.7  # OPT_PARAM: {"initial": 0.7, "min": 0.3, "max": 0.9, "type": "float"}
    adjusted_base_stock = base_stock + safety_stock + (demand_adjustment * adjustment_factor)

    # Calculate order amount with smoothing
    order_amount = max(0, adjusted_base_stock - inventory_position)

    # Apply order smoothing with dynamic maximum
    max_order_multiplier = 1.2  # OPT_PARAM: {"initial": 1.2, "min": 1.2, "max": 2.5, "type": "float"}
    max_order = base_stock * max_order_multiplier / 2.0

    # Further smoothing for large orders
    if order_amount > max_order:
        smoothing_factor = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 0.9, "type": "float"}
        order_amount = max_order + (order_amount - max_order) * smoothing_factor

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
