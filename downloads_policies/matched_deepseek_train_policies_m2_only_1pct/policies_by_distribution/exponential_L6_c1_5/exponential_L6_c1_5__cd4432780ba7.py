# policy_hash: cd4432780ba7b5432f735739f8b8e3842aa464bdc30da69bfea4687d4e33ce1b
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_5
# matched_train_cells: 4
# source_prompt_files: 1
# best_target_performance: 11623.04
# best_prompt_performance: 11622.96
# best_rel_error_pct: 0.000688
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_060720.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 448.9056505622684  # OPT_PARAM: {"initial": 448.9056505622684, "min": 100, "max": 800, "type": "float"}
    safety_stock = 184.1767753386622  # OPT_PARAM: {"initial": 184.1767753386622, "min": 50, "max": 300, "type": "float"}
    pipeline_weight = 0.8210273911364142  # OPT_PARAM: {"initial": 0.8210273911364142, "min": 0.5, "max": 1.0, "type": "float"}

    # Calculate effective inventory position with weighted pipeline
    effective_pipeline = sum(pipeline_orders) * pipeline_weight
    inventory_position = on_hand_inventory + effective_pipeline

    # Dynamic order-up-to level based on demand variability
    demand_variability_factor = 1.1720541360041163  # OPT_PARAM: {"initial": 1.1720541360041163, "min": 1.0, "max": 2.0, "type": "float"}
    order_up_to = base_stock + safety_stock * demand_variability_factor

    # Calculate order amount
    order_amount = max(0, order_up_to - inventory_position)

    # Apply demand-responsive smoothing
    smoothing_factor = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 1.0, "type": "float"}
    if order_amount > 0:
        order_amount = order_amount * smoothing_factor

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
