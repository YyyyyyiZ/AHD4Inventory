# policy_hash: d153ace20477b71f02495ff4d73f30b866107931d6e726f1ce25a99376c899aa
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_2
# matched_train_cells: 14
# source_prompt_files: 2
# best_target_performance: 943.78
# best_prompt_performance: 943.78
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_023633.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 280.40000000005716  # OPT_PARAM: {"initial": 280.40000000005716, "min": 250, "max": 320, "type": "float"}
    safety_stock = 15.400000000057263  # OPT_PARAM: {"initial": 15.400000000057263, "min": 5, "max": 40, "type": "float"}
    demand_forecast = 98.49999999999154  # OPT_PARAM: {"initial": 98.49999999999154, "min": 95, "max": 105, "type": "float"}
    pipeline_weight = 0.2210496819605003  # OPT_PARAM: {"initial": 0.2210496819605003, "min": 0.2, "max": 0.8, "type": "float"}
    smoothing_factor = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 0.9, "type": "float"}
    max_order_multiplier = 1.2  # OPT_PARAM: {"initial": 1.2, "min": 1.2, "max": 2.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected pipeline coverage with more aggressive adjustment
    expected_pipeline = demand_forecast * len(pipeline_orders)
    pipeline_adjustment = (expected_pipeline - sum(pipeline_orders)) * pipeline_weight

    # Dynamic order-up-to level with reduced safety stock
    order_up_to = base_stock + safety_stock + pipeline_adjustment

    # Calculate order amount
    order_amount = max(0, order_up_to - inventory_position)

    # Apply tighter smoothing with higher multiplier
    if order_amount > max_order_multiplier * demand_forecast:
        order_amount = smoothing_factor * order_amount + (1 - smoothing_factor) * max_order_multiplier * demand_forecast

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
