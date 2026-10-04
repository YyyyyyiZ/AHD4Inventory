# policy_hash: 2aa22a60d31c90b97a879c862f8c5cf94400976eeb7c0b1be7f5c0fbd7cac343
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_2
# matched_train_cells: 11
# source_prompt_files: 1
# best_target_performance: 1144.02
# best_prompt_performance: 1144.02
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_234922.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 541.1792950968967  # OPT_PARAM: {"initial": 541.1792950968967, "min": 400, "max": 650, "type": "float"}
    safety_stock = 29.51772632863704  # OPT_PARAM: {"initial": 29.51772632863704, "min": 10, "max": 50, "type": "float"}
    demand_forecast = 98.01530540649314  # OPT_PARAM: {"initial": 98.01530540649314, "min": 90, "max": 110, "type": "float"}
    pipeline_weight = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.6, "max": 1.0, "type": "float"}
    smoothing_factor = 0.2  # OPT_PARAM: {"initial": 0.2, "min": 0.2, "max": 0.5, "type": "float"}
    lost_sales_weight = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 1.0, "max": 2.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate target inventory with asymmetric adjustment for lost sales
    pipeline_adjustment = pipeline_weight * pipeline_orders[-1]
    target_inventory = base_stock + safety_stock - pipeline_adjustment

    # Calculate order-up-to quantity
    order_needed = target_inventory - inventory_position

    # Apply smoothing with demand forecast
    if order_needed > 0:
        smoothed_order = smoothing_factor * order_needed + (1 - smoothing_factor) * demand_forecast
    else:
        smoothed_order = 0

    # Adjust for lost sales risk (more aggressive ordering when inventory is low)
    if on_hand_inventory < demand_forecast:
        smoothed_order = smoothed_order * lost_sales_weight

    # Ensure non-negative integer order
    order_amount = max(0, int(round(smoothed_order)))

    return order_amount
