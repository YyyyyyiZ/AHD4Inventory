# policy_hash: 2b93be4f9f17f3c9d1d80db1763a71fb54f8c948a8ba4859a30975e6997764e5
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_2
# matched_train_cells: 5
# source_prompt_files: 1
# best_target_performance: 1494.06
# best_prompt_performance: 1493.1
# best_rel_error_pct: 0.064254
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_074546.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 506.438614504557  # OPT_PARAM: {"initial": 506.438614504557, "min": 400, "max": 600, "type": "float"}
    safety_stock = 65.48346397687841  # OPT_PARAM: {"initial": 65.48346397687841, "min": 20, "max": 80, "type": "float"}
    demand_forecast = 102.74185924720172  # OPT_PARAM: {"initial": 102.74185924720172, "min": 90, "max": 110, "type": "float"}
    pipeline_weight = 0.9234672742820468  # OPT_PARAM: {"initial": 0.9234672742820468, "min": 0.8, "max": 1.2, "type": "float"}
    smoothing_factor = 0.427990636390945  # OPT_PARAM: {"initial": 0.427990636390945, "min": 0.3, "max": 0.9, "type": "float"}

    # Calculate inventory position with weighted pipeline
    effective_pipeline = sum(pipeline_orders) * pipeline_weight
    inventory_position = on_hand_inventory + effective_pipeline

    # Use demand forecast adjustment
    adjusted_base = base_stock * (demand_forecast / 100.0)

    # Calculate order-up-to level with safety stock
    order_up_to = adjusted_base + safety_stock

    # Calculate desired order quantity
    desired_order = max(0, order_up_to - inventory_position)

    # Apply smoothing to reduce volatility
    smoothed_order = smoothing_factor * desired_order

    # Round to nearest integer
    order_amount = int(round(smoothed_order))

    return order_amount
