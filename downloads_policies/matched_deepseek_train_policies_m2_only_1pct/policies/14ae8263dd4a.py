# policy_hash: 14ae8263dd4a9ac923739227f8b88632571cbb75e376beec8cb07f02d0400241
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_5
# matched_train_cells: 7
# source_prompt_files: 1
# best_target_performance: 1228.22
# best_prompt_performance: 1228.22
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_031357.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 271.8239274073009  # OPT_PARAM: {"initial": 271.8239274073009, "min": 250, "max": 350, "type": "float"}
    safety_stock = 21.62615213799902  # OPT_PARAM: {"initial": 21.62615213799902, "min": 15, "max": 40, "type": "float"}
    demand_estimate = 98.30285374314509  # OPT_PARAM: {"initial": 98.30285374314509, "min": 95, "max": 105, "type": "float"}
    pipeline_weight = 0.2  # OPT_PARAM: {"initial": 0.2, "min": 0.2, "max": 0.5, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.4, "type": "float"}
    lost_sales_multiplier = 1.2363597277288947  # OPT_PARAM: {"initial": 1.2363597277288947, "min": 1.2, "max": 2.5, "type": "float"}
    pipeline_correction = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.3, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate target inventory level
    target_level = base_stock + safety_stock * lost_sales_multiplier

    # Base order amount
    base_order = max(0, target_level - inventory_position)

    # Pipeline adjustment
    if len(pipeline_orders) > 0:
        expected_pipeline = demand_estimate * len(pipeline_orders)
        current_pipeline = sum(pipeline_orders)
        pipeline_deficit = max(0, expected_pipeline - current_pipeline)
        base_order += pipeline_weight * pipeline_deficit

        # Additional correction for pipeline imbalances
        pipeline_ratio = current_pipeline / max(1, expected_pipeline)
        if pipeline_ratio < 0.8:
            base_order += pipeline_correction * demand_estimate

    # Apply smoothing
    order_amount = smoothing_factor * base_order + (1 - smoothing_factor) * demand_estimate

    # Ensure non-negative integer order
    order_amount = max(0, int(round(order_amount)))

    return order_amount
