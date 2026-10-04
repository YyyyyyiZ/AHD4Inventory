# policy_hash: 5891488afb75ce96c2d97d4b8d9d308cdfa5e458502347ee74029b2b8605dcc3
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_5
# matched_train_cells: 6
# source_prompt_files: 1
# best_target_performance: 1224.1
# best_prompt_performance: 1224.1
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_032731.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 279.48257353894087  # OPT_PARAM: {"initial": 279.48257353894087, "min": 250, "max": 350, "type": "float"}
    safety_stock = 20.818384524485392  # OPT_PARAM: {"initial": 20.818384524485392, "min": 15, "max": 40, "type": "float"}
    demand_estimate = 97.90708077560338  # OPT_PARAM: {"initial": 97.90708077560338, "min": 95, "max": 105, "type": "float"}
    pipeline_weight = 0.2  # OPT_PARAM: {"initial": 0.2, "min": 0.2, "max": 0.5, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.4, "type": "float"}
    lost_sales_multiplier = 1.0883942506258897  # OPT_PARAM: {"initial": 1.0883942506258897, "min": 1.0, "max": 1.3, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Dynamic target level with lost sales adjustment
    target_level = base_stock + safety_stock * lost_sales_multiplier

    # Base order amount
    base_order = max(0, target_level - inventory_position)

    # Pipeline adjustment
    if len(pipeline_orders) > 0:
        expected_pipeline = demand_estimate * len(pipeline_orders)
        current_pipeline = sum(pipeline_orders)
        pipeline_deficit = max(0, expected_pipeline - current_pipeline)
        base_order += pipeline_weight * pipeline_deficit

    # Apply smoothing
    order_amount = smoothing_factor * base_order + (1 - smoothing_factor) * demand_estimate

    # Ensure non-negative integer order
    order_amount = max(0, int(round(order_amount)))

    return order_amount
