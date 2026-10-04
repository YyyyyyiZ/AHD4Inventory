# policy_hash: 2c462ea1dbdfd8f5ea2d0efdb17bc5c94c0aa987ef306adbc842e7b1a93ddfc3
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_2
# matched_train_cells: 1
# source_prompt_files: 1
# best_target_performance: 1890.46
# best_prompt_performance: 1891.76
# best_rel_error_pct: 0.068766
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_092041.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 604.8771893823379  # OPT_PARAM: {"initial": 604.8771893823379, "min": 400, "max": 900, "type": "float"}
    safety_stock = 74.87718938232528  # OPT_PARAM: {"initial": 74.87718938232528, "min": 50, "max": 200, "type": "float"}
    demand_forecast = 120.0  # OPT_PARAM: {"initial": 120.0, "min": 80, "max": 120, "type": "float"}
    pipeline_weight = 0.8094907966474008  # OPT_PARAM: {"initial": 0.8094907966474008, "min": 0.5, "max": 1.0, "type": "float"}
    adjustment_factor = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 1.0, "type": "float"}
    reorder_threshold = 129.464737819269  # OPT_PARAM: {"initial": 129.464737819269, "min": 10, "max": 150, "type": "float"}
    max_order = 183.90293153916724  # OPT_PARAM: {"initial": 183.90293153916724, "min": 100, "max": 300, "type": "float"}

    # Calculate effective inventory position
    full_pipeline = sum(pipeline_orders)
    effective_pipeline = full_pipeline * pipeline_weight
    inventory_position = on_hand_inventory + effective_pipeline

    # Calculate target inventory level
    target_inventory = base_stock + safety_stock

    # Calculate deficit from target
    deficit = target_inventory - inventory_position

    # Only order if deficit is significant
    if deficit > reorder_threshold:
        # Base order: deficit plus forecasted demand
        base_order = deficit + demand_forecast

        # Apply adjustment factor for smoother ordering
        adjusted_order = base_order * adjustment_factor

        # Cap the order to avoid excessive ordering
        capped_order = min(adjusted_order, max_order)

        order_amount = max(0, capped_order)
    else:
        order_amount = 0

    # Round to nearest integer
    return order_amount
