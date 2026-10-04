# policy_hash: bb0d5ed665565d34d1028f909ad127b91efbc8889fdfd3b09f30e1845bbe141b
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_2
# matched_train_cells: 5
# source_prompt_files: 1
# best_target_performance: 712.48
# best_prompt_performance: 712.48
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_024135.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 217.66473852913435  # OPT_PARAM: {"initial": 217.66473852913435, "min": 160, "max": 230, "type": "float"}
    safety_stock = 84.36446819832386  # OPT_PARAM: {"initial": 84.36446819832386, "min": 30, "max": 90, "type": "float"}
    demand_forecast = 96.00981091509932  # OPT_PARAM: {"initial": 96.00981091509932, "min": 90, "max": 110, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Simple order-up-to level
    order_up_to = base_stock + safety_stock

    # Calculate order amount
    order_amount = max(0, order_up_to - inventory_position)

    # Apply smoothing to avoid extreme orders
    smoothing_factor = 0.9  # OPT_PARAM: {"initial": 0.9, "min": 0.5, "max": 0.9, "type": "float"}
    if order_amount > demand_forecast:
        order_amount = smoothing_factor * demand_forecast + (1 - smoothing_factor) * order_amount

    # Round to nearest integer
    return order_amount
