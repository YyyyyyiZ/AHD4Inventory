# policy_hash: 9336d8a635d470277c3c5e083bfd302ae0a9ceb8e4c4d8a1b9291489777d851e
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L6_c1_5
# matched_train_cells: 8
# source_prompt_files: 1
# best_target_performance: 1248.74
# best_prompt_performance: 1248.74
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260129_195734.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 674.0521530585387  # OPT_PARAM: {"initial": 674.0521530585387, "min": 500, "max": 850, "type": "float"}
    safety_stock = 95.1  # OPT_PARAM: {"initial": 95.1, "min": 50, "max": 140, "type": "float"}
    demand_forecast = 97.56962570599282  # OPT_PARAM: {"initial": 97.56962570599282, "min": 85, "max": 115, "type": "float"}
    smoothing_factor = 0.010651305844020492  # OPT_PARAM: {"initial": 0.010651305844020492, "min": 0.0, "max": 0.3, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    expected_lead_time_demand = demand_forecast * len(pipeline_orders)

    # Calculate order-up-to level using both base stock and safety stock
    order_up_to = max(base_stock, expected_lead_time_demand + safety_stock)

    # Calculate order quantity
    order_amount = max(0, order_up_to - inventory_position)

    # Apply smoothing only when order is positive
    if order_amount > 0 and smoothing_factor > 0:
        order_amount = smoothing_factor * order_amount + (1 - smoothing_factor) * demand_forecast

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
