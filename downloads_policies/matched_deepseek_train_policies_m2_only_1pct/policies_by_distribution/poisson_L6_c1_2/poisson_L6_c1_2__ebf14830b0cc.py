# policy_hash: ebf14830b0ccd373418b5fb46783256449a742bb714d6dd07b12055e4b12666e
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_2
# matched_train_cells: 4
# source_prompt_files: 1
# best_target_performance: 789.52
# best_prompt_performance: 788.91
# best_rel_error_pct: 0.077262
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_092553.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 584.0835128570567  # OPT_PARAM: {"initial": 584.0835128570567, "min": 500, "max": 650, "type": "float"}
    safety_stock = 79.08351285705761  # OPT_PARAM: {"initial": 79.08351285705761, "min": 50, "max": 100, "type": "float"}
    demand_forecast = 106.2072955409251  # OPT_PARAM: {"initial": 106.2072955409251, "min": 90, "max": 110, "type": "float"}
    pipeline_weight = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.8, "max": 1.0, "type": "float"}
    adjustment_factor = 0.5193306334489441  # OPT_PARAM: {"initial": 0.5193306334489441, "min": 0.4, "max": 0.7, "type": "float"}
    reorder_threshold = 30.0  # OPT_PARAM: {"initial": 30.0, "min": 20, "max": 60, "type": "float"}
    max_order = 100.0  # OPT_PARAM: {"initial": 100.0, "min": 100, "max": 150, "type": "float"}

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
