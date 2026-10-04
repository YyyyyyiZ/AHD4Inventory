# policy_hash: 1f17c95e36e4e474480ed7e7d45a0c9ab750348a86e1a058e71110f67bb0ec26
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_5
# matched_train_cells: 1
# source_prompt_files: 1
# best_target_performance: 1351.76
# best_prompt_performance: 1351.76
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_030500.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 180.0  # OPT_PARAM: {"initial": 180.0, "min": 100, "max": 300, "type": "float"}
    safety_stock = 15.0  # OPT_PARAM: {"initial": 15.0, "min": 0, "max": 50, "type": "float"}
    demand_estimate = 102.1531244457987  # OPT_PARAM: {"initial": 102.1531244457987, "min": 80, "max": 120, "type": "float"}
    pipeline_weight = 0.30734487310358133  # OPT_PARAM: {"initial": 0.30734487310358133, "min": 0.1, "max": 0.8, "type": "float"}
    order_smoothing = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate target inventory level
    target_level = base_stock + safety_stock

    # Base order amount
    base_order = max(0, target_level - inventory_position)

    # Add pipeline-aware adjustment
    if len(pipeline_orders) > 0:
        expected_pipeline = demand_estimate * len(pipeline_orders)
        current_pipeline = sum(pipeline_orders)
        pipeline_ratio = current_pipeline / expected_pipeline if expected_pipeline > 0 else 1.0
        if pipeline_ratio < 0.8:
            adjustment = pipeline_weight * (expected_pipeline - current_pipeline)
            base_order += max(0, adjustment)

    # Apply smoothing
    order_amount = order_smoothing * base_order + (1 - order_smoothing) * demand_estimate

    # Ensure non-negative integer order
    order_amount = max(0, int(round(order_amount)))

    return order_amount
