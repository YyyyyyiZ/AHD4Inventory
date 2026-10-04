# policy_hash: aee5212be3468e7c4dc91afd89559742cb5f7ea44cb373b863e5da460844c2ed
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_2
# matched_train_cells: 5
# source_prompt_files: 1
# best_target_performance: 1661.7
# best_prompt_performance: 1666.47
# best_rel_error_pct: 0.287055
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_092045.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 548.4423167538189  # OPT_PARAM: {"initial": 548.4423167538189, "min": 400, "max": 700, "type": "float"}
    safety_stock = 58.44231675381861  # OPT_PARAM: {"initial": 58.44231675381861, "min": 30, "max": 120, "type": "float"}
    demand_forecast = 98.44231675381151  # OPT_PARAM: {"initial": 98.44231675381151, "min": 80, "max": 120, "type": "float"}
    pipeline_weight = 0.8  # OPT_PARAM: {"initial": 0.8, "min": 0.8, "max": 1.0, "type": "float"}
    adjustment_factor = 0.3901023771524947  # OPT_PARAM: {"initial": 0.3901023771524947, "min": 0.3, "max": 0.8, "type": "float"}
    reorder_threshold = 50.0  # OPT_PARAM: {"initial": 50.0, "min": 20, "max": 100, "type": "float"}
    max_order = 148.26978700486242  # OPT_PARAM: {"initial": 148.26978700486242, "min": 100, "max": 200, "type": "float"}

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
