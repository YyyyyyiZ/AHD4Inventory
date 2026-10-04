# policy_hash: c7ad9e44e17d92b0426e998dbf35a983e5de995502aba7eccc6083555a722891
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_5
# matched_train_cells: 3
# source_prompt_files: 1
# best_target_performance: 1326.44
# best_prompt_performance: 1326.44
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_031137.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 211.8928226884114  # OPT_PARAM: {"initial": 211.8928226884114, "min": 100, "max": 300, "type": "float"}
    safety_stock = 16.892822688411293  # OPT_PARAM: {"initial": 16.892822688411293, "min": 0, "max": 50, "type": "float"}
    demand_alpha = 0.4  # OPT_PARAM: {"initial": 0.4, "min": 0.1, "max": 0.9, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate demand using exponential smoothing of pipeline orders
    # Recent pipeline orders reflect recent demand patterns
    if len(pipeline_orders) >= 2:
        # Use weighted average of recent pipeline orders as demand estimate
        recent_orders = pipeline_orders[-2:]  # Last two orders
        weighted_sum = sum(w * o for w, o in zip([0.7, 0.3], recent_orders))
        expected_demand = weighted_sum * demand_alpha
    else:
        expected_demand = 100.0  # Default estimate

    # Dynamic base stock adjustment
    adjusted_base_stock = base_stock + safety_stock + expected_demand

    # Calculate order-up-to amount
    order_up_to = max(0, adjusted_base_stock - inventory_position)

    # Apply proportional adjustment based on current inventory level
    if on_hand_inventory > 0:
        inventory_ratio = min(1.0, on_hand_inventory / (expected_demand + 1e-6))
        reduction_factor = 0.13267911418136233  # OPT_PARAM: {"initial": 0.13267911418136233, "min": 0.0, "max": 0.5, "type": "float"}
        order_up_to *= (1.0 - reduction_factor * inventory_ratio)

    # Smooth order quantity to reduce volatility
    smoothing_factor = 0.3288203733625476  # OPT_PARAM: {"initial": 0.3288203733625476, "min": 0.1, "max": 0.8, "type": "float"}
    if pipeline_orders:
        previous_order = pipeline_orders[-1]
        smoothed_order = smoothing_factor * order_up_to + (1 - smoothing_factor) * previous_order
        order_up_to = max(0, smoothed_order)

    # Round to nearest integer
    order_amount = int(round(order_up_to))

    return order_amount
