# policy_hash: 19eb47848ccf5a0aea8ebd70b2bae77a1ea33209a8a5910cc869b1b3e2618473
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_2
# matched_train_cells: 9
# source_prompt_files: 1
# best_target_performance: 712.5
# best_prompt_performance: 712.5
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_024421.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 241.1817396548582  # OPT_PARAM: {"initial": 241.1817396548582, "min": 220, "max": 280, "type": "float"}
    safety_stock = 61.18173965485817  # OPT_PARAM: {"initial": 61.18173965485817, "min": 40, "max": 90, "type": "float"}
    demand_forecast = 102.5  # OPT_PARAM: {"initial": 102.5, "min": 98, "max": 108, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Dynamic order-up-to level based on pipeline composition
    pipeline_imbalance = pipeline_orders[0] - pipeline_orders[-1] if len(pipeline_orders) > 1 else 0
    adjustment_factor = 0.15  # OPT_PARAM: {"initial": 0.15, "min": 0.05, "max": 0.3, "type": "float"}
    dynamic_adjustment = adjustment_factor * pipeline_imbalance

    order_up_to = base_stock + safety_stock - dynamic_adjustment

    # Calculate order amount
    order_amount = max(0, order_up_to - inventory_position)

    # Apply demand-responsive smoothing
    smoothing_threshold = 95.99164484005756  # OPT_PARAM: {"initial": 95.99164484005756, "min": 70, "max": 120, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.4, "type": "float"}

    if order_amount > smoothing_threshold:
        excess = order_amount - smoothing_threshold
        smoothed_excess = smoothing_factor * excess
        order_amount = smoothing_threshold + smoothed_excess

    # Round to nearest integer
    return order_amount
