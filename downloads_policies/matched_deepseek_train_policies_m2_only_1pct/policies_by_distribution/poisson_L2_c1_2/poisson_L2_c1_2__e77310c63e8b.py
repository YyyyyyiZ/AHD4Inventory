# policy_hash: e77310c63e8b497366ea5d6be13cb8c925593d41901241c892a251a914c8ed1a
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_2
# matched_train_cells: 5
# source_prompt_files: 1
# best_target_performance: 697.27
# best_prompt_performance: 697.27
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_023949.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 213.92833582565362  # OPT_PARAM: {"initial": 213.92833582565362, "min": 180, "max": 280, "type": "float"}
    safety_stock = 88.92833582564839  # OPT_PARAM: {"initial": 88.92833582564839, "min": 60, "max": 120, "type": "float"}
    demand_forecast = 97.37831757748333  # OPT_PARAM: {"initial": 97.37831757748333, "min": 90, "max": 110, "type": "float"}

    # Calculate current inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate order-up-to level with dynamic adjustment
    # Reduce base stock when pipeline has significant inventory
    pipeline_total = sum(pipeline_orders)
    pipeline_adjustment = 0.4  # OPT_PARAM: {"initial": 0.4, "min": 0.1, "max": 0.5, "type": "float"}

    if pipeline_total > demand_forecast * 1.5:
        adjusted_base = base_stock - pipeline_adjustment * (pipeline_total - demand_forecast * 1.5)
    else:
        adjusted_base = base_stock

    order_up_to = max(demand_forecast * 2, adjusted_base + safety_stock)

    # Calculate order amount
    order_amount = max(0, order_up_to - inventory_position)

    # Apply progressive smoothing based on order size
    smoothing_threshold = 94.55183548263102  # OPT_PARAM: {"initial": 94.55183548263102, "min": 80, "max": 200, "type": "float"}

    if order_amount > smoothing_threshold:
        # More aggressive smoothing for larger orders
        smoothing_factor = 0.2  # OPT_PARAM: {"initial": 0.2, "min": 0.2, "max": 0.8, "type": "float"}
        excess = order_amount - smoothing_threshold
        smoothed_excess = smoothing_factor * excess
        order_amount = smoothing_threshold + smoothed_excess

    # Round to nearest integer
    return order_amount
