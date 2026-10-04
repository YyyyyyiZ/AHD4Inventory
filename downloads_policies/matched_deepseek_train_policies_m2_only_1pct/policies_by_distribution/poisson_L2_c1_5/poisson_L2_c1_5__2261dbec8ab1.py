# policy_hash: 2261dbec8ab1ed9a07c70c3554720ff3f95d6dcb8ad6263301fa5204884b09fb
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_5
# matched_train_cells: 29
# source_prompt_files: 2
# best_target_performance: 1324.1
# best_prompt_performance: 1324.1
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_231242.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 309.9832444725077  # OPT_PARAM: {"initial": 309.9832444725077, "min": 200, "max": 400, "type": "float"}
    safety_stock = 54.98324447251217  # OPT_PARAM: {"initial": 54.98324447251217, "min": 0, "max": 100, "type": "float"}
    adjustment_factor = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.0, "type": "float"}
    pipeline_weight = 0.0  # OPT_PARAM: {"initial": 0.0, "min": 0.0, "max": 0.5, "type": "float"}
    demand_buffer = 36.65069837492692  # OPT_PARAM: {"initial": 36.65069837492692, "min": 0, "max": 50, "type": "float"}

    # Calculate current inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate weighted pipeline to anticipate near-term arrivals
    weighted_pipeline = sum(p * (1 - pipeline_weight * i)
                          for i, p in enumerate(pipeline_orders)) / len(pipeline_orders)

    # Dynamic target based on pipeline status
    dynamic_target = base_stock + safety_stock - pipeline_weight * weighted_pipeline

    # Add demand buffer for variability
    target_position = dynamic_target + demand_buffer

    # Calculate order amount with smoother adjustment
    raw_order = max(0, target_position - inventory_position)
    adjusted_order = adjustment_factor * raw_order

    # Round to nearest integer
    order_amount = int(round(adjusted_order))

    return order_amount
